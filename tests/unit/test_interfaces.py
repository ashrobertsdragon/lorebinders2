import inspect
from typing import Protocol
from pathlib import Path

import pytest
from lorebinders.core import interfaces, models

def test_ingestion_provider_protocol():
    """Verify IngestionProvider protocol definition."""
    assert issubclass(interfaces.IngestionProvider, Protocol)

    assert hasattr(interfaces.IngestionProvider, 'ingest')
    sig = inspect.signature(interfaces.IngestionProvider.ingest)
    assert 'source' in sig.parameters
    assert sig.parameters['source'].annotation == Path
    assert 'output_dir' in sig.parameters
    assert sig.parameters['output_dir'].annotation == Path
    assert sig.return_annotation == models.Book

def test_extraction_agent_protocol():
    """Verify ExtractionAgent protocol definition."""
    assert issubclass(interfaces.ExtractionAgent, Protocol)

    assert hasattr(interfaces.ExtractionAgent, 'extract')
    sig = inspect.signature(interfaces.ExtractionAgent.extract)
    assert 'chapter' in sig.parameters
    assert sig.parameters['chapter'].annotation == models.Chapter
    assert sig.return_annotation == list[str]

def test_analysis_agent_protocol():
    """Verify AnalysisAgent protocol definition."""
    assert issubclass(interfaces.AnalysisAgent, Protocol)

    assert hasattr(interfaces.AnalysisAgent, 'analyze')
    sig = inspect.signature(interfaces.AnalysisAgent.analyze)
    assert 'name' in sig.parameters
    assert sig.parameters['name'].annotation == str
    assert 'context' in sig.parameters
    assert sig.parameters['context'].annotation == models.Chapter
    assert sig.return_annotation == models.CharacterProfile

def test_reporting_provider_protocol():
    """Verify ReportingProvider protocol definition."""
    assert issubclass(interfaces.ReportingProvider, Protocol)

    assert hasattr(interfaces.ReportingProvider, 'generate')
    sig = inspect.signature(interfaces.ReportingProvider.generate)
    assert 'data' in sig.parameters
    assert sig.parameters['data'].annotation == list[models.CharacterProfile]
    assert 'output_path' in sig.parameters
    assert sig.parameters['output_path'].annotation == Path
    assert sig.return_annotation is None
