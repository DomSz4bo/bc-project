from langchain.agents import create_agent
from langchain.messages import HumanMessage
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.runtime import Runtime
from loguru import logger

from src.graph.state import AgentState, GraphContext
from src.utils.llm import gemini_3_flash_lite as llm
from src.utils.source_context import extract_project_context
from src.utils.tools import get_mcp_client, run_tests


async def engineer(state: AgentState, runtime: Runtime[GraphContext]) -> AgentState:
    """
    Engineer agent.
    Writes the implemenation for the designed system and tests.
    """
    logger.debug("Engineer node initiated.")

    context = extract_project_context(state, runtime.context.get("working_directory"))

    qa_feedback = state.get("qa_feedback")

    human_prompt = HUMAN_PROMPT
    if qa_feedback:
        human_prompt += f"\n\n### Quality Assurance FEEDBACK\n:{qa_feedback}"

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
            llm,
            all_tools,
            system_prompt=SYSTEM_PROMPT,
            context_schema=GraphContext,
        )
        await engineer_agent.ainvoke({"messages": [input_message]})

    return {}


SYSTEM_PROMPT = """
You are an expert software engineer and you task is to implement the system.
"""


HUMAN_PROMPT = """
Here is the system design:

**Use Case**
<use_case>
{use_case}
</use_case>

**Mermaid Sequence Diagram**
<sequence_diagram>
{sequence_diagram}
</sequence_diagrma>

Here are the current contents of the project files:
{source_code_context}

The tests that the implementation needs to fufill.
{tests_context}
"""
