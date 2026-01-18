"""Refinement module for LoreBinders - data cleaning and deduplication."""

from typing import Any

from lorebinders.refinement.cleaning import clean_binder
from lorebinders.refinement.deduplication import resolve_binder


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
    cleaned_binder = clean_binder(binder, narrator_name)

    resolved_binder = resolve_binder(cleaned_binder)

    return resolved_binder
