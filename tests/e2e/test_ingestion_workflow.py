import os
import shutil
from pathlib import Path
from typer.testing import CliRunner
from lorebinders.cli import app

runner = CliRunner()

def test_e2e_ingestion_flow(tmp_path):
    """
    E2E Test for the Ingestion Workflow via CLI.

    Steps:
    1. Create a dummy text file masking as an ebook.
       (Since we are using ebook2text which might fail on fake binary files if they are not valid,
        we will use a text file or mock the actual conversion if we wanted to be strictly unit,
        but for E2E we want real behavior.
        However, ebook2text might essentially just read text from .txt files or try to parse epub.
        Wait, requirement 1 says "Supported Formats: .epub and .txt".
        Let's use a .txt file for simplicity and reliability in the test environment without needing valid zip structure of epub).

    2. Run CLI command.
    3. Verify workspace creation.
    4. Verify content extraction (if possible to check result/logs).
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

    try:
        result = runner.invoke(
            app,
            [
                str(source_file),
                "--author", "E2E Test Author",
                "--title", "E2E Book",
            ],
        )


        print(result.output)
        assert result.exit_code == 0
        assert "Ingestion Complete!" in result.output



        cwd = Path.cwd()
        expected_workspace = cwd / "work" / "E2E_Test_Author" / "E2E_Book"

        assert expected_workspace.exists()
        assert expected_workspace.is_dir()

    finally:

        cwd = Path.cwd()
        cleanup_target = cwd / "work" / "E2E_Test_Author"
        if cleanup_target.exists():
            shutil.rmtree(cleanup_target)
