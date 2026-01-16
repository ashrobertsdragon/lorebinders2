import pytest
from lorebinders.refinement.resolver import to_singular, _is_similar_key, resolve_binder, _merge_values

def test_to_singular():
    assert to_singular("Cats") == "cat"
    assert to_singular("Knives") == "knife"
    assert to_singular("Cities") == "city"
    assert to_singular("Potatoes") == "potato"
    assert to_singular("John") == "john"

def test_is_similar_key():

    assert _is_similar_key("John Smith", "John Smiths") is True

    assert _is_similar_key("Captain John", "John") is True

    assert _is_similar_key("John", "Jane") is False

def test_resolve_merging():
    data = {
        "Characters": {
            "John Smith": {"Traits": ["Tall"], "Eyes": "Blue"},
            "John": {"Traits": ["Brave"], "Hair": "Brown"}
        }
    }


    resolved = resolve_binder(data)

    assert "John Smith" in resolved["Characters"]
    assert "John" not in resolved["Characters"]

    merged = resolved["Characters"]["John Smith"]
    assert "Tall" in merged["Traits"]
    assert "Brave" in merged["Traits"]
    assert merged["Eyes"] == "Blue"
    assert merged["Hair"] == "Brown"

def test_merge_complex_values():
    v1 = {"a": 1, "b": [2]}
    v2 = {"b": [3], "c": 4}
    merged = _merge_values(v1, v2)
    assert merged["a"] == 1
    assert 2 in merged["b"]
    assert 3 in merged["b"]
    assert merged["c"] == 4
