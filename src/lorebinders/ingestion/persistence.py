from pathlib import Path

from lorebinders import models


def _get_path(profiles_dir: Path, chapter_num: int, entity_name: str) -> Path:
    """Get the file path for a specific profile result.

    Args:
        profiles_dir: The directory to save profiles in.
        chapter_num: The chapter number.
        entity_name: The name of the entity (sanitized).

    Returns:
        The path to the JSON storage file.
    """
    safe_name = "".join(c if c.isalnum() else "_" for c in entity_name)
    return profiles_dir / f"ch{chapter_num}_{safe_name}.json"


def profile_exists(
    profiles_dir: Path, chapter_num: int, entity_name: str
) -> bool:
    """Check if a profile already exists.

    Args:
        profiles_dir: The directory to save profiles in.
        chapter_num: The chapter number.
        entity_name: The name of the entity.

    Returns:
        True if the profile data exists on disk.
    """
    return _get_path(profiles_dir, chapter_num, entity_name).exists()


def save_profile(
    profiles_dir: Path,
    chapter_num: int,
    profile: models.CharacterProfile,
) -> None:
    """Save a character profile to disk.

    Args:
        profiles_dir: The directory to save profiles in.
        chapter_num: The chapter number.
        profile: The profile to save.
    """
    path = _get_path(profiles_dir, chapter_num, profile.name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(profile.model_dump_json(indent=2))


def load_profile(
    profiles_dir: Path, chapter_num: int, entity_name: str
) -> models.CharacterProfile:
    """Load a character profile from disk.

    Args:
        profiles_dir: The directory to save profiles in.
        chapter_num: The chapter number.
        entity_name: The name of the entity.

    Returns:
        The loaded CharacterProfile.
    """
    path = _get_path(profiles_dir, chapter_num, entity_name)
    with open(path, encoding="utf-8") as f:
        content = f.read()
        return models.CharacterProfile.model_validate_json(content)
