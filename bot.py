#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram Bot (python-telegram-bot v21) – Student Registration & Course Management
"""

import asyncio
import logging
import os
from typing import List

from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    ApplicationBuilder,
    AIORateLimiter,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
)

# Load envs early
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("bot")

# Local imports
from config import Config
from utils.storage import StudentStorage
from handlers.registration import build_registration_conversation
from handlers.menu import register_menu_handlers, ensure_registered
from handlers.courses import register_course_handlers
from handlers.books import register_book_handlers
from handlers.social import register_social_handlers
from handlers.contact import register_contact_handlers


async def start(update: Update, context):
    """Handle /start and show registration if needed."""
    config = context.bot_data["config"]
    storage: StudentStorage = context.bot_data["storage"]

    user_id = update.effective_user.id if update.effective_user else 0
    first_name = update.effective_user.first_name if update.effective_user else "کاربر"

    # Admins bypass registration
    if user_id in config.bot.admin_user_ids:
        await register_menu_handlers.send_main_menu(update, context)
        return

    student = storage.get_student(user_id)
    if student:
        await register_menu_handlers.send_main_menu(update, context)
        return

    # Show welcome with Register button
    from utils.keyboards import build_register_keyboard
    from ui.messages import Messages

    await update.effective_chat.send_message(
        text=Messages.get_welcome_message(first_name),
        reply_markup=build_register_keyboard(),
        parse_mode=ParseMode.HTML,
    )


def build_application() -> Application:
    config = Config()
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        raise ValueError("BOT_TOKEN environment variable is required")

    storage = StudentStorage(json_path=os.path.join(config.database.path, "students.json"))

    application: Application = (
        ApplicationBuilder()
        .token(bot_token)
        .rate_limiter(AIORateLimiter())
        .build()
    )

    # Shared objects
    application.bot_data["config"] = config
    application.bot_data["storage"] = storage

    # Core commands
    application.add_handler(CommandHandler("start", start))

    # Registration conversation
    application.add_handler(build_registration_conversation())

    # Feature handlers (gated for registered users inside handlers)
    register_menu_handlers(application)
    register_course_handlers(application)
    register_book_handlers(application)
    register_social_handlers(application)
    register_contact_handlers(application)

    return application


async def main():
    app = build_application()
    logger.info("🚀 Starting Telegram Bot (python-telegram-bot)")
    await app.run_polling(close_loop=False)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
