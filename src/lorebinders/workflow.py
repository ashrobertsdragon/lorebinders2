import asyncio
import logging
from collections.abc import Awaitable, Callable
from pathlib import Path

from pydantic_ai import Agent

from lorebinders import models
from lorebinders.agent.summarization import summarize_binder
from lorebinders.refinement.cleaning import clean_traits
from lorebinders.refinement.sorting import sort_extractions
from lorebinders.storage.provider import FilesystemStorage, StorageProvider
from lorebinders.storage.workspace import sanitize_filename
from lorebinders.types import SortedExtractions

logger = logging.getLogger(__name__)


async def _extract_chapter(
    chapter: models.Chapter,
    extraction_fn: Callable[[models.Chapter], Awaitable[dict[str, list[str]]]],
    extractions_dir: Path,
    idx: int,
    total: int,
    semaphore: asyncio.Semaphore,
    storage: StorageProvider,
    progress: Callable[[models.ProgressUpdate], None] | None = None,
) -> tuple[int, dict[str, list[str]]]:
    """Extract entities from a chapter.

    Uses throttling and abstracted storage.

    Args:
        chapter: The chapter to extract from.
        extraction_fn: The function to use for extraction.
        extractions_dir: The directory to save extractions to.
        idx: The current chapter index.
        total: The total number of chapters.
        semaphore: Semaphore for concurrency control.
        storage: The storage provider for persistence.
        progress: Optional callback for progress updates.

    Returns:
        A tuple of (chapter_number, extraction_data).
    """
    if progress:
        progress(
            models.ProgressUpdate(
                stage="extraction",
                current=idx,
                total=total,
                message=f"Extracting chapter {chapter.number}: {chapter.title}",
            )
        )

    if storage.extraction_exists(extractions_dir, chapter.number):
        logger.info(f"Loading cached extraction for chapter {chapter.number}")
        result = storage.load_extraction(extractions_dir, chapter.number)
    else:
        async with semaphore:
            result = await extraction_fn(chapter)
            storage.save_extraction(extractions_dir, chapter.number, result)

    return chapter.number, result


async def _extract_all_chapters(
    book: models.Book,
    extraction_fn: Callable[[models.Chapter], Awaitable[dict[str, list[str]]]],
    extractions_dir: Path,
    storage: StorageProvider,
    progress: Callable[[models.ProgressUpdate], None] | None = None,
) -> dict[int, dict[str, list[str]]]:
    """Extract entities from all chapters in parallel with throttling.

    Args:
        book: The book to extract from.
        extraction_fn: The function to use for extraction.
        extractions_dir: The directory to save extractions to.
        storage: The storage provider for persistence.
        progress: Optional callback for progress updates.

    Returns:
        A dictionary mapping chapter numbers to extraction data.
    """
    total_chapters = len(book.chapters)
    logger.info(f"Extracting entities from {total_chapters} chapters")

    semaphore = asyncio.Semaphore(10)

    tasks = [
        _extract_chapter(
            chapter,
            extraction_fn,
            extractions_dir,
            idx,
            total_chapters,
            semaphore,
            storage,
            progress,
        )
        for idx, chapter in enumerate(book.chapters, 1)
    ]

    results = await asyncio.gather(*tasks)
    return dict(results)


async def _analyze_batch(
    target_categories: list[models.CategoryTarget],
    chapter: models.Chapter,
    profiles_dir: Path,
    analysis_fn: Callable[
        [list[models.CategoryTarget], models.Chapter],
        Awaitable[list[models.EntityProfile]],
    ],
    storage: StorageProvider,
) -> list[models.EntityProfile]:
    """Analyze a batch of entities synchronously with abstracted storage.

    Args:
        target_categories: The categories and entities to analyze.
        chapter: The chapter context for analysis.
        profiles_dir: The directory to save profiles to.
        analysis_fn: The function to use for analysis.
        storage: The storage provider for persistence.

    Returns:
        A list of analyzed entity profiles.
    """
    profiles: list[models.EntityProfile] = []
    to_analyze: list[models.CategoryTarget] = []

    for cat_target in target_categories:
        category = cat_target.name
        entities_to_run = []
        for name in cat_target.entities:
            if storage.profile_exists(
                profiles_dir, chapter.number, category, name
            ):
                profiles.append(
                    storage.load_profile(
                        profiles_dir, chapter.number, category, name
                    )
                )
            else:
                entities_to_run.append(name)

        if entities_to_run:
            to_analyze.append(
                models.CategoryTarget(name=category, entities=entities_to_run)
            )

    if not to_analyze:
        return profiles

    analyzed_profiles = await analysis_fn(to_analyze, chapter)
    for p in analyzed_profiles:
        storage.save_profile(profiles_dir, chapter.number, p)
        profiles.append(p)

    return profiles


async def _analyze_all_entities(
    entities: SortedExtractions,
    book: models.Book,
    profiles_dir: Path,
    analysis_fn: Callable[
        [list[models.CategoryTarget], models.Chapter],
        Awaitable[list[models.EntityProfile]],
    ],
    storage: StorageProvider,
    progress: Callable[[models.ProgressUpdate], None] | None = None,
) -> list[models.EntityProfile]:
    """Analyze all entities sequentially with abstracted storage.

    Args:
        entities: The sorted extractions to analyze.
        book: The book context.
        profiles_dir: The directory to save profiles to.
        analysis_fn: The function to use for analysis.
        storage: The storage provider for persistence.
        progress: Optional callback for progress updates.

    Returns:
        A list of all analyzed entity profiles.
    """
    chapter_map = {ch.number: ch for ch in book.chapters}
    chapter_entities: dict[int, dict[str, list[str]]] = {}

    for category, entity_chapters in entities.items():
        for entity_name, chapters in entity_chapters.items():
            for chapter_num in chapters:
                if chapter_num not in chapter_entities:
                    chapter_entities[chapter_num] = {}
                if category not in chapter_entities[chapter_num]:
                    chapter_entities[chapter_num][category] = []
                chapter_entities[chapter_num][category].append(entity_name)

    profiles = []
    batch_tasks = []

    for chapter_num, cat_map in chapter_entities.items():
        chapter = chapter_map.get(chapter_num)
        if not chapter:
            continue

        for category, names in cat_map.items():
            batch_targets = [
                models.CategoryTarget(name=category, entities=names)
            ]
            batch_tasks.append((batch_targets, chapter))

    total_batches = len(batch_tasks)
    logger.info(
        f"Analyzing {total_batches} entity batches "
        f"across {len(chapter_entities)} chapters"
    )

    for idx, (batch, chapter) in enumerate(batch_tasks, 1):
        if progress:
            progress(
                models.ProgressUpdate(
                    stage="analysis",
                    current=idx,
                    total=total_batches,
                    message=(
                        f"Analyzing batch {idx}/{total_batches} "
                        f"(Chapter {chapter.number})"
                    ),
                )
            )
        batch_profiles = await _analyze_batch(
            batch, chapter, profiles_dir, analysis_fn, storage
        )
        profiles.extend(batch_profiles)

    return profiles


def _aggregate_to_binder(
    profiles: list[models.EntityProfile],
) -> models.Binder:
    """Aggregate profiles into the Binder model, cleaning traits.

    Args:
        profiles: The list of entity profiles to aggregate.

    Returns:
        A Binder model containing all aggregated entities.
    """
    binder = models.Binder()
    for p in profiles:
        if cleaned := clean_traits(p.traits):
            binder.add_appearance(
                category=p.category,
                name=p.name,
                chapter=p.chapter_number,
                traits=cleaned,
            )
    return binder


async def build_binder(
    config: models.RunConfiguration,
    ingestion: Callable[[Path, Path], models.Book],
    extraction: Callable[[models.Chapter], Awaitable[dict[str, list[str]]]],
    analysis: Callable[
        [list[models.CategoryTarget], models.Chapter],
        Awaitable[list[models.EntityProfile]],
    ],
    reporting: Callable[[models.Binder, Path], None],
    summarization_agent: Agent[models.AgentDeps, models.SummarizerResult]
    | None = None,
    progress: Callable[[models.ProgressUpdate], None] | None = None,
    storage: StorageProvider | None = None,
) -> None:
    """Execute the LoreBinders build pipeline.

    Args:
        config: The run configuration.
        ingestion: The function to use for ingestion.
        extraction: The function to use for extraction.
        analysis: The function to use for analysis.
        reporting: The function to use for reporting.
        summarization_agent: Optional agent for summarization.
        progress: Optional callback for progress updates.
        storage: Optional storage provider.
    """
    if storage is None:
        storage = FilesystemStorage()

    logger.info(
        f"Starting binder build for {config.book_title} by {config.author_name}"
    )
    output_dir = storage.ensure_workspace(config.author_name, config.book_title)
    profiles_dir = output_dir / "profiles"
    profiles_dir.mkdir(exist_ok=True)
    extractions_dir = output_dir / "extractions"
    extractions_dir.mkdir(exist_ok=True)
    summaries_dir = output_dir / "summaries"
    summaries_dir.mkdir(exist_ok=True)

    logger.debug("Ingesting book...")
    book = ingestion(config.book_path, output_dir)

    logger.debug("Starting extraction phase...")
    raw_extractions = await _extract_all_chapters(
        book, extraction, extractions_dir, storage, progress
    )

    logger.debug("Starting early refinement...")
    narrator_name = (
        config.narrator_config.name if config.narrator_config else None
    )
    sorted_extractions = sort_extractions(raw_extractions, narrator_name)

    logger.debug("Starting analysis phase...")
    profiles = await _analyze_all_entities(
        sorted_extractions,
        book,
        profiles_dir,
        analysis,
        storage,
        progress=progress,
    )

    logger.debug("Aggregating profiles and cleaning traits...")
    binder = _aggregate_to_binder(profiles)

    logger.debug("Starting summarization phase...")
    await summarize_binder(binder, summaries_dir, summarization_agent, storage)

    safe_title = sanitize_filename(config.book_title)
    output_file = output_dir / f"{safe_title}_story_bible.pdf"
    logger.debug(f"Generating report to {output_file}...")
    reporting(binder, output_file)
    logger.debug("Report generation complete.")
