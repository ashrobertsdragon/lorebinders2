import json

import pytest
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart
from pydantic_ai.models.function import FunctionModel

from lorebinders.agent import (
    create_analysis_agent,
    create_extraction_agent,
    run_agent,
)
from lorebinders.models import AnalysisConfig, ExtractionConfig, NarratorConfig

@pytest.mark.skip(reason="Requires Phase 6 testing overhaul for output type alignment")
def test_agents_flow() -> None:
    async def mock_extract_call(
        messages: list[ModelMessage], info: object
    ) -> ModelResponse:
        return ModelResponse(
            parts=[TextPart(content=json.dumps(["Sherlock Holmes", "Dr. Watson"]))]
        )

    async def mock_analyze_call(
        messages: list[ModelMessage], info: object
    ) -> ModelResponse:
        result = {
            "entity_name": "Sherlock Holmes",
            "category": "Character",
            "traits": [
                {
                    "trait": "Role",
                    "value": "Detective",
                    "evidence": "The world's only consulting detective",
                }
            ],
        }
        return ModelResponse(parts=[TextPart(content=json.dumps(result))])

    extraction_agent = create_extraction_agent()
    analysis_agent = create_analysis_agent()

    with (
        extraction_agent.override(model=FunctionModel(mock_extract_call)),
        analysis_agent.override(model=FunctionModel(mock_analyze_call)),
    ):
        text_chunk = (
            "Sherlock Holmes sat in his chair. Dr. Watson looked at him. "
            "The world's only consulting detective was thinking."
        )

        ext_config = ExtractionConfig(
            target_category="Character",
            narrator=NarratorConfig(is_3rd_person=True),
        )
        entities = run_agent(extraction_agent, text_chunk, ext_config)

        assert "Sherlock Holmes" in entities
        assert "Dr. Watson" in entities

        analysis_config = AnalysisConfig(
            target_entity="Sherlock Holmes",
            category="Character",
            traits=["Role"],
        )
        result = run_agent(analysis_agent, text_chunk, analysis_config)

        assert result.entity_name == "Sherlock Holmes"
        assert result.traits[0].value == "Detective"
