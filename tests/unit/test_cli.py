from unittest.mock import patch
from typer.testing import CliRunner

from lorebinders.cli import app
from lorebinders.models import Book

runner = CliRunner()


def test_cli_help():
    """Test that the CLI help message exists."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Usage" in result.stdout


def test_cli_input_parsing(tmp_path):
    """Test that the CLI accepts the expected arguments."""
    d = tmp_path / "subdir"
    d.mkdir()
    p = d / "book.epub"
    p.write_text("content")

    with patch("lorebinders.cli.WorkspaceManager") as mock_ws_cls, \
         patch("lorebinders.cli.ingest") as mock_ingest:

        mock_ws = mock_ws_cls.return_value
        mock_ws.ensure_workspace.return_value = d / "workspace"

        mock_ingest.return_value = Book(title="Test", author="Test", chapters=[])

        result = runner.invoke(
            app,
            [
                str(p),
                "--author", "Jane Doe",
                "--title", "My Book",
                "--narrator-name", "John",
                "--is-3rd-person",
                "--trait", "Bravery",
                "--trait", "Intelligence",
                "--category", "Physical",
            ],
        )

        assert result.exit_code == 0
