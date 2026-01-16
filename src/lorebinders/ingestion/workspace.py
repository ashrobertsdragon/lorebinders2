import re
import shutil
from pathlib import Path


class WorkspaceManager:
    """Manages creation and cleanup of workspace directories."""

    def __init__(self, base_path: Path = Path("work")):
        """Initialize the WorkspaceManager.

        Args:
            base_path: Root directory for workspaces. Defaults to "work".
        """
        self.base_path = base_path

    def ensure_workspace(self, author: str, title: str) -> Path:
        """Create (if needed) and return the path to the book's workspace.

        Structure: work/{author}/{title}

        Args:
            author: The name of the author.
            title: The title of the book.

        Returns:
            The Path to the book's workspace directory.
        """
        safe_author = self.sanitize_filename(author)
        safe_title = self.sanitize_filename(title)

        path = self.base_path / safe_author / safe_title
        path.mkdir(parents=True, exist_ok=True)
        return path

    def clean_workspace(self, author: str, title: str) -> None:
        """Remove the workspace directory for a specific book.

        Args:
            author: The name of the author.
            title: The title of the book.
        """
        safe_author = self.sanitize_filename(author)
        safe_title = self.sanitize_filename(title)

        path = self.base_path / safe_author / safe_title
        if path.exists():
            shutil.rmtree(path)

    def sanitize_filename(self, name: str) -> str:
        """Sanitize a string to be safe for use as a filename.

        Replaces non-alphanumeric characters (except - and .) with underscores.

        Args:
            name: The input string.

        Returns:
            A safe filename string.
        """
        cleaned = re.sub(r"[^a-zA-Z0-9\-]", "_", name)
        cleaned = re.sub(r"_+", "_", cleaned)
        return cleaned
