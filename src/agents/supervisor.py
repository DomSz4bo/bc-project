from langchain.agents import create_agent

from src.graph.state import AgentState
from src.utils.llm import llm




main_agent = create_agent()


async def supervisor(state: AgentState) -> AgentState:
    return state
