#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database initialization and session management using SQLAlchemy 2.0
Supports PostgreSQL via DATABASE_URL; falls back to SQLite if not provided.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase


class Base(DeclarativeBase):
    pass


def _build_db_url() -> str:
    url = os.getenv("DATABASE_URL", "").strip()
    if url:
        # Normalize to psycopg v3 (binary) driver if not explicitly specified
        # e.g., 'postgres://...' or 'postgresql://...' -> 'postgresql+psycopg_binary://...'
        lowered = url.lower()
        if (
            lowered.startswith("postgres://") or lowered.startswith("postgresql://")
        ) and "+" not in url:
            return url.replace("postgres://", "postgresql+psycopg_binary://").replace(
                "postgresql://", "postgresql+psycopg_binary://"
            )
        return url
    # Fallback to SQLite for development
    return "sqlite:///data/app.db"


ENGINE = create_engine(_build_db_url(), pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(
    bind=ENGINE, autoflush=False, autocommit=False, expire_on_commit=False
)

# Lazy, idempotent schema initialization for test and script contexts
# Avoids circular imports by importing migrate only on demand.
_SCHEMA_INIT_DONE = False


def _ensure_schema_initialized() -> None:
    global _SCHEMA_INIT_DONE
    if _SCHEMA_INIT_DONE:
        return
    try:
        # Probe for a core table; if missing, run initializer
        with ENGINE.connect() as conn:
            try:
                conn.exec_driver_sql("SELECT 1 FROM users LIMIT 1")
                _SCHEMA_INIT_DONE = True
                return
            except Exception:
                pass
        # Run initializer (idempotent and concurrency-safe on Postgres)
        try:
            from database.migrate import init_db  # local import to avoid cycles

            init_db()
        except Exception:
            # Best-effort: leave to caller if initialization fails here
            pass
        _SCHEMA_INIT_DONE = True
    except Exception:
        # As a last resort, mark as done to prevent infinite attempts
        _SCHEMA_INIT_DONE = True


@contextmanager
def session_scope() -> Generator:
    # Ensure schema exists at first use in tests/CLI contexts
    _ensure_schema_initialized()
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
