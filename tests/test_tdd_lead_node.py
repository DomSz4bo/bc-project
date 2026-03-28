from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agents.tdd_lead import FileChange, TDDPlan, tdd_lead
from src.graph.state import AgentState


@pytest.mark.asyncio
async def test_tdd_lead_logic(tmp_path):
    working_dir = tmp_path / "project"
    src_dir = working_dir / "src"
    src_dir.mkdir(parents=True)

    (src_dir / "vending_machine.py").write_text("class VendingMachine:\n    pass\n")

    state: AgentState = {
        "use_case": "Use Case Content",
        "sequence_diagram": "Sequence Diagram Content",
        "messages": [],
        "user_intent_summary": "Test",
        "supervisor_phase": "APPROVAL",
        "critic_verdict": "PASS",
        "revision_count": 0,
    }

    mock_runtime = MagicMock()
    mock_runtime.context = {"working_directory": working_dir}

    mock_plan = TDDPlan(
        files=[
            FileChange(
                path="tests/test_vending_machine.py", content="def test_foo(): pass"
            ),
            FileChange(
                path="src/vending_machine.py",
                content="class VendingMachine:\n    def foo(self):\n        pass\n",
            ),
        ]
    )

    with patch("src.agents.tdd_lead.structured_llm") as mock_llm:
        mock_llm.ainvoke = AsyncMock(return_value=mock_plan)

        await tdd_lead(state, mock_runtime)

        test_file = working_dir / "tests/test_vending_machine.py"
        assert test_file.exists()
        assert test_file.read_text() == "def test_foo(): pass"

        source_file = working_dir / "src/vending_machine.py"
        assert source_file.exists()
        assert (
            source_file.read_text()
            == "class VendingMachine:\n    def foo(self):\n        pass\n"
        )


@pytest.mark.asyncio
async def test_tdd_lead_missing_data():
    state: AgentState = {"use_case": None, "sequence_diagram": None, "messages": []}
    mock_runtime = MagicMock()
    mock_runtime.context = {"working_directory": Path(".")}

    with pytest.raises(KeyError, match="No use_case found in state."):
        await tdd_lead(state, mock_runtime)
