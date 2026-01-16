import json
import pytest
from pydantic_ai.models.function import FunctionModel
from pydantic_ai.messages import ModelResponse, TextPart
from lorebinders.refinement.manager import refine_binder
from lorebinders.agents.summarization import summarization_agent

def test_refinement_manager_integration():
    """Test refine_binder using real components."""

    expected_summary = "A legendary wizard."
    expected_result_dict = {
        "entity_name": "Gandalf",
        "summary": expected_summary
    }

    async def mock_model_call(messages, info) -> ModelResponse:
        return ModelResponse(parts=[TextPart(content=json.dumps(expected_result_dict))])

    with summarization_agent.override(model=FunctionModel(mock_model_call)):
        raw_binder = {
            "Characters": {
                "Captain Gandalf": {"Traits": ["Tall"], "Eyes": "Blue"},
                "Gandalf": {"Traits": ["Wizard"], "Hair": "Grey"}
            },
            "Settings": {
                "The Shire (Exterior)": {"Climate": "Mild"}
            }
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
