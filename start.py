#!/usr/bin/env python3
"""
Minimal Railway startup script for Telegram Bot (PTB-based)
Delegates lifecycle to PTB; avoids nested event loops.
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
        
        # If WEBHOOK_URL is not set, run polling but expose a tiny health endpoint
        # on PORT so Railway healthcheck passes.
        webhook_url = os.getenv("WEBHOOK_URL")
        port = int(os.getenv("PORT", "0") or 0)

        if not webhook_url and port > 0:
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
                    httpd = HTTPServer(("0.0.0.0", port), HealthHandler)
                    httpd.serve_forever()
                except Exception:
                    pass

            t = threading.Thread(target=run_health, daemon=True)
            t.start()
            logger.info(f"✅ Health server started on port {port}")

        # Call synchronous bot.main() to let PTB own the event loop
        bot_main()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
