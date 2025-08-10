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
import time
import json

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

# Import telegram modules
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

from config import config

# Import handlers
from handlers.registration import build_registration_conversation
from handlers.menu import (
    build_menu_handlers,
    send_main_menu,
    handle_menu_selection,
    handle_back_to_menu,
)
from handlers.courses import (
    build_course_handlers,
    handle_free_courses,
    handle_paid_courses,
    handle_purchased_courses,
    handle_course_registration,
)
from handlers.books import build_book_purchase_conversation, handle_book_info
from handlers.payments import build_payment_handlers, handle_payment_receipt
from handlers.contact import build_contact_handlers, handle_contact_us
from handlers.social import build_social_handlers, handle_social_media

# Import utilities
from utils.rate_limiter import rate_limiter, multi_rate_limiter, rate_limit_handler
from utils.storage import StudentStorage
from utils.error_handler import ptb_error_handler
from ui.keyboards import build_register_keyboard

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# Command handlers
@rate_limit_handler("default")
async def start_command(update: Update, context: Any) -> None:
    """Handle /start command"""
    try:
        await send_main_menu(update, context)
    except Exception as e:
        logger.error(f"Error in start_command: {e}")
        await update.message.reply_text("❌ خطا در شروع ربات. لطفاً دوباره تلاش کنید.")


@rate_limit_handler("admin")
async def students_command(update: Update, context: Any) -> None:
    """Handle /students command - Admin only"""
    try:
        user_id = update.effective_user.id
        if user_id not in config.bot.admin_user_ids:
            await update.message.reply_text(
                "⛔️ این دستور فقط برای ادمین‌ها در دسترس است."
            )
            return

        storage: StudentStorage = context.bot_data["storage"]
        students = storage.get_all_students()

        if not students:
            await update.message.reply_text("هیچ دانش‌آموزی ثبت‌نام نکرده است.")
            return

        # Create students.json file
        import json
        import tempfile

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump({"students": students}, f, ensure_ascii=False, indent=2)
            temp_file_path = f.name

        try:
            # Send file to admin
            with open(temp_file_path, "rb") as f:
                await update.message.reply_document(
                    document=f,
                    caption=f"📊 اطلاعات {len(students)} دانش‌آموز",
                )
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except OSError:
                pass

    except Exception as e:
        logger.error(f"Error in students_command: {e}")
        await update.message.reply_text("❌ خطا در دریافت اطلاعات دانش‌آموزان.")


def _is_admin(user_id: int) -> bool:
    return user_id in set(config.bot.admin_user_ids)


async def _ensure_admin(update: Update) -> bool:
    user_id = update.effective_user.id if update and update.effective_user else 0
    if not _is_admin(user_id):
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "⛔️ این دستور فقط برای ادمین‌هاست."
            )
        return False
    return True


@rate_limit_handler("admin")
async def broadcast_command(update: Update, context: Any) -> None:
    """Handle /broadcast command - Admin only"""
    try:
        if not await _ensure_admin(update):
            return

        storage: StudentStorage = context.bot_data["storage"]
        students = storage.get_all_students()

        if not students:
            await update.effective_message.reply_text(
                "هیچ کاربری برای ارسال وجود ندارد."
            )
            return

        text = " ".join(context.args) if context.args else ""
        if not text:
            await update.effective_message.reply_text(
                "لطفاً متن پیام را پس از دستور وارد کنید.\n"
                "مثال: /broadcast سلام! کلاس جدید شروع شده است."
            )
            return

        # Validate message length (Telegram limit is 4096 characters)
        if len(text) > 4000:
            await update.effective_message.reply_text(
                "❌ پیام خیلی طولانی است. حداکثر 4000 کاراکتر مجاز است."
            )
            return

        sent = 0
        failed = 0
        errors = []

        for student in students:
            try:
                user_id = student.get("user_id")
                if not user_id or storage.is_user_banned(user_id):
                    continue

                await context.bot.send_message(chat_id=user_id, text=text)
                sent += 1

                # Small delay to avoid hitting rate limits
                await asyncio.sleep(0.1)

            except Exception as e:
                error_msg = f"Failed to send to user {user_id}: {e}"
                logger.warning(error_msg)
                errors.append(error_msg)
                failed += 1
                continue

        # Send summary
        summary = (
            f"✅ پیام برای {sent} کاربر ارسال شد.\n❌ {failed} کاربر دریافت نکردند."
        )
        if errors and len(errors) <= 3:
            summary += f"\n\nخطاها:\n" + "\n".join(errors[:3])
        elif errors:
            summary += f"\n\n{len(errors)} خطا رخ داد (نمایش داده نشد)"

        await update.effective_message.reply_text(summary)

    except Exception as e:
        logger.error(f"Error in broadcast_command: {e}")
        await update.effective_message.reply_text("❌ خطا در ارسال پیام همگانی.")


@rate_limit_handler("admin")
async def ban_command(update: Update, context: Any) -> None:
    """Handle /ban command - Admin only"""
    try:
        if not await _ensure_admin(update):
            return

        if not context.args:
            await update.effective_message.reply_text(
                "فرمت درست: /ban 123456789\n" "لطفاً شناسه کاربری را وارد کنید."
            )
            return

        try:
            uid = int(context.args[0])
        except ValueError:
            await update.effective_message.reply_text("فرمت درست: /ban 123456789")
            return

        storage: StudentStorage = context.bot_data["storage"]
        if storage.ban_user(uid):
            await update.effective_message.reply_text(f"✅ کاربر {uid} مسدود شد.")
        else:
            await update.effective_message.reply_text("❌ خطا در مسدودسازی کاربر.")

    except Exception as e:
        logger.error(f"Error in ban_command: {e}")
        await update.effective_message.reply_text("❌ خطا در اجرای دستور.")


@rate_limit_handler("admin")
async def unban_command(update: Update, context: Any) -> None:
    """Handle /unban command - Admin only"""
    try:
        if not await _ensure_admin(update):
            return

        if not context.args:
            await update.effective_message.reply_text(
                "فرمت درست: /unban 123456789\n" "لطفاً شناسه کاربری را وارد کنید."
            )
            return

        try:
            uid = int(context.args[0])
        except ValueError:
            await update.effective_message.reply_text("فرمت درست: /unban 123456789")
            return

        storage: StudentStorage = context.bot_data["storage"]
        if storage.unban_user(uid):
            await update.effective_message.reply_text(f"✅ کاربر {uid} آزاد شد.")
        else:
            await update.effective_message.reply_text("❌ خطا در آزادسازی کاربر.")

    except Exception as e:
        logger.error(f"Error in unban_command: {e}")
        await update.effective_message.reply_text("❌ خطا در اجرای دستور.")


@rate_limit_handler("admin")
async def confirm_payment_command(update: Update, context: Any) -> None:
    """Handle /confirm_payment command - Admin only"""
    try:
        user_id = update.effective_user.id
        if user_id not in config.bot.admin_user_ids:
            await update.message.reply_text(
                "⛔️ این دستور فقط برای ادمین‌ها در دسترس است."
            )
            return

        if not context.args:
            await update.message.reply_text(
                "فرمت درست: /confirm_payment 123456789\n"
                "لطفاً شناسه کاربری را وارد کنید."
            )
            return

        try:
            student_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text(
                "❌ فرمت دستور اشتباه است. نمونه صحیح:\n/confirm_payment 123456789"
            )
            return

        storage: StudentStorage = context.bot_data["storage"]

        if not storage.confirm_payment(student_id):
            await update.message.reply_text(
                "❌ دانش‌آموز یافت نشد یا پرداختی در انتظار تایید ندارد."
            )
            return

        # Notify student
        try:
            await context.bot.send_message(
                chat_id=student_id,
                text="✅ پرداخت شما تایید شد. می‌توانید از منوی «دوره‌های خریداری‌شده» به محتوا دسترسی داشته باشید.",
            )
        except Exception as e:
            logger.warning(f"Failed to notify student {student_id}: {e}")

        await update.message.reply_text("✅ پرداخت با موفقیت تایید شد.")

    except Exception as e:
        logger.error(f"Error in confirm_payment_command: {e}")
        await update.message.reply_text("❌ خطا در تایید پرداخت.")


@rate_limit_handler("default")
async def profile_command(update: Update, context: Any) -> None:
    """Handle /profile command"""
    try:
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

    except Exception as e:
        logger.error(f"Error in profile_command: {e}")
        await update.message.reply_text("❌ خطا در نمایش پروفایل.")


@rate_limit_handler("default")
async def help_command(update: Update, context: Any) -> None:
    """Handle /help command"""
    try:
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
            "**دستورات ادمین:**\n"
            "📊 `/status` - وضعیت ربات\n"
            "👥 `/students` - لیست دانش‌آموزان\n"
            "📢 `/broadcast` - ارسال پیام همگانی\n"
            "🚫 `/ban` - مسدودسازی کاربر\n"
            "✅ `/unban` - آزادسازی کاربر\n"
            "💰 `/confirm_payment` - تایید پرداخت\n\n"
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

    except Exception as e:
        logger.error(f"Error in help_command: {e}")
        await update.message.reply_text("❌ خطا در نمایش راهنما.")


@rate_limit_handler("default")
async def courses_command(update: Update, context: Any) -> None:
    """Handle /courses command - Show available courses"""
    try:
        await send_main_menu(update, context)
    except Exception as e:
        logger.error(f"Error in courses_command: {e}")
        await update.message.reply_text("❌ خطا در نمایش دوره‌ها.")


@rate_limit_handler("default")
async def mycourses_command(update: Update, context: Any) -> None:
    """Handle /mycourses command - Show user's purchased courses"""
    try:
        # Redirect to the purchased courses handler
        await handle_purchased_courses(update, context)
    except Exception as e:
        logger.error(f"Error in mycourses_command: {e}")
        await update.message.reply_text("❌ خطا در نمایش دوره‌های شما.")


@rate_limit_handler("default")
async def book_command(update: Update, context: Any) -> None:
    """Handle /book command - Show book information"""
    try:
        # Redirect to the book info handler
        await handle_book_info(update, context)
    except Exception as e:
        logger.error(f"Error in book_command: {e}")
        await update.message.reply_text("❌ خطا در نمایش اطلاعات کتاب.")


@rate_limit_handler("default")
async def contact_command(update: Update, context: Any) -> None:
    """Handle /contact command - Show contact information"""
    try:
        # Redirect to the contact handler
        await handle_contact_us(update, context)
    except Exception as e:
        logger.error(f"Error in contact_command: {e}")
        await update.message.reply_text("❌ خطا در نمایش اطلاعات تماس.")


@rate_limit_handler("default")
async def social_command(update: Update, context: Any) -> None:
    """Handle /social command - Show social media links"""
    try:
        # Redirect to the social media handler
        await handle_social_media(update, context)
    except Exception as e:
        logger.error(f"Error in social_command: {e}")
        await update.message.reply_text("❌ خطا در نمایش شبکه‌های اجتماعی.")


@rate_limit_handler("default")
async def about_command(update: Update, context: Any) -> None:
    """Handle /about command - Show information about Ostad Hatami"""
    try:
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

    except Exception as e:
        logger.error(f"Error in about_command: {e}")
        await update.message.reply_text("❌ خطا در نمایش اطلاعات.")


@rate_limit_handler("admin")
async def status_command(update: Update, context: Any) -> None:
    """Handle /status command - Admin only"""
    try:
        if not await _ensure_admin(update):
            return

        storage: StudentStorage = context.bot_data["storage"]

        # Get bot info
        try:
            bot_info = await context.bot.get_me()
            bot_name = bot_info.first_name
            bot_username = bot_info.username
        except Exception as e:
            logger.error(f"Error getting bot info: {e}")
            bot_name = "Unknown"
            bot_username = "Unknown"

        # Get storage stats
        students = storage.get_all_students()
        total_students = len(students)

        # Get rate limiter stats if available
        rate_limiter_stats = {}
        try:
            if "rate_limiter" in context.bot_data:
                rate_limiter = context.bot_data["rate_limiter"]
                rate_limiter_stats = await rate_limiter.get_all_stats()
        except Exception as e:
            logger.warning(f"Could not get rate limiter stats: {e}")

        # Build status message
        status_text = f"🤖 **وضعیت ربات {bot_name}**\n\n"
        status_text += f"📊 **آمار کلی:**\n"
        status_text += f"• تعداد دانش‌آموزان: {total_students}\n"
        status_text += f"• نام کاربری: @{bot_username}\n"

        if rate_limiter_stats:
            status_text += f"\n🚦 **محدودیت درخواست:**\n"
            for level, stats in rate_limiter_stats.items():
                status_text += f"• {level}: {stats.get('total_requests', 0)} درخواست\n"

        # Add webhook status if in webhook mode
        if config.webhook.enabled:
            status_text += f"\n🌐 **حالت وب‌هوک:**\n"
            status_text += f"• فعال: ✅\n"
            status_text += f"• پورت: {config.webhook.port}\n"
            status_text += f"• مسیر: {config.webhook.path}\n"
        else:
            status_text += f"\n📡 **حالت پولینگ:**\n"
            status_text += f"• فعال: ✅\n"

        await update.effective_message.reply_text(status_text, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error in status_command: {e}")
        await update.effective_message.reply_text("❌ خطا در دریافت وضعیت ربات.")


async def setup_handlers(application: Application) -> None:
    """Setup all bot handlers"""
    try:
        # Add pre-check handlers for banned users
        async def block_banned_messages(update: Update, context: Any) -> None:
            try:
                storage: StudentStorage = context.bot_data["storage"]
                user_id = (
                    update.effective_user.id if update and update.effective_user else 0
                )
                if storage.is_user_banned(user_id):
                    if update.effective_message:
                        await update.effective_message.reply_text(
                            "⛔️ دسترسی شما محدود شده است."
                        )
                    # Stop further handler processing for this update
                    raise ApplicationHandlerStop()
            except Exception as e:
                logger.error(f"Error in block_banned_messages: {e}")

        application.add_handler(
            MessageHandler(filters.ALL, block_banned_messages), group=0
        )
        application.add_handler(CallbackQueryHandler(block_banned_messages), group=0)

        # Add command handlers
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
        application.add_handler(CommandHandler("status", status_command))

        # Add conversation handlers
        registration_conv = build_registration_conversation()
        if registration_conv:
            application.add_handler(registration_conv)

        # Add menu handlers
        menu_handlers = build_menu_handlers()
        for handler in menu_handlers:
            application.add_handler(handler)

        # Add course handlers
        course_handlers = build_course_handlers()
        for handler in course_handlers:
            application.add_handler(handler)

        # Add book handlers
        book_handlers = build_book_purchase_conversation()
        if book_handlers:
            application.add_handler(book_handlers)

        # Add payment handlers
        payment_handlers = build_payment_handlers()
        for handler in payment_handlers:
            application.add_handler(handler)

        # Add contact handlers
        contact_handlers = build_contact_handlers()
        for handler in contact_handlers:
            application.add_handler(handler)

        # Add social handlers
        social_handlers = build_social_handlers()
        for handler in social_handlers:
            application.add_handler(handler)

        # Add callback query handlers
        application.add_handler(
            CallbackQueryHandler(handle_menu_selection, pattern="^menu_")
        )
        application.add_handler(
            CallbackQueryHandler(handle_back_to_menu, pattern="^back_to_menu$")
        )

        # Add registration back handlers
        from handlers.registration import back_to_province, back_to_city, back_to_grade

        application.add_handler(
            CallbackQueryHandler(back_to_province, pattern="^back_to_province$")
        )
        application.add_handler(
            CallbackQueryHandler(back_to_city, pattern="^back_to_city$")
        )
        application.add_handler(
            CallbackQueryHandler(back_to_grade, pattern="^back_to_grade$")
        )

        application.add_handler(
            CallbackQueryHandler(handle_free_courses, pattern="^courses_free$")
        )
        application.add_handler(
            CallbackQueryHandler(handle_paid_courses, pattern="^courses_paid$")
        )
        application.add_handler(
            CallbackQueryHandler(
                handle_purchased_courses, pattern="^courses_purchased$"
            )
        )
        application.add_handler(
            CallbackQueryHandler(
                handle_course_registration, pattern="^register_course_"
            )
        )
        # Payment receipt handler is provided by build_payment_handlers()

        application.add_handler(
            CallbackQueryHandler(handle_social_media, pattern="^social_media$")
        )
        application.add_handler(
            CallbackQueryHandler(handle_contact_us, pattern="^contact_us$")
        )

        # Add book info handler
        from handlers.books import show_book_info

        application.add_handler(
            CallbackQueryHandler(show_book_info, pattern="^book_info$")
        )

        # Add error handler
        application.add_error_handler(ptb_error_handler)

        logger.info("✅ All handlers setup successfully")

    except Exception as e:
        logger.error(f"❌ Error setting up handlers: {e}")
        raise


async def run_webhook_mode(application: Application) -> None:
    """Run bot in webhook mode for Railway deployment"""
    try:
        import aiohttp
        from aiohttp import web

        # Create web application
        app = web.Application()

        # Health check endpoint
        async def health_check(request):
            try:
                # Check if bot is healthy
                bot_info = await application.bot.get_me()
                return web.json_response(
                    {
                        "status": "healthy",
                        "bot_name": bot_info.first_name,
                        "bot_username": bot_info.username,
                        "timestamp": time.time(),
                    }
                )
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                return web.json_response(
                    {"status": "unhealthy", "error": str(e), "timestamp": time.time()},
                    status=500,
                )

        # Telegram webhook endpoint
        async def telegram_webhook(request):
            if request.method != "POST":
                return web.Response(status=405)

            try:
                # Validate Telegram secret token header if configured
                expected_token = (config.webhook.secret_token or "").strip()
                if expected_token:
                    header_token = request.headers.get(
                        "X-Telegram-Bot-Api-Secret-Token", ""
                    ).strip()
                    if header_token != expected_token:
                        logger.warning("Invalid or missing webhook secret token")
                        return web.Response(status=401)

                # Validate request
                if (
                    not request.content_type
                    or "application/json" not in request.content_type
                ):
                    logger.warning(f"Invalid content type: {request.content_type}")
                    return web.Response(status=400)

                data = await request.json()
                if not data:
                    logger.warning("Empty webhook data received")
                    return web.Response(status=400)

                # Process update
                update = Update.de_json(data, application.bot)
                await application.process_update(update)
                return web.json_response({"ok": True})
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in webhook: {e}")
                return web.Response(status=400)
            except Exception as e:
                logger.error(f"Error processing webhook update: {e}")
                return web.Response(status=500)

        # Add routes
        app.router.add_get("/", health_check)
        app.router.add_post(config.webhook.path, telegram_webhook)

        # Setup webhook with proper error handling
        await application.initialize()
        await application.start()

        # Delete any existing webhook first to prevent 409 errors
        try:
            await application.bot.delete_webhook(drop_pending_updates=True)
            logger.info("✅ Existing webhook deleted successfully")
        except Exception as e:
            logger.warning(f"Warning: Could not delete existing webhook: {e}")

        # Set webhook with retry logic
        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                full_webhook_url = config.webhook.url.rstrip("/") + config.webhook.path
                await application.bot.set_webhook(
                    url=full_webhook_url,
                    drop_pending_updates=config.webhook.drop_pending_updates,
                    secret_token=(
                        config.webhook.secret_token
                        if config.webhook.secret_token
                        else None
                    ),
                    allowed_updates=[
                        "message",
                        "edited_message",
                        "callback_query",
                        "channel_post",
                        "edited_channel_post",
                    ],
                    max_connections=40,
                )
                logger.info(f"🌐 Webhook set successfully to: {full_webhook_url}")
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Webhook setup attempt {attempt + 1} failed: {e}. Retrying in {retry_delay}s..."
                    )
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    logger.error(
                        f"Failed to set webhook after {max_retries} attempts: {e}"
                    )
                    raise

        logger.info(f"✅ Health check at: http://0.0.0.0:{config.webhook.port}/")

        # Start background maintenance tasks (rate limiter cleanup)
        try:
            await multi_rate_limiter.start_cleanup_tasks()
        except Exception as e:
            logger.warning(f"Could not start rate limiter cleanup tasks: {e}")

        # Start web server
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", config.webhook.port)
        await site.start()

        logger.info(f"🚀 Web server started on port {config.webhook.port}")

        # Keep running with proper shutdown handling
        try:
            while True:
                await asyncio.sleep(3600)  # Check every hour
        except asyncio.CancelledError:
            logger.info("🛑 Webhook mode cancelled, shutting down...")
        finally:
            # Cleanup
            try:
                await application.bot.delete_webhook()
                logger.info("✅ Webhook deleted successfully")
            except Exception as e:
                logger.warning(
                    f"Warning: Could not delete webhook during shutdown: {e}"
                )

            await application.stop()
            await application.shutdown()
            await runner.cleanup()
            logger.info("✅ Webhook mode shutdown complete")

    except Exception as e:
        logger.error(f"❌ Error in webhook mode: {e}")
        raise


async def run_polling_mode(application: Application) -> None:
    """Run bot in polling mode for development"""
    try:
        logger.info("📡 Starting polling mode...")
        await application.run_polling(drop_pending_updates=False)
        logger.info("📡 Polling started successfully")
    except Exception as e:
        logger.error(f"❌ Error in polling mode: {e}")
        raise


def main() -> None:
    """Initialize and start the bot (synchronous entrypoint)."""
    try:
        # Validate configuration

        # Validate configuration
        try:
            config.validate()
            logger.info("✅ Configuration validated successfully")
        except ValueError as e:
            logger.error(f"❌ Configuration validation failed: {e}")
            return

        # Create application with proper configuration
        application = (
            ApplicationBuilder()
            .token(config.bot_token)
            .rate_limiter(AIORateLimiter())
            .connection_pool_size(8)
            .connect_timeout(30.0)
            .read_timeout(30.0)
            .write_timeout(30.0)
            .pool_timeout(30.0)
            .build()
        )

        # Initialize storage
        storage = StudentStorage()
        application.bot_data["storage"] = storage
        application.bot_data["config"] = config

        # Setup handlers and expose rate limiter for status diagnostics
        asyncio.run(setup_handlers(application))
        application.bot_data["rate_limiter"] = multi_rate_limiter

        logger.info("🚀 Starting bot...")
        logger.info(f"📊 Configuration: {config.to_dict()}")

        # Choose mode based on configuration
        if config.webhook.enabled and config.webhook.url and config.webhook.port > 0:
            # Webhook mode for Railway
            logger.info("🌐 Starting in webhook mode for Railway deployment")
            asyncio.run(run_webhook_mode(application))
        else:
            # Polling mode for development
            logger.info("📡 Starting in polling mode for development")
            asyncio.run(run_polling_mode(application))

    except KeyboardInterrupt:
        logger.info("🛑 Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"❌ Error starting bot: {e}")
        # Exit non-zero to signal Railway to restart
        sys.exit(1)


# When running directly (not imported), start the bot
if __name__ == "__main__":
    # For local development only - Railway uses start.py
    main()
