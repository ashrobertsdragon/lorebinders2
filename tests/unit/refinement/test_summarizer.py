import json
import pytest
from pydantic_ai.models.function import FunctionModel
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, SystemPromptPart, TextPart

from lorebinders.agents.summarization import run_summarization, summarization_agent
from lorebinders.agents.models import SummarizerConfig, SummarizerResult
from lorebinders.refinement.summarizer import summarize_binder

def test_summarization_agent_run_sync_and_prompt():
    """Test run_summarization execution and prompt generation."""

    captured_messages = []

    expected_result_dict = {
        "entity_name": "Gandalf",
        "summary": "A powerful wizard."
    }

    expected_result_obj = SummarizerResult(
        entity_name="Gandalf",
        summary="A powerful wizard."
    )

    async def mock_model_call(messages: list[ModelMessage], info) -> ModelResponse:
        nonlocal captured_messages
        captured_messages = messages
        return ModelResponse(parts=[TextPart(content=json.dumps(expected_result_dict))])

    with summarization_agent.override(model=FunctionModel(mock_model_call)):
        config = SummarizerConfig(
            entity_name="Gandalf",
            category="Character",
            context_data="He is a wizard. He wears grey."
        )

        result = run_summarization(config)

        assert result == expected_result_obj

    system_prompt_content = ""
    for msg in captured_messages:
        if isinstance(msg, ModelRequest):
            for part in msg.parts:
                if isinstance(part, SystemPromptPart):
                    system_prompt_content = part.content
                    break

    assert system_prompt_content != ""
    assert "Gandalf" in system_prompt_content
    assert "Character" in system_prompt_content
    assert "He is a wizard" in system_prompt_content


def test_entity_summarizer_orchestration():
    """Test that summarize_binder correctly constructs config and orchestrates the agent."""

    expected_result_dict = {
        "entity_name": "Frodo",
        "summary": "A brave hobbit."
    }

    async def mock_model_call(messages: list[ModelMessage], info) -> ModelResponse:
        return ModelResponse(parts=[TextPart(content=json.dumps(expected_result_dict))])

    with summarization_agent.override(model=FunctionModel(mock_model_call)):
        binder = {
            "Characters": {
                "Frodo": {
                    "Traits": ["Brave", "Short"],
                    "Item": "Ring"
                }
            }
        }

        result_binder = summarize_binder(binder)

        assert "Characters" in result_binder
        assert "Frodo" in result_binder["Characters"]
        assert "Summary" in result_binder["Characters"]["Frodo"]
        assert result_binder["Characters"]["Frodo"]["Summary"] == "A brave hobbit."

        assert "Traits" in result_binder["Characters"]["Frodo"]
