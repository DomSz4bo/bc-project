import json
from pathlib import Path
from typing import Any

from langchain_core.load import dumpd
from langgraph.types import StateSnapshot


def serialize_snapshot(snapshot: StateSnapshot) -> dict[str, Any]:
    """
    Serializes a LangGraph StateSnapshot into a JSON-compatible dictionary.
    """
    return {
        "values": dumpd(snapshot.values),
        "next": snapshot.next,
        "config": snapshot.config,
        "metadata": snapshot.metadata,
    }


def save_to_json(data, filename: Path | str):
    """
    Saves data to a pretty-printed JSON file in the current working directory.
    """
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
