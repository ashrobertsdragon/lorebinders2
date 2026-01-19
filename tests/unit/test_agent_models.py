from lorebinders.models import AnalysisConfig, ExtractionConfig, NarratorConfig


def test_extraction_config_valid() -> None:
    """Test valid ExtractionConfig creation."""
    config = ExtractionConfig(
        target_category="Characters",
        description="People in the story",
        narrator=NarratorConfig(is_3rd_person=True),
    )
    assert config.target_category == "Characters"
    assert config.description == "People in the story"
    assert config.narrator is not None
    assert config.narrator.is_3rd_person is True


def test_extraction_config_defaults() -> None:
    """Test ExtractionConfig defaults."""
    config = ExtractionConfig(target_category="Locations")
    assert config.target_category == "Locations"
    assert config.narrator is None
    assert config.description is None


def test_analysis_config_valid() -> None:
    """Test valid AnalysisConfig creation."""
    config = AnalysisConfig(
        target_entity="Gandalf",
        category="Character",
        traits=["Role", "Power Level"],
    )
    assert config.target_entity == "Gandalf"
    assert config.category == "Character"
    assert config.traits == ["Role", "Power Level"]


def test_analysis_config_validation() -> None:
    """Test AnalysisConfig validation."""
    config = AnalysisConfig(
        target_entity="Shire", category="Location", traits=[]
    )
    assert config.traits == []
