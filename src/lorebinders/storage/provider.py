from pathlib import Path
from typing import Protocol

from lorebinders import models
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
from lorebinders.storage.summaries import (
    load_summary,
    save_summary,
    summary_exists,
)
from lorebinders.storage.workspace import ensure_workspace


class StorageProvider(Protocol):
    """Protocol for LoreBinders storage backends."""

    def ensure_workspace(self, author: str, title: str) -> Path:
        """Ensure the workspace directory exists.

        Returns:
            The path to the workspace.
        """
        ...

    def extraction_exists(
        self, extractions_dir: Path, chapter_num: int
    ) -> bool:
        """Check if extraction exists.

        Returns:
            True if it exists.
        """
        ...

    def save_extraction(
        self,
        extractions_dir: Path,
        chapter_num: int,
        data: dict[str, list[str]],
    ) -> None:
        """Save extraction data."""
        ...

    def load_extraction(
        self, extractions_dir: Path, chapter_num: int
    ) -> dict[str, list[str]]:
        """Load extraction data.

        Returns:
            The extraction data.
        """
        ...

    def profile_exists(
        self, profiles_dir: Path, chapter_num: int, category: str, name: str
    ) -> bool:
        """Check if profile exists.

        Returns:
            True if it exists.
        """
        ...

    def save_profile(
        self,
        profiles_dir: Path,
        chapter_num: int,
        profile: models.EntityProfile,
    ) -> None:
        """Save profile data."""
        ...

    def load_profile(
        self, profiles_dir: Path, chapter_num: int, category: str, name: str
    ) -> models.EntityProfile:
        """Load profile data.

        Returns:
            The entity profile.
        """
        ...

    def summary_exists(
        self, summaries_dir: Path, category: str, name: str
    ) -> bool:
        """Check if summary exists.

        Returns:
            True if it exists.
        """
        ...

    def save_summary(
        self, summaries_dir: Path, category: str, name: str, summary: str
    ) -> None:
        """Save summary data."""
        ...

    def load_summary(
        self, summaries_dir: Path, category: str, name: str
    ) -> str:
        """Load summary data.

        Returns:
            The summary text.
        """
        ...


class FilesystemStorage:
    """Standard filesystem-based storage implementation."""

    def ensure_workspace(self, author: str, title: str) -> Path:
        """Ensure the workspace directory exists.

        Returns:
            The path to the workspace.
        """
        return ensure_workspace(author, title)

    def extraction_exists(
        self, extractions_dir: Path, chapter_num: int
    ) -> bool:
        """Check if extraction exists.

        Returns:
            True if it exists.
        """
        return extraction_exists(extractions_dir, chapter_num)

    def save_extraction(
        self,
        extractions_dir: Path,
        chapter_num: int,
        data: dict[str, list[str]],
    ) -> None:
        """Save extraction data."""
        save_extraction(extractions_dir, chapter_num, data)

    def load_extraction(
        self, extractions_dir: Path, chapter_num: int
    ) -> dict[str, list[str]]:
        """Load extraction data.

        Returns:
            The extraction data.
        """
        return load_extraction(extractions_dir, chapter_num)

    def profile_exists(
        self, profiles_dir: Path, chapter_num: int, category: str, name: str
    ) -> bool:
        """Check if profile exists.

        Returns:
            True if it exists.
        """
        return profile_exists(profiles_dir, chapter_num, category, name)

    def save_profile(
        self,
        profiles_dir: Path,
        chapter_num: int,
        profile: models.EntityProfile,
    ) -> None:
        """Save profile data."""
        save_profile(profiles_dir, chapter_num, profile)

    def load_profile(
        self, profiles_dir: Path, chapter_num: int, category: str, name: str
    ) -> models.EntityProfile:
        """Load profile data.

        Returns:
            The entity profile.
        """
        return load_profile(profiles_dir, chapter_num, category, name)

    def summary_exists(
        self, summaries_dir: Path, category: str, name: str
    ) -> bool:
        """Check if summary exists.

        Returns:
            True if it exists.
        """
        return summary_exists(summaries_dir, category, name)

    def save_summary(
        self, summaries_dir: Path, category: str, name: str, summary: str
    ) -> None:
        """Save summary data."""
        save_summary(summaries_dir, category, name, summary)

    def load_summary(
        self, summaries_dir: Path, category: str, name: str
    ) -> str:
        """Load summary data.

        Returns:
            The summary text.
        """
        return load_summary(summaries_dir, category, name)
