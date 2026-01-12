import pytest
from unittest.mock import MagicMock, patch
from lorebinders.agents.analysis import UniversalAnalysisAgent
from lorebinders.agents.models import AnalysisConfig, AnalysisResult, TraitValue

@pytest.fixture
def mock_pydantic_agent():
    with patch("lorebinders.agents.analysis.Agent") as mock:
        yield mock

def test_analysis_agent_run_sync(mock_pydantic_agent):
    """Test that run_sync calls the underlying agent correctly."""
    mock_instance = mock_pydantic_agent.return_value

    expected_result = AnalysisResult(
        entity_name="Gandalf",
        category="Character",
        traits=[
            TraitValue(trait="Role", value="Wizard", evidence="Uses magic"),
            TraitValue(trait="Origin", value="Maiar", evidence="From Valinor")
        ]
    )
    mock_instance.run_sync.return_value.data = expected_result

    agent = UniversalAnalysisAgent()
    config = AnalysisConfig(
        target_entity="Gandalf",
        category="Character",
        traits=["Role", "Origin"]
    )
    text = "Gandalf the Wizard came from Valinor."

    result = agent.run_sync(text, config)

    assert result == expected_result
    mock_instance.run_sync.assert_called_once_with(text, deps=config)

def test_analysis_agent_system_prompt_logic():
    """Test that the system prompt generation logic works."""
    with patch("lorebinders.agents.analysis.Agent") as mock_cls:
        agent = UniversalAnalysisAgent()

        mock_cls.assert_called_once()
        call_kwargs = mock_cls.call_args[1]
        assert "deps_type" in call_kwargs
        assert call_kwargs["deps_type"] == AnalysisConfig
        assert "result_type" in call_kwargs
        assert call_kwargs["result_type"] == AnalysisResult

        assert "system_prompt" in call_kwargs
