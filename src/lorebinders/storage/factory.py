"""Factory functions for storage backends.

This module exposes a singleton get_storage() for the storage provider.
"""

from lorebinders.storage.provider import FilesystemStorage, StorageProvider

__storage_singleton: StorageProvider | None = None


def get_storage(
    provider: type[StorageProvider] = FilesystemStorage,
) -> StorageProvider:
    """Get the process-wide storage provider.

    Args:
        provider: The storage provider to use.

    Returns:
        StorageProvider: A singleton storage implementation.
    """
    global __storage_singleton
    if not __storage_singleton or not isinstance(__storage_singleton, provider):
        __storage_singleton = provider()
    return __storage_singleton
