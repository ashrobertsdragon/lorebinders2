from pydantic_ai import Agent, RunContext

from lorebinders.agents.models import AnalysisConfig, AnalysisResult


def _system_prompt(ctx: RunContext[AnalysisConfig]) -> str:
    """Generate system prompt based on analysis configuration.

    Returns:
        The generated system prompt string.
    """
    config = ctx.deps
    entity = config.target_entity
    category = config.category
    traits = ", ".join(config.traits)

    prompt = (
        f"You are an expert literary analyst. Your task is to analyze the "
        f"{category} known as '{entity}' based on the provided text chunk.\n\n"
        f"Extract the following traits: {traits}.\n"
    )

    prompt += (
        "\nFor each trait, provide:\n"
        "1. The value (concise description)\n"
        "2. The evidence (direct quote or reference)\n\n"
        "If a trait is not found, return 'Not Found' for valid and empty "
        "string for evidence."
    )

    return prompt


class UniversalAnalysisAgent:
    """Agent for analyzing specific entities against user-defined schemas."""

    def __init__(self, model_name: str = "openai:gpt-4o"):
        """Initialize the analysis agent."""
        self.agent = Agent(
            model_name,
            deps_type=AnalysisConfig,
            result_type=AnalysisResult,
            system_prompt=_system_prompt,
        )

    def run_sync(self, text: str, config: AnalysisConfig) -> AnalysisResult:
        """Run the agent synchronously to analyze an entity.

        Returns:
            The structured analysis result.
        """
        result = self.agent.run_sync(text, deps=config)
        return result.data
