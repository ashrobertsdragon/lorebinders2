"""Application entry point for LoreBinders."""

from collections.abc import Callable
from pathlib import Path
from typing import Any

from pydantic_ai import Agent

from lorebinders.agent import (
    create_analysis_agent,
    create_extraction_agent,
    run_agent,
)
from lorebinders.builder import build_binder
from lorebinders.ingestion.ingester import ingest
from lorebinders.ingestion.workspace import ensure_workspace, sanitize_filename
from lorebinders.models import (
    AnalysisConfig,
    Chapter,
    CharacterProfile,
    ExtractionConfig,
    RunConfiguration,
)
from lorebinders.reporting.pdf import generate_pdf_report


def _create_extractor(
    config: RunConfiguration,
    agent: Agent[Any, Any],
) -> Callable[[Chapter], list[str]]:
    def extract(chapter: Chapter) -> list[str]:
        category = (
            config.custom_categories[0]
            if config.custom_categories
            else "Characters"
        )
        ext_config = ExtractionConfig(
            target_category=category,
            narrator=config.narrator_config,
        )
        return run_agent(agent, chapter.content, ext_config)

    return extract


def _create_analyzer(
    config: RunConfiguration,
    agent: Agent[Any, Any],
) -> Callable[[str, Chapter], CharacterProfile]:
    def analyze(name: str, context: Chapter) -> CharacterProfile:
        traits = config.custom_traits or ["Role", "Personality", "Appearance"]
        category = (
            config.custom_categories[0]
            if config.custom_categories
            else "Characters"
        )

        analysis_config = AnalysisConfig(
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

        return CharacterProfile(
            name=result.entity_name,
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

    extraction_agent = create_extraction_agent()
    analysis_agent = create_analysis_agent()

    extractor = _create_extractor(config, extraction_agent)
    analyzer = _create_analyzer(config, analysis_agent)

    build_binder(
        config=config,
        ingestion=ingest,
        extraction=extractor,
        analysis=analyzer,
        reporting=generate_pdf_report,
    )

    safe_title = sanitize_filename(config.book_title)
    return output_dir / f"{safe_title}_story_bible.pdf"
