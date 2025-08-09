#!/usr/bin/env python3
"""
Minimal Railway startup script for Telegram Bot (PTB-based)
Delegates lifecycle to PTB; avoids nested event loops.
"""

import os
import sys
import logging
import asyncio

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

        # Import and run the bot's async main once
        from bot import main as bot_main
        # Call synchronous bot.main() to let PTB own the event loop
        bot_main()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
