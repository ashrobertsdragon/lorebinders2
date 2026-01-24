import json
from typing import Any

from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    SystemPromptPart,
    TextPart,
)
from pydantic_ai.models.function import FunctionModel


def create_mock_model(
    response_data: Any,
    model_name: str | None = None,
) -> tuple[FunctionModel, list[ModelMessage]]:
    captured_messages: list[ModelMessage] = []

    def _serialize(data: Any) -> Any:
        if hasattr(data, "model_dump"):
            return data.model_dump()
        if isinstance(data, list):
            return [_serialize(item) for item in data]
        if isinstance(data, dict):
            return {k: _serialize(v) for k, v in data.items()}
        return data

    def mock_call(messages: list[ModelMessage], info: object) -> ModelResponse:
        nonlocal captured_messages
        captured_messages.extend(messages)
        return ModelResponse(
            parts=[TextPart(content=json.dumps(_serialize(response_data)))]
        )

    return FunctionModel(mock_call, model_name=model_name), captured_messages


def get_system_prompt(messages: list[ModelMessage]) -> str:
    for msg in messages:
        if isinstance(msg, ModelRequest):
            for part in msg.parts:
                if isinstance(part, SystemPromptPart):
                    return part.content
    return ""
