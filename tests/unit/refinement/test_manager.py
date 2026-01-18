import json

import pytest
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart
from pydantic_ai.models.function import FunctionModel

from lorebinders.agent import create_summarization_agent
from lorebinders.refinement import refine_binder

@pytest.mark.skip(reason="Requires Phase 6 testing overhaul for agent injection")
def test_refinement_manager_integration() -> None:
    expected_summary = "A legendary wizard."
    expected_result_dict = {"entity_name": "Gandalf", "summary": expected_summary}

    async def mock_model_call(
        messages: list[ModelMessage], info: object
    ) -> ModelResponse:
        return ModelResponse(parts=[TextPart(content=json.dumps(expected_result_dict))])

    agent = create_summarization_agent()
    with agent.override(model=FunctionModel(mock_model_call)):
        raw_binder = {
            "Characters": {
                "Captain Gandalf": {"Traits": ["Tall"], "Eyes": "Blue"},
                "Gandalf": {"Traits": ["Wizard"], "Hair": "Grey"},
            },
            "Settings": {"The Shire (Exterior)": {"Climate": "Mild"}},
        }

        result = refine_binder(raw_binder, narrator_name=None)

        assert "Gandalf" in result["Characters"]
        assert "Captain Gandalf" not in result["Characters"]

        assert "The Shire" in result["Settings"]
        assert "The Shire (Exterior)" not in result["Settings"]

        gandalf = result["Characters"]["Gandalf"]
        assert "Tall" in gandalf["Traits"]
        assert "Wizard" in gandalf["Traits"]

        assert gandalf["Summary"] == expected_summary
