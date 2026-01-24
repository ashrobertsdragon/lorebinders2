import pytest

from lorebinders.refinement.sorting import (
    _deduplicate_entity_names,
    _is_similar_key,
    sort_extractions,
)


def test_deduplicate_entity_names_merges_similar() -> None:
    """Test that similar entity names are merged."""
    names = ["Father", "the father", "Father"]
    result = _deduplicate_entity_names(names)
    assert len(result) == 1


def test_deduplicate_entity_names_keeps_distinct() -> None:
    """Test that distinct entity names are preserved."""
    names = ["Alice", "Bob", "Charlie"]
    result = _deduplicate_entity_names(names)
    assert set(result) == {"Alice", "Bob", "Charlie"}


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


def test_sort_merging() -> None:
    data = {
        1: {"Characters": ["John Smith", "John"]},
        2: {"Characters": ["John"]},
    }

    sorted_data = sort_extractions(data)

    assert "John Smith" in sorted_data["Characters"]
    assert "John" not in sorted_data["Characters"]

    merged = sorted_data["Characters"]["John Smith"]
    assert 1 in merged
    assert 2 in merged
