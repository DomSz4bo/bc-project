from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agents.scaffolder import Component, ScaffoldPlan, scaffolder
from src.graph.state import AgentState


@pytest.mark.asyncio
async def test_scaffolder_logic(tmp_path):
    # Setup
    working_dir = tmp_path / "project"
    working_dir.mkdir()

    state: AgentState = {
        "use_case": """
### Use Case: Test
**Primary Actor:** User
**Secondary Actors:** 
* **External API** (Mock)
""",
        "sequence_diagram": """```mermaid
sequenceDiagram
    actor User
    participant System
    participant External API
    User->>System: Do something
    System->>External API: Call
```""",
        "messages": [],
        "user_intent_summary": "Test",
        "supervisor_phase": "APPROVAL",
        "critic_verdict": "PASS",
        "revision_count": 0,
    }

    mock_runtime = MagicMock()
    mock_runtime.context = {"working_directory": working_dir}

    mock_plan = ScaffoldPlan(
        components=[Component(class_name="System", file_name="system")]
    )

    with patch("src.agents.scaffolder.structured_llm") as mock_llm:
        mock_llm.ainvoke = AsyncMock(return_value=mock_plan)

        await scaffolder(state, mock_runtime)

        src_dir = working_dir / "src"
        assert src_dir.exists()
        assert (src_dir / "__init__.py").exists()
        assert (src_dir / "system.py").exists()

        with open(src_dir / "system.py", "r") as f:
            content = f.read()
            assert "class System:" in content


@pytest.mark.asyncio
async def test_scaffolder_none_data():
    state: AgentState = {
        "use_case": None,
        "sequence_diagram": None,
        "messages": [],
        "user_intent_summary": "Test",
        "supervisor_phase": "APPROVAL",
        "critic_verdict": "PASS",
        "revision_count": 0,
    }
    mock_runtime = MagicMock()
    mock_runtime.context = {"working_directory": Path(".")}
    with pytest.raises(ValueError, match="Missing use_case or sequence_diagram"):
        await scaffolder(state, mock_runtime)


@pytest.mark.asyncio
async def test_scaffolder_missing_keys():
    state = {}
    mock_runtime = MagicMock()
    mock_runtime.context = {"working_directory": Path(".")}
    with pytest.raises(ValueError, match="Missing use_case or sequence_diagram"):
        await scaffolder(state, mock_runtime)
