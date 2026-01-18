from collections.abc import Callable
from pathlib import Path
from typing import Any

from lorebinders import models
from lorebinders.ingestion.persistence import (
    load_profile,
    profile_exists,
    save_profile,
)
from lorebinders.ingestion.workspace import ensure_workspace, sanitize_filename
from lorebinders.refinement.manager import refine_binder


def _aggregate_book_data(book: models.Book) -> dict[str, Any]:
    """Aggregate data from all chapters into a binder dict.

    Iterates through the book's chapters and aggregates the profiles
    stored on each chapter into a nested binder structure.

    Args:
        book: The book containing chapters with profiles.

    Returns:
        The aggregated binder dict: {Category: {Name: {ChapterNum: Traits}}}
    """
    binder: dict[str, dict[str, Any]] = {}

    for chapter in book.chapters:
        for p in chapter.profiles:
            if p.category not in binder:
                binder[p.category] = {}

            if p.name not in binder[p.category]:
                binder[p.category][p.name] = {}

            binder[p.category][p.name][chapter.number] = p.traits

    return binder


def _binder_to_profiles(
    binder: dict[str, Any],
) -> list[models.EntityProfile]:
    """Convert binder dict format back to list of profiles.

    Args:
        binder (dict[str, Any]): The binder dict format.

    Returns:
        list[models.EntityProfile]: The list of profiles.
    """
    profiles = []
    for category, entities in binder.items():
        if isinstance(entities, dict):
            for name, data in entities.items():
                if isinstance(data, dict):
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


def _analyze_character(
    name: str,
    category: str,
    chapter: models.Chapter,
    profiles_dir: Path,
    analysis_fn: Callable[[str, str, models.Chapter], models.EntityProfile],
) -> models.EntityProfile:
    """Analyze a single entity, checking persistence first.

    Args:
        name: The name of the entity.
        category: The category of the entity.
        chapter: The chapter context.
        profiles_dir: Directory for persistence.
        analysis_fn: Function to perform analysis.

    Returns:
        The analyzed profile.
    """
    if profile_exists(profiles_dir, chapter.number, category, name):
        return load_profile(profiles_dir, chapter.number, category, name)

    profile = analysis_fn(name, category, chapter)

    save_profile(profiles_dir, chapter.number, profile)
    return profile


def _process_chapter(
    chapter: models.Chapter,
    profiles_dir: Path,
    extraction_fn: Callable[[models.Chapter], dict[str, list[str]]],
    analysis_fn: Callable[[str, str, models.Chapter], models.EntityProfile],
) -> list[models.EntityProfile]:
    """Process a single chapter: extract and analyze entities.

    Args:
        chapter: The chapter to process.
        profiles_dir: Directory for persistence.
        extraction_fn: Function to extract entities (Category -> Names).
        analysis_fn: Function to analyze entities.

    Returns:
        A list of entity profiles found in this chapter.
    """
    extracted_data = extraction_fn(chapter)

    chapter_profiles = []
    for category, names in extracted_data.items():
        for name in names:
            profile = _analyze_character(
                name, category, chapter, profiles_dir, analysis_fn
            )
            chapter_profiles.append(profile)

    return chapter_profiles


def build_binder(
    config: models.RunConfiguration,
    ingestion: Callable[[Path, Path], models.Book],
    extraction: Callable[[models.Chapter], dict[str, list[str]]],
    analysis: Callable[[str, str, models.Chapter], models.EntityProfile],
    reporting: Callable[[list[models.EntityProfile], Path], None],
) -> None:
    """Execute the LoreBinders build pipeline.

    Args:
        config: Configuration for the build run.
        ingestion: Function to ingest the book.
        extraction: Function to extract entities from a chapter.
        analysis: Function to analyze an entity in a chapter.
        reporting: Function to generate the final report.
    """
    output_dir = ensure_workspace(config.author_name, config.book_title)
    profiles_dir = output_dir / "profiles"
    profiles_dir.mkdir(exist_ok=True)

    book = ingestion(config.book_path, output_dir)

    for chapter in book.chapters:
        chapter.profiles = _process_chapter(
            chapter, profiles_dir, extraction, analysis
        )

    raw_binder = _aggregate_book_data(book)

    narrator_name = (
        config.narrator_config.name if config.narrator_config else None
    )
    refined_binder = refine_binder(raw_binder, narrator_name)

    final_profiles = _binder_to_profiles(refined_binder)

    safe_title = sanitize_filename(config.book_title)
    reporting(final_profiles, output_dir / f"{safe_title}_story_bible.pdf")
