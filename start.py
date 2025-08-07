#!/usr/bin/env python3
"""
Railway startup script for Telegram Bot (PTB-based)
Ensures proper initialization and error handling
"""

import os
import sys
import logging
import asyncio
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

# Configure basic logging for startup
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class HealthCheckHandler(BaseHTTPRequestHandler):
    """Simple health check handler for Railway"""

    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            response = {
                "status": "healthy",
                "service": "Telegram Bot",
                "version": "ptb",
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()


def start_health_server():
    """Start health check server in background"""
    try:
        port = int(os.environ.get("PORT", 8080))
        server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
        logger.info(f"Health check server started on port {port}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"Failed to start health server: {e}")


def main():
    """Main startup function"""
    try:
        bot_token = os.getenv("BOT_TOKEN")
        if not bot_token:
            logger.error("BOT_TOKEN environment variable is not set!")
            sys.exit(1)

        logger.info("🚀 Starting Telegram Bot...")

        # Start health check server in background
        health_thread = threading.Thread(target=start_health_server, daemon=True)
        health_thread.start()

        # Import and run the main bot (PTB entrypoint)
        from bot import main as bot_main

        asyncio.run(bot_main())

    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Fatal error during startup: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
