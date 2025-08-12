#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple migration bootstrap: create tables if not exist.
For production use Alembic; this provides a quick start.
"""

import logging
from sqlalchemy import text

from database.db import ENGINE, Base
from database.models_sql import *  # noqa


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

    is_postgres = ENGINE.dialect.name == "postgresql"

    # Use a dedicated connection/transaction to serialize initialization on Postgres
    with ENGINE.connect() as conn:
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
                logger.warning(
                    f"create_all failed, falling back to per-table creation: {e}"
                )
                _create_tables_individually(conn)

            # Run idempotent upgrades after ensuring tables exist
            try:
                _upgrade_schema_if_needed(conn)
            except Exception as ue:
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
        ]
        for tname in creation_order:
            table = name_to_table.get(tname)
            if table is None:
                continue
            try:
                table.create(bind=conn, checkfirst=True)
            except Exception as te:
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
                logger.warning(f"Could not alter users.telegram_user_id to BIGINT: {e}")
    except Exception as e:
        logger.warning(
            f"Could not read/upgrade users.telegram_user_id column type: {e}"
        )

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
                logger.warning(
                    f"Could not alter purchases.admin_action_by to BIGINT: {e}"
                )
    except Exception as e:
        logger.warning(
            f"Could not read/upgrade purchases.admin_action_by column type: {e}"
        )


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
            logger.warning(f"Table create skipped/failed for {table.name}: {te}")
    # Create remaining tables if any
    for table in Base.metadata.sorted_tables:
        if table.name in order:
            continue
        try:
            table.create(bind=conn, checkfirst=True)
        except Exception as te:
            logger.warning(f"Table create skipped/failed for {table.name}: {te}")
    # Create indexes explicitly (checkfirst). This may be a no-op if the tables
    # were just created above.
    for table in Base.metadata.sorted_tables:
        for idx in table.indexes:
            try:
                idx.create(bind=conn, checkfirst=True)
            except Exception as ie:
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
    print("DB initialized.")
