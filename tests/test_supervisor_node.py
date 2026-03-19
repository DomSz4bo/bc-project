from unittest.mock import AsyncMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from src.agents.supervisor import SupervisorOutput, supervisor


@pytest.mark.asyncio
async def test_supervisor_intake_to_design():
    """
    Verify the supervisor transitions from INTAKE to DESIGN.
    """
    mock_output = SupervisorOutput(
        next_step="DESIGN",
        user_intent_summary="User intent placeholder.",
        message_to_user=None,
    )

    with patch("src.agents.supervisor.llm_with_structure") as mock_llm:
        mock_llm.ainvoke = AsyncMock(return_value=mock_output)

        state = {
            "messages": [
                HumanMessage(content="I want to implement a login system using JWT.")
            ],
            "supervisor_phase": "INTAKE",
            "next_step": None,
            "user_intent_summary": None,
        }

        result = await supervisor(state)

        assert result["next_step"] == "DESIGN"
        assert result["user_intent_summary"] == "User intent placeholder."

        mock_llm.ainvoke.assert_called_once()
        called_messages = mock_llm.ainvoke.call_args[0][0]
        assert isinstance(called_messages[0], SystemMessage)
        assert "INTAKE" in called_messages[0].content


@pytest.mark.asyncio
async def test_supervisor_approval_prompt_selection():
    """
    Verify that the APPROVAL phase correctly selects and formats the system prompt.
    """
    mock_output = SupervisorOutput(next_step="USER", message_to_user="Question?")

    with patch("src.agents.supervisor.llm_with_structure") as mock_llm:
        mock_llm.ainvoke = AsyncMock(return_value=mock_output)

        use_case = "Use Case Placeholder"
        sq_diagram = "Sequence Diagram Placeholder"
        state = {
            "messages": [HumanMessage(content="Is this correct?")],
            "supervisor_phase": "APPROVAL",
            "use_case": use_case,
            "sequence_diagram": sq_diagram,
            "next_step": None,
            "user_intent_summary": None,
        }

        await supervisor(state)

        called_messages = mock_llm.ainvoke.call_args[0][0]
        system_content = called_messages[0].content
        assert "APPROVAL" in system_content
        assert use_case in system_content
        assert sq_diagram in system_content


@pytest.mark.asyncio
async def test_supervisor_message_to_user_added():
    """
    Verify that message_to_user from LLM is correctly added to messages as an AIMessage.
    """
    mock_output = SupervisorOutput(
        next_step="USER",
        message_to_user="Could you please clarify the authentication method?",
    )

    with patch("src.agents.supervisor.llm_with_structure") as mock_llm:
        mock_llm.ainvoke = AsyncMock(return_value=mock_output)

        state = {
            "messages": [HumanMessage(content="I want login.")],
            "supervisor_phase": "INTAKE",
        }

        result = await supervisor(state)

        assert "messages" in result
        assert len(result["messages"]) == 1
        ai_msg = result["messages"][0]
        assert isinstance(ai_msg, AIMessage)
        assert ai_msg.content == "Could you please clarify the authentication method?"
