"""Entity summarization using AI agents."""

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
from lorebinders.models import AgentDeps, SummarizerResult
from lorebinders.settings import get_settings
from lorebinders.storage.summaries import (
    load_summary,
    save_summary,
    summary_exists,
)
from lorebinders.types import Binder, EntityEntry

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


def _sumarize_entity(
    summaries_dir: Path,
    category: str,
    name: str,
    agent: Agent[AgentDeps, SummarizerResult] | None,
    prompt: str,
) -> str:
    """Summarize an entity using the AI agent.

    Args:
        summaries_dir (Path): Directory for caching summaries.
        category (str): The category of the entity.
        name (str): The name of the entity.
        agent (Agent | None): The agent to use for summarization.
        prompt (str): The prompt to use for summarization.

    Returns:
        str: The summary text.
    """
    if agent is None:
        agent = create_summarization_agent()

    if summary_exists(summaries_dir, category, name):
        logger.info(f"Loading cached summary for {category}: {name}")
        summary_text = load_summary(summaries_dir, category, name)
        return summary_text

    logger.info(f"Summarizing {category}: {name}")
    try:
        deps = AgentDeps(
            settings=get_settings(),
            prompt_loader=load_prompt_from_assets,
        )
        result: SummarizerResult = run_agent(agent, prompt, deps)
        summary_text = result.summary
        save_summary(summaries_dir, category, name, summary_text)
        return summary_text

    except Exception as e:
        logger.error(f"Failed to summarize {name}: {e}")
        raise


def summarize_binder(
    binder: Binder,
    summaries_dir: Path,
    agent: Agent[AgentDeps, SummarizerResult] | None = None,
) -> Binder:
    """Summarize entities in the binder.

    Iterates through categories and entities, generating a summary for each
    using the AI agent, and appending it to the entity's data.

    Args:
        binder (Binder): The refined binder dictionary.
        summaries_dir (Path): Directory for caching summaries.
        agent (Agent | None): The agent to use for summarization.

    Returns:
        Binder: The binder with added summaries.
    """
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
            binder[category][name]["Summary"] = _sumarize_entity(
                summaries_dir, category, name, agent, prompt
            )

    return binder
