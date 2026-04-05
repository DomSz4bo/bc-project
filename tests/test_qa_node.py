from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.prebuilt import ToolNode

from src.agents.qa import qa_tool_node, quality_assurance, reject_implementation


@pytest.fixture
def mock_runtime():
    runtime = MagicMock()
    runtime.context = {"working_directory": Path("."), "max_code_revisions": 3}
    return runtime


@pytest.mark.asyncio
async def test_quality_assurance_revision_limit(mock_runtime):
    state = {
        "qa_revision_count": 3,
        "qa_messages": [],
    }
    with patch("src.agents.qa.llm_with_tools") as _:
        result = await quality_assurance(state, mock_runtime)

    assert result == {"qa_feedback": "LIMIT"}


@pytest.mark.asyncio
async def test_quality_assurance_initial_messages(mock_runtime):
    state = {
        "qa_revision_count": 0,
        "qa_messages": [],
    }

    mock_response = AIMessage(content="I will test this.")

    with (
        patch("src.agents.qa.llm_with_tools") as mock_llm,
        patch("src.agents.qa.extract_project_context") as mock_extract,
    ):
        mock_extract.return_value = MagicMock(
            use_case="Use Case",
            sequence_diagram="Seq Diagram",
            source_code_context="Source Code",
            test_files_context="Test Files",
        )

        mock_llm.ainvoke = AsyncMock(return_value=mock_response)

        result = await quality_assurance(state, mock_runtime)

        assert "qa_messages" in result
        assert len(result["qa_messages"]) == 3
        assert isinstance(result["qa_messages"][0], SystemMessage)
        assert isinstance(result["qa_messages"][1], HumanMessage)
        assert result["qa_messages"][2] == mock_response


@pytest.mark.asyncio
async def test_quality_assurance_existing_messages(mock_runtime):
    existing_messages = [HumanMessage(content="Hello"), AIMessage(content="Hi")]
    state = {
        "qa_revision_count": 1,
        "qa_messages": existing_messages,
    }

    mock_response = AIMessage(content="Next step.")

    with patch("src.agents.qa.llm_with_tools") as mock_llm:
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)

        result = await quality_assurance(state, mock_runtime)

        assert "qa_messages" in result
        assert len(result["qa_messages"]) == 3
        assert result["qa_messages"][:2] == existing_messages
        assert result["qa_messages"][2] == mock_response


@pytest.mark.asyncio
async def test_qa_tool_node_no_messages():
    state = {"qa_messages": []}

    with pytest.raises(ValueError, match="There are no qa_messages"):
        await qa_tool_node(state)


@pytest.mark.asyncio
async def test_qa_tool_node_with_messages():
    mock_ai_message = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "reject_implementation",
                "args": {"feedback": "bad code"},
                "id": "call_1",
            }
        ],
    )
    state = {"qa_messages": [mock_ai_message]}

    mock_tool_message = ToolMessage(content="success", tool_call_id="call_1")

    with patch.object(ToolNode, "ainvoke", new_callable=AsyncMock) as mock_ainvoke:
        mock_ainvoke.return_value = [mock_tool_message]

        result = await qa_tool_node(state)

        assert "qa_messages" in result
        assert result["qa_messages"][-1] == mock_tool_message


@pytest.mark.asyncio
async def test_reject_implementation():
    result = await reject_implementation.ainvoke({"feedback": "Fix this please"})
    assert result == "Handoff to Engineer failed - called with other tools."
