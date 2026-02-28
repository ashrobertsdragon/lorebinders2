"""Dummy storage provider for testing purposes."""

from pathlib import Path

import lorebinders.models as models


class TestStorageProvider:
    """In-memory storage provider for testing purposes."""

    def set_workspace(self, author: str, title: str) -> None:
        """Create a workspace for testing."""
        self._path = Path(f"/mock/{author}/{title}")
        self.extractions: dict[int, dict[str, list[str]]] = {}
        self.profiles: dict[tuple[int, str, str], models.EntityProfile] = {}
        self.summaries: dict[tuple[str, str], str] = {}

    @property
    def path(self) -> Path:
        """The base path of the workspace."""
        if not self._path:
            raise RuntimeError("Workspace not set")
        return self._path

    def extraction_exists(self, chapter_num: int) -> bool:
        """Check if extraction exists."""
        return chapter_num in self.extractions

    def save_extraction(
        self,
        chapter_num: int,
        data: dict[str, list[str]],
    ) -> None:
        """Save extraction data."""
        self.extractions[chapter_num] = data

    def load_extraction(self, chapter_num: int) -> dict[str, list[str]]:
        """Load extraction data."""
        if chapter_num not in self.extractions:
            raise FileNotFoundError(
                f"Extraction for chapter {chapter_num} not found"
            )
        return self.extractions[chapter_num]

    def profile_exists(
        self, chapter_num: int, category: str, name: str
    ) -> bool:
        """Check if profile exists."""
        return (chapter_num, category, name) in self.profiles

    def save_profile(
        self,
        chapter_num: int,
        profile: models.EntityProfile,
    ) -> None:
        """Save profile data."""
        self.profiles[(chapter_num, profile.category, profile.name)] = profile

    def load_profile(
        self, chapter_num: int, category: str, name: str
    ) -> models.EntityProfile:
        """Load profile data."""
        key = (chapter_num, category, name)
        if key not in self.profiles:
            raise FileNotFoundError(f"Profile {name} not found")
        return self.profiles[key]

    def summary_exists(self, category: str, name: str) -> bool:
        """Check if summary exists."""
        return (category, name) in self.summaries

    def save_summary(self, category: str, name: str, summary: str) -> None:
        """Save summary data."""
        self.summaries[(category, name)] = summary

    def load_summary(self, category: str, name: str) -> str:
        """Load summary data."""
        key = (category, name)
        if key not in self.summaries:
            raise FileNotFoundError(f"Summary {name} not found")
        return self.summaries[key]
