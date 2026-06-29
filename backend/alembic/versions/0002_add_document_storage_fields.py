"""add document storage fields

Revision ID: 0002_add_document_storage_fields
Revises: 0001_create_core_tables
Create Date: 2026-06-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_add_document_storage_fields"
down_revision: str | None = "0001_create_core_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("storage_backend", sa.String(length=40), nullable=True))
    op.add_column("documents", sa.Column("storage_path", sa.String(length=1000), nullable=True))
    op.add_column("documents", sa.Column("storage_public_url", sa.String(length=1000), nullable=True))
    op.create_index("ix_documents_storage_backend", "documents", ["storage_backend"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_documents_storage_backend", table_name="documents")
    op.drop_column("documents", "storage_public_url")
    op.drop_column("documents", "storage_path")
    op.drop_column("documents", "storage_backend")