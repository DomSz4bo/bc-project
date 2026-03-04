from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import create_agent

from src.graph.state import AgentState
from src.agents import (
    supervisor,
    analyst,
    architect,
    critic,
    quality_assurance,
    engineer,
)

builder = StateGraph(AgentState)
builder.add_node("supervisor", supervisor)
builder.add_node("analyst", analyst)
builder.add_node("architect", architect)
builder.add_node("critic", critic)
builder.add_node("QA", quality_assurance)
builder.add_node("engineer", engineer)

builder.set_entry_point("supervisor")
builder.add_edge()
# builder.add_conditional_edges()
builder.set_finish_point()

checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)

if __name__ == "__main__":
    mmd = graph.get_graph().draw_mermaid()
    with open("graph.mmd", "w") as file:
        print(mmd, file=file)
