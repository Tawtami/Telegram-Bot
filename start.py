#!/usr/bin/env python3
"""
Railway startup script for Ostad Hatami Bot
Ensures proper initialization and error handling
"""

import os
import sys
import logging

# Configure basic logging for startup
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Main startup function"""
    try:
        # Check if BOT_TOKEN is set
        bot_token = os.getenv("BOT_TOKEN")
        if not bot_token:
            logger.error("BOT_TOKEN environment variable is not set!")
            logger.error("Please set BOT_TOKEN in Railway environment variables")
            sys.exit(1)

        logger.info("🚀 Starting Ostad Hatami Bot...")
        logger.info("✅ Environment variables loaded")
        logger.info("✅ Dependencies verified")

        # Import and run the main bot
        from bot import main as bot_main
        import asyncio

        # Run the bot
        asyncio.run(bot_main())

    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        logger.error("Please check if all dependencies are installed")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Fatal error during startup: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
