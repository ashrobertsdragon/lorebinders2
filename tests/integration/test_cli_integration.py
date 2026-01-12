from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from lorebinders.cli import app
from lorebinders.core.models import Book, Chapter

runner = CliRunner()


@pytest.fixture
def mock_env():
    """Mock the environment variables required by dependencies."""
    with patch.dict("os.environ", {"OPENAI_MODEL": "gpt-4o"}):
        yield


@pytest.fixture
def mock_ingester(mock_env):
    """Mock the EbookIngester class."""
    # We need to ensure local import or patch before import
    # But since ebook2text imports at top level, we might crash before patching if we are not careful.
    # Luckily, pytest fixtures run before the test function, but we need to ensure the module isn't already loaded
    # OR that the environment is set before file import.
    # Since we are using patch("..."), it mocks the class. But the module import happens when looking up the target.
    # The error happened during `patch` target resolution which involves importing the module.
    # So we must set the env var BEFORE the patch tries to resolve the name.

    with patch.dict("os.environ", {"OPENAI_MODEL": "gpt-4o"}):
         with patch("lorebinders.ingestion.ingester.EbookIngester") as mock:
            instance = mock.return_value
            instance.ingest.return_value = Book(
                title="Test Book",
                author="Test Author",
                chapters=[Chapter(number=1, title="Ch1", content="Content")],
            )
            yield instance


@pytest.fixture
def mock_workspace():
    """Mock the WorkspaceManager class."""
    with patch("lorebinders.ingestion.workspace.WorkspaceManager") as mock:
        instance = mock.return_value
        instance.ensure_workspace.return_value = Path("/tmp/work/Test_Author/Test_Book")
        yield instance


def test_cli_ingest_success(mock_ingester, mock_workspace, tmp_path):
    """Test successful ingestion flow via CLI."""
    # Create a dummy file to pass the "exists=True" check in Typer
    book_path = tmp_path / "test.epub"
    book_path.touch()

    result = runner.invoke(
        app,
        [str(book_path), "--author", "Test Author", "--title", "Test Book"],
    )

    assert result.exit_code == 0
    assert "Ingestion Complete!" in result.output
    assert "Imported 1 chapters" in result.output

    # Verify WorkspaceManager calls
    mock_workspace.ensure_workspace.assert_called_once_with(
        author="Test Author", title="Test Book"
    )

    # Verify EbookIngester calls
    mock_ingester.ingest.assert_called_once()
    # Check arguments passed to ingest
    call_args = mock_ingester.ingest.call_args
    assert call_args.kwargs["source"] == book_path
    assert call_args.kwargs["output_dir"] == Path("/tmp/work/Test_Author/Test_Book")


def test_cli_file_not_found():
    """Test CLI behavior when input file does not exist."""
    result = runner.invoke(
        app,
        ["nonexistent.epub", "--author", "Test Author", "--title", "Test Book"],
    )

    assert result.exit_code != 0
    # Typer automatically handles file existence check
    assert "Invalid value for 'BOOK_PATH'" in result.output
    # The exact message depends on click/typer version but usually prints to stderr which is in output
