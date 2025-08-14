#!/usr/bin/env python3
"""
Test script to verify database connection with psycopg2.
Run this to test if the database connection is working properly.
"""

import os
import sys
from sqlalchemy import create_engine, text


def test_connection():
    """Test database connection with psycopg2."""
    try:
        # Get database URL from environment
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            logger.error("❌ DATABASE_URL environment variable not set")
            return False

        logger.info(f"🔗 Testing connection to: {db_url}")

        # Create engine with psycopg2
        if db_url.startswith("postgres") and "+" not in db_url:
            # Convert to psycopg2 if not specified
            db_url = db_url.replace("postgres://", "postgresql+psycopg2://").replace(
                "postgresql://", "postgresql+psycopg2://"
            )
            logger.info(f"🔄 Converted URL to: {db_url}")

        # Create engine
        engine = create_engine(
            db_url,
            poolclass=None,  # Use default pool
            echo=True,  # Show SQL queries
            connect_args={"connect_timeout": 10, "application_name": "connection_test"},
        )

        # Test connection
        with engine.connect() as conn:
            logger.info("✅ Database connection successful!")

            # Test basic query
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            logger.info(f"📊 PostgreSQL version: {version}")

            # Test if alembic_version table exists
            try:
                result = conn.execute(
                    text(
                        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'alembic_version')"
                    )
                )
                exists = result.scalar()
                logger.info(f"📋 Alembic version table exists: {exists}")
            except Exception as e:
                logger.warning(f"⚠️ Could not check alembic_version table: {e}")

            return True

    except Exception as e:
        logger.error(f"❌ Connection failed: {e}")
        return False


if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
