"""Entity cleaning logic for refinement using Binder models."""

import logging

from lorebinders.models import (
    Binder,
    CategoryRecord,
    EntityRecord,
    EntityTraits,
)
from lorebinders.refinement.normalization import (
    remove_titles,
)
from lorebinders.refinement.patterns import (
    LOCATION_SUFFIX_PATTERN,
    NARRATOR_PATTERN,
)

logger = logging.getLogger(__name__)

MAX_ENTITY_NAME_LENGTH = 200


def clean_str(text: str) -> str:
    """Clean 'none found' from strings.

    Args:
        text: The string to clean.

    Returns:
        The cleaned string.
    """
    if text.lower().strip() == "none found":
        return ""
    return text


def clean_traits(
    traits: EntityTraits,
) -> EntityTraits:
    """Recursively clean traits dictionary.

    Args:
        traits: The traits dictionary to clean.

    Returns:
        The cleaned traits dictionary.
    """
    cleaned: EntityTraits = {}
    for key, value in traits.items():
        if key.lower().strip() == "none found":
            continue

        if isinstance(value, str):
            val = clean_str(value)
            if val:
                cleaned[key] = val
        elif isinstance(value, list):
            val_list: list[str] = [
                clean_str(v) if isinstance(v, str) else v for v in value
            ]
            val_list = [v for v in val_list if v]
            if val_list:
                cleaned[key] = val_list
    return cleaned


def _replace_narrator_text(text: str, narrator_name: str) -> str:
    return NARRATOR_PATTERN.sub(narrator_name, text)


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

    Raises:
        ValueError: If the entity name exceeds the maximum length.
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


def clean_binder(binder: Binder, narrator_name: str | None) -> Binder:
    """Full cleaning pipeline using Binder model.

    Args:
        binder: The Binder model to clean.
        narrator_name: The name of the narrator to replace placeholders.

    Returns:
        The cleaned Binder model.
    """
    logger.debug("Starting binder cleaning...")

    new_binder = Binder()

    for cat_name, category in binder.categories.items():
        target_cat_name = (
            _replace_narrator_text(cat_name, narrator_name)
            if narrator_name
            else cat_name
        )

        for ent_name, entity in category.entities.items():
            target_ent_name = (
                _replace_narrator_text(ent_name, narrator_name)
                if narrator_name
                else ent_name
            )

            clean_name = _clean_entity_name(target_ent_name, target_cat_name)

            for chap_num, appearance in entity.appearances.items():
                cleaned_traits = clean_traits(appearance.traits)

                if narrator_name:
                    final_traits: EntityTraits = {}
                    for k, v in cleaned_traits.items():
                        new_k = _replace_narrator_text(k, narrator_name)
                        if isinstance(v, str):
                            final_traits[new_k] = _replace_narrator_text(
                                v, narrator_name
                            )
                        elif isinstance(v, list):
                            final_traits[new_k] = [
                                _replace_narrator_text(i, narrator_name)
                                if isinstance(i, str)
                                else i
                                for i in v
                            ]
                        else:
                            final_traits[new_k] = v
                    cleaned_traits = final_traits

                if cleaned_traits:
                    new_binder.add_appearance(
                        target_cat_name, clean_name, chap_num, cleaned_traits
                    )

            if entity.summary:
                sum_text = entity.summary
                if narrator_name:
                    sum_text = _replace_narrator_text(sum_text, narrator_name)

                if target_cat_name not in new_binder.categories:
                    new_binder.categories[target_cat_name] = CategoryRecord(
                        name=target_cat_name
                    )
                cat = new_binder.categories[target_cat_name]
                if clean_name not in cat.entities:
                    cat.entities[clean_name] = EntityRecord(
                        name=clean_name, category=target_cat_name
                    )
                cat.entities[clean_name].summary = sum_text

    logger.debug("Binder cleaning complete.")
    return new_binder
