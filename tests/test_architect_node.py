from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from src.agents.design_lab.architect import architect, ArchitectOutput
from src.utils.mermaid import ValidationResult


@pytest.mark.asyncio
async def test_architect_generation():
    """
    Verify the architect node generates a sequence diagram from a use case.
    """
    mock_diagram = """```mermaid\nsequenceDiagram
    Alice->>+John: Hello John, how are you?
    Alice->>+John: John, can you hear me?
    John-->>-Alice: Hi Alice, I can hear you!
    John-->>-Alice: I feel great!\n```"""

    mock_response = ArchitectOutput(
        reasoning="mock reason", sequence_diagram=mock_diagram
    )

    with (
        patch("src.agents.design_lab.architect.llm_with_structure") as mock_llm,
        patch("src.agents.design_lab.architect.get_stream_writer") as mock_writer,
    ):
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        mock_writer.return_value = MagicMock(return_value=None)

        state = {
            "use_case": "# USE CASE: Login System\n...",
        }

        mock_runtime = MagicMock()
        mock_runtime.context = {"mmd_syntax_validation_limit": 3}

        command = await architect(state, mock_runtime)
        result = command.update

        assert "sequence_diagram" in result
        assert result["sequence_diagram"] == mock_diagram

        mock_llm.ainvoke.assert_called_once()
        called_messages = mock_llm.ainvoke.call_args[0][0]

        assert isinstance(called_messages[0], SystemMessage)
        assert "System Architect" in called_messages[0].content

        assert isinstance(called_messages[1], HumanMessage)
        assert "USE CASE:" in called_messages[1].content


@pytest.mark.asyncio
async def test_architect_fix_mode():
    """
    Verify the architect node enters fix mode when critic feedback is present.
    """
    mock_diagram = """```mermaid
sequenceDiagram
    Alice->>+John: Hello John, how are you?
    Alice->>+John: John, can you hear me?
    John-->>-Alice: Hi Alice, I can hear you!
    John-->>-Alice: I feel great!\n```"""
    mock_response = ArchitectOutput(
        reasoning="mock reason", sequence_diagram=mock_diagram
    )

    with (
        patch("src.agents.design_lab.architect.llm_with_structure") as mock_llm,
        patch("src.agents.design_lab.architect.get_stream_writer") as mock_writer,
    ):
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        mock_writer.return_value = MagicMock(return_value=None)

        state = {
            "use_case": "# USE CASE: Login System\n...",
            "sequence_diagram": """```mermaid
sequenceDiagram
    Alice->>John: Hello John, how are you?
    Alice->>John: John, can you hear me?
    John-->>Alice: Hi Alice, I can hear you!
    John-->>Alice: I feel great!```""",
            "critic_verdict": "FAIL",
            "critic_feedback": "Missing validation step.",
        }

        mock_runtime = MagicMock()
        mock_runtime.context = {}

        command = await architect(state, mock_runtime)
        result = command.update

        assert result["sequence_diagram"] == mock_diagram

        mock_llm.ainvoke.assert_called_once()
        called_messages = mock_llm.ainvoke.call_args.args[0]

        assert "```mermaid\n" in called_messages[2].content
        assert "Missing validation step." in called_messages[3].content


@pytest.mark.asyncio
async def test_architect_missing_use_case():
    """
    Verify the architect fails if no use case is provided.
    """
    mock_response = AIMessage(content="Nothing")
    with (
        patch("src.agents.design_lab.architect.llm_with_structure") as mock_llm,
        patch("src.agents.design_lab.architect.get_stream_writer") as mock_writer,
    ):
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        mock_writer.return_value = MagicMock(return_value=None)

        state = {}
        mock_runtime = MagicMock()
        mock_runtime.context = {}
        with pytest.raises(ValueError, match="No use_case"):
            await architect(state, mock_runtime)


@pytest.mark.asyncio
async def test_architect_fix_syntax():
    """
    Veriy that the syntax validation cycle is initiated.
    """
    mock_responses = [
        ArchitectOutput(reasoning="mock reason", sequence_diagram="```mermaid\ninvalid_diagram\n```"),
        ArchitectOutput(reasoning="mock reason", sequence_diagram="```mermaid\nvalid_diagram\n```"),
    ]
    mock_validations = [
        ValidationResult(False, "It's wrong."),
        ValidationResult(True),
    ]
    with (
        patch("src.agents.design_lab.architect.llm_with_structure") as mock_llm,
        patch("src.agents.design_lab.architect.validate_mermaid") as mock_validation,
        patch("src.agents.design_lab.architect.get_stream_writer") as mock_writer,
    ):
        mock_llm.ainvoke = AsyncMock(side_effect=mock_responses)
        mock_validation.side_effect = mock_validations
        mock_writer.return_value = MagicMock(return_value=None)

        state = {
            "use_case": "# USE CASE: Login System\n...",
        }

        mock_runtime = MagicMock()
        mock_runtime.context = {"mmd_syntax_validation_limit": 3}

        command = await architect(state, mock_runtime)
        result = command.update

        assert result["sequence_diagram"] == mock_responses[1].sequence_diagram

        assert mock_llm.ainvoke.call_count == 2
        called_messages = mock_llm.ainvoke.call_args.args[0]
        assert "VALIDATION FAILED" in called_messages[3].content
