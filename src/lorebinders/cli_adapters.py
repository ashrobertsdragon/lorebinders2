from collections.abc import Callable

from lorebinders import models
from lorebinders.agent import (
    create_analysis_agent,
    create_extraction_agent,
    run_agent,
)


def get_extraction_func(
    config: models.RunConfiguration,
) -> Callable[[models.Chapter], list[str]]:
    """Get a callable for extraction based on config.

    Returns:
        A callable that extracts entities from a chapter.
    """
    agent = create_extraction_agent()

    def extract(chapter: models.Chapter) -> list[str]:
        category = "Characters"
        if config.custom_categories:
            category = config.custom_categories[0]

        ext_config = models.ExtractionConfig(
            target_category=category,
            narrator=config.narrator_config,
        )
        return run_agent(agent, chapter.content, ext_config)

    return extract


def get_analysis_func(
    config: models.RunConfiguration,
) -> Callable[[str, models.Chapter], models.CharacterProfile]:
    """Get a callable for analysis based on config.

    Returns:
        A callable that analyzes an entity in a chapter.
    """
    agent = create_analysis_agent()

    def analyze(name: str, context: models.Chapter) -> models.CharacterProfile:
        traits = config.custom_traits or [
            "Role",
            "Personality",
            "Appearance",
        ]

        category = "Characters"
        if config.custom_categories:
            category = config.custom_categories[0]

        analysis_config = models.AnalysisConfig(
            target_entity=name,
            category=category,
            traits=traits,
        )

        full_prompt = (
            f"Context:\n{context.content}\n\n"
            f"Task: Analyze the entity '{name}' based on the context above."
        )

        result = run_agent(agent, full_prompt, analysis_config)

        profile_traits = {t.trait: t.value for t in result.traits}

        return models.CharacterProfile(
            name=result.entity_name,
            traits=profile_traits,
            confidence_score=0.8,
        )

    return analyze
