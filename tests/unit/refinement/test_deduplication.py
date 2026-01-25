from typing import Any

import pytest

from lorebinders.refinement.deduplication import (
    _prioritize_keys,
    _resolve_category_entities,
    resolve_binder,
)


@pytest.mark.parametrize(
    "key1, key2, expected_keep, expected_merge",
    [
        ("John", "John Smith", "John", "John Smith"),
        ("John Smith", "John", "John", "John Smith"),
        ("Foo", "FooBar", "Foo", "FooBar"),
        ("Apple", "Berry", "Berry", "Apple"),
        ("Sam", "Samwise", "Sam", "Samwise"),
        (
            "The King",
            "King",
            "The King",
            "King",
        ),
        (
            "gandalf",
            "Gandalf",
            "Gandalf",
            "gandalf",
        ),
        (
            "Frodo",
            "FRODO",
            "FRODO",
            "Frodo",
        ),
        ("Merry", "Meriadoc", "Merry", "Meriadoc"),
        ("Aragorn", "Strider", "Strider", "Aragorn"),
    ],
)
def test_prioritize_keys(
    key1: str, key2: str, expected_keep: str, expected_merge: str
) -> None:
    keep, merge = _prioritize_keys(key1, key2)
    assert keep == expected_keep
    assert merge == expected_merge


def test_resolve_category_entities_merges_duplicates() -> None:
    entities: dict[str, Any] = {
        "John": {1: {"trait": "A"}},
        "John Smith": {1: {"trait": "B"}},
        "Jane": {1: {"trait": "C"}},
    }
    resolved = _resolve_category_entities(entities)
    assert "John" not in resolved
    assert "John Smith" in resolved
    assert "Jane" in resolved


def test_resolve_category_entities_preserves_distinct() -> None:
    entities: dict[str, Any] = {
        "John": {},
        "Jane": {},
    }
    resolved = _resolve_category_entities(entities)
    assert len(resolved) == 2
    assert "John" in resolved
    assert "Jane" in resolved


def test_resolve_binder_resolves_categories() -> None:
    binder: dict[str, Any] = {
        "Characters": {
            "John": {1: {"A": "B"}},
            "John Smith": {1: {"C": "D"}},
        },
        "Locations": {
            "SomeMetadata": "Value",
        },
    }
    resolved = resolve_binder(binder)
    assert "John" not in resolved["Characters"]
    assert "John Smith" in resolved["Characters"]
    assert resolved["Locations"] == {"SomeMetadata": "Value"}
