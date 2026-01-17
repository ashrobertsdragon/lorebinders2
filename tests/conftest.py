import json
from typing import Any, Callable
from pydantic_ai.models.function import FunctionModel
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, TextPart, SystemPromptPart

def create_mock_model(response_data: Any) -> tuple[FunctionModel, list[ModelMessage]]:
    """Create a mock model that returns the given response data.

    Returns:
        A tuple of (model, captured_messages_list).
        The list will be populated when the model is called.
    """
    captured_messages = []

    async def mock_call(messages: list[ModelMessage], info) -> ModelResponse:
        nonlocal captured_messages
        captured_messages.extend(messages)
        return ModelResponse(parts=[TextPart(content=json.dumps(response_data))])

    return FunctionModel(mock_call), captured_messages

def get_system_prompt(messages: list[ModelMessage]) -> str:
    """Extract the system prompt from captured messages."""
    for msg in messages:
        if isinstance(msg, ModelRequest):
            for part in msg.parts:
                if isinstance(part, SystemPromptPart):
                    return part.content
    return ""
