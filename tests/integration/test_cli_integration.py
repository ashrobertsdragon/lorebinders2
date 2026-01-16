from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from lorebinders.cli import app
from lorebinders.core.models import Book, Chapter

runner = CliRunner()


@pytest.fixture
def mock_ingester():
    """Mock the ingest function."""
    with patch("lorebinders.cli.ingest") as mock:
        mock.return_value = Book(
            title="Test Book",
            author="Test Author",
            chapters=[Chapter(number=1, title="Ch1", content="Content")],
        )
        yield mock


@pytest.fixture
def mock_workspace():
    """Mock the WorkspaceManager class."""
    workspace_path = Path("work/Test_Author/Test_Book")
    with patch("lorebinders.cli.WorkspaceManager") as mock:
        instance = mock.return_value
        instance.ensure_workspace.return_value = workspace_path
        yield instance


def test_cli_ingest_success(mock_ingester, mock_workspace, tmp_path):
    """Test successful ingestion flow via CLI."""
    book_path = tmp_path / "test.epub"
    book_path.touch()

    result = runner.invoke(
        app,
        [str(book_path), "--author", "Test Author", "--title", "Test Book"],
    )

    assert result.exit_code == 0
    assert "Build Complete!" in result.output

    mock_workspace.ensure_workspace.assert_called_once_with(
        author="Test Author", title="Test Book"
    )

    mock_ingester.assert_called_once()
    call_args = mock_ingester.call_args
    assert call_args.args[0] == book_path
    assert call_args.args[1] == mock_workspace.ensure_workspace.return_value


def test_cli_file_not_found():
    """Test CLI behavior when input file does not exist."""
    result = runner.invoke(
        app,
        ["nonexistent.epub", "--author", "Test Author", "--title", "Test Book"],
    )

    assert result.exit_code != 0
    assert "Invalid value for 'BOOK_PATH'" in result.output
