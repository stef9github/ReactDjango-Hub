"""
Storage layer for document management.
"""

from .base import StorageBackend
from .local_storage import LocalFileStorage
from .manager import StorageManager

__all__ = [
    "StorageBackend",
    "LocalFileStorage", 
    "StorageManager"
]