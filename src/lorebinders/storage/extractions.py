import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def _get_path(extractions_dir: Path, chapter_num: int) -> Path:
    return extractions_dir / f"ch{chapter_num}_extraction.json"


def extraction_exists(extractions_dir: Path, chapter_num: int) -> bool:
    """Check if an extraction result already exists.

    Args:
        extractions_dir: The directory saving extractions.
        chapter_num: The chapter number.

    Returns:
        True if the extraction data exists on disk.
    """
    return _get_path(extractions_dir, chapter_num).exists()


def save_extraction(
    extractions_dir: Path,
    chapter_num: int,
    extraction: dict[str, list[str]],
) -> None:
    """Save an extraction result to disk.

    Args:
        extractions_dir: The directory saving extractions.
        chapter_num: The chapter number.
        extraction: The extraction data map.
    """
    path = _get_path(extractions_dir, chapter_num)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(extraction, f, indent=2)
    logger.debug(f"Saved extraction for chapter {chapter_num}")


def load_extraction(
    extractions_dir: Path, chapter_num: int
) -> dict[str, list[str]]:
    """Load an extraction result from disk.

    Args:
        extractions_dir: The directory saving extractions.
        chapter_num: The chapter number.

    Returns:
        The dictionary of extracted entities.
    """
    path = _get_path(extractions_dir, chapter_num)
    with open(path, encoding="utf-8") as f:
        logger.debug(f"Loaded extraction for chapter {chapter_num}")
        return json.load(f)
