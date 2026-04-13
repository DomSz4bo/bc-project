import asyncio
import uuid
from pathlib import Path
from typing import Any, cast

import chainlit as cl
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import (
    CustomStreamPart,
    MessagesStreamPart,
    StreamPart,
    UpdatesStreamPart,
)

from src.graph.node_names import Nodes
from src.graph.state import GraphContext
from src.graph.workflow import create_graph
from src.utils.skills import SkillManager
from src.utils.streaming import CustomStreamData
from src.utils.mermaid import generate_mermaid_url

graph = create_graph()

show_nodes = [
    Nodes.SUPERVISOR,
    Nodes.ANALYST,
    Nodes.ARCHITECT,
    Nodes.CRITIC,
    Nodes.SCAFFOLDER,
    Nodes.TDD,
    Nodes.ENGINEER,
    Nodes.QA,
]


@cl.on_chat_start
async def on_chat_start():
    thread_id = str(uuid.uuid4())
    graph_config: RunnableConfig = {"configurable": {"thread_id": thread_id}}

    working_directory = Path.cwd()
    skills_manager = SkillManager([working_directory])
    skills_manager.reload_skills()

    graph_context: GraphContext = {
        "max_revisions": 3,
        "working_directory": working_directory,
        "skill_manager": skills_manager,
    }

    cl.user_session.set("graph_config", graph_config)
    cl.user_session.set("graph_context", graph_context)


def _process_node_update(node_name: str, updates: dict[str, Any]) -> str | None:
    """Processes updates and returns formatted string for step display."""
    content_lines = []

    if "supervisor_phase" in updates:
        content_lines.append(f"**Phase:** {updates['supervisor_phase']}")
    if "user_intent_summary" in updates:
        content_lines.append(f"**Intent:** {updates['user_intent_summary']}")
    if "design_notes" in updates:
        content_lines.append(f"**Notes:** {updates['design_notes']}")
    if "critic_verdict" in updates:
        content_lines.append(f"**Critic Verdict:** {updates['critic_verdict']}")
    if "critic_feedback" in updates:
        content_lines.append(f"**Critic Feedback:** {updates['critic_feedback']}")
    if "qa_feedback" in updates:
        content_lines.append(f"**QA Feedback:** {updates['qa_feedback']}")

    if "messages" in updates and updates["messages"]:
        last_msg = updates["messages"][-1]
        if isinstance(last_msg, ToolMessage):
            content_lines.append(
                f"**ToolMessage** ({last_msg.name}): {last_msg.content}"
            )

    if "qa_messages" in updates and updates["qa_messages"]:
        last_msg = updates["qa_messages"][-1]
        if isinstance(last_msg, ToolMessage):
            content_lines.append(
                f"**QAToolMessage** ({last_msg.name}): {last_msg.content}"
            )

    return "\n\n".join(content_lines) if content_lines else None


@cl.on_message
async def on_message(message: cl.Message):
    graph_config = cast(RunnableConfig, cl.user_session.get("graph_config"))
    graph_context = cast(GraphContext, cl.user_session.get("graph_context"))

    input_state = {"messages": [HumanMessage(content=message.content)]}

    main_msg: cl.Message | None = None
    current_custom_step: cl.Step | None = None
    current_node_step: cl.Step | None = None

    async for chunk in graph.astream(
        input_state,
        config=graph_config,
        context=graph_context,
        stream_mode=["updates", "messages", "custom"],
        version="v2",
        subgraphs=False,
    ):
        chunk: StreamPart

        if chunk["type"] == "custom":
            chunk: CustomStreamPart
            data: CustomStreamData = chunk["data"]
            if data.type == "start":
                if current_custom_step:
                    await current_custom_step.remove()
                current_custom_step = cl.Step(name=data.message)
                current_custom_step.status = "run"
                await current_custom_step.send()

            elif data.type == "end" and current_custom_step:
                current_custom_step.status = "success"
                await current_custom_step.update()
                current_custom_step = None

            elif data.type == "message":
                step = cl.Step(name=data.message)
                step.status = "success"
                await step.send()

            elif current_custom_step:
                if current_custom_step.output:
                    current_custom_step.output += f"\n\n{data.message}"
                else:
                    current_custom_step.output = data.message
                await current_custom_step.update()

        elif chunk["type"] == "messages":
            chunk: MessagesStreamPart
            msg_chunk, metadata = chunk["data"]
            node_name = metadata.get("langgraph_node")

            if node_name == Nodes.SUPERVISOR:
                if msg_chunk.text:
                    if not main_msg:
                        main_msg = cl.Message(content="")
                    await main_msg.stream_token(msg_chunk.text)

                if current_node_step:
                    current_node_step.status = "success"
                    await current_node_step.send()
                    current_node_step = None

            elif node_name not in show_nodes:
                if main_msg:
                    await main_msg.send()
                    main_msg = None

                if current_node_step:
                    current_node_step.status = "success"
                    await current_node_step.send()
                    current_node_step = None
            else:
                if not current_node_step:
                    current_node_step = cl.Step(node_name)

                elif node_name != current_node_step.name:
                    current_node_step.status = "success"
                    await current_node_step.send()
                    current_node_step = cl.Step(node_name)

                await current_node_step.stream_token(
                    msg_chunk.text if msg_chunk.text else ""
                )

        elif chunk["type"] == "updates":
            chunk: UpdatesStreamPart
            for node_name, updates in chunk["data"].items():
                node_step = cl.Step(name=f"✓ [{node_name}] completed task")
                node_step.status = "success"
                await node_step.send()

                update_content = _process_node_update(node_name, updates)
                if update_content:
                    node_step.output = update_content
                    await node_step.update()

                if "use_case" in updates:
                    await cl.Message(updates["use_case"], "Design Lab").send()

                if "sequence_diagram" in updates:
                    img_url = generate_mermaid_url(updates["sequence_diagram"], "base")
                    image = cl.Image(
                        name="Sequence Diagram",
                        display="inline",
                        size="small",
                        url=img_url,
                    )
                    await cl.Message(content="", elements=[image]).send()

    if not main_msg.content:
        main_msg.content = "Workflow step completed."

    await main_msg.send()
