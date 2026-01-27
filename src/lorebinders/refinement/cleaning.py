"""Entity cleaning logic for refinement."""

import re

from lorebinders.refinement.normalization import (
    merge_values,
    remove_titles,
)
from lorebinders.types import (
    Binder,
    CleanableDict,
    CleanableValue,
    EntityData,
    TraitDict,
)

NARRATOR_PATTERN = re.compile(
    r"\b(narrator|the narrator|the protagonist|protagonist|"
    r"the main character|main character|i|me|my|myself)\b",
    re.IGNORECASE,
)

LOCATION_SUFFIX_PATTERN = re.compile(r"\s*[\(\-].*", re.IGNORECASE)

MAX_ENTITY_NAME_LENGTH = 200


def clean_str(text: str) -> str:
    """Clean 'none found' from strings.

    Args:
        text (str): The text to clean.

    Returns:
        str: The cleaned text.
    """
    if text.lower().strip() == "none found":
        return ""
    return text


def clean_list(items: list[CleanableValue]) -> list[CleanableValue]:
    """Recursively clean items in a list.

    Args:
        items: The list to clean.

    Returns:
        The cleaned list.
    """
    cleaned: list[CleanableValue] = []
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


def clean_none_found(data: CleanableDict) -> CleanableDict:
    """Recursively remove 'none found' values from a dictionary.

    Args:
        data: The dictionary to clean.

    Returns:
        The cleaned dictionary.
    """
    cleaned: CleanableDict = {}
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


def replace_narrator(data: Binder, narrator_name: str | None) -> Binder:
    """Replace narrator references with a name.

    Args:
        data: The binder data to replace narrator references in.
        narrator_name: The name to replace narrator reference with.

    Returns:
        The data with narrator references replaced.
    """
    if not narrator_name:
        return data

    new_binder: Binder = {}
    for category, entities in data.items():
        new_category = NARRATOR_PATTERN.sub(narrator_name, category)
        new_entities = _replace_narrator_in_entities(entities, narrator_name)
        if new_category in new_binder:
            new_binder[new_category] = merge_values(
                new_binder[new_category], new_entities
            )
        else:
            new_binder[new_category] = new_entities
    return new_binder


def _replace_narrator_in_entities(
    entities: EntityData, narrator_name: str
) -> EntityData:
    """Replace narrator references in entity data.

    Args:
        entities: The entity data to process.
        narrator_name: The name to replace narrator reference with.

    Returns:
        The entity data with narrator references replaced.
    """
    new_entities: EntityData = {}
    for name, entry in entities.items():
        new_name = NARRATOR_PATTERN.sub(narrator_name, name)
        new_entry = _replace_narrator_in_entry(entry, narrator_name)
        if new_name in new_entities:
            new_entities[new_name] = merge_values(
                new_entities[new_name], new_entry
            )
        else:
            new_entities[new_name] = new_entry
    return new_entities


def _replace_narrator_in_entry(
    entry: dict[int | str, TraitDict | str], narrator_name: str
) -> dict[int | str, TraitDict | str]:
    """Replace narrator references in a single entity entry.

    Args:
        entry: The entity entry to process.
        narrator_name: The name to replace narrator reference with.

    Returns:
        The entry with narrator references replaced.
    """
    new_entry: dict[int | str, TraitDict | str] = {}
    for key, value in entry.items():
        new_key = key
        if isinstance(key, str):
            new_key = NARRATOR_PATTERN.sub(narrator_name, key)

        if isinstance(value, str):
            new_entry[new_key] = NARRATOR_PATTERN.sub(narrator_name, value)
        elif isinstance(value, dict):
            new_entry[new_key] = _replace_narrator_in_traits(
                value, narrator_name
            )
        else:
            new_entry[new_key] = value
    return new_entry


def _replace_narrator_in_traits(
    traits: TraitDict, narrator_name: str
) -> TraitDict:
    """Replace narrator references in trait dictionary.

    Args:
        traits: The trait dictionary to process.
        narrator_name: The name to replace narrator reference with.

    Returns:
        The trait dictionary with narrator references replaced.
    """
    new_traits: TraitDict = {}
    for trait_key, trait_value in traits.items():
        new_key = NARRATOR_PATTERN.sub(narrator_name, trait_key)
        if isinstance(trait_value, str):
            new_traits[new_key] = NARRATOR_PATTERN.sub(
                narrator_name, trait_value
            )
        elif isinstance(trait_value, list):
            new_traits[new_key] = [
                NARRATOR_PATTERN.sub(narrator_name, v)
                if isinstance(v, str)
                else v
                for v in trait_value
            ]
        else:
            new_traits[new_key] = trait_value
    return new_traits


def standardize_location(name: str) -> str:
    """Remove suffixes like (Interior) or - Night from locations.

    Args:
        name (str): The name to standardize.

    Returns:
        str: The standardized name.
    """
    return LOCATION_SUFFIX_PATTERN.sub("", name).strip()


def _clean_entity_name(name: str, category: str) -> str:
    """Clean an entity name based on its category.

    Args:
        name: The entity name to clean.
        category: The entity category.

    Returns:
        The cleaned entity name.

    Raises:
        ValueError: If the entity name exceeds maximum length.
    """
    if len(name) > MAX_ENTITY_NAME_LENGTH:
        raise ValueError(
            f"Entity name exceeds maximum length: {len(name)} chars"
        )

    match category.lower():
        case "locations":
            return standardize_location(name)
        case "characters":
            return remove_titles(name)
    return name


def _process_category_entities(
    entities: EntityData, category: str
) -> EntityData:
    """Process all entities in a category.

    Cleans names and merges duplicates.

    Args:
        entities: The entity data for a category.
        category: The category name.

    Returns:
        The processed entities dictionary.
    """
    new_entities: EntityData = {}
    for name, details in entities.items():
        clean_name = _clean_entity_name(name, category)
        if clean_name in new_entities:
            new_entities[clean_name] = merge_values(
                new_entities[clean_name], details
            )
        else:
            new_entities[clean_name] = details
    return new_entities


def clean_binder(binder: Binder, narrator_name: str | None) -> Binder:
    """Full cleaning pipeline.

    Args:
        binder: The binder to clean.
        narrator_name: The name to replace narrator reference with.

    Returns:
        The cleaned binder.
    """
    if narrator_name:
        binder = replace_narrator(binder, narrator_name)

    return {
        category: _process_category_entities(entities, category)
        for category, entities in binder.items()
    }
