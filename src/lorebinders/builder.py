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


class LoreBinderBuilder:
    """Orchestrator for the LoreBinders build process."""

    def __init__(
        self,
        ingestion: Callable[[Path, Path], models.Book],
        extraction: Callable[[models.Chapter], list[str]],
        analysis: Callable[[str, models.Chapter], models.CharacterProfile],
        reporting: Callable[[list[models.CharacterProfile], Path], None],
    ):
        """Initialize with required providers and agents."""
        self.ingestion = ingestion
        self.extraction = extraction
        self.analysis = analysis
        self.reporting = reporting

    def _profiles_to_binder(
        self, profiles: list[models.CharacterProfile]
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
        self, binder: dict[str, Any]
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

    def _process_chapter(
        self,
        chapter: models.Chapter,
        profiles_dir: Path,
    ) -> list[models.CharacterProfile]:
        """Process a single chapter: extract and analyze characters.

        Args:
            chapter: The chapter to process.
            profiles_dir: Directory for persistence.

        Returns:
            A list of character profiles found in this chapter.
        """
        names = self.extraction(chapter)

        chapter_profiles = []
        for name in names:
            profile = self._analyze_character(name, chapter, profiles_dir)
            chapter_profiles.append(profile)

        return chapter_profiles

    def _analyze_character(
        self,
        name: str,
        chapter: models.Chapter,
        profiles_dir: Path,
    ) -> models.CharacterProfile:
        """Analyze a single character, checking persistence first.

        Args:
            name: The name of the character.
            chapter: The chapter context.
            profiles_dir: Directory for persistence.

        Returns:
            The analyzed profile.
        """
        if profile_exists(profiles_dir, chapter.number, name):
            return load_profile(profiles_dir, chapter.number, name)

        profile = self.analysis(name, chapter)

        save_profile(profiles_dir, chapter.number, profile)
        return profile

    def run(self, config: models.RunConfiguration) -> None:
        """Execute the build pipeline synchronously."""
        output_dir = ensure_workspace(config.author_name, config.book_title)
        profiles_dir = output_dir / "profiles"
        profiles_dir.mkdir(exist_ok=True)

        book = self.ingestion(config.book_path, output_dir)

        all_profiles: list[models.CharacterProfile] = []

        for chapter in book.chapters:
            chapter_profiles = self._process_chapter(chapter, profiles_dir)
            all_profiles.extend(chapter_profiles)

        raw_binder = self._profiles_to_binder(all_profiles)

        narrator_name = (
            config.narrator_config.name if config.narrator_config else None
        )
        refined_binder = refine_binder(raw_binder, narrator_name)

        final_profiles = self._binder_to_profiles(refined_binder)

        safe_title = sanitize_filename(config.book_title)
        self.reporting(
            final_profiles, output_dir / f"{safe_title}_story_bible.pdf"
        )
