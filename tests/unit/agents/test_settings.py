from lorebinders.agent.settings import settings_config


def test_settings_config_openai() -> None:
    settings = settings_config("openai")

    assert settings["openai_reasoning_effort"] == "low"


def test_settings_config_anthropic() -> None:
    settings = settings_config("anthropic")

    assert settings["anthropic_thinking"] == {"type": "disabled"}


def test_settings_config_google() -> None:
    for provider in ["google-gla", "google-vertex"]:
        settings = settings_config(provider)

        assert settings["google_thinking_config"] == {"include_thoughts": False}


def test_settings_config_groq() -> None:
    settings = settings_config("groq")

    assert settings["groq_reasoning_format"] == "hidden"


def test_settings_config_openrouter() -> None:
    settings = settings_config("openrouter")

    assert settings["openrouter_reasoning"] == {"effort": "low"}


def test_settings_config_unknown_fallback() -> None:
    settings = settings_config("mistral")

    assert settings == {}
