import json
import pytest
from pydantic_ai.models.function import FunctionModel
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart

from lorebinders.agents.extraction import run_extraction, extraction_agent
from lorebinders.agents.analysis import run_analysis, analysis_agent
from lorebinders.agents.models import (
    ExtractionConfig,
    AnalysisConfig,
    NarratorConfig,
    AnalysisResult,
    TraitValue
)

def test_agents_flow():
    """Test the full flow of extraction and analysis with PydanticAI overrides."""


    async def mock_extract_call(messages: list[ModelMessage], info) -> ModelResponse:
        return ModelResponse(parts=[TextPart(content=json.dumps({"response": ["Sherlock Holmes", "Dr. Watson"]}))])


    async def mock_analyze_call(messages: list[ModelMessage], info) -> ModelResponse:


        result = {
            "entity_name": "Sherlock Holmes",
            "category": "Character",
            "traits": [
                {"trait": "Role", "value": "Detective", "evidence": "The world's only consulting detective"}
            ]
        }
        return ModelResponse(parts=[TextPart(content=json.dumps(result))])

    with extraction_agent.override(model=FunctionModel(mock_extract_call)), \
         analysis_agent.override(model=FunctionModel(mock_analyze_call)):

        text_chunk = (
            "Sherlock Holmes sat in his chair. Dr. Watson looked at him. "
            "The world's only consulting detective was thinking."
        )

        ext_config = ExtractionConfig(
            target_category="Character",
            narrator=NarratorConfig(is_3rd_person=True)
        )
        entities = run_extraction(text_chunk, ext_config)

        assert "Sherlock Holmes" in entities
        assert "Dr. Watson" in entities

        analysis_config = AnalysisConfig(
            target_entity="Sherlock Holmes",
            category="Character",
            traits=["Role"]
        )
        result = run_analysis(text_chunk, analysis_config)

        assert result.entity_name == "Sherlock Holmes"
        assert result.traits[0].value == "Detective"
