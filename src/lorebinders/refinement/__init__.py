"""Refinement module for LoreBinders - data cleaning and deduplication."""

import logging
from typing import Any

from lorebinders.refinement.cleaning import clean_binder

logger = logging.getLogger(__name__)


def refine_binder(
    binder: dict[str, Any], narrator_name: str | None = None
) -> dict[str, Any]:
    """Execute the refinement pipeline.

    Flow: Clean -> Resolve.

    Args:
        binder: The raw binder data from extraction.
        narrator_name: Optional name of the narrator to replace
            placeholders.

    Returns:
        The cleaned and deduplicated binder.
    """
    logger.info("Starting cleaning phase")
    cleaned_binder = clean_binder(binder, narrator_name)

    return cleaned_binder
