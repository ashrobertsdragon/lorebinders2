"""Text normalization utilities shared across refinement modules."""

from typing import cast

from lorebinders.models import CleanableValue

TITLES: frozenset[str] = frozenset(
    {
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
)


def remove_titles(name: str) -> str:
    """Remove titles from a name.

    Args:
        name: The name to remove titles from.

    Returns:
        The name with titles removed.
    """
    if not name:
        return name
    name_split = name.split(" ")
    first_word = name_split[0].lower().rstrip(".")
    if first_word in TITLES and name.lower() not in TITLES:
        return " ".join(name_split[1:])
    return name


def to_singular(plural: str) -> str:
    """Convert a plural word to its singular form.

    Args:
        plural: The plural word to convert.

    Returns:
        The singular form of the word.
    """
    import re

    if not plural:
        return ""

    patterns = [
        (r"(?i)(.*)(lves)$", r"\1lf"),
        (r"(?i)(.*)(eaves)$", r"\1eaf"),
        (r"(?i)(.*)(oaves)$", r"\1oaf"),
        (r"(?i)(.*)(ives)$", r"\1ife"),
        (r"(?i)(.*)(ves)$", r"\1f"),
        (r"(?i)(.*)(ies)$", r"\1y"),
        (r"(?i)(.*)(i)$", r"\1us"),
        (r"(?i)(.*)(a)$", r"\1um"),
        (r"(?i)(.*)(oes)$", r"\1o"),
        (r"(?i)(.*)(sses)$", r"\1ss"),
        (r"(?i)(.*)(ses)$", r"\1s"),
        (r"(?i)(.*)(xes)$", r"\1x"),
        (r"(?i)(.*)(zes)$", r"\1ze"),
        (r"(?i)(.*)(ches)$", r"\1ch"),
        (r"(?i)(.*)(shes)$", r"\1sh"),
        (r"(?i)(.*)(s)$", r"\1"),
    ]

    for pattern, replacement in patterns:
        singular, n = re.subn(pattern, replacement, plural)
        if n > 0:
            return singular

    return plural


def merge_values(v1: object, v2: object) -> CleanableValue:
    """Merge two values when keys collide during entity resolution.

    Args:
        v1: The first value to merge.
        v2: The second value to merge.

    Returns:
        The merged value.
    """
    if isinstance(v1, dict) and isinstance(v2, dict):
        merged = v1.copy()
        for k, v in v2.items():
            merged[k] = merge_values(merged[k], v) if k in merged else v
        return cast(CleanableValue, merged)
    if isinstance(v1, list) and isinstance(v2, list):
        return cast(CleanableValue, list(set(v1 + v2)))
    if isinstance(v1, list):
        return cast(CleanableValue, list(set(v1 + [v2])))
    if isinstance(v2, list):
        return cast(CleanableValue, list(set([v1] + v2)))
    return (
        cast(CleanableValue, v1) if v1 == v2 else cast(CleanableValue, [v1, v2])
    )
