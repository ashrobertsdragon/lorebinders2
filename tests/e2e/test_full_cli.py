import shutil
from pathlib import Path
from unittest.mock import patch

from pydantic_ai import Agent
from typer.testing import CliRunner

from lorebinders.cli.__cli__ import cli
from lorebinders.models import (
    AgentDeps,
    AnalysisResult,
    ExtractionResult,
    SummarizerResult,
    TraitValue,
)
from tests.utils import create_mock_model

runner = CliRunner()


def test_e2e_ingestion_flow(
    tmp_path: Path,
) -> None:
    book_content = (
        "Project Genesis\n"
        "***\n"
        "Chapter 1\n"
        "It was a dark and stormy night.\n"
        "***\n"
        "Chapter 2\n"
        "The sun came out."
    )

    source_file = tmp_path / "genesis.txt"
    source_file.write_text(book_content)

    cleanup_target = Path.cwd() / "work" / "Test_Author"

    summarizer_result = SummarizerResult(
        entity_name="Night", summary="A dark and stormy night."
    )
    summarizer_model, _ = create_mock_model(
        summarizer_result,
        model_name="test:mock_summarizer",
    )
    mock_summarizer_agent: Agent[AgentDeps, SummarizerResult] = Agent(
        summarizer_model,
        deps_type=AgentDeps,
        output_type=SummarizerResult,
    )

    extractor_model, _ = create_mock_model(
        {"results": [{"category": "Locations", "entities": ["Night"]}]},
        model_name="test:mock_extractor",
    )
    mock_extractor_agent: Agent[AgentDeps, ExtractionResult] = Agent(
        extractor_model,
        deps_type=AgentDeps,
        output_type=ExtractionResult,
    )

    analysis_result = AnalysisResult(
        entity_name="Night",
        category="Locations",
        traits=[
            TraitValue(
                trait="Key Features",
                value="Dark and stormy",
                evidence="It was a dark and stormy night.",
            ),
            TraitValue(
                trait="Relative Location",
                value="Unknown",
                evidence="It was a dark and stormy night.",
            ),
            TraitValue(
                trait="Character Familiarity",
                value="Unknown",
                evidence="It was a dark and stormy night.",
            ),
        ],
    )
    analyzer_model, _ = create_mock_model(
        {"response": [analysis_result]},
        model_name="test:mock_analyzer",
    )
    mock_analyzer_agent: Agent[AgentDeps, list[AnalysisResult]] = Agent(
        analyzer_model,
        deps_type=AgentDeps,
        output_type=list[AnalysisResult],
    )

    try:
        with (
            patch(
                "lorebinders.app.create_extraction_agent"
            ) as mock_create_extraction_agent,
            patch(
                "lorebinders.app.create_analysis_agent"
            ) as mock_create_analysis_agent,
            patch(
                "lorebinders.agent.summarization.create_summarization_agent"
            ) as mock_create_summarization_agent,
        ):
            mock_create_extraction_agent.return_value = mock_extractor_agent
            mock_create_analysis_agent.return_value = mock_analyzer_agent
            mock_create_summarization_agent.return_value = mock_summarizer_agent
            result = runner.invoke(
                cli,
                [
                    str(source_file),
                    "--author",
                    "Test Author",
                    "--title",
                    "Project Genesis",
                ],
            )

        assert result.exit_code == 0

    finally:
        if cleanup_target.exists():
            shutil.rmtree(cleanup_target)
