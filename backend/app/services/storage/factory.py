from app.core.config import get_settings
from app.services.storage.base import StorageService
from app.services.storage.local import LocalStorageService


def get_storage_service() -> StorageService:
    settings = get_settings()
    return get_storage_service_for_backend(settings.file_storage_backend)


def get_storage_service_for_backend(backend_name: str) -> StorageService:
    backend = backend_name.lower().strip()

    if backend == "local":
        return LocalStorageService()

    raise NotImplementedError(
        f"File storage backend '{backend_name}' is configured but not implemented yet."
    )