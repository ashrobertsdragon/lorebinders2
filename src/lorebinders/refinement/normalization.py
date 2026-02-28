"""Text normalization utilities shared across refinement modules."""

import re

from lorebinders.types import EntityTraits, TraitValue

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


def _merge_trait_values(v1: TraitValue, v2: TraitValue) -> TraitValue:
    """Safely merge two trait values (strings or lists of strings).

    Args:
        v1: The first trait value.
        v2: The second trait value.

    Returns:
        The merged trait value.
    """
    if isinstance(v1, list):
        if isinstance(v2, list):
            return sorted(list(set(v1 + v2)))
        return sorted(list(set(v1 + [v2])))
    if isinstance(v2, list):
        return sorted(list(set([v1] + v2)))
    return v1 if v1 == v2 else sorted([v1, v2])


def merge_values(v1: EntityTraits, v2: EntityTraits) -> EntityTraits:
    """Merge two EntityTraits dictionaries when keys collide.

    Args:
        v1: The first trait dictionary.
        v2: The second trait dictionary.

    Returns:
        The merged trait dictionary.
    """
    for k, v in v2.items():
        if k in v1:
            v1[k] = _merge_trait_values(v1[k], v)
        else:
            v1[k] = v
    return v1
