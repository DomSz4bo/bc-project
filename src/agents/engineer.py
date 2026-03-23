import asyncio
from pathlib import Path

from langchain.agents import create_agent
from langchain.messages import HumanMessage, SystemMessage
from langchain.tools import ToolRuntime, tool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.graph import MessagesState
from langgraph.runtime import Runtime
from loguru import logger

from src.graph.state import AgentState, GraphContext
from src.utils.llm import gemini_3_flash_lite as llm
from src.utils.source_context import read_source_files


async def get_filesystem_tools(allowed_dir: Path):
    client = MultiServerMCPClient(
        {
            "filesystem": {
                "transport": "stdio",
                "command": "npx",
                "args": [
                    "-y",
                    "@modelcontextprotocol/server-filesystem",
                    allowed_dir,
                ],
            }
        }
    )
    return await client.get_tools()


@tool
async def run_tests(runtime: ToolRuntime[GraphContext]) -> str:
    """
    Executes the pytest suite. Returns the output of the test run.
    Use this to verify your changes.
    """
    process = await asyncio.create_subprocess_exec(
        "pytest", "-q", "--tb=short",
        cwd=runtime.context["working_directory"],
        stderr=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await process.communicate()
    result_text = stdout.decode() + stderr.decode()

    if process.returncode == 0:
        return "✅ Tests Passed"
    else:
        return f"❌ Tests Failed (Code {process.returncode}):\n{result_text}"


async def engineer(state: AgentState, runtime: Runtime[GraphContext]) -> AgentState:
    """Engineer node"""
    logger.debug("Engineer node initiated.")

    use_case = state.get("use_case")
    sequence_diagram = state.get("sequence_diagram")
    working_dir = runtime.context.get("working_directory", None)

    if not use_case:
        raise ValueError("No use_case found in AgentState.")
    if not sequence_diagram:
        raise ValueError("No sequence_diagram found in AgentState.")
    if not working_dir:
        raise ValueError("Missing working_directory in GraphContext.")

    source_code_context = read_source_files(working_dir)

    messages = [
        SystemMessage(SYSTEM_PROMPT),
        HumanMessage(
            HUMAN_PROMPT.format(
                use_case=use_case,
                sequence_diagram=sequence_diagram,
                source_code_context=source_code_context,
            ),
        ),
    ]

    tools = (await get_filesystem_tools()) + [run_tests]
    engineer_agent = create_agent(
        llm, tools=tools, state_schema=MessagesState, context_schema=GraphContext
    )
    await engineer_agent.ainvoke({"messages": messages})

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

And here are the current contents of the project files:
{source_code_context}
"""
