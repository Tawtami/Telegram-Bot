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

from sqlalchemy import create_engine, text
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


_db_url = _build_db_url()
is_postgres = _db_url.startswith("postgresql+") or _db_url.startswith("postgresql://")
ENGINE = create_engine(
    _db_url,
    pool_pre_ping=True,
    future=True,
    pool_size=int(os.getenv("DB_POOL_SIZE", "20")),
    max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "30")),
    pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "300")),
)
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
        # Probe for core tables; if missing, run initializer
        with ENGINE.connect() as conn:
            # Apply a conservative statement timeout on Postgres connections (server-side)
            try:
                if is_postgres:
                    conn.execute(text("SET statement_timeout TO 8000"))
            except Exception:
                pass
            try:
                conn.exec_driver_sql("SELECT 1 FROM users LIMIT 1")
                try:
                    conn.exec_driver_sql("SELECT 1 FROM banned_users LIMIT 1")
                except Exception:
                    # missing banned_users: run init
                    raise
                # Probe learning tables (if any missing, trigger init)
                try:
                    conn.exec_driver_sql("SELECT 1 FROM quiz_questions LIMIT 1")
                    conn.exec_driver_sql("SELECT 1 FROM quiz_attempts LIMIT 1")
                    conn.exec_driver_sql("SELECT 1 FROM user_stats LIMIT 1")
                except Exception:
                    raise
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
