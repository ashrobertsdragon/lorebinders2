from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict

from pydantic import BaseModel, Field
from typing_extensions import NotRequired

from lorebinders.settings import Settings


class EntityTarget(TypedDict):
    """Target entity for batch analysis."""

    name: str
    category: str
    traits: NotRequired[list[str]]


TraitDict = dict[str, str | list[str]]
EntityChapterData = dict[int, TraitDict]
EntityData = dict[str, EntityChapterData]
Binder = dict[str, EntityData]


@dataclass
class AgentDeps:
    """Dependencies injected into agents."""

    settings: Settings
    prompt_loader: Callable[[str], str]


class NarratorConfig(BaseModel):
    """Configuration for narrator detection and handling."""

    is_1st_person: bool = False
    name: str | None = None


class RunConfiguration(BaseModel):
    """Configuration for a complete execution run."""

    book_path: Path
    author_name: str
    book_title: str
    narrator_config: NarratorConfig
    custom_traits: dict[str, list[str]] = Field(default_factory=dict)
    custom_categories: list[str] = Field(default_factory=list)


class Chapter(BaseModel):
    """Represents a single chapter from the book."""

    number: int
    title: str
    content: str
    profiles: list["EntityProfile"] = Field(default_factory=list)


class Book(BaseModel):
    """Represents the entire ingested book."""

    title: str
    author: str
    chapters: list[Chapter] = Field(default_factory=list)


class EntityProfile(BaseModel):
    """Structured output for an entity analysis."""

    name: str
    category: str
    chapter_number: int
    traits: dict[str, str | list[str]] = Field(
        default_factory=dict, description="Map of trait keys to analysis values"
    )
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)


class ExtractionConfig(BaseModel):
    """Configuration for the entity extraction agent."""

    target_categories: list[str]
    description: str | None = None
    narrator: NarratorConfig | None = None


class CategoryEntities(BaseModel):
    """Entities extracted for a single category."""

    category: str = Field(description="Category name (e.g. 'Characters')")
    entities: list[str] = Field(
        default_factory=list,
        description="List of entity names found in this category",
    )


class ExtractionResult(BaseModel):
    """Result of entity extraction."""

    results: list[CategoryEntities] = Field(
        default_factory=list,
        description="List of categories with their extracted entity names",
    )

    def to_dict(self) -> dict[str, list[str]]:
        """Convert results list to category→entities dictionary."""
        return {item.category: item.entities for item in self.results}


class AnalysisConfig(BaseModel):
    """Configuration for the entity analysis agent."""

    target_entity: str
    category: str
    traits: list[str]


class TraitValue(BaseModel):
    """A single analyzed trait for an entity."""

    trait: str
    value: str
    evidence: str


class AnalysisResult(BaseModel):
    """Complete analysis result for an entity."""

    entity_name: str
    category: str
    traits: list[TraitValue]


class SummarizerConfig(BaseModel):
    """Configuration for the entity summarization agent."""

    entity_name: str
    category: str
    context_data: str


class SummarizerResult(BaseModel):
    """Result of entity summarization."""

    entity_name: str
    summary: str
