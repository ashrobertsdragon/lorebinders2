"""Entity summarization using AI agents."""

import copy
import json
import logging
from pathlib import Path

from pydantic_ai import Agent

from lorebinders.agent.factory import (
    build_summarization_user_prompt,
    create_summarization_agent,
    load_prompt_from_assets,
    run_agent,
)
from lorebinders.models import (
    AgentDeps,
    Binder,
    EntityEntry,
    SummarizerResult,
)
from lorebinders.settings import get_settings
from lorebinders.storage.summaries import (
    load_summary,
    save_summary,
    summary_exists,
)

logger = logging.getLogger(__name__)


def _format_context(data: EntityEntry) -> str:
    """Format the entity data into a readable string for the AI.

    Args:
        data (EntityEntry): The data to format.

    Returns:
        str: The formatted data.
    """
    if isinstance(data, dict):
        return json.dumps(data, indent=2)
    return str(data)


def summarize_binder(
    binder: Binder,
    summaries_dir: Path,
    agent: Agent[AgentDeps, SummarizerResult] | None = None,
) -> Binder:
    """Summarize entities in the binder.

    Iterates through categories and entities, generating a summary for each
    using the AI agent, and appending it to the entity's data.

    Args:
        binder: The refined binder dictionary.
        summaries_dir: Directory for caching summaries.
        agent: Optional agent instance for testing.

    Returns:
        The binder with added summaries.
    """
    summarized_binder = copy.deepcopy(binder)
    if agent is None:
        agent = create_summarization_agent()

    for category, entities in binder.items():
        if not isinstance(entities, dict):
            continue

        for name, details in entities.items():
            context_str = _format_context(details)

            prompt = build_summarization_user_prompt(
                entity_name=name,
                category=category,
                context_data=context_str,
            )

            try:
                if summary_exists(summaries_dir, category, name):
                    logger.info(
                        f"Loading cached summary for {category}: {name}"
                    )
                    summary_text = load_summary(summaries_dir, category, name)
                else:
                    logger.info(f"Summarizing {category}: {name}")
                    deps = AgentDeps(
                        settings=get_settings(),
                        prompt_loader=load_prompt_from_assets,
                    )
                    result: SummarizerResult = run_agent(agent, prompt, deps)
                    summary_text = result.summary
                    save_summary(summaries_dir, category, name, summary_text)

                summarized_binder[category][name]["Summary"] = summary_text
            except Exception as e:
                logger.error(f"Failed to summarize {name}: {e}")
                raise

    return summarized_binder
