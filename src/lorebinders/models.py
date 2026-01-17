from pathlib import Path

from pydantic import BaseModel, Field


class NarratorConfig(BaseModel):
    """Configuration for narrator detection and handling."""

    is_3rd_person: bool = True
    name: str | None = None


class RunConfiguration(BaseModel):
    """Configuration for a complete execution run."""

    book_path: Path
    author_name: str
    book_title: str
    narrator_config: NarratorConfig
    custom_traits: list[str] = Field(default_factory=list)
    custom_categories: list[str] = Field(default_factory=list)


class Chapter(BaseModel):
    """Represents a single chapter from the book."""

    number: int
    title: str
    content: str


class Book(BaseModel):
    """Represents the entire ingested book."""

    title: str
    author: str
    chapters: list[Chapter] = Field(default_factory=list)


class CharacterProfile(BaseModel):
    """Structured output for a character analysis."""

    name: str
    traits: dict[str, str] = Field(
        default_factory=dict, description="Map of trait keys to analysis values"
    )
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)


class ExtractionConfig(BaseModel):
    """Configuration for the entity extraction agent."""

    target_category: str
    description: str | None = None
    narrator: NarratorConfig | None = None


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
