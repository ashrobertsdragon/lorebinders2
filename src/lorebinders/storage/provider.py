from pathlib import Path
from typing import Protocol

from lorebinders import models


class StorageProvider(Protocol):
    """Protocol for LoreBinders storage backends."""

    def set_workspace(self, author: str, title: str) -> None:
        """Set the active workspace for this storage provider.

        Args:
            author: The author name.
            title: The book title.
        """
        ...

    @property
    def path(self) -> Path:
        """The base path of the workspace."""
        ...

    def extraction_exists(self, chapter_num: int) -> bool:
        """Check if extraction exists.

        Returns:
            True if it exists.
        """
        ...

    def save_extraction(
        self,
        chapter_num: int,
        data: dict[str, list[str]],
    ) -> None:
        """Save extraction data."""
        ...

    def load_extraction(self, chapter_num: int) -> dict[str, list[str]]:
        """Load extraction data.

        Returns:
            The extraction data.
        """
        ...

    def profile_exists(
        self, chapter_num: int, category: str, name: str
    ) -> bool:
        """Check if profile exists.

        Returns:
            True if it exists.
        """
        ...

    def save_profile(
        self,
        chapter_num: int,
        profile: models.EntityProfile,
    ) -> None:
        """Save profile data."""
        ...

    def load_profile(
        self, chapter_num: int, category: str, name: str
    ) -> models.EntityProfile:
        """Load profile data.

        Returns:
            The entity profile.
        """
        ...

    def summary_exists(self, category: str, name: str) -> bool:
        """Check if summary exists.

        Returns:
            True if it exists.
        """
        ...

    def save_summary(self, category: str, name: str, summary: str) -> None:
        """Save summary data."""
        ...

    def load_summary(self, category: str, name: str) -> str:
        """Load summary data.

        Returns:
            The summary text.
        """
        ...

    def save_book(self, title: str, text: str) -> None:
        """Save the book text."""
        ...
