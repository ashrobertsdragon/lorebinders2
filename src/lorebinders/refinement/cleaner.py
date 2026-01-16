"""Entity cleaning logic for refinement."""

import re
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

NARRATOR_PATTERN = re.compile(
    r"\b(narrator|the narrator|the protagonist|protagonist|"
    r"the main character|main character|i|me|my|myself)\b",
    re.IGNORECASE,
)

LOCATION_SUFFIX_PATTERN = re.compile(r"\s*[\(\-].*", re.IGNORECASE)


def remove_titles(name: str) -> str:
    """Remove titles from a name."""
    if not name:
        return name
    name_split = name.split(" ")
    first_word = name_split[0].lower().rstrip(".")
    if first_word in TITLES and name.lower() not in TITLES:
        return " ".join(name_split[1:])
    return name


def clean_str(text: str) -> str:
    """Clean 'none found' from strings."""
    if text.lower().strip() == "none found":
        return ""
    return text


def clean_list(items: list[Any]) -> list[Any]:
    """Recursively clean items in a list."""
    cleaned: list[Any] = []
    for item in items:
        if isinstance(item, str):
            cleaned_str = clean_str(item)
            if cleaned_str:
                cleaned.append(cleaned_str)
        elif isinstance(item, dict):
            cleaned_dict = clean_none_found(item)
            if cleaned_dict:
                cleaned.append(cleaned_dict)
        elif isinstance(item, list):
            cleaned_inner_list = clean_list(item)
            if cleaned_inner_list:
                cleaned.append(cleaned_inner_list)
    return cleaned


def clean_none_found(data: dict[str, Any]) -> dict[str, Any]:
    """Recursively remove 'none found' values from a dictionary."""
    cleaned: dict[str, Any] = {}
    for key, value in data.items():
        if key.lower().strip() == "none found":
            continue

        if isinstance(value, dict):
            cleaned_val_dict = clean_none_found(value)
            if cleaned_val_dict:
                cleaned[key] = cleaned_val_dict
        elif isinstance(value, list):
            cleaned_val_list = clean_list(value)
            if cleaned_val_list:
                cleaned[key] = cleaned_val_list
        elif isinstance(value, str):
            cleaned_val_str = clean_str(value)
            if cleaned_val_str:
                cleaned[key] = cleaned_val_str
    return cleaned


def _merge_values(v1: Any, v2: Any) -> Any:
    """Helper to merge values when keys collide during replacement."""
    if isinstance(v1, dict) and isinstance(v2, dict):
        merged = v1.copy()
        for k, v in v2.items():
            if k in merged:
                merged[k] = _merge_values(merged[k], v)
            else:
                merged[k] = v
        return merged
    if isinstance(v1, list) and isinstance(v2, list):
        return list(set(v1 + v2))
    if isinstance(v1, list):
        return list(set(v1 + [v2]))
    if isinstance(v2, list):
        return list(set([v1] + v2))
    if v1 == v2:
        return v1
    return [v1, v2]


def replace_narrator(data: Any, narrator_name: str | None) -> Any:
    """Replace narrator references with a name."""
    if not narrator_name:
        return data

    if isinstance(data, str):
        return NARRATOR_PATTERN.sub(narrator_name, data)
    elif isinstance(data, list):
        return [replace_narrator(item, narrator_name) for item in data]
    elif isinstance(data, dict):
        new_dict: dict[str, Any] = {}
        for key, value in data.items():
            new_key = NARRATOR_PATTERN.sub(narrator_name, key)
            new_val = replace_narrator(value, narrator_name)
            if new_key in new_dict:
                new_dict[new_key] = _merge_values(new_dict[new_key], new_val)
            else:
                new_dict[new_key] = new_val
        return new_dict
    return data


def standardize_location(name: str) -> str:
    """Remove suffixes like (Interior) or - Night from locations."""
    return LOCATION_SUFFIX_PATTERN.sub("", name).strip()


def clean_binder(
    binder: dict[str, Any], narrator_name: str | None
) -> dict[str, Any]:
    """Full cleaning pipeline."""
    if narrator_name:
        binder = replace_narrator(binder, narrator_name)

    binder = clean_none_found(binder)

    final_binder: dict[str, Any] = {}
    for category, entities in binder.items():
        new_entities: dict[str, Any] = {}
        for name, details in entities.items():
            clean_name = name
            if category.lower() == "settings":
                clean_name = standardize_location(name)
            elif category.lower() == "characters":
                clean_name = remove_titles(name)

            if clean_name in new_entities:
                new_entities[clean_name] = _merge_values(
                    new_entities[clean_name], details
                )
            else:
                new_entities[clean_name] = details
        final_binder[category] = new_entities

    return final_binder
