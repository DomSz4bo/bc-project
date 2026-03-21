import asyncio
import uuid
from pathlib import Path
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style

from cli.commands import handle_exit, handle_save, handle_save_full
from src.graph.workflow import create_graph


class InteractiveCLI:
    """
    Interactive CLI for testing the LangGraph workflow.
    """

    def __init__(self):
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

    def _setup_paths(self):
        """Initializes configuration and history paths."""
        self.working_directory = Path.cwd()
        self.config_dir = self.working_directory / ".app_cli"
        self.config_dir.mkdir(exist_ok=True)
        self.save_dir = self.config_dir / "saved_states"
        self.save_dir.mkdir(exist_ok=True)
        self.history_file = self.config_dir / "history"
        self.output_file = self.config_dir / "output.md"

    def get_relative_path(self, filepath: Path):
        """Returns the relative path from the CLI's working directory."""
        return filepath.relative_to(self.working_directory)

    def _setup_commands(self):
        """Maps CLI commands to their handler functions."""
        self.commands_map = {
            "/exit": handle_exit,
            "/save": handle_save,
            "/save-full": handle_save_full,
        }

    def _setup_ui(self):
        """Initializes prompt_toolkit session, styles, and completers."""
        commands = list(self.commands_map.keys())
        commands_completer = WordCompleter(commands, ignore_case=True, sentence=True)

        style = Style.from_dict(
            {
                "prompt": "ansicyan bold",
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
            mouse_support=True,
        )

    def _save_output(self):
        """Saves current use case and sequence diagram to output.md."""
        with open(self.output_file, "w", encoding="utf-8") as f:
            f.write("# Design Lab Output\n\n## Use Case\n\n")
            f.write(self.current_use_case or "Not yet generated.")
            f.write("\n\n## Sequence Diagram\n\n")
            f.write(self.current_sequence_diagram or "Not yet generated.")

    def _get_toolbar(self):
        """Generates the bottom toolbar text."""
        return HTML(
            " Submit: <key>[Alt+Enter]</key> | "
            "New Line: <key>[Enter]</key> | "
            "<key>[Ctrl+D]</key> to quit "
        )

    async def _handle_command(self, user_input: str) -> bool:
        """
        Executes a slash command. Returns True if the CLI should exit.
        """
        action = self.commands_map.get(user_input)
        if action:
            return await action(cli=self)

        print(f"\033[91mUnknown command: {user_input}\033[0m")
        return False

    async def _execute_workflow(self, user_input: str):
        """Streams events from the LangGraph workflow."""
        input_state = {"messages": [HumanMessage(content=user_input)]}
        print("\n" + "-" * 20 + " Workflow Execution " + "-" * 20)

        graph_context = {
            "max_revisions": 1,
            "working_directory": self.working_directory,
        }

        async for event in self.graph.astream(
            input_state,
            config=self.graph_config,
            context=graph_context,
            stream_mode="updates",
        ):
            for node_name, updates in event.items():
                self._process_node_updates(node_name, updates)

        print("-" * 60 + "\n")

    def _process_node_updates(self, node_name: str, updates: dict[str, Any]):
        """Processes and prints updates from a single workflow node."""
        print(f"[{node_name}] running...")

        if "next_step" in updates:
            print(f"  ➜ next_step: {updates['next_step']}")
        if "supervisor_phase" in updates:
            print(f"  ➜ phase: {updates['supervisor_phase']}")
        if "critic_verdict" in updates:
            print(f"  ➜ critic: {updates['critic_verdict']}")
        if "critic_feedback" in updates:
            print(f"  ➜ feedback: {updates['critic_feedback']}")

        if "use_case" in updates or "sequence_diagram" in updates:
            if "use_case" in updates:
                self.current_use_case = updates["use_case"]
            if "sequence_diagram" in updates:
                self.current_sequence_diagram = updates["sequence_diagram"]
            self._save_output()
            print(f"  ➜ Updated {self.get_relative_path(self.output_file)}")

        if "messages" in updates:
            last_msg = updates["messages"][-1]
            if isinstance(last_msg, AIMessage):
                print(f"\nAssistant: {last_msg.content}\n")

    async def run(self):
        """Primary execution loop for the CLI."""
        print("=" * 50)
        print("🚀 WORKFLOW INTERACTIVE CLI")
        print(f"Session ID: {self.thread_id}")
        print(f"History saved to: {self.history_file}")
        print("=" * 50 + "\n")

        while True:
            try:
                user_input: str = await self.session.prompt_async(
                    HTML("<prompt>User > </prompt>"),
                    multiline=True,
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
                print(f"\n❌ \033[91mError ({type(e).__name__}):\033[0m {e}")
        print("\n\033[93mExiting... Goodbye!\033[0m")


def main():
    """Synchronous entry point for the CLI"""
    cli = InteractiveCLI()
    try:
        asyncio.run(cli.run())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
