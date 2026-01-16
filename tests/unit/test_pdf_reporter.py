"""Unit tests for the PDF reporter."""

import shutil
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from lorebinders.core.models import Book, CharacterProfile, Chapter
from lorebinders.reporting.pdf import generate_pdf_report

@pytest.fixture
def dummy_data():
    book = Book(
        title="Test Book",
        author="Test Author",
        chapters=[Chapter(number=1, title="Ch1", content="Content")]
    )
    profile = CharacterProfile(
        name="Protagonist",
        traits={"Role": "Hero", "Personality": "Brave"},
        confidence_score=0.9
    )
    return [profile]

def test_generate_pdf_creates_file(dummy_data, tmp_path):
    """Test that the PDF generation creates a valid file."""
    output_path = tmp_path / "report.pdf"
    generate_pdf_report(dummy_data, output_path)

    assert output_path.exists()
    assert output_path.stat().st_size > 0

    with open(output_path, "rb") as f:
        header = f.read(5)
        assert header == b"%PDF-"
