"""Entity analysis using AI agents."""

import logging
from collections import defaultdict
from collections.abc import Callable

from pydantic_ai import Agent

from lorebinders import models
from lorebinders.agent.factory import build_analysis_user_prompt
from lorebinders.storage.provider import StorageProvider
from lorebinders.types import SortedExtractions

logger = logging.getLogger(__name__)


async def _analyze_batch(
    target_categories: list[models.CategoryTarget],
    chapter: models.Chapter,
    agent: Agent[models.AgentDeps, list[models.AnalysisResult]],
    deps: models.AgentDeps,
    effective_traits: dict[str, list[str]],
    storage: StorageProvider,
) -> list[models.EntityProfile]:
    """Analyze a batch of entities synchronously with abstracted storage.

    Args:
        target_categories: The categories and entities to analyze.
        chapter: The chapter context for analysis.
        agent: The analysis agent.
        deps: Dependencies for the agent.
        effective_traits: Map of category to traits.
        storage: The storage provider for persistence.

    Returns:
        A list of analyzed entity profiles.
    """
    profiles: list[models.EntityProfile] = []
    to_analyze: list[models.CategoryTarget] = []

    for cat_target in target_categories:
        category = cat_target.name
        cached_names = [
            n
            for n in cat_target.entities
            if storage.profile_exists(chapter.number, category, n)
        ]
        run_names = [
            n
            for n in cat_target.entities
            if not storage.profile_exists(chapter.number, category, n)
        ]

        profiles.extend(
            storage.load_profile(chapter.number, category, n)
            for n in cached_names
        )

        if run_names:
            c_traits = effective_traits.get(category) or ["Description", "Role"]
            to_analyze.append(
                models.CategoryTarget(
                    name=category, entities=run_names, traits=c_traits
                )
            )

    if not to_analyze:
        return profiles

    full_prompt = build_analysis_user_prompt(
        context_text=chapter.content,
        categories=to_analyze,
    )
    result = await agent.run(full_prompt, deps=deps)

    for r in result.output:
        profile_traits: models.EntityTraits = {
            trait.trait: trait.value for trait in r.traits
        }
        p = models.EntityProfile(
            name=r.entity_name,
            category=r.category,
            chapter_number=chapter.number,
            traits=profile_traits,
            confidence_score=deps.settings.confidence_threshold,
        )
        storage.save_profile(chapter.number, p)
        profiles.append(p)

    return profiles


async def analyze_entities(
    entities: SortedExtractions,
    book: models.Book,
    agent: Agent[models.AgentDeps, list[models.AnalysisResult]],
    deps: models.AgentDeps,
    effective_traits: dict[str, list[str]],
    storage: StorageProvider,
    progress: Callable[[models.ProgressUpdate], None] | None = None,
) -> list[models.EntityProfile]:
    """Analyze all entities sequentially with abstracted storage.

    Args:
        entities: The sorted extractions to analyze.
        book: The book context.
        agent: The analysis agent.
        deps: Dependencies for the agent.
        effective_traits: Map of category to traits.
        storage: The storage provider for persistence.
        progress: Optional callback for progress updates.

    Returns:
        A list of all analyzed entity profiles.
    """
    chapter_map = {ch.number: ch for ch in book.chapters}

    chapter_entities: dict[int, dict[str, list[str]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for category, entity_chapters in entities.items():
        for entity_name, chapters in entity_chapters.items():
            for chapter_num in chapters:
                chapter_entities[chapter_num][category].append(entity_name)

    profiles = []
    batch_tasks = []

    for chapter_num, cat_map in chapter_entities.items():
        if not (chapter := chapter_map.get(chapter_num)):
            continue

        for category, names in cat_map.items():
            batch_targets = [
                models.CategoryTarget(name=category, entities=names)
            ]
            batch_tasks.append((batch_targets, chapter))

    total_batches = len(batch_tasks)
    logger.info(
        f"Analyzing {total_batches} entity batches "
        f"across {len(chapter_entities)} chapters"
    )

    for idx, (batch, chapter) in enumerate(batch_tasks, 1):
        if progress:
            progress(
                models.ProgressUpdate(
                    stage="analysis",
                    current=idx,
                    total=total_batches,
                    message=(
                        f"Analyzing batch {idx}/{total_batches} "
                        f"(Chapter {chapter.number})"
                    ),
                )
            )
        batch_profiles = await _analyze_batch(
            batch, chapter, agent, deps, effective_traits, storage
        )
        profiles.extend(batch_profiles)

    return profiles
