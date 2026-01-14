from lorebinders.agents.analysis import UniversalAnalysisAgent
from lorebinders.agents.extraction import EntityExtractionAgent
from lorebinders.agents.models import AnalysisConfig, ExtractionConfig
from lorebinders.core import models
from lorebinders.core.interfaces import AnalysisAgent, ExtractionAgent


class ExtractionAdapter(ExtractionAgent):
    """Adapter for EntityExtractionAgent to match ExtractionAgent protocol."""

    def __init__(self, config: models.RunConfiguration):
        """Initialize with run configuration."""
        self.config = config
        self.agent = EntityExtractionAgent()

    def extract(self, chapter: models.Chapter) -> list[str]:
        """Extract entities from chapter content.

        Returns:
            A list of extracted entity names.
        """
        category = "Characters"
        if self.config.custom_categories:
            category = self.config.custom_categories[0]

        ext_config = ExtractionConfig(
            target_category=category,
            narrator=self.config.narrator_config,
        )
        return self.agent.run_sync(chapter.content, ext_config)


class AnalysisAdapter(AnalysisAgent):
    """Adapter for UniversalAnalysisAgent to match AnalysisAgent protocol."""

    def __init__(self, config: models.RunConfiguration):
        """Initialize with run configuration."""
        self.config = config
        self.agent = UniversalAnalysisAgent()

    def analyze(
        self, name: str, context: models.Chapter
    ) -> models.CharacterProfile:
        """Analyze an entity within the context of a chapter.

        Returns:
            The created character profile.
        """
        traits = self.config.custom_traits or [
            "Role",
            "Personality",
            "Appearance",
        ]

        category = "Characters"
        if self.config.custom_categories:
            category = self.config.custom_categories[0]

        ana_config = AnalysisConfig(
            target_entity=name,
            category=category,
            traits=traits,
        )
        result = self.agent.run_sync(context.content, ana_config)

        profile_traits = {t.trait: t.value for t in result.traits}

        return models.CharacterProfile(
            name=result.entity_name,
            traits=profile_traits,
            confidence_score=0.8,
        )
