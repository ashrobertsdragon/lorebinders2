"""Entity summarization logic for refinement."""

import json
from typing import Any

from lorebinders.agents.models import SummarizerConfig
from lorebinders.agents.summarization import run_summarization


def _format_context(data: Any) -> str:
    """Format the entity data into a readable string for the AI."""
    if isinstance(data, dict):
        return json.dumps(data, indent=2)
    return str(data)


def summarize_binder(binder: dict[str, Any]) -> dict[str, Any]:
    """Summarize entities in the binder.

    Iterates through categories and entities, generating a summary for each
    using the AI agent, and appending it to the entity's data.

    Args:
        binder: The refined binder dictionary.

    Returns:
        The binder with added summaries.
    """
    summarized_binder = binder.copy()

    for category, entities in binder.items():
        if not isinstance(entities, dict):
            continue

        for name, details in entities.items():
            context_str = _format_context(details)

            config = SummarizerConfig(
                entity_name=name,
                category=category,
                context_data=context_str,
            )

            try:
                result = run_summarization(config)

                if isinstance(summarized_binder[category][name], dict):
                    summarized_binder[category][name]["Summary"] = (
                        result.summary
                    )
                else:
                    summarized_binder[category][name] = {
                        "Original": summarized_binder[category][name],
                        "Summary": result.summary,
                    }
            except Exception as e:
                print(f"Failed to summarize {name}: {e}")
                pass

    return summarized_binder
