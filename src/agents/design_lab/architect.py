from src.graph.state import AgentState
from src.utils.llm import llm


async def architect(state: AgentState) -> AgentState:
    return state