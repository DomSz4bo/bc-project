from typing import Literal, Annotated
from typing_extensions import TypedDict

# 1. Use init_chat_model for flexibility
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig

from langgraph.prebuilt import ToolNode
from langgraph.graph import END, StateGraph, START
from langgraph.graph.message import MessagesState
# 2. Import MemorySaver to actually enable conversation history
from langgraph.checkpoint.memory import MemorySaver

import chainlit as cl

@tool
async def get_weather(city: Literal["nyc", "sf"]): # Made async
    """Use this to get weather information."""
    if city == "nyc":
        return "It might be cloudy in nyc"
    elif city == "sf":
        return "It's always sunny in sf"
    else:
        raise AssertionError("Unknown city")

tools = [get_weather]

model = init_chat_model(
    "gemma-3-27b-it", model_provider="google_genai"
    )
final_model = init_chat_model("gemma-3-27b-it", model_provider="google_genai")

# model = model.bind_tools(tools).with_config(run_name="Weather Master")
model = model.with_config(run_name="Weather Master")
final_model = final_model.with_config(tags=["final_stream"])

tool_node = ToolNode(tools=tools)

def should_continue(state: MessagesState) -> Literal["tools", "final"]:
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        return "tools"
    return "final"

# 4. Make nodes fully asynchronous 
async def call_model(state: MessagesState):
    messages = state["messages"]
    response = await model.ainvoke(messages) # Use ainvoke
    return {"messages": [response]}

async def call_final_model(state: MessagesState):
    messages = state["messages"]
    last_ai_message = messages[-1]
    response = await final_model.ainvoke( # Use ainvoke
        [
            # SystemMessage(content="Rewrite this in the voice of Al Roker"),
            # HumanMessage(content=last_ai_message.content),
            HumanMessage(
                content=f"Rewrite this in the voice of Al Roker: {last_ai_message.content}"),
        ]
    )
    response.id = last_ai_message.id
    return {"messages": [response]}

builder = StateGraph(MessagesState)

builder.add_node("agent", call_model)
builder.add_node("tools", tool_node)
builder.add_node("final", call_final_model)

builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", should_continue)
builder.add_edge("tools", "agent")
builder.add_edge("final", END)

# 5. Attach the checkpointer so thread_id actually works
memory = MemorySaver()
graph = builder.compile(checkpointer=memory)

@cl.on_message
async def on_message(msg: cl.Message):
    config = {"configurable": {"thread_id": cl.context.session.id}}
    active_steps = {}
    final_answer = cl.Message(content="")

    async for event in graph.astream_events(
        {"messages": [HumanMessage(content=msg.content)]},
        version="v2", 
        config=config
    ):
        kind = event["event"]
        name = event["name"] # Now uses your custom "run_name"
        run_id = event["run_id"]

        # 1. Handle "Thoughts" (Intermediate LLM calls)
        if kind == "on_chat_model_start" and "final_stream" not in event.get("tags", []):
            async with cl.Step(name=name, type="tool") as step:
                active_steps[run_id] = step

        # 2. Handle Tool Uses
        elif kind == "on_tool_start":
            async with cl.Step(name=f"Tool: {name}", type="tool") as step:
                active_steps[run_id] = step

        # 3. Stream content to the correct place
        elif kind == "on_chat_model_stream":
            content = event["data"]["chunk"].content
            if not content: continue

            if "final_stream" in event.get("tags", []):
                await final_answer.stream_token(content)
            elif run_id in active_steps:
                await active_steps[run_id].stream_token(content)

        # 4. Cleanup/Close steps
        elif kind in ["on_chat_model_end", "on_tool_end"]:
            if run_id in active_steps:
                await active_steps[run_id].update()
                del active_steps[run_id]

    await final_answer.update()
    