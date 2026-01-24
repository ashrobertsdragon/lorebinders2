import re
from pathlib import Path

import ebook2text
from dotenv import load_dotenv

from lorebinders.models import Book, Chapter

load_dotenv()


def ingest(source: Path, output_dir: Path) -> Book:
    """Ingest a book from source path and save/return the Book model.

    Args:
        source: Path to the source ebook file.
        output_dir: Directory to save processed files (unused in this step).

    Returns:
        Book: A structured Book model containing chapters.

    Raises:
        FileNotFoundError: If the source file does not exist.
    """
    if not source.exists():
        raise FileNotFoundError(f"File not found: {source}")

    raw_text = _convert_to_text(source)
    chapters = _split_chapters(raw_text)

    title = source.stem

    return Book(title=title, author="Unknown", chapters=chapters)


def _convert_to_text(path: Path) -> str:
    """Convert ebook file to raw string.

    Args:
        path: Path to the ebook file.

    Returns:
        str: The extracted raw text content of the book.
    """
    metadata = {"title": path.stem, "author": "Unknown"}
    return ebook2text.convert_file(path, metadata, save_file=False)


def _split_chapters(text: str) -> list[Chapter]:
    """Split text into chapters based on delimiters.

    Args:
        text: The full raw text of the book.

    Returns:
        list[Chapter]: A list of Chapter models extracted from the text.
    """
    chapters: list[Chapter] = []

    if "***" in text:
        parts = text.split("***")
        for i, part in enumerate(parts):
            content = part.strip()
            if not content:
                continue
            chapters.append(
                Chapter(
                    number=len(chapters) + 1,
                    title=f"Chapter {len(chapters) + 1}",
                    content=content,
                )
            )

    if len(chapters) <= 1:
        header_pattern = re.compile(r"\n#+\s*Chapter", re.IGNORECASE)
        parts = header_pattern.split(text)

        if len(parts) > 1:
            chapters = []
            for i, part in enumerate(parts):
                content = part.strip()
                if not content:
                    continue

                chapters.append(
                    Chapter(
                        number=len(chapters) + 1,
                        title=f"Chapter {len(chapters) + 1}",
                        content=content,
                    )
                )

    if not chapters:
        chapters.append(
            Chapter(number=1, title="Chapter 1", content=text.strip())
        )

    return chapters
