from unittest.mock import AsyncMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from src.agents.design_lab.architect import architect


@pytest.mark.asyncio
async def test_architect_generation():
    """
    Verify the architect node generates a sequence diagram from a use case.
    """
    mock_diagram = """```mermaid
    sequenceDiagram
    Alice->>+John: Hello John, how are you?
    Alice->>+John: John, can you hear me?
    John-->>-Alice: Hi Alice, I can hear you!
    John-->>-Alice: I feel great!```"""
    mock_response = AIMessage(content=mock_diagram)

    with patch("src.agents.design_lab.architect.llm") as mock_llm:
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)

        state = {
            "use_case": "# USE CASE: Login System\n...",
        }

        result = await architect(state)

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
    John-->>-Alice: I feel great!```"""
    mock_response = AIMessage(content=mock_diagram)

    with patch("src.agents.design_lab.architect.llm") as mock_llm:
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)

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

        result = await architect(state)

        assert result["sequence_diagram"] == mock_diagram

        mock_llm.ainvoke.assert_called_once()
        called_messages = mock_llm.ainvoke.call_args[0][0]

        assert "```mermaid\n" in called_messages[2].content
        assert "Missing validation step." in called_messages[3].content
