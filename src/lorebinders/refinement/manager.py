"""Orchestration for the refinement pipeline."""

from typing import Any

from lorebinders.refinement.cleaner import EntityCleaner
from lorebinders.refinement.resolver import EntityResolver
from lorebinders.refinement.summarizer import EntitySummarizer


class RefinementManager:
    """Orchestrates the entity refinement pipeline.

    Flow: Clean -> Resolve -> Summarize.
    """

    def __init__(self):
        """Initialize the manager with pipeline components."""
        self.cleaner = EntityCleaner()
        self.resolver = EntityResolver()
        self.summarizer = EntitySummarizer()

    def process(
        self, binder: dict[str, Any], narrator_name: str | None = None
    ) -> dict[str, Any]:
        """Execute the full refinement pipeline.

        Args:
            binder: The raw binder data from extraction.
            narrator_name: Optional name of the narrator to replace
                placeholders.

        Returns:
            The fully refined and summarized binder.
        """
        cleaned_binder = self.cleaner.clean(binder, narrator_name)

        resolved_binder = self.resolver.resolve(cleaned_binder)

        final_binder = self.summarizer.summarize(resolved_binder)

        return final_binder
