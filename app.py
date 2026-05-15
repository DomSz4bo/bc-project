import os
import traceback
import uuid
from pathlib import Path
from typing import Any

import chainlit as cl
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import (
    CustomStreamPart,
    MessagesStreamPart,
    StreamPart,
    UpdatesStreamPart,
)

from src.graph.node_names import Nodes
from src.graph.state import GraphContext
from src.graph.workflow import create_graph
from src.utils.mermaid import generate_mermaid_url
from src.utils.skills import SkillManager
from src.utils.streaming import CustomStreamData

shared_graph = create_graph()

SHOW_SUBAGENT_OUTPUTS = True
SHOW_STATE_UPDATES = False


class WorkflowApp:
    def __init__(self, graph: CompiledStateGraph):
        self.graph = graph
        self.show_nodes = [
            Nodes.SUPERVISOR,
            Nodes.ANALYST,
            Nodes.ARCHITECT,
            Nodes.CRITIC,
            Nodes.SCAFFOLDER,
            Nodes.TDD,
            Nodes.ENGINEER,
            Nodes.QA,
        ]

        self.main_msg: cl.Message | None = None
        self.current_custom_step: cl.Step | None = None
        self.current_node_step: cl.Step | None = None

    async def on_chat_start(self):
        thread_id = str(uuid.uuid4())
        graph_config: RunnableConfig = {"configurable": {"thread_id": thread_id}}

        working_directory_str = os.environ.get("BC_APP_CWD")
        if working_directory_str:
            print(f"Captured CWD: {working_directory_str}")
            working_directory = Path(working_directory_str)
        else:
            print(f"Falling back to cwd: {os.getcwd()}")
            working_directory = Path.cwd()

        root_dirs = [working_directory]
        source_directory = Path(__file__).parent
        if not os.path.samefile(working_directory, source_directory):
            root_dirs.append(source_directory)

        skills_manager = SkillManager(root_dirs)
        skills_manager.reload_skills()

        graph_context: GraphContext = {
            "max_revisions": 3,
            "working_directory": working_directory,
            "skill_manager": skills_manager,
        }

        cl.user_session.set("graph_config", graph_config)
        cl.user_session.set("graph_context", graph_context)

    async def _process_custom_stream(self, chunk: CustomStreamPart) -> None:
        data: CustomStreamData = chunk["data"]
        if data.type == "start":
            if self.current_custom_step:
                await self.current_custom_step.remove()
            self.current_custom_step = cl.Step(name=data.message)
            self.current_custom_step.status = "run"
            await self.current_custom_step.send()

        elif data.type == "end" and self.current_custom_step:
            self.current_custom_step.status = "success"
            if data.extra.get("type", "") == "tool":
                self.current_custom_step.name = data.extra.get("title", "Unknown Tool")
                if "output" in data.extra:
                    self.current_custom_step.output = data.extra.get("output")
            else:
                self.current_custom_step.name = data.message
            await self.current_custom_step.update()
            self.current_custom_step = None

        elif data.type == "message":
            step = cl.Step()
            if data.extra.get("type", "") == "tool":
                step.name = data.extra.get("title", "Unknown Tool")
                if "output" in data.extra:
                    step.output = data.extra.get("output")
            else:
                step.name = data.message
            step.status = "success"
            await step.send()

        elif self.current_custom_step:
            if self.current_custom_step.output:
                self.current_custom_step.output += f"\n\n{data.message}"
            else:
                self.current_custom_step.output = data.message
            await self.current_custom_step.update()

    async def _process_message_stream(self, chunk: MessagesStreamPart) -> None:
        msg_chunk, metadata = chunk["data"]
        node_name = metadata.get("langgraph_node")

        if node_name == Nodes.SUPERVISOR:
            if msg_chunk.text:
                if not self.main_msg:
                    self.main_msg = cl.Message(content="")
                await self.main_msg.stream_token(msg_chunk.text)

            if self.current_node_step:
                self.current_node_step.status = "success"
                await self.current_node_step.send()
                self.current_node_step = None

        elif node_name not in self.show_nodes:
            if self.main_msg:
                await self.main_msg.send()
                self.main_msg = None

            if self.current_node_step:
                self.current_node_step.status = "success"
                await self.current_node_step.send()
                self.current_node_step = None
        elif SHOW_SUBAGENT_OUTPUTS:
            if not self.current_node_step:
                self.current_node_step = cl.Step(node_name)

            elif node_name != self.current_node_step.name:
                self.current_node_step.status = "success"
                await self.current_node_step.send()
                self.current_node_step = cl.Step(node_name)

            await self.current_node_step.stream_token(
                msg_chunk.text if msg_chunk.text else ""
            )

    async def _process_update_stream(self, chunk: UpdatesStreamPart) -> None:
        if self.current_custom_step:
            await self.current_custom_step.remove()
            self.current_custom_step = None

        for node_name, updates in chunk["data"].items():
            if not updates:
                continue

            if SHOW_STATE_UPDATES:
                node_step = cl.Step(name=f"✓ [{node_name}] completed task")
                node_step.status = "success"
                await node_step.send()

                update_content = self._process_node_update(node_name, updates)
                if update_content:
                    node_step.output = update_content
                    await node_step.update()

            if "use_case" in updates and updates["use_case"]:
                await cl.Message(updates["use_case"], "Design Lab").send()

            if "sequence_diagram" in updates and updates["sequence_diagram"]:
                encoded_mmd = generate_mermaid_url(updates["sequence_diagram"], "base")
                img_url = "https://mermaid.ink/img/" + encoded_mmd
                image = cl.Image(
                    name="Sequence Diagram",
                    display="inline",
                    size="small",
                    url=img_url,
                )
                editor_url = f"https://mermaid.ai/live/edit#{encoded_mmd}"
                await cl.Message(
                    content=f"[Mermaid editor]({editor_url})", elements=[image]
                ).send()

    def _process_node_update(
        self, node_name: str, updates: dict[str, Any]
    ) -> str | None:
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

    async def handle_message(self, message: cl.Message):
        graph_config: RunnableConfig = cl.user_session.get("graph_config")
        graph_context: GraphContext = cl.user_session.get("graph_context")

        input_state = {"messages": [HumanMessage(content=message.content)]}

        self.main_msg = None
        self.current_custom_step = None
        self.current_node_step = None

        try:
            async for chunk in self.graph.astream(
                input_state,
                config=graph_config,
                context=graph_context,
                stream_mode=["updates", "messages", "custom"],
                version="v2",
                subgraphs=True,
            ):
                chunk: StreamPart

                if chunk["type"] == "custom":
                    await self._process_custom_stream(chunk)

                elif chunk["type"] == "messages":
                    await self._process_message_stream(chunk)

                elif chunk["type"] == "updates":
                    await self._process_update_stream(chunk)

            if self.main_msg:
                if not self.main_msg.content:
                    self.main_msg.content = "Workflow step completed."
                await self.main_msg.send()
            else:
                await cl.Message(content="Workflow step completed.").send()

        except Exception as e:
            if self.current_custom_step:
                self.current_custom_step.status = "failed"
                self.current_custom_step.output = str(e)
                await self.current_custom_step.update()

            if self.current_node_step:
                self.current_node_step.status = "failed"
                self.current_node_step.output = str(e)
                await self.current_node_step.update()

            traceback.print_exc()

            await cl.ErrorMessage(
                content=f"An error occurred in the workflow: {str(e)}"
            ).send()


@cl.on_chat_start
async def on_chat_start():
    app = WorkflowApp(shared_graph)
    await app.on_chat_start()
    cl.user_session.set("app", app)


@cl.on_message
async def on_message(message: cl.Message):
    app: WorkflowApp = cl.user_session.get("app")
    await app.handle_message(message)
