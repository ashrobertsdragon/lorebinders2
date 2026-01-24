from pathlib import Path
from unittest.mock import patch

import pytest

from lorebinders.models import Book
from lorebinders.refinement.conversion import _split_chapters, ingest


@pytest.fixture
def mock_ebook2text():
    with patch("lorebinders.refinement.conversion.ebook2text") as mock:
        yield mock


def test_split_chapters_with_asterisks() -> None:
    """Test splitting text by '***' delimiter."""
    text = "Chapter 1\nSome text.\n***\nChapter 2\nMore text."
    chapters = _split_chapters(text)
    assert len(chapters) == 2
    assert chapters[0].content.strip() == "Chapter 1\nSome text."
    assert chapters[1].content.strip() == "Chapter 2\nMore text."
    assert chapters[0].number == 1
    assert chapters[1].number == 2


def test_split_chapters_with_markdown_headers() -> None:
    """Test splitting text by markdown headers."""
    text = "# Chapter One\nText 1.\n# Chapter Two\nText 2."
    chapters = _split_chapters(text)
    assert len(chapters) == 2
    assert "Text 1." in chapters[0].content
    assert "Text 2." in chapters[1].content


def test_split_chapters_fallback() -> None:
    """Test fallback to single chapter if no delimiters found."""
    text = "Just a short story."
    chapters = _split_chapters(text)
    assert len(chapters) == 1
    assert chapters[0].content == text
    assert chapters[0].title == "Chapter 1"


def test_ingest_flow(mock_ebook2text, tmp_path) -> None:
    """Test the full ingest flow using mocked ebook2text."""
    source_file = tmp_path / "book.epub"
    source_file.touch()
    mock_ebook2text.convert_file.return_value = (
        "Chapter 1\nText.\n***\nChapter 2\nEnd."
    )

    book = ingest(source_file, tmp_path)

    assert isinstance(book, Book)
    assert len(book.chapters) == 2
    assert book.title == "book"

    expected_metadata = {"title": "book", "author": "Unknown"}
    mock_ebook2text.convert_file.assert_called_once_with(
        source_file, expected_metadata, save_file=False
    )


def test_ingest_file_not_found(tmp_path) -> None:
    """Test that FileNotFoundError is raised if file doesn't exist."""
    with pytest.raises(FileNotFoundError):
        ingest(Path("nonexistent.epub"), tmp_path)


def test_empty_chapter_filter() -> None:
    """Test that empty chapters are discarded."""
    text = "Chapter 1\n***\n   \n***\nChapter 2"
    chapters = _split_chapters(text)
    assert len(chapters) == 2
    assert "Chapter 1" in chapters[0].content
    assert "Chapter 2" in chapters[1].content
