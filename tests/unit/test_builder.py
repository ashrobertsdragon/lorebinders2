from unittest.mock import Mock, call

import pytest
from lorebinders.builder import LoreBinderBuilder
from lorebinders.core.interfaces import (
    AnalysisAgent,
    ExtractionAgent,
    IngestionProvider,
    ReportingProvider,
)
from lorebinders.core.models import (
    Book,
    Chapter,
    CharacterProfile,
    NarratorConfig,
    RunConfiguration,
)


@pytest.fixture
def mock_ingestion():
    return Mock(spec=IngestionProvider)


@pytest.fixture
def mock_extraction():
    return Mock(spec=ExtractionAgent)


@pytest.fixture
def mock_analysis():
    return Mock(spec=AnalysisAgent)


@pytest.fixture
def mock_reporting():
    return Mock(spec=ReportingProvider)


@pytest.fixture
def mock_config(tmp_path):
    return RunConfiguration(
        book_path=tmp_path / "book.epub",
        author_name="Test Author",
        book_title="Test Book",
        narrator_config=NarratorConfig(is_3rd_person=True),
        custom_traits=["Trait1"],
        custom_categories=["Category1"],
    )


def test_builder_flow(
    mock_ingestion,
    mock_extraction,
    mock_analysis,
    mock_reporting,
    mock_config,
    tmp_path,
):
    mock_book = Book(
        title="Test Book",
        author="Test Author",
        chapters=[
            Chapter(number=1, title="Ch 1", content="Chapter 1 content"),
            Chapter(number=2, title="Ch 2", content="Chapter 2 content"),
        ],
    )
    mock_ingestion.ingest.return_value = mock_book

    mock_extraction.extract.side_effect = [
        ["Alice", "Bob"],
        ["Alice", "Charlie"],
    ]

    mock_analysis.analyze.return_value = CharacterProfile(
        name="Alice",
        traits={"Trait1": "Value1"},
        confidence_score=0.9,
    )

    builder = LoreBinderBuilder(
        ingestion=mock_ingestion,
        extraction=mock_extraction,
        analysis=mock_analysis,
        reporting=mock_reporting,
    )

    builder.run(mock_config)

    mock_ingestion.ingest.assert_called_once()
    assert mock_ingestion.ingest.call_args[0][0] == mock_config.book_path

    assert mock_extraction.extract.call_count == 2
    mock_extraction.extract.assert_has_calls([
        call(mock_book.chapters[0]),
        call(mock_book.chapters[1]),
    ])

    assert mock_analysis.analyze.call_count == 4

    mock_reporting.generate.assert_called_once()
    args = mock_reporting.generate.call_args[0]
    assert len(args[0]) >= 2
