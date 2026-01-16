"""Entity resolution and deduplication logic for refinement."""

import re
from itertools import combinations
from typing import Any

TITLES: set[str] = {
    "admiral",
    "airman",
    "ambassador",
    "aunt",
    "baron",
    "baroness",
    "brother",
    "cadet",
    "cap",
    "captain",
    "col",
    "colonel",
    "commander",
    "commodore",
    "corporal",
    "count",
    "countess",
    "cousin",
    "dad",
    "daddy",
    "doc",
    "doctor",
    "dr",
    "duchess",
    "duke",
    "earl",
    "ensign",
    "father",
    "gen",
    "general",
    "granddad",
    "grandfather",
    "grandma",
    "grandmom",
    "grandmother",
    "grandpop",
    "great aunt",
    "great grandfather",
    "great grandmother",
    "great uncle",
    "great-aunt",
    "great-grandfather",
    "great-grandmother",
    "great-uncle",
    "king",
    "lady",
    "leftenant",
    "lieutenant",
    "lord",
    "lt",
    "ma",
    "ma'am",
    "madam",
    "major",
    "marquis",
    "miss",
    "missus",
    "mister",
    "mjr",
    "mom",
    "mommy",
    "mother",
    "mr",
    "mrs",
    "ms",
    "nurse",
    "pa",
    "pfc",
    "pop",
    "prince",
    "princess",
    "private",
    "queen",
    "sarge",
    "seaman",
    "sergeant",
    "sir",
    "sister",
    "the",
    "uncle",
}


def to_singular(plural: str) -> str:
    """Convert a plural word to its singular form."""
    if not plural:
        return ""
    lower_plural = plural.lower()

    if lower_plural == "knives":
        return "knife"
    if lower_plural == "lives":
        return "life"

    patterns = [
        (r"(.+)(ves)$", r"\1f"),
        (r"(.+)(ies)$", r"\1y"),
        (r"(.+)(i)$", r"\1us"),
        (r"(.+)(a)$", r"\1um"),
        (r"(.+)(en)$", r"\1an"),
        (r"(.+)(oes)$", r"\1o"),
        (r"(.+)(sses)$", r"\1s"),
        (r"(.+)(ses)$", r"\1se"),
        (r"(.+)(hes)$", r"\1h"),
        (r"(.+)(xes)$", r"\1x"),
        (r"(.+)(zes)$", r"\1ze"),
        (r"(.+)(s)$", r"\1"),
    ]

    for pattern, repl in patterns:
        if re.match(pattern, lower_plural):
            return re.sub(pattern, repl, lower_plural)
    return lower_plural


def remove_titles(name: str) -> str:
    """Remove titles from a name."""
    if not name:
        return name
    name_split = name.split(" ")
    first_word = name_split[0].lower().rstrip(".")
    if first_word in TITLES and name.lower() not in TITLES:
        return " ".join(name_split[1:])
    return name


def _is_similar_key(key1: str, key2: str) -> bool:
    """Determine if two keys are similar."""
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

    if detitled_k1 != k1 or detitled_k2 != k2:
        return any(
            [
                detitled_k1 == k2,
                k1 == detitled_k2,
                detitled_k1 == detitled_k2,
                detitled_k1 == singular_k2,
                singular_k1 == detitled_k2,
                detitled_k1 + " " in k2,
                detitled_k2 + " " in k1,
                k1 + " " in detitled_k2,
                k2 + " " in detitled_k1,
            ]
        )

    return False


def _merge_values(v1: Any, v2: Any) -> Any:
    """Recursively merge values of unknown datatypes."""
    if isinstance(v1, dict) and isinstance(v2, dict):
        merged = v1.copy()
        for k, v in v2.items():
            if k in merged:
                merged[k] = _merge_values(merged[k], v)
            else:
                merged[k] = v
        return merged

    if isinstance(v1, list) and isinstance(v2, list):
        combined = v1 + v2
        try:
            return list(set(combined))
        except TypeError:
            return combined

    if isinstance(v1, list):
        if v2 not in v1:
            return v1 + [v2]
        return v1

    if isinstance(v2, list):
        if v1 not in v2:
            return [v1] + v2
        return v2

    if v1 == v2:
        return v1

    return [v1, v2]


def _prioritize_keys(key1: str, key2: str) -> tuple[str, str]:
    """Determine which key to keep and which to merge."""
    l1, l2 = key1.lower(), key2.lower()
    if (l1 in l2 or l2 in l1) and l1 != l2:
        if l1 in TITLES:
            return key2, key1
        if l2 in TITLES:
            return key1, key2

    if len(key1) >= len(key2):
        return key2, key1
    return key1, key2


def resolve_binder(binder: dict[str, Any]) -> dict[str, Any]:
    """Full resolution pipeline."""
    resolved_binder: dict[str, Any] = {}

    for category, entities in binder.items():
        if not isinstance(entities, dict):
            resolved_binder[category] = entities
            continue

        working_entities = entities.copy()
        names = list(working_entities.keys())
        duplicates_to_remove = set()

        for n1, n2 in combinations(names, 2):
            if n1 in duplicates_to_remove or n2 in duplicates_to_remove:
                continue

            if _is_similar_key(n1, n2):
                to_merge, to_keep = _prioritize_keys(n1, n2)
                working_entities[to_keep] = _merge_values(
                    working_entities[to_keep], working_entities[to_merge]
                )
                duplicates_to_remove.add(to_merge)

        resolved_binder[category] = {
            name: val
            for name, val in working_entities.items()
            if name not in duplicates_to_remove
        }

    return resolved_binder
