import pytest

from app.services.storage.factory import get_storage_service
from app.services.storage.local import LocalStorageService


def test_storage_factory_returns_local_storage(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FILE_STORAGE_BACKEND", "local")
    service = get_storage_service()

    assert isinstance(service, LocalStorageService)