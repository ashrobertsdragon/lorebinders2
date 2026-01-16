import inspect
from typing import Protocol, get_args
from pathlib import Path

import pytest
from lorebinders.core import interfaces, models

def test_ingestion_provider_alias():
    """Verify IngestionProvider callable alias definition."""


    assert hasattr(interfaces, 'IngestionProvider')

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

def test_reporting_provider_alias():
    """Verify ReportingProvider callable alias definition."""
    assert hasattr(interfaces, 'ReportingProvider')
