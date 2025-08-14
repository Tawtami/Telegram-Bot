from __future__ import annotations

import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Alembic config
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import project metadata
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from database import alembic_metadata
    target_metadata = alembic_metadata()
except Exception as e:
    print(f"Error importing database metadata: {e}")
    # Fallback to empty metadata if import fails
    from sqlalchemy import MetaData
    target_metadata = MetaData()


def get_url() -> str:
    url = os.getenv("DATABASE_URL", "sqlite:///data/app.db")
    lowered = url.lower()
    if (
        lowered.startswith("postgres://") or lowered.startswith("postgresql://")
    ) and "+" not in url:
        url = url.replace("postgres://", "postgresql+psycopg_binary://").replace(
            "postgresql://", "postgresql+psycopg_binary://"
        )
    
    # Debug logging
    print(f"Database URL: {url}")
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
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = get_url()
    
    # Add explicit driver configuration for PostgreSQL
    if "postgresql" in get_url():
        configuration["sqlalchemy.driver"] = "psycopg_binary"
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
