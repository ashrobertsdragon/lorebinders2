import json
import os
from typing import Any

import pytest
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, SystemPromptPart, TextPart
from pydantic_ai.models.function import FunctionModel


@pytest.fixture(autouse=True)
def set_model_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EXTRACTION_MODEL", "openai:gpt-4o-nano")
    monkeypatch.setenv("ANALYSIS_MODEL", "openai:gpt-4o-mini")
    monkeypatch.setenv("SUMMARIZATION_MODEL", "openai:gpt-4o-nano")


def create_mock_model(response_data: Any) -> tuple[FunctionModel, list[ModelMessage]]:
    captured_messages: list[ModelMessage] = []

    async def mock_call(
        messages: list[ModelMessage], info: object
    ) -> ModelResponse:
        nonlocal captured_messages
        captured_messages.extend(messages)
        return ModelResponse(parts=[TextPart(content=json.dumps(response_data))])

    return FunctionModel(mock_call), captured_messages


def get_system_prompt(messages: list[ModelMessage]) -> str:
    for msg in messages:
        if isinstance(msg, ModelRequest):
            for part in msg.parts:
                if isinstance(part, SystemPromptPart):
                    return part.content
    return ""
