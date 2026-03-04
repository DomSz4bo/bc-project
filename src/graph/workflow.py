from typing import Literal

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, StateGraph

from src.agents import (
    analyst,
    architect,
    critic,
    engineer,
    quality_assurance,
    supervisor,
)
from src.graph.state import AgentState

# Node names
SUPERVISOR = "Supervisor"
ANALYST = "Analyst"
ARCHITECT = "Architect"
CRITIC = "Critic"
QA = "Quality assurance"
ENGINEER = "Engineer"


builder = StateGraph(AgentState)
# Node definitions
builder.add_node(SUPERVISOR, supervisor)
builder.add_node(ANALYST, analyst)
builder.add_node(ARCHITECT, architect)
builder.add_node(CRITIC, critic)
builder.add_node(QA, quality_assurance)
builder.add_node(ENGINEER, engineer)


# Router functions
async def supervisor_router(state: AgentState) -> Literal["design", "implement", "end"]:
    if 1 > 2:
        return "design"
    if 1 == 2:
        return "implement"
    return "end"


async def critic_router(state: AgentState) -> Literal["fix", "done"]:
    if 1 < 2:
        return "fix"
    return "done"


# Edge definitions
builder.set_entry_point(SUPERVISOR)
builder.add_conditional_edges(
    SUPERVISOR, supervisor_router, {"design": ANALYST, "implement": QA, "end": END}
)
## Design lab
builder.add_edge(ANALYST, ARCHITECT)
builder.add_edge(ARCHITECT, CRITIC)
builder.add_conditional_edges(
    CRITIC, critic_router, {"fix": ARCHITECT, "done": SUPERVISOR}
)
## Implementation lab
builder.add_edge(QA, ENGINEER)
builder.add_edge(ENGINEER, SUPERVISOR)

# Graph compilation
checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)


if __name__ == "__main__":
    graph.get_graph().draw_mermaid_png(output_file_path="graph.png")
    mmd = graph.get_graph().draw_mermaid(with_styles=False)
    with open("graph.mmd", "w") as file:
        print(mmd, file=file)
