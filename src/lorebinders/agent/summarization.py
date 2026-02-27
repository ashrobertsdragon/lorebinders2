"""Entity summarization using AI agents."""

import logging
from pathlib import Path

from pydantic_ai import Agent

from lorebinders.agent.factory import (
    build_summarization_user_prompt,
    create_summarization_agent,
    load_prompt_from_assets,
)
from lorebinders.models import AgentDeps, Binder, EntityRecord, SummarizerResult
from lorebinders.settings import get_settings
from lorebinders.storage.provider import FilesystemStorage, StorageProvider

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
            val_str = (
                ", ".join(value) if isinstance(value, list) else str(value)
            )
            lines.append(f"  - {trait}: {val_str}")
    return "\n".join(lines)


async def _summarize_entity(
    summaries_dir: Path,
    category: str,
    name: str,
    agent: Agent[AgentDeps, SummarizerResult],
    prompt: str,
    storage: StorageProvider,
    deps: AgentDeps,
) -> str:
    """Summarize an entity using the AI agent with abstracted storage.

    Args:
        summaries_dir: Directory for caching summaries.
        category: The category of the entity.
        name: The name of the entity.
        agent: The agent to use for summarization.
        prompt: The prompt to use for summarization.
        storage: The storage provider for persistence.
        deps: The dependencies to inject into the agent.

    Returns:
        str: The summary text.
    """
    if storage.summary_exists(summaries_dir, category, name):
        logger.debug(f"Loading cached summary for {category}: {name}")
        return storage.load_summary(summaries_dir, category, name)

    logger.info(f"Summarizing {category}: {name}")
    try:
        result = await agent.run(prompt, deps=deps)
        summary_text = result.output.summary
        storage.save_summary(summaries_dir, category, name, summary_text)
        logger.debug(f"Summary saved for {category}: {name}")
        return summary_text

    except Exception as e:
        logger.error(f"Failed to summarize {name}: {e}")
        raise


async def summarize_binder(
    binder: Binder,
    summaries_dir: Path,
    agent: Agent[AgentDeps, SummarizerResult] | None = None,
    storage: StorageProvider | None = None,
    deps: AgentDeps | None = None,
) -> None:
    """Summarize entities in the binder asynchronously in-place.

    Includes throttling and abstracted storage.

    Args:
        binder: The refined binder model.
        summaries_dir: Directory for caching summaries.
        agent: The agent to use for summarization.
        storage: Optional storage provider.
        deps: Optional dependencies for the agent.
    """
    import asyncio

    if agent is None:
        agent = create_summarization_agent()

    if storage is None:
        storage = FilesystemStorage()

    if deps is None:
        deps = AgentDeps(
            settings=get_settings(),
            prompt_loader=load_prompt_from_assets,
        )

    semaphore = asyncio.Semaphore(10)
    tasks = []
    entity_refs = []

    async def _throttled_summarize(e: "EntityRecord", p: str) -> str:
        async with semaphore:
            return await _summarize_entity(
                summaries_dir,
                e.category,
                e.name,
                agent,
                p,
                storage,
                deps,
            )

    for category_record in binder.categories.values():
        for entity in category_record.entities.values():
            if not entity.summary and entity.appearances:
                context_str = _format_context(entity.appearances)
                prompt = build_summarization_user_prompt(
                    entity_name=entity.name,
                    category=entity.category,
                    context_data=context_str,
                )
                tasks.append(_throttled_summarize(entity, prompt))
                entity_refs.append(entity)

    if tasks:
        summaries = await asyncio.gather(*tasks)
        for entity, summary in zip(entity_refs, summaries, strict=True):
            entity.summary = summary
