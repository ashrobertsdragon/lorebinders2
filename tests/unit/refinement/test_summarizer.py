import json

import pytest
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, SystemPromptPart, TextPart
from pydantic_ai.models.function import FunctionModel

from lorebinders.agent import create_summarization_agent, run_agent
from lorebinders.models import SummarizerConfig, SummarizerResult
from lorebinders.refinement.summarization import summarize_binder


def test_summarization_agent_run_sync_and_prompt() -> None:
    captured_messages: list[ModelMessage] = []

    expected_result_dict = {"entity_name": "Gandalf", "summary": "A powerful wizard."}

    expected_result_obj = SummarizerResult(
        entity_name="Gandalf", summary="A powerful wizard."
    )

    async def mock_model_call(
        messages: list[ModelMessage], info: object
    ) -> ModelResponse:
        nonlocal captured_messages
        captured_messages = list(messages)
        return ModelResponse(parts=[TextPart(content=json.dumps(expected_result_dict))])

    agent = create_summarization_agent()
    with agent.override(model=FunctionModel(mock_model_call)):
        config = SummarizerConfig(
            entity_name="Gandalf",
            category="Character",
            context_data="He is a wizard. He wears grey.",
        )

        result = run_agent(agent, "Please summarize this entity.", config)

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

@pytest.mark.skip(reason="Requires Phase 6 testing overhaul for agent injection")
def test_entity_summarizer_orchestration() -> None:
    expected_result_dict = {"entity_name": "Frodo", "summary": "A brave hobbit."}

    async def mock_model_call(
        messages: list[ModelMessage], info: object
    ) -> ModelResponse:
        return ModelResponse(parts=[TextPart(content=json.dumps(expected_result_dict))])

    agent = create_summarization_agent()
    with agent.override(model=FunctionModel(mock_model_call)):
        binder = {
            "Characters": {"Frodo": {"Traits": ["Brave", "Short"], "Item": "Ring"}}
        }

        result_binder = summarize_binder(binder)

        assert "Characters" in result_binder
        assert "Frodo" in result_binder["Characters"]
        assert "Summary" in result_binder["Characters"]["Frodo"]
        assert result_binder["Characters"]["Frodo"]["Summary"] == "A brave hobbit."
        assert "Traits" in result_binder["Characters"]["Frodo"]
