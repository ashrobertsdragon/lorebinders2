import pytest

from lorebinders.refinement.normalization import (
    merge_values,
    remove_titles,
    to_singular,
)


@pytest.mark.parametrize(
    "name, expected",
    [
        ("Captain John Smith", "John Smith"),
        ("Dr. Watson", "Watson"),
        ("The Kitchen", "Kitchen"),
        ("John Smith", "John Smith"),
        ("Captain", "Captain"),
        ("", ""),
    ],
)
def test_remove_titles(name: str, expected: str) -> None:
    assert remove_titles(name) == expected


@pytest.mark.parametrize(
    "plural, expected",
    [
        ("Cats", "Cat"),
        ("Dogs", "Dog"),
        ("Trees", "Tree"),
        ("Boys", "Boy"),
        ("Cities", "City"),
        ("Parties", "Party"),
        ("Families", "Family"),
        ("Wolves", "Wolf"),
        ("Shelves", "Shelf"),
        ("Knives", "Knife"),
        ("Wives", "Wife"),
        ("Lives", "Life"),
        ("Cacti", "Cactus"),
        ("Fungi", "Fungus"),
        ("Data", "Datum"),
        ("Men", "Men"),
        ("Women", "Women"),
        ("Potatoes", "Potato"),
        ("Heroes", "Hero"),
        ("Tomatoes", "Tomato"),
        ("Glasses", "Glass"),
        ("Boxes", "Box"),
        ("Foxes", "Fox"),
        ("Watches", "Watch"),
        ("Dishes", "Dish"),
        ("John", "John"),
        ("James", "Jame"),
        ("", ""),
    ],
)
def test_to_singular(plural: str, expected: str) -> None:
    assert to_singular(plural) == expected


def test_merge_values() -> None:
    v1 = {"a": 1, "b": [2]}
    v2 = {"b": [3], "c": 4}
    merged_dict = merge_values(v1, v2)
    assert merged_dict["a"] == 1
    assert 2 in merged_dict["b"]
    assert 3 in merged_dict["b"]
    assert merged_dict["c"] == 4

    l1 = [1, 2]
    l2 = [2, 3]
    merged_list = merge_values(l1, l2)
    assert set(merged_list) == {1, 2, 3}
    assert set(merge_values(1, [2])) == {1, 2}
    assert set(merge_values([1], 2)) == {1, 2}
    assert merge_values(1, 1) == 1
    assert set(merge_values(1, 2)) == {1, 2}
