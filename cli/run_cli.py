import asyncio
import uuid
from os.path import samefile
from pathlib import Path
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import (
    CustomStreamPart,
    MessagesStreamPart,
    StreamPart,
    UpdatesStreamPart,
)
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style as PromptStyle
from rich.console import Console

from cli.commands import (
    handle_exit,
    handle_list_skills,
    handle_reload_skills,
    handle_save,
    handle_save_full,
)
from src.graph.state import GraphContext
from src.graph.workflow import create_graph, SUPERVISOR
from src.utils.skills import SkillManager


class InteractiveCLI:
    """
    Interactive CLI for testing the LangGraph workflow.
    """

    def __init__(self):
        self.console = Console()
        self.graph = create_graph()
        self.thread_id = str(uuid.uuid4())
        self.graph_config: RunnableConfig = {
            "configurable": {"thread_id": self.thread_id}
        }

        self.current_use_case: str | None = None
        self.current_sequence_diagram: str | None = None

        self._setup_paths()
        self._setup_commands()
        self._setup_ui()
        self._setup_skills()

    def _setup_paths(self):
        """Initializes configuration and history paths."""
        self.working_directory = Path.cwd()
        try:
            self.cwd_str = str("~" / self.working_directory.relative_to(Path.home()))
        except ValueError:
            self.cwd_str = str(self.working_directory)
        self.config_dir = self.working_directory / ".app_cli"
        self.config_dir.mkdir(exist_ok=True)
        self.save_dir = self.config_dir / "saved_states"
        self.save_dir.mkdir(exist_ok=True)
        self.history_file = self.config_dir / "history"
        self.output_file = self.config_dir / "output.md"

    def _setup_commands(self):
        """Maps CLI commands to their handler functions."""
        self.commands_map = {
            "/exit": handle_exit,
            "/save": handle_save,
            "/save-full": handle_save_full,
            "/skills-list": handle_list_skills,
            "/skills-reload": handle_reload_skills,
        }

    def _setup_ui(self):
        """Initializes prompt_toolkit session, styles, and completers."""
        commands = list(self.commands_map.keys())
        commands_completer = WordCompleter(commands, ignore_case=True, sentence=True)

        style = PromptStyle.from_dict(
            {
                "prompt": "ansicyan bold",
                "line": "ansigray",
                "bottom-toolbar": "#6446A0 bg:ansiwhite",
                "key": "bold",
                "": "ansigreen",
            }
        )

        self.session = PromptSession(
            history=FileHistory(str(self.history_file)),
            completer=commands_completer,
            complete_while_typing=True,
            style=style,
        )

    def _setup_skills(self):
        root_dirs = [self.working_directory]

        source_directory = Path(__file__).parents[1]
        if not samefile(self.working_directory, source_directory):
            root_dirs.append(source_directory)

        self.skills_manager = SkillManager(root_dirs)
        self.skills_manager.reload_skills()
        for warning in self.skills_manager.get_warnings():
            self.console.print(f"[yellow]Warning:[/yellow] {warning}")

    def get_relative_path(self, path: Path) -> str:
        """Returns the path relative to the working directory if possible."""
        try:
            return str(path.relative_to(self.working_directory))
        except ValueError:
            return str(path)

    def _save_output(self):
        """Saves current use case and sequence diagram to output.md."""
        with open(self.output_file, "w", encoding="utf-8") as f:
            f.write("# Design Lab Output\n\n## Use Case\n\n")
            f.write(self.current_use_case or "Not yet generated.")
            f.write("\n\n## Sequence Diagram\n\n")
            f.write(self.current_sequence_diagram or "Not yet generated.")

    def _get_toolbar(self):
        """Generates the bottom toolbar text."""

        normalized_size = max(len(self.cwd_str), 9)
        return HTML(
            f" {'Workspace': ^{normalized_size}}  .    Submit     .    Exit    \n"
            f" {self.cwd_str: <{normalized_size}}  │"
            "  <key>[Alt+Enter]</key>  │  <key>[Ctrl+D]</key>  "
        )

    def _get_prompt_continuation(self, width, line_number, is_soft_wrap):
        """Prefix for 2nd, 3rd, etc. lines in multiline mode."""
        if is_soft_wrap:
            return HTML(" " * 7)
        return HTML(f"<line>{line_number: >4}   </line>")

    async def _handle_command(self, user_input: str) -> bool:
        """
        Executes a slash command. Returns True if the CLI should exit.
        """
        action = self.commands_map.get(user_input)
        if action:
            return await action(cli=self)

        self.console.print(f"[red]Unknown command:[/red] {user_input}")
        return False

    async def _execute_workflow(self, user_input: str):
        """Streams events from the LangGraph workflow."""
        input_state = {"messages": [HumanMessage(content=user_input)]}

        graph_context: GraphContext = {
            "max_revisions": 3,
            "working_directory": self.working_directory,
            "skill_manager": self.skills_manager,
        }

        self.active_node = None
        self.status = self.console.status(
            "[bold]Starting workflow...[/bold]", spinner="hearts"
        )

        try:
            self.status.start()
            async for chunk in self.graph.astream(
                input_state,
                config=self.graph_config,
                context=graph_context,
                stream_mode=["updates", "messages", "custom"],
                version="v2",
            ):
                chunk: StreamPart
                match chunk["type"]:
                    case "messages":
                        self._process_message_stream(chunk)
                    case "custom":
                        self._process_custom_stream(chunk)
                    case "updates":
                        self._process_update_stream(chunk)
                    case _:
                        pass
        finally:
            self.status.stop()
            self.active_node = None

        self.console.print("-" * 10 + "\n")

    def _process_custom_stream(self, chunk: CustomStreamPart) -> None:
        self.status.start()
        self.status.update("New status", spinner="arc")

    def _process_message_stream(self, chunk: MessagesStreamPart) -> None:
        self.status.stop()
        msg_chunk, metadata = chunk["data"]
        node_name = metadata.get("langgraph_node")

        if node_name and node_name != self.active_node:
            self.active_node = node_name

        if node_name == SUPERVISOR and msg_chunk.content:
            self.console.print(msg_chunk.text, end="")

    def _process_update_stream(self, chunk: UpdatesStreamPart) -> None:
        self.status.start()
        for node_name, update in chunk["data"].items():
            if len(update) > 1:
                raise ValueError("You though it's only a single update.")
            self._process_node_update(node_name, update)
        

    def _process_node_update(self, node_name: str, updates: dict[str, Any]):
        """Processes and prints updates from a single workflow node."""
        self.console.print(f"✓ [{node_name}] completed task.")

        if "supervisor_phase" in updates:
            self.console.print(f"  ➜ phase: {updates['supervisor_phase']}")
        if "critic_verdict" in updates:
            self.console.print(f"  ➜ critic: {updates['critic_verdict']}")
        if "critic_feedback" in updates:
            self.console.print(f"  ➜ feedback: {updates['critic_feedback']}")

        if "use_case" in updates or "sequence_diagram" in updates:
            if "use_case" in updates:
                self.current_use_case = updates["use_case"]
            if "sequence_diagram" in updates:
                self.current_sequence_diagram = updates["sequence_diagram"]
            self._save_output()
            self.console.print(
                f"  ➜ Updated {self.get_relative_path(self.output_file)}"
            )

        if "messages" in updates:
            last_msg = updates["messages"][-1]
            if isinstance(last_msg, AIMessage):
                if node_name == "Supervisor":
                    pass
                elif last_msg.content:
                    self.console.print(
                        f"\nAssistant ({node_name}): {last_msg.content}\n"
                    )

    async def run(self):
        """Primary execution loop for the CLI."""
        self.console.print("\n" + "=" * 50)
        self.console.print("🚀 WORKFLOW INTERACTIVE CLI")
        self.console.print(f"Session ID: {self.thread_id}")
        self.console.print("=" * 50 + "\n")

        while True:
            try:
                user_input: str = await self.session.prompt_async(
                    HTML("<prompt>User > </prompt>"),
                    multiline=True,
                    prompt_continuation=self._get_prompt_continuation,
                    bottom_toolbar=self._get_toolbar,
                )

                user_input = user_input.strip()

                if not user_input:
                    continue

                if user_input.startswith("/"):
                    should_exit = await self._handle_command(user_input)
                    if should_exit:
                        break
                    continue

                await self._execute_workflow(user_input)

            except KeyboardInterrupt:
                continue
            except EOFError:
                break
            except Exception as e:
                self.console.print(f"\n❌ [red]Error ({type(e).__name__}):[/red] {e}")
        self.console.print("\n[yellow]Exiting... Goodbye![/yellow]")


def main():
    """Synchronous entry point for the CLI"""
    cli = InteractiveCLI()
    try:
        asyncio.run(cli.run())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
