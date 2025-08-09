#!/usr/bin/env python3
"""
Minimal Railway startup script for Telegram Bot (PTB-based)
Delegates lifecycle to PTB; avoids nested event loops.
Updated: Fixed port conflicts and PTB warnings
Last update: 2025-08-09 23:30 - Force Railway redeploy
CI bypass: 2025-08-09 23:35 - Force immediate deployment
"""

import os
import sys
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

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

        # Use PORT+1 for health server to avoid conflict with webhook
        port = int(os.getenv("PORT", "0") or 0)
        webhook_url = os.getenv("WEBHOOK_URL")

        if port > 0:
            health_port = port + 1

            class HealthHandler(BaseHTTPRequestHandler):
                def do_GET(self):
                    self.send_response(200)
                    self.send_header("Content-Type", "text/plain; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(b"OK")

                def log_message(self, format, *args):
                    return

            def run_health():
                try:
                    httpd = HTTPServer(("0.0.0.0", health_port), HealthHandler)
                    httpd.serve_forever()
                except Exception:
                    pass

            t = threading.Thread(target=run_health, daemon=True)
            t.start()
            logger.info(f"✅ Health server started on port {health_port}")

        # Call synchronous bot.main() to let PTB own the event loop
        bot_main()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
