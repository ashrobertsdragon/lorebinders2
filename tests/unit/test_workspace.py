import shutil
from pathlib import Path

import pytest
from lorebinders.ingestion.workspace import WorkspaceManager


@pytest.fixture
def workspace_base(tmp_path):
    return tmp_path / "work_test"


@pytest.fixture
def manager(workspace_base):
    return WorkspaceManager(base_path=workspace_base)


def test_ensure_workspace_creates_directory(manager, workspace_base):
    """Test that ensure_workspace creates the correct directory structure."""
    author = "New Author"
    title = "My Book"


    path = manager.ensure_workspace(author, title)

    assert path.exists()
    assert path.is_dir()
    assert (workspace_base / "New_Author" / "My_Book").exists()
    assert path == workspace_base / "New_Author" / "My_Book"


def test_clean_workspace(manager, workspace_base):
    """Test that clean_workspace removes the specific book directory."""
    author = "Author"
    title = "Title"
    path = manager.ensure_workspace(author, title)


    (path / "dummy.txt").touch()
    assert (path / "dummy.txt").exists()

    manager.clean_workspace(author, title)

    assert not path.exists()


def test_ensure_workspace_idempotent(manager):
    """Test that calling ensure_workspace multiple times doesn't fail."""
    path1 = manager.ensure_workspace("A", "B")
    path2 = manager.ensure_workspace("A", "B")
    assert path1 == path2
    assert path1.exists()


def test_sanitize_filename(manager):
    """Test internal filename sanitization."""

    assert manager.sanitize_filename("Normal") == "Normal"
    assert manager.sanitize_filename("Space Valid") == "Space_Valid"
    assert manager.sanitize_filename("Bad/Chars\\Here") == "Bad_Chars_Here"
    assert manager.sanitize_filename("..") == "_"
