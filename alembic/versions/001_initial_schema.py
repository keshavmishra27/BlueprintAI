"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-05-20
"""

from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "assessment_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_name", sa.String(), nullable=False),
        sa.Column("domains", sa.JSON(), nullable=False),
        sa.Column("questions_json", sa.JSON(), nullable=False),
        sa.Column("scores", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(), server_default="active"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "repo_analyses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_name", sa.String(), nullable=False),
        sa.Column("github_url", sa.String(), nullable=False),
        sa.Column("result_json", sa.JSON(), nullable=False),
        sa.Column("static_analysis_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "idea_validations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("idea_text", sa.Text(), nullable=False),
        sa.Column("check_result_json", sa.JSON(), nullable=True),
        sa.Column("refine_result_json", sa.JSON(), nullable=True),
        sa.Column("search_sources_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "swot_analyses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("subject_name", sa.String(), nullable=False),
        sa.Column("subject_type", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("result_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )


def downgrade():
    op.drop_table("swot_analyses")
    op.drop_table("idea_validations")
    op.drop_table("repo_analyses")
    op.drop_table("assessment_sessions")
