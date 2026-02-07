import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def _get_path(summaries_dir: Path, category: str, entity_name: str) -> Path:
    safe_category = "".join(c if c.isalnum() else "_" for c in category)
    safe_name = "".join(c if c.isalnum() else "_" for c in entity_name)
    return summaries_dir / f"{safe_category}_{safe_name}_summary.json"


def summary_exists(
    summaries_dir: Path, category: str, entity_name: str
) -> bool:
    """Check if a summary already exists.

    Args:
        summaries_dir: The directory saving summaries.
        category: The entity category.
        entity_name: The name of the entity.

    Returns:
        True if the summary data exists on disk.
    """
    return _get_path(summaries_dir, category, entity_name).exists()


def save_summary(
    summaries_dir: Path,
    category: str,
    entity_name: str,
    summary: str,
) -> None:
    """Save an entity summary to disk.

    Args:
        summaries_dir: The directory saving summaries.
        category: The entity category.
        entity_name: The name of the entity.
        summary: The summary text.
    """
    path = _get_path(summaries_dir, category, entity_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"entity_name": entity_name, "summary": summary}, f, indent=2)
    logger.debug(f"Saved summary: {category}/{entity_name}")


def load_summary(summaries_dir: Path, category: str, entity_name: str) -> str:
    """Load an entity summary from disk.

    Args:
        summaries_dir: The directory saving summaries.
        category: The entity category.
        entity_name: The name of the entity.

    Returns:
        The summary text.
    """
    path = _get_path(summaries_dir, category, entity_name)
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
        return data["summary"]
