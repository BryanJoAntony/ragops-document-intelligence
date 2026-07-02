from app.services.chunking import ChunkingService
from app.services.document_parser import ParsedDocument, ParsedPage


def test_chunk_document_generates_chunks_with_metadata() -> None:
    parsed = ParsedDocument(
        parser_name="test_parser",
        full_text="Overview\n\nThis is a test document for chunking.",
        pages=[
            ParsedPage(
                page_number=1,
                text="Overview\n\nThis is a test document for chunking.",
            )
        ],
    )

    chunker = ChunkingService(max_chars=200, overlap_chars=20)
    chunks = chunker.chunk_document(parsed)

    assert len(chunks) == 1
    assert chunks[0].chunk_index == 0
    assert chunks[0].page_number == 1
    assert chunks[0].metadata["parser_name"] == "test_parser"


def test_chunk_document_splits_large_text() -> None:
    long_text = "A" * 500

    parsed = ParsedDocument(
        parser_name="test_parser",
        full_text=long_text,
        pages=[ParsedPage(page_number=1, text=long_text)],
    )

    chunker = ChunkingService(max_chars=100, overlap_chars=10)
    chunks = chunker.chunk_document(parsed)

    assert len(chunks) > 1