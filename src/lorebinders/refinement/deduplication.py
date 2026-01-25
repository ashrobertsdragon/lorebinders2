"""Entity resolution and deduplication logic for refinement."""

from itertools import combinations
from typing import Any

from lorebinders.refinement.normalization import (
    TITLES,
    merge_values,
    remove_titles,
    to_singular,
)


def _is_similar_key(key1: str, key2: str) -> bool:
    """Determine if two keys are similar.

    Args:
        key1 (str): The first key to compare.
        key2 (str): The second key to compare.

    Returns:
        bool: Whether the keys are similar.
    """
    k1 = key1.strip().lower()
    k2 = key2.strip().lower()

    if k1 == k2:
        return True

    detitled_k1 = remove_titles(k1)
    detitled_k2 = remove_titles(k2)
    singular_k1 = to_singular(k1)
    singular_k2 = to_singular(k2)

    if any(
        [
            k1 == singular_k2,
            singular_k1 == k2,
            singular_k1 == singular_k2,
        ]
    ):
        return True

    k1_is_title = k1 in TITLES
    k2_is_title = k2 in TITLES
    if (k1_is_title and k1 + " " in k2) or (k2_is_title and k2 + " " in k1):
        return True

    if (detitled_k1 + " " in detitled_k2) or (detitled_k2 + " " in detitled_k1):
        return True

    destructured_match = any(
        [
            (detitled_k1 + " " in k2 + " "),
            (detitled_k2 + " " in k1 + " "),
            (k1 + " " in detitled_k2 + " "),
            (k2 + " " in detitled_k1 + " "),
        ]
    )

    if detitled_k1 != k1 or detitled_k2 != k2:
        return any(
            [
                detitled_k1 == k2,
                k1 == detitled_k2,
                detitled_k1 == detitled_k2,
                detitled_k1 == singular_k2,
                singular_k1 == detitled_k2,
                destructured_match,
            ]
        )

    return destructured_match


def _prioritize_keys(key1: str, key2: str) -> tuple[str, str]:
    """Determine which key to keep and which to merge.

    Args:
        key1 (str): The first key to compare.
        key2 (str): The second key to compare.

    Returns:
        tuple[str, str]: The keys to keep and merge.
    """
    l1, l2 = key1.lower(), key2.lower()
    if (l1 in l2 or l2 in l1) and l1 != l2:
        if l1 in TITLES:
            return key2, key1
        if l2 in TITLES:
            return key1, key2

    if len(key1) >= len(key2):
        return key2, key1
    return key1, key2


def _resolve_category_entities(entities: dict[str, Any]) -> dict[str, Any]:
    """Resolve duplicates within a category's entities.

    Returns:
        The resolved entities dictionary.
    """
    working_entities = entities.copy()
    names = list(working_entities.keys())
    duplicates_to_remove: set[str] = set()

    for n1, n2 in combinations(names, 2):
        if n1 in duplicates_to_remove or n2 in duplicates_to_remove:
            continue
        if _is_similar_key(n1, n2):
            to_merge, to_keep = _prioritize_keys(n1, n2)
            working_entities[to_keep] = merge_values(
                working_entities[to_keep], working_entities[to_merge]
            )
            duplicates_to_remove.add(to_merge)

    return {
        name: val
        for name, val in working_entities.items()
        if name not in duplicates_to_remove
    }


def resolve_binder(binder: dict[str, Any]) -> dict[str, Any]:
    """Full resolution pipeline.

    Args:
        binder (dict[str, Any]): The binder to resolve.

    Returns:
        dict[str, Any]: The resolved binder.
    """
    resolved_binder: dict[str, Any] = {}

    for category, entities in binder.items():
        if not isinstance(entities, dict):
            resolved_binder[category] = entities
            continue
        resolved_binder[category] = _resolve_category_entities(entities)

    return resolved_binder
