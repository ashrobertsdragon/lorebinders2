"""Entity sorting and early refinement logic.

Normalizes and deduplicates entities IMMEDIATELY after extraction to
minimize redundant analysis calls.
"""

import logging
import re

from lorebinders.models import SortedExtractions
from lorebinders.refinement.deduplication import (
    _is_similar_key,
    _prioritize_keys,
)
from lorebinders.refinement.normalization import remove_titles

logger = logging.getLogger(__name__)

NARRATOR_PATTERN = re.compile(
    r"\b(narrator|the narrator|the protagonist|protagonist|"
    r"the main character|main character|i|me|my|myself)\b",
    re.IGNORECASE,
)

LOCATION_SUFFIX_PATTERN = re.compile(r"\s*[\(\-].*", re.IGNORECASE)


def standardize_location(name: str) -> str:
    """Remove suffixes like (Interior) or - Night from locations.

    Args:
        name: The location name to standardize.

    Returns:
        The standardized location name.
    """
    return LOCATION_SUFFIX_PATTERN.sub("", name).strip()


def _clean_entity_name(name: str, category: str) -> str:
    """Clean an entity name based on its category.

    Args:
        name: The entity name to clean.
        category: The category of the entity.

    Returns:
        The cleaned entity name.
    """
    match category.lower():
        case "locations":
            return standardize_location(name)
        case "characters":
            return remove_titles(name)
    return name


def _replace_narrator_in_category(
    categories: dict[str, list[str]], narrator_name: str
) -> dict[str, list[str]]:
    """Replace narrator references in category data.

    Args:
        categories: The categories and entity names.
        narrator_name: The name of the narrator.

    Returns:
        The updated categories dictionary.
    """
    result: dict[str, list[str]] = {}
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


def _deduplicate_entity_names(names: list[str], category: str) -> list[str]:
    """Clean and deduplicate a list of entity names.

    Args:
        names: A list of entity names.
        category: The category of the entities.

    Returns:
        A list of cleaned and deduplicated entity names.
    """
    if not names:
        return []

    cleaned_names = []
    for n in names:
        trimmed = n.strip()
        if not trimmed:
            continue
        cleaned = _clean_entity_name(trimmed, category)
        if cleaned:
            cleaned_names.append(cleaned)

    if len(cleaned_names) <= 1:
        return cleaned_names

    canonical_names: list[str] = []
    for name in cleaned_names:
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


def sort_extractions(
    raw_extractions: dict[int, dict[str, list[str]]],
    narrator_name: str | None = None,
) -> SortedExtractions:
    """Aggregates, cleans, and deduplicates raw extractions.

    Performs early refinement to ensure that synonyms and titles are resolved
    before analysis.

    Args:
        raw_extractions: Map of ChapterNum -> Category -> list[Names]
        narrator_name: Optional name of the narrator.

    Returns:
        SortedExtractions: Map of Category -> EntityName -> list[ChapterNumbers]
    """
    aggregated: SortedExtractions = {}

    for chapter_num, categories in raw_extractions.items():
        if narrator_name:
            categories = _replace_narrator_in_category(
                categories, narrator_name
            )

        for category, names in categories.items():
            if category not in aggregated:
                aggregated[category] = {}

            deduped_names = _deduplicate_entity_names(names, category)

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
                            logger.debug(f"Merging '{existing}' into '{name}'")
                            chapters = aggregated[category].pop(existing)
                            aggregated[category][name] = chapters
                            if chapter_num not in aggregated[category][name]:
                                aggregated[category][name].append(chapter_num)

                        found_match = True
                        break

                if not found_match:
                    aggregated[category][name] = [chapter_num]

    for cat in aggregated.values():
        for name in cat:
            cat[name].sort()

    return aggregated
