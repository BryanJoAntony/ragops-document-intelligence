"""add document metadata fields

Revision ID: 0003_doc_metadata
Revises: 0002_add_document_storage_fields
Create Date: 2026-06-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_doc_metadata"
down_revision: str | None = "0002_add_document_storage_fields"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column(
            "generated_tags",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column("documents", sa.Column("detected_document_type", sa.String(length=120), nullable=True))
    op.add_column("documents", sa.Column("language", sa.String(length=40), nullable=True))
    op.add_column("documents", sa.Column("parser_name", sa.String(length=120), nullable=True))
    op.add_column("documents", sa.Column("parsed_at", sa.DateTime(timezone=True), nullable=True))

    op.create_index("ix_documents_detected_document_type", "documents", ["detected_document_type"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_documents_detected_document_type", table_name="documents")
    op.drop_column("documents", "parsed_at")
    op.drop_column("documents", "parser_name")
    op.drop_column("documents", "language")
    op.drop_column("documents", "detected_document_type")
    op.drop_column("documents", "generated_tags")