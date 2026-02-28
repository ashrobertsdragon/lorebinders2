"""Unit tests for the DB-backed storage provider."""

from collections.abc import Generator

import pytest

from lorebinders import models
from lorebinders.storage.providers.db import DBStorage


@pytest.fixture
def storage() -> Generator[DBStorage, None, None]:
    """Provide a fresh in-memory database storage for each test."""
    storage = DBStorage("sqlite:///:memory:")
    storage.set_workspace("test_author", "test_title")
    yield storage
    storage.engine.dispose()


def test_extraction_lifecycle(
    storage: DBStorage,
) -> None:
    """Test saving and loading extraction data."""
    chapter_num = 1
    data = {"Characters": ["Alice", "Bob"], "Locations": ["Paris"]}

    assert not storage.extraction_exists(chapter_num)

    storage.save_extraction(chapter_num, data)
    assert storage.extraction_exists(chapter_num)

    loaded_data = storage.load_extraction(chapter_num)
    assert loaded_data == data


def test_profile_lifecycle(
    storage: DBStorage,
) -> None:
    """Test saving and loading entity profiles."""
    chapter_num = 1
    category = "Characters"
    name = "Alice"
    profile = models.EntityProfile(
        chapter_number=chapter_num,
        category=category,
        name=name,
        traits={"Age": "25", "Role": "Hacker"},
    )

    assert not storage.profile_exists(chapter_num, category, name)

    storage.save_profile(chapter_num, profile)
    assert storage.profile_exists(chapter_num, category, name)

    loaded_profile = storage.load_profile(chapter_num, category, name)
    assert loaded_profile == profile


def test_summary_lifecycle(
    storage: DBStorage,
) -> None:
    """Test saving and loading summaries."""
    category = "Characters"
    name = "Alice"
    summary_text = "Updated summary."
    storage.save_summary(category, name, summary_text)
    assert storage.load_summary(category, name) == summary_text
