"""bootstrap initial schema

Revision ID: 0001_bootstrap
Revises: 
Create Date: 2025-08-12 22:25:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0001_bootstrap"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # users
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=False),
        sa.Column("first_name_enc", sa.String(length=512), nullable=False),
        sa.Column("last_name_enc", sa.String(length=512), nullable=False),
        sa.Column("phone_enc", sa.String(length=512), nullable=True),
        sa.Column("province", sa.String(length=128), nullable=True),
        sa.Column("city", sa.String(length=128), nullable=True),
        sa.Column("grade", sa.String(length=32), nullable=True),
        sa.Column("field_of_study", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_unique_constraint("uq_users_telegram", "users", ["telegram_user_id"])
    op.create_index("ix_users_telegram", "users", ["telegram_user_id"])
    op.create_index("ix_users_province", "users", ["province"])
    op.create_index("ix_users_city", "users", ["city"])
    op.create_index("ix_users_grade", "users", ["grade"])
    op.create_index("ix_users_field", "users", ["field_of_study"])

    # banned_users
    op.create_table(
        "banned_users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_unique_constraint(
        "uq_banned_telegram", "banned_users", ["telegram_user_id"]
    )
    op.create_index("ix_banned_telegram", "banned_users", ["telegram_user_id"])

    # profile_changes
    op.create_table(
        "profile_changes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("field_name", sa.String(length=64), nullable=False),
        sa.Column("old_value_enc", sa.String(length=1024), nullable=False),
        sa.Column("new_value_enc", sa.String(length=1024), nullable=False),
        sa.Column("changed_by", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_profile_changes_timestamp", "profile_changes", ["timestamp"]
    )

    # purchases
    op.create_table(
        "purchases",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("product_type", sa.String(length=16), nullable=False),
        sa.Column("product_id", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("admin_action_by", sa.BigInteger(), nullable=True),
        sa.Column("admin_action_at", sa.DateTime(), nullable=True),
        sa.Column("notes_enc", sa.String(length=2048), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_unique_constraint(
        "uq_user_product", "purchases", ["user_id", "product_type", "product_id"]
    )
    op.create_index(
        "ix_purchases_user_status", "purchases", ["user_id", "status"]
    )
    op.create_index("ix_purchases_created_at", "purchases", ["created_at"])

    # receipts
    op.create_table(
        "receipts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("purchase_id", sa.Integer(), nullable=False),
        sa.Column("telegram_file_id", sa.String(length=256), nullable=False),
        sa.Column("file_unique_id", sa.String(length=128), nullable=False),
        sa.Column("submitted_at", sa.DateTime(), nullable=True),
        sa.Column("duplicate_checked", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["purchase_id"], ["purchases.id"], ondelete="CASCADE"
        ),
    )
    op.create_unique_constraint(
        "uq_file_unique_id", "receipts", ["file_unique_id"]
    )
    op.create_index("ix_receipts_purchase_id", "receipts", ["purchase_id"])
    op.create_index("ix_receipts_submitted_at", "receipts", ["submitted_at"])

    # purchase_audits
    op.create_table(
        "purchase_audits",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("purchase_id", sa.Integer(), nullable=False),
        sa.Column("admin_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=16), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
    )
    op.create_index(
        "ix_purchase_audits_purchase_id", "purchase_audits", ["purchase_id"]
    )

    # quiz_questions
    op.create_table(
        "quiz_questions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("grade", sa.String(length=32), nullable=True),
        sa.Column("difficulty", sa.Integer(), nullable=True),
        sa.Column("question_text", sa.String(length=2048), nullable=False),
        sa.Column("options", sa.JSON(), nullable=True),
        sa.Column("correct_index", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_quiz_grade_diff", "quiz_questions", ["grade", "difficulty"])

    # quiz_attempts
    op.create_table(
        "quiz_attempts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("selected_index", sa.Integer(), nullable=False),
        sa.Column("correct", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["question_id"], ["quiz_questions.id"], ondelete="CASCADE"
        ),
    )
    op.create_index("ix_quiz_attempts_user", "quiz_attempts", ["user_id"])
    op.create_index("ix_quiz_attempts_question", "quiz_attempts", ["question_id"])
    op.create_index("ix_quiz_attempts_created_at", "quiz_attempts", ["created_at"])

    # user_stats
    op.create_table(
        "user_stats",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False, unique=True),
        sa.Column("total_attempts", sa.Integer(), nullable=True),
        sa.Column("total_correct", sa.Integer(), nullable=True),
        sa.Column("streak_days", sa.Integer(), nullable=True),
        sa.Column("last_attempt_date", sa.String(length=10), nullable=True),
        sa.Column("points", sa.Integer(), nullable=True),
        sa.Column("last_daily_award_date", sa.String(length=10), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_user_stats_user", "user_stats", ["user_id"])
    op.create_index("ix_user_stats_points", "user_stats", ["points"])


def downgrade() -> None:
    op.drop_table("user_stats")
    op.drop_table("quiz_attempts")
    op.drop_index("ix_quiz_grade_diff", table_name="quiz_questions")
    op.drop_table("quiz_questions")
    op.drop_table("purchase_audits")
    op.drop_table("receipts")
    op.drop_table("purchases")
    op.drop_table("profile_changes")
    op.drop_table("banned_users")
    op.drop_table("users")


