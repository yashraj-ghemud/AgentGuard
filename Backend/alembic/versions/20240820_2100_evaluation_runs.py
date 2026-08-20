"""Add durable evaluation run history.

Revision ID: 20240820_2100
Revises: 20240818_2000
Create Date: 2024-08-20 21:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20240820_2100"
down_revision = "20240818_2000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "evaluation_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("execution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("evaluation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("scenario_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("passed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("failure_type", sa.String(64), nullable=True),
        sa.Column("severity", sa.String(32), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("checks", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("output_data", postgresql.JSONB(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.UniqueConstraint("execution_id", name="uq_evaluation_runs_execution_id"),
        sa.UniqueConstraint("evaluation_id", name="uq_evaluation_runs_evaluation_id"),
    )
    op.create_index("idx_evaluation_runs_agent_id", "evaluation_runs", ["agent_id"])
    op.create_index("idx_evaluation_runs_agent_version_id", "evaluation_runs", ["agent_version_id"])
    op.create_index("idx_evaluation_runs_scenario_id", "evaluation_runs", ["scenario_id"])
    op.create_index("idx_evaluation_runs_created_at", "evaluation_runs", ["created_at"])
    op.create_index("idx_evaluation_runs_failure_type", "evaluation_runs", ["failure_type"])


def downgrade() -> None:
    op.drop_index("idx_evaluation_runs_failure_type", table_name="evaluation_runs")
    op.drop_index("idx_evaluation_runs_created_at", table_name="evaluation_runs")
    op.drop_index("idx_evaluation_runs_scenario_id", table_name="evaluation_runs")
    op.drop_index("idx_evaluation_runs_agent_version_id", table_name="evaluation_runs")
    op.drop_index("idx_evaluation_runs_agent_id", table_name="evaluation_runs")
    op.drop_table("evaluation_runs")
