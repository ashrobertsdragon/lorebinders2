import pytest
from lorebinders.refinement.resolver import EntityResolver

@pytest.fixture
def resolver():
    return EntityResolver()

def test_to_singular(resolver):
    assert resolver.to_singular("Cats") == "cat"
    assert resolver.to_singular("Knives") == "knife"
    assert resolver.to_singular("Cities") == "city"
    assert resolver.to_singular("Potatoes") == "potato"
    assert resolver.to_singular("John") == "john"

def test_is_similar_key(resolver):

    assert resolver._is_similar_key("John Smith", "John Smiths") is True

    assert resolver._is_similar_key("Captain John", "John") is True

    assert resolver._is_similar_key("John", "Jane") is False

def test_resolve_merging(resolver):
    data = {
        "Characters": {
            "John Smith": {"Traits": ["Tall"], "Eyes": "Blue"},
            "John": {"Traits": ["Brave"], "Hair": "Brown"}
        }
    }


    resolved = resolver.resolve(data)

    assert "John Smith" in resolved["Characters"]
    assert "John" not in resolved["Characters"]

    merged = resolved["Characters"]["John Smith"]
    assert "Tall" in merged["Traits"]
    assert "Brave" in merged["Traits"]
    assert merged["Eyes"] == "Blue"
    assert merged["Hair"] == "Brown"

def test_merge_complex_values(resolver):
    v1 = {"a": 1, "b": [2]}
    v2 = {"b": [3], "c": 4}
    merged = resolver._merge_values(v1, v2)
    assert merged["a"] == 1
    assert 2 in merged["b"]
    assert 3 in merged["b"]
    assert merged["c"] == 4
