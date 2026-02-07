import logging
from collections.abc import Callable
from pathlib import Path

from pydantic_ai import Agent

from lorebinders import models, types
from lorebinders.agent.summarization import summarize_binder
from lorebinders.refinement import refine_binder
from lorebinders.refinement.sorting import sort_extractions
from lorebinders.storage.extractions import (
    extraction_exists,
    load_extraction,
    save_extraction,
)
from lorebinders.storage.profiles import (
    load_profile,
    profile_exists,
    save_profile,
)
from lorebinders.storage.workspace import ensure_workspace, sanitize_filename

logger = logging.getLogger(__name__)


def _extract_all_chapters(
    book: models.Book,
    extraction_fn: Callable[[models.Chapter], dict[str, list[str]]],
    extractions_dir: Path,
    progress: Callable[[models.ProgressUpdate], None] | None = None,
) -> dict[int, dict[str, list[str]]]:
    """Extract entities from all chapters.

    Args:
        book: The book containing chapters.
        extraction_fn: Function to extract entities from a chapter.
        extractions_dir: Directory for caching extraction results.
        progress: Optional callback for progress updates.

    Returns:
        Map of chapter number to category to list of entity names.
    """
    raw_extractions: dict[int, dict[str, list[str]]] = {}
    total_chapters = len(book.chapters)

    logger.info(f"Extracting entities from {total_chapters} chapters")
    for idx, chapter in enumerate(book.chapters, 1):
        if progress:
            progress(
                models.ProgressUpdate(
                    stage="extraction",
                    current=idx,
                    total=total_chapters,
                    message=(
                        f"Extracting chapter {chapter.number}: {chapter.title}"
                    ),
                )
            )

        if extraction_exists(extractions_dir, chapter.number):
            logger.info(
                f"Loading cached extraction for chapter {chapter.number}"
            )
            raw_extractions[chapter.number] = load_extraction(
                extractions_dir, chapter.number
            )
        else:
            result = extraction_fn(chapter)
            save_extraction(extractions_dir, chapter.number, result)
            raw_extractions[chapter.number] = result

    return raw_extractions


def _analyze_batch(
    target_categories: list[types.CategoryTarget],
    chapter: models.Chapter,
    profiles_dir: Path,
    analysis_fn: Callable[
        [list[types.CategoryTarget], models.Chapter],
        list[models.EntityProfile],
    ],
) -> list[models.EntityProfile]:
    """Analyze a batch of entities, skipping already analyzed ones.

    Returns:
        List of EntityProfile objects (loaded or newly analyzed).
    """
    profiles: list[models.EntityProfile] = []
    to_analyze: list[types.CategoryTarget] = []

    for cat_target in target_categories:
        category = cat_target["name"]
        entities_to_run = []
        for name in cat_target["entities"]:
            if profile_exists(profiles_dir, chapter.number, category, name):
                profiles.append(
                    load_profile(profiles_dir, chapter.number, category, name)
                )
            else:
                entities_to_run.append(name)

        if entities_to_run:
            to_analyze.append(
                types.CategoryTarget(name=category, entities=entities_to_run)
            )

    if not to_analyze:
        return profiles

    analyzed_profiles = analysis_fn(to_analyze, chapter)
    for p in analyzed_profiles:
        save_profile(profiles_dir, chapter.number, p)
        profiles.append(p)

    return profiles


def _analyze_all_entities(
    entities: dict[str, dict[str, list[int]]],
    book: models.Book,
    profiles_dir: Path,
    analysis_fn: Callable[
        [list[types.CategoryTarget], models.Chapter],
        list[models.EntityProfile],
    ],
    progress: Callable[[models.ProgressUpdate], None] | None = None,
) -> list[models.EntityProfile]:
    """Analyze all entities across all their chapter appearances.

    Args:
        entities: Map of category to entity name to chapter numbers.
        book: The book with chapters.
        profiles_dir: Directory for persistence.
        analysis_fn: Function to analyze a batch of entities.
        progress: Optional callback for progress updates.

    Returns:
        List of all entity profiles.
    """
    chapter_map = {ch.number: ch for ch in book.chapters}

    chapter_entities: types.CategoryChapterData = {}

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
                types.CategoryTarget(name=category, entities=names)
            ]
            batch_tasks.append((batch_targets, chapter))

    total_batches = len(batch_tasks)
    logger.info(
        f"Analyzing {total_batches} entity batches across "
        f"{len(chapter_entities)} chapters"
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
        batch_profiles = _analyze_batch(
            batch, chapter, profiles_dir, analysis_fn
        )
        profiles.extend(batch_profiles)

    return profiles


def _aggregate_profiles_to_binder(
    profiles: list[models.EntityProfile],
) -> types.Binder:
    """Convert list of profiles to binder dict format.

    Returns:
        Binder dict: {Category: {Name: {ChapterNum: Traits}}}
    """
    binder: types.Binder = {}

    for p in profiles:
        if p.category not in binder:
            binder[p.category] = {}
        if p.name not in binder[p.category]:
            binder[p.category][p.name] = {}
        binder[p.category][p.name][p.chapter_number] = p.traits

    return binder


def _binder_to_profiles(
    binder: types.Binder,
) -> list[models.EntityProfile]:
    """Convert binder dict format back to list of profiles.

    Returns:
        List of EntityProfile objects.
    """
    profiles = []
    for category, entities in binder.items():
        if not isinstance(entities, dict):
            continue
        for name, data in entities.items():
            if not isinstance(data, dict):
                continue
            for chapter, traits in data.items():
                try:
                    chap_num = int(chapter)
                except (ValueError, TypeError):
                    continue
                if isinstance(traits, dict):
                    profiles.append(
                        models.EntityProfile(
                            name=name,
                            category=category,
                            chapter_number=chap_num,
                            traits=traits,
                            confidence_score=1.0,
                        )
                    )
    return profiles


def _get_summarizable_binder(
    binder: types.Binder, threshold: int = 3
) -> types.Binder:
    """Filter binder for entities meeting chapter threshold.

    Args:
        binder: The source binder to filter.
        threshold: Minimum number of chapters required.

    Returns:
        A new binder containing only qualifying entities.
    """
    result: types.Binder = {}
    for category, entities in binder.items():
        if not isinstance(entities, dict):
            continue

        valid_entities = _filter_category_entities(entities, threshold)
        if valid_entities:
            result[category] = valid_entities
    return result


def _filter_category_entities(
    entities: types.EntityData, threshold: int
) -> types.EntityData:
    """Filter entities within a category by chapter count.

    Args:
        entities: The entity dictionary for a category.
        threshold: Minimum chapter count.

    Returns:
        Dictionary of qualifying entities.
    """
    filtered: types.EntityData = {}
    for name, data in entities.items():
        if not isinstance(data, dict):
            continue
        if len(data) >= threshold:
            filtered[name] = data
    return filtered


def _merge_summary_results(target: types.Binder, source: types.Binder) -> None:
    """Merge summary fields from source binder into target binder.

    Args:
        target: The destination binder to update.
        source: The binder containing generated summaries.
    """
    for category, entities in source.items():
        if not isinstance(entities, dict):
            continue
        _merge_category_summaries(target, category, entities)


def _merge_category_summaries(
    target: types.Binder, category: str, source_entities: types.EntityData
) -> None:
    """Merge summaries for a specific category.

    Args:
        target: The destination binder.
        category: The category key.
        source_entities: The source entities with summaries.
    """
    if category not in target:
        return

    target_entities = target[category]
    if not isinstance(target_entities, dict):
        return

    for name, data in source_entities.items():
        if not isinstance(data, dict):
            continue
        if "Summary" in data:
            _update_entity_summary(target_entities, name, data["Summary"])


def _update_entity_summary(
    entities: types.EntityData, name: str, summary: str | types.TraitDict
) -> None:
    """Update a single entity's summary if it exists in target.

    Args:
        entities: The target entity dictionary.
        name: The entity name.
        summary: The summary text to set.
    """
    if name not in entities:
        return

    entity_data = entities[name]
    if isinstance(entity_data, dict):
        entity_data["Summary"] = summary


def build_binder(
    config: models.RunConfiguration,
    ingestion: Callable[[Path, Path], models.Book],
    extraction: Callable[[models.Chapter], dict[str, list[str]]],
    analysis: Callable[
        [list[types.CategoryTarget], models.Chapter],
        list[models.EntityProfile],
    ],
    reporting: Callable[[types.Binder, Path], None],
    summarization_agent: Agent[models.AgentDeps, models.SummarizerResult]
    | None = None,
    progress: Callable[[models.ProgressUpdate], None] | None = None,
) -> None:
    """Execute the LoreBinders build pipeline.

    Args:
        config: Configuration for the run.
        ingestion: Function to ingest the book.
        extraction: Function to extract entities.
        analysis: Function to analyze entities.
        reporting: Function to generate reports.
        summarization_agent: Agent for summarization.
        progress: Progress callback.
    """
    logger.info(
        f"Starting binder build for {config.book_title} by {config.author_name}"
    )
    output_dir = ensure_workspace(config.author_name, config.book_title)
    profiles_dir = output_dir / "profiles"
    profiles_dir.mkdir(exist_ok=True)
    extractions_dir = output_dir / "extractions"
    extractions_dir.mkdir(exist_ok=True)
    summaries_dir = output_dir / "summaries"
    summaries_dir.mkdir(exist_ok=True)

    logger.debug("Ingesting book...")
    book = ingestion(config.book_path, output_dir)
    logger.debug(f"Book ingested. found {len(book.chapters)} chapters.")

    logger.debug("Starting extraction phase...")
    raw_extractions = _extract_all_chapters(
        book, extraction, extractions_dir, progress
    )
    logger.debug("Extraction phase complete.")

    narrator_name = (
        config.narrator_config.name if config.narrator_config else None
    )

    logger.debug("Sorting extractions...")
    entities = sort_extractions(raw_extractions, narrator_name)
    logger.debug("Extractions sorted.")

    logger.debug("Starting analysis phase...")
    profiles = _analyze_all_entities(
        entities,
        book,
        profiles_dir,
        analysis,
        progress=progress,
    )
    logger.debug("Analysis phase complete.")

    logger.debug("Aggregating profiles...")
    raw_binder = _aggregate_profiles_to_binder(profiles)

    logger.debug("Refining binder...")
    refined_binder = refine_binder(raw_binder, narrator_name)

    logger.debug("Filtering for summarization...")
    summarizable_binder = _get_summarizable_binder(refined_binder, 3)

    logger.debug("Starting summarization phase...")
    partial_summarized_binder = summarize_binder(
        summarizable_binder, summaries_dir, summarization_agent
    )
    logger.debug("Summarization phase complete.")

    logger.debug("Merging summaries...")
    _merge_summary_results(refined_binder, partial_summarized_binder)

    safe_title = sanitize_filename(config.book_title)
    output_file = output_dir / f"{safe_title}_story_bible.pdf"
    logger.debug(f"Generating report to {output_file}...")
    reporting(refined_binder, output_file)
    logger.debug("Report generation complete.")
