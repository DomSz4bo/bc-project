from __future__ import annotations

import json
from typing import TYPE_CHECKING

from loguru import logger

from cli.utils import deserialize_values, save_to_json, serialize_snapshot

if TYPE_CHECKING:
    from cli.run_cli import InteractiveCLI

THREAD_PREFIX_LENGTH = 8


async def handle_exit(cli: InteractiveCLI, *args) -> bool:
    """Signals the CLI to exit."""
    return True


async def handle_save(cli: InteractiveCLI, *args) -> bool:
    """Saves the current state of the workflow to a JSON file."""
    state = cli.graph.get_state(cli.graph_config)
    thread_prefix = cli.thread_id[:THREAD_PREFIX_LENGTH]
    filepath = cli.save_dir / f"state_{thread_prefix}.json"
    save_to_json(serialize_snapshot(state), filepath)
    relative_path = cli.get_relative_path(filepath)
    cli.console.print(f"  ➜  Saved current state to [blue]{relative_path}[/blue]")
    return False


async def handle_save_full(cli: InteractiveCLI, *args) -> bool:
    """Saves the full state history of the workflow to a JSON file."""
    history = list(cli.graph.get_state_history(cli.graph_config))
    thread_prefix = cli.thread_id[:THREAD_PREFIX_LENGTH]
    filepath = cli.save_dir / f"history_{thread_prefix}.json"
    serialized_history = [serialize_snapshot(s) for s in history]
    save_to_json(serialized_history, filepath)
    relative_path = cli.get_relative_path(filepath)
    cli.console.print(f"  ➜  Saved full state history to [blue]{relative_path}[/blue]")
    return False


async def handle_list_skills(cli: InteractiveCLI, *args):
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


async def handle_reload_skills(cli: InteractiveCLI, *args) -> bool:
    """Reloads Agent skills."""
    cli.skills_manager.reload_skills()
    cli.console.print("\n  [green]✓ Agent skills reloaded successfully.[/green]\n")
    return False


async def handle_load_state(cli: InteractiveCLI, *args) -> bool:
    """Loads a saved state from a JSON file into the graph."""
    if not args:
        cli.console.print(
            "  [red]Error:[/red] Please provide the path to the state JSON file."
        )
        cli.console.print(
            "  Usage: /load <filename_or_path>   [ state_idx (for history file) ]"
        )
        return False

    filename: str = args[0]
    filepath = cli.save_dir / filename
    if not filepath.exists():
        filepath = cli.working_directory / filename

    if not filepath.exists():
        logger.info(f"Failed to load state from {filename}.")
        cli.console.print(
            f"  [red]Error:[/red] Could not find file: [bold]{filename}[/bold]"
        )
        return False

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            state_n = int(args[1]) if len(args) > 1 else 0
            data = data[state_n]

        saved_state = deserialize_values(data["values"])
        cli._create_new_config()

        cli.graph.update_state(cli.graph_config, saved_state)

        if "use_case" in saved_state:
            cli.current_use_case = saved_state["use_case"]
        if "sequence_diagram" in saved_state:
            cli.current_sequence_diagram = saved_state["sequence_diagram"]
        cli._save_output()

        relative_path = cli.get_relative_path(filepath)
        cli.console.print(
            f"  [green]✓ Successfully loaded state from:[/green] [blue]{relative_path}[/blue]"
        )
        return False
    except Exception as e:
        logger.info(f"Failed to load state from {filename}.")
        logger.debug(f"State loading raised {type(e).__name__}: {e}")
        cli.console.print(f"  [red]Error loading state:[/red] {e}")
        return False
