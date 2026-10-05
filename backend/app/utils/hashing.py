import hashlib
from pathlib import Path


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def build_stored_filename(file_hash: str, original_filename: str) -> str:
    suffix = Path(original_filename).suffix.lower()
    return f"{file_hash}{suffix}"