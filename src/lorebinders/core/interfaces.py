from pathlib import Path
from typing import Protocol, runtime_checkable

from lorebinders.core import models


@runtime_checkable
class IngestionProvider(Protocol):
    """Protocol for ingesting a book from a source file."""

    def ingest(self, source: Path, output_dir: Path) -> models.Book:
        """Ingest a book from source path and save/return the Book model."""
        ...


@runtime_checkable
class ExtractionAgent(Protocol):
    """Protocol for extracting entities (names) from text."""

    def extract(self, chapter: models.Chapter) -> list[str]:
        """Extract a list of names from the chapter."""
        ...


@runtime_checkable
class AnalysisAgent(Protocol):
    """Protocol for analyzing a character."""

    def analyze(
        self, name: str, context: models.Chapter
    ) -> models.CharacterProfile:
        """Analyze a character within the context of a chapter."""
        ...


@runtime_checkable
class ReportingProvider(Protocol):
    """Protocol for generating reports."""

    def generate(
        self, data: list[models.CharacterProfile], output_path: Path
    ) -> None:
        """Generate a report (e.g. PDF) from character profiles."""
        ...
