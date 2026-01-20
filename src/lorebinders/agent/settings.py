"""Set model settings for agents."""

from pydantic_ai import ModelSettings


def settings_config(model_provider: str) -> ModelSettings:
    """Set model settings for agents.

    Args:
        model_provider (str): The model provider to use.

    Returns:
        ModelSettings: The model settings for the specified model provider.
    """
    match model_provider:
        case "openai":
            from pydantic_ai.models.openai import OpenAIChatModelSettings

            return OpenAIChatModelSettings(openai_reasoning_effort="low")
        case "anthropic":
            from pydantic_ai.models.anthropic import AnthropicModelSettings

            return AnthropicModelSettings(
                anthropic_thinking={"type": "disabled"}
            )
        case "google" | "vertexai" | "gemini":
            from pydantic_ai.models.google import GoogleModelSettings

            return GoogleModelSettings(
                google_thinking_config={"include_thoughts": False}
            )
        case "groq":
            from pydantic_ai.models.groq import GroqModelSettings

            return GroqModelSettings(groq_reasoning_format="hidden")
        case "openrouter":
            from pydantic_ai.models.openrouter import OpenRouterModelSettings

            return OpenRouterModelSettings(
                openrouter_reasoning={"effort": "low"}
            )
        case _:
            return ModelSettings()
