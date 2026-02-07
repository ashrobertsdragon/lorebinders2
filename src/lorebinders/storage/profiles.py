import logging
from pathlib import Path

from lorebinders import models

logger = logging.getLogger(__name__)


def _get_path(
    profiles_dir: Path, chapter_num: int, category: str, entity_name: str
) -> Path:
    """Get the file path for a specific profile result.

    Args:
        profiles_dir: The directory to save profiles in.
        chapter_num: The chapter number.
        category: The entity category.
        entity_name: The name of the entity (sanitized).

    Returns:
        The path to the JSON storage file.
    """
    safe_name = "".join(c if c.isalnum() else "_" for c in entity_name)
    safe_category = "".join(c if c.isalnum() else "_" for c in category)
    return profiles_dir / f"ch{chapter_num}_{safe_category}_{safe_name}.json"


def profile_exists(
    profiles_dir: Path, chapter_num: int, category: str, entity_name: str
) -> bool:
    """Check if a profile already exists.

    Args:
        profiles_dir: The directory to save profiles in.
        chapter_num: The chapter number.
        category: The entity category.
        entity_name: The name of the entity.

    Returns:
        True if the profile data exists on disk.
    """
    return _get_path(profiles_dir, chapter_num, category, entity_name).exists()


def save_profile(
    profiles_dir: Path,
    chapter_num: int,
    profile: models.EntityProfile,
) -> None:
    """Save an entity profile to disk.

    Args:
        profiles_dir: The directory to save profiles in.
        chapter_num: The chapter number.
        profile: The profile to save.
    """
    path = _get_path(profiles_dir, chapter_num, profile.category, profile.name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(profile.model_dump_json(indent=2))
    logger.debug(f"Saved profile: {profile.category}/{profile.name}")


def load_profile(
    profiles_dir: Path, chapter_num: int, category: str, entity_name: str
) -> models.EntityProfile:
    """Load an entity profile from disk.

    Args:
        profiles_dir: The directory to save profiles in.
        chapter_num: The chapter number.
        category: The entity category.
        entity_name: The name of the entity.

    Returns:
        The loaded EntityProfile.
    """
    path = _get_path(profiles_dir, chapter_num, category, entity_name)
    with open(path, encoding="utf-8") as f:
        content = f.read()
        return models.EntityProfile.model_validate_json(content)
