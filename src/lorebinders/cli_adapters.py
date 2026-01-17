from lorebinders import models
from lorebinders.agent import analysis_agent, extraction_agent, run_agent


class ExtractionAdapter:
    """Adapter for run_extraction to match ExtractionAgent protocol."""

    def __init__(self, config: models.RunConfiguration):
        """Initialize with run configuration."""
        self.config = config

    def extract(self, chapter: models.Chapter) -> list[str]:
        """Extract entities from chapter content.

        Returns:
            A list of extracted entity names.
        """
        category = "Characters"
        if self.config.custom_categories:
            category = self.config.custom_categories[0]

        ext_config = models.ExtractionConfig(
            target_category=category,
            narrator=self.config.narrator_config,
        )
        return run_agent(extraction_agent, chapter.content, ext_config)


class AnalysisAdapter:
    """Adapter for run_analysis to match AnalysisAgent protocol."""

    def __init__(self, config: models.RunConfiguration):
        """Initialize with run configuration."""
        self.config = config

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

        config = models.AnalysisConfig(
            target_entity=name,
            category=category,
            traits=traits,
        )
        result = run_agent(analysis_agent, context.content, config)

        profile_traits = {t.trait: t.value for t in result.traits}

        return models.CharacterProfile(
            name=result.entity_name,
            traits=profile_traits,
            confidence_score=0.8,
        )
