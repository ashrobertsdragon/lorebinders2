import json

from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    SystemPromptPart,
    TextPart,
    UserPromptPart,
)
from pydantic_ai.models.function import FunctionModel

from lorebinders.agent import (
    build_summarization_user_prompt,
    create_summarization_agent,
    run_agent,
)
from lorebinders.agent.summarization import summarize_binder
from lorebinders.models import AgentDeps, SummarizerResult
from lorebinders.settings import Settings


def test_summarization_agent_run_sync_and_prompt() -> None:
    captured_messages: list[ModelMessage] = []

    expected_result_dict = {
        "entity_name": "Gandalf",
        "summary": "A powerful wizard.",
    }

    expected_result_obj = SummarizerResult(
        entity_name="Gandalf", summary="A powerful wizard."
    )

    def mock_model_call(
        messages: list[ModelMessage], info: object
    ) -> ModelResponse:
        nonlocal captured_messages
        captured_messages = list(messages)
        return ModelResponse(
            parts=[TextPart(content=json.dumps(expected_result_dict))]
        )

    agent = create_summarization_agent()
    deps = AgentDeps(
        settings=Settings(),
        prompt_loader=lambda x: f"Mock content for {x}",
    )

    with agent.override(model=FunctionModel(mock_model_call)):
        prompt = build_summarization_user_prompt(
            entity_name="Gandalf",
            category="Character",
            context_data="He is a wizard. He wears grey.",
        )

        result = run_agent(agent, prompt, deps)

        assert result == expected_result_obj

    system_prompt_content = ""
    for msg in captured_messages:
        if isinstance(msg, ModelRequest):
            for part in msg.parts:
                if isinstance(part, SystemPromptPart):
                    system_prompt_content = part.content
                    break

    user_prompt_content = ""
    for msg in captured_messages:
        if isinstance(msg, ModelRequest):
            for part in msg.parts:
                if isinstance(part, UserPromptPart):
                    if isinstance(part.content, str):
                        user_prompt_content += part.content

    assert system_prompt_content == "Mock content for summarization.txt"
    assert "Gandalf" in user_prompt_content
    assert "Character" in user_prompt_content
    assert "He is a wizard" in user_prompt_content


def test_entity_summarizer_orchestration() -> None:
    expected_result_dict = {
        "entity_name": "Frodo",
        "summary": "A brave hobbit.",
    }

    def mock_model_call(
        messages: list[ModelMessage], info: object
    ) -> ModelResponse:
        return ModelResponse(
            parts=[TextPart(content=json.dumps(expected_result_dict))]
        )

    agent = create_summarization_agent()
    with agent.override(model=FunctionModel(mock_model_call)):
        binder = {
            "Characters": {
                "Frodo": {"Traits": ["Brave", "Short"], "Item": "Ring"}
            }
        }

        result_binder = summarize_binder(binder, agent)

        assert "Characters" in result_binder
        assert "Frodo" in result_binder["Characters"]
        assert "Summary" in result_binder["Characters"]["Frodo"]
        assert (
            result_binder["Characters"]["Frodo"]["Summary"] == "A brave hobbit."
        )
        assert "Traits" in result_binder["Characters"]["Frodo"]
