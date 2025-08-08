#!/usr/bin/env python3
"""
Railway startup script for Telegram Bot (PTB-based)
Ensures proper initialization and error handling with webhook support
"""

import os
import sys
import time
import json
import signal
import logging
import asyncio
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# Configure basic logging for startup
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

"""
Note: Railway will health-check the web process via PORT; our bot's webhook/polling
is managed in bot.py. Keep startup minimal and avoid running a separate HTTP server
that conflicts with the PTB webhook server.
"""


is_bot_ready = False
is_shutting_down = False


def _noop_health_server():
    return None


def stop_health_server():
    return None


def handle_shutdown(signum, frame):
    """Handle shutdown signals"""
    global is_shutting_down
    logger.info(f"Received signal {signum}, initiating shutdown...")
    is_shutting_down = True
    stop_health_server()
    sys.exit(0)


async def setup_webhook():
    """Setup webhook for Railway deployment"""
    try:
        from bot import main as bot_main

        # Set environment variables for webhook
        port = int(os.environ.get("PORT", 8080))
        railway_public_url = os.environ.get("RAILWAY_PUBLIC_DOMAIN")

        if railway_public_url:
            webhook_url = f"https://{railway_public_url}"
            os.environ["WEBHOOK_URL"] = webhook_url
            logger.info(f"🌐 Webhook URL set to: {webhook_url}")

        return await bot_main()

    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Fatal error during bot startup: {e}")
        sys.exit(1)


async def main():
    """Main startup function"""
    global is_bot_ready

    try:
        # Register signal handlers
        signal.signal(signal.SIGTERM, handle_shutdown)
        signal.signal(signal.SIGINT, handle_shutdown)

        # Check environment variables
        bot_token = os.getenv("BOT_TOKEN")
        if not bot_token:
            logger.error("BOT_TOKEN environment variable is not set!")
            sys.exit(1)

        logger.info("🚀 Starting Telegram Bot...")

        # No separate health server; PTB webhook will bind to PORT if configured

        # Setup webhook and run bot
        is_bot_ready = True
        await setup_webhook()

    except Exception as e:
        logger.error(f"💥 Fatal error during startup: {e}")
        sys.exit(1)
    finally:
        stop_health_server()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        sys.exit(1)
