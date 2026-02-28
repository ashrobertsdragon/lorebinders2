import json
import logging
from pathlib import Path

import lorebinders.storage.workspace as workspace
from lorebinders import models

logger = logging.getLogger(__name__)


def _get_extraction_path(extractions_dir: Path, chapter_num: int) -> Path:
    return extractions_dir / f"ch{chapter_num}_extraction.json"


def _get_profile_path(
    profiles_dir: Path, chapter_num: int, category: str, entity_name: str
) -> Path:
    safe_name = "".join(c if c.isalnum() else "_" for c in entity_name)
    safe_category = "".join(c if c.isalnum() else "_" for c in category)
    return profiles_dir / f"ch{chapter_num}_{safe_category}_{safe_name}.json"


def _get_summary_path(
    summaries_dir: Path, category: str, entity_name: str
) -> Path:
    safe_category = "".join(c if c.isalnum() else "_" for c in category)
    safe_name = "".join(c if c.isalnum() else "_" for c in entity_name)
    return summaries_dir / f"{safe_category}_{safe_name}_summary.json"


class FilesystemStorage:
    """Standard filesystem-based storage implementation."""

    def set_workspace(self, author: str, title: str) -> None:
        """Set the workspace directories."""
        self._path = workspace.ensure_workspace(author, title)
        self.extractions_dir = self._path / "extractions"
        self.profiles_dir = self._path / "profiles"
        self.summaries_dir = self._path / "summaries"

    @property
    def path(self) -> Path:
        """The base path of the workspace."""
        if not self._path:
            raise RuntimeError("Workspace not set. Call set_workspace first.")
        return self._path

    def extraction_exists(self, chapter_num: int) -> bool:
        """Check if extraction exists.

        Returns:
            True if it exists.
        """
        return _get_extraction_path(self.extractions_dir, chapter_num).exists()

    def save_extraction(
        self,
        chapter_num: int,
        data: dict[str, list[str]],
    ) -> None:
        """Save extraction data."""
        path = _get_extraction_path(self.extractions_dir, chapter_num)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open(mode="w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        logger.debug(f"Saved extraction for chapter {chapter_num}")

    def load_extraction(self, chapter_num: int) -> dict[str, list[str]]:
        """Load extraction data."""
        path = _get_extraction_path(self.extractions_dir, chapter_num)
        with path.open(encoding="utf-8") as f:
            logger.debug(f"Loaded extraction for chapter {chapter_num}")
            return json.load(f)

    def profile_exists(
        self, chapter_num: int, category: str, name: str
    ) -> bool:
        """Check if profile exists."""
        return _get_profile_path(
            self.profiles_dir, chapter_num, category, name
        ).exists()

    def save_profile(
        self,
        chapter_num: int,
        profile: models.EntityProfile,
    ) -> None:
        """Save profile data."""
        path = _get_profile_path(
            self.profiles_dir, chapter_num, profile.category, profile.name
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open(mode="w", encoding="utf-8") as f:
            f.write(profile.model_dump_json(indent=2))
        logger.debug(f"Saved profile: {profile.category}/{profile.name}")

    def load_profile(
        self, chapter_num: int, category: str, name: str
    ) -> models.EntityProfile:
        """Load profile data."""
        path = _get_profile_path(self.profiles_dir, chapter_num, category, name)
        with path.open(encoding="utf-8") as f:
            content = f.read()
            return models.EntityProfile.model_validate_json(content)

    def summary_exists(self, category: str, name: str) -> bool:
        """Check if summary exists."""
        return _get_summary_path(self.summaries_dir, category, name).exists()

    def save_summary(self, category: str, name: str, summary: str) -> None:
        """Save summary data."""
        path = _get_summary_path(self.summaries_dir, category, name)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open(mode="w", encoding="utf-8") as f:
            json.dump({"entity_name": name, "summary": summary}, f, indent=2)
        logger.debug(f"Saved summary: {category}/{name}")

    def load_summary(self, category: str, name: str) -> str:
        """Load summary data."""
        path = _get_summary_path(self.summaries_dir, category, name)
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
            return data["summary"]
