from collections.abc import Callable
from pathlib import Path
from typing import Any

from pydantic_ai import Agent

from lorebinders.agent import (
    AgentDeps,
    build_analysis_user_prompt,
    build_extraction_user_prompt,
    create_analysis_agent,
    create_extraction_agent,
    load_prompt_from_assets,
    run_agent,
)
from lorebinders.builder import build_binder
from lorebinders.ingestion.ingester import ingest
from lorebinders.ingestion.workspace import ensure_workspace, sanitize_filename
from lorebinders.models import (
    Chapter,
    EntityProfile,
    RunConfiguration,
)
from lorebinders.reporting.pdf import generate_pdf_report
from lorebinders.settings import Settings, get_settings


def get_effective_traits(
    settings: Settings, config: RunConfiguration
) -> dict[str, list[str]]:
    """Merge default settings with run configuration to get effective traits.

    Args:
        settings: Application settings with defaults.
        config: Run configuration with overrides/extensions.

    Returns:
        A dictionary mapping category names to their list of traits.
    """
    effective_traits: dict[str, list[str]] = {
        "Characters": settings.character_traits.copy(),
        "Locations": settings.location_traits.copy(),
    }

    for category, traits in config.custom_traits.items():
        if category not in effective_traits:
            effective_traits[category] = []

        current_set = set(effective_traits[category])
        for t in traits:
            if t not in current_set:
                effective_traits[category].append(t)
                current_set.add(t)

    for category in config.custom_categories:
        if category not in effective_traits:
            effective_traits[category] = []

    return effective_traits


def create_extractor(
    config: RunConfiguration,
    agent: Agent[AgentDeps, list[str]],
    deps: AgentDeps,
    categories: list[str],
) -> Callable[[Chapter], dict[str, list[str]]]:
    """Create an extraction function.

    Args:
        config: The run configuration.
        agent: The extraction agent.
        deps: Dependencies to inject.
        categories: List of categories to extract.

    Returns:
        A callable that extracts entities mapping category -> names.
    """

    def extract(chapter: Chapter) -> dict[str, list[str]]:
        results: dict[str, list[str]] = {}
        for category in categories:
            prompt = build_extraction_user_prompt(
                text=chapter.content,
                target_category=category,
                description=None,
                narrator=config.narrator_config,
            )

            names = run_agent(agent, prompt, deps)
            results[category] = names
        return results

    return extract


def create_analyzer(
    config: RunConfiguration,
    agent: Agent[AgentDeps, Any],
    deps: AgentDeps,
    effective_traits: dict[str, list[str]],
) -> Callable[[str, str, Chapter], EntityProfile]:
    """Create an analysis function.

    Args:
        config: The run configuration.
        agent: The analysis agent.
        deps: Dependencies to inject.
        effective_traits: Map of category -> traits.

    Returns:
        A callable that analyzes an entity.
    """

    def analyze(name: str, category: str, context: Chapter) -> EntityProfile:
        traits = effective_traits.get(category, [])
        if not traits:
            traits = ["Description", "Role"]

        full_prompt = build_analysis_user_prompt(
            context_text=context.content,
            entity_name=name,
            category=category,
            traits=traits,
        )

        result = run_agent(agent, full_prompt, deps)
        profile_traits = {t.trait: t.value for t in result.traits}

        return EntityProfile(
            name=result.entity_name,
            category=category,
            traits=profile_traits,
            confidence_score=0.8,
        )

    return analyze


def run(config: RunConfiguration) -> Path:
    """Execute the LoreBinders build pipeline.

    Args:
        config: The run configuration containing book path, author, title, etc.

    Returns:
        The path to the generated PDF report.
    """
    output_dir = ensure_workspace(config.author_name, config.book_title)
    settings = get_settings()
    deps = AgentDeps(settings=settings, prompt_loader=load_prompt_from_assets)

    effective_traits = get_effective_traits(settings, config)
    all_categories = list(effective_traits.keys())

    extraction_agent = create_extraction_agent(settings)
    analysis_agent = create_analysis_agent(settings)

    extractor = create_extractor(config, extraction_agent, deps, all_categories)
    analyzer = create_analyzer(config, analysis_agent, deps, effective_traits)

    build_binder(
        config=config,
        ingestion=ingest,
        extraction=extractor,
        analysis=analyzer,
        reporting=generate_pdf_report,
    )

    safe_title = sanitize_filename(config.book_title)
    return output_dir / f"{safe_title}_story_bible.pdf"
