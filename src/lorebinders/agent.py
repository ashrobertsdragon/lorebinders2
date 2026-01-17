import os
from pathlib import Path

from lorebinder.models import (
    AnalysisConfig,
    AnalysisResult,
    ExtractionConfig,
    SummarizerConfig,
    SummarizerResult,
)
from pydantic_ai import Agent, RunContext
from pydantic_ai.agent import RunOutputDataT
from pydantic_ai.tools import AgentDepsT


def load_prompt(filename: str) -> str:
    """Load a prompt template from the assets directory.

    Args:
        filename: The name of the prompt file (e.g. 'analysis.txt').

    Returns:
        The content of the prompt file.
    """
    prompt_path = Path(__file__).parent.parent / "assets" / "prompts" / filename
    return prompt_path.read_text(encoding="utf-8")


def create_agent(
    model_env_var: str,
    deps_type: type[AgentDepsT],
    output_type: type[RunOutputDataT],
) -> Agent[AgentDepsT, RunOutputDataT]:
    """Create a PydanticAI Agent configured from environment variables.

    Args:
        model_env_var: The name of the environment variable containing the
            model name.
        deps_type: The type of dependencies (configuration) the agent uses.
        output_type: The expected output type of the agent.

    Returns:
        A configured Agent instance.

    Raises:
        ValueError: If the model environment variable is not set.
    """
    model_name = os.getenv(model_env_var)
    if not model_name:
        raise ValueError(f"Environment variable {model_env_var} is not set.")
    return Agent(
        model_name,
        deps_type=deps_type,
        output_type=output_type,
    )


def run_agent(
    agent: Agent[AgentDepsT, RunOutputDataT],
    user_prompt: str,
    deps: AgentDepsT,
) -> RunOutputDataT:
    """Run an agent synchronously and return the output.

    Args:
        agent: The agent instance to run.
        user_prompt: The prompt text to send to the agent.
        deps: The dependencies (configuration) for this run.

    Returns:
        The structured output from the agent.
    """
    result = agent.run_sync(user_prompt, deps=deps)
    return result.output


extraction_agent = create_agent(
    "EXTRACTION_MODEL",
    deps_type=ExtractionConfig,
    output_type=list[str],
)


@extraction_agent.system_prompt
def _extraction_system_prompt(ctx: RunContext[ExtractionConfig]) -> str:
    """Generate system prompt based on extraction configuration.

    Args:
        ctx: The run context containing the extraction configuration.

    Returns:
        The system prompt for the extraction agent.
    """
    config = ctx.deps
    category = config.target_category

    template = load_prompt("extraction.txt")

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


analysis_agent = create_agent(
    "ANALYSIS_MODEL",
    deps_type=AnalysisConfig,
    output_type=AnalysisResult,
)


@analysis_agent.system_prompt
def _analysis_system_prompt(ctx: RunContext[AnalysisConfig]) -> str:
    """Generate system prompt based on analysis configuration.

    Args:
        ctx: The run context containing the analysis configuration.

    Returns:
        The system prompt for the analysis agent.
    """
    config = ctx.deps
    entity = config.target_entity
    category = config.category
    traits = ", ".join(config.traits)

    template = load_prompt("analysis.txt")

    return template.format(category=category, entity=entity, traits=traits)


summarization_agent = create_agent(
    "SUMMARIZATION_MODEL",
    deps_type=SummarizerConfig,
    output_type=SummarizerResult,
)


@summarization_agent.system_prompt
def _summarization_system_prompt(ctx: RunContext[SummarizerConfig]) -> str:
    """Generate system prompt based on summarization configuration.

    Args:
        ctx: The run context containing the summarization configuration.

    Returns:
        The system prompt for the summarization agent.
    """
    config = ctx.deps
    template = load_prompt("summarization.txt")

    return template.format(
        category=config.category,
        entity_name=config.entity_name,
        context_data=config.context_data,
    )
