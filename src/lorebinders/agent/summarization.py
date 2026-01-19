"""Entity summarization using AI agents."""

import json
from typing import Any

from pydantic_ai import Agent

from lorebinders.agent.factory import (
    build_summarization_user_prompt,
    create_summarization_agent,
    load_prompt_from_assets,
    run_agent,
)
from lorebinders.models import AgentDeps, SummarizerResult
from lorebinders.settings import get_settings


def _format_context(data: Any) -> str:
    """Format the entity data into a readable string for the AI.

    Args:
        data (Any): The data to format.

    Returns:
        str: The formatted data.
    """
    if isinstance(data, dict):
        return json.dumps(data, indent=2)
    return str(data)


def summarize_binder(
    binder: dict[str, Any],
    agent: Agent[AgentDeps, SummarizerResult] | None = None,
) -> dict[str, Any]:
    """Summarize entities in the binder.

    Iterates through categories and entities, generating a summary for each
    using the AI agent, and appending it to the entity's data.

    Args:
        binder: The refined binder dictionary.
        agent: Optional agent instance for testing.

    Returns:
        The binder with added summaries.
    """
    summarized_binder = binder.copy()
    if agent is None:
        agent = create_summarization_agent()

    for category, entities in binder.items():
        if not isinstance(entities, dict):
            continue

        for name, details in entities.items():
            context_str = _format_context(details)

            prompt = build_summarization_user_prompt(
                entity_name=name,
                category=category,
                context_data=context_str,
            )

            try:
                deps = AgentDeps(
                    settings=get_settings(),
                    prompt_loader=load_prompt_from_assets,
                )
                result: SummarizerResult = run_agent(agent, prompt, deps)

                if isinstance(summarized_binder[category][name], dict):
                    summarized_binder[category][name]["Summary"] = (
                        result.summary
                    )
                else:
                    summarized_binder[category][name] = {
                        "Original": summarized_binder[category][name],
                        "Summary": result.summary,
                    }
            except Exception as e:
                print(f"Failed to summarize {name}: {e}")
                pass

    return summarized_binder
