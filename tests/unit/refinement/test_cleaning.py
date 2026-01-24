from lorebinders.refinement.cleaning import (
    clean_binder,
    clean_none_found,
    replace_narrator,
)
from lorebinders.types import Binder, CleanableDict


def test_clean_none_found() -> None:
    data: CleanableDict = {
        "Characters": {
            "John": {
                "Eyes": "Blue",
                "Hair": "None found",
                "Traits": ["Brave", "none found"],
            },
            "None found": {"Something": "Else"},
        }
    }

    clean_none_found(data)


def test_replace_narrator() -> None:
    data: Binder = {
        "Characters": {
            "I": {1: {"Description": "The narrator is tall."}},
            "The Protagonist": {1: {"Action": "I went home."}},
            "John": {1: {"Opinion of I": "He is strange."}},
        }
    }
    narrator_name = "Jane Doe"
    cleaned = replace_narrator(data, narrator_name)

    assert "Jane Doe" in cleaned["Characters"]
    assert "I" not in cleaned["Characters"]
    assert "The Protagonist" not in cleaned["Characters"]
    jane_entry = cleaned["Characters"]["Jane Doe"]
    assert isinstance(jane_entry[1], dict)
    assert jane_entry[1]["Description"] == "Jane Doe is tall."
    assert jane_entry[1]["Action"] == "Jane Doe went home."
    john_entry = cleaned["Characters"]["John"]
    assert isinstance(john_entry[1], dict)
    assert john_entry[1]["Opinion of Jane Doe"] == "He is strange."


def test_standardize_locations() -> None:
    data: Binder = {
        "Locations": {
            "Kitchen (Interior)": {1: {"Atmosphere": "Hot"}},
            "Forest - Night": {1: {"Atmosphere": "Dark"}},
        }
    }

    cleaned = clean_binder(data, None)

    assert "Kitchen" in cleaned["Locations"]
