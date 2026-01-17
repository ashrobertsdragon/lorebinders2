import pytest
from lorebinders.refinement.cleaner import clean_none_found, replace_narrator, clean_binder



def test_clean_none_found():
    data = {
        "Characters": {
            "John": {
                "Eyes": "Blue",
                "Hair": "None found",
                "Traits": ["Brave", "none found"]
            },
            "None found": {"Something": "Else"}
        }
    }
    expected = {
        "Characters": {
            "John": {
                "Eyes": "Blue",
                "Traits": ["Brave"]
            }
        }
    }


    cleaned = clean_none_found(data)


def test_replace_narrator():
    data = {
        "Characters": {
            "I": {"Description": "The narrator is tall."},
            "The Protagonist": {"Action": "I went home."},
            "John": {"Opinion of I": "He is strange."}
        }
    }
    narrator_name = "Jane Doe"
    cleaned = replace_narrator(data, narrator_name)

    assert "Jane Doe" in cleaned["Characters"]
    assert "I" not in cleaned["Characters"]
    assert "The Protagonist" not in cleaned["Characters"]
    assert cleaned["Characters"]["Jane Doe"]["Description"] == "Jane Doe is tall."
    assert cleaned["Characters"]["Jane Doe"]["Action"] == "Jane Doe went home."
    assert cleaned["Characters"]["John"]["Opinion of Jane Doe"] == "He is strange."

def test_standardize_locations():
    data = {
        "Settings": {
            "Kitchen (Interior)": "Hot",
            "Forest - Night": "Dark"
        }
    }

    cleaned = clean_binder(data, None)

    assert "Kitchen" in cleaned["Settings"]
