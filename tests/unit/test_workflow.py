"""Unit tests for the workflow module."""

import json
import os
from pathlib import Path

import pytest
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart
from pydantic_ai.models.function import FunctionModel

from lorebinders import models
from lorebinders.agent import create_summarization_agent
from lorebinders.storage.provider import FilesystemStorage
from lorebinders.workflow import (
    _aggregate_to_binder,
    _analyze_all_entities,
    _extract_all_chapters,
    build_binder,
)


@pytest.fixture
def temp_workspace(tmp_path: Path) -> Path:
    """Fixture providing a temporary workspace directory."""
    from lorebinders.settings import get_settings

    ws = tmp_path / "work"
    ws.mkdir()
    os.environ["LOREBINDERS_WORKSPACE_BASE_PATH"] = str(ws)
    get_settings.cache_clear()
    return ws


@pytest.fixture
def book_file(tmp_path: Path) -> Path:
    """Fixture providing a temporary book file."""
    path = tmp_path / "book.txt"
    path.write_text("Chapter 1\nAlice.")
    return path


@pytest.fixture
def run_config(book_file: Path) -> models.RunConfiguration:
    """Fixture providing a standard run configuration."""
    return models.RunConfiguration(
        book_path=book_file,
        author_name="Test Author",
        book_title="Test Book",
        narrator_config=models.NarratorConfig(),
    )


@pytest.fixture
def summarization_agent():
    """Fixture providing a summarization agent."""
    return create_summarization_agent()


def _fake_ingest(path: Path, output: Path) -> models.Book:
    """Fake ingestion function for testing."""
    return models.Book(
        title="Test Book",
        author="Test Author",
        chapters=[
            models.Chapter(number=1, title="Ch1", content="Alice content")
        ],
    )


async def _fake_extract(ctx: models.Chapter) -> dict[str, list[str]]:
    """Fake extraction function for testing."""
    return {"Characters": ["Alice"]}


async def _fake_analyze(
    targets: list[models.CategoryTarget], ctx: models.Chapter
) -> list[models.EntityProfile]:
    """Fake analysis function for testing."""
    profiles = []
    for cat in targets:
        for entity_name in cat.entities:
            profiles.append(
                models.EntityProfile(
                    name=entity_name,
                    category=cat.name,
                    chapter_number=ctx.number,
                    traits={"Role": "Hero"},
                )
            )
    return profiles


def _mock_summarize(
    messages: list[ModelMessage], info: object
) -> ModelResponse:
    """Mock summarization function returning Alice summary."""
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


@pytest.mark.anyio
async def test_extract_all_chapters_calls_extraction_per_chapter(
    tmp_path: Path,
) -> None:
    """Test that extraction is called for each chapter."""
    chapters = [
        models.Chapter(number=1, title="Ch1", content="Content 1"),
        models.Chapter(number=2, title="Ch2", content="Content 2"),
    ]
    book = models.Book(title="Test", author="Test", chapters=chapters)

    extract_calls = []

    async def fake_extract(ch: models.Chapter) -> dict[str, list[str]]:
        extract_calls.append(ch.number)
        return {"Characters": [f"Char{ch.number}"]}

    storage = FilesystemStorage()
    result = await _extract_all_chapters(book, fake_extract, tmp_path, storage)

    assert sorted(extract_calls) == [1, 2]
    assert 1 in result
    assert 2 in result


def test_aggregate_to_binder_structure() -> None:
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

    binder = _aggregate_to_binder(profiles)

    assert "Characters" in binder.categories
    alice = binder.categories["Characters"].entities["Alice"]
    assert alice.appearances[1].traits == {"Role": "Hero"}
    assert alice.appearances[2].traits == {"Age": "20"}


@pytest.mark.anyio
async def test_analyze_all_entities_processes_each_chapter(
    temp_workspace: Path,
) -> None:
    """Test that all entities are analyzed per chapter."""
    chapters = [
        models.Chapter(number=1, title="Ch1", content="Content 1"),
        models.Chapter(number=2, title="Ch2", content="Content 2"),
    ]
    book = models.Book(title="Test", author="Test", chapters=chapters)

    entities = {"Characters": {"Alice": [1, 2]}}

    async def fake_analyze_batch(
        targets: list[models.CategoryTarget], ctx: models.Chapter
    ) -> list[models.EntityProfile]:
        profiles = []
        for cat in targets:
            for entity_name in cat.entities:
                profiles.append(
                    models.EntityProfile(
                        name=entity_name,
                        category=cat.name,
                        chapter_number=ctx.number,
                        traits={"Found": "Yes"},
                    )
                )
        return profiles

    storage = FilesystemStorage()
    profiles = await _analyze_all_entities(
        entities, book, temp_workspace, fake_analyze_batch, storage
    )

    assert len(profiles) == 2
    assert {p.chapter_number for p in profiles} == {1, 2}


@pytest.mark.anyio
async def test_build_binder_orchestration(
    temp_workspace: Path,
    run_config: models.RunConfiguration,
    summarization_agent,
) -> None:
    """Test end-to-end binder build orchestration."""
    report_path = None

    def fake_report(binder: models.Binder, path: Path) -> None:
        nonlocal report_path
        report_path = path
        path.write_text("PDF Content")

    with summarization_agent.override(model=FunctionModel(_mock_summarize)):
        await build_binder(
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
