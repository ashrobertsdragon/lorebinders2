from lorebinders.agent import run_agent, analysis_agent
from lorebinders.models import AnalysisConfig, AnalysisResult, TraitValue
from tests.conftest import create_mock_model, get_system_prompt

def test_analysis_agent_run_sync_and_prompt():
    """Test run_sync execution and system prompt generation using PydanticAI."""

    expected_result_dict = {
        "entity_name": "Gandalf",
        "category": "Character",
        "traits": [
            {"trait": "Role", "value": "Wizard", "evidence": "Uses magic"},
            {"trait": "Origin", "value": "Maiar", "evidence": "From Valinor"}
        ]
    }

    expected_result_obj = AnalysisResult(
        entity_name="Gandalf",
        category="Character",
        traits=[
             TraitValue(trait="Role", value="Wizard", evidence="Uses magic"),
             TraitValue(trait="Origin", value="Maiar", evidence="From Valinor")
        ]
    )

    mock_model, captured_messages = create_mock_model(expected_result_dict)

    with analysis_agent.override(model=mock_model):
        config = AnalysisConfig(
            target_entity="Gandalf",
            category="Character",
            traits=["Role", "Origin"]
        )
        text = "Gandalf the Wizard came from Valinor."

        result = run_agent(analysis_agent, text, config)

        assert result == expected_result_obj

    system_prompt_content = get_system_prompt(captured_messages)

    assert system_prompt_content != ""

    assert "Gandalf" in system_prompt_content
    assert "Character" in system_prompt_content
    assert "Role, Origin" in system_prompt_content
