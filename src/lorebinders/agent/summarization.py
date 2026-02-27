"""Entity summarization using AI agents."""

import logging
from pathlib import Path

from pydantic_ai import Agent

from lorebinders.agent.factory import (
    build_summarization_user_prompt,
    create_summarization_agent,
    load_prompt_from_assets,
)
from lorebinders.models import AgentDeps, Binder, SummarizerResult
from lorebinders.settings import get_settings
from lorebinders.storage.summaries import (
    load_summary,
    save_summary,
    summary_exists,
)

logger = logging.getLogger(__name__)


def _format_context(details: dict) -> str:
    """Format the entity data into a readable string for the AI.

    Args:
        details: The entity details containing appearances.

    Returns:
        str: The formatted data.
    """
    lines = []
    for chap_num, appearance in details.items():
        lines.append(f"Chapter {chap_num}:")
        for trait, value in appearance.traits.items():
            if isinstance(value, list):
                val_str = ", ".join(value)
            else:
                val_str = str(value)
            lines.append(f"  - {trait}: {val_str}")
    return "\n".join(lines)


async def _summarize_entity(
    summaries_dir: Path,
    category: str,
    name: str,
    agent: Agent[AgentDeps, SummarizerResult],
    prompt: str,
) -> str:
    """Summarize an entity using the AI agent.

    Args:
        summaries_dir: Directory for caching summaries.
        category: The category of the entity.
        name: The name of the entity.
        agent: The agent to use for summarization.
        prompt: The prompt to use for summarization.

    Returns:
        str: The summary text.
    """
    if summary_exists(summaries_dir, category, name):
        logger.debug(f"Loading cached summary for {category}: {name}")
        return load_summary(summaries_dir, category, name)

    logger.info(f"Summarizing {category}: {name}")
    try:
        deps = AgentDeps(
            settings=get_settings(),
            prompt_loader=load_prompt_from_assets,
        )
        result = await agent.run(prompt, deps=deps)
        summary_text = result.output.summary
        save_summary(summaries_dir, category, name, summary_text)
        logger.debug(f"Summary saved for {category}: {name}")
        return summary_text

    except Exception as e:
        logger.error(f"Failed to summarize {name}: {e}")
        raise


async def summarize_binder(
    binder: Binder,
    summaries_dir: Path,
    agent: Agent[AgentDeps, SummarizerResult] | None = None,
) -> Binder:
    """Summarize entities in the binder asynchronously.

    Args:
        binder: The refined binder model.
        summaries_dir: Directory for caching summaries.
        agent: The agent to use for summarization.

    Returns:
        Binder: The binder with added summaries.
    """
    import asyncio

    if agent is None:
        agent = create_summarization_agent()

    tasks = []
    entity_refs = []

    for category_record in binder.categories.values():
        for entity in category_record.entities.values():
            if not entity.summary and entity.appearances:
                context_str = _format_context(entity.appearances)
                prompt = build_summarization_user_prompt(
                    entity_name=entity.name,
                    category=entity.category,
                    context_data=context_str,
                )
                tasks.append(
                    _summarize_entity(
                        summaries_dir,
                        entity.category,
                        entity.name,
                        agent,
                        prompt,
                    )
                )
                entity_refs.append(entity)

    if tasks:
        summaries = await asyncio.gather(*tasks)
        for entity, summary in zip(entity_refs, summaries, strict=True):
            entity.summary = summary

    return binder
