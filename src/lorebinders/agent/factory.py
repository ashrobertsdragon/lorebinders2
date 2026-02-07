import logging
from pathlib import Path

from pydantic_ai import Agent, RunContext
from pydantic_ai.agent import RunOutputDataT
from pydantic_ai.settings import ModelSettings
from pydantic_ai.tools import AgentDepsT

from lorebinders.models import (
    AgentDeps,
    AnalysisResult,
    ExtractionResult,
    NarratorConfig,
    SummarizerResult,
)
from lorebinders.settings import Settings, get_settings
from lorebinders.types import CategoryTarget


def load_prompt_from_assets(filename: str) -> str:
    """Load a prompt template from the assets directory.

    Returns:
        The content of the prompt file.
    """
    return (Path(__file__).parent / "assets" / "prompts" / filename).read_text(
        encoding="utf-8"
    )


logger = logging.getLogger(__name__)


def create_agent(
    model_name: str,
    deps_type: type[AgentDepsT],
    output_type: type[RunOutputDataT],
    model_settings: ModelSettings | None = None,
) -> Agent[AgentDepsT, RunOutputDataT]:
    """Create a PydanticAI Agent with the given model.

    Args:
        model_name: The model identifier (e.g. 'openai:gpt-4o-mini').
        deps_type: The type of dependencies (configuration) the agent uses.
        output_type: The expected output type of the agent.

    Returns:
        A configured Agent instance.
    """
    logger.debug(f"Creating agent for model: {model_name}")
    return Agent(
        model_name,
        deps_type=deps_type,
        output_type=output_type,
        model_settings=model_settings,
    )


def run_agent(
    agent: Agent[AgentDepsT, RunOutputDataT],
    user_prompt: str,
    deps: AgentDepsT,
    model_settings: ModelSettings | None = None,
) -> RunOutputDataT:
    """Run an agent synchronously and return the output.

    Args:
        agent: The agent instance to run.
        user_prompt: The prompt text to send to the agent.
        deps: The dependencies (configuration) for this run.
        model_settings: Optional provider-specific model settings.

    Returns:
        The structured output from the agent.
    """
    logger.debug(f"Running agent with model: {agent.model.name()}")
    try:
        result = agent.run_sync(
            user_prompt, deps=deps, model_settings=model_settings
        )
        logger.debug("Agent run completed successfully")
        return result.output
    except Exception as e:
        logger.error(f"Agent run failed: {e}")
        raise


def create_extraction_agent(
    settings: Settings | None = None,
) -> Agent[AgentDeps, ExtractionResult]:
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
        output_type=ExtractionResult,
        model_settings=settings.extractor_model_settings,
    )

    @agent.system_prompt
    def _extraction_system_prompt(ctx: RunContext[AgentDeps]) -> str:
        return ctx.deps.prompt_loader("extraction.txt")

    return agent


def build_extraction_user_prompt(
    text: str,
    categories: list[str],
    description: str | None = None,
    narrator: NarratorConfig | None = None,
) -> str:
    """Build the user prompt for batch extraction of all categories.

    Args:
        text: The text to extract from.
        categories: The categories to extract.
        description: A description of the categories.
        narrator: The narrator configuration.

    Returns:
        The constructed user prompt string.
    """
    prompt = ["## CATEGORIES TO EXTRACT"]
    prompt.extend([f"- {cat}" for cat in categories])

    if description:
        prompt.append(f"Category Description: {description}")

    if narrator and narrator.is_1st_person and narrator.name:
        prompt.append(
            "## NARRATOR HANDLING\n"
            f"This text is in first person. The narrator is '{narrator.name}'."
        )

    prompt.append(f"## TEXT\n{text}")
    return "\n".join(prompt)


def create_analysis_agent(
    settings: Settings | None = None,
) -> Agent[AgentDeps, list[AnalysisResult]]:
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
        output_type=list[AnalysisResult],
    )

    @agent.system_prompt
    def _analysis_system_prompt(ctx: RunContext[AgentDeps]) -> str:
        return ctx.deps.prompt_loader("analysis.txt")

    return agent


def build_analysis_user_prompt(
    context_text: str,
    categories: list[CategoryTarget],
) -> str:
    """Build user prompt for batch analysis.

    Args:
        context_text: The chapter content.
        categories: List of dicts with 'name', 'entities', 'traits'.

    Returns:
        The constructed user prompt string.
    """
    prompt = [f"## CONTEXT\n{context_text}\n", "## TASKS"]
    for category in categories:
        prompt.append(
            f"### {category['name']}\nAnalyze the following traits:\n"
        )
        prompt.append("\n- ".join(category["traits"]))
        prompt.append("### Entities:\n")
        prompt.extend([f"- {entity}" for entity in category["entities"]])

    return "\n".join(prompt)


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
