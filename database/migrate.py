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
        for table in Base.metadata.sorted_tables:
            try:
                table.create(bind=ENGINE, checkfirst=True)
            except Exception as te:
                logger.warning(f"Table create skipped/failed for {table.name}: {te}")
        # Create indexes explicitly (checkfirst)
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
