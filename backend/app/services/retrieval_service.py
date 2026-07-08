from dataclasses import dataclass
from uuid import UUID

from rank_bm25 import BM25Okapi
from rapidfuzz import fuzz
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import DocumentChunk
from app.services.embedding_service import EmbeddingService
from app.services.vector_store_service import VectorStoreService
from app.utils.retrieval import clamp_score, normalize_scores, tokenize_for_retrieval
from app.utils.text import text_preview


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: UUID
    document_id: UUID
    chunk_index: int
    score: float
    text_preview: str
    chunk_text: str
    metadata: dict


class RetrievalService:
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStoreService()

    def search(
        self,
        query: str,
        top_k: int,
        document_id: UUID | None = None,
        retrieval_mode: str | None = None,
    ) -> list[RetrievedChunk]:
        mode = (retrieval_mode or self.settings.default_retrieval_mode).lower().strip()

        if mode == "vector":
            return self.vector_search(query=query, top_k=top_k, document_id=document_id)

        if mode == "bm25":
            return self.bm25_search(query=query, top_k=top_k, document_id=document_id)

        if mode == "fuzzy":
            return self.fuzzy_search(query=query, top_k=top_k, document_id=document_id)

        if mode == "hybrid":
            return self.hybrid_search(query=query, top_k=top_k, document_id=document_id)

        raise ValueError(f"Unsupported retrieval mode: {retrieval_mode}")

    def vector_search(
        self,
        query: str,
        top_k: int,
        document_id: UUID | None = None,
    ) -> list[RetrievedChunk]:
        query_vector = self.embedding_service.embed_query(query)
        hits = self.vector_store.search(
            query_vector=query_vector,
            top_k=top_k,
            document_id=document_id,
        )

        results: list[RetrievedChunk] = []

        for hit in hits:
            payload = hit.payload or {}
            chunk_id = payload.get("chunk_id")

            if not chunk_id:
                continue

            chunk = self.db.get(DocumentChunk, UUID(chunk_id))
            if chunk is None:
                continue

            results.append(
                self._build_retrieved_chunk(
                    chunk=chunk,
                    score=float(hit.score),
                    score_details={
                        "retrieval_mode": "vector",
                        "vector_score": float(hit.score),
                        "qdrant_point_id": str(hit.id),
                    },
                )
            )

        return results

    def bm25_search(
        self,
        query: str,
        top_k: int,
        document_id: UUID | None = None,
    ) -> list[RetrievedChunk]:
        chunks = self._load_candidate_chunks(document_id)

        if not chunks:
            return []

        tokenized_chunks = [tokenize_for_retrieval(chunk.chunk_text) for chunk in chunks]
        tokenized_query = tokenize_for_retrieval(query)

        if not tokenized_query:
            return []

        bm25 = BM25Okapi(tokenized_chunks)
        raw_scores = bm25.get_scores(tokenized_query)
        normalized_scores = normalize_scores(raw_scores)

        scored_chunks: list[tuple[DocumentChunk, float, float, str]] = []

        for chunk, normalized_score, raw_score, chunk_tokens in zip(
            chunks,
            normalized_scores,
            raw_scores,
            tokenized_chunks,
            strict=True,
        ):
            score = normalized_score
            score_source = "bm25"

            # BM25 can return zero on tiny corpora. Use keyword overlap as a safe fallback
            # so exact terms like "audit history" still retrieve relevant chunks locally.
            if score <= 0:
                score = self._keyword_overlap_score(tokenized_query, chunk_tokens)
                score_source = "keyword_overlap_fallback"

            if score > 0:
                scored_chunks.append((chunk, score, float(raw_score), score_source))

        scored_chunks.sort(key=lambda item: item[1], reverse=True)

        return [
            self._build_retrieved_chunk(
                chunk=chunk,
                score=score,
                score_details={
                    "retrieval_mode": "bm25",
                    "bm25_score": score,
                    "bm25_raw_score": raw_score,
                    "bm25_score_source": score_source,
                },
            )
            for chunk, score, raw_score, score_source in scored_chunks[:top_k]
        ]

    def fuzzy_search(
        self,
        query: str,
        top_k: int,
        document_id: UUID | None = None,
    ) -> list[RetrievedChunk]:
        chunks = self._load_candidate_chunks(document_id)

        scored_chunks: list[tuple[DocumentChunk, float]] = []

        for chunk in chunks:
            searchable_text = " ".join(
                part
                for part in [
                    chunk.section_title or "",
                    chunk.chunk_text,
                    " ".join(chunk.metadata_json.get("tags", [])),
                ]
                if part
            )

            score = fuzz.token_set_ratio(query, searchable_text) / 100

            if score > 0:
                scored_chunks.append((chunk, score))

        scored_chunks.sort(key=lambda item: item[1], reverse=True)

        return [
            self._build_retrieved_chunk(
                chunk=chunk,
                score=score,
                score_details={
                    "retrieval_mode": "fuzzy",
                    "fuzzy_score": score,
                },
            )
            for chunk, score in scored_chunks[:top_k]
        ]

    def hybrid_search(
        self,
        query: str,
        top_k: int,
        document_id: UUID | None = None,
    ) -> list[RetrievedChunk]:
        # Pull a wider candidate pool from each retriever, then merge and rerank.
        candidate_k = max(top_k * 3, 10)

        vector_results = self.vector_search(query=query, top_k=candidate_k, document_id=document_id)
        bm25_results = self.bm25_search(query=query, top_k=candidate_k, document_id=document_id)
        fuzzy_results = self.fuzzy_search(query=query, top_k=candidate_k, document_id=document_id)

        merged: dict[UUID, dict] = {}

        self._merge_results(
            merged=merged,
            results=vector_results,
            score_key="vector_score",
            weight=self.settings.vector_weight,
        )
        self._merge_results(
            merged=merged,
            results=bm25_results,
            score_key="bm25_score",
            weight=self.settings.bm25_weight,
        )
        self._merge_results(
            merged=merged,
            results=fuzzy_results,
            score_key="fuzzy_score",
            weight=self.settings.fuzzy_weight,
        )

        reranked = sorted(
            merged.values(),
            key=lambda item: item["combined_score"],
            reverse=True,
        )

        final_results: list[RetrievedChunk] = []

        for item in reranked[:top_k]:
            retrieved_chunk: RetrievedChunk = item["retrieved_chunk"]
            score_details = item["score_details"]
            score_details["retrieval_mode"] = "hybrid"
            score_details["combined_score"] = item["combined_score"]

            metadata = dict(retrieved_chunk.metadata)
            metadata["score_details"] = score_details

            final_results.append(
                RetrievedChunk(
                    chunk_id=retrieved_chunk.chunk_id,
                    document_id=retrieved_chunk.document_id,
                    chunk_index=retrieved_chunk.chunk_index,
                    score=clamp_score(item["combined_score"]),
                    text_preview=retrieved_chunk.text_preview,
                    chunk_text=retrieved_chunk.chunk_text,
                    metadata=metadata,
                )
            )

        return final_results

    @staticmethod
    def _merge_results(
        merged: dict[UUID, dict],
        results: list[RetrievedChunk],
        score_key: str,
        weight: float,
    ) -> None:
        for result in results:
            existing = merged.setdefault(
                result.chunk_id,
                {
                    "retrieved_chunk": result,
                    "combined_score": 0.0,
                    "score_details": {
                        "vector_score": 0.0,
                        "bm25_score": 0.0,
                        "fuzzy_score": 0.0,
                    },
                },
            )

            weighted_score = result.score * weight
            existing["combined_score"] += weighted_score
            existing["score_details"][score_key] = result.score

            source_details = result.metadata.get("score_details", {})
            if "qdrant_point_id" in source_details:
                existing["score_details"]["qdrant_point_id"] = source_details["qdrant_point_id"]

    def _load_candidate_chunks(self, document_id: UUID | None = None) -> list[DocumentChunk]:
        statement = select(DocumentChunk)

        if document_id is not None:
            statement = statement.where(DocumentChunk.document_id == document_id)

        statement = statement.order_by(DocumentChunk.created_at.desc())

        return list(self.db.scalars(statement).all())

    @staticmethod
    def _keyword_overlap_score(query_tokens: list[str], chunk_tokens: list[str]) -> float:
        if not query_tokens or not chunk_tokens:
            return 0.0

        query_set = set(query_tokens)
        chunk_set = set(chunk_tokens)

        overlap = query_set.intersection(chunk_set)

        if not overlap:
            return 0.0

        return len(overlap) / len(query_set)
    
    def _build_retrieved_chunk(
        self,
        chunk: DocumentChunk,
        score: float,
        score_details: dict,
    ) -> RetrievedChunk:
        metadata = {
            "page_number": chunk.page_number,
            "section_title": chunk.section_title,
            "metadata_json": chunk.metadata_json,
            "score_details": score_details,
        }

        return RetrievedChunk(
            chunk_id=chunk.id,
            document_id=chunk.document_id,
            chunk_index=chunk.chunk_index,
            score=clamp_score(score),
            text_preview=text_preview(chunk.chunk_text),
            chunk_text=chunk.chunk_text,
            metadata=metadata,
        )