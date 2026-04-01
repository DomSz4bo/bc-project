from __future__ import annotations

from typing import TYPE_CHECKING

from cli.utils import save_to_json, serialize_snapshot

if TYPE_CHECKING:
    from cli.run_cli import InteractiveCLI

THREAD_PREFIX_LENGTH = 8


async def handle_exit(cli: InteractiveCLI) -> bool:
    """Signals the CLI to exit."""
    return True


async def handle_save(cli: InteractiveCLI) -> bool:
    """Saves the current state of the workflow to a JSON file."""
    state = cli.graph.get_state(cli.graph_config)
    thread_prefix = cli.thread_id[:THREAD_PREFIX_LENGTH]
    filepath = cli.save_dir / f"state_{thread_prefix}.json"
    save_to_json(serialize_snapshot(state), filepath)
    relative_path = cli.get_relative_path(filepath)
    cli.console.print(f"  ➜  Saved current state to [blue]{relative_path}[/blue]")
    return False


async def handle_save_full(cli: InteractiveCLI) -> bool:
    """Saves the full state history of the workflow to a JSON file."""
    history = list(cli.graph.get_state_history(cli.graph_config))
    thread_prefix = cli.thread_id[:THREAD_PREFIX_LENGTH]
    filepath = cli.save_dir / f"history_{thread_prefix}.json"
    serialized_history = [serialize_snapshot(s) for s in history]
    save_to_json(serialized_history, filepath)
    relative_path = cli.get_relative_path(filepath)
    cli.console.print(f"  ➜  Saved full state history to [blue]{relative_path}[/blue]")
    return False


async def handle_list_skills(cli: InteractiveCLI):
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
