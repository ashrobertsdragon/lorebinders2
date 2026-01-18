from pathlib import Path

from pydantic_ai import Agent, RunContext
from pydantic_ai.agent import RunOutputDataT
from pydantic_ai.tools import AgentDepsT

from lorebinders.models import (
    AgentDeps,
    AnalysisResult,
    NarratorConfig,
    SummarizerResult,
)
from lorebinders.settings import Settings, get_settings


def load_prompt_from_assets(filename: str) -> str:
    """Load a prompt template from the assets directory.

    Returns:
        The content of the prompt file.
    """
    return (Path(__file__).parent / "assets" / "prompts" / filename).read_text(
        encoding="utf-8"
    )


def create_agent(
    model_name: str,
    deps_type: type[AgentDepsT],
    output_type: type[RunOutputDataT],
) -> Agent[AgentDepsT, RunOutputDataT]:
    """Create a PydanticAI Agent with the given model.

    Args:
        model_name: The model identifier (e.g. 'openai:gpt-4o-mini').
        deps_type: The type of dependencies (configuration) the agent uses.
        output_type: The expected output type of the agent.

    Returns:
        A configured Agent instance.
    """
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
    settings: Settings | None = None,
) -> Agent[AgentDeps, list[str]]:
    """Create a configured extraction agent.

    Args:
        settings: Application settings. Uses defaults if not provided.

    Returns:
        A configured Agent instance.
    """
    settings = settings or get_settings()
    agent = create_agent(
        settings.extraction_model,
        deps_type=AgentDeps,
        output_type=list[str],
    )

    @agent.system_prompt
    def _extraction_system_prompt(ctx: RunContext[AgentDeps]) -> str:
        return ctx.deps.prompt_loader("extraction.txt")

    return agent


def build_extraction_user_prompt(
    text: str,
    target_category: str,
    description: str | None = None,
    narrator: NarratorConfig | None = None,
) -> str:
    """Build the user prompt with configuration constraints.

    Returns:
        The constructed user prompt string.
    """
    prompt = f"## EXTRACT: {target_category}\n"

    if description:
        prompt += f"Category Description: {description}\n"

    if narrator:
        prompt += "Narrator Handling:"
        if narrator.is_3rd_person:
            prompt += (
                "\n- The text is in 3rd person. Do not extract the narrator."
            )
        if narrator.name:
            prompt += (
                f"\n- The narrator is named '{narrator.name}'. "
                "Do not extract them."
            )
        prompt += "\n"

    prompt += f"\n## TEXT CHUNK\n{text}"
    return prompt


def create_analysis_agent(
    settings: Settings | None = None,
) -> Agent[AgentDeps, AnalysisResult]:
    """Create a configured analysis agent.

    Args:
        settings: Application settings. Uses defaults if not provided.

    Returns:
        A configured Agent instance.
    """
    settings = settings or get_settings()
    agent = create_agent(
        settings.analysis_model,
        deps_type=AgentDeps,
        output_type=AnalysisResult,
    )

    @agent.system_prompt
    def _analysis_system_prompt(ctx: RunContext[AgentDeps]) -> str:
        return ctx.deps.prompt_loader("analysis.txt")

    return agent


def build_analysis_user_prompt(
    context_text: str,
    entity_name: str,
    category: str,
    traits: list[str],
) -> str:
    """Build user prompt with context FIRST for prefix caching.

    Returns:
        The constructed user prompt string.
    """
    return (
        f"## CONTEXT\n{context_text}\n\n"
        f"## TASK\n"
        f"Analyze the {category}: '{entity_name}'\n"
        f"Focus on traits: {', '.join(traits)}"
    )


def create_summarization_agent(
    settings: Settings | None = None,
) -> Agent[AgentDeps, SummarizerResult]:
    """Create a configured summarization agent.

    Args:
        settings: Application settings. Uses defaults if not provided.

    Returns:
        A configured Agent instance.
    """
    settings = settings or get_settings()
    agent = create_agent(
        settings.summarization_model,
        deps_type=AgentDeps,
        output_type=SummarizerResult,
    )

    @agent.system_prompt
    def _summarization_system_prompt(ctx: RunContext[AgentDeps]) -> str:
        return ctx.deps.prompt_loader("summarization.txt")

    return agent


def build_summarization_user_prompt(
    entity_name: str,
    category: str,
    context_data: str,
) -> str:
    """Build user prompt for summarization.

    Returns:
        The constructed user prompt string.
    """
    return (
        f"## ENTITY: {entity_name} ({category})\n\n"
        f"## CONTEXT DATA\n{context_data}\n\n"
        f"## TASK\nProvide a Story Bible summary."
    )
