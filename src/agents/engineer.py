from langchain.agents import create_agent
from langchain.agents.middleware import ModelFallbackMiddleware, ModelRetryMiddleware
from langchain.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.config import get_stream_writer
from langgraph.runtime import Runtime
from loguru import logger

from src.graph.state import AgentState, GraphContext
from src.utils.llm import gemini_3p1_flash_lite, gemma_4_31b
from src.utils.middleware import (
    LoggingMiddleware,
    ModelCallStreamingMiddleware,
    ToolErrorMiddleware,
    ToolStreamingMiddleware,
)
from src.utils.source_context import extract_project_context
from src.utils.streaming import CustomStreamData
from src.utils.tools import get_mcp_client, run_tests


async def engineer(
    state: AgentState, runtime: Runtime[GraphContext], config: RunnableConfig
) -> AgentState:
    """
    Engineer agent.
    Writes the implementation for the designed system and tests.
    """
    writer = get_stream_writer()
    writer(CustomStreamData("Engineer", "node_name"))
    writer(CustomStreamData("Engineer is working on the implementation", "start"))
    logger.info("Engineer node initiated.")

    context = extract_project_context(state, runtime.context.get("working_directory"))

    qa_feedback = state.get("qa_feedback")

    human_prompt = HUMAN_PROMPT
    if qa_feedback:
        human_prompt += (
            f"\n\n### 🚨 QUALITY ASSURANCE FEEDBACK\n"
            f"Your previous implementation was rejected by QA for the following reasons:\n"
            f"<qa_feedback>\n{qa_feedback}\n</qa_feedback>\n\n"
            f"You must fix these issues and verify them using `run_tests` before finishing."
        )

    input_message = HumanMessage(
        human_prompt.format(
            use_case=context.use_case,
            sequence_diagram=context.sequence_diagram,
            source_code_context=context.source_code_context,
            tests_context=context.test_files_context,
        ),
    )

    filesystem_client = get_mcp_client()

    async with filesystem_client.session("filesystem") as session:
        file_tools = await load_mcp_tools(session)
        all_tools = file_tools + [run_tests]

        engineer_agent = create_agent(
            gemini_3p1_flash_lite,
            all_tools,
            system_prompt=SYSTEM_PROMPT,
            context_schema=GraphContext,
            middleware=[
                ModelFallbackMiddleware(gemma_4_31b),
                ModelRetryMiddleware(
                    on_failure="error", initial_delay=3, backoff_factor=22, max_delay=70
                ),
                ModelCallStreamingMiddleware("Working on the implementation...", ""),
                ToolStreamingMiddleware(),
                ToolErrorMiddleware(),
                LoggingMiddleware(),
            ],
        )
        await engineer_agent.ainvoke({"messages": [input_message]}, config=config)

    writer(CustomStreamData("Implementation written.", "end"))
    logger.info("Engineer finished work.")

    return {}


SYSTEM_PROMPT = """
You are the Implementation Engineer in a visual-first AI development pipeline.
Your mandate is to write the concrete Python code implementation for the system based strictly on the verified design, and ensure that all tests pass.

---

## YOUR MANDATE
1. **Understand the Design:** Rely on the provided Cockburn Use Case (Intent) and Mermaid Sequence Diagram (Logic) as the absolute source of truth for business rules and architecture.
2. **Implement the Logic:** The project has already been scaffolded by the Scaffolder agent. Your task is to fill in the missing implementation logic within these existing files.
3. **Pass the Tests:** The Test-Driven Development (TDD) Lead has provided a comprehensive test suite. Your implementation MUST pass these tests. Do not modify the test files unless they are fundamentally broken; focus on making the production code satisfy the tests.
4. **Iterative Verification:** You must not assume your code works. Use the `run_tests` tool repeatedly to verify your work. Read the test error output, debug, and fix the implementation until all tests pass.

---

## PYTHON & PROGRAMMING BEST PRACTICES
- **Pythonic Code:** Write clean, readable, and idiomatic Python (adhering to PEP 8 standards).
- **Type Hinting:** Strictly use modern Python type hints (e.g., `list[str]`, `dict[str, int]`, `type | None`) for all function signatures and class attributes to ensure type safety.
- **Clean Architecture:** Keep functions and methods focused on a single responsibility. Avoid deep nesting and write modular code.
- **Error Handling:** Anticipate failures and handle exceptions gracefully. Use custom exception classes if it clarifies the domain logic.
- **Maintainability:** Use clear, descriptive variable and function names. Avoid mutable default arguments.
- **No Hacks:** Do not use `type: ignore` or other bypasses unless absolutely necessary. Write structurally sound code.

---

## WORKFLOW
1. **Analyze:** Review the source code stubs and test files provided in the context.
2. **Plan**: Create a plan of what the implementation will look like.
3. **Implement:** Use filesystem tools to write the required logic adhering to Python best practices.
4. **Verify:** Run the `run_tests` tool.
5. **Fix:** If tests fail, analyze the failures, apply fixes, and run `run_tests` again.
6. **Finish:** Once all tests pass, provide a brief summary of your implementation. Do not finish until all tests pass.
"""


HUMAN_PROMPT = """
Here is the system design and current state of the project:

### DESIGN SPECIFICATIONS

**1. Cockburn Use Case (Intent)**
<use_case>
{use_case}
</use_case>

**2. Mermaid Sequence Diagram (Logic)**
<sequence_diagram>
{sequence_diagram}
</sequence_diagram>

---

### CURRENT PROJECT STATE

**Production Source Code**
<source_code>
{source_code_context}
</source_code>

**Test Suite**
<tests>
{tests_context}
</tests>

---

### INSTRUCTIONS
Please implement the required logic in the source code files to satisfy the design and make all tests pass.
Use the `run_tests` tool to execute the test suite and iteratively verify your work.
"""
