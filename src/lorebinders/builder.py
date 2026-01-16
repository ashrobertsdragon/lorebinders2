from typing import Any

from lorebinders.core import models
from lorebinders.core.interfaces import (
    AnalysisAgent,
    ExtractionAgent,
    IngestionProvider,
    ReportingProvider,
)
from lorebinders.ingestion.workspace import WorkspaceManager
from lorebinders.refinement.manager import refine_binder


class LoreBinderBuilder:
    """Orchestrator for the LoreBinders build process."""

    def __init__(
        self,
        ingestion: IngestionProvider,
        extraction: ExtractionAgent,
        analysis: AnalysisAgent,
        reporting: ReportingProvider,
    ):
        """Initialize with required providers and agents."""
        self.ingestion = ingestion
        self.extraction = extraction
        self.analysis = analysis
        self.reporting = reporting
        self.workspace_manager = WorkspaceManager()

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

    def run(self, config: models.RunConfiguration) -> None:
        """Execute the build pipeline."""
        output_dir = self.workspace_manager.ensure_workspace(
            config.author_name, config.book_title
        )

        book = self.ingestion(config.book_path, output_dir)

        all_profiles: list[models.CharacterProfile] = []

        for chapter in book.chapters:
            names = self.extraction.extract(chapter)

            for name in names:
                profile = self.analysis.analyze(name, chapter)
                all_profiles.append(profile)

        raw_binder = self._profiles_to_binder(all_profiles)

        narrator_name = (
            config.narrator_config.name if config.narrator_config else None
        )
        refined_binder = refine_binder(raw_binder, narrator_name)

        final_profiles = self._binder_to_profiles(refined_binder)

        safe_title = self.workspace_manager.sanitize_filename(config.book_title)
        self.reporting(
            final_profiles, output_dir / f"{safe_title}_story_bible.pdf"
        )
