#!/usr/bin/env python3
"""
Minimal Railway startup script for Telegram Bot (PTB-based)
Delegates lifecycle to PTB; avoids nested event loops.
Updated: Fixed port conflicts and PTB warnings
Last update: 2025-08-10 07:35 - Simplified startup for Railway deployment
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

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def _prepare_webhook_env() -> None:
    """Set WEBHOOK_URL from Railway's public domain if available."""
    railway_public_url = os.environ.get("RAILWAY_PUBLIC_DOMAIN")
    if railway_public_url:
        webhook_url = f"https://{railway_public_url}"
        os.environ["WEBHOOK_URL"] = webhook_url
        logger.info(f"🌐 Webhook URL set to: {webhook_url}")


def main() -> None:
    try:
        if not os.getenv("BOT_TOKEN"):
            logger.error("BOT_TOKEN environment variable is not set!")
            sys.exit(1)

        _prepare_webhook_env()

        # Import and run the bot's main function
        from bot import main as bot_main
        bot_main()
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
