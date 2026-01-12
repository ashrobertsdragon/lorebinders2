import os
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner

# Mock environment variables BEFORE any imports that might need them
# This is crucial because lorebinders.cli imports modules that check env vars at top level
with patch.dict(os.environ, {"OPENAI_MODEL": "gpt-4o", "OPENAI_API_KEY": "dummy"}):
    from lorebinders.cli import app


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

    # We must patch the dependencies that are called by the CLI
    # Since imports are top-level in cli.py, we patch where they are used (lorebinders.cli)
    with patch("lorebinders.cli.WorkspaceManager") as mock_ws_cls, \
         patch("lorebinders.cli.EbookIngester") as mock_ingest_cls:

        # Setup mocks
        mock_ws = mock_ws_cls.return_value
        mock_ws.ensure_workspace.return_value = d / "workspace"

        mock_ingester = mock_ingest_cls.return_value
        # Mocking the ingest method to return a dummy Book object
        # We need to import Book/Chapter here or mock the return object structure
        from lorebinders.core.models import Book
        mock_ingester.ingest.return_value = Book(title="Test", author="Test", chapters=[])

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
