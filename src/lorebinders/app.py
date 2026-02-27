import asyncio
import logging
from collections.abc import Awaitable, Callable
from pathlib import Path

from pydantic_ai import Agent

from lorebinders.agent import (
    build_analysis_user_prompt,
    build_extraction_user_prompt,
    create_analysis_agent,
    create_extraction_agent,
    load_prompt_from_assets,
)
from lorebinders.models import (
    AgentDeps,
    AnalysisResult,
    CategoryTarget,
    Chapter,
    EntityProfile,
    ExtractionResult,
    ProgressUpdate,
    RunConfiguration,
    SummarizerResult,
)
from lorebinders.refinement.conversion import ingest
from lorebinders.reporting.pdf import generate_pdf_report
from lorebinders.settings import Settings, get_settings
from lorebinders.storage.workspace import ensure_workspace, sanitize_filename
from lorebinders.workflow import build_binder

logger = logging.getLogger(__name__)


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
        for trait in traits:
            if trait not in current_set:
                effective_traits[category].append(trait)
                current_set.add(trait)

    for category in config.custom_categories:
        if category not in effective_traits:
            effective_traits[category] = []

    return effective_traits


def create_extractor(
    config: RunConfiguration,
    agent: Agent[AgentDeps, ExtractionResult],
    deps: AgentDeps,
    categories: list[str],
) -> Callable[[Chapter], Awaitable[dict[str, list[str]]]]:
    """Create an async extraction function.

    Args:
        config: The run configuration.
        agent: The extraction agent.
        deps: Dependencies to inject.
        categories: List of categories to extract.

    Returns:
        A callable that extracts entities mapping category -> names.
    """

    async def extract(chapter: Chapter) -> dict[str, list[str]]:
        prompt = build_extraction_user_prompt(
            text=chapter.content,
            categories=categories,
            narrator=config.narrator_config,
        )
        result = await agent.run(prompt, deps=deps)
        return result.output.to_dict()

    return extract


def create_analyzer(
    agent: Agent[AgentDeps, list[AnalysisResult]],
    deps: AgentDeps,
    effective_traits: dict[str, list[str]],
) -> Callable[[list[CategoryTarget], Chapter], Awaitable[list[EntityProfile]]]:
    """Create an async analysis function.

    Args:
        agent: The analysis agent.
        deps: Dependencies to inject.
        effective_traits: Map of category -> traits.

    Returns:
        A callable that analyzes a batch of entities.
    """

    async def analyze(
        categories: list[CategoryTarget], context: Chapter
    ) -> list[EntityProfile]:
        for category in categories:
            cat = category.name
            traits = effective_traits.get(cat, [])
            if not traits:
                traits = ["Description", "Role"]
            category.traits = traits

        full_prompt = build_analysis_user_prompt(
            context_text=context.content,
            categories=categories,
        )

        result = await agent.run(full_prompt, deps=deps)
        results = result.output

        profiles = []
        for r in results:
            profile_traits: dict[str, str | list[str]] = {
                trait.trait: trait.value for trait in r.traits
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


async def _run_async(
    config: RunConfiguration,
    progress: Callable[[ProgressUpdate], None] | None = None,
    extraction_agent: Agent[AgentDeps, ExtractionResult] | None = None,
    analysis_agent: Agent[AgentDeps, list[AnalysisResult]] | None = None,
    summarization_agent: Agent[AgentDeps, SummarizerResult] | None = None,
) -> Path:
    """Internal async implementation of the run command.

    Args:
        config: The run configuration.
        progress: Optional callback to report progress.
        extraction_agent: Optional agent override.
        analysis_agent: Optional agent override.
        summarization_agent: Optional agent override.

    Returns:
        The path to the generated PDF report.
    """
    output_dir = ensure_workspace(config.author_name, config.book_title)
    settings = get_settings()
    deps = AgentDeps(settings=settings, prompt_loader=load_prompt_from_assets)

    effective_traits = merge_traits(settings, config)
    all_categories = list(effective_traits.keys())

    ext_agent = extraction_agent or create_extraction_agent(settings)
    ana_agent = analysis_agent or create_analysis_agent(settings)

    extractor = create_extractor(config, ext_agent, deps, all_categories)
    analyzer = create_analyzer(ana_agent, deps, effective_traits)

    await build_binder(
        config=config,
        ingestion=ingest,
        extraction=extractor,
        analysis=analyzer,
        reporting=generate_pdf_report,
        summarization_agent=summarization_agent,
        progress=progress,
    )

    safe_title = sanitize_filename(config.book_title)
    return output_dir / f"{safe_title}_story_bible.pdf"


def run(
    config: RunConfiguration,
    progress: Callable[[ProgressUpdate], None] | None = None,
    log_file: Path | None = None,
    extraction_agent: Agent | None = None,
    analysis_agent: Agent | None = None,
    summarization_agent: Agent | None = None,
) -> Path:
    """Execute the LoreBinders build pipeline.

    Args:
        config: The run configuration containing book path, author, title, etc.
        progress: Optional callback to report progress.
        log_file: Optional path to log file.
        extraction_agent: Optional agent override.
        analysis_agent: Optional agent override.
        summarization_agent: Optional agent override.

    Returns:
        The path to the generated PDF report.
    """
    return asyncio.run(
        _run_async(
            config,
            progress,
            extraction_agent=extraction_agent,
            analysis_agent=analysis_agent,
            summarization_agent=summarization_agent,
        )
    )
