from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class StoredFile:
    storage_backend: str
    storage_path: str
    public_url: str | None = None


class StorageService(ABC):
    @abstractmethod
    def save_file(self, content: bytes, stored_filename: str) -> StoredFile:
        raise NotImplementedError

    @abstractmethod
    def ensure_file_exists(self, content: bytes, stored_filename: str) -> StoredFile:
        raise NotImplementedError

    @abstractmethod
    def get_file(self, storage_path: str) -> bytes:
        raise NotImplementedError