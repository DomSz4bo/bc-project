from typing import Literal

from langchain_core.globals import set_verbose
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.agents import (
    analyst,
    architect,
    critic,
    engineer,
    quality_assurance,
    supervisor,
    scaffolder,
    tdd_lead,
)
from src.graph.state import AgentState, GraphContext

set_verbose(True)

SUPERVISOR = "Supervisor"
ANALYST = "Analyst"
ARCHITECT = "Architect"
CRITIC = "Critic"
SCAFFOLDER = "Scaffolder"
TDD = "TDD Lead"
QA = "Quality assurance"
ENGINEER = "Engineer"


async def supervisor_router(state: AgentState) -> Literal["design", "implement", "end"]:
    match state["next_step"]:
        case "DESIGN":
            return "design"
        case "IMPLEMENT":
            return "implement"
        case "USER":
            return "end"
    raise ValueError(f"Unexpected next_step value: {state['next_step']}")


async def critic_router(state: AgentState) -> Literal["fix", "done"]:
    match state["critic_verdict"]:
        case "FAIL":
            return "fix"
        case "PASS" | "LIMIT":
            return "done"
    raise ValueError(f"Unexpected critic_verdict value: {state['critic_verdict']}")


def create_graph() -> CompiledStateGraph:
    """
    Creates and compiles the state graph for the AI development pipeline.
    """
    builder = StateGraph(AgentState, GraphContext)

    builder.add_node(SUPERVISOR, supervisor)
    builder.add_node(ANALYST, analyst)
    builder.add_node(ARCHITECT, architect)
    builder.add_node(CRITIC, critic)
    builder.add_node(SCAFFOLDER, scaffolder)
    builder.add_node(TDD, tdd_lead)
    builder.add_node(ENGINEER, engineer)
    builder.add_node(QA, quality_assurance)

    builder.set_entry_point(SUPERVISOR)
    builder.add_conditional_edges(
        SUPERVISOR,
        supervisor_router,
        {"design": ANALYST, "implement": SCAFFOLDER, "end": END},
    )

    ## Design lab
    builder.add_edge(ANALYST, ARCHITECT)
    builder.add_edge(ARCHITECT, CRITIC)
    builder.add_conditional_edges(
        CRITIC, critic_router, {"fix": ARCHITECT, "done": SUPERVISOR}
    )

    ## Implementation lab
    builder.add_edge(SCAFFOLDER, TDD)
    builder.add_edge(TDD, ENGINEER)
    builder.add_edge(ENGINEER, QA)
    builder.add_edge(QA, END)

    # Graph compilation
    checkpointer = InMemorySaver()
    return builder.compile(checkpointer=checkpointer)


if __name__ == "__main__":
    graph = create_graph()
    graph.get_graph().draw_mermaid_png(output_file_path="graph.png")
    mmd = graph.get_graph().draw_mermaid(with_styles=False)
    with open("graph.mmd", "w") as file:
        print(mmd, file=file)
