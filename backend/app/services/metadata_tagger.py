from pathlib import Path


class MetadataTaggingService:
    def detect_document_type(self, filename: str, text: str) -> str:
        haystack = f"{filename} {text[:3000]}".lower()

        rules = [
            ("invoice", ["invoice", "amount due", "bill to", "tax invoice"]),
            ("contract", ["agreement", "contract", "termination", "party", "obligation"]),
            ("policy", ["policy", "procedure", "guideline", "compliance"]),
            ("resume", ["experience", "education", "skills", "projects"]),
            ("manual", ["manual", "instructions", "troubleshooting", "installation"]),
            ("report", ["summary", "analysis", "findings", "recommendation"]),
        ]

        for document_type, keywords in rules:
            if any(keyword in haystack for keyword in keywords):
                return document_type

        suffix = Path(filename).suffix.lower().replace(".", "")
        return f"{suffix}_document" if suffix else "unknown"

    def detect_language(self, text: str) -> str:
        # Simple v1 heuristic. A language detection library can replace this later.
        return "en" if text.strip() else "unknown"

    def generate_document_tags(self, filename: str, text: str) -> list[str]:
        haystack = f"{filename} {text[:5000]}".lower()
        tags: set[str] = set()

        keyword_tags = {
            "invoice": ["invoice", "amount due", "payment"],
            "contract": ["contract", "agreement", "clause", "termination"],
            "policy": ["policy", "procedure", "compliance", "guideline"],
            "rag": ["rag", "retrieval", "chunk", "embedding", "vector"],
            "storage": ["storage", "upload", "file", "sha-256", "hash"],
            "security": ["security", "pii", "sensitive", "authentication"],
            "evaluation": ["evaluation", "evaluator", "groundedness", "hallucination"],
            "operations": ["monitoring", "audit", "logging", "status"],
        }

        for tag, keywords in keyword_tags.items():
            if any(keyword in haystack for keyword in keywords):
                tags.add(tag)

        detected_type = self.detect_document_type(filename, text)
        if detected_type != "unknown":
            tags.add(detected_type)

        return sorted(tags)

    def generate_chunk_tags(self, text: str, section_title: str | None = None) -> list[str]:
        haystack = f"{section_title or ''} {text}".lower()
        tags: set[str] = set()

        keyword_tags = {
            "overview": ["overview", "summary", "introduction"],
            "requirements": ["requirement", "must", "should", "shall"],
            "payment": ["payment", "invoice", "amount", "fee"],
            "legal": ["agreement", "contract", "termination", "liability"],
            "technical": ["api", "database", "docker", "redis", "qdrant", "postgres"],
            "retrieval": ["retrieval", "rag", "chunk", "embedding", "vector"],
            "audit": ["audit", "logging", "trace", "history"],
            "risk": ["risk", "failure", "error", "fallback"],
        }

        for tag, keywords in keyword_tags.items():
            if any(keyword in haystack for keyword in keywords):
                tags.add(tag)

        return sorted(tags)