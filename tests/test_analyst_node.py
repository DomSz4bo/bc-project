from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from src.agents.design_lab.analyst import analyst


@pytest.mark.asyncio
async def test_analyst_generation():
    """
    Verify the analyst node generates a use case from a user intent summary.
    """
    mock_use_case = "# USE CASE: Login System\n..."
    mock_response = AIMessage(content=mock_use_case)

    with (
        patch("src.agents.design_lab.analyst.llm") as mock_llm,
        patch("src.agents.design_lab.analyst.get_stream_writer") as mock_writer,
    ):
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        mock_writer.return_value = MagicMock(return_value=None)

        state = {
            "user_intent_summary": "I want a JWT login system.",
        }

        result = await analyst(state)

        assert "use_case" in result
        assert result["use_case"] == mock_use_case

        mock_llm.ainvoke.assert_called_once()
        called_messages = mock_llm.ainvoke.call_args[0][0]

        assert isinstance(called_messages[0], SystemMessage)
        assert "Use Case" in called_messages[0].content

        assert isinstance(called_messages[1], HumanMessage)
        assert "I want a JWT login system." in called_messages[1].content


@pytest.mark.asyncio
async def test_analyst_missing_summary():
    """
    Verify the analyst fails if the user intent summary is missing.
    """
    mock_response = AIMessage(content="Nothing.")

    with (
        patch("src.agents.design_lab.analyst.llm") as mock_llm,
        patch("src.agents.design_lab.analyst.get_stream_writer") as mock_writer,
    ):
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        mock_writer.return_value = MagicMock(return_value=None)

        state = {}
        with pytest.raises(ValueError, match="No user_intent_summary"):
            await analyst(state)
