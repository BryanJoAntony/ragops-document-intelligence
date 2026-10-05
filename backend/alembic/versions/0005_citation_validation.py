"""add citation validation results

Revision ID: 0005_citation_validation
Revises: 0004_eval_tables
Create Date: 2026-07-31
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "0005_citation_validation"
down_revision: Union[str, None] = "0004_eval_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "citation_validation_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("request_id", sa.String(length=100), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer_text", sa.Text(), nullable=False),
        sa.Column("citation_markers_found", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("citations_provided_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cited_claims_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("supported_claims_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("unsupported_claims_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("validation_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("validation_details", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_index(
        "ix_citation_validation_results_request_id",
        "citation_validation_results",
        ["request_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_citation_validation_results_request_id",
        table_name="citation_validation_results",
    )
    op.drop_table("citation_validation_results")
