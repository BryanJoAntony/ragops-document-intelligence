from app.utils.hashing import build_stored_filename, sha256_bytes


def test_sha256_bytes_is_stable() -> None:
    content = b"hello ragops"
    assert sha256_bytes(content) == sha256_bytes(content)


def test_build_stored_filename_preserves_suffix_lowercase() -> None:
    filename = build_stored_filename("abc123", "MyFile.PDF")
    assert filename == "abc123.pdf"