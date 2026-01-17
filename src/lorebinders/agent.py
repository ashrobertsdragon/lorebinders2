import os
from pathlib import Path

from pydantic_ai import Agent, RunContext
from pydantic_ai.agent import RunOutputDataT
from pydantic_ai.tools import AgentDepsT

from lorebinders.models import (
    AnalysisConfig,
    AnalysisResult,
    ExtractionConfig,
    SummarizerConfig,
    SummarizerResult,
)


def load_prompt(filename: str) -> str:
    """Load a prompt template from the assets directory.

    Args:
        filename: The name of the prompt file (e.g. 'analysis.txt').

    Returns:
        The content of the prompt file.
    """
    prompt_path = Path(__file__).parent / "assets" / "prompts" / filename
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


def create_extraction_agent(
    model_env_var: str = "EXTRACTION_MODEL",
) -> Agent[ExtractionConfig, list[str]]:
    """Create a configured extraction agent.

    Returns:
        A configured Agent instance.
    """
    agent = create_agent(
        model_env_var,
        deps_type=ExtractionConfig,
        output_type=list[str],
    )

    @agent.system_prompt
    def _extraction_system_prompt(ctx: RunContext[ExtractionConfig]) -> str:
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
                    "\n- The text is in 3rd person. Do not extract the "
                    "narrator."
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

    return agent


def create_analysis_agent(
    model_env_var: str = "ANALYSIS_MODEL",
) -> Agent[AnalysisConfig, AnalysisResult]:
    """Create a configured analysis agent.

    Returns:
        A configured Agent instance.
    """
    agent = create_agent(
        model_env_var,
        deps_type=AnalysisConfig,
        output_type=AnalysisResult,
    )

    @agent.system_prompt
    def _analysis_system_prompt(ctx: RunContext[AnalysisConfig]) -> str:
        config = ctx.deps
        category = config.category
        traits = ", ".join(config.traits)

        return (
            f"You are an expert literary analyst specializing in {category}. "
            f"Your task is to analyze characters based on their description "
            f"in the text.\nFocus on these traits: {traits}."
        )

    return agent


def create_summarization_agent(
    model_env_var: str = "SUMMARIZATION_MODEL",
) -> Agent[SummarizerConfig, SummarizerResult]:
    """Create a configured summarization agent.

    Returns:
        A configured Agent instance.
    """
    agent = create_agent(
        model_env_var,
        deps_type=SummarizerConfig,
        output_type=SummarizerResult,
    )

    @agent.system_prompt
    def _summarization_system_prompt(ctx: RunContext[SummarizerConfig]) -> str:
        config = ctx.deps
        template = load_prompt("summarization.txt")
        return template.format(
            category=config.category,
            entity_name=config.entity_name,
            context_data=config.context_data,
        )

    return agent
