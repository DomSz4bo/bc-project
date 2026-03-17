import chainlit as cl
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig

from src.graph.workflow import create_graph 


graph =  create_graph()


@cl.on_message
async def on_message(msg: cl.Message):
    config: RunnableConfig = {"configurable": {"thread_id": cl.context.session.id}}
    active_steps: dict[str, cl.Step] = {}
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
            if not content: 
                continue
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
    