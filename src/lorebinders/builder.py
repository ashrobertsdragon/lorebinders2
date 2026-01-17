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


def _profiles_to_binder(
    profiles: list[models.CharacterProfile],
) -> dict[str, Any]:
    """Convert list of profiles to binder dict format.

    Args:
        profiles (list[models.CharacterProfile]): The profiles to convert.

    Returns:
        dict[str, Any]: The binder dict format.
    """
    binder: dict[str, dict[str, Any]] = {"Characters": {}}

    for p in profiles:
        if p.name not in binder["Characters"]:
            binder["Characters"][p.name] = p.traits
        else:
            current = binder["Characters"][p.name]

            if isinstance(current, dict) and isinstance(p.traits, dict):
                binder["Characters"][p.name].update(p.traits)

    return binder


def _binder_to_profiles(
    binder: dict[str, Any],
) -> list[models.CharacterProfile]:
    """Convert binder dict format back to list of profiles.

    Args:
        binder (dict[str, Any]): The binder dict format.

    Returns:
        list[models.CharacterProfile]: The list of profiles.
    """
    profiles = []
    if "Characters" in binder and isinstance(binder["Characters"], dict):
        for name, data in binder["Characters"].items():
            if isinstance(data, dict):
                profiles.append(
                    models.CharacterProfile(
                        name=name, traits=data, confidence_score=1.0
                    )
                )
    return profiles


def _analyze_character(
    name: str,
    chapter: models.Chapter,
    profiles_dir: Path,
    analysis_fn: Callable[[str, models.Chapter], models.CharacterProfile],
) -> models.CharacterProfile:
    """Analyze a single character, checking persistence first.

    Args:
        name: The name of the character.
        chapter: The chapter context.
        profiles_dir: Directory for persistence.
        analysis_fn: Function to perform analysis.

    Returns:
        The analyzed profile.
    """
    if profile_exists(profiles_dir, chapter.number, name):
        return load_profile(profiles_dir, chapter.number, name)

    profile = analysis_fn(name, chapter)

    save_profile(profiles_dir, chapter.number, profile)
    return profile


def _process_chapter(
    chapter: models.Chapter,
    profiles_dir: Path,
    extraction_fn: Callable[[models.Chapter], list[str]],
    analysis_fn: Callable[[str, models.Chapter], models.CharacterProfile],
) -> list[models.CharacterProfile]:
    """Process a single chapter: extract and analyze characters.

    Args:
        chapter: The chapter to process.
        profiles_dir: Directory for persistence.
        extraction_fn: Function to extract entities.
        analysis_fn: Function to analyze entities.

    Returns:
        A list of character profiles found in this chapter.
    """
    names = extraction_fn(chapter)

    chapter_profiles = []
    for name in names:
        profile = _analyze_character(name, chapter, profiles_dir, analysis_fn)
        chapter_profiles.append(profile)

    return chapter_profiles


def build_binder(
    config: models.RunConfiguration,
    ingestion: Callable[[Path, Path], models.Book],
    extraction: Callable[[models.Chapter], list[str]],
    analysis: Callable[[str, models.Chapter], models.CharacterProfile],
    reporting: Callable[[list[models.CharacterProfile], Path], None],
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

    all_profiles: list[models.CharacterProfile] = []

    for chapter in book.chapters:
        chapter_profiles = _process_chapter(
            chapter, profiles_dir, extraction, analysis
        )
        all_profiles.extend(chapter_profiles)

    raw_binder = _profiles_to_binder(all_profiles)

    narrator_name = (
        config.narrator_config.name if config.narrator_config else None
    )
    refined_binder = refine_binder(raw_binder, narrator_name)

    final_profiles = _binder_to_profiles(refined_binder)

    safe_title = sanitize_filename(config.book_title)
    reporting(final_profiles, output_dir / f"{safe_title}_story_bible.pdf")
