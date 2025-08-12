#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple migration bootstrap: create tables if not exist.
For production use Alembic; this provides a quick start.
"""

import logging
from database.db import ENGINE, Base
from database.models_sql import *  # noqa


logger = logging.getLogger(__name__)


def init_db():
    """Initialize DB schema robustly (idempotent).

    - First try normal metadata.create_all (checkfirst=True by default)
    - If anything fails (e.g., duplicate index/object), fall back to creating
      each table and its indexes individually with checkfirst=True.
    """
    try:
        Base.metadata.create_all(ENGINE)
        return
    except Exception as e:
        logger.warning(f"create_all failed, falling back to per-table creation: {e}")

    # Fallback: create tables one by one and then indexes
    try:
        # Ensure parent tables first (users, courses, purchases, receipts, audits)
        order = [
            "users",
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
                table.create(bind=ENGINE, checkfirst=True)
            except Exception as te:
                logger.warning(f"Table create skipped/failed for {table.name}: {te}")
        # Create remaining tables if any
        for table in Base.metadata.sorted_tables:
            if table.name in order:
                continue
            try:
                table.create(bind=ENGINE, checkfirst=True)
            except Exception as te:
                logger.warning(f"Table create skipped/failed for {table.name}: {te}")
        # Create indexes explicitly (checkfirst) — minimal explicit indexes left after model change
        for table in Base.metadata.sorted_tables:
            for idx in table.indexes:
                try:
                    idx.create(bind=ENGINE, checkfirst=True)
                except Exception as ie:
                    logger.warning(f"Index create skipped/failed for {idx.name}: {ie}")
    except Exception as e:
        logger.error(f"Fallback schema init failed: {e}")
        raise


if __name__ == "__main__":
    init_db()
    print("DB initialized.")
