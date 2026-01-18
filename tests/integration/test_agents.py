import json

import pytest
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart
from pydantic_ai.models.function import FunctionModel

from lorebinders.agent import (
    AgentDeps,
    create_analysis_agent,
    create_extraction_agent,
    run_agent,
)
from lorebinders.models import AnalysisConfig, ExtractionConfig, NarratorConfig
from lorebinders.settings import Settings



def mock_prompt_loader(filename: str) -> str:
    return f"Mock content for {filename}"


def test_agents_flow() -> None:
    async def mock_extract_call(
        messages: list[ModelMessage], info: object
    ) -> ModelResponse:


        return ModelResponse(
            parts=[TextPart(content=json.dumps({"response": ["Sherlock Holmes", "Dr. Watson"]}))]
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
            "confidence_score": 0.95,
        }
        return ModelResponse(parts=[TextPart(content=json.dumps(result))])


    settings = Settings()
    deps = AgentDeps(settings=settings, prompt_loader=mock_prompt_loader)

    extraction_agent = create_extraction_agent(settings)
    analysis_agent = create_analysis_agent(settings)

    with (
        extraction_agent.override(model=FunctionModel(mock_extract_call)),
        analysis_agent.override(model=FunctionModel(mock_analyze_call)),
    ):
        text_chunk = (
            "Sherlock Holmes sat in his chair. Dr. Watson looked at him. "
            "The world's only consulting detective was thinking."
        )
















        from lorebinders.agent import build_extraction_user_prompt, build_analysis_user_prompt

        ext_config = ExtractionConfig(
            target_category="Character",
            narrator=NarratorConfig(is_3rd_person=True),
        )

        extraction_prompt = build_extraction_user_prompt(
            text_chunk,
            ext_config.target_category,
            narrator=ext_config.narrator
        )

        entities = run_agent(extraction_agent, extraction_prompt, deps)

        assert "Sherlock Holmes" in entities
        assert "Dr. Watson" in entities

        analysis_config = AnalysisConfig(
            target_entity="Sherlock Holmes",
            category="Character",
            traits=["Role"],
        )

        analysis_prompt = build_analysis_user_prompt(
            text_chunk,
            analysis_config.target_entity,
            analysis_config.category,
            analysis_config.traits
        )

        result = run_agent(analysis_agent, analysis_prompt, deps)

        assert result.entity_name == "Sherlock Holmes"
        assert result.traits[0].value == "Detective"
