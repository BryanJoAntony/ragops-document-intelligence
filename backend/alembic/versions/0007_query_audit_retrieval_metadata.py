"""add query audit retrieval metadata

Revision ID: 0007_query_audit_meta
Revises: 0006_async_jobs
Create Date: 2026-08-03
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0007_query_audit_meta"
down_revision = "0006_async_jobs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "query_audits",
        sa.Column("retrieval_mode", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "query_audits",
        sa.Column("query_filters", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("query_audits", "query_filters")
    op.drop_column("query_audits", "retrieval_mode")

