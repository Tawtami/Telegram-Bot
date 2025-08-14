#!/usr/bin/env python3
"""
Tests for database connection and initialization functionality.
"""

import pytest
import os
from unittest.mock import patch, MagicMock
from database.db import _build_db_url, is_postgres, ENGINE, SessionLocal


def test_build_db_url_with_postgres():
    """Test database URL building with PostgreSQL."""
    with patch.dict(os.environ, {'DATABASE_URL': 'postgres://user:pass@host/db'}):
        url = _build_db_url()
        assert url == 'postgresql+psycopg2://user:pass@host/db'


def test_build_db_url_with_postgresql():
    """Test database URL building with postgresql://."""
    with patch.dict(os.environ, {'DATABASE_URL': 'postgresql://user:pass@host/db'}):
        url = _build_db_url()
        assert url == 'postgresql+psycopg2://user:pass@host/db'


def test_build_db_url_with_existing_driver():
    """Test database URL building with existing driver specification."""
    with patch.dict(os.environ, {'DATABASE_URL': 'postgresql+psycopg2://user:pass@host/db'}):
        url = _build_db_url()
        assert url == 'postgresql+psycopg2://user:pass@host/db'


def test_build_db_url_fallback():
    """Test database URL fallback when DATABASE_URL is not set."""
    with patch.dict(os.environ, {}, clear=True):
        url = _build_db_url()
        assert url == 'sqlite:///data/app.db'


def test_build_db_url_empty_string():
    """Test database URL building with empty string."""
    with patch.dict(os.environ, {'DATABASE_URL': ''}):
        url = _build_db_url()
        assert url == 'sqlite:///data/app.db'


def test_build_db_url_whitespace():
    """Test database URL building with whitespace."""
    with patch.dict(os.environ, {'DATABASE_URL': '  postgres://user:pass@host/db  '}):
        url = _build_db_url()
        assert url == 'postgresql+psycopg2://user:pass@host/db'


def test_is_postgres_detection():
    """Test PostgreSQL detection logic."""
    from database.db import _is_postgres_url

    # Test with PostgreSQL URL
    assert _is_postgres_url('postgresql://user:pass@host/db') is True
    assert _is_postgres_url('postgresql+psycopg2://user:pass@host/db') is True
    assert _is_postgres_url('postgres://user:pass@host/db') is False  # This gets converted

    # Test with SQLite URL
    assert _is_postgres_url('sqlite:///data/app.db') is False
    assert _is_postgres_url('mysql://user:pass@host/db') is False


def test_session_local_creation():
    """Test that SessionLocal can be created."""
    assert SessionLocal is not None
    assert callable(SessionLocal)


def test_engine_creation_postgres():
    """Test engine creation for PostgreSQL."""
    from database.db import ENGINE

    # Just verify that the engine exists and has expected attributes
    assert ENGINE is not None
    assert hasattr(ENGINE, 'dialect')
    assert hasattr(ENGINE, 'connect')


def test_engine_creation_sqlite():
    """Test engine creation for SQLite."""
    from database.db import ENGINE

    # Just verify that the engine exists and has expected attributes
    assert ENGINE is not None
    assert hasattr(ENGINE, 'dialect')
    assert hasattr(ENGINE, 'connect')


def test_database_imports():
    """Test that database module can be imported without errors."""
    try:
        from database import Base, ENGINE, SessionLocal, session_scope

        assert Base is not None
        assert ENGINE is not None
        assert SessionLocal is not None
        assert session_scope is not None
    except ImportError as e:
        pytest.fail(f"Database module import failed: {e}")


def test_base_class_structure():
    """Test that Base class has expected structure."""
    from database.db import Base

    # Base is a DeclarativeBase, so it should have these attributes
    assert hasattr(Base, 'metadata')
    assert hasattr(Base, 'registry')
    # These are the standard attributes of SQLAlchemy 2.0 DeclarativeBase
    # __table__ is only present on actual model instances, not the base class


def test_session_scope_context_manager():
    """Test session_scope context manager."""
    from database.db import session_scope

    # Mock the session
    mock_session = MagicMock()

    with patch('database.db.SessionLocal', return_value=mock_session):
        with session_scope() as session:
            assert session == mock_session

        # Check that session was closed
        mock_session.close.assert_called_once()


def test_database_metadata():
    """Test that database metadata is properly configured."""
    from database import alembic_metadata

    metadata = alembic_metadata()
    assert metadata is not None

    # Check that tables are defined
    assert len(metadata.tables) > 0

    # Check for expected table names
    table_names = list(metadata.tables.keys())
    expected_tables = ['users', 'courses', 'purchases']

    for expected_table in expected_tables:
        assert expected_table in table_names, f"Expected table {expected_table} not found"


def test_database_connection_parameters():
    """Test database connection parameters are properly set."""
    # Test environment variable handling
    test_url = 'postgresql://test:test@localhost/testdb'

    with patch.dict(os.environ, {'DATABASE_URL': test_url}):
        url = _build_db_url()
        assert 'psycopg2' in url
        assert 'postgresql' in url


def test_database_fallback_behavior():
    """Test database fallback behavior when DATABASE_URL is invalid."""
    with patch.dict(os.environ, {'DATABASE_URL': 'invalid://url'}):
        url = _build_db_url()
        # Should not modify invalid URLs
        assert url == 'invalid://url'


def test_database_url_normalization():
    """Test that database URLs are properly normalized."""
    test_cases = [
        ('postgres://user:pass@host/db', 'postgresql+psycopg2://user:pass@host/db'),
        ('postgresql://user:pass@host/db', 'postgresql+psycopg2://user:pass@host/db'),
        ('postgresql+psycopg2://user:pass@host/db', 'postgresql+psycopg2://user:pass@host/db'),
        ('sqlite:///data/app.db', 'sqlite:///data/app.db'),
    ]

    for input_url, expected_url in test_cases:
        with patch.dict(os.environ, {'DATABASE_URL': input_url}):
            url = _build_db_url()
            assert url == expected_url, f"Expected {expected_url}, got {url} for input {input_url}"
