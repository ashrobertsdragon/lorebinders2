from pathlib import Path

from pydantic_ai import Agent, RunContext

from lorebinders.agents.models import ExtractionConfig


def _get_prompt_path() -> Path:
    """Get the path to the extraction prompt template."""
    return (
        Path(__file__).parent.parent / "assets" / "prompts" / "extraction.txt"
    )


def _system_prompt(ctx: RunContext[ExtractionConfig]) -> str:
    """Generate system prompt based on extraction configuration.

    Returns:
        The generated system prompt string.
    """
    config = ctx.deps
    category = config.target_category

    template = _get_prompt_path().read_text(encoding="utf-8")

    description_block = ""
    if config.description:
        description_block = f"Category Description: {config.description}"

    narrator_block = ""
    if config.narrator:
        narrator_block = "Narrator Handling:"
        if config.narrator.is_3rd_person:
            narrator_block += (
                "\n- The text is in 3rd person. Do not extract the narrator."
            )
        if config.narrator.name:
            narrator_block += (
                f"\n- The narrator is named '{config.narrator.name}'."
                " Do not extract them."
            )

    return template.format(
        target_category=category,
        description_block=description_block,
        narrator_block=narrator_block,
    )


class EntityExtractionAgent:
    """Agent for extracting entities of a specific category from text."""

    def __init__(self, model_name: str = "openai:gpt-4o"):
        """Initialize the extraction agent."""
        self.agent = Agent(
            model_name,
            deps_type=ExtractionConfig,
            result_type=list[str],
            system_prompt=_system_prompt,
        )

    def run_sync(self, text: str, config: ExtractionConfig) -> list[str]:
        """Run the agent synchronously to extract entities.

        Returns:
             A list of extracted entity names/identifiers.
        """
        result = self.agent.run_sync(text, deps=config)
        return result.data
