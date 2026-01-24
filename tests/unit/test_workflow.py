"""Unit tests for the workflow module."""

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart
from pydantic_ai.models.function import FunctionModel

from lorebinders import models, types
from lorebinders.agent import create_summarization_agent
from lorebinders.workflow import (
    _aggregate_profiles_to_binder,
    _analyze_all_entities,
    _binder_to_profiles,
    _extract_all_chapters,
    build_binder,
)


@pytest.fixture
def temp_workspace(tmp_path: Path) -> Path:
    """Fixture providing a temporary workspace directory.

    Args:
        tmp_path: Pytest's temporary path fixture.

    Returns:
        Path to the workspace directory.
    """
    ws = tmp_path / "work"
    ws.mkdir()
    os.environ["LOREBINDERS_WORKSPACE_BASE_PATH"] = str(ws)
    return ws


@pytest.fixture
def book_file(tmp_path: Path) -> Path:
    """Fixture providing a temporary book file.

    Args:
        tmp_path: Pytest's temporary path fixture.

    Returns:
        Path to the book file.
    """
    path = tmp_path / "book.txt"
    path.write_text("Chapter 1\nAlice.")
    return path


@pytest.fixture
def run_config(book_file: Path) -> models.RunConfiguration:
    """Fixture providing a standard run configuration.

    Args:
        book_file: The book file fixture.

    Returns:
        A RunConfiguration instance.
    """
    return models.RunConfiguration(
        book_path=book_file,
        author_name="Test Author",
        book_title="Test Book",
        narrator_config=models.NarratorConfig(),
    )


@pytest.fixture
def summarization_agent():
    """Fixture providing a summarization agent.

    Returns:
        A summarization agent instance.
    """
    return create_summarization_agent()


def _fake_ingest(path: Path, output: Path) -> models.Book:
    """Fake ingestion function for testing.

    Args:
        path: Path to the book file.
        output: Output directory.

    Returns:
        A test Book instance.
    """
    return models.Book(
        title="Test Book",
        author="Test Author",
        chapters=[
            models.Chapter(number=1, title="Ch1", content="Alice content")
        ],
    )


def _fake_extract(ctx: models.Chapter) -> dict[str, list[str]]:
    """Fake extraction function for testing.

    Args:
        ctx: The chapter context.

    Returns:
        Extracted entities.
    """
    return {"Characters": ["Alice"]}


def _fake_analyze(
    targets: list[types.CategoryTarget], ctx: models.Chapter
) -> list[models.EntityProfile]:
    """Fake analysis function for testing.

    Args:
        targets: Category targets to analyze.
        ctx: The chapter context.

    Returns:
        List of entity profiles.
    """
    profiles = []
    for cat in targets:
        for entity_name in cat["entities"]:
            profiles.append(
                models.EntityProfile(
                    name=entity_name,
                    category=cat["name"],
                    chapter_number=ctx.number,
                    traits={"Role": "Hero"},
                )
            )
    return profiles


def _fake_empty_analyze(
    targets: list[types.CategoryTarget], ctx: models.Chapter
) -> list[models.EntityProfile]:
    """Fake analysis function that returns empty results.

    Args:
        targets: Category targets to analyze.
        ctx: The chapter context.

    Returns:
        Empty list.
    """
    return []


def _mock_summarize(
    messages: list[ModelMessage], info: object
) -> ModelResponse:
    """Mock summarization function returning Alice summary.

    Args:
        messages: Model messages.
        info: Model info.

    Returns:
        A ModelResponse with Alice summary.
    """
    return ModelResponse(
        parts=[
            TextPart(
                content=json.dumps(
                    {
                        "entity_name": "Alice",
                        "summary": "A test character.",
                    }
                )
            )
        ]
    )


def _mock_summarize_high(
    messages: list[ModelMessage], info: object
) -> ModelResponse:
    """Mock summarization function returning EntityHigh summary.

    Args:
        messages: Model messages.
        info: Model info.

    Returns:
        A ModelResponse with EntityHigh summary.
    """
    return ModelResponse(
        parts=[
            TextPart(
                content=json.dumps(
                    {
                        "entity_name": "EntityHigh",
                        "summary": "Summarized",
                    }
                )
            )
        ]
    )


def test_extract_all_chapters_calls_extraction_per_chapter(
    tmp_path: Path,
) -> None:
    """Test that extraction is called for each chapter."""
    chapters = [
        models.Chapter(number=1, title="Ch1", content="Content 1"),
        models.Chapter(number=2, title="Ch2", content="Content 2"),
    ]
    book = models.Book(title="Test", author="Test", chapters=chapters)

    extract_calls = []

    def fake_extract(ch: models.Chapter) -> dict[str, list[str]]:
        extract_calls.append(ch.number)
        return {"Characters": [f"Char{ch.number}"]}

    result = _extract_all_chapters(book, fake_extract, tmp_path)

    assert extract_calls == [1, 2]
    assert 1 in result
    assert 2 in result


def test_aggregate_profiles_to_binder_structure() -> None:
    """Test that profiles are aggregated into binder structure."""
    profiles = [
        models.EntityProfile(
            name="Alice",
            category="Characters",
            chapter_number=1,
            traits={"Role": "Hero"},
        ),
        models.EntityProfile(
            name="Alice",
            category="Characters",
            chapter_number=2,
            traits={"Age": "20"},
        ),
    ]

    binder = _aggregate_profiles_to_binder(profiles)

    assert "Characters" in binder
    assert "Alice" in binder["Characters"]
    assert binder["Characters"]["Alice"][1] == {"Role": "Hero"}
    assert binder["Characters"]["Alice"][2] == {"Age": "20"}


def test_binder_to_profiles_reconstruction() -> None:
    """Test that binder can be reconstructed to profiles."""
    binder: types.Binder = {
        "Characters": {
            "Alice": {1: {"Role": "Hero"}, 2: {"Age": "20"}},
        }
    }

    profiles = _binder_to_profiles(binder)

    assert len(profiles) == 2
    p1 = next(p for p in profiles if p.chapter_number == 1)
    p2 = next(p for p in profiles if p.chapter_number == 2)

    assert p1.name == "Alice" and p1.traits == {"Role": "Hero"}
    assert p2.name == "Alice" and p2.traits == {"Age": "20"}


def test_analyze_all_entities_processes_each_chapter(
    temp_workspace: Path,
) -> None:
    """Test that all entities are analyzed per chapter."""
    chapters = [
        models.Chapter(number=1, title="Ch1", content="Content 1"),
        models.Chapter(number=2, title="Ch2", content="Content 2"),
    ]
    book = models.Book(title="Test", author="Test", chapters=chapters)

    entities = {"Characters": {"Alice": [1, 2]}}

    def fake_analyze_batch(
        targets: list[types.CategoryTarget], ctx: models.Chapter
    ) -> list[models.EntityProfile]:
        profiles = []
        for cat in targets:
            for entity_name in cat["entities"]:
                profiles.append(
                    models.EntityProfile(
                        name=entity_name,
                        category=cat["name"],
                        chapter_number=ctx.number,
                        traits={"Found": "Yes"},
                    )
                )
        return profiles

    profiles = _analyze_all_entities(
        entities, book, temp_workspace, fake_analyze_batch
    )

    assert len(profiles) == 2
    assert {p.chapter_number for p in profiles} == {1, 2}


def test_build_binder_orchestration(
    temp_workspace: Path,
    run_config: models.RunConfiguration,
    summarization_agent,
) -> None:
    """Test end-to-end binder build orchestration."""
    report_path = None

    def fake_report(profiles: types.Binder, path: Path) -> None:
        nonlocal report_path
        report_path = path
        path.write_text("PDF Content")

    with summarization_agent.override(model=FunctionModel(_mock_summarize)):
        build_binder(
            run_config,
            _fake_ingest,
            _fake_extract,
            _fake_analyze,
            fake_report,
            summarization_agent,
        )

    author_dir = temp_workspace / "Test_Author" / "Test_Book"
    assert author_dir.exists()
    assert (author_dir / "profiles").exists()
    assert (author_dir / "profiles" / "ch1_Characters_Alice.json").exists()

    assert report_path == author_dir / "Test_Book_story_bible.pdf"
    assert report_path.exists()


def test_summarization_threshold_filters_entities(
    temp_workspace: Path,
    run_config: models.RunConfiguration,
    summarization_agent,
) -> None:
    """Verify that only entities with >= 3 chapters are summarized."""
    refined_binder: types.Binder = {
        "Characters": {
            "EntityLow": {
                1: {"Trait": "Value"},
                2: {"Trait": "Value"},
            },
            "EntityHigh": {
                1: {"Trait": "Value"},
                2: {"Trait": "Value"},
                3: {"Trait": "Value"},
            },
        }
    }

    captured_binder: types.Binder | None = None

    def capture_report(binder: types.Binder, path: Path) -> None:
        nonlocal captured_binder
        captured_binder = binder

    with patch(
        "lorebinders.workflow.refine_binder", return_value=refined_binder
    ):
        with summarization_agent.override(
            model=FunctionModel(_mock_summarize_high)
        ):
            build_binder(
                run_config,
                _fake_ingest,
                _fake_extract,
                _fake_empty_analyze,
                capture_report,
                summarization_agent,
            )

    assert captured_binder is not None
    characters = captured_binder.get("Characters")
    assert isinstance(characters, dict)

    assert "EntityLow" in characters
    assert "Summary" not in characters["EntityLow"]

    assert "EntityHigh" in characters
    assert characters["EntityHigh"].get("Summary") == "Summarized"
