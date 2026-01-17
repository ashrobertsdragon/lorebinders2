import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from lorebinders.cli.__cli__ import cli

runner = CliRunner()


@pytest.mark.skip(reason="Requires LLM model env vars to be configured")
def test_e2e_ingestion_flow(tmp_path: Path) -> None:
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

    cleanup_target = Path.cwd() / "work" / "E2E_Test_Author"
    try:
        result = runner.invoke(
            cli,
            [
                str(source_file),
                "--author",
                "E2E Test Author",
                "--title",
                "E2E Book",
                "--category",
                "Characters",
            ],
        )

        assert result.exit_code == 0

    finally:
        if cleanup_target.exists():
            shutil.rmtree(cleanup_target)
