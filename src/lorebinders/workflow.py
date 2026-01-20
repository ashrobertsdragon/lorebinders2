from collections.abc import Callable
from pathlib import Path

from pydantic_ai import Agent

from lorebinders import models
from lorebinders.agent.summarization import summarize_binder
from lorebinders.models import (
    AgentDeps,
    Binder,
    EntityTarget,
    ProgressUpdate,
    SummarizerResult,
)
from lorebinders.refinement import refine_binder
from lorebinders.refinement.deduplication import (
    _is_similar_key,
    _prioritize_keys,
)
from lorebinders.storage.profiles import (
    load_profile,
    profile_exists,
    save_profile,
)
from lorebinders.storage.workspace import ensure_workspace, sanitize_filename


def _extract_all_chapters(
    book: models.Book,
    extraction_fn: Callable[[models.Chapter], dict[str, list[str]]],
    progress: Callable[[ProgressUpdate], None] | None = None,
) -> dict[int, dict[str, list[str]]]:
    """Extract entities from all chapters.

    Args:
        book: The book containing chapters.
        extraction_fn: Function to extract entities from a chapter.
        progress: Optional callback for progress updates.

    Returns:
        Map of chapter number to category to list of entity names.
    """
    raw_extractions: dict[int, dict[str, list[str]]] = {}
    total_chapters = len(book.chapters)

    for idx, chapter in enumerate(book.chapters, 1):
        if progress:
            progress(
                ProgressUpdate(
                    stage="extraction",
                    current=idx,
                    total=total_chapters,
                    message=(
                        f"Extracting chapter {chapter.number}: {chapter.title}"
                    ),
                )
            )
        raw_extractions[chapter.number] = extraction_fn(chapter)

    return raw_extractions


def _deduplicate_entity_names(
    names: list[str],
) -> list[str]:
    """Deduplicate a list of entity names using existing similarity logic.

    Returns:
        List of deduplicated entity names.
    """
    if len(names) <= 1:
        return names

    canonical_names: list[str] = []
    for name in names:
        found_match = False
        for i, existing in enumerate(canonical_names):
            if _is_similar_key(name, existing):
                _, keeper = _prioritize_keys(name, existing)
                canonical_names[i] = keeper
                found_match = True
                break
        if not found_match:
            canonical_names.append(name)
    return canonical_names


def _aggregate_extractions(
    raw_extractions: dict[int, dict[str, list[str]]],
) -> dict[str, dict[str, list[int]]]:
    """Aggregate extracted names into entity -> chapters mapping.

    Args:
        raw_extractions: Map of chapter number to category to names.

    Returns:
        Map of category to entity name to list of chapter numbers.
    """
    aggregated: dict[str, dict[str, list[int]]] = {}

    for chapter_num, categories in raw_extractions.items():
        for category, names in categories.items():
            if category not in aggregated:
                aggregated[category] = {}

            deduped = _deduplicate_entity_names(names)
            for name in deduped:
                clean_name = name.strip()
                if not clean_name:
                    continue

                found = False
                for existing in list(aggregated[category].keys()):
                    if _is_similar_key(clean_name, existing):
                        _, keeper = _prioritize_keys(clean_name, existing)
                        if keeper != existing:
                            aggregated[category][keeper] = aggregated[
                                category
                            ].pop(existing)
                        if chapter_num not in aggregated[category][keeper]:
                            aggregated[category][keeper].append(chapter_num)
                        found = True
                        break
                if not found:
                    aggregated[category][clean_name] = [chapter_num]

    return aggregated


def _analyze_batch(
    target_entities: list[EntityTarget],
    chapter: models.Chapter,
    profiles_dir: Path,
    analysis_fn: Callable[
        [list[EntityTarget], models.Chapter], list[models.EntityProfile]
    ],
) -> list[models.EntityProfile]:
    """Analyze a batch of entities, skipping already analyzed ones.

    Returns:
        List of EntityProfile objects (loaded or newly analyzed).
    """
    profiles: list[models.EntityProfile] = []
    to_analyze: list[EntityTarget] = []

    for entity in target_entities:
        name = entity["name"]
        category = entity["category"]
        if profile_exists(profiles_dir, chapter.number, category, name):
            profiles.append(
                load_profile(profiles_dir, chapter.number, category, name)
            )
        else:
            to_analyze.append(entity)

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
        [list[EntityTarget], models.Chapter], list[models.EntityProfile]
    ],
    batch_size: int = 5,
    progress: Callable[[ProgressUpdate], None] | None = None,
) -> list[models.EntityProfile]:
    """Analyze all entities across all their chapter appearances.

    Args:
        entities: Map of category to entity name to chapter numbers.
        book: The book with chapters.
        profiles_dir: Directory for persistence.
        analysis_fn: Function to analyze a batch of entities.
        batch_size: Number of entities to analyze in one call.

    Returns:
        List of all entity profiles.
    """
    chapter_map = {ch.number: ch for ch in book.chapters}

    chapter_entities: dict[int, list[EntityTarget]] = {}

    for category, entity_chapters in entities.items():
        for entity_name, chapters in entity_chapters.items():
            for chapter_num in chapters:
                if chapter_num not in chapter_entities:
                    chapter_entities[chapter_num] = []

                chapter_entities[chapter_num].append(
                    EntityTarget(name=entity_name, category=category)
                )

    profiles: list[models.EntityProfile] = []

    total_batches = 0
    batch_tasks = []

    for chapter_num, targets in chapter_entities.items():
        chapter = chapter_map.get(chapter_num)
        if not chapter:
            continue
        for i in range(0, len(targets), batch_size):
            batch_tasks.append((targets[i : i + batch_size], chapter))

    total_batches = len(batch_tasks)

    for idx, (batch, chapter) in enumerate(batch_tasks, 1):
        if progress:
            progress(
                ProgressUpdate(
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
) -> Binder:
    """Convert list of profiles to binder dict format.

    Returns:
        Binder dict: {Category: {Name: {ChapterNum: Traits}}}
    """
    binder: Binder = {}

    for p in profiles:
        if p.category not in binder:
            binder[p.category] = {}
        if p.name not in binder[p.category]:
            binder[p.category][p.name] = {}
        binder[p.category][p.name][p.chapter_number] = p.traits

    return binder


def _binder_to_profiles(
    binder: Binder,
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


def build_binder(
    config: models.RunConfiguration,
    ingestion: Callable[[Path, Path], models.Book],
    extraction: Callable[[models.Chapter], dict[str, list[str]]],
    analysis: Callable[
        [list[EntityTarget], models.Chapter], list[models.EntityProfile]
    ],
    reporting: Callable[[list[models.EntityProfile], Path], None],
    summarization_agent: Agent[AgentDeps, SummarizerResult] | None = None,
    progress: Callable[[ProgressUpdate], None] | None = None,
) -> None:
    """Execute the LoreBinders build pipeline.

    Pipeline: Ingest -> Extract -> Dedupe -> Analyze -> Refine -> Report
    """
    output_dir = ensure_workspace(config.author_name, config.book_title)
    profiles_dir = output_dir / "profiles"
    profiles_dir.mkdir(exist_ok=True)

    book = ingestion(config.book_path, output_dir)

    raw_extractions = _extract_all_chapters(book, extraction, progress)

    entities = _aggregate_extractions(raw_extractions)

    profiles = _analyze_all_entities(
        entities,
        book,
        profiles_dir,
        analysis,
        progress=progress,
    )

    raw_binder = _aggregate_profiles_to_binder(profiles)

    narrator_name = (
        config.narrator_config.name if config.narrator_config else None
    )
    refined_binder = refine_binder(raw_binder, narrator_name)

    summarized_binder = summarize_binder(refined_binder, summarization_agent)

    final_profiles = _binder_to_profiles(summarized_binder)

    safe_title = sanitize_filename(config.book_title)
    reporting(final_profiles, output_dir / f"{safe_title}_story_bible.pdf")
