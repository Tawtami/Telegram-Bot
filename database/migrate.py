#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple migration bootstrap: create tables if not exist.
For production use Alembic; this provides a quick start.
"""

import logging
from sqlalchemy import text

from database.db import ENGINE, Base
from database.models_sql import (
    Base,
    User,
    Course,
    Purchase,
    Receipt,
    PurchaseAudit,
    ProfileChange,
    QuizQuestion,
    QuizAttempt,
    UserStats,
    BannedUser,
)


logger = logging.getLogger(__name__)


def init_db():
    """Initialize DB schema robustly (idempotent, concurrency-safe on Postgres).

    Strategy:
    - Acquire a Postgres advisory lock (no-op for other DBs) to avoid race conditions
      when multiple app instances start concurrently.
    - Attempt normal `metadata.create_all` first.
    - If that fails, create tables individually in a stable order.
    - Perform lightweight, idempotent upgrades (e.g., BIGINT for telegram_user_id).
    """

    # SQLAlchemy dialect names for psycopg2 are like 'postgresql+psycopg2'
    # ENGINE.dialect.name can be MagicMock in tests; coerce to string safely
    try:
        dialect_name = str(getattr(ENGINE.dialect, 'name', ''))
    except Exception:
        dialect_name = ''
    is_postgres = dialect_name.startswith("postgresql")

    # Use a dedicated connection/transaction to serialize initialization on Postgres
    # Use a transactional connection so DDL changes are committed
    with ENGINE.begin() as conn:
        locked = False
        try:
            if is_postgres:
                # Arbitrary app-level lock id; must be constant across instances
                conn.execute(text("SELECT pg_advisory_lock(54193217)"))
                locked = True
        except Exception as e:
            logger.warning(f"Could not acquire advisory lock: {e}")

        try:
            try:
                Base.metadata.create_all(bind=conn)
            except Exception as e:
                try:
                    conn.rollback()
                except Exception:
                    pass
                logger.warning(f"create_all failed, falling back to per-table creation: {e}")
                _create_tables_individually(conn)

            # Run idempotent upgrades after ensuring tables exist
            try:
                _upgrade_schema_if_needed(conn)
            except Exception as ue:
                try:
                    conn.rollback()
                except Exception:
                    pass
                logger.warning(f"Schema upgrade check failed: {ue}")
        finally:
            # Always release the advisory lock if we acquired it
            if locked:
                try:
                    conn.execute(text("SELECT pg_advisory_unlock(54193217)"))
                except Exception:
                    pass


def _upgrade_schema_if_needed(conn):
    """Lightweight, idempotent upgrades for live DB.

    - Ensure tables exist (users, courses, purchases, receipts, purchase_audits, profile_changes)
    - Ensure users.telegram_user_id is BIGINT (for large Telegram IDs)
    """

    # 1) Ensure core tables exist (idempotent)
    try:
        name_to_table = {t.name: t for t in Base.metadata.sorted_tables}
        creation_order = [
            "users",
            "banned_users",
            "courses",
            "purchases",
            "receipts",
            "purchase_audits",
            "profile_changes",
            "quiz_questions",
            "quiz_attempts",
            "user_stats",
        ]
        for tname in creation_order:
            table = name_to_table.get(tname)
            if table is None:
                continue
            try:
                table.create(bind=conn, checkfirst=True)
            except Exception as te:
                try:
                    conn.rollback()
                except Exception:
                    pass
                logger.warning(f"Table create skipped/failed for {tname}: {te}")
    except Exception as e:
        logger.warning(f"Ensuring tables failed: {e}")

    # 2) Ensure BIGINT for users.telegram_user_id and purchases.admin_action_by
    try:
        dt_row = conn.execute(
            text(
                "SELECT data_type FROM information_schema.columns "
                "WHERE table_name='users' AND column_name='telegram_user_id'"
            )
        ).scalar()
        if dt_row and str(dt_row).lower() in ("integer", "int4"):
            try:
                # Use USING to be explicit and future-proof
                conn.execute(
                    text(
                        "ALTER TABLE users ALTER COLUMN telegram_user_id TYPE BIGINT USING telegram_user_id::bigint"
                    )
                )
                logger.info("Upgraded users.telegram_user_id to BIGINT")
            except Exception as e:
                try:
                    conn.rollback()
                except Exception:
                    pass
                logger.warning(f"Could not alter users.telegram_user_id to BIGINT: {e}")
    except Exception as e:
        logger.warning(f"Could not read/upgrade users.telegram_user_id column type: {e}")

    try:
        dt_row = conn.execute(
            text(
                "SELECT data_type FROM information_schema.columns "
                "WHERE table_name='purchases' AND column_name='admin_action_by'"
            )
        ).scalar()
        if dt_row and str(dt_row).lower() in ("integer", "int4"):
            try:
                conn.execute(
                    text(
                        "ALTER TABLE purchases ALTER COLUMN admin_action_by TYPE BIGINT USING admin_action_by::bigint"
                    )
                )
                logger.info("Upgraded purchases.admin_action_by to BIGINT")
            except Exception as e:
                try:
                    conn.rollback()
                except Exception:
                    pass
                logger.warning(f"Could not alter purchases.admin_action_by to BIGINT: {e}")
    except Exception as e:
        logger.warning(f"Could not read/upgrade purchases.admin_action_by column type: {e}")

    # 3) Fallback DDL for critical tables and column additions (Postgres)
    try:
        if str(getattr(ENGINE.dialect, 'name', '')).startswith("postgresql"):
            # Users: add plain PII columns if missing
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS first_name TEXT"))
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_name TEXT"))
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS phone TEXT"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_phone ON users(phone)"))

            # Purchases: ensure financial columns and receipt columns
            # Add financial columns to purchases if missing
            try:
                conn.execute(text("ALTER TABLE purchases ADD COLUMN IF NOT EXISTS amount INTEGER"))
            except Exception:
                try:
                    conn.rollback()
                except Exception:
                    pass
            try:
                conn.execute(
                    text("ALTER TABLE purchases ADD COLUMN IF NOT EXISTS discount INTEGER")
                )
            except Exception:
                try:
                    conn.rollback()
                except Exception:
                    pass
            try:
                conn.execute(
                    text(
                        "ALTER TABLE purchases ADD COLUMN IF NOT EXISTS payment_method VARCHAR(32)"
                    )
                )
            except Exception:
                try:
                    conn.rollback()
                except Exception:
                    pass
            try:
                conn.execute(
                    text(
                        "ALTER TABLE purchases ADD COLUMN IF NOT EXISTS transaction_id VARCHAR(128)"
                    )
                )
            except Exception:
                try:
                    conn.rollback()
                except Exception:
                    pass
            # Receipt columns inline (optional)
            try:
                conn.execute(text("ALTER TABLE purchases ADD COLUMN IF NOT EXISTS receipt_file_id VARCHAR(256)"))
                conn.execute(text("ALTER TABLE purchases ADD COLUMN IF NOT EXISTS receipt_mime VARCHAR(64)"))
                conn.execute(text("ALTER TABLE purchases ADD COLUMN IF NOT EXISTS receipt_uploaded_at TIMESTAMP"))
                conn.execute(text("ALTER TABLE purchases ADD COLUMN IF NOT EXISTS receipt_notes VARCHAR(1024)"))
            except Exception:
                try:
                    conn.rollback()
                except Exception:
                    pass
            conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS banned_users (
                      id SERIAL PRIMARY KEY,
                      telegram_user_id BIGINT UNIQUE,
                      created_at TIMESTAMP DEFAULT NOW()
                    )
                    """
                )
            )
            conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS quiz_questions (
                      id SERIAL PRIMARY KEY,
                      grade VARCHAR(32),
                      difficulty INTEGER DEFAULT 1,
                      question_text VARCHAR(2048),
                      options JSON,
                      correct_index INTEGER,
                      created_at TIMESTAMP DEFAULT NOW()
                    )
                    """
                )
            )
            conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS quiz_attempts (
                      id SERIAL PRIMARY KEY,
                      user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                      question_id INTEGER REFERENCES quiz_questions(id) ON DELETE CASCADE,
                      selected_index INTEGER,
                      correct INTEGER DEFAULT 0,
                      created_at TIMESTAMP DEFAULT NOW()
                    )
                    """
                )
            )
            conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS user_stats (
                      id SERIAL PRIMARY KEY,
                      user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
                      total_attempts INTEGER DEFAULT 0,
                      total_correct INTEGER DEFAULT 0,
                      streak_days INTEGER DEFAULT 0,
                      last_attempt_date VARCHAR(10),
                      points INTEGER DEFAULT 0,
                      last_daily_award_date VARCHAR(10),
                      updated_at TIMESTAMP DEFAULT NOW()
                    )
                    """
                )
            )
    except Exception as e:
        logger.warning(f"Fallback DDL create (critical tables) failed: {e}")
    # 3) Create recommended indexes if missing (Postgres)
    try:
        if str(getattr(ENGINE.dialect, 'name', '')).startswith("postgresql"):
            # Users demography indexes
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_province ON users(province)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_city ON users(city)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_grade ON users(grade)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_field ON users(field_of_study)"))
    except Exception as e:
        logger.warning(f"Creating optional indexes failed: {e}")


def _create_tables_individually(conn):
    """Create tables one by one and then indexes with checkfirst=True."""
    # Ensure parent tables first (users, courses, purchases, receipts, audits)
    order = [
        "users",
        "banned_users",
        "courses",
        "purchases",
        "receipts",
        "purchase_audits",
        "profile_changes",
    ]
    name_to_table = {t.name: t for t in Base.metadata.sorted_tables}
    for tname in order:
        table = name_to_table.get(tname)
        if not table:
            continue
        try:
            table.create(bind=conn, checkfirst=True)
        except Exception as te:
            try:
                conn.rollback()
            except Exception:
                pass
            logger.warning(f"Table create skipped/failed for {table.name}: {te}")
    # Create remaining tables if any
    for table in Base.metadata.sorted_tables:
        if table.name in order:
            continue
        try:
            table.create(bind=conn, checkfirst=True)
        except Exception as te:
            try:
                conn.rollback()
            except Exception:
                pass
            logger.warning(f"Table create skipped/failed for {table.name}: {te}")
    # Create indexes explicitly (checkfirst). This may be a no-op if the tables
    # were just created above.
    for table in Base.metadata.sorted_tables:
        for idx in table.indexes:
            try:
                idx.create(bind=conn, checkfirst=True)
            except Exception as ie:
                try:
                    conn.rollback()
                except Exception:
                    pass
                logger.warning(f"Index create skipped/failed for {idx.name}: {ie}")

    # Add constraints/checks that SQLAlchemy might not emit automatically
    try:
        # Enforce decision attribution when not pending
        conn.execute(
            text(
                """
                DO $$
                BEGIN
                  IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint WHERE conname = 'ck_purchases_decision_fields'
                  ) THEN
                    ALTER TABLE purchases
                      ADD CONSTRAINT ck_purchases_decision_fields
                      CHECK (
                        status = 'pending' OR (admin_action_by IS NOT NULL AND admin_action_at IS NOT NULL)
                      );
                  END IF;
                END$$;
                """
            )
        )
    except Exception as e:
        logger.warning(f"Check constraint create skipped/failed: {e}")


if __name__ == "__main__":
    init_db()
    logger.info("DB initialized.")
