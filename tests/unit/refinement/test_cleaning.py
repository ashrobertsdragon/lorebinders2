from typing import Any

import pytest

from lorebinders.refinement.cleaning import (
    _clean_entity_name,
    clean_binder,
    clean_list,
    clean_none_found,
    clean_str,
    replace_narrator,
)
from lorebinders.types import Binder, CleanableDict


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


@pytest.mark.parametrize(
    "input_list, expected",
    [
        (["A", "None found", "B"], ["A", "B"]),
        ([{"A": "B"}, {"C": "None found"}], [{"A": "B"}]),
        ([["A", "None Found"]], [["A"]]),
        (["None found"], []),
        ([], []),
        ([1, 2, 3], []),
        (["  ", ""], ["  "]),
        (["Valid", "none found", "Also Valid"], ["Valid", "Also Valid"]),
        ([[[]], ["None Found"]], []),
        ([None, "String"], ["String"]),
    ],
)
def test_clean_list(input_list: list[Any], expected: list[Any]) -> None:
    assert clean_list(input_list) == expected


def test_clean_none_found_removes_empty_values() -> None:
    data: CleanableDict = {
        "Characters": {
            "John": {
                "Eyes": "Blue",
                "Hair": "None found",
                "Traits": ["Brave", "none found"],
                "Nested": {"Key": "None Found"},
            },
            "None found": {"Something": "Else"},
        }
    }
    cleaned = clean_none_found(data)
    characters = cleaned["Characters"]
    assert isinstance(characters, dict)
    assert "None found" not in characters
    john = characters["John"]
    assert isinstance(john, dict)
    assert "Hair" not in john
    assert "Nested" not in john
    assert john["Eyes"] == "Blue"
    assert john["Traits"] == ["Brave"]


def test_replace_narrator_substitutes_references() -> None:
    data: Binder = {
        "Characters": {
            "I": {1: {"Description": "The narrator is tall."}},
            "The Protagonist": {
                1: {"Action": "I went home.", "List": ["I saw myself"]}
            },
            "John": {1: {"Opinion of I": "He is strange."}},
        }
    }
    cleaned = replace_narrator(data, "Jane Doe")
    assert "Jane Doe" in cleaned["Characters"]
    assert "I" not in cleaned["Characters"]
    jane_entry = cleaned["Characters"]["Jane Doe"]
    jane_first_chapter = jane_entry[1]
    assert isinstance(jane_first_chapter, dict)
    assert jane_first_chapter["Description"] == "Jane Doe is tall."


@pytest.mark.parametrize(
    "name, category, expected",
    [
        ("Mr. John", "Characters", "John"),
        ("Forest (Dark)", "Locations", "Forest"),
        ("Mr. John", "Other", "Mr. John"),
        ("Dr. Strange", "Characters", "Strange"),
        (
            "The Castle",
            "Locations",
            "The Castle",
        ),
        (
            "Castle of Doom",
            "Locations",
            "Castle of Doom",
        ),
        ("Captain Jack", "Characters", "Jack"),
        ("Lady Jane", "Characters", "Jane"),
        ("Mount Doom (Volcano)", "Locations", "Mount Doom"),
        ("Sir Lancelot", "Characters", "Lancelot"),
    ],
)
def test_clean_entity_name(name: str, category: str, expected: str) -> None:
    assert _clean_entity_name(name, category) == expected


def test_clean_binder_integrates_steps() -> None:
    data: Binder = {
        "Characters": {
            "Mr. Smith": {1: {"Trait": "A"}},
            "Smith": {1: {"Trait": "B"}},
            "I": {1: {"Trait": "C"}},
        },
        "Locations": {"Cave (Deep)": {1: {"Trait": "Dark"}}},
    }
    cleaned = clean_binder(data, "Jane")
    assert "Smith" in cleaned["Characters"]
    assert "Mr. Smith" not in cleaned["Characters"]
    assert "Jane" in cleaned["Characters"]
    assert "Cave" in cleaned["Locations"]
