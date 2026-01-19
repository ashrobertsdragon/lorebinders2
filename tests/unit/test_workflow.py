import os
from pathlib import Path

import pytest

from lorebinders import models
from lorebinders.models import Binder, EntityTarget
from lorebinders.workflow import (
    _aggregate_extractions,
    _aggregate_profiles_to_binder,
    _analyze_all_entities,
    _binder_to_profiles,
    _deduplicate_entity_names,
    _extract_all_chapters,
    build_binder,
)


@pytest.fixture
def temp_workspace(tmp_path: Path) -> Path:
    ws = tmp_path / "work"
    ws.mkdir()
    os.environ["LOREBINDERS_WORKSPACE_BASE_PATH"] = str(ws)
    return ws


def test_deduplicate_entity_names_merges_similar() -> None:
    names = ["Father", "the father", "Father"]
    result = _deduplicate_entity_names(names)
    assert len(result) == 1


def test_deduplicate_entity_names_keeps_distinct() -> None:
    names = ["Alice", "Bob", "Charlie"]
    result = _deduplicate_entity_names(names)
    assert set(result) == {"Alice", "Bob", "Charlie"}


def test_aggregate_extractions_merges_across_chapters() -> None:
    raw = {
        1: {"Characters": ["Alice", "Bob"]},
        2: {"Characters": ["Alice", "Charlie"]},
    }
    result = _aggregate_extractions(raw)

    assert "Characters" in result
    assert "Alice" in result["Characters"]
    assert 1 in result["Characters"]["Alice"]
    assert 2 in result["Characters"]["Alice"]


def test_aggregate_extractions_deduplicates_similar_names() -> None:
    raw = {
        1: {"Characters": ["Father", "the father"]},
    }
    result = _aggregate_extractions(raw)

    assert len(result["Characters"]) == 1


def test_extract_all_chapters_calls_extraction_per_chapter() -> None:
    chapters = [
        models.Chapter(number=1, title="Ch1", content="Content 1"),
        models.Chapter(number=2, title="Ch2", content="Content 2"),
    ]
    book = models.Book(title="Test", author="Test", chapters=chapters)

    extract_calls = []

    def fake_extract(ch: models.Chapter) -> dict[str, list[str]]:
        extract_calls.append(ch.number)
        return {"Characters": [f"Char{ch.number}"]}

    result = _extract_all_chapters(book, fake_extract)

    assert extract_calls == [1, 2]
    assert 1 in result
    assert 2 in result


def test_aggregate_profiles_to_binder_structure() -> None:
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
    binder: Binder = {
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
    chapters = [
        models.Chapter(number=1, title="Ch1", content="Content 1"),
        models.Chapter(number=2, title="Ch2", content="Content 2"),
    ]
    book = models.Book(title="Test", author="Test", chapters=chapters)

    entities = {"Characters": {"Alice": [1, 2]}}

    def fake_analyze_batch(
        targets: list[EntityTarget], ctx: models.Chapter
    ) -> list[models.EntityProfile]:
        profiles = []
        for e in targets:
            profiles.append(
                models.EntityProfile(
                    name=e["name"],
                    category=e["category"],
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
    temp_workspace: Path, tmp_path: Path
) -> None:
    import json

    from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart
    from pydantic_ai.models.function import FunctionModel

    from lorebinders.agent import create_summarization_agent

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
            chapters=[
                models.Chapter(number=1, title="Ch1", content="Alice content")
            ],
        )

    def fake_extract(ctx: models.Chapter) -> dict[str, list[str]]:
        return {"Characters": ["Alice"]}

    def fake_analyze(
        targets: list[EntityTarget], ctx: models.Chapter
    ) -> list[models.EntityProfile]:
        profiles = []
        for e in targets:
            profiles.append(
                models.EntityProfile(
                    name=e["name"],
                    category=e["category"],
                    chapter_number=ctx.number,
                    traits={"Role": "Hero"},
                )
            )
        return profiles

    report_path = None

    def fake_report(profiles: list[models.EntityProfile], path: Path) -> None:
        nonlocal report_path
        report_path = path
        path.write_text("PDF Content")

    def mock_summarize(
        messages: list[ModelMessage], info: object
    ) -> ModelResponse:
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

    summarization_agent = create_summarization_agent()
    with summarization_agent.override(model=FunctionModel(mock_summarize)):
        build_binder(
            config,
            fake_ingest,
            fake_extract,
            fake_analyze,
            fake_report,
            summarization_agent,
        )

    author_dir = temp_workspace / "Test_Author" / "Test_Book"
    assert author_dir.exists()
    assert (author_dir / "profiles").exists()
    assert (author_dir / "profiles" / "ch1_Characters_Alice.json").exists()

    assert report_path == author_dir / "Test_Book_story_bible.pdf"
    assert report_path.exists()
