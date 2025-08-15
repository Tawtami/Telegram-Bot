from __future__ import annotations

import os
import logging
from logging.config import fileConfig
from sqlalchemy import pool, text
from alembic import context

# Alembic config
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
logger = logging.getLogger(__name__)

# Import project metadata
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from database import alembic_metadata

    target_metadata = alembic_metadata()
except Exception as e:
    logger.error(f"Error importing database metadata: {e}")
    # Fallback to empty metadata if import fails
    from sqlalchemy import MetaData

    target_metadata = MetaData()


def get_url() -> str:
    url = os.getenv("DATABASE_URL", "sqlite:///data/app.db")
    lowered = url.lower()
    if (
        lowered.startswith("postgres://") or lowered.startswith("postgresql://")
    ) and "+" not in url:
        # Use psycopg2-binary instead of psycopg3 for better compatibility
        url = url.replace("postgres://", "postgresql+psycopg2://").replace(
            "postgresql://", "postgresql+psycopg2://"
        )

    # Debug logging
    logger.info(f"Database URL: {url}")
    return url


def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    # Create engine with minimal configuration to avoid driver issues
    try:
        from sqlalchemy import create_engine

        connectable = create_engine(
            get_url(),
            poolclass=pool.NullPool,
            echo=True,  # Enable SQL logging for debugging
            # Add PostgreSQL-specific options for better compatibility
            connect_args={"connect_timeout": 10, "application_name": "alembic_migration"},
        )

        # Test connection before proceeding
        with connectable.connect() as test_conn:
            test_conn.execute(text("SELECT 1"))
            logger.info("Database connection test successful")

    except Exception as e:
        logger.error(f"Engine creation failed: {e}")
        raise

    with connectable.connect() as connection:
        # Try to manually check if alembic_version table exists to avoid driver issues
        try:
            result = connection.execute(
                text(
                    """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'alembic_version'
                )
            """
                )
            )
            version_table_exists = result.scalar()
            logger.info(f"Alembic version table exists: {version_table_exists}")
        except Exception as e:
            logger.warning(f"Could not check version table: {e}")
            version_table_exists = False

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            # Force version table creation if it doesn't exist
            version_table_schema=None,
            # Add transaction isolation level for PostgreSQL
            transaction_per_migration=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
