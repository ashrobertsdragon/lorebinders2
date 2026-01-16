from pydantic import BaseModel

from lorebinders.core.models import NarratorConfig


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
