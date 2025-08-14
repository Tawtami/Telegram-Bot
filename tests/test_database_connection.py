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
    # Test with PostgreSQL URL
    with patch.dict(os.environ, {'DATABASE_URL': 'postgresql://user:pass@host/db'}):
        # Re-import to get updated value
        import importlib
        import database.db

        importlib.reload(database.db)
        assert database.db.is_postgres is True

    # Test with SQLite URL
    with patch.dict(os.environ, {'DATABASE_URL': 'sqlite:///data/app.db'}):
        importlib.reload(database.db)
        assert database.db.is_postgres is False


def test_session_local_creation():
    """Test that SessionLocal can be created."""
    assert SessionLocal is not None
    assert callable(SessionLocal)


@patch('database.db.create_engine')
def test_engine_creation_postgres(mock_create_engine):
    """Test engine creation for PostgreSQL."""
    mock_engine = MagicMock()
    mock_create_engine.return_value = mock_engine

    with patch.dict(os.environ, {'DATABASE_URL': 'postgresql://user:pass@host/db'}):
        import importlib
        import database.db

        importlib.reload(database.db)

        # Check that create_engine was called with correct parameters
        mock_create_engine.assert_called()
        call_args = mock_create_engine.call_args
        assert 'pool_pre_ping' in call_args[1]
        assert 'future' in call_args[1]


@patch('database.db.create_engine')
def test_engine_creation_sqlite(mock_create_engine):
    """Test engine creation for SQLite."""
    mock_engine = MagicMock()
    mock_create_engine.return_value = mock_engine

    with patch.dict(os.environ, {'DATABASE_URL': 'sqlite:///data/app.db'}):
        import importlib
        import database.db

        importlib.reload(database.db)

        # Check that create_engine was called with SQLite-specific parameters
        mock_create_engine.assert_called()
        call_args = mock_create_engine.call_args
        assert 'pool_pre_ping' in call_args[1]
        assert 'future' in call_args[1]


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

    assert hasattr(Base, '__tablename__')
    assert hasattr(Base, 'metadata')
    assert hasattr(Base, '__table__')


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
