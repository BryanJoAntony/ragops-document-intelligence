from uuid import uuid4

from qdrant_client.http.models import Filter

from app.schemas.query import QueryAskRequest, RetrievalFilters
from app.services.retrieval_service import RetrievalService
from app.services.vector_store_service import VectorStoreService


def test_retrieval_filters_has_filters_false_when_empty() -> None:
    filters = RetrievalFilters()

    assert filters.has_filters() is False


def test_retrieval_filters_has_filters_true_when_set() -> None:
    filters = RetrievalFilters(filename="sample.txt")

    assert filters.has_filters() is True


def test_query_request_merges_document_id_into_filters() -> None:
    document_id = uuid4()

    request = QueryAskRequest(
        question="Where should audit history be stored?",
        document_id=document_id,
    )

    assert request.filters is not None
    assert request.filters.document_id == document_id


def test_query_request_rejects_conflicting_document_ids() -> None:
    try:
        QueryAskRequest(
            question="Where should audit history be stored?",
            document_id=uuid4(),
            filters=RetrievalFilters(document_id=uuid4()),
        )
    except ValueError as exc:
        assert "document_id and filters.document_id must match" in str(exc)
    else:
        raise AssertionError("Expected conflicting document_id validation error")


def test_normalize_filters_removes_none_values() -> None:
    filters = RetrievalFilters(
        filename="policy.txt",
        language=None,
        parser_name="txt_parser",
    )

    normalized = RetrievalService._normalize_filters(filters=filters)

    assert normalized == {
        "filename": "policy.txt",
        "parser_name": "txt_parser",
    }


def test_normalize_filters_merges_document_id() -> None:
    document_id = uuid4()

    normalized = RetrievalService._normalize_filters(
        document_id=document_id,
        filters=RetrievalFilters(filename="policy.txt"),
    )

    assert normalized["document_id"] == document_id
    assert normalized["filename"] == "policy.txt"


def test_vector_store_build_query_filter_returns_none_without_filters() -> None:
    query_filter = VectorStoreService._build_query_filter()

    assert query_filter is None


def test_vector_store_build_query_filter_creates_qdrant_filter() -> None:
    document_id = uuid4()

    query_filter = VectorStoreService._build_query_filter(
        filters={
            "document_id": document_id,
            "filename": "policy.txt",
            "language": "en",
        }
    )

    assert isinstance(query_filter, Filter)
    assert len(query_filter.must) == 3
