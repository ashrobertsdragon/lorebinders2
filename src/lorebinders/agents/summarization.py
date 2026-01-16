"""Agent for summarizing aggregated entity data."""

import os
from pathlib import Path

from pydantic_ai import Agent, RunContext

from lorebinders.agents.models import SummarizerConfig, SummarizerResult


def _get_prompt_path() -> Path:
    """Get the path to the summarization prompt template.

    Returns:
        The path to the summarization.txt template file.
    """
    return (
        Path(__file__).parent.parent
        / "assets"
        / "prompts"
        / "summarization.txt"
    )


summarization_agent = Agent(
    os.getenv("SUMMARIZATION_MODEL", os.getenv("ANALYSIS_MODEL")),
    deps_type=SummarizerConfig,
    output_type=SummarizerResult,
)


@summarization_agent.system_prompt
def _system_prompt(ctx: RunContext[SummarizerConfig]) -> str:
    """Generate system prompt based on summarization configuration.

    Returns:
        The generated system prompt string.
    """
    config = ctx.deps
    template = _get_prompt_path().read_text(encoding="utf-8")

    return template.format(
        category=config.category,
        entity_name=config.entity_name,
        context_data=config.context_data,
    )


class EntitySummarizationAgent:
    """Agent for summarizing entities based on aggregated data."""

    def __init__(self):
        """Initialize the summarization agent."""
        self.agent = summarization_agent

    def run_sync(self, config: SummarizerConfig) -> SummarizerResult:
        """Run the agent synchronously to summarize an entity.

        Returns:
            The structured summarization result.
        """
        result = self.agent.run_sync(
            "Please summarize this entity.", deps=config
        )
        return result.output
