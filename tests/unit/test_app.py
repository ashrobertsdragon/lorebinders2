import json

import pytest
from pydantic_ai.messages import (
    ModelMessage,
    ModelResponse,
    TextPart,
    UserPromptPart,
)
from pydantic_ai.models.function import FunctionModel

from lorebinders import models
from lorebinders.agent import (
    create_analysis_agent,
    create_extraction_agent,
)
from lorebinders.app import create_analyzer, create_extractor
from lorebinders.settings import Settings


def mock_prompt_loader(filename: str) -> str:
    return f"Mock content for {filename}"


@pytest.fixture
def test_deps():
    return models.AgentDeps(
        settings=Settings(), prompt_loader=mock_prompt_loader
    )


@pytest.fixture
def test_config(tmp_path):
    return models.RunConfiguration(
        book_path=tmp_path / "book.txt",
        author_name="Test Author",
        book_title="Test Book",
        narrator_config=models.NarratorConfig(),
    )


def test_create_extractor(test_config, test_deps) -> None:
    def test_extract(
        messages: list[ModelMessage], info: object
    ) -> ModelResponse:
        found = False
        for msg in messages:
            for part in msg.parts:
                if isinstance(
                    part, UserPromptPart
                ) and "Some chapter content" in str(part.content):
                    found = True
                    break
        assert found, f"User prompt not found in messages: {messages}"

        return ModelResponse(
            parts=[
                TextPart(
                    content=json.dumps(
                        {
                            "results": [
                                {
                                    "category": "Characters",
                                    "entities": ["Alice", "Bob"],
                                }
                            ]
                        }
                    )
                )
            ]
        )

    agent = create_extraction_agent(test_deps.settings)

    with agent.override(model=FunctionModel(test_extract)):
        extractor = create_extractor(
            test_config, agent, test_deps, categories=["Characters"]
        )

        chapter = models.Chapter(
            number=1, title="Ch1", content="Some chapter content"
        )
        results = extractor(chapter)

        assert results == {"Characters": ["Alice", "Bob"]}


def test_create_analyzer(test_deps) -> None:
    """Test create_analyzer logic with FunctionModel."""

    def test_analyze(
        messages: list[ModelMessage], info: object
    ) -> ModelResponse:
        found = False
        for msg in messages:
            for part in msg.parts:
                if isinstance(part, UserPromptPart):
                    if "Role" in str(part.content) and "Alice" in str(
                        part.content
                    ):
                        found = True
                        break
        assert found, f"User prompt content not found in messages: {messages}"

        result = {
            "entity_name": "Alice",
            "category": "Characters",
            "traits": [
                {"trait": "Role", "value": "Protagonist", "evidence": "text"},
            ],
        }
        return ModelResponse(
            parts=[TextPart(content=json.dumps({"response": [result]}))]
        )

    agent = create_analysis_agent(test_deps.settings)

    with agent.override(model=FunctionModel(test_analyze)):
        traits_map = {"Characters": ["Role"]}
        analyzer = create_analyzer(
            agent, test_deps, effective_traits=traits_map
        )

        chapter = models.Chapter(number=1, title="Ch1", content="Context")

        entities: list[models.EntityTarget] = [
            models.EntityTarget(name="Alice", category="Characters")
        ]
        profiles = analyzer(entities, chapter)

        assert len(profiles) == 1
        profile = profiles[0]
        assert profile.name == "Alice"
        assert profile.category == "Characters"
        assert profile.traits["Role"] == "Protagonist"
