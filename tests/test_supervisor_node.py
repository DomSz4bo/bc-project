from unittest.mock import AsyncMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from src.agents.supervisor import supervisor


@pytest.mark.asyncio
async def test_supervisor_intake_flow():
    """
    Verify the supervisor correctly formats the INTAKE prompt and returns the LLM response.
    """
    mock_response = AIMessage(content="What kind of authentication do you need?")

    with patch("src.agents.supervisor.llm") as mock_llm:
        mock_bound_llm = AsyncMock()
        mock_llm.bind_tools.return_value = mock_bound_llm
        mock_bound_llm.ainvoke.return_value = mock_response

        state = {
            "messages": [
                HumanMessage(content="I want to implement a login system.")
            ],
            "supervisor_phase": "INTAKE",
        }

        result = await supervisor(state)

        assert "messages" in result
        assert result["messages"] == mock_response

        mock_llm.bind_tools.assert_called_once()
        
        mock_bound_llm.ainvoke.assert_called_once()
        called_messages = mock_bound_llm.ainvoke.call_args[0][0]
        assert isinstance(called_messages[0], SystemMessage)
        assert "INTAKE" in called_messages[0].content
        assert "Axiom" in called_messages[0].content


@pytest.mark.asyncio
async def test_supervisor_approval_flow():
    """
    Verify the supervisor correctly formats the APPROVAL prompt with design context.
    """
    mock_response = AIMessage(content="The design looks solid. Should we proceed?")
    use_case = "UC: Login Flow"
    sq_diagram = "sequenceDiagram ..."

    with patch("src.agents.supervisor.llm") as mock_llm:
        mock_bound_llm = AsyncMock()
        mock_llm.bind_tools.return_value = mock_bound_llm
        mock_bound_llm.ainvoke.return_value = mock_response

        state = {
            "messages": [HumanMessage(content="Explain the flow.")],
            "supervisor_phase": "APPROVAL",
            "use_case": use_case,
            "sequence_diagram": sq_diagram,
        }

        result = await supervisor(state)

        assert result["messages"] == mock_response

        called_messages = mock_bound_llm.ainvoke.call_args[0][0]
        system_content = called_messages[0].content
        assert "APPROVAL" in system_content
        assert use_case in system_content
        assert sq_diagram in system_content


@pytest.mark.asyncio
async def test_supervisor_tool_handoff_call():
    """
    Verify the supervisor can return a message containing tool calls (handoff).
    """
    tool_call = {
        "name": "handoff_to_design",
        "args": {
            "user_intent_summary": "Detailed login requirements.",
            "instructions": "Use JWT."
        },
        "id": "call_123"
    }
    mock_response = AIMessage(content="", tool_calls=[tool_call])

    with patch("src.agents.supervisor.llm") as mock_llm:
        mock_bound_llm = AsyncMock()
        mock_llm.bind_tools.return_value = mock_bound_llm
        mock_bound_llm.ainvoke.return_value = mock_response

        state = {
            "messages": [HumanMessage(content="Go to design phase.")],
            "supervisor_phase": "INTAKE",
        }

        result = await supervisor(state)

        assert len(result["messages"].tool_calls) == 1
        assert result["messages"].tool_calls[0]["name"] == "handoff_to_design"
        assert result["messages"].tool_calls[0]["args"]["user_intent_summary"] == "Detailed login requirements."
