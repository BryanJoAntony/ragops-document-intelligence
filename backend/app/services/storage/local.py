from pathlib import Path

from app.core.config import get_settings
from app.services.storage.base import StorageService, StoredFile


class LocalStorageService(StorageService):
    def __init__(self) -> None:
        self.settings = get_settings()
        self.upload_dir = Path(self.settings.upload_dir)

    def save_file(self, content: bytes, stored_filename: str) -> StoredFile:
        stored_path = self.upload_dir / stored_filename
        stored_path.parent.mkdir(parents=True, exist_ok=True)
        stored_path.write_bytes(content)

        return StoredFile(
            storage_backend="local",
            storage_path=str(stored_path),
        )

    def ensure_file_exists(self, content: bytes, stored_filename: str) -> StoredFile:
        stored_path = self.upload_dir / stored_filename

        # Local dev volumes can be cleared while the DB still has metadata.
        # Restore the file so later parsing/indexing steps can still run.
        if not stored_path.exists():
            stored_path.parent.mkdir(parents=True, exist_ok=True)
            stored_path.write_bytes(content)

        return StoredFile(
            storage_backend="local",
            storage_path=str(stored_path),
        )

    def get_file(self, storage_path: str) -> bytes:
        path = Path(storage_path)

        if not path.exists():
            raise FileNotFoundError(f"Stored file not found: {storage_path}")

        return path.read_bytes()