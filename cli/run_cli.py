import asyncio
import sys
import traceback
import uuid
import warnings
from os.path import samefile
from pathlib import Path
from typing import Any

from langchain_core.globals import set_verbose
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import (
    CustomStreamPart,
    MessagesStreamPart,
    StreamPart,
    UpdatesStreamPart,
)
from loguru import logger
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style as PromptStyle
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from cli.commands import (
    CommandBase,
    Exit,
    Help,
    ListSkills,
    LoadState,
    ReloadSkills,
    SaveHistory,
    SaveState,
)
from src.graph.node_names import Nodes
from src.graph.state import GraphContext
from src.graph.workflow import create_graph
from src.utils.skills import SkillManager
from src.utils.streaming import CustomStreamData

set_verbose(False)
SHOW_STATE_UPDATES = True

logger.remove()
logger.add(".app_cli/logs/logs_{time:YYYY-MM-DD_HH-mm-ss}.log")

NODES_OF_INTEREST = [
    Nodes.SUPERVISOR,
    Nodes.ANALYST,
    Nodes.ARCHITECT,
    Nodes.CRITIC,
    Nodes.SCAFFOLDER,
    Nodes.TDD,
    Nodes.ENGINEER,
    Nodes.QA,
]


class InteractiveCLI:
    """
    Interactive CLI for testing the LangGraph workflow.
    """

    def __init__(self):
        self.console = Console()
        self.graph = create_graph()
        self._create_new_config()

        self.current_use_case: str | None = None
        self.current_sequence_diagram: str | None = None

        self._setup_paths()
        self._setup_commands()
        self._setup_ui()
        self._setup_skills()

    def _create_new_config(self):
        self.thread_id = str(uuid.uuid4())
        self.graph_config: RunnableConfig = {
            "configurable": {"thread_id": self.thread_id}
        }

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
        self.commands_map: dict[str, CommandBase] = {
            "/exit": Exit("/exit"),
            "/save": SaveState("/save"),
            "/save-history": SaveHistory("/save-history"),
            "/load": LoadState("/load"),
            "/skills-list": ListSkills("/skills-list"),
            "/skills-reload": ReloadSkills(".skills-reload"),
            "/help": Help("/help"),
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
        command, *args = user_input.split()
        action = self.commands_map.get(command)
        if action:
            return await action.handle(self, *args)

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
        self.full_response = ""
        self.status = self.console.status(
            "[bold]Starting workflow...[/bold]", spinner="hearts"
        )

        self.console.print("=" * 50)

        try:
            self.status.start()
            async for chunk in self.graph.astream(
                input_state,
                config=self.graph_config,
                context=graph_context,
                stream_mode=["updates", "messages", "custom"],
                version="v2",
                subgraphs=True,
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
            self.status = None

        self.console.print("\n" + "=" * 50 + "\n")

    def _process_custom_stream(self, chunk: CustomStreamPart) -> None:
        data: CustomStreamData = chunk["data"]

        if data.type == "node_name":
            self._print_node_name(data.message)
            return

        style = data.extra.get("style", "bold italic")
        message = Text(data.message, style)

        if data.type == "start":
            self.status.start()
            spinner = data.extra.get("spinner", "dots")
            self.status.update(message, spinner=spinner)
            return

        if data.type == "end":
            self.status.stop()

        if self.full_response and self.full_response[-1] != "\n":
            self.console.print()
        self.console.print(Panel(message))

    def _process_message_stream(self, chunk: MessagesStreamPart) -> None:
        msg_chunk, metadata = chunk["data"]
        node_name = metadata.get("langgraph_node")

        if node_name and node_name != self.active_node:
            if self.full_response and self.full_response[-1] != "\n":
                self.status.stop()
                self.console.print()
            if node_name in NODES_OF_INTEREST:
                self.status.stop()
                self._print_node_name(node_name)
            self.active_node = node_name
            self.full_response = ""

        if msg_chunk.text and node_name == Nodes.SUPERVISOR:
            self.status.stop()
            self.full_response += msg_chunk.text
            self.console.print(msg_chunk.text, end="")

    def _print_node_name(self, node_name: str):
        self.console.print(Panel(f"{node_name}:"), style="bold blue3")

    def _process_update_stream(self, chunk: UpdatesStreamPart) -> None:
        self.status.stop()
        for node_name, updates in chunk["data"].items():
            self._process_node_update(node_name, updates)

    def _process_node_update(self, node_name: str, updates: dict[str, Any]):
        """Processes and prints updates from a single workflow node."""
        if SHOW_STATE_UPDATES:
            self.console.print("\n\n" + "-" * 15 + " update " + "-" * 15)
            self.console.print(f"✓ [{node_name}] completed task.")
        if not updates:
            return

        if SHOW_STATE_UPDATES:
            if "supervisor_phase" in updates:
                self.console.print(f"  ➜ phase: {updates['supervisor_phase']}")
            if "user_intent_summary" in updates:
                self.console.print(f"  ➜ intent: {updates['user_intent_summary']}")
            if "design_notes" in updates:
                self.console.print(f"  ➜ notes: {updates['design_notes']}")
            if "critic_verdict" in updates:
                self.console.print(f"  ➜ critic: {updates['critic_verdict']}")
            if "critic_feedback" in updates:
                self.console.print(f"  ➜ criti_feedback: {updates['critic_feedback']}")
            if "qa_feedback" in updates:
                self.console.print(f"  ➜ qa_feedback: {updates['qa_feedback']}")

        if "use_case" in updates or "sequence_diagram" in updates:
            if "use_case" in updates:
                self.current_use_case = updates["use_case"]
            if "sequence_diagram" in updates:
                self.current_sequence_diagram = updates["sequence_diagram"]
            self._save_output()
            self.console.print(
                f"  ➜ Updated {self.get_relative_path(self.output_file)}"
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
                traceback.print_exc()
                self.console.print(f"\n❌ [red]Error ({type(e).__name__}):[/red] {e}")
        self.console.print("\n[yellow]Exiting... Goodbye![/yellow]")


def main():
    """Synchronous entry point for the CLI"""
    warnings.filterwarnings("ignore")
    sys.tracebacklimit = 0
    cli = InteractiveCLI()
    try:
        asyncio.run(cli.run())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
