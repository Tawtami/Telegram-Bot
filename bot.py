#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ostad Hatami Math Classes Bot - Main Entry Point
Using python-telegram-bot v20+ with async syntax
"""

import os
import sys
import logging
import asyncio
from typing import Dict, Any

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
)

from config import config
from handlers.registration import build_registration_conversation
from handlers.menu import (
    send_main_menu,
    handle_menu_selection,
    handle_back_to_menu,
)
from handlers.courses import (
    handle_free_courses,
    handle_paid_courses,
    handle_purchased_courses,
    handle_course_registration,
    handle_payment_receipt,
)
from handlers.books import build_book_purchase_conversation
from handlers.social import handle_social_media
from handlers.contact import handle_contact_us
from utils.storage import StudentStorage
from utils.error_handler import error_handler
from utils.rate_limiter import rate_limiter
from utils.performance_monitor import monitor

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Command handlers
async def start_command(update: Update, context: Any) -> None:
    """Handle /start command"""
    await send_main_menu(update, context)

async def students_command(update: Update, context: Any) -> None:
    """Handle /students command - Admin only"""
    user_id = update.effective_user.id
    if user_id not in config.bot.admin_user_ids:
        await update.message.reply_text("⛔️ این دستور فقط برای ادمین‌ها در دسترس است.")
        return

    storage: StudentStorage = context.bot_data["storage"]
    students = storage.get_all_students()
    
    if not students:
        await update.message.reply_text("هیچ دانش‌آموزی ثبت‌نام نکرده است.")
        return

    # Create students.json file
    import json
    with open("data/students.json", "w", encoding="utf-8") as f:
        json.dump({"students": students}, f, ensure_ascii=False, indent=2)

    # Send file to admin
    await update.message.reply_document(
        document=open("data/students.json", "rb"),
        caption=f"📊 اطلاعات {len(students)} دانش‌آموز",
    )

async def confirm_payment_command(update: Update, context: Any) -> None:
    """Handle /confirm_payment command - Admin only"""
    user_id = update.effective_user.id
    if user_id not in config.bot.admin_user_ids:
        await update.message.reply_text("⛔️ این دستور فقط برای ادمین‌ها در دسترس است.")
        return

    try:
        student_id = int(context.args[0])
        storage: StudentStorage = context.bot_data["storage"]
        
        if not storage.confirm_payment(student_id):
            await update.message.reply_text("❌ دانش‌آموز یافت نشد یا پرداختی در انتظار تایید ندارد.")
            return

        # Notify student
        await context.bot.send_message(
            chat_id=student_id,
            text="✅ پرداخت شما تایید شد. می‌توانید از منوی «دوره‌های خریداری‌شده» به محتوا دسترسی داشته باشید.",
        )

        await update.message.reply_text("✅ پرداخت با موفقیت تایید شد.")

    except (ValueError, IndexError):
        await update.message.reply_text(
            "❌ فرمت دستور اشتباه است. نمونه صحیح:\n/confirm_payment 123456789"
        )

def main() -> None:
    """Initialize and start the bot"""
    try:
        # Initialize bot application
        application = Application.builder().token(config.bot_token).build()

        # Initialize storage
        storage = StudentStorage()
        application.bot_data["storage"] = storage
        application.bot_data["config"] = config

        # Add handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("students", students_command))
        application.add_handler(CommandHandler("confirm_payment", confirm_payment_command))

        # Registration conversation
        application.add_handler(build_registration_conversation())

        # Book purchase conversation
        application.add_handler(build_book_purchase_conversation())

        # Menu handlers
        application.add_handler(CallbackQueryHandler(handle_menu_selection, pattern="^menu_"))
        application.add_handler(CallbackQueryHandler(handle_back_to_menu, pattern="^back_to_menu$"))

        # Course handlers
        application.add_handler(CallbackQueryHandler(handle_free_courses, pattern="^free_courses$"))
        application.add_handler(CallbackQueryHandler(handle_paid_courses, pattern="^paid_courses$"))
        application.add_handler(CallbackQueryHandler(handle_purchased_courses, pattern="^purchased_courses$"))
        application.add_handler(CallbackQueryHandler(handle_course_registration, pattern="^register_course_"))
        application.add_handler(MessageHandler(filters.PHOTO & ~filters.COMMAND, handle_payment_receipt))

        # Other menu handlers
        application.add_handler(CallbackQueryHandler(handle_social_media, pattern="^social_media$"))
        application.add_handler(CallbackQueryHandler(handle_contact_us, pattern="^contact_us$"))

        # Error handler
        application.add_error_handler(error_handler)

        # Start the bot
        logger.info("🚀 Starting bot...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

    except Exception as e:
        logger.error(f"❌ Error starting bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()