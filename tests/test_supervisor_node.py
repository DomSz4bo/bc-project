from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from src.agents.supervisor import (
    ACTION_TOOLS,
    handoff_to_design,
    handoff_to_implementation,
    supervisor,
)


@pytest.fixture
def mock_runtime():
    """Base runtime mock."""
    runtime = MagicMock()
    runtime.context = {}
    return runtime


@pytest.fixture
def mock_runtime_no_skills(mock_runtime):
    """Runtime mock with a skill manager that has no available skills."""
    skill_manager = MagicMock()
    skill_manager.has_available_skills.return_value = False
    mock_runtime.context["skill_manager"] = skill_manager
    return mock_runtime


@pytest.fixture
def mock_runtime_with_skills(mock_runtime):
    """Runtime mock with a skill manager that has available skills."""
    skill_manager = MagicMock()
    skill_manager.has_available_skills.return_value = True
    skill_manager.get_skill_catalog.return_value = (
        "<available_skills><skill><name>test-skill</name></skill></available_skills>"
    )
    mock_runtime.context["skill_manager"] = skill_manager
    return mock_runtime


@pytest.mark.asyncio
async def test_supervisor_intake_flow(mock_runtime):
    """
    Verify the supervisor correctly formats the INTAKE prompt and returns the LLM response.
    """
    mock_response = AIMessage(content="What kind of authentication do you need?")

    with (
        patch("src.agents.supervisor.main_llm") as _,
        patch("src.agents.supervisor.fallback_llm") as _,
        patch("src.agents.supervisor.build_fallback_chain") as mock_chain_builder,
        patch("src.agents.supervisor.get_stream_writer") as _,
    ):

        mock_llm_with_tools = AsyncMock()
        mock_llm_with_tools.ainvoke.return_value = mock_response
        mock_chain_builder.return_value = mock_llm_with_tools

        state = {
            "messages": [HumanMessage(content="I want to implement a login system.")],
            "supervisor_phase": "INTAKE",
        }

        result = await supervisor(state, mock_runtime)

        assert "messages" in result
        assert result["messages"] == [mock_response]

        mock_chain_builder.assert_called_once()
        assert "tools" in mock_chain_builder.call_args.kwargs
        assert mock_chain_builder.call_args.kwargs["tools"] == [handoff_to_design]

        mock_llm_with_tools.ainvoke.assert_called_once()
        called_messages = mock_llm_with_tools.ainvoke.call_args[0][0]
        assert isinstance(called_messages[0], SystemMessage)
        assert "INTAKE" in called_messages[0].content
        assert "Axiom" in called_messages[0].content


@pytest.mark.asyncio
async def test_supervisor_approval_flow(mock_runtime):
    """
    Verify the supervisor correctly formats the APPROVAL prompt with design context.
    """
    mock_response = AIMessage(content="The design looks solid. Should we proceed?")
    use_case = "UC: Login Flow"
    sq_diagram = "sequenceDiagram ..."

    with (
        patch("src.agents.supervisor.main_llm") as _,
        patch("src.agents.supervisor.fallback_llm") as _,
        patch("src.agents.supervisor.build_fallback_chain") as mock_chain_builder,
        patch("src.agents.supervisor.get_stream_writer") as _,
    ):
        mock_llm_with_tools = AsyncMock()
        mock_llm_with_tools.ainvoke.return_value = mock_response
        mock_chain_builder.return_value = mock_llm_with_tools

        state = {
            "messages": [HumanMessage(content="Explain the flow.")],
            "supervisor_phase": "APPROVAL",
            "use_case": use_case,
            "sequence_diagram": sq_diagram,
        }

        result = await supervisor(state, mock_runtime)

        assert result["messages"] == [mock_response]

        mock_chain_builder.assert_called_once()
        assert "tools" in mock_chain_builder.call_args.kwargs
        assert mock_chain_builder.call_args.kwargs["tools"] == [handoff_to_design, handoff_to_implementation]

        called_messages = mock_llm_with_tools.ainvoke.call_args[0][0]
        system_content = called_messages[0].content
        assert "APPROVAL" in system_content
        assert use_case in system_content
        assert sq_diagram in system_content


@pytest.mark.asyncio
async def test_supervisor_post_implementation_flow_no_skills(mock_runtime_no_skills):
    """
    Verify the supervisor formats the POST_IMPLEMENTATION prompt correctly when no skills are available.
    """
    mock_response = AIMessage(content="The implementation is complete. Let's review.")

    with (
        patch("src.agents.supervisor.main_llm") as _,
        patch("src.agents.supervisor.fallback_llm") as _,
        patch("src.agents.supervisor.build_fallback_chain") as mock_chain_builder,
        patch("src.agents.supervisor.get_stream_writer") as _,
    ):
        mock_llm_with_tools = AsyncMock()
        mock_llm_with_tools.ainvoke.return_value = mock_response
        mock_chain_builder.return_value = mock_llm_with_tools

        state = {
            "messages": [HumanMessage(content="What's the status?")],
            "supervisor_phase": "POST_IMPLEMENTATION",
        }

        result = await supervisor(state, mock_runtime_no_skills)

        assert result["messages"] == [mock_response]

        mock_chain_builder.assert_called_once()
        assert "tools" in mock_chain_builder.call_args.kwargs
        assert mock_chain_builder.call_args.kwargs["tools"] == ACTION_TOOLS

        called_messages = mock_llm_with_tools.ainvoke.call_args[0][0]
        system_content = called_messages[0].content

        assert "POST_IMPLEMENTATION" in system_content
        assert "`activate_skill` tool" not in system_content


@pytest.mark.asyncio
async def test_supervisor_post_implementation_with_skills(mock_runtime_with_skills):
    """
    Verify skill catalog injection and specific instructions in POST_IMPLEMENTATION phase when skills are available.
    """
    mock_response = AIMessage(content="I see the skills.")

    with (
        patch("src.agents.supervisor.main_llm") as _,
        patch("src.agents.supervisor.fallback_llm") as _,
        patch("src.agents.supervisor.build_fallback_chain") as mock_chain_builder,
        patch("src.agents.supervisor.get_stream_writer") as _,
    ):
        mock_llm_with_tools = AsyncMock()
        mock_llm_with_tools.ainvoke.return_value = mock_response
        mock_chain_builder.return_value = mock_llm_with_tools

        state = {
            "messages": [HumanMessage(content="What skills are available?")],
            "supervisor_phase": "POST_IMPLEMENTATION",
        }

        await supervisor(state, mock_runtime_with_skills)

        called_messages = mock_llm_with_tools.ainvoke.call_args[0][0]
        system_content = called_messages[0].content

        assert "test-skill" in system_content
        assert "`activate_skill` tool" in system_content


@pytest.mark.asyncio
async def test_supervisor_tool_handoff_call(mock_runtime):
    """
    Verify the supervisor can return a message containing tool calls (handoff).
    """
    tool_call = {
        "name": "handoff_to_design",
        "args": {
            "user_intent_summary": "Detailed login requirements.",
            "instructions": "Use JWT.",
        },
        "id": "call_123",
    }
    mock_response = AIMessage(content="", tool_calls=[tool_call])

    with (
        patch("src.agents.supervisor.main_llm") as _,
        patch("src.agents.supervisor.fallback_llm") as _,
        patch("src.agents.supervisor.build_fallback_chain") as mock_chain_builder,
        patch("src.agents.supervisor.get_stream_writer") as _,
    ):
        mock_llm_with_tools = AsyncMock()
        mock_llm_with_tools.ainvoke.return_value = mock_response
        mock_chain_builder.return_value = mock_llm_with_tools

        state = {
            "messages": [HumanMessage(content="Go to design phase.")],
            "supervisor_phase": "INTAKE",
        }

        result = await supervisor(state, mock_runtime)

        assert len(result["messages"][0].tool_calls) == 1

        tool_name = result["messages"][0].tool_calls[0]["name"]
        assert tool_name == "handoff_to_design"

        summary = result["messages"][0].tool_calls[0]["args"]["user_intent_summary"]
        assert summary == "Detailed login requirements."
