"""Interfaces and protocols for LoreBinders components."""

from collections.abc import Callable
from pathlib import Path
from typing import Protocol, runtime_checkable

from lorebinders.core import models

IngestionProvider = Callable[[Path, Path], models.Book]


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


ReportingProvider = Callable[[list[models.CharacterProfile], Path], None]
