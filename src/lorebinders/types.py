from typing import TypedDict, TypeVar

from typing_extensions import NotRequired

T = TypeVar("T")


class CategoryTarget(TypedDict):
    """Target category for batch analysis."""

    name: str
    traits: NotRequired[list[str]]
    entities: list[str]


CategoryTraits = dict[str, list[str]]
CategoryChapterData = dict[int, CategoryTraits]
CategoryData = dict[str, CategoryChapterData]
TraitDict = dict[str, str | list[str]]
EntityChapterData = dict[int, TraitDict]
EntityEntry = dict[int | str, TraitDict | str]
EntityData = dict[str, EntityEntry]
Binder = dict[str, EntityData]
SortedEntities = dict[str, dict[str, list[int]]]

CleanableValue = str | dict[str, "CleanableValue"] | list["CleanableValue"]
CleanableDict = dict[str, CleanableValue]
