import os
import shutil
import json
from pathlib import Path

from typer.testing import CliRunner
from pydantic_ai.models.test import TestModel

from lorebinders.cli import app
from lorebinders.agents.extraction import extraction_agent
from lorebinders.agents.analysis import analysis_agent

runner = CliRunner()

def test_e2e_ingestion_flow(tmp_path):
    """
    E2E Test for the Ingestion Workflow via CLI.

    Verifies:
    1. Ingestion (ebook2text)
    2. Orchestration (Builder)
    3. Reporting (PDF Generation)

    Uses PydanticAI TestModel to simulate LLM responses without mocks.
    """

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

    extraction_response = json.dumps(["Protagonist", "Antagonist"])

    analysis_response_protagonist = json.dumps({
        "entity_name": "Protagonist",
        "category": "Characters",
        "traits": [
            {"trait": "Role", "value": "Hero", "evidence": "Saves the day"},
            {"trait": "Personality", "value": "Brave", "evidence": "Fights monster"}
        ]
    })

    with extraction_agent.override(model=TestModel()), \
         analysis_agent.override(model=TestModel()):

        try:
            result = runner.invoke(
                app,
                [
                    str(source_file),
                    "--author", "E2E Test Author",
                    "--title", "E2E Book",
                    "--category", "Characters"
                ],
            )

            assert result.exit_code == 0
            assert "Build Complete!" in result.output
            assert "PDF Report generated" in result.output

            cwd = Path.cwd()
            workspace_dir = cwd / "work" / "E2E_Test_Author" / "E2E_Book"
            assert workspace_dir.exists()
            assert workspace_dir.is_dir()

            pdf_path = workspace_dir / "E2E_Book_story_bible.pdf"
            assert pdf_path.exists()
            assert pdf_path.stat().st_size > 0

        finally:

            cwd = Path.cwd()
            cleanup_target = cwd / "work" / "E2E_Test_Author"
            if cleanup_target.exists():
                shutil.rmtree(cleanup_target)
