from lorebinders.agent import (
    AgentDeps,
    build_extraction_user_prompt,
    create_extraction_agent,
    run_agent,
)
from lorebinders.models import NarratorConfig
from lorebinders.settings import Settings
from tests.conftest import create_mock_model, get_system_prompt

def test_extraction_agent_run_sync_and_prompt():
    """Test run_sync execution and system prompt generation using PydanticAI."""

    mock_model, captured_messages = create_mock_model({"response": ["Hero", "Villain"]})


    agent = create_extraction_agent()
    deps = AgentDeps(
        settings=Settings(),
        prompt_loader=lambda x: "Mock content for extraction.txt",
    )

    with agent.override(model=mock_model):
        prompt = build_extraction_user_prompt(
            text="The Hero fought the Villain.",
            target_category="Characters",
            description="Main characters",
            narrator=NarratorConfig(is_3rd_person=True),
        )

        result = run_agent(agent, prompt, deps)

        assert result == ["Hero", "Villain"]


    system_prompt_content = get_system_prompt(captured_messages)

    assert system_prompt_content != ""


    assert "Mock content" in system_prompt_content
