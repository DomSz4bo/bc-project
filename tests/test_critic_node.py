import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from langchain_core.messages import SystemMessage, HumanMessage
from src.agents.design_lab.critic import critic, CriticOutput

@pytest.mark.asyncio
async def test_critic_pass():
    """
    Verify the critic node returns PASS when the diagram is correct.
    """
    mock_output = CriticOutput(verdict="PASS", feedback=None)
    
    with patch("src.agents.design_lab.critic.llm_with_structure") as mock_llm:
        mock_llm.ainvoke = AsyncMock(return_value=mock_output)
        
        state = {
            "use_case": "Use case content",
            "sequence_diagram": "Sequence diagram content",
            "revision_count": 0,
        }
        
        mock_runtime = MagicMock()
        mock_runtime.context = {"max_revisions": 3}
        
        result = await critic(state, mock_runtime)
        
        assert result["critic_verdict"] == "PASS"
        assert result["supervisor_phase"] == "APPROVAL"
        assert result["revision_count"] == 0
        assert result["critic_feedback"] is None
        
        # Verify inputs to LLM
        mock_llm.ainvoke.assert_called_once()
        called_messages = mock_llm.ainvoke.call_args[0][0]
        assert isinstance(called_messages[0], SystemMessage)
        assert "Design Critic" in called_messages[0].content
        assert isinstance(called_messages[1], HumanMessage)
        assert "Use case content" in called_messages[1].content
        assert "Sequence diagram content" in called_messages[1].content

@pytest.mark.asyncio
async def test_critic_fail():
    """
    Verify the critic node returns FAIL and increments revision_count.
    """
    mock_output = CriticOutput(verdict="FAIL", feedback="Missing step.")
    
    with patch("src.agents.design_lab.critic.llm_with_structure") as mock_llm:
        mock_llm.ainvoke = AsyncMock(return_value=mock_output)
        
        state = {
            "use_case": "Use case content",
            "sequence_diagram": "Sequence diagram content",
            "revision_count": 1,
        }
        
        mock_runtime = MagicMock()
        mock_runtime.context = {"max_revisions": 3}
        
        result = await critic(state, mock_runtime)
        
        assert result["critic_verdict"] == "FAIL"
        assert result["supervisor_phase"] == "APPROVAL"
        assert result["revision_count"] == 2
        assert result["critic_feedback"] == "Missing step."

@pytest.mark.asyncio
async def test_critic_limit():
    """
    Verify the critic node returns LIMIT when max_revisions is reached.
    """
    state = {
        "revision_count": 3,
    }
    
    mock_runtime = MagicMock()
    mock_runtime.context = {"max_revisions": 3}
    
    with patch("src.agents.design_lab.critic.llm_with_structure") as mock_llm:
        result = await critic(state, mock_runtime)
        
        assert result["critic_verdict"] == "LIMIT"
        assert result["supervisor_phase"] == "APPROVAL"
        assert result["critic_feedback"] is None
        mock_llm.ainvoke.assert_not_called()
