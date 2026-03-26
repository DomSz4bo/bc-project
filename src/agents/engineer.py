from langchain.agents import create_agent
from langchain.messages import HumanMessage
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.runtime import Runtime
from loguru import logger

from src.graph.state import AgentState, GraphContext
from src.utils.llm import gemini_3_flash_lite as llm
from src.utils.mcp_clients import get_filesystem_client
from src.utils.source_context import read_source_files
from src.utils.tools import run_tests


async def engineer(state: AgentState, runtime: Runtime[GraphContext]) -> AgentState:
    """
    Engineer agent.
    Writes the implemenation for the designed system and tests.
    """
    logger.debug("Engineer node initiated.")

    use_case = state.get("use_case")
    sequence_diagram = state.get("sequence_diagram")
    working_dir = runtime.context.get("working_directory")

    if not use_case:
        raise ValueError("No use_case found in AgentState.")
    if not sequence_diagram:
        raise ValueError("No sequence_diagram found in AgentState.")
    if not working_dir:
        raise ValueError("Missing working_directory in GraphContext.")

    source_code_context = read_source_files(working_dir)

    input_message = HumanMessage(
        HUMAN_PROMPT.format(
            use_case=use_case,
            sequence_diagram=sequence_diagram,
            source_code_context=source_code_context,
        ),
    )

    filesystem_client = get_filesystem_client(working_dir)

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

And here are the current contents of the project files:
{source_code_context}
"""
