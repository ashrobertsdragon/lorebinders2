import os
import json
from pathlib import Path
from typing import Any

import pytest

from lorebinders import models
from lorebinders.builder import (
    _aggregate_book_data,
    _binder_to_profiles,
    _process_chapter,
    _analyze_character,
    build_binder,
)


@pytest.fixture
def temp_workspace(tmp_path: Path) -> Path:
    """Fixture to provide a clean workspace per test."""
    ws = tmp_path / "work"
    ws.mkdir()
    os.environ["LOREBINDERS_WORKSPACE_BASE_PATH"] = str(ws)
    return ws


def test_aggregate_book_data_preserves_context():
    """Test that data is aggregated by chapter without overwriting."""
    chapter1 = models.Chapter(number=1, title="Ch1", content="")
    chapter1.profiles = [
        models.EntityProfile(name="Alice", category="Characters", chapter_number=1, traits={"Role": "Hero"}, confidence_score=1.0)
    ]

    chapter2 = models.Chapter(number=2, title="Ch2", content="")
    chapter2.profiles = [
        models.EntityProfile(name="Alice", category="Characters", chapter_number=2, traits={"Age": "20"}, confidence_score=0.9)
    ]

    book = models.Book(title="Test", author="Test", chapters=[chapter1, chapter2])

    binder = _aggregate_book_data(book)

    assert "Characters" in binder
    assert "Alice" in binder["Characters"]

    assert binder["Characters"]["Alice"][1] == {"Role": "Hero"}
    assert binder["Characters"]["Alice"][2] == {"Age": "20"}


def test_binder_to_profiles_reconstruction():
    """Test converting nested binder dict back to profile objects."""
    binder = {
        "Characters": {
            "Alice": {
                1: {"Role": "Hero"},
                2: {"Age": "20"}
            }
        }
    }

    profiles = _binder_to_profiles(binder)

    assert len(profiles) == 2
    p1 = next(p for p in profiles if p.chapter_number == 1)
    p2 = next(p for p in profiles if p.chapter_number == 2)

    assert p1.name == "Alice" and p1.traits == {"Role": "Hero"}
    assert p2.name == "Alice" and p2.traits == {"Age": "20"}


def test_analyze_character_new_creates_file(temp_workspace: Path):
    """Test analyzing a new character saves it to disk."""
    chapter = models.Chapter(number=1, title="Ch1", content="Some content")

    def fake_analysis(name: str, category: str, ctx: models.Chapter) -> models.EntityProfile:
        return models.EntityProfile(name=name, category=category, chapter_number=ctx.number, traits={"Status": "New"}, confidence_score=0.8)

    profile = _analyze_character("Alice", "Characters", chapter, temp_workspace, fake_analysis)

    assert profile.name == "Alice"
    assert profile.category == "Characters"
    assert profile.chapter_number == 1
    assert profile.traits["Status"] == "New"

    expected_file = temp_workspace / "ch1_Characters_Alice.json"
    assert expected_file.exists()


def test_analyze_character_existing_loads_file(temp_workspace: Path):
    """Test that existing profiles are loaded instead of re-analyzed."""
    chapter = models.Chapter(number=1, title="Ch1", content="Some content")

    existing = models.EntityProfile(name="Alice", category="Characters", chapter_number=1, traits={"Status": "Old"}, confidence_score=1.0)
    file_path = temp_workspace / "ch1_Characters_Alice.json"
    file_path.write_text(existing.model_dump_json(), encoding="utf-8")

    called = False
    def fake_analysis(name: str, category: str, ctx: models.Chapter) -> models.EntityProfile:
        nonlocal called
        called = True
        return models.EntityProfile(name=name, category=category, chapter_number=ctx.number, traits={"Status": "Wrong"}, confidence_score=0.0)

    profile = _analyze_character("Alice", "Characters", chapter, temp_workspace, fake_analysis)

    assert not called
    assert profile.traits["Status"] == "Old"


def test_process_chapter_workflow(temp_workspace: Path):
    """Test processing a chapter extracts and analyzes names."""
    chapter = models.Chapter(number=1, title="Meeting", content="Alice meeting Bob")

    def fake_extract(ctx: models.Chapter) -> dict[str, list[str]]:
        return {"Characters": ["Alice", "Bob"]}

    def fake_analyze(name: str, category: str, ctx: models.Chapter) -> models.EntityProfile:
        return models.EntityProfile(name=name, category=category, chapter_number=ctx.number, traits={"Found": "Yes"})

    profiles = _process_chapter(chapter, temp_workspace, fake_extract, fake_analyze)

    assert len(profiles) == 2
    assert {p.name for p in profiles} == {"Alice", "Bob"}
    assert (temp_workspace / "ch1_Characters_Alice.json").exists()


def test_build_binder_orchestration(temp_workspace: Path, tmp_path: Path):
    """Test the full build_binder pipeline functioning."""

    book_file = tmp_path / "book.txt"
    book_file.write_text("Chapter 1\nAlice.")

    config = models.RunConfiguration(
        book_path=book_file,
        author_name="Test Author",
        book_title="Test Book",
        narrator_config=models.NarratorConfig(),
    )

    def fake_ingest(path: Path, output: Path) -> models.Book:
        return models.Book(
            title="Test Book",
            author="Test Author",
            chapters=[models.Chapter(number=1, title="Ch1", content="Alice content")]
        )

    def fake_extract(ctx: models.Chapter) -> dict[str, list[str]]:
        return {"Characters": ["Alice"]}

    def fake_analyze(name: str, category: str, ctx: models.Chapter) -> models.EntityProfile:
        return models.EntityProfile(name=name, category=category, chapter_number=ctx.number, traits={"Role": "Hero"})

    report_path = None
    def fake_report(profiles: list[models.EntityProfile], path: Path) -> None:
        nonlocal report_path
        report_path = path
        path.write_text("PDF Content")


    build_binder(config, fake_ingest, fake_extract, fake_analyze, fake_report)


    author_dir = temp_workspace / "Test_Author" / "Test_Book"
    assert author_dir.exists()
    assert (author_dir / "profiles").exists()


    assert (author_dir / "profiles" / "ch1_Characters_Alice.json").exists()


    assert report_path == author_dir / "Test_Book_story_bible.pdf"
    assert report_path.exists()
