import pytest
from unittest.mock import MagicMock, patch
from lorebinders.refinement.manager import RefinementManager
from lorebinders.refinement.cleaner import EntityCleaner
from lorebinders.refinement.resolver import EntityResolver
from lorebinders.refinement.summarizer import EntitySummarizer

@pytest.fixture
def mock_cleaner():
    with patch("lorebinders.refinement.manager.EntityCleaner") as mock:
        instance = mock.return_value
        instance.clean.return_value = {"cleaned": True}
        yield instance

@pytest.fixture
def mock_resolver():
    with patch("lorebinders.refinement.manager.EntityResolver") as mock:
        instance = mock.return_value
        instance.resolve.return_value = {"resolved": True}
        yield instance

@pytest.fixture
def mock_summarizer():
    with patch("lorebinders.refinement.manager.EntitySummarizer") as mock:
        instance = mock.return_value
        instance.summarize.return_value = {"summarized": True}
        yield instance

def test_refinement_manager_pipeline(mock_cleaner, mock_resolver, mock_summarizer):
    """Test that RefinementManager orchestrates the steps in the correct order."""
    manager = RefinementManager()

    raw_binder = {"raw": "data"}
    narrator_name = "Jane"

    result = manager.process(raw_binder, narrator_name)


    mock_cleaner.clean.assert_called_once_with(raw_binder, narrator_name)
    mock_resolver.resolve.assert_called_once_with({"cleaned": True})
    mock_summarizer.summarize.assert_called_once_with({"resolved": True})

    assert result == {"summarized": True}

def test_refinement_manager_pipeline_no_summary(mock_cleaner, mock_resolver, mock_summarizer):
    """Test that RefinementManager can skip summarization if configured (optional)."""


    pass
