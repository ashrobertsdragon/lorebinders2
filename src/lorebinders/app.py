from collections.abc import Callable
from pathlib import Path

from pydantic_ai import Agent

from lorebinders.agent import (
    build_analysis_user_prompt,
    build_extraction_user_prompt,
    create_analysis_agent,
    create_extraction_agent,
    load_prompt_from_assets,
    run_agent,
)
from lorebinders.models import (
    AgentDeps,
    AnalysisResult,
    Chapter,
    EntityProfile,
    ExtractionResult,
    ProgressUpdate,
    RunConfiguration,
)
from lorebinders.refinement.conversion import ingest
from lorebinders.reporting.pdf import generate_pdf_report
from lorebinders.settings import Settings, get_settings
from lorebinders.storage.workspace import ensure_workspace, sanitize_filename
from lorebinders.types import CategoryTarget
from lorebinders.workflow import build_binder


def merge_traits(
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
    agent: Agent[AgentDeps, ExtractionResult],
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
        prompt = build_extraction_user_prompt(
            text=chapter.content,
            categories=categories,
            narrator=config.narrator_config,
        )
        result = run_agent(agent, prompt, deps)
        return result.to_dict()

    return extract


def create_analyzer(
    agent: Agent[AgentDeps, list[AnalysisResult]],
    deps: AgentDeps,
    effective_traits: dict[str, list[str]],
) -> Callable[[list[CategoryTarget], Chapter], list[EntityProfile]]:
    """Create an analysis function.

    Args:
        agent: The analysis agent.
        deps: Dependencies to inject.
        effective_traits: Map of category -> traits.

    Returns:
        A callable that analyzes a batch of entities.
    """

    def analyze(
        categories: list[CategoryTarget], context: Chapter
    ) -> list[EntityProfile]:
        for category in categories:
            cat = category["name"]
            traits = effective_traits.get(cat, [])
            if not traits:
                traits = ["Description", "Role"]
            category["traits"] = traits

        full_prompt = build_analysis_user_prompt(
            context_text=context.content,
            categories=categories,
        )

        results = run_agent(agent, full_prompt, deps)

        profiles = []
        for r in results:
            profile_traits: dict[str, str | list[str]] = {
                t.trait: t.value for t in r.traits
            }
            profiles.append(
                EntityProfile(
                    name=r.entity_name,
                    category=r.category,
                    chapter_number=context.number,
                    traits=profile_traits,
                    confidence_score=0.8,
                )
            )
        return profiles

    return analyze


def run(
    config: RunConfiguration,
    progress: Callable[[ProgressUpdate], None] | None = None,
    log_file: Path | None = None,
) -> Path:
    """Execute the LoreBinders build pipeline.

    Args:
        config: The run configuration containing book path, author, title, etc.
        progress: Optional callback to report progress.

    Returns:
        The path to the generated PDF report.
    """
    output_dir = ensure_workspace(config.author_name, config.book_title)
    settings = get_settings()
    deps = AgentDeps(settings=settings, prompt_loader=load_prompt_from_assets)

    effective_traits = merge_traits(settings, config)
    all_categories = list(effective_traits.keys())

    extraction_agent = create_extraction_agent(settings)
    analysis_agent = create_analysis_agent(settings)

    extractor = create_extractor(config, extraction_agent, deps, all_categories)
    analyzer = create_analyzer(analysis_agent, deps, effective_traits)

    build_binder(
        config=config,
        ingestion=ingest,
        extraction=extractor,
        analysis=analyzer,
        reporting=generate_pdf_report,
        progress=progress,
    )

    safe_title = sanitize_filename(config.book_title)
    return output_dir / f"{safe_title}_story_bible.pdf"
