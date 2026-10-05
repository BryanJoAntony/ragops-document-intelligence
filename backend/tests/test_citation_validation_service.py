from uuid import uuid4

from app.services.answer_generation_service import Citation, GeneratedAnswer
from app.services.citation_validation_service import CitationValidationService
from app.services.retrieval_service import RetrievedChunk


def _chunk() -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=uuid4(),
        document_id=uuid4(),
        chunk_index=0,
        score=0.9,
        text_preview="Audit history should be stored in PostgreSQL.",
        chunk_text="Audit history should be stored in PostgreSQL. Qdrant should store vector embeddings.",
        metadata={
            "page_number": 1,
            "section_title": "Storage Policy",
            "metadata_json": {"tags": ["audit", "storage"]},
        },
    )


def test_extract_citation_markers_deduplicates() -> None:
    markers = CitationValidationService._extract_citation_markers(
        "Audit history is stored in PostgreSQL [C1]. More context [C1] and [C2]."
    )

    assert markers == ["[C1]", "[C2]"]


def test_extract_cited_claims() -> None:
    claims = CitationValidationService._extract_cited_claims(
        "- Audit history is stored in PostgreSQL. [C1]\n"
        "This line has no citation.\n"
        "- Qdrant stores embeddings. [C2]"
    )

    assert claims == [
        ("Audit history is stored in PostgreSQL.", "[C1]"),
        ("Qdrant stores embeddings.", "[C2]"),
    ]


def test_keyword_overlap_score() -> None:
    score = CitationValidationService._keyword_overlap_score(
        claim_text="Audit history is stored in PostgreSQL.",
        evidence_text="Audit history should be stored in PostgreSQL.",
    )

    assert score > 0.5


def test_calculate_validation_score_full_support() -> None:
    score = CitationValidationService._calculate_validation_score(
        citation_markers_found=["[C1]"],
        citations_provided_count=1,
        cited_claims_count=1,
        supported_claims_count=1,
    )

    assert score == 1.0


def test_validate_citation_markers_maps_to_provided_citation() -> None:
    service = CitationValidationService.__new__(CitationValidationService)
    chunk = _chunk()
    citation = Citation(citation_id="C1", chunk=chunk)

    results = service._validate_citation_markers(
        citation_markers_found=["[C1]"],
        citation_map={"C1": citation},
    )

    assert len(results) == 1
    assert results[0].citation_id == "C1"
    assert results[0].citation_marker == "[C1]"
    assert results[0].citation_provided is True
    assert results[0].chunk_id == chunk.chunk_id
    assert results[0].document_id == chunk.document_id


def test_validate_claims_marks_supported_claim() -> None:
    service = CitationValidationService.__new__(CitationValidationService)
    chunk = _chunk()
    citation = Citation(citation_id="C1", chunk=chunk)

    results = service._validate_claims(
        answer_text="- Audit history should be stored in PostgreSQL. [C1]",
        citation_map={"C1": citation},
    )

    assert len(results) == 1
    assert results[0].supported is True
    assert results[0].support_score >= 0.30
    assert results[0].citation_id == "C1"


def test_validate_claims_marks_missing_citation_as_unsupported() -> None:
    service = CitationValidationService.__new__(CitationValidationService)

    results = service._validate_claims(
        answer_text="- Audit history should be stored in PostgreSQL. [C9]",
        citation_map={},
    )

    assert len(results) == 1
    assert results[0].supported is False
    assert results[0].support_score == 0.0
    assert results[0].citation_id == "C9"
