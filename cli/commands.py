from typing import Any

from langgraph.graph.state import CompiledStateGraph

from cli.utils import save_to_json, serialize_snapshot

THREAD_PREFIX_LENGTH = 8


async def handle_exit(*args, **kwargs) -> bool:
    print("\n\033[93mExiting... Goodbye!\033[0m")
    return True


async def handle_save(graph: CompiledStateGraph, config: dict[str, Any]) -> bool:
    state = graph.get_state(config)
    thread_prefix = config["configurable"]["thread_id"][:THREAD_PREFIX_LENGTH]
    filename = f"state_{thread_prefix}.json"
    save_to_json(serialize_snapshot(state), filename)
    print(f"  ➜  Saved current state to \033[94m{filename}\033[0m")
    return False


async def handle_save_full(graph: CompiledStateGraph, config: dict[str, Any]) -> bool:
    history = list(graph.get_state_history(config))
    thread_prefix = config["configurable"]["thread_id"][:THREAD_PREFIX_LENGTH]
    filename = f"history_{thread_prefix}.json"
    serialized_history = [serialize_snapshot(s) for s in history]
    save_to_json(serialized_history, filename)
    print(f"  ➜  Saved full state history to \033[94m{filename}\033[0m")
    return False
