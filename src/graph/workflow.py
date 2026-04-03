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
    scaffolder,
    supervisor,
    tdd_lead,
)
from src.agents.qa import REJECT_IMPLEMENTATION, qa_tool_node
from src.agents.supervisor import (
    DESIGN_HANDOFF,
    IMPLEMENT_HANDOFF,
    supervisor_tool_node,
)
from src.graph.state import AgentState, GraphContext
from src.graph.util_nodes import (
    finish_design_node,
    finish_implementation_node,
    prepare_design_node,
    prepare_fix_node,
    prepare_implementation_node,
)

set_verbose(True)

SUPERVISOR = "Supervisor"
ANALYST = "Analyst"
ARCHITECT = "Architect"
CRITIC = "Critic"
SCAFFOLDER = "Scaffolder"
TDD = "TDD Lead"
QA = "Quality assurance"
ENGINEER = "Engineer"
TOOLS = "tools"
QA_TOOLS = "qa_tools"
PREPARE_DESIGN = "PrepareDesign"
FINISH_DESIGN = "FinishDesign"
PREPARE_IMPLEMENTATION = "PrepareImplementation"
FINISH_IMPLEMENTATION = "FinishImplementation"
PREPARE_FIX = "PrepareFix"


async def supervisor_router(
    state: AgentState,
) -> Literal["design", "implement", "tools", "end"]:
    last_message = state["messages"][-1]
    if not last_message.tool_calls:
        return "end"

    tool_names = [tc["name"] for tc in last_message.tool_calls]
    handoff_tools = [DESIGN_HANDOFF, IMPLEMENT_HANDOFF]

    if any(name not in handoff_tools for name in tool_names):
        return "tools"

    if DESIGN_HANDOFF in tool_names:
        return "design"
    if IMPLEMENT_HANDOFF in tool_names:
        return "implement"

    return "end"


async def qa_router(
    state: AgentState,
) -> Literal["fix", "tools", "done"]:
    feedback = state["qa_feedback"]
    if feedback and feedback == "LIMIT":
        return "done"

    last_message = state["messages"][-1]
    if not last_message.tool_calls:
        return "done"

    tool_names = [tc["name"] for tc in last_message.tool_calls]

    if any(name != REJECT_IMPLEMENTATION for name in tool_names):
        return "tools"

    return "fix"


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
    builder.add_node(TOOLS, supervisor_tool_node)
    builder.add_node(QA_TOOLS, qa_tool_node)
    builder.add_node(PREPARE_DESIGN, prepare_design_node)
    builder.add_node(FINISH_DESIGN, finish_design_node)
    builder.add_node(PREPARE_IMPLEMENTATION, prepare_implementation_node)
    builder.add_node(FINISH_IMPLEMENTATION, finish_implementation_node)
    builder.add_node(PREPARE_FIX, prepare_fix_node)

    builder.set_entry_point(SUPERVISOR)
    builder.add_conditional_edges(
        SUPERVISOR,
        supervisor_router,
        {
            "design": PREPARE_DESIGN,
            "implement": PREPARE_IMPLEMENTATION,
            "tools": TOOLS,
            "end": END,
        },
    )
    builder.add_edge(TOOLS, SUPERVISOR)

    # Design lab
    builder.add_edge(PREPARE_DESIGN, ANALYST)
    builder.add_edge(ANALYST, ARCHITECT)
    builder.add_edge(ARCHITECT, CRITIC)
    builder.add_conditional_edges(
        CRITIC, critic_router, {"fix": ARCHITECT, "done": FINISH_DESIGN}
    )
    builder.add_edge(FINISH_DESIGN, SUPERVISOR)

    # Implementation lab
    builder.add_edge(PREPARE_IMPLEMENTATION, SCAFFOLDER)
    builder.add_edge(SCAFFOLDER, TDD)
    builder.add_edge(TDD, ENGINEER)
    builder.add_edge(ENGINEER, QA)

    builder.add_conditional_edges(
        QA,
        qa_router,
        {"fix": PREPARE_FIX, "tools": QA_TOOLS, "done": FINISH_IMPLEMENTATION},
    )
    builder.add_edge(QA_TOOLS, QA)
    builder.add_edge(PREPARE_FIX, ENGINEER)
    builder.add_edge(FINISH_IMPLEMENTATION, SUPERVISOR)

    # Graph compilation
    checkpointer = InMemorySaver()
    return builder.compile(checkpointer=checkpointer)


if __name__ == "__main__":
    graph = create_graph()
    graph.get_graph().draw_mermaid_png(output_file_path="graph.png")
    mmd = graph.get_graph().draw_mermaid(with_styles=False)
    with open("graph.mmd", "w") as file:
        print(mmd, file=file)
