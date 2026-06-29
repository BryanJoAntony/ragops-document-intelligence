from app.core.config import get_settings
from app.services.storage.base import StorageService
from app.services.storage.local import LocalStorageService


def get_storage_service() -> StorageService:
    settings = get_settings()
    backend = settings.file_storage_backend.lower().strip()

    if backend == "local":
        return LocalStorageService()

    raise NotImplementedError(
        f"File storage backend '{settings.file_storage_backend}' is configured but not implemented yet."
    )