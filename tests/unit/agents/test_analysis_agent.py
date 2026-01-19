from lorebinders.agent import (
    AgentDeps,
    build_analysis_user_prompt,
    create_analysis_agent,
    run_agent,
)
from lorebinders.models import AnalysisResult, EntityTarget, TraitValue
from lorebinders.settings import Settings
from tests.conftest import create_mock_model, get_system_prompt


def test_analysis_agent_run_sync_and_prompt() -> None:
    """Test run_sync execution and system prompt generation using PydanticAI."""
    expected_result_dict = [
        {
            "entity_name": "Gandalf",
            "category": "Character",
            "traits": [
                {"trait": "Role", "value": "Wizard", "evidence": "Uses magic"},
                {
                    "trait": "Origin",
                    "value": "Maiar",
                    "evidence": "From Valinor",
                },
            ],
        }
    ]

    expected_result_obj = AnalysisResult(
        entity_name="Gandalf",
        category="Character",
        traits=[
            TraitValue(trait="Role", value="Wizard", evidence="Uses magic"),
            TraitValue(trait="Origin", value="Maiar", evidence="From Valinor"),
        ],
    )

    mock_model, captured_messages = create_mock_model(
        {"response": expected_result_dict}
    )

    agent = create_analysis_agent()
    deps = AgentDeps(
        settings=Settings(),
        prompt_loader=lambda x: "Mock content for analysis.txt",
    )

    with agent.override(model=mock_model):
        entities: list[EntityTarget] = [
            EntityTarget(
                name="Gandalf",
                category="Character",
                traits=["Role", "Origin"],
            )
        ]

        prompt = build_analysis_user_prompt(
            context_text="Gandalf the Wizard came from Valinor.",
            entities=entities,
        )

        result = run_agent(agent, prompt, deps)

        assert result == [expected_result_obj]

    system_prompt_content = get_system_prompt(captured_messages)

    assert system_prompt_content != ""

    for msg in captured_messages:
        if hasattr(msg, "parts"):
            for part in msg.parts:
                if hasattr(part, "content") and not isinstance(
                    part, type(get_system_prompt)
                ):
                    pass

    assert "Mock content for analysis.txt" in system_prompt_content

    found_user_text = False
    for msg in captured_messages:
        if hasattr(msg, "parts"):
            for part in msg.parts:
                if getattr(part, "part_kind", "") == "user-prompt" or (
                    hasattr(part, "content") and "Gandalf" in str(part.content)
                ):
                    found_user_text = True

    assert found_user_text, "Dynamic content not found in messages"
