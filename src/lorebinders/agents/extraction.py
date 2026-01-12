from pydantic_ai import Agent, RunContext

from lorebinders.agents.models import ExtractionConfig


def _system_prompt(ctx: RunContext[ExtractionConfig]) -> str:
    """Generate system prompt based on extraction configuration.

    Returns:
        The generated system prompt string.
    """
    config = ctx.deps
    category = config.target_category

    prompt = (
        "You are an expert literary analyst. Your task is to extract all "
        f"entities matching the category '{category}' from the provided "
        "text chunk.\n\n"
    )

    if config.description:
        prompt += f"Category Description: {config.description}\n"

    prompt += "\nReturn ONLY a list of names/identifiers. No other text."

    if config.narrator:
        prompt += "\n\nNarrator Handling:"
        if config.narrator.is_3rd_person:
            prompt += (
                "\n- The text is in 3rd person. Do not extract the narrator."
            )
        if config.narrator.name:
            prompt += (
                f"\n- The narrator is named '{config.narrator.name}'."
                " Do not extract them."
            )

    return prompt


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
