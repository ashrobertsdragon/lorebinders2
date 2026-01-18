import json
from pathlib import Path
from collections.abc import Callable

import pytest
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart
from pydantic_ai.models.function import FunctionModel

from lorebinders import models
from lorebinders.agent import (
    AgentDeps,
    create_analysis_agent,
    create_extraction_agent,
)
from lorebinders.app import create_analyzer, create_extractor
from lorebinders.settings import Settings


def mock_prompt_loader(filename: str) -> str:
    return f"Mock content for {filename}"


@pytest.fixture
def test_deps():
    return AgentDeps(settings=Settings(), prompt_loader=mock_prompt_loader)


@pytest.fixture
def test_config(tmp_path):
    return models.RunConfiguration(
        book_path=tmp_path / "book.txt",
        author_name="Test Author",
        book_title="Test Book",
        narrator_config=models.NarratorConfig(),
    )


def test_create_extractor(test_config, test_deps):
    """Test create_extractor logic with FunctionModel."""
    async def test_extract(messages: list[ModelMessage], info: object) -> ModelResponse:

        found = False
        for msg in messages:
            for part in msg.parts:
                if "Some chapter content" in str(part.content):
                    found = True
                    break
        assert found, f"User prompt not found in messages: {messages}"

        return ModelResponse(
             parts=[TextPart(content=json.dumps({"response": ["Alice", "Bob"]}))]
        )

    agent = create_extraction_agent(test_deps.settings)

    with agent.override(model=FunctionModel(test_extract)):

        extractor = create_extractor(test_config, agent, test_deps, categories=["Characters"])

        chapter = models.Chapter(number=1, title="Ch1", content="Some chapter content")
        results = extractor(chapter)

        assert results == {"Characters": ["Alice", "Bob"]}


def test_create_analyzer(test_config, test_deps):
    """Test create_analyzer logic with FunctionModel."""
    async def test_analyze(messages: list[ModelMessage], info: object) -> ModelResponse:

        found = False
        for msg in messages:
            for part in msg.parts:
                if "Role" in str(part.content) and "Alice" in str(part.content):
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
        return ModelResponse(parts=[TextPart(content=json.dumps(result))])

    agent = create_analysis_agent(test_deps.settings)

    with agent.override(model=FunctionModel(test_analyze)):

        traits_map = {"Characters": ["Role"]}
        analyzer = create_analyzer(test_config, agent, test_deps, effective_traits=traits_map)

        chapter = models.Chapter(number=1, title="Ch1", content="Context")

        profile = analyzer("Alice", "Characters", chapter)

        assert profile.name == "Alice"
        assert profile.category == "Characters"
        assert profile.traits["Role"] == "Protagonist"
