#!/usr/bin/env python3
"""
Minimal Railway startup script for Telegram Bot (PTB-based)
Delegates lifecycle to PTB; avoids nested event loops.
Updated: Fixed port conflicts and PTB warnings
Last update: 2025-01-15 - Production-ready Railway deployment
"""

import os
import sys
import logging
import warnings

# Suppress specific PTB warnings that don't affect functionality
warnings.filterwarnings(
    "ignore",
    message="If 'per_message=False', 'CallbackQueryHandler' will not be tracked for every message",
    category=UserWarning,
    module="handlers.registration",
)
warnings.filterwarnings(
    "ignore",
    message="If 'per_message=False', 'CallbackQueryHandler' will not be tracked for every message",
    category=UserWarning,
    module="handlers.books",
)

# Configure logging for Railway
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def _prepare_webhook_env() -> None:
    """Set WEBHOOK_URL from Railway's public domain if available."""
    railway_public_url = os.environ.get("RAILWAY_PUBLIC_DOMAIN")
    if railway_public_url:
        webhook_url = f"https://{railway_public_url}"
        os.environ["WEBHOOK_URL"] = webhook_url
        logger.info(f"🌐 Webhook URL set to: {webhook_url}")

    # Log important environment variables
    logger.info(
        f"🚀 Starting bot with environment: {os.environ.get('ENVIRONMENT', 'production')}"
    )
    logger.info(f"🔧 Force polling: {os.environ.get('FORCE_POLLING', 'false')}")
    logger.info(f"🌍 Port: {os.environ.get('PORT', 'not set')}")


def _validate_environment() -> bool:
    """Validate that required environment variables are set."""
    required_vars = ["BOT_TOKEN"]

    missing_vars = []
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)

    if missing_vars:
        logger.error(
            f"❌ Missing required environment variables: {', '.join(missing_vars)}"
        )
        return False

    return True


def main() -> None:
    try:
        logger.info("🚀 Starting Ostad Hatami Bot...")

        if not _validate_environment():
            sys.exit(1)

        _prepare_webhook_env()

        # Import and run the bot's main function
        # Ensure DATABASE_URL uses psycopg v3+binaries on Railway
        try:
            import os

            url = os.environ.get("DATABASE_URL", "")
            if (
                url
                and "+" not in url
                and (url.startswith("postgres://") or url.startswith("postgresql://"))
            ):
                os.environ["DATABASE_URL"] = url.replace(
                    "postgres://", "postgresql+psycopg://"
                ).replace("postgresql://", "postgresql+psycopg://")
        except Exception:
            pass

        from bot import main as bot_main

        bot_main()
    except KeyboardInterrupt:
        logger.info("🛑 Received keyboard interrupt, shutting down...")
    except ImportError as e:
        logger.error(f"💥 Import error: {e}")
        logger.error(
            "Please ensure all dependencies are installed: pip install -r requirements.txt"
        )
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
