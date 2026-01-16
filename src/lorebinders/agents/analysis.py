import os
from pathlib import Path

from pydantic_ai import Agent, RunContext

from lorebinders.agents.models import AnalysisConfig, AnalysisResult


def _get_prompt_path() -> Path:
    """Get the path to the analysis prompt template.

    Returns:
        The path to the analysis.txt template file.
    """
    return Path(__file__).parent.parent / "assets" / "prompts" / "analysis.txt"


analysis_agent = Agent(
    os.getenv("ANALYSIS_MODEL"),
    deps_type=AnalysisConfig,
    output_type=AnalysisResult,
)


@analysis_agent.system_prompt
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


def run_analysis(text: str, config: AnalysisConfig) -> AnalysisResult:
    """Run the agent synchronously to analyze an entity.

    Returns:
        The structured analysis result.
    """
    result = analysis_agent.run_sync(text, deps=config)
    return result.output
