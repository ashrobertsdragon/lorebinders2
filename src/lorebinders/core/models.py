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
