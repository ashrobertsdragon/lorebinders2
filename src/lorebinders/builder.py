from pathlib import Path

from lorebinders.core import models
from lorebinders.core.interfaces import (
    AnalysisAgent,
    ExtractionAgent,
    IngestionProvider,
    ReportingProvider,
)


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

    def run(self, config: models.RunConfiguration) -> None:
        """Execute the build pipeline."""
        output_dir = Path("work") / config.author_name / config.book_title
        output_dir.mkdir(parents=True, exist_ok=True)

        book = self.ingestion.ingest(config.book_path, output_dir)

        all_profiles: list[models.CharacterProfile] = []

        for chapter in book.chapters:
            names = self.extraction.extract(chapter)

            for name in names:
                profile = self.analysis.analyze(name, chapter)
                all_profiles.append(profile)

        self.reporting.generate(all_profiles, output_dir)
