"""Storage package for persistence and workspace management."""

from lorebinders.storage.factory import get_storage
from lorebinders.storage.provider import FilesystemStorage, StorageProvider

__all__ = [
    "get_storage",
    "StorageProvider",
    "FilesystemStorage",
]
