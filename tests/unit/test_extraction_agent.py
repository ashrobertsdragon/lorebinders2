from lorebinders.agent import run_agent, create_extraction_agent
from lorebinders.models import ExtractionConfig, NarratorConfig
from tests.conftest import create_mock_model, get_system_prompt

def test_extraction_agent_run_sync_and_prompt():
    """Test run_sync execution and system prompt generation using PydanticAI."""

    mock_model, captured_messages = create_mock_model({"response": ["Hero", "Villain"]})


    agent = create_extraction_agent()

    with agent.override(model=mock_model):
        config = ExtractionConfig(
            target_category="Characters",
            description="Main characters",
            narrator=NarratorConfig(is_3rd_person=True)
        )
        text = "The Hero fought the Villain."

        result = run_agent(agent, text, config)

        assert result == ["Hero", "Villain"]


    system_prompt_content = get_system_prompt(captured_messages)

    assert system_prompt_content != ""


    assert "Variable: target_category" not in system_prompt_content
    assert "Characters" in system_prompt_content
    assert "Category Description: Main characters" in system_prompt_content
    assert "The text is in 3rd person" in system_prompt_content
