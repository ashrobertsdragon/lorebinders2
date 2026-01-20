"""Centralized application settings using pydantic-settings."""

from pathlib import Path

from pydantic_ai.settings import ModelSettings
from pydantic_settings import BaseSettings, SettingsConfigDict

from lorebinders.agent.settings import settings_config


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="LOREBINDERS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    extraction_model: str = "openai:gpt-5-nano"
    analysis_model: str = "openai:gpt-5-mini"
    summarization_model: str = "openai:gpt-5-nano"

    workspace_base_path: Path = Path("work")

    categories: list[str] = ["Characters", "Locations"]
    character_traits: list[str] = [
        "Appearance",
        "Personality",
        "Mood",
        "Relationships to other characters",
    ]
    location_traits: list[str] = [
        "Key Features",
        "Relative Location",
        "Character Familiarity",
    ]

    @property
    def extractor_model_settings(self) -> ModelSettings:
        """Set reasoning level for the extraction agent."""
        model_provider = self.extraction_model.split(":")[0]
        return settings_config(model_provider)


def get_settings() -> Settings:
    """Get application settings singleton.

    Returns:
        The application settings instance.
    """
    return Settings()
