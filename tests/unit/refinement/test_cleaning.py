from lorebinders.refinement.cleaning import (
    clean_binder,
    clean_none_found,
    replace_narrator,
)


def test_clean_none_found() -> None:
    data = {
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
    data = {
        "Characters": {
            "I": {"Description": "The narrator is tall."},
            "The Protagonist": {"Action": "I went home."},
            "John": {"Opinion of I": "He is strange."},
        }
    }
    narrator_name = "Jane Doe"
    cleaned = replace_narrator(data, narrator_name)

    assert "Jane Doe" in cleaned["Characters"]
    assert "I" not in cleaned["Characters"]
    assert "The Protagonist" not in cleaned["Characters"]
    assert (
        cleaned["Characters"]["Jane Doe"]["Description"] == "Jane Doe is tall."
    )
    assert cleaned["Characters"]["Jane Doe"]["Action"] == "Jane Doe went home."
    assert (
        cleaned["Characters"]["John"]["Opinion of Jane Doe"] == "He is strange."
    )


def test_standardize_locations() -> None:
    data = {
        "Locations": {"Kitchen (Interior)": "Hot", "Forest - Night": "Dark"}
    }

    cleaned = clean_binder(data, None)

    assert "Kitchen" in cleaned["Locations"]
