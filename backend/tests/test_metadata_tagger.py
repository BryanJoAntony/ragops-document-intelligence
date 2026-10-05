from app.services.metadata_tagger import MetadataTaggingService


def test_detect_policy_document_type() -> None:
    tagger = MetadataTaggingService()

    doc_type = tagger.detect_document_type(
        filename="policy.txt",
        text="This policy describes compliance requirements and procedures.",
    )

    assert doc_type == "policy"


def test_generate_chunk_tags_detects_technical_and_audit() -> None:
    tagger = MetadataTaggingService()

    tags = tagger.generate_chunk_tags(
        text="The API stores audit history in PostgreSQL and uses Docker.",
    )

    assert "technical" in tags
    assert "audit" in tags