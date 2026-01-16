"""Orchestration for the refinement pipeline."""

from typing import Any

from lorebinders.refinement.cleaner import clean_binder
from lorebinders.refinement.resolver import resolve_binder
from lorebinders.refinement.summarizer import summarize_binder


def refine_binder(
    binder: dict[str, Any], narrator_name: str | None = None
) -> dict[str, Any]:
    """Execute the full refinement pipeline.

    Flow: Clean -> Resolve -> Summarize.

    Args:
        binder: The raw binder data from extraction.
        narrator_name: Optional name of the narrator to replace
            placeholders.

    Returns:
        The fully refined and summarized binder.
    """
    cleaned_binder = clean_binder(binder, narrator_name)

    resolved_binder = resolve_binder(cleaned_binder)

    final_binder = summarize_binder(resolved_binder)

    return final_binder
