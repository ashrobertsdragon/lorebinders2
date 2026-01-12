import pytest
from unittest.mock import MagicMock, patch
from lorebinders.agents.extraction import EntityExtractionAgent
from lorebinders.agents.models import ExtractionConfig
from lorebinders.core.models import NarratorConfig

@pytest.fixture
def mock_pydantic_agent():
    with patch("lorebinders.agents.extraction.Agent") as mock:
        yield mock

def test_extraction_agent_run_sync(mock_pydantic_agent):
    """Test that run_sync calls the underlying agent correctly."""
    mock_instance = mock_pydantic_agent.return_value
    mock_instance.run_sync.return_value.data = ["Hero", "Villain"]

    agent = EntityExtractionAgent()
    config = ExtractionConfig(
        target_category="Characters",
        description="Main characters",
        narrator=NarratorConfig(is_3rd_person=True)
    )
    text = "The Hero fought the Villain."

    result = agent.run_sync(text, config)

    assert result == ["Hero", "Villain"]
    mock_instance.run_sync.assert_called_once_with(text, deps=config)

def test_extraction_agent_system_prompt_logic():
    """Test that the system prompt generation logic works (if exposed)."""
    with patch("lorebinders.agents.extraction.Agent") as mock_cls:
        agent = EntityExtractionAgent()

        mock_cls.assert_called_once()
        call_kwargs = mock_cls.call_args[1]
        assert "deps_type" in call_kwargs
        assert call_kwargs["deps_type"] == ExtractionConfig
        assert "result_type" in call_kwargs

        assert "system_prompt" in call_kwargs
