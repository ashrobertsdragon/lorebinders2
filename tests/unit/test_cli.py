from pathlib import Path

from typer.testing import CliRunner

from lorebinders.cli import cli

runner = CliRunner()


def test_cli_help() -> None:
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Usage" in result.stdout


def test_cli_requires_book_path() -> None:
    result = runner.invoke(cli, ["--author", "Test", "--title", "Test"])
    assert result.exit_code != 0


def test_cli_requires_author() -> None:
    result = runner.invoke(cli, ["nonexistent.epub", "--title", "Test"])
    assert result.exit_code != 0


def test_cli_requires_title() -> None:
    result = runner.invoke(cli, ["nonexistent.epub", "--author", "Test"])
    assert result.exit_code != 0


def test_cli_file_not_found() -> None:
    result = runner.invoke(
        cli,
        ["nonexistent.epub", "--author", "Test Author", "--title", "Test Book"],
    )
    assert result.exit_code != 0
    assert "Invalid value for 'BOOK_PATH'" in result.output


def test_cli_accepts_expected_arguments(tmp_path: Path) -> None:
    book_path = tmp_path / "book.epub"
    book_path.write_text("content")

    result = runner.invoke(
        cli,
        [
            str(book_path),
            "--author",
            "Jane Doe",
            "--title",
            "My Book",
            "--help",
        ],
    )
    assert "Usage" in result.output
