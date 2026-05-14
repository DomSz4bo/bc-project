from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any

from loguru import logger

from cli.utils import deserialize_values, save_to_json, serialize_snapshot

if TYPE_CHECKING:
    from cli.run_cli import InteractiveCLI

THREAD_PREFIX_LENGTH = 8


class CommandBase(ABC):
    usage_template: str
    help_description: str

    def __init__(self, command: str):
        self.command = command

    @abstractmethod
    async def handle(self, cli: InteractiveCLI, *args) -> bool: ...

    @property
    def usage(self) -> str:
        return self.usage_template.format(self.command)


class Exit(CommandBase):
    help_description = "Exit the CLI"
    usage_template = ""

    async def handle(self, cli: InteractiveCLI, *args) -> bool:
        """Signals the CLI to exit."""
        return True


class SaveBase:
    usage_template = "Usage: {}  [ filename ]"

    @staticmethod
    def get_save_filename(args: tuple[str], fallback_template: str, thread_id: str):
        if args:
            filename: str = args[0]
            if not filename.lower().endswith(".json"):
                filename += ".json"
        else:
            thread_prefix = thread_id[:THREAD_PREFIX_LENGTH]
            filename = fallback_template.replace("{id}", thread_prefix)

        return filename


class SaveState(CommandBase, SaveBase):
    help_description = "Save the current state of the workflow"

    async def handle(self, cli: InteractiveCLI, *args) -> bool:
        """Saves the current state of the workflow to a JSON file."""
        filename = self.get_save_filename(args, "state_{id}.json", cli.thread_id)
        filepath = cli.save_dir / filename

        state = cli.graph.get_state(cli.graph_config)
        serialized_state = serialize_snapshot(state)
        try:
            save_to_json(serialized_state, filepath)
        except FileNotFoundError:
            cli.console.print(
                "  [red]Error:[/red] Please provide a valid filename.",
                f"  {self.usage}",
                sep="\n",
            )
            return False

        relative_path = cli.get_relative_path(filepath)
        cli.console.print(f"  ➜  Saved current state to [blue]{relative_path}[/blue]")
        return False


class SaveHistory(CommandBase, SaveBase):
    help_description = "Save the full state history of the workflow"

    async def handle(self, cli: InteractiveCLI, *args) -> bool:
        """Saves the full state history of the workflow to a JSON file."""
        filename = self.get_save_filename(args, "history_{id}.json", cli.thread_id)
        filepath = cli.save_dir / filename

        history = list(cli.graph.get_state_history(cli.graph_config))
        serialized_history = [serialize_snapshot(s) for s in history]
        try:
            save_to_json(serialized_history, filepath)
        except FileNotFoundError:
            cli.console.print(
                "  [red]Error:[/red] Please provide a valid filename.",
                f"  {self.usage}",
                sep="\n",
            )
            return False

        relative_path = cli.get_relative_path(filepath)
        cli.console.print(
            f"  ➜  Saved full state history to [blue]{relative_path}[/blue]"
        )
        return False


class ListSkills(CommandBase):
    help_description = "List all available skills"
    usage_template = ""

    async def handle(self, cli: InteractiveCLI, *args):
        """Lists all available skills."""
        skills = cli.skills_manager.get_all_skills()
        if not skills:
            cli.console.print("  [yellow]No skills currently available.[/yellow]")
            return False

        cli.console.print("\n  [bold]Available Skills:[/bold]")
        for skill in skills:
            name = skill["name"]
            description = skill["description"]
            cli.console.print(f"  [cyan]{name}[/cyan]: {description}")
        cli.console.print()
        return False


class ReloadSkills(CommandBase):
    help_description = "Reload Supervisor agent skills"
    usage_template = ""

    async def handle(self, cli: InteractiveCLI, *args) -> bool:
        """Reloads Agent skills."""
        cli.skills_manager.reload_skills()
        cli.console.print("\n  [green]✓ Agent skills reloaded successfully.[/green]\n")
        return False


class LoadState(CommandBase):
    help_description = "Load a saved state from a file"
    usage_template = (
        "Usage: {} filename  [ state_idx ]\n"
        "      state_idx  -  Index of state in a full history file, numbered from most recent as 0 (default)"
    )

    def _resolve_filepath(self, cli: InteractiveCLI, filename: str) -> Path:
        filepath = cli.save_dir / filename
        if not filepath.exists():
            filepath = cli.working_directory / filename
        return filepath

    def _print_no_args(self, cli: InteractiveCLI) -> None:
        cli.console.print(
            "  [red]Error:[/red] Please provide the path to the state JSON file.",
            f"  {self.usage}",
            sep="\n",
        )

    def _log_file_not_found(self, filename: str) -> None:
        logger.info(f"Failed to load state, could not find file {filename}.")

    def _print_file_not_found(self, cli: InteractiveCLI, filename: str) -> None:
        cli.console.print(
            f"  [red]Error:[/red] Could not find file: [bold]{filename}[/bold]"
        )

    def _log_failed_to_decode_json(self, filename: str, exception: Exception) -> None:
        logger.info(f"Failed to deserialize json from {filename}.")
        logger.debug(
            f"State JSON loading raised {type(exception).__name__}: {exception}"
        )

    def _print_failed_to_decode_json(self, cli: InteractiveCLI) -> None:
        cli.console.print("  [red]Error:[/red] Failed to load state - invalid JSON format.")

    def _log_load_failure(self, filename: str, exc: Exception) -> None:
        logger.info(f"Failed to load state from {filename}.")
        logger.debug(f"State loading raised {type(exc).__name__}: {exc}")

    def _print_load_failure(self, cli: InteractiveCLI) -> None:
        cli.console.print(
            "  [red]Error:[/red] Failed to load state - make sure the file is a valid state save."
        )

    def _print_loading_success(self, cli: InteractiveCLI, filename: str) -> None:
        filepath = self._resolve_filepath(cli, filename)
        relative_path = cli.get_relative_path(filepath)
        cli.console.print(
            f"  [green]✓ Successfully loaded state from:[/green] [blue]{relative_path}[/blue]"
        )

    def _load_json(self, filepath: str) -> Any:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data

    def _extract_data(self, cli: InteractiveCLI, filename: str) -> Any | None:
        filepath = self._resolve_filepath(cli, filename)

        if not filepath.exists():
            raise FileNotFoundError(f"File with name {filename} does not exist")

        try:
            data = self._load_json(filepath)
        except json.JSONDecodeError as json_exc:
            raise json_exc

        return data

    def _data_is_from_history_file(self, data: Any) -> bool:
        return isinstance(data, list)

    class _StateUpdateError(Exception):
        def __init__(self, error_source: Exception):
            self.error_source = error_source
            super().__init__(error_source)

    def _update_state(self, cli: InteractiveCLI, state_data: Any):
        if not isinstance(state_data, dict):
            raise self._StateUpdateError(TypeError())
        
        try:
            saved_state = deserialize_values(state_data["values"])
            cli._create_new_config()
            cli.graph.update_state(cli.graph_config, saved_state)
        except (KeyError, ValueError) as state_ecx:
            raise self._StateUpdateError(state_ecx)

        if "use_case" in saved_state:
            cli.current_use_case = saved_state["use_case"]
        if "sequence_diagram" in saved_state:
            cli.current_sequence_diagram = saved_state["sequence_diagram"]
        cli._save_output()

    def _load_state(self, cli: InteractiveCLI, filename: str, state_idx: int) -> None:
        state_data = self._extract_data(cli, filename)

        if self._data_is_from_history_file(state_data) and state_idx < len(state_data):
            state_data = state_data[state_idx]

        self._update_state(cli, state_data)

    async def handle(self, cli: InteractiveCLI, *args) -> bool:
        """Loads a saved state from a JSON file."""
        if not args:
            self._print_no_args(cli)
            return False

        filename = args[0]
        state_idx = int(args[1]) if len(args) > 1 else 0

        try:
            self._load_state(cli, filename, state_idx)
        except FileNotFoundError:
            self._log_file_not_found(filename)
            self._print_file_not_found(cli, filename)
        except json.JSONDecodeError as json_exc:
            self._log_failed_to_decode_json(filename, json_exc)
            self._print_failed_to_decode_json(cli)
        except self._StateUpdateError as state_exc:
            self._log_load_failure(filename, state_exc.error_source)
            self._print_load_failure(cli)
        else:
            filepath = self._resolve_filepath(cli, filename)
            relative_path = cli.get_relative_path(filepath)
            cli.console.print(
                f"  [green]✓ Successfully loaded state from:[/green] [blue]{relative_path}[/blue]"
            )

        return False


class Help(CommandBase):
    help_description = "Show a help message for the CLI"
    usage_template = ""

    def _construct_help_message(self, command_map: dict[str, CommandBase]) -> str:
        message = "[bold]Commands:[/bold]\n"
        for command, action in command_map.items():
            message += f" {command} - {action.help_description}\n"
            usage_help = action.usage
            if usage_help:
                message += f"   {usage_help}\n"
        return message

    async def handle(self, cli: InteractiveCLI, *args) -> bool:
        """Print help message for cli commands."""
        help_message = self._construct_help_message(cli.commands_map)
        cli.console.print(help_message)
        return False
