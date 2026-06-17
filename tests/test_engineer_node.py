from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import HumanMessage

from src.agents.engineer import HUMAN_PROMPT, SYSTEM_PROMPT, engineer
from src.graph.state import GraphContext


@pytest.fixture
def mock_runtime():
    runtime = MagicMock()
    runtime.context = {"working_directory": Path(".")}
    return runtime


@pytest.fixture
def mock_config():
    config = MagicMock()
    return config


@pytest.fixture
def mock_context():
    context = MagicMock()
    context.use_case = "Test Use Case"
    context.sequence_diagram = "Test Sequence Diagram"
    context.source_code_context = "Test Source Code"
    context.test_files_context = "Test Files Context"
    return context


@pytest.mark.asyncio
async def test_engineer_normal_execution(mock_runtime, mock_context, mock_config):
    state = {}

    with (
        patch(
            "src.agents.engineer.extract_project_context", return_value=mock_context
        ) as mock_extract,
        patch("src.agents.engineer.get_mcp_client") as mock_get_client,
        patch(
            "src.agents.engineer.load_mcp_tools", new_callable=AsyncMock
        ) as mock_load_tools,
        patch("src.agents.engineer.create_agent") as mock_create_agent,
        patch("src.agents.engineer.run_tests", "mock_run_tests_tool"),
        patch("src.agents.engineer.get_stream_writer") as _,
    ):
        mock_session_context = AsyncMock()
        mock_client = MagicMock()
        mock_client.session.return_value = mock_session_context
        mock_get_client.return_value = mock_client

        mock_load_tools.return_value = ["mock_file_tool"]

        mock_agent = AsyncMock()
        mock_create_agent.return_value = mock_agent

        result = await engineer(state, mock_runtime, mock_config)

        assert result == {}
        mock_extract.assert_called_once_with(state, Path("."))

        mock_create_agent.assert_called_once()
        _, kwargs = mock_create_agent.call_args
        assert kwargs["system_prompt"] == SYSTEM_PROMPT
        assert kwargs["context_schema"] == GraphContext

        mock_agent.ainvoke.assert_called_once()
        call_args = mock_agent.ainvoke.call_args[0][0]
        assert "messages" in call_args
        messages = call_args["messages"]
        assert len(messages) == 1
        assert isinstance(messages[0], HumanMessage)

        expected_content = HUMAN_PROMPT.format(
            use_case="Test Use Case",
            sequence_diagram="Test Sequence Diagram",
            source_code_context="Test Source Code",
            tests_context="Test Files Context",
        )
        assert messages[0].content == expected_content


@pytest.mark.asyncio
async def test_engineer_with_qa_feedback(mock_runtime, mock_context, mock_config):
    state = {"qa_feedback": "Tests failed on line 42"}

    with (
        patch("src.agents.engineer.extract_project_context", return_value=mock_context),
        patch("src.agents.engineer.get_mcp_client") as mock_get_client,
        patch("src.agents.engineer.load_mcp_tools", new_callable=AsyncMock),
        patch("src.agents.engineer.create_agent") as mock_create_agent,
        patch("src.agents.engineer.get_stream_writer") as _,
    ):
        mock_session_context = AsyncMock()
        mock_client = MagicMock()
        mock_client.session.return_value = mock_session_context
        mock_get_client.return_value = mock_client

        mock_agent = AsyncMock()
        mock_create_agent.return_value = mock_agent

        await engineer(state, mock_runtime, mock_config)

        mock_agent.ainvoke.assert_called_once()
        call_args = mock_agent.ainvoke.call_args[0][0]
        messages = call_args["messages"]

        assert "🚨 QUALITY ASSURANCE FEEDBACK" in messages[0].content
        assert "Tests failed on line 42" in messages[0].content
        assert "Test Use Case" in messages[0].content
