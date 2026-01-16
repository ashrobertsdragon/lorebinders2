import json
import pytest
from pydantic_ai.models.function import FunctionModel
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart
from lorebinders.agents.extraction import run_extraction, extraction_agent
from lorebinders.agents.models import ExtractionConfig
from lorebinders.core.models import NarratorConfig

def test_extraction_agent_run_sync_and_prompt():
    """Test run_sync execution and system prompt generation using PydanticAI."""

    captured_messages = []

    async def mock_model_call(messages: list[ModelMessage], info) -> ModelResponse:
        nonlocal captured_messages
        captured_messages = messages
        return ModelResponse(parts=[TextPart(content=json.dumps({"response": ["Hero", "Villain"]}))])

    with extraction_agent.override(model=FunctionModel(mock_model_call)):
        config = ExtractionConfig(
            target_category="Characters",
            description="Main characters",
            narrator=NarratorConfig(is_3rd_person=True)
        )
        text = "The Hero fought the Villain."

        result = run_extraction(text, config)

        assert result == ["Hero", "Villain"]


    from pydantic_ai.messages import ModelRequest, SystemPromptPart

    system_prompt_content = ""
    for msg in captured_messages:
        if isinstance(msg, ModelRequest):
            for part in msg.parts:
                if isinstance(part, SystemPromptPart):
                    system_prompt_content = part.content
                    break

    assert system_prompt_content != ""


    assert "Variable: target_category" not in system_prompt_content
    assert "Characters" in system_prompt_content
    assert "Category Description: Main characters" in system_prompt_content
    assert "The text is in 3rd person" in system_prompt_content
