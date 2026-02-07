"""Entity sorting logic for the pipeline.

Handles aggregation, cleaning, and deduplication of entities BEFORE analysis.
"""

import logging
import re

from lorebinders.refinement.deduplication import (
    _is_similar_key,
    _prioritize_keys,
)
from lorebinders.types import (
    CategoryChapterData,
    CategoryTraits,
    SortedEntities,
)

NARRATOR_PATTERN = re.compile(
    r"\b(narrator|the narrator|the protagonist|protagonist|"
    r"the main character|main character|i|me|my|myself)\b",
    re.IGNORECASE,
)


def _replace_narrator_in_category(
    categories: CategoryTraits, narrator_name: str
) -> CategoryTraits:
    """Replace narrator references in category trait data.

    Args:
        categories: The category to entity list mapping.
        narrator_name: The name to replace narrator references with.

    Returns:
        The data with narrator references replaced.
    """
    result: CategoryTraits = {}
    for category, names in categories.items():
        new_category = NARRATOR_PATTERN.sub(narrator_name, category)
        new_names = [
            NARRATOR_PATTERN.sub(narrator_name, name) for name in names
        ]
        if new_category in result:
            result[new_category].extend(new_names)
        else:
            result[new_category] = new_names
    return result


def _deduplicate_entity_names(names: list[str]) -> list[str]:
    """Deduplicate a list of entity names using existing similarity logic.

    Args:
        names: list of entity names to deduplicate.

    Returns:
        list of deduplicated entity names.
    """
    if len(names) <= 1:
        return names

    canonical_names: list[str] = []
    for name in names:
        found_match = False
        for i, existing in enumerate(canonical_names):
            if _is_similar_key(name, existing):
                _, keeper = _prioritize_keys(name, existing)
                canonical_names[i] = keeper
                found_match = True
                break
        if not found_match:
            canonical_names.append(name)
    return list(set(canonical_names))


logger = logging.getLogger(__name__)


def sort_extractions(
    raw_extractions: CategoryChapterData,
    narrator_name: str | None = None,
) -> SortedEntities:
    """Aggregates, cleans, and deduplicates raw extractions.

    This functions performs the pre-analysis sorting to ensure that
    synonyms and duplicates are merged into a single entity entry before
    expensive analysis is performed.

    Args:
        raw_extractions: Map of ChapterNum -> Category -> list[Names]
        narrator_name: Optional name of the narrator to replace placeholders.

    Returns:
        Map of Category -> EntityName -> list[ChapterNumbers]
    """
    aggregated: SortedEntities = {}

    for chapter_num, categories in raw_extractions.items():
        if narrator_name:
            categories = _replace_narrator_in_category(
                categories, narrator_name
            )

        for category, names in categories.items():
            if category not in aggregated:
                aggregated[category] = {}

            valid_names = [n.strip() for n in names if n.strip()]
            unique_names = list(set(valid_names))
            deduped_names = _deduplicate_entity_names(unique_names)

            if len(unique_names) != len(deduped_names):
                logger.debug(
                    f"Deduplicated {category} in ch{chapter_num}: "
                    f"{len(unique_names)} -> {len(deduped_names)}"
                )

            for name in deduped_names:
                found_match = False

                existing_keys = list(aggregated[category].keys())

                for existing in existing_keys:
                    if _is_similar_key(name, existing):
                        _, keeper = _prioritize_keys(name, existing)

                        if keeper == existing:
                            if (
                                chapter_num
                                not in aggregated[category][existing]
                            ):
                                aggregated[category][existing].append(
                                    chapter_num
                                )
                        else:
                            logger.debug(
                                f"Merging '{existing}' into better name "
                                f"'{name}'"
                            )
                            chapters = aggregated[category].pop(existing)
                            aggregated[category][name] = chapters
                            if chapter_num not in aggregated[category][name]:
                                aggregated[category][name].append(chapter_num)

                        found_match = True
                        break

                if not found_match:
                    aggregated[category][name] = [chapter_num]

    return aggregated
