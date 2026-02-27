import pytest

from lorebinders.models import Binder, EntityTraits
from lorebinders.refinement.cleaning import (
    _clean_entity_name,
    clean_binder,
    clean_str,
    clean_traits,
)


@pytest.mark.parametrize(
    "input_str, expected",
    [
        ("Valid", "Valid"),
        ("  None Found  ", ""),
        ("none found", ""),
        ("  ", "  "),
        ("", ""),
        ("n/a", "n/a"),
        ("NONE FOUND", ""),
        ("No info", "No info"),
        (
            "  Tabs\tAnd\nNewlines  ",
            "  Tabs\tAnd\nNewlines  ",
        ),
        ("UNKNOWN", "UNKNOWN"),
    ],
)
def test_clean_str(input_str: str, expected: str) -> None:
    assert clean_str(input_str) == expected


def test_clean_traits_removes_empty_values() -> None:
    traits: EntityTraits = {
        "Eyes": "Blue",
        "Hair": "None found",
        "Traits": ["Brave", "none found"],
    }
    cleaned = clean_traits(traits)
    assert "Hair" not in cleaned
    assert cleaned["Eyes"] == "Blue"
    assert cleaned["Traits"] == ["Brave"]


def test_clean_binder_replaces_narrator() -> None:
    binder = Binder()
    binder.add_appearance(
        "Characters", "I", 1, {"Description": "The narrator is tall."}
    )

    cleaned = clean_binder(binder, "Jane Doe")

    assert "Jane Doe" in cleaned.categories["Characters"].entities
    assert "I" not in cleaned.categories["Characters"].entities

    jane = cleaned.categories["Characters"].entities["Jane Doe"]
    assert jane.appearances[1].traits["Description"] == "Jane Doe is tall."


@pytest.mark.parametrize(
    "name, category, expected",
    [
        ("Mr. John", "Characters", "John"),
        ("Forest (Dark)", "Locations", "Forest"),
        ("Mr. John", "Other", "Mr. John"),
        ("Dr. Strange", "Characters", "Strange"),
        ("Captain Jack", "Characters", "Jack"),
        ("Lady Jane", "Characters", "Jane"),
        ("Mount Doom (Volcano)", "Locations", "Mount Doom"),
        ("Sir Lancelot", "Characters", "Lancelot"),
    ],
)
def test_clean_entity_name(name: str, category: str, expected: str) -> None:
    assert _clean_entity_name(name, category) == expected


def test_clean_binder_integrates_steps() -> None:
    binder = Binder()
    binder.add_appearance("Characters", "Mr. Smith", 1, {"Trait": "A"})
    binder.add_appearance("Characters", "Smith", 1, {"Trait": "B"})
    binder.add_appearance("Characters", "I", 1, {"Trait": "C"})
    binder.add_appearance("Locations", "Cave (Deep)", 1, {"Trait": "Dark"})

    cleaned = clean_binder(binder, "Jane")

    chars = cleaned.categories["Characters"].entities
    assert "Smith" in chars
    assert "Mr. Smith" not in chars
    assert "Jane" in chars
    assert "Cave" in cleaned.categories["Locations"].entities
