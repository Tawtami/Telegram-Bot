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
import warnings
from typing import Dict, Any
import hashlib

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

# Try to import telegram modules with fallback
try:
    from telegram import Update
    from telegram.ext import (
        Application,
        ApplicationBuilder,
        CommandHandler,
        MessageHandler,
        CallbackQueryHandler,
        ConversationHandler,
        filters,
        AIORateLimiter,
        ApplicationHandlerStop,
    )

    TELEGRAM_AVAILABLE = True
except ImportError:
    print("⚠️ Warning: python-telegram-bot not installed. Bot functionality disabled.")
    TELEGRAM_AVAILABLE = False

    # Create dummy classes for development
    class Update:
        pass

    class Application:
        pass


from config import config

# Import handlers with fallback
try:
    from handlers.registration import build_registration_conversation
    from handlers.menu import build_menu_handlers
    from handlers.courses import build_course_handlers
    from handlers.books import build_book_purchase_conversation
    from handlers.payments import build_payment_handlers
    from handlers.contact import build_contact_handlers
    from handlers.social import build_social_handlers

    # Also import the specific handler functions
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
    )
    from handlers.payments import handle_payment_receipt
    from handlers.social import handle_social_media
    from handlers.contact import handle_contact_us

    HANDLERS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Warning: Some handlers not available: {e}")
    HANDLERS_AVAILABLE = False

    # Create dummy functions for development
    def build_registration_conversation():
        return None

    def build_menu_handlers():
        return []

    def build_course_handlers():
        return []

    def build_book_purchase_conversation():
        return None

    def build_payment_handlers():
        return []

    def build_contact_handlers():
        return []

    def build_social_handlers():
        return []

    # Create dummy handler functions
    async def send_main_menu(update, context):
        await update.message.reply_text(
            "⚠️ Bot is in development mode - handlers not available"
        )

    async def handle_menu_selection(update, context):
        await update.message.reply_text(
            "⚠️ Bot is in development mode - handlers not available"
        )

    async def handle_back_to_menu(update, context):
        await update.message.reply_text(
            "⚠️ Bot is in development mode - handlers not available"
        )

    async def handle_free_courses(update, context):
        await update.message.reply_text(
            "⚠️ Bot is in development mode - handlers not available"
        )

    async def handle_paid_courses(update, context):
        await update.message.reply_text(
            "⚠️ Bot is in development mode - handlers not available"
        )

    async def handle_purchased_courses(update, context):
        await update.message.reply_text(
            "⚠️ Bot is in development mode - handlers not available"
        )

    async def handle_course_registration(update, context):
        await update.message.reply_text(
            "⚠️ Bot is in development mode - handlers not available"
        )

    async def handle_payment_receipt(update, context):
        await update.message.reply_text(
            "⚠️ Bot is in development mode - handlers not available"
        )

    async def handle_social_media(update, context):
        await update.message.reply_text(
            "⚠️ Bot is in development mode - handlers not available"
        )

    async def handle_contact_us(update, context):
        await update.message.reply_text(
            "⚠️ Bot is in development mode - handlers not available"
        )


from utils.storage import StudentStorage
from utils.error_handler import ptb_error_handler
from utils.rate_limiter import rate_limiter, multi_rate_limiter
from utils.performance_monitor import monitor
from ui.keyboards import build_register_keyboard

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


def _is_admin(user_id: int) -> bool:
    return user_id in set(config.bot.admin_user_ids)


async def _ensure_admin(update: Update) -> bool:
    user_id = update.effective_user.id if update and update.effective_user else 0
    if not _is_admin(user_id):
        if update and update.effective_message:
            await update.effective_message.reply_text("⛔️ این دستور فقط برای ادمین‌هاست.")
        return False
    return True


async def broadcast_command(update: Update, context: Any) -> None:
    if not await _ensure_admin(update):
        return
    storage: StudentStorage = context.bot_data["storage"]
    students = storage.get_all_students()
    if not students:
        await update.effective_message.reply_text("هیچ کاربری برای ارسال وجود ندارد.")
        return
    text = " ".join(context.args) if context.args else ""
    if not text:
        await update.effective_message.reply_text("لطفاً متن پیام را پس از دستور وارد کنید.")
        return
    sent = 0
    for s in students:
        try:
            if storage.is_user_banned(s.get("user_id")):
                continue
            await context.bot.send_message(chat_id=s.get("user_id"), text=text)
            sent += 1
        except Exception:
            continue
    await update.effective_message.reply_text(f"✅ پیام برای {sent} کاربر ارسال شد.")


async def ban_command(update: Update, context: Any) -> None:
    if not await _ensure_admin(update):
        return
    storage: StudentStorage = context.bot_data["storage"]
    try:
        uid = int(context.args[0])
    except Exception:
        await update.effective_message.reply_text("فرمت درست: /ban 123456789")
        return
    if storage.ban_user(uid):
        await update.effective_message.reply_text(f"کاربر {uid} مسدود شد.")
    else:
        await update.effective_message.reply_text("خطا در مسدودسازی کاربر.")


async def unban_command(update: Update, context: Any) -> None:
    if not await _ensure_admin(update):
        return
    storage: StudentStorage = context.bot_data["storage"]
    try:
        uid = int(context.args[0])
    except Exception:
        await update.effective_message.reply_text("فرمت درست: /unban 123456789")
        return
    if storage.unban_user(uid):
        await update.effective_message.reply_text(f"کاربر {uid} آزاد شد.")
    else:
        await update.effective_message.reply_text("خطا در آزادسازی کاربر.")


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
            await update.message.reply_text(
                "❌ دانش‌آموز یافت نشد یا پرداختی در انتظار تایید ندارد."
            )
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


async def profile_command(update: Update, context: Any) -> None:
    """Handle /profile command"""
    storage: StudentStorage = context.bot_data["storage"]
    user_id = update.effective_user.id
    student = storage.get_student(user_id)

    if not student:
        await update.message.reply_text(
            "❌ شما هنوز ثبت‌نام نکرده‌اید.\n" "لطفاً ابتدا ثبت‌نام کنید.",
            reply_markup=build_register_keyboard(),
        )
        return

    profile_text = (
        "📋 **پروفایل شما:**\n\n"
        f"👤 **نام:** {student['first_name']}\n"
        f"👤 **نام خانوادگی:** {student['last_name']}\n"
        f"📱 **شماره تماس:** {student.get('phone_number', 'ثبت نشده')}\n"
        f"📍 **استان:** {student['province']}\n"
        f"🏙 **شهر:** {student['city']}\n"
        f"📚 **پایه تحصیلی:** {student['grade']}\n"
        f"🎓 **رشته تحصیلی:** {student['field']}\n\n"
        "برای ویرایش اطلاعات، لطفاً دوباره ثبت‌نام کنید."
    )

    await update.message.reply_text(profile_text, parse_mode="Markdown")


async def help_command(update: Update, context: Any) -> None:
    """Handle /help command"""
    help_text = (
        "🤖 **راهنمای ربات استاد حاتمی**\n\n"
        "**دستورات اصلی:**\n"
        "📝 `/start` - شروع کار با ربات\n"
        "👤 `/profile` - مشاهده پروفایل\n"
        "❓ `/help` - راهنما (همین پیام)\n"
        "📚 `/courses` - مشاهده دوره‌ها\n"
        "🛒 `/mycourses` - دوره‌های خریداری شده\n"
        "📖 `/book` - اطلاعات کتاب\n"
        "📞 `/contact` - ارتباط با ما\n"
        "🌐 `/social` - شبکه‌های اجتماعی\n"
        "ℹ️ `/about` - درباره استاد حاتمی\n\n"
        "**منوهای اصلی:**\n"
        "🎁 دوره‌های رایگان\n"
        "💼 دوره‌های تخصصی\n"
        "🛒 دوره‌های خریداری‌شده\n"
        "📘 خرید کتاب انفجار خلاقیت\n"
        "🌐 شبکه‌های اجتماعی\n"
        "📞 ارتباط با ما\n\n"
        "**پشتیبانی:**\n"
        "📞 تلگرام: @ostad_hatami\n"
        "📧 ایمیل: info@ostadhatami.ir\n\n"
        "💡 **نکته:** برای استفاده کامل از ربات، ابتدا ثبت‌نام کنید."
    )

    await update.message.reply_text(help_text)


async def courses_command(update: Update, context: Any) -> None:
    """Handle /courses command - Show available courses"""
    await send_main_menu(update, context)


async def mycourses_command(update: Update, context: Any) -> None:
    """Handle /mycourses command - Show user's purchased courses"""
    # Redirect to the purchased courses handler
    from handlers.courses import handle_purchased_courses

    await handle_purchased_courses(update, context)


async def book_command(update: Update, context: Any) -> None:
    """Handle /book command - Show book information"""
    # Redirect to the book info handler
    from handlers.books import handle_book_info

    await handle_book_info(update, context)


async def contact_command(update: Update, context: Any) -> None:
    """Handle /contact command - Show contact information"""
    # Redirect to the contact handler
    from handlers.contact import handle_contact_us

    await handle_contact_us(update, context)


async def social_command(update: Update, context: Any) -> None:
    """Handle /social command - Show social media links"""
    # Redirect to the social media handler
    from handlers.social import handle_social_media

    await handle_social_media(update, context)


async def about_command(update: Update, context: Any) -> None:
    """Handle /about command - Show information about Ostad Hatami"""
    about_text = (
        "👨‍🏫 **استاد حاتمی - کلاس‌های ریاضی**\n\n"
        "**🎯 هدف:**\n"
        "ارتقای سطح ریاضی دانش‌آموزان با روش‌های نوین و خلاقانه\n\n"
        "**📚 خدمات:**\n"
        "• دوره‌های رایگان پایه\n"
        "• دوره‌های تخصصی پیشرفته\n"
        "• کتاب انفجار خلاقیت ریاضی\n"
        "• مشاوره تحصیلی\n\n"
        "**🏆 ویژگی‌ها:**\n"
        "• آموزش مفهومی و کاربردی\n"
        "• حل مسئله با روش‌های خلاقانه\n"
        "• پشتیبانی مستمر\n"
        "• قیمت‌های مناسب\n\n"
        "**📞 ارتباط:**\n"
        "تلگرام: @ostad_hatami\n"
        "ایمیل: info@ostadhatami.ir\n\n"
        "**💡 شعار:**\n"
        "ریاضی را آسان و لذت‌بخش یاد بگیرید!"
    )

    await update.message.reply_text(about_text, parse_mode="Markdown")


def main() -> None:
    """Initialize and start the bot (synchronous entrypoint).

    PTB manages the asyncio event loop internally via run_polling/run_webhook,
    so we avoid wrapping it in asyncio.run to prevent loop close errors.
    """
    try:
        # Check if telegram modules are available
        if not TELEGRAM_AVAILABLE:
            print("❌ Cannot start bot: python-telegram-bot not installed")
            print("💡 To install: pip install python-telegram-bot[webhooks]")
            print("💡 Or run: pip install -r requirements.txt")
            return

        application = (
            ApplicationBuilder()
            .token(config.bot_token)
            .rate_limiter(AIORateLimiter())
            .build()
        )

        # Initialize storage
        storage = StudentStorage()
        application.bot_data["storage"] = storage
        application.bot_data["config"] = config

        # Add pre-check handlers for banned users
        async def block_banned_messages(update: Update, context: Any) -> None:
            storage: StudentStorage = context.bot_data["storage"]
            user_id = update.effective_user.id if update and update.effective_user else 0
            if storage.is_user_banned(user_id):
                if update.effective_message:
                    await update.effective_message.reply_text("⛔️ دسترسی شما محدود شده است.")
                return

        application.add_handler(MessageHandler(filters.ALL, block_banned_messages), group=0)
        application.add_handler(CallbackQueryHandler(block_banned_messages), group=0)

        # Add handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("students", students_command))
        application.add_handler(CommandHandler("broadcast", broadcast_command))
        application.add_handler(CommandHandler("ban", ban_command))
        application.add_handler(CommandHandler("unban", unban_command))
        application.add_handler(CommandHandler("profile", profile_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("courses", courses_command))
        application.add_handler(CommandHandler("mycourses", mycourses_command))
        application.add_handler(CommandHandler("book", book_command))
        application.add_handler(CommandHandler("contact", contact_command))
        application.add_handler(CommandHandler("social", social_command))
        application.add_handler(CommandHandler("about", about_command))
        application.add_handler(
            CommandHandler("confirm_payment", confirm_payment_command)
        )

        application.add_handler(build_registration_conversation())
        application.add_handler(build_book_purchase_conversation())

        application.add_handler(
            CallbackQueryHandler(handle_menu_selection, pattern="^menu_")
        )
        application.add_handler(
            CallbackQueryHandler(handle_back_to_menu, pattern="^back_to_menu$")
        )

        application.add_handler(
            CallbackQueryHandler(handle_free_courses, pattern="^free_courses$")
        )
        application.add_handler(
            CallbackQueryHandler(handle_paid_courses, pattern="^paid_courses$")
        )
        application.add_handler(
            CallbackQueryHandler(
                handle_purchased_courses, pattern="^purchased_courses$"
            )
        )
        application.add_handler(
            CallbackQueryHandler(
                handle_course_registration, pattern="^register_course_"
            )
        )
        application.add_handler(
            MessageHandler(filters.PHOTO & ~filters.COMMAND, handle_payment_receipt)
        )

        application.add_handler(
            CallbackQueryHandler(handle_social_media, pattern="^social_media$")
        )
        application.add_handler(
            CallbackQueryHandler(handle_contact_us, pattern="^contact_us$")
        )

        application.add_error_handler(ptb_error_handler)

        logger.info("🚀 Starting bot...")

        port = int(os.environ.get("PORT", 0))
        webhook_url_root = os.environ.get("WEBHOOK_URL")
        force_polling = os.environ.get("FORCE_POLLING", "false").lower() == "true"

        if not force_polling and port > 0 and webhook_url_root:
            # Use aiohttp to serve both healthcheck and webhook
            import asyncio
            from aiohttp import web
            import json

            async def health(request):
                return web.Response(text="OK", content_type="text/plain")

            # Derive a non-guessable webhook path (avoid exposing token)
            token_hash = hashlib.sha256(config.bot_token.encode()).hexdigest()[:24]
            path = f"/webhook/{token_hash}"
            full_webhook_url = webhook_url_root.rstrip("/") + path

            async def telegram_webhook(request):
                if request.method != "POST":
                    return web.Response(status=405)
                try:
                    data = await request.json()
                except Exception:
                    return web.Response(status=400)
                update = Update.de_json(data, application.bot)
                await application.process_update(update)
                return web.json_response({"ok": True})

            app = web.Application()
            app.router.add_get("/", health)
            app.router.add_post(path, telegram_webhook)

            async def runner():
                await application.initialize()
                await application.start()
                await application.bot.set_webhook(url=full_webhook_url, drop_pending_updates=True)
                runner = web.AppRunner(app)
                await runner.setup()
                site = web.TCPSite(runner, "0.0.0.0", port)
                logger.info(f"🌐 Webhook set to: {full_webhook_url}")
                logger.info(f"✅ Health check at: http://0.0.0.0:{port}/")
                await site.start()
                try:
                    while True:
                        await asyncio.sleep(3600)
                except asyncio.CancelledError:
                    pass
                finally:
                    await application.bot.delete_webhook()
                    await application.stop()
                    await application.shutdown()

            asyncio.run(runner())
        else:
            application.run_polling(drop_pending_updates=False)
            logger.info("📡 Polling started")

    except Exception as e:
        logger.error(f"❌ Error starting bot: {e}")
        # Exit non-zero to signal Railway to restart
        sys.exit(1)


# When running directly (not imported), start the bot
if __name__ == "__main__":
    # For local development only - Railway uses start.py
    main()
