"""Unit tests for the DB-backed storage provider."""

from collections.abc import Generator
from pathlib import Path

import pytest

from lorebinders import models
from lorebinders.storage.db import DBStorage


@pytest.fixture
def storage() -> Generator[DBStorage, None, None]:
    """Provide an in-memory DBStorage instance."""
    storage = DBStorage(db_url="sqlite:///:memory:")
    yield storage
    storage.engine.dispose()


@pytest.fixture
def test_dir(tmp_path: Path) -> Path:
    """A mock directory path to use as a key."""
    return tmp_path / "work"


def test_extraction_storage(storage: DBStorage, test_dir: Path) -> None:
    """Test saving and loading extractions."""
    data = {"Characters": ["Alice", "Bob"], "Locations": ["Paris"]}

    assert not storage.extraction_exists(test_dir, 1)

    with pytest.raises(FileNotFoundError):
        storage.load_extraction(test_dir, 1)

    storage.save_extraction(test_dir, 1, data)

    assert storage.extraction_exists(test_dir, 1)
    loaded = storage.load_extraction(test_dir, 1)
    assert loaded == data

    data["Characters"].append("Charlie")
    storage.save_extraction(test_dir, 1, data)
    assert storage.load_extraction(test_dir, 1) == data


def test_profile_storage(storage: DBStorage, test_dir: Path) -> None:
    """Test saving and loading entity profiles."""
    profile = models.EntityProfile(
        name="Alice",
        category="Characters",
        chapter_number=2,
        traits={"Appearance": ["Tall"], "Mood": ["Happy"]},
        confidence_score=0.9,
    )

    assert not storage.profile_exists(test_dir, 2, "Characters", "Alice")

    with pytest.raises(FileNotFoundError):
        storage.load_profile(test_dir, 2, "Characters", "Alice")

    storage.save_profile(test_dir, 2, profile)

    assert storage.profile_exists(test_dir, 2, "Characters", "Alice")
    loaded = storage.load_profile(test_dir, 2, "Characters", "Alice")
    assert loaded.name == profile.name
    assert loaded.category == profile.category
    assert loaded.traits == profile.traits
    assert loaded.confidence_score == profile.confidence_score

    profile.confidence_score = 0.95
    storage.save_profile(test_dir, 2, profile)
    loaded_updated = storage.load_profile(test_dir, 2, "Characters", "Alice")
    assert loaded_updated.confidence_score == 0.95


def test_summary_storage(storage: DBStorage, test_dir: Path) -> None:
    """Test saving and loading summaries."""
    summary_text = "Alice is a tall, happy protagonist."

    assert not storage.summary_exists(test_dir, "Characters", "Alice")

    with pytest.raises(FileNotFoundError):
        storage.load_summary(test_dir, "Characters", "Alice")

    storage.save_summary(test_dir, "Characters", "Alice", summary_text)

    assert storage.summary_exists(test_dir, "Characters", "Alice")
    assert storage.load_summary(test_dir, "Characters", "Alice") == summary_text

    summary_text = "Updated summary."
    storage.save_summary(test_dir, "Characters", "Alice", summary_text)
    assert storage.load_summary(test_dir, "Characters", "Alice") == summary_text
