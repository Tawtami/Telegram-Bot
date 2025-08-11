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
        return url
    # Fallback to SQLite for development
    return "sqlite:///data/app.db"


ENGINE = create_engine(_build_db_url(), pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=ENGINE, autoflush=False, autocommit=False, expire_on_commit=False)


@contextmanager
def session_scope() -> Generator:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


