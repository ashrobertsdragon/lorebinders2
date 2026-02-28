from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from lorebinders import models
from lorebinders.app import run


@pytest.fixture
def run_config(tmp_path: Path) -> models.RunConfiguration:
    return models.RunConfiguration(
        book_path=tmp_path / "book.txt",
        author_name="Test Author",
        book_title="Test Book",
        narrator_config=models.NarratorConfig(),
    )


def test_run_returns_path(run_config: models.RunConfiguration) -> None:
    """Test that run delegates to build_binder and returns a Path."""
    fake_path = Path("/fake/output/Test_Book_story_bible.pdf")

    with patch(
        "lorebinders.app.build_binder",
        new_callable=AsyncMock,
        return_value=fake_path,
    ) as mock_build:
        result = run(run_config)

    mock_build.assert_awaited_once_with(
        run_config,
        progress=None,
        extraction_agent=None,
        analysis_agent=None,
        summarization_agent=None,
    )
    assert result == fake_path


def test_run_passes_optional_args(run_config: models.RunConfiguration) -> None:
    """Test that agent overrides and progress callbacks are forwarded."""
    fake_path = Path("/fake/output/Test_Book_story_bible.pdf")
    fake_agent = MagicMock()

    def fake_progress(update: models.ProgressUpdate) -> None:
        pass

    with patch(
        "lorebinders.app.build_binder",
        new_callable=AsyncMock,
        return_value=fake_path,
    ) as mock_build:
        result = run(
            run_config,
            progress=fake_progress,
            extraction_agent=fake_agent,
            analysis_agent=fake_agent,
            summarization_agent=fake_agent,
        )

    mock_build.assert_awaited_once_with(
        run_config,
        progress=fake_progress,
        extraction_agent=fake_agent,
        analysis_agent=fake_agent,
        summarization_agent=fake_agent,
    )
    assert result == fake_path
