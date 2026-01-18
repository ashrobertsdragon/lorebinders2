import pytest
from lorebinders.refinement.deduplication import _is_similar_key, resolve_binder

@pytest.mark.parametrize(
    "key1, key2, expected",
    [
        ("John Smith", "John Smiths", True),
        ("Captain John", "John", True),
        ("John", "Jane", False),
    ],
)
def test_is_similar_key(key1: str, key2: str, expected: bool) -> None:
    assert _is_similar_key(key1, key2) == expected

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
