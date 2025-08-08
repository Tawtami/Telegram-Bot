#!/usr/bin/env python3
"""
Railway startup script for Telegram Bot (PTB-based)
Ensures proper initialization and error handling
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

# Global flags for health check
is_bot_ready = False
is_shutting_down = False


class HealthCheckHandler(BaseHTTPRequestHandler):
    """Enhanced health check handler for Railway"""

    def log_message(self, format, *args):
        """Disable request logging"""
        pass

    def do_GET(self):
        """Handle GET request"""
        if self.path == "/":
            if is_shutting_down:
                self.send_error_response("Service is shutting down")
                return

            if not is_bot_ready:
                self.send_error_response("Service is starting")
                return

            self.send_success_response()
        else:
            self.send_response(404)
            self.end_headers()

    def send_success_response(self):
        """Send 200 OK response"""
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        response = {
            "status": "healthy",
            "service": "Telegram Bot",
            "version": "ptb",
            "timestamp": int(time.time()),
        }
        self.wfile.write(json.dumps(response).encode())

    def send_error_response(self, message: str):
        """Send 503 Service Unavailable response"""
        self.send_response(503)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        response = {
            "status": "unhealthy",
            "message": message,
            "timestamp": int(time.time()),
        }
        self.wfile.write(json.dumps(response).encode())


def start_health_server():
    """Start health check server in background"""
    try:
        port = int(os.environ.get("PORT", 8080))
        server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
        logger.info(f"Health check server started on port {port}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"Failed to start health server: {e}")
        sys.exit(1)


def handle_shutdown(signum, frame):
    """Handle shutdown signals"""
    global is_shutting_down
    logger.info(f"Received signal {signum}, initiating shutdown...")
    is_shutting_down = True
    sys.exit(0)


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

        # Start health check server in background
        health_thread = threading.Thread(target=start_health_server, daemon=True)
        health_thread.start()

        # Import and initialize bot
        try:
            from bot import main as bot_main

            is_bot_ready = True
            await bot_main()
        except ImportError as e:
            logger.error(f"❌ Import error: {e}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"💥 Fatal error during bot startup: {e}")
            sys.exit(1)

    except Exception as e:
        logger.error(f"💥 Fatal error during startup: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        sys.exit(1)
