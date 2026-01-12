import pytest
from pydantic import ValidationError

from lorebinders.agents.models import AnalysisConfig, ExtractionConfig
from lorebinders.core.models import NarratorConfig


def test_extraction_config_valid():
    """Test valid ExtractionConfig creation."""
    config = ExtractionConfig(
        target_category="Characters",
        description="People in the story",
        narrator=NarratorConfig(is_3rd_person=True)
    )
    assert config.target_category == "Characters"
    assert config.description == "People in the story"
    assert config.narrator is not None
    assert config.narrator.is_3rd_person is True


def test_extraction_config_defaults():
    """Test ExtractionConfig defaults."""
    config = ExtractionConfig(target_category="Locations")
    assert config.target_category == "Locations"
    assert config.narrator is None
    assert config.description is None


def test_analysis_config_valid():
    """Test valid AnalysisConfig creation."""
    config = AnalysisConfig(
        target_entity="Gandalf",
        category="Character",
        traits=["Role", "Power Level"]
    )
    assert config.target_entity == "Gandalf"
    assert config.category == "Character"
    assert config.traits == ["Role", "Power Level"]


def test_analysis_config_validation():
    """Test AnalysisConfig validation."""
    config = AnalysisConfig(
        target_entity="Shire",
        category="Location",
        traits=[]
    )
    assert config.traits == []
