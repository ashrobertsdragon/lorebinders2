import json
import pytest
from pydantic_ai.models.function import FunctionModel
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, SystemPromptPart, TextPart

from lorebinders.agents.analysis import run_analysis, analysis_agent
from lorebinders.agents.models import AnalysisConfig, AnalysisResult, TraitValue

def test_analysis_agent_run_sync_and_prompt():
    """Test run_sync execution and system prompt generation using PydanticAI."""

    captured_messages = []

    expected_result_dict = {
        "entity_name": "Gandalf",
        "category": "Character",
        "traits": [
            {"trait": "Role", "value": "Wizard", "evidence": "Uses magic"},
            {"trait": "Origin", "value": "Maiar", "evidence": "From Valinor"}
        ]
    }

    expected_result_obj = AnalysisResult(
        entity_name="Gandalf",
        category="Character",
        traits=[
             TraitValue(trait="Role", value="Wizard", evidence="Uses magic"),
             TraitValue(trait="Origin", value="Maiar", evidence="From Valinor")
        ]
    )

    async def mock_model_call(messages: list[ModelMessage], info) -> ModelResponse:
        nonlocal captured_messages
        captured_messages = messages
        return ModelResponse(parts=[TextPart(content=json.dumps(expected_result_dict))])

    with analysis_agent.override(model=FunctionModel(mock_model_call)):
        config = AnalysisConfig(
            target_entity="Gandalf",
            category="Character",
            traits=["Role", "Origin"]
        )
        text = "Gandalf the Wizard came from Valinor."

        result = run_analysis(text, config)

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
    assert "Role, Origin" in system_prompt_content
