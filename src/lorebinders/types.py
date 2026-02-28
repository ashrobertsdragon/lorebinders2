from typing import TypeAlias

TraitValue: TypeAlias = str | list[str]
EntityTraits: TypeAlias = dict[str, TraitValue]
SimpleValue: TypeAlias = str | int | float | bool | None
CleanableValue: TypeAlias = SimpleValue | EntityTraits | list[str]
SortedExtractions: TypeAlias = dict[str, dict[str, list[int]]]
