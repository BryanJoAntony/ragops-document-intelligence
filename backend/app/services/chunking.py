from dataclasses import dataclass

from app.services.document_parser import ParsedDocument
from app.utils.text import estimate_tokens, normalize_whitespace, text_preview


@dataclass(frozen=True)
class TextChunk:
    chunk_index: int
    chunk_text: str
    page_number: int | None
    section_title: str | None
    token_estimate: int
    metadata: dict


class ChunkingService:
    def __init__(self, max_chars: int = 1400, overlap_chars: int = 150) -> None:
        self.max_chars = max_chars
        self.overlap_chars = overlap_chars

    def chunk_document(self, parsed_document: ParsedDocument) -> list[TextChunk]:
        chunks: list[TextChunk] = []
        chunk_index = 0

        for page in parsed_document.pages:
            page_chunks = self._chunk_page_text(page.text)

            for chunk_text in page_chunks:
                section_title = self._detect_section_title(chunk_text)

                chunks.append(
                    TextChunk(
                        chunk_index=chunk_index,
                        chunk_text=chunk_text,
                        page_number=page.page_number,
                        section_title=section_title,
                        token_estimate=estimate_tokens(chunk_text),
                        metadata={
                            "parser_name": parsed_document.parser_name,
                            "text_preview": text_preview(chunk_text),
                            "chunking_strategy": "paragraph_window_v1",
                        },
                    )
                )
                chunk_index += 1

        return chunks

    def _chunk_page_text(self, text: str) -> list[str]:
        text = normalize_whitespace(text)
        if not text:
            return []

        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        chunks: list[str] = []
        current = ""

        for paragraph in paragraphs:
            if not current:
                current = paragraph
                continue

            candidate = f"{current}\n\n{paragraph}"

            if len(candidate) <= self.max_chars:
                current = candidate
            else:
                chunks.extend(self._split_large_text(current))
                current = self._with_overlap(current, paragraph)

        if current:
            chunks.extend(self._split_large_text(current))

        return [normalize_whitespace(chunk) for chunk in chunks if normalize_whitespace(chunk)]

    def _split_large_text(self, text: str) -> list[str]:
        if len(text) <= self.max_chars:
            return [text]

        chunks: list[str] = []
        start = 0

        while start < len(text):
            end = start + self.max_chars
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            if end >= len(text):
                break

            start = max(0, end - self.overlap_chars)

        return chunks

    def _with_overlap(self, previous_text: str, next_paragraph: str) -> str:
        overlap = previous_text[-self.overlap_chars :].strip()
        if not overlap:
            return next_paragraph
        return f"{overlap}\n\n{next_paragraph}"

    @staticmethod
    def _detect_section_title(chunk_text: str) -> str | None:
        first_line = chunk_text.splitlines()[0].strip()

        if len(first_line) <= 80 and not first_line.endswith("."):
            return first_line

        return None