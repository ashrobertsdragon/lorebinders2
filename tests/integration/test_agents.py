import pytest
from unittest.mock import patch, MagicMock

from lorebinders.agents.extraction import EntityExtractionAgent
from lorebinders.agents.analysis import UniversalAnalysisAgent
from lorebinders.agents.models import (
    ExtractionConfig,
    AnalysisConfig,
    NarratorConfig,
    AnalysisResult,
    TraitValue
)

@pytest.fixture
def mock_extraction_agent():
    with patch("lorebinders.agents.extraction.Agent") as mock:
        instance = mock.return_value
        instance.run_sync.return_value.data = ["Sherlock Holmes", "Dr. Watson"]
        yield instance

@pytest.fixture
def mock_analysis_agent():
    with patch("lorebinders.agents.analysis.Agent") as mock:
        instance = mock.return_value
        instance.run_sync.return_value.data = AnalysisResult(
            entity_name="Sherlock Holmes",
            category="Character",
            traits=[
                TraitValue(
                    trait="Role",
                    value="Detective",
                    evidence="The world's only consulting detective"
                )
            ]
        )
        yield instance

def test_agents_flow(mock_extraction_agent, mock_analysis_agent):
    """Test the full flow of extraction and analysis with mocks."""
    text_chunk = (
        "Sherlock Holmes sat in his chair. Dr. Watson looked at him. "
        "The world's only consulting detective was thinking."
    )


    extractor = EntityExtractionAgent()
    ext_config = ExtractionConfig(
        target_category="Character",
        narrator=NarratorConfig(is_3rd_person=True)
    )
    entities = extractor.run_sync(text_chunk, ext_config)

    assert "Sherlock Holmes" in entities
    assert "Dr. Watson" in entities


    analyzer = UniversalAnalysisAgent()
    analysis_config = AnalysisConfig(
        target_entity="Sherlock Holmes",
        category="Character",
        traits=["Role"]
    )
    result = analyzer.run_sync(text_chunk, analysis_config)

    assert result.entity_name == "Sherlock Holmes"
    assert result.traits[0].value == "Detective"
