from pathlib import Path

from pydantic_ai import Agent, RunContext

from lorebinders.agents.models import AnalysisConfig, AnalysisResult


def _get_prompt_path() -> Path:
    """Get the path to the analysis prompt template."""
    return Path(__file__).parent.parent / "assets" / "prompts" / "analysis.txt"


def _system_prompt(ctx: RunContext[AnalysisConfig]) -> str:
    """Generate system prompt based on analysis configuration.

    Returns:
        The generated system prompt string.
    """
    config = ctx.deps
    entity = config.target_entity
    category = config.category
    traits = ", ".join(config.traits)

    template = _get_prompt_path().read_text(encoding="utf-8")

    return template.format(category=category, entity=entity, traits=traits)


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
