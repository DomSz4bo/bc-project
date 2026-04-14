from typing import Literal

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
from src.agents.qa import qa_tool_node
from src.agents.supervisor import (
    DESIGN_HANDOFF,
    IMPLEMENT_HANDOFF,
    supervisor_tool_node,
)
from src.graph.node_names import Nodes
from src.graph.state import AgentState, GraphContext
from src.graph.util_nodes import (
    finish_design_node,
    finish_implementation_node,
    prepare_design_node,
    prepare_fix_node,
    prepare_implementation_node,
)


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

    builder.add_node(Nodes.SUPERVISOR, supervisor)
    builder.add_node(Nodes.ANALYST, analyst)
    builder.add_node(Nodes.ARCHITECT, architect)
    builder.add_node(Nodes.CRITIC, critic)
    builder.add_node(Nodes.SCAFFOLDER, scaffolder)
    builder.add_node(Nodes.TDD, tdd_lead)
    builder.add_node(Nodes.ENGINEER, engineer)
    builder.add_node(Nodes.QA, quality_assurance)
    builder.add_node(Nodes.TOOLS, supervisor_tool_node)
    builder.add_node(Nodes.QA_TOOLS, qa_tool_node)
    builder.add_node(Nodes.PREPARE_DESIGN, prepare_design_node)
    builder.add_node(Nodes.FINISH_DESIGN, finish_design_node)
    builder.add_node(Nodes.PREPARE_IMPLEMENTATION, prepare_implementation_node)
    builder.add_node(Nodes.FINISH_IMPLEMENTATION, finish_implementation_node)
    builder.add_node(Nodes.PREPARE_FIX, prepare_fix_node)

    builder.set_entry_point(Nodes.SUPERVISOR)
    builder.add_conditional_edges(
        Nodes.SUPERVISOR,
        supervisor_router,
        {
            "design": Nodes.PREPARE_DESIGN,
            "implement": Nodes.PREPARE_IMPLEMENTATION,
            "tools": Nodes.TOOLS,
            "end": END,
        },
    )
    builder.add_edge(Nodes.TOOLS, Nodes.SUPERVISOR)

    # Design lab
    builder.add_edge(Nodes.PREPARE_DESIGN, Nodes.ANALYST)
    builder.add_edge(Nodes.ANALYST, Nodes.ARCHITECT)
    builder.add_conditional_edges(
        Nodes.CRITIC,
        critic_router,
        {"fix": Nodes.ARCHITECT, "done": Nodes.FINISH_DESIGN},
    )
    builder.add_edge(Nodes.FINISH_DESIGN, Nodes.SUPERVISOR)

    # Implementation lab
    builder.add_edge(Nodes.PREPARE_IMPLEMENTATION, Nodes.SCAFFOLDER)
    builder.add_edge(Nodes.SCAFFOLDER, Nodes.TDD)
    builder.add_edge(Nodes.TDD, Nodes.ENGINEER)
    builder.add_edge(Nodes.ENGINEER, Nodes.QA)
    builder.add_edge(Nodes.QA_TOOLS, Nodes.QA)
    builder.add_edge(Nodes.PREPARE_FIX, Nodes.ENGINEER)
    builder.add_edge(Nodes.FINISH_IMPLEMENTATION, Nodes.SUPERVISOR)

    # Graph compilation
    checkpointer = InMemorySaver()
    return builder.compile(checkpointer=checkpointer)


if __name__ == "__main__":
    graph = create_graph()
    graph.get_graph().draw_mermaid_png(output_file_path="graph.png")
    mmd = graph.get_graph().draw_mermaid(with_styles=False)
    with open("graph.mmd", "w") as file:
        print(mmd, file=file)
