from uuid import UUID

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, FieldCondition, Filter, MatchValue, PointStruct, VectorParams

from app.core.config import get_settings


class VectorStoreService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = QdrantClient(url=self.settings.qdrant_url, timeout=10)
        self.collection_name = self.settings.qdrant_collection_name

    def ensure_collection(self) -> None:
        collections = self.client.get_collections().collections
        existing_names = {collection.name for collection in collections}

        if self.collection_name in existing_names:
            return

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=self.settings.embedding_dimension,
                distance=Distance.COSINE,
            ),
        )

    def upsert_chunk_vectors(
        self,
        points: list[tuple[str, list[float], dict]],
    ) -> None:
        if not points:
            return

        self.ensure_collection()

        qdrant_points = [
            PointStruct(
                id=point_id,
                vector=vector,
                payload=payload,
            )
            for point_id, vector, payload in points
        ]

        self.client.upsert(
            collection_name=self.collection_name,
            points=qdrant_points,
        )

    def search(
        self,
        query_vector: list[float],
        top_k: int,
        document_id: UUID | None = None,
        filters: dict | None = None,
    ) -> list:
        self.ensure_collection()

        query_filter = self._build_query_filter(
            document_id=document_id,
            filters=filters,
        )

        return self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            query_filter=query_filter,
            limit=top_k,
        )

    @staticmethod
    def _build_query_filter(
        document_id: UUID | None = None,
        filters: dict | None = None,
    ) -> Filter | None:
        must_conditions = []

        effective_filters = dict(filters or {})

        if document_id is not None:
            effective_filters["document_id"] = str(document_id)

        supported_payload_fields = {
            "document_id": "document_id",
            "workspace_id": "workspace_id",
            "filename": "filename",
            "language": "language",
            "parser_name": "parser_name",
            "document_type": "document_type",
        }

        for filter_key, payload_key in supported_payload_fields.items():
            value = effective_filters.get(filter_key)

            if value is None:
                continue

            must_conditions.append(
                FieldCondition(
                    key=payload_key,
                    match=MatchValue(value=str(value)),
                )
            )

        if not must_conditions:
            return None

        return Filter(must=must_conditions)
