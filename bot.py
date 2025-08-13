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
import re
import sentry_sdk

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
from handlers.profile import build_profile_edit_handlers
from handlers.books import build_book_purchase_conversation, handle_book_info
from handlers.payments import build_payment_handlers, handle_payment_receipt
from handlers.contact import build_contact_handlers, handle_contact_us
from handlers.social import build_social_handlers, handle_social_media

# Import utilities
from utils.rate_limiter import rate_limiter, multi_rate_limiter, rate_limit_handler
from database.db import session_scope
from database.service import is_user_banned, ban_user, unban_user
from utils.error_handler import ptb_error_handler
from ui.keyboards import build_register_keyboard
from datetime import datetime
from utils.background import BroadcastManager

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Reduce noisy third-party HTTP logs and redact Telegram bot token if it appears in URLs
try:
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("telegram.vendor.ptb_urllib3.urllib3.connectionpool").setLevel(
        logging.WARNING
    )

    class _RedactFilter(logging.Filter):
        _pat = re.compile(r"(https://api\.telegram\.org/bot)[A-Za-z0-9:_-]+")

        def filter(self, record: logging.LogRecord) -> bool:
            try:
                msg = record.getMessage()
                red = self._pat.sub(r"\1***", msg)
                if red != msg:
                    record.msg = red
                    record.args = ()
            except Exception:
                pass
            return True

    for lname in ("httpx", "bot", "aiohttp.access"):
        logging.getLogger(lname).addFilter(_RedactFilter())
except Exception:
    pass

# Initialize Sentry if DSN is provided
try:
    dsn = os.getenv("SENTRY_DSN", "").strip()
    if dsn:
        sentry_sdk.init(dsn=dsn, traces_sample_rate=0.05)
        logger.info("Sentry initialized")
except Exception as _e:
    logger.warning(f"Sentry init failed: {_e}")


# ---------------------
# Helpers to reduce handler complexity
# ---------------------


def _parse_admin_filters(request):
    from datetime import datetime, timedelta

    status = request.query.get("status", "pending").lower()
    ptype = request.query.get("type", "").lower()
    uid_str = request.query.get("uid", "").strip()
    product_q = request.query.get("product", "").strip()
    from_str = request.query.get("from", "").strip()
    to_str = request.query.get("to", "").strip()
    fmt = request.query.get("format", "").lower()
    page = max(0, int(request.query.get("page", "0") or 0))
    page_size = max(1, min(100, int(request.query.get("size", "20") or 20)))

    uid = int(uid_str) if uid_str.isdigit() else None
    dt_from = None
    dt_to = None
    try:
        if from_str:
            dt_from = (
                datetime.fromisoformat(from_str)
                if len(from_str) > 10
                else datetime.fromisoformat(from_str + "T00:00:00")
            )
        if to_str:
            base = (
                datetime.fromisoformat(to_str)
                if len(to_str) > 10
                else datetime.fromisoformat(to_str + "T00:00:00")
            )
            dt_to = base + (timedelta(days=1) if len(to_str) <= 10 else timedelta(seconds=0))
    except Exception:
        dt_from = None
        dt_to = None

    return {
        "status": status,
        "ptype": ptype,
        "uid": uid,
        "uid_str": uid_str,
        "product_q": product_q,
        "dt_from": dt_from,
        "dt_to": dt_to,
        "from_str": from_str,
        "to_str": to_str,
        "fmt": fmt,
        "page": page,
        "page_size": page_size,
    }


def _build_admin_qs(base_url, status, ptype, uid_str, product_q, from_str, to_str, page_size, page):
    params = {
        "status": status,
        "type": ptype,
        "uid": uid_str,
        "product": product_q,
        "from": from_str,
        "to": to_str,
        "size": str(page_size),
        "page": str(page),
    }
    parts = [f"{k}={v}" for k, v in params.items() if v not in (None, "")]
    return base_url + "&" + "&".join(parts)


def _query_purchases_filtered(stmt):
    from database.db import session_scope

    try:
        with session_scope() as session:
            return list(session.execute(stmt).scalars())
    except Exception as e:
        try:
            logger.warning(f"purchase query failed, attempting DB init: {e}")
            from database.migrate import init_db

            init_db()
            with session_scope() as session:
                return list(session.execute(stmt).scalars())
        except Exception as e2:
            logger.error(f"fatal DB error after init retry: {e2}")
            raise


# Command handlers
@rate_limit_handler("registration")
async def start_command(update: Update, context: Any) -> None:
    """Handle /start command"""
    try:
        user_id = update.effective_user.id if update and update.effective_user else 0
        logger.info(f"/start received from user_id={user_id}")
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
            await update.message.reply_text("⛔️ این دستور فقط برای ادمین‌ها در دسترس است.")
            return

        # Export: basic CSV from DB users table
        from sqlalchemy import select
        from database.models_sql import User as DBUser

        with session_scope() as session:
            rows = list(session.execute(select(DBUser)).scalars())
        students = [
            {
                "user_id": u.telegram_user_id,
                "first_name": None,
                "last_name": None,
                "phone_number": None,
                "province": u.province,
                "city": u.city,
                "grade": u.grade,
                "field": u.field_of_study,
            }
            for u in rows
        ]

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
            await update.effective_message.reply_text("⛔️ این دستور فقط برای ادمین‌هاست.")
        return False
    return True


@rate_limit_handler("admin")
async def broadcast_command(update: Update, context: Any) -> None:
    """Handle /broadcast command - Admin only"""
    try:
        if not await _ensure_admin(update):
            return

        # Broadcast to all registered users
        from sqlalchemy import select
        from database.models_sql import User as DBUser

        with session_scope() as session:
            rows = list(session.execute(select(DBUser)).scalars())
        students = [{"user_id": u.telegram_user_id} for u in rows]

        if not students:
            await update.effective_message.reply_text("هیچ کاربری برای ارسال وجود ندارد.")
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

        # Start background broadcast with progress
        manager: BroadcastManager = context.bot_data["broadcast_manager"]
        user_ids = [s.get("user_id") for s in students if s.get("user_id")]
        await manager.start_broadcast(context.application, update.effective_chat.id, user_ids, text)

    except Exception as e:
        logger.error(f"Error in broadcast_command: {e}")
        await update.effective_message.reply_text("❌ خطا در ارسال پیام همگانی.")


@rate_limit_handler("admin")
async def broadcast_grade_command(update: Update, context: Any) -> None:
    """Handle /broadcast_grade <grade> <message...> - Admin only"""
    try:
        if not await _ensure_admin(update):
            return

        if not context.args or len(context.args) < 2:
            await update.effective_message.reply_text("فرمت درست: /broadcast_grade دهم پیام شما")
            return

        target_grade = context.args[0]
        text = " ".join(context.args[1:])
        if target_grade not in config.grades:
            await update.effective_message.reply_text("پایه تحصیلی نامعتبر است.")
            return

        from sqlalchemy import select
        from database.models_sql import User as DBUser

        with session_scope() as session:
            rows = list(
                session.execute(select(DBUser).where(DBUser.grade == target_grade)).scalars()
            )
        students = [{"user_id": u.telegram_user_id} for u in rows]
        if not students:
            await update.effective_message.reply_text("کاربری با این پایه یافت نشد.")
            return

        sent = 0
        failed = 0
        for student in students:
            try:
                uid = student.get("user_id")
                if not uid:
                    continue
                await context.bot.send_message(chat_id=uid, text=text)
                sent += 1
                await asyncio.sleep(0.05)
            except Exception:
                failed += 1
                continue

        await update.effective_message.reply_text(f"✅ ارسال شد: {sent} | ناموفق: {failed}")
    except Exception as e:
        logger.error(f"Error in broadcast_grade_command: {e}")
        await update.effective_message.reply_text("❌ خطا در ارسال پیام گروهی بر اساس پایه.")


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

        with session_scope() as session:
            ok = ban_user(session, uid)
        if ok:
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

        with session_scope() as session:
            ok = unban_user(session, uid)
        if ok:
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
            await update.message.reply_text("⛔️ این دستور فقط برای ادمین‌ها در دسترس است.")
            return

        if not context.args:
            await update.message.reply_text(
                "فرمت درست: /confirm_payment 123456789\n" "لطفاً شناسه کاربری را وارد کنید."
            )
            return

        try:
            student_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text(
                "❌ فرمت دستور اشتباه است. نمونه صحیح:\n/confirm_payment 123456789"
            )
            return

        # No longer needed: approvals handled via buttons/DB; keep manual ack minimal

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


@rate_limit_handler("admin")
async def orders_command(update: Update, context: Any) -> None:
    """Handle /orders [pending|approved|rejected] - Admin only"""
    try:
        if not await _ensure_admin(update):
            return

        status = (context.args[0] if context.args else "pending").lower()
        valid = {"pending": "در انتظار", "approved": "تایید", "rejected": "رد"}
        if status not in valid:
            await update.effective_message.reply_text("فرمت: /orders [pending|approved|rejected]")
            return

        notifications = context.bot_data.get("payment_notifications", {})
        entries = [
            (t, m)
            for t, m in notifications.items()
            if (
                (status == "pending" and not m.get("processed"))
                or (
                    status != "pending"
                    and m.get("processed")
                    and m.get("decision") == ("approve" if status == "approved" else "reject")
                )
            )
        ]
        if not entries:
            await update.effective_message.reply_text("موردی یافت نشد.")
            return

        lines = [f"🧾 سفارش‌های {valid[status]}:"]
        for token, meta in entries[:30]:
            lines.append(
                f"• کاربر {meta.get('student_id')} | {meta.get('item_type')} «{meta.get('item_title','')}» | توکن: {token}"
            )
        text = "\n".join(lines)
        # Optional CSV export
        if context.args and any(a.lower() == "csv" for a in context.args):
            import csv, io

            buf = io.StringIO()
            writer = csv.writer(buf)
            writer.writerow(["token", "student_id", "item_type", "item_title", "status"])
            for token, meta in entries:
                writer.writerow(
                    [
                        token,
                        meta.get("student_id"),
                        meta.get("item_type"),
                        (meta.get("item_title") or ""),
                        ("pending" if not meta.get("processed") else meta.get("decision")),
                    ]
                )
            buf.seek(0)
            await update.effective_message.reply_document(
                document=io.BytesIO(buf.getvalue().encode("utf-8")),
                filename="orders.csv",
                caption="🧾 سفارش‌ها (CSV)",
            )
        else:
            await update.effective_message.reply_text(text)
    except Exception as e:
        logger.error(f"Error in orders_command: {e}")
        await update.effective_message.reply_text("❌ خطا در نمایش سفارش‌ها.")


@rate_limit_handler("admin")
async def user_search_command(update: Update, context: Any) -> None:
    """Handle /user_search <query> - search by name or phone (admin only)"""
    try:
        if not await _ensure_admin(update):
            return

        q = " ".join(context.args) if context.args else ""
        if not q:
            await update.effective_message.reply_text("فرمت: /user_search واژه_جستجو")
            return
        q = q.strip().lower()

        from sqlalchemy import select
        from database.models_sql import User as DBUser

        results = []
        with session_scope() as session:
            rows = list(session.execute(select(DBUser)).scalars())
        for u in rows:
            hay = f"{(u.province or '').lower()} {(u.city or '').lower()} {(u.grade or '').lower()} {(u.field_of_study or '').lower()}"
            if q in hay or q in str(u.telegram_user_id):
                results.append(u)

        if not results:
            await update.effective_message.reply_text("چیزی یافت نشد.")
            return

        lines = ["نتایج:"]
        for u in results[:25]:
            lines.append(
                f"• id={u.telegram_user_id} | {u.province or '—'} {u.city or '—'} | {u.grade or '—'} {u.field_of_study or '—'}"
            )
        await update.effective_message.reply_text("\n".join(lines))
    except Exception as e:
        logger.error(f"Error in user_search_command: {e}")
        await update.effective_message.reply_text("❌ خطا در جستجو.")


@rate_limit_handler("admin")
async def orders_ui_command(update: Update, context: Any) -> None:
    """Admin inline UI to list pending orders with quick access.
    Shows last 10 pending items and links to existing inline approve/reject buttons.
    """
    try:
        if not await _ensure_admin(update):
            return
        notifications = context.bot_data.get("payment_notifications", {})
        pending = [(t, m) for t, m in notifications.items() if not m.get("processed")]
        if not pending:
            await update.effective_message.reply_text("مورد در انتظاری وجود ندارد.")
            return

        # Filters: page [book|course] [user_id]
        page = 0
        type_filter = "all"
        user_filter = None
        for arg in context.args or []:
            if arg.isdigit():
                if page == 0:
                    page = max(0, int(arg))
                else:
                    user_filter = int(arg)
            elif arg.lower() in ("book", "course"):
                type_filter = arg.lower()

        # Apply filters
        if type_filter in ("book", "course"):
            pending = [(t, m) for t, m in pending if m.get("item_type") == type_filter]
        if user_filter is not None:
            pending = [(t, m) for t, m in pending if int(m.get("student_id", 0)) == user_filter]

        page_size = 5
        ordered = list(sorted(pending, key=lambda kv: kv[1].get("created_at", 0), reverse=True))
        start = page * page_size
        end = start + page_size
        slice_items = ordered[start:end]

        from telegram import InlineKeyboardMarkup, InlineKeyboardButton

        lines = [f"🕒 پرداخت‌های در انتظار (صفحه {page+1})"]
        rows = []
        for token, meta in slice_items:
            title = meta.get("item_title", "")
            student_id = meta.get("student_id")
            lines.append(
                f"• {meta.get('item_type')} «{title}» | کاربر {student_id} | توکن: {token}"
            )
            rows.append(
                [
                    InlineKeyboardButton("✅ تایید", callback_data=f"pay:{token}:approve"),
                    InlineKeyboardButton("❌ رد", callback_data=f"pay:{token}:reject"),
                ]
            )
        nav = []
        if start > 0:
            nav.append(
                InlineKeyboardButton(
                    "⬅️ قبلی",
                    callback_data=f"orders_page:{page-1}:{type_filter}:{user_filter if user_filter is not None else '-'}",
                )
            )
        if end < len(ordered):
            nav.append(
                InlineKeyboardButton(
                    "بعدی ➡️",
                    callback_data=f"orders_page:{page+1}:{type_filter}:{user_filter if user_filter is not None else '-'}",
                )
            )
        if nav:
            rows.append(nav)

        await update.effective_message.reply_text(
            "\n".join(lines), reply_markup=InlineKeyboardMarkup(rows) if rows else None
        )
    except Exception as e:
        logger.error(f"Error in orders_ui_command: {e}")
        await update.effective_message.reply_text("❌ خطا در نمایش رابط سفارش‌ها.")


@rate_limit_handler("default")
async def profile_command(update: Update, context: Any) -> None:
    """Handle /profile command"""
    try:
        from database.db import session_scope
        from database.models_sql import User as DBUser
        from utils.crypto import crypto_manager

        user_id = update.effective_user.id
        with session_scope() as session:
            db_user = session.query(DBUser).filter(DBUser.telegram_user_id == user_id).one_or_none()

        if not db_user:
            await update.message.reply_text(
                "❌ شما هنوز ثبت‌نام نکرده‌اید.\nلطفاً ابتدا ثبت‌نام کنید.",
                reply_markup=build_register_keyboard(),
            )
            return

        # Decrypt PII for display to the user only
        try:
            first_name = crypto_manager.decrypt_text(db_user.first_name_enc) or ""
        except Exception:
            first_name = ""
        try:
            last_name = crypto_manager.decrypt_text(db_user.last_name_enc) or ""
        except Exception:
            last_name = ""
        try:
            phone = crypto_manager.decrypt_text(db_user.phone_enc) or "ثبت نشده"
        except Exception:
            phone = "ثبت نشده"

        profile_text = (
            "📋 **پروفایل شما:**\n\n"
            f"👤 **نام:** {first_name} {last_name}\n"
            f"📱 **شماره تماس:** {phone}\n"
            f"📍 **استان:** {db_user.province or '—'}\n"
            f"🏙 **شهر:** {db_user.city or '—'}\n"
            f"📚 **پایه تحصیلی:** {db_user.grade or '—'}\n"
            f"🎓 **رشته تحصیلی:** {db_user.field_of_study or '—'}\n"
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
async def daily_command(update: Update, context: Any) -> None:
    try:
        # Send daily quiz directly (no mock), same logic as handle_daily_quiz
        from database.db import session_scope
        from database.models_sql import User as DBUser
        from database.service import get_daily_question
        from sqlalchemy import select
        from telegram import InlineKeyboardMarkup, InlineKeyboardButton

        with session_scope() as session:
            db_user = session.execute(
                select(DBUser).where(DBUser.telegram_user_id == update.effective_user.id)
            ).scalar_one_or_none()
        if not db_user:
            await update.effective_message.reply_text("❌ ابتدا ثبت‌نام کنید.")
            return
        q = None
        with session_scope() as session:
            q = get_daily_question(session, db_user.grade or "دهم")
        if not q:
            await update.effective_message.reply_text("سوال روز موجود نیست. فردا دوباره تلاش کنید.")
            return
        choices = (q.options or {}).get("choices", [])
        rows = [
            [InlineKeyboardButton(text=c, callback_data=f"quiz:{q.id}:{i}")]
            for i, c in enumerate(choices[:8])
        ]
        rows.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_menu")])
        await update.effective_message.reply_text(
            f"سوال روز ({q.grade})\n\n{q.question_text}",
            reply_markup=InlineKeyboardMarkup(rows),
        )
    except Exception as e:
        logger.error(f"Error in daily_command: {e}")
        await update.message.reply_text("❌ خطا در سوال روز.")


@rate_limit_handler("default")
async def progress_command(update: Update, context: Any) -> None:
    try:
        from sqlalchemy import select
        from database.models_sql import User as DBUser
        from database.db import session_scope
        from database.service import get_user_stats

        with session_scope() as session:
            u = session.execute(
                select(DBUser).where(DBUser.telegram_user_id == update.effective_user.id)
            ).scalar_one_or_none()
            if not u:
                await update.message.reply_text("❌ ابتدا ثبت‌نام کنید.")
                return
            s = get_user_stats(session, u.id)
        await update.message.reply_text(
            f"📊 پیشرفت شما:\nامتیاز: {s['points']}\nدرست‌ها: {s['total_correct']} از {s['total_attempts']}\nاستریک: {s['streak_days']} روز"
        )
    except Exception as e:
        logger.error(f"Error in progress_command: {e}")
        await update.message.reply_text("❌ خطا در نمایش پیشرفت.")


@rate_limit_handler("default")
async def leaderboard_command(update: Update, context: Any) -> None:
    try:
        from database.db import session_scope
        from database.service import get_leaderboard_top

        with session_scope() as session:
            top = get_leaderboard_top(session, limit=10)
        if not top:
            await update.message.reply_text("هنوز جدول امتیازات خالی است.")
            return
        lines = ["🏆 جدول امتیازات:"]
        for i, row in enumerate(top, 1):
            lines.append(f"{i}. {row['telegram_user_id']} — {row['points']} امتیاز")
        await update.message.reply_text("\n".join(lines))
    except Exception as e:
        logger.error(f"Error in leaderboard_command: {e}")
        await update.message.reply_text("❌ خطا در جدول امتیازات.")


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

        await update.message.reply_text(about_text)

    except Exception as e:
        logger.error(f"Error in about_command: {e}")
        await update.message.reply_text("❌ خطا در نمایش اطلاعات.")


@rate_limit_handler("admin")
async def status_command(update: Update, context: Any) -> None:
    """Handle /status command - Admin only"""
    try:
        if not await _ensure_admin(update):
            return

        # Get bot info
        try:
            bot_info = await context.bot.get_me()
            bot_name = bot_info.first_name
            bot_username = bot_info.username
        except Exception as e:
            logger.error(f"Error getting bot info: {e}")
            bot_name = "Unknown"
            bot_username = "Unknown"

        # Get user count from DB
        try:
            from sqlalchemy import select, func
            from database.models_sql import User as DBUser

            with session_scope() as session:
                total_students = session.execute(select(func.count(DBUser.id))).scalar() or 0
        except Exception:
            total_students = 0

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


@rate_limit_handler("admin")
async def payments_audit_command(update: Update, context: Any) -> None:
    """Audit recent payment decisions and pending items (admin only)."""
    try:
        if not await _ensure_admin(update):
            return

        notifications = context.bot_data.get("payment_notifications", {})
        if not notifications:
            await update.effective_message.reply_text("هیچ پرداختی ثبت نشده است.")
            return

        # Build a concise audit log
        lines = ["🧾 گزارش پرداخت‌ها:"]
        # Sort by created_at desc
        entries = sorted(
            notifications.items(),
            key=lambda kv: kv[1].get("created_at", 0),
            reverse=True,
        )
        for token, meta in entries[:20]:
            created = datetime.fromtimestamp(meta.get("created_at", 0)).strftime("%Y-%m-%d %H:%M")
            decided_at = (
                datetime.fromtimestamp(meta["decided_at"]).strftime("%Y-%m-%d %H:%M")
                if meta.get("decided_at")
                else "—"
            )
            status = (
                "در انتظار"
                if not meta.get("processed")
                else ("تایید" if meta.get("decision") == "approve" else "رد")
            )
            lines.append(
                f"• {created} | کاربر {meta['student_id']} | {meta.get('item_type','?')} «{meta.get('item_title','?')}» | وضعیت: {status} | تصمیم‌گیر: {meta.get('decided_by','—')} | زمان تصمیم: {decided_at} | توکن: {token}"
            )

        text = "\n".join(lines)
        await update.effective_message.reply_text(text)
    except Exception as e:
        logger.error(f"Error in payments_audit_command: {e}")
        await update.effective_message.reply_text("❌ خطا در گزارش پرداخت‌ها.")


@rate_limit_handler("admin")
async def metrics_command(update: Update, context: Any) -> None:
    try:
        if not await _ensure_admin(update):
            return
        from utils.performance_monitor import monitor

        stats = await monitor.get_stats()
        sys = stats.get("system", {})
        counters = stats.get("counters", {})
        handlers = stats.get("handlers", {})
        lines = [
            "📈 آمار سیستم:",
            f"• آپ‌تایم (ساعت): {sys.get('uptime_hours', 0)}",
            f"• کل درخواست‌ها: {sys.get('total_requests', 0)}",
            f"• خطاها: {sys.get('total_errors', 0)}",
            f"• میانگین زمان پاسخ: {sys.get('avg_response_time', 0)}s",
            "",
            "🔢 شمارنده‌ها:",
        ]
        for k, v in counters.items():
            lines.append(f"• {k}: {v}")
        lines.append("")
        lines.append("🧩 هندلرها:")
        for name, data in handlers.items():
            lines.append(
                f"• {name}: {data.get('total_requests',0)} req | err {data.get('error_count',0)} | avg {data.get('avg_duration',0)}s"
            )
        # CSV export if requested
        if context.args and any(a.lower() == "csv" for a in context.args):
            import csv, io

            buf = io.StringIO()
            writer = csv.writer(buf)
            writer.writerow(["metric", "value"])
            for k, v in counters.items():
                writer.writerow([k, v])
            writer.writerow([])
            writer.writerow(["handler", "total_requests", "error_count", "avg_duration"])
            for name, data in handlers.items():
                writer.writerow(
                    [
                        name,
                        data.get("total_requests", 0),
                        data.get("error_count", 0),
                        data.get("avg_duration", 0),
                    ]
                )
            buf.seek(0)
            await update.effective_message.reply_document(
                document=io.BytesIO(buf.getvalue().encode("utf-8")),
                filename="metrics.csv",
                caption="📈 آمار (CSV)",
            )
        else:
            await update.effective_message.reply_text("\n".join(lines))
    except Exception as e:
        logger.error(f"Error in metrics_command: {e}")
        await update.effective_message.reply_text("❌ خطا در خواندن آمار.")


async def setup_handlers(application: Application) -> None:
    """Setup all bot handlers"""
    try:
        # Add pre-check handlers for banned users
        async def block_banned_messages(update: Update, context: Any) -> None:
            try:
                user_id = update.effective_user.id if update and update.effective_user else 0
                with session_scope() as session:
                    banned = is_user_banned(session, user_id)
                if banned:
                    if update.effective_message:
                        await update.effective_message.reply_text("⛔️ دسترسی شما محدود شده است.")
                    # Stop further handler processing for this update
                    raise ApplicationHandlerStop()
            except Exception as e:
                logger.error(f"Error in block_banned_messages: {e}")

        application.add_handler(MessageHandler(filters.ALL, block_banned_messages), group=0)
        application.add_handler(CallbackQueryHandler(block_banned_messages), group=0)

        # Add command handlers
        application.add_handler(CommandHandler("start", start_command), group=1)
        application.add_handler(CommandHandler("students", students_command), group=1)
        application.add_handler(CommandHandler("broadcast", broadcast_command), group=1)
        application.add_handler(CommandHandler("broadcast_grade", broadcast_grade_command), group=1)
        application.add_handler(CommandHandler("ban", ban_command), group=1)
        application.add_handler(CommandHandler("unban", unban_command), group=1)
        application.add_handler(CommandHandler("profile", profile_command), group=1)
        application.add_handler(CommandHandler("help", help_command), group=1)
        application.add_handler(CommandHandler("daily", daily_command), group=1)
        application.add_handler(CommandHandler("progress", progress_command), group=1)
        application.add_handler(CommandHandler("leaderboard", leaderboard_command), group=1)
        application.add_handler(CommandHandler("courses", courses_command), group=1)
        application.add_handler(CommandHandler("mycourses", mycourses_command), group=1)
        application.add_handler(CommandHandler("book", book_command), group=1)
        application.add_handler(CommandHandler("contact", contact_command), group=1)
        application.add_handler(CommandHandler("social", social_command), group=1)
        application.add_handler(CommandHandler("about", about_command), group=1)
        application.add_handler(CommandHandler("confirm_payment", confirm_payment_command), group=1)
        application.add_handler(CommandHandler("status", status_command), group=1)
        application.add_handler(CommandHandler("metrics", metrics_command), group=1)
        application.add_handler(CommandHandler("payments_audit", payments_audit_command), group=1)
        application.add_handler(CommandHandler("orders", orders_command), group=1)
        application.add_handler(CommandHandler("user_search", user_search_command), group=1)
        application.add_handler(CommandHandler("orders_ui", orders_ui_command), group=1)

        # Add conversation handlers
        registration_conv = build_registration_conversation()
        if registration_conv:
            application.add_handler(registration_conv, group=1)

        # Add menu handlers
        menu_handlers = build_menu_handlers()
        for handler in menu_handlers:
            application.add_handler(handler, group=1)

        # Add course handlers
        course_handlers = build_course_handlers()
        for handler in course_handlers:
            application.add_handler(handler, group=1)

        # Add book handlers
        book_handlers = build_book_purchase_conversation()
        if book_handlers:
            application.add_handler(book_handlers, group=1)

        # Add payment handlers
        payment_handlers = build_payment_handlers()
        for handler in payment_handlers:
            application.add_handler(handler, group=1)

        # Add profile edit handlers
        for handler in build_profile_edit_handlers():
            application.add_handler(handler, group=1)

        # Add contact handlers
        contact_handlers = build_contact_handlers()
        for handler in contact_handlers:
            application.add_handler(handler, group=1)

        # Add social handlers
        social_handlers = build_social_handlers()
        for handler in social_handlers:
            application.add_handler(handler, group=1)

        # Add callback query handlers
        application.add_handler(
            CallbackQueryHandler(handle_menu_selection, pattern="^menu_"), group=1
        )
        application.add_handler(
            CallbackQueryHandler(handle_back_to_menu, pattern="^back_to_menu$"), group=1
        )

        # Add registration back handlers
        from handlers.registration import back_to_province, back_to_city, back_to_grade

        application.add_handler(
            CallbackQueryHandler(back_to_province, pattern="^back_to_province$"),
            group=1,
        )
        application.add_handler(
            CallbackQueryHandler(back_to_city, pattern="^back_to_city$"), group=1
        )
        application.add_handler(
            CallbackQueryHandler(back_to_grade, pattern="^back_to_grade$"), group=1
        )

        application.add_handler(
            CallbackQueryHandler(handle_free_courses, pattern="^courses_free$"), group=1
        )
        application.add_handler(
            CallbackQueryHandler(handle_paid_courses, pattern="^courses_paid$"), group=1
        )
        application.add_handler(
            CallbackQueryHandler(handle_purchased_courses, pattern="^courses_purchased$"),
            group=1,
        )
        application.add_handler(
            CallbackQueryHandler(handle_course_registration, pattern="^register_course_"),
            group=1,
        )
        # Learning: daily quiz
        from handlers.courses import handle_daily_quiz, handle_quiz_answer

        application.add_handler(
            CallbackQueryHandler(handle_daily_quiz, pattern="^daily_quiz$"), group=1
        )
        application.add_handler(
            CallbackQueryHandler(handle_quiz_answer, pattern=r"^quiz:\d+:\d+$"),
            group=1,
        )
        # Payment receipt handler is provided by build_payment_handlers()

        application.add_handler(
            CallbackQueryHandler(handle_social_media, pattern="^social_media$"), group=1
        )
        application.add_handler(
            CallbackQueryHandler(handle_contact_us, pattern="^contact_us$"), group=1
        )

        # Add book info handler
        from handlers.books import show_book_info

        application.add_handler(
            CallbackQueryHandler(show_book_info, pattern="^book_info$"), group=1
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

        # Create web application with gzip compression
        @web.middleware
        async def gzip_middleware(request, handler):
            resp = await handler(request)
            try:
                # Only compress JSON/text and when client accepts gzip
                if (
                    resp.status == 200
                    and isinstance(resp, web.Response)
                    and "gzip" in (request.headers.get("Accept-Encoding", ""))
                    and (resp.content_type or "").startswith(("application/json", "text/"))
                    and not resp.headers.get("Content-Encoding")
                    and resp.body is not None
                    and len(resp.body) > 256
                ):
                    import gzip

                    compressed = gzip.compress(resp.body)
                    resp.body = compressed
                    resp.headers["Content-Encoding"] = "gzip"
                    resp.headers["Vary"] = "Accept-Encoding"
            except Exception:
                pass
            # Add cache and security headers
            resp.headers.setdefault("X-Content-Type-Options", "nosniff")
            resp.headers.setdefault("X-Frame-Options", "DENY")
            resp.headers.setdefault("Cache-Control", "private, max-age=60")
            return resp

        app = web.Application(middlewares=[gzip_middleware])

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

        # DB health endpoint
        async def db_health(request):
            try:
                from database.db import ENGINE
                from sqlalchemy import text as _text

                with ENGINE.connect() as conn:
                    conn.execute(_text("SELECT 1"))
                return web.json_response({"db": "ok"})
            except Exception as e:
                return web.json_response({"db": "error", "error": str(e)}, status=500)

        # Telegram webhook endpoint
        async def telegram_webhook(request):
            if request.method != "POST":
                return web.Response(status=405)

            try:
                # Basic trace for incoming webhook
                logger.info("Incoming Telegram webhook POST")
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
                if not request.content_type or "application/json" not in request.content_type:
                    logger.warning(f"Invalid content type: {request.content_type}")
                    return web.Response(status=400)

                data = await request.json()
                if not data:
                    logger.warning("Empty webhook data received")
                    return web.Response(status=400)

                # Process update (ensure DB schema at start of bursts)
                try:
                    from database.migrate import init_db

                    init_db()
                except Exception:
                    pass
                update = Update.de_json(data, application.bot)
                # Avoid logging raw user content to protect sensitive data
                try:
                    if update.message:
                        logger.info(
                            f"Update message from user_id={getattr(update.effective_user,'id',0)}"
                        )
                    elif update.callback_query:
                        logger.info(
                            f"Update callback from user_id={getattr(update.effective_user,'id',0)}"
                        )
                except Exception:
                    pass
                await application.process_update(update)
                return web.json_response({"ok": True})
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in webhook: {e}")
                return web.Response(status=400)
            except Exception as e:
                logger.error(f"Error processing webhook update: {e}")
                return web.Response(status=500)

        # Admin dashboard (token-protected) - minimal HTML/JSON
        async def _require_token(request):
            token = request.query.get("token", "").strip()
            if not token and request.method.upper() == "POST":
                try:
                    data = await request.post()
                    token = (data.get("token") or "").strip()
                except Exception:
                    token = ""
            expected = (config.bot.admin_dashboard_token or "").strip()
            if not expected or token != expected:
                return None
            return token

        async def admin_list(request):
            try:
                token_ok = await _require_token(request)
                if token_ok is None:
                    return web.Response(status=401, text="unauthorized")
                from sqlalchemy import select
                from database.db import session_scope
                from database.models_sql import Purchase, User as DBUser
                from database.service import (
                    get_stats_summary,
                    list_stale_pending_purchases,
                )
                import secrets

                f = _parse_admin_filters(request)

                stmt = select(Purchase)
                if f["status"]:
                    stmt = stmt.where(Purchase.status == f["status"])
                if f["ptype"] in ("book", "course"):
                    stmt = stmt.where(Purchase.product_type == f["ptype"])
                if f["product_q"]:
                    stmt = stmt.where(Purchase.product_id.like(f"%{f['product_q']}%"))
                if f["dt_from"] is not None:
                    stmt = stmt.where(Purchase.created_at >= f["dt_from"])
                if f["dt_to"] is not None:
                    stmt = stmt.where(Purchase.created_at < f["dt_to"])
                if f["uid"] is not None:
                    stmt = stmt.join(DBUser, DBUser.id == Purchase.user_id).where(
                        DBUser.telegram_user_id == f["uid"]
                    )
                stmt = stmt.order_by(Purchase.created_at.desc())

                try:
                    items = _query_purchases_filtered(stmt)
                except Exception:
                    return web.Response(status=500, text="server error")

                total = len(items)
                start = f["page"] * f["page_size"]
                slice_items = items[start : start + f["page_size"]]
                rows = [
                    {
                        "id": p.id,
                        "user_id": p.user_id,
                        "type": p.product_type,
                        "product": p.product_id,
                        "status": p.status,
                        "created_at": (
                            getattr(p, "created_at", None).isoformat()
                            if getattr(p, "created_at", None)
                            else None
                        ),
                    }
                    for p in slice_items
                ]

                accept = request.headers.get("Accept", "")
                wants_csv = f["fmt"] == "csv" or ("text/csv" in accept)
                if wants_csv:
                    import csv, io

                    # Map internal user_id -> telegram_user_id and demographics for richer exports
                    try:
                        user_ids = {getattr(p, "user_id", None) for p in items}
                        user_ids.discard(None)
                        tg_map = {}
                        user_demo = {}
                        if user_ids:
                            from sqlalchemy import select as _select
                            from database.models_sql import User as _User

                            with session_scope() as _s:
                                for _id, _tg, _city, _grade in _s.execute(
                                    _select(
                                        _User.id,
                                        _User.telegram_user_id,
                                        _User.city,
                                        _User.grade,
                                    ).where(_User.id.in_(list(user_ids)))
                                ):
                                    tg_map[int(_id)] = int(_tg)
                                    user_demo[int(_id)] = {
                                        "city": _city or "",
                                        "grade": _grade or "",
                                    }
                    except Exception:
                        tg_map = {}
                        user_demo = {}

                    # Load course price map (best-effort)
                    course_price = {}
                    try:
                        import json as _json

                        with open("data/courses.json", "r", encoding="utf-8") as _f:
                            _all = _json.load(_f)
                        for c in _all or []:
                            slug = c.get("course_id") or c.get("slug")
                            if slug:
                                course_price[slug] = c.get("price")
                    except Exception:
                        course_price = {}

                    buf = io.StringIO()
                    writer = csv.writer(buf)
                    writer.writerow(
                        [
                            "id",
                            "user_id",
                            "telegram_user_id",
                            "city",
                            "grade",
                            "product_type",
                            "product_id",
                            "status",
                            "payment_status",
                            "amount",
                            "discount",
                            "payment_method",
                            "transaction_id",
                            "admin_action_by",
                            "admin_action_at",
                            "created_at",
                        ]
                    )
                    for p in items:
                        _uid = getattr(p, "user_id", None)
                        _tg = tg_map.get(_uid, None)
                        _demo = user_demo.get(_uid, {"city": "", "grade": ""})
                        _amount = None
                        _discount = None
                        if getattr(p, "product_type", None) == "course":
                            _amount = course_price.get(getattr(p, "product_id", ""))
                        _payment_status = getattr(p, "status", None)
                        _payment_method = None
                        _transaction_id = None
                        writer.writerow(
                            [
                                getattr(p, "id", None),
                                _uid,
                                _tg,
                                _demo.get("city"),
                                _demo.get("grade"),
                                getattr(p, "product_type", None),
                                getattr(p, "product_id", None),
                                getattr(p, "status", None),
                                _payment_status,
                                _amount,
                                _discount,
                                _payment_method,
                                _transaction_id,
                                getattr(p, "admin_action_by", None),
                                (
                                    p.admin_action_at.isoformat()
                                    if getattr(p, "admin_action_at", None)
                                    else ""
                                ),
                                (
                                    p.created_at.isoformat()
                                    if getattr(p, "created_at", None)
                                    else ""
                                ),
                            ]
                        )
                    csv_bytes = buf.getvalue().encode("utf-8")
                    return web.Response(
                        body=csv_bytes,
                        content_type="text/csv",
                        headers={
                            "Content-Disposition": f"attachment; filename=orders_{f['status'] or 'all'}.csv"
                        },
                        charset="utf-8",
                    )

                # XLSX export
                if f["fmt"] == "xlsx":
                    try:
                        import io
                        from openpyxl import Workbook

                        # Map internal user_id -> telegram_user_id and demographics for richer exports
                        try:
                            user_ids = {getattr(p, "user_id", None) for p in items}
                            user_ids.discard(None)
                            tg_map = {}
                            user_demo = {}
                            if user_ids:
                                from sqlalchemy import select as _select
                                from database.models_sql import User as _User

                                with session_scope() as _s:
                                    for _id, _tg, _city, _grade in _s.execute(
                                        _select(
                                            _User.id,
                                            _User.telegram_user_id,
                                            _User.city,
                                            _User.grade,
                                        ).where(_User.id.in_(list(user_ids)))
                                    ):
                                        tg_map[int(_id)] = int(_tg)
                                        user_demo[int(_id)] = {
                                            "city": _city or "",
                                            "grade": _grade or "",
                                        }
                        except Exception:
                            tg_map = {}
                            user_demo = {}

                        # Load course price map (best-effort)
                        course_price = {}
                        try:
                            import json as _json

                            with open("data/courses.json", "r", encoding="utf-8") as _f:
                                _all = _json.load(_f)
                            for c in _all or []:
                                slug = c.get("course_id") or c.get("slug")
                                if slug:
                                    course_price[slug] = c.get("price")
                        except Exception:
                            course_price = {}

                        wb = Workbook()
                        ws = wb.active
                        ws.title = "orders"
                        ws.append(
                            [
                                "id",
                                "user_id",
                                "telegram_user_id",
                                "city",
                                "grade",
                                "product_type",
                                "product_id",
                                "status",
                                "payment_status",
                                "amount",
                                "discount",
                                "payment_method",
                                "transaction_id",
                                "admin_action_by",
                                "admin_action_at",
                                "created_at",
                            ]
                        )
                        for p in items:
                            _uid = getattr(p, "user_id", None)
                            _tg = tg_map.get(_uid, None)
                            _demo = user_demo.get(_uid, {"city": "", "grade": ""})
                            _amount = None
                            _discount = None
                            if getattr(p, "product_type", None) == "course":
                                _amount = course_price.get(getattr(p, "product_id", ""))
                            _payment_status = getattr(p, "status", None)
                            _payment_method = None
                            _transaction_id = None
                            ws.append(
                                [
                                    getattr(p, "id", None),
                                    _uid,
                                    _tg,
                                    _demo.get("city"),
                                    _demo.get("grade"),
                                    getattr(p, "product_type", None),
                                    getattr(p, "product_id", None),
                                    getattr(p, "status", None),
                                    _payment_status,
                                    _amount,
                                    _discount,
                                    _payment_method,
                                    _transaction_id,
                                    getattr(p, "admin_action_by", None),
                                    (
                                        p.admin_action_at.isoformat()
                                        if getattr(p, "admin_action_at", None)
                                        else ""
                                    ),
                                    (
                                        p.created_at.isoformat()
                                        if getattr(p, "created_at", None)
                                        else ""
                                    ),
                                ]
                            )
                        bio = io.BytesIO()
                        wb.save(bio)
                        bio.seek(0)
                        return web.Response(
                            body=bio.getvalue(),
                            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            headers={
                                "Content-Disposition": f"attachment; filename=orders_{f['status'] or 'all'}.xlsx"
                            },
                        )
                    except Exception as e:
                        logger.error(f"xlsx export failed: {e}")
                        return web.Response(status=500, text="xlsx error")

                if "text/html" in accept or not accept:
                    qbase = f"/admin?token={config.bot.admin_dashboard_token}"

                    def _qs(**kw):
                        return _build_admin_qs(
                            qbase,
                            f["status"],
                            f["ptype"],
                            f["uid_str"],
                            f["product_q"],
                            f["from_str"],
                            f["to_str"],
                            f["page_size"],
                            kw.get("page", f["page"]),
                        )

                    csrf_value = request.cookies.get("csrf")
                    if not csrf_value or len(csrf_value) < 16:
                        csrf_value = secrets.token_urlsafe(32)

                    flash_msg = request.cookies.get("flash", "")
                    flash_type = request.cookies.get("flash_type", "success")
                    flash_html = (
                        f"<div class='flash {flash_type}'>{flash_msg}</div>" if flash_msg else ""
                    )

                    # Build dynamic payment method options from config
                    try:
                        _methods = list(config.bot.payment_methods or ["card", "cash", "transfer"])
                    except Exception:
                        _methods = ["card", "cash", "transfer"]
                    _default_pm = (config.bot.default_payment_method or "").strip().lower()
                    # Optionally move default to the front
                    if _default_pm and config.bot.payment_default_first:
                        if _default_pm in _methods:
                            _methods = [_default_pm] + [m for m in _methods if m != _default_pm]

                    # Localized labels for methods
                    _labels = {}
                    try:
                        _labels = dict(config.bot.payment_method_labels or {})
                    except Exception:
                        _labels = {}

                    def _label_for(m: str) -> str:
                        return _labels.get(m, m)

                    # Placeholder text optionally shows default, using label
                    if config.bot.payment_placeholder_show_default and _default_pm:
                        _placeholder = f"انتخاب روش پرداخت (پیش‌فرض: {_label_for(_default_pm)})"
                    else:
                        _placeholder = "انتخاب روش پرداخت"

                    _method_opts = "".join(
                        [f"<option value='' selected>{_placeholder}</option>"]
                        + [
                            (
                                f"<option value='{m}' selected>{_label_for(m)}</option>"
                                if m == _default_pm
                                else f"<option value='{m}'>{_label_for(m)}</option>"
                            )
                            for m in _methods
                        ]
                    )

                    # Admin UI i18n dictionary (for button labels, etc.)
                    _ui = {}
                    try:
                        _ui = dict(config.bot.admin_ui_labels or {})
                    except Exception:
                        _ui = {}

                    def _ui_t(key: str, default: str) -> str:
                        return _ui.get(key, default)

                    html_rows = "".join(
                        f"<tr><td>{r['id']}</td><td>{r['user_id']}</td><td>{r['type']}</td><td>{r['product']}</td><td>{r.get('created_at','')}</td><td><span class='badge {r['status']}'>{r['status']}</span></td>"
                        f"<td>"
                        f"<form method='POST' action='/admin/act' style='display:inline'>"
                        f"<input type='hidden' name='token' value='{config.bot.admin_dashboard_token}'/>"
                        f"<input type='hidden' name='id' value='{r['id']}'/>"
                        f"<input type='hidden' name='action' value='approve'/>"
                        f"<input type='hidden' name='csrf' value='{csrf_value}'/>"
                        f"<input type='hidden' name='redirect' value='{_qs(page=f['page'])}'/>"
                        f"<select name='payment_method' title='روش پرداخت را انتخاب کنید' style='width:140px;margin-inline:4px'>{_method_opts}</select>"
                        f"<input type='text' name='transaction_id' placeholder='شناسه تراکنش' title='شناسه تراکنش (در صورت وجود)' style='width:140px;margin-inline:4px'/>"
                        f"<input type='number' name='discount' placeholder='تخفیف' title='مبلغ تخفیف (اختیاری)' style='width:100px;margin-inline:4px'/>"
                        f"<button class='btn approve' type='submit'>{_ui_t('approve_button','تایید')}</button>"
                        f"</form> "
                        f"<form method='POST' action='/admin/act' style='display:inline'>"
                        f"<input type='hidden' name='token' value='{config.bot.admin_dashboard_token}'/>"
                        f"<input type='hidden' name='id' value='{r['id']}'/>"
                        f"<input type='hidden' name='action' value='reject'/>"
                        f"<input type='hidden' name='csrf' value='{csrf_value}'/>"
                        f"<input type='hidden' name='redirect' value='{_qs(page=f['page'])}'/>"
                        f"<button class='btn reject' type='submit'>{_ui_t('reject_button','رد')}</button>"
                        f"</form>"
                        f"</td></tr>"
                        for r in rows
                    )

                    # Stats summary (top)
                    try:
                        with session_scope() as session:
                            stats = get_stats_summary(session)
                            stale = list_stale_pending_purchases(session, older_than_days=14)
                    except Exception:
                        stats = {
                            "users": 0,
                            "purchases": {},
                            "grades": [],
                            "cities_top": [],
                        }
                        stale = []
                    # i18n for admin UI labels
                    _ui = {}
                    try:
                        _ui = dict(config.bot.admin_ui_labels or {})
                    except Exception:
                        _ui = {}

                    def _ui_t(key: str, default: str) -> str:
                        return _ui.get(key, default)

                    stats_html = (
                        f"<div class='meta'>{_ui_t('users','کاربران')}: {stats.get('users',0)} | "
                        f"{_ui_t('orders','سفارش‌ها')}: {_ui_t('total','کل')} {stats.get('purchases',{}).get('total',0)}، "
                        f"{_ui_t('pending','در انتظار')} {stats.get('purchases',{}).get('pending',0)}</div>"
                    )
                    stale_html = ""
                    if stale:
                        stale_html = (
                            f"<details><summary>{_ui_t('stale_pending','در انتظارهای قدیمی')} (14+ روز)</summary><ul>"
                            + "".join(
                                f"<li>#{s['purchase_id']} | u={s['user_id']} | {s['product_type']}:{s['product_id']} | {s['created_at']}</li>"
                                for s in stale[:20]
                            )
                            + "</ul></details>"
                        )
                    body = f"""
                    <html>
                    <head>
                      <meta charset='utf-8'>
                      <title>{_ui_t('admin_title','مدیریت سفارش‌ها')}</title>
                       <style>
                        body {{ font-family: Vazirmatn, tahoma, sans-serif; margin: 24px; background:#f8fafc; color:#0f172a; }}
                        h3 {{ margin-top:0; }}
                        .panel {{ background:#fff; border:1px solid #e2e8f0; border-radius:8px; padding:16px; box-shadow:0 1px 2px rgba(0,0,0,0.04); }}
                        table {{ width:100%; border-collapse:collapse; margin-top:12px; }}
                        th, td {{ border-bottom:1px solid #e2e8f0; padding:8px 10px; text-align:left; }}
                        th {{ background:#f1f5f9; font-weight:600; }}
                        .controls {{ display:flex; gap:8px; margin:10px 0; align-items:center; flex-wrap:wrap; }}
                        input, select {{ padding:6px 8px; border:1px solid #cbd5e1; border-radius:6px; }}
                        input[type='text']{{ width:180px; }}
                        .btn {{ padding:6px 10px; border-radius:6px; text-decoration:none; color:#fff; margin-right:6px; border:none; cursor:pointer; }}
                        .approve {{ background:#16a34a; }}
                        .reject {{ background:#dc2626; }}
                        .filter {{ background:#2563eb; }}
                        .csv {{ background:#0f766e; }}
                        .pager a {{ margin:0 6px; text-decoration:none; color:#2563eb; }}
                        .badge {{ padding:2px 8px; border-radius:999px; font-size:12px; color:#fff; }}
                        .badge.pending {{ background:#ea580c; }}
                        .badge.approved {{ background:#16a34a; }}
                        .badge.rejected {{ background:#dc2626; }}
                        .meta {{ color:#475569; font-size:13px; }}
                         .flash {{ padding:10px 12px; border-radius:6px; margin-bottom:12px; }}
                         .flash.success {{ background:#ecfdf5; color:#065f46; border:1px solid #a7f3d0; }}
                         .flash.error {{ background:#fef2f2; color:#991b1b; border:1px solid #fecaca; }}
                      </style>
                    </head>
                    <body>
                      <div class='panel'>
                        {flash_html}
                         <h3>{_ui_t('orders','سفارش‌ها')} ({f['status']})</h3>
                        {stats_html}
                        <form method='GET' action='/admin' class='controls'>
                          <input type='hidden' name='token' value='{config.bot.admin_dashboard_token}' />
                          <label>{_ui_t('status_label','وضعیت:')}
                            <select name='status'>
                              <option value='pending' {'selected' if f['status']=='pending' else ''}>{_ui_t('status_pending','pending')}</option>
                              <option value='approved' {'selected' if f['status']=='approved' else ''}>{_ui_t('status_approved','approved')}</option>
                              <option value='rejected' {'selected' if f['status']=='rejected' else ''}>{_ui_t('status_rejected','rejected')}</option>
                            </select>
                          </label>
                          <label>{_ui_t('type_label','نوع:')}
                            <select name='type'>
                              <option value='' {'selected' if not f['ptype'] else ''}>{_ui_t('type_all','همه')}</option>
                              <option value='course' {'selected' if f['ptype']=='course' else ''}>{_ui_t('type_course','course')}</option>
                              <option value='book' {'selected' if f['ptype']=='book' else ''}>{_ui_t('type_book','book')}</option>
                            </select>
                          </label>
                          <label>{_ui_t('uid_label','UID:')}
                            <input id='uid' name='uid' value='{f['uid_str']}' placeholder='{_ui_t('uid_placeholder','telegram id')}' />
                          </label>
                          <label>{_ui_t('product_label','محصول:')}
                            <input id='product' name='product' value='{f['product_q']}' placeholder='{_ui_t('product_placeholder','عنوان/شناسه')}' />
                          </label>
                          <label>{_ui_t('from_label','از:')}
                            <input type='date' name='from' value='{f['from_str']}' />
                          </label>
                          <label>{_ui_t('to_label','تا:')}
                            <input type='date' name='to' value='{f['to_str']}' />
                          </label>
                          <label>{_ui_t('page_size_label','سایز صفحه:')}
                            <input type='number' min='1' max='100' name='size' value='{f['page_size']}' />
                          </label>
                          <button class='btn filter' type='submit'>{_ui_t('filter_button','فیلتر')}</button>
                          <a class='btn csv' href='{_qs(page=0)}&format=csv'>{_ui_t('csv_button_label','CSV')}</a>
                        </form>
                        <div class='meta'>
                           {_ui_t('results_total','مجموع نتایج')}: {total} | {_ui_t('page','صفحه')}: {f['page']+1}
                        </div>
                        <table>
                          <thead>
                            <tr><th>{_ui_t('th_id','ID')}</th><th>{_ui_t('th_user','User')}</th><th>{_ui_t('th_type','Type')}</th><th>{_ui_t('th_product','Product')}</th><th>{_ui_t('th_created','Created')}</th><th>{_ui_t('th_status','Status')}</th><th>{_ui_t('th_action','Action')}</th></tr>
                          </thead>
                          <tbody>{html_rows or f"<tr><td colspan=6>{_ui_t('not_found','موردی یافت نشد')}</td></tr>"}</tbody>
                        </table>
                        <div class='pager'>
                          <a href='{_qs(page=max(0, f['page']-1))}'>&laquo; {_ui_t('prev','قبلی')}</a>
                          |
                          <a href='{_qs(page=f['page']+1)}'>{_ui_t('next','بعدی')} &raquo;</a>
                        </div>
                        <div class='controls' style='margin-top:10px;'>
                          <a class='btn csv' href='{_qs(page=0)}&format=csv'>{_ui_t('csv_button_label','CSV')}</a>
                          <a class='btn filter' href='{_qs(page=0)}&format=xlsx'>{_ui_t('xlsx_button_label','XLSX')}</a>
                        </div>
                        {stale_html}
                      </div>
                      <script>
                        const form = document.querySelector('form.controls');
                        const uidInput = document.getElementById('uid');
                        const productInput = document.getElementById('product');
                        let t1=null, t2=null;
                        uidInput && uidInput.addEventListener('input', ()=>{{ clearTimeout(t1); t1=setTimeout(()=>form.submit(), 550); }});
                        productInput && productInput.addEventListener('input', ()=>{{ clearTimeout(t2); t2=setTimeout(()=>form.submit(), 550); }});
                      </script>
                    </body></html>
                    """
                    resp = web.Response(text=body, content_type="text/html", charset="utf-8")
                    try:
                        resp.set_cookie(
                            "csrf",
                            csrf_value,
                            max_age=3600,
                            path="/",
                            secure=str(config.webhook.url).startswith("https://"),
                            httponly=True,
                            samesite="Lax",
                        )
                    except Exception:
                        pass
                    return resp

                return web.json_response(
                    {
                        "status": f["status"],
                        "type": f["ptype"],
                        "uid": f["uid"],
                        "product": f["product_q"],
                        "from": f["from_str"],
                        "to": f["to_str"],
                        "page": f["page"],
                        "page_size": f["page_size"],
                        "total": total,
                        "items": rows,
                    }
                )
            except Exception as e:
                logger.error(f"admin_list error: {e}")
                return web.Response(status=500, text="server error")

        async def admin_act(request):
            try:
                token_ok = await _require_token(request)
                if token_ok is None:
                    return web.Response(status=401, text="unauthorized")
                from sqlalchemy import select
                from database.db import session_scope
                from database.models_sql import Purchase
                from database.service import approve_or_reject_purchase

                pid = int(request.query.get("id", "0") or 0)
                action = request.query.get("action", "").lower()
                if action not in ("approve", "reject") or pid <= 0:
                    return web.Response(status=400, text="bad request")

                # For audit purposes, attribute to first admin id
                admin_id = (config.bot.admin_user_ids or [0])[0]

                try:
                    with session_scope() as session:
                        db_purchase = session.execute(
                            select(Purchase).where(Purchase.id == pid)
                        ).scalar_one_or_none()
                        if not db_purchase or db_purchase.status != "pending":
                            return web.Response(status=404, text="not found or already decided")
                        # Accept optional financial fields
                        pm = (request.query.get("payment_method") or "").strip().lower() or None
                        tx = (request.query.get("transaction_id") or "").strip() or None
                        try:
                            dc = int(request.query.get("discount") or 0)
                        except Exception:
                            dc = None
                        # Validate payment method
                        _allowed_pm = set(
                            config.bot.payment_methods or ["card", "cash", "transfer"]
                        )
                        if pm not in _allowed_pm:
                            pm = None
                        # Validate transaction id (basic)
                        if tx and not (4 <= len(tx) <= 64):
                            tx = None
                        if pm:
                            db_purchase.payment_method = pm
                        if tx:
                            db_purchase.transaction_id = tx
                        if dc is not None:
                            db_purchase.discount = dc
                        result = approve_or_reject_purchase(
                            session, db_purchase.id, admin_id, action
                        )
                        if not result:
                            return web.Response(status=409, text="conflict")
                except Exception as e:
                    try:
                        logger.warning(f"admin_act query failed, attempting DB init: {e}")
                        from database.migrate import init_db

                        init_db()
                        with session_scope() as session:
                            db_purchase = session.execute(
                                select(Purchase).where(Purchase.id == pid)
                            ).scalar_one_or_none()
                            if not db_purchase or db_purchase.status != "pending":
                                return web.Response(status=404, text="not found or already decided")
                            result = approve_or_reject_purchase(
                                session, db_purchase.id, admin_id, action
                            )
                            if not result:
                                return web.Response(status=409, text="conflict")
                    except Exception as e2:
                        logger.error(f"admin_act fatal DB error after init retry: {e2}")
                        return web.Response(status=500, text="server error")

                # Try to notify student and admins asynchronously (fire-and-forget)
                try:
                    admin_ip = request.headers.get("X-Forwarded-For", request.remote)
                    logger.info(f"Admin action via GET: id={pid} action={action} ip={admin_ip}")
                    student_id = (
                        db_purchase.user_id
                    )  # DB user numeric id; need telegram id lookup if necessary
                    # In this codebase, Purchase.user_id refers to internal users.id; we need telegram id for messaging.
                    from database.models_sql import User as DBUser

                    with session_scope() as session:
                        u = session.execute(
                            select(DBUser).where(DBUser.id == db_purchase.user_id)
                        ).scalar_one_or_none()
                    if u:
                        text = (
                            f"✅ پرداخت شما برای «{db_purchase.product_id}» تایید شد."
                            if action == "approve"
                            else f"❌ پرداخت شما برای «{db_purchase.product_id}» رد شد."
                        )
                        asyncio.create_task(
                            application.bot.send_message(chat_id=u.telegram_user_id, text=text)
                        )
                except Exception:
                    pass

                return web.json_response({"ok": True, "id": pid, "action": action})
            except Exception as e:
                logger.error(f"admin_act error: {e}")
                return web.Response(status=500, text="server error")

        async def admin_act_post(request):
            data = None
            redirect_to = ""
            try:
                token_ok = await _require_token(request)
                if token_ok is None:
                    return web.Response(status=401, text="unauthorized")
                data = await request.post()
                csrf_cookie = request.cookies.get("csrf", "")
                csrf_form = (data.get("csrf") or "").strip()
                redirect_to = data.get("redirect") or ""
                if not csrf_cookie or not csrf_form or csrf_cookie != csrf_form:
                    return web.Response(status=403, text="forbidden")

                # Admin UI i18n labels for flash messages
                _ui = {}
                try:
                    _ui = dict(config.bot.admin_ui_labels or {})
                except Exception:
                    _ui = {}

                def _ui_t(key: str, default: str) -> str:
                    return _ui.get(key, default)

                from sqlalchemy import select
                from database.db import session_scope
                from database.models_sql import Purchase, User as DBUser
                from database.service import approve_or_reject_purchase

                try:
                    pid = int((data.get("id") or "0"))
                except ValueError:
                    return web.Response(status=400, text="bad request")
                action = (data.get("action") or "").lower()
                if action not in ("approve", "reject") or pid <= 0:
                    return web.Response(status=400, text="bad request")

                admin_id = (config.bot.admin_user_ids or [0])[0]
                admin_ip = request.headers.get("X-Forwarded-For", request.remote)
                try:
                    with session_scope() as session:
                        db_purchase = session.execute(
                            select(Purchase).where(Purchase.id == pid)
                        ).scalar_one_or_none()
                        if not db_purchase or db_purchase.status != "pending":
                            return web.Response(status=404, text="not found or already decided")
                        # Accept optional financial fields from POST
                        pm = (data.get("payment_method") or "").strip().lower() or None
                        tx = (data.get("transaction_id") or "").strip() or None
                        try:
                            dc = int(data.get("discount") or 0)
                        except Exception:
                            dc = None
                        _allowed_pm = set(
                            config.bot.payment_methods or ["card", "cash", "transfer"]
                        )
                        if pm not in _allowed_pm:
                            pm = None
                        if tx and not (4 <= len(tx) <= 64):
                            tx = None
                        if pm:
                            db_purchase.payment_method = pm
                        if tx:
                            db_purchase.transaction_id = tx
                        if dc is not None:
                            db_purchase.discount = dc
                        result = approve_or_reject_purchase(
                            session, db_purchase.id, admin_id, action
                        )
                        if not result:
                            return web.Response(status=409, text="conflict")
                except Exception as e:
                    try:
                        logger.warning(f"admin_act_post query failed, attempting DB init: {e}")
                        from database.migrate import init_db

                        init_db()
                        with session_scope() as session:
                            db_purchase = session.execute(
                                select(Purchase).where(Purchase.id == pid)
                            ).scalar_one_or_none()
                            if not db_purchase or db_purchase.status != "pending":
                                return web.Response(status=404, text="not found or already decided")
                            result = approve_or_reject_purchase(
                                session, db_purchase.id, admin_id, action
                            )
                            if not result:
                                return web.Response(status=409, text="conflict")
                    except Exception as e2:
                        logger.error(f"admin_act_post fatal DB error after init retry: {e2}")
                        # Redirect back with error if possible
                        if redirect_to:
                            resp = web.HTTPSeeOther(location=redirect_to)
                            try:
                                resp.set_cookie(
                                    "flash",
                                    _ui_t("flash_error", "خطا در انجام عملیات"),
                                    max_age=10,
                                    path="/",
                                    secure=str(config.webhook.url).startswith("https://"),
                                    samesite="Strict",
                                )
                                resp.set_cookie(
                                    "flash_type",
                                    "error",
                                    max_age=10,
                                    path="/",
                                    secure=str(config.webhook.url).startswith("https://"),
                                    samesite="Strict",
                                )
                            except Exception:
                                pass
                            raise resp
                        return web.Response(status=500, text="server error")

                # Notify student fire-and-forget
                try:
                    with session_scope() as session:
                        u = session.execute(
                            select(DBUser).where(DBUser.id == db_purchase.user_id)
                        ).scalar_one_or_none()
                    if u:
                        text = (
                            f"✅ پرداخت شما برای «{db_purchase.product_id}» تایید شد."
                            if action == "approve"
                            else f"❌ پرداخت شما برای «{db_purchase.product_id}» رد شد."
                        )
                        asyncio.create_task(
                            application.bot.send_message(chat_id=u.telegram_user_id, text=text)
                        )
                    try:
                        logger.info(
                            f"Admin action via POST: id={pid} action={action} ip={admin_ip}"
                        )
                    except Exception:
                        pass
                except Exception:
                    pass

                if redirect_to:
                    # Set flash message for one redirect
                    msg = (
                        _ui_t("flash_approve_success", "با موفقیت تایید شد.")
                        if action == "approve"
                        else _ui_t("flash_reject_success", "با موفقیت رد شد.")
                    )
                    resp = web.HTTPSeeOther(location=redirect_to)
                    try:
                        resp.set_cookie(
                            "flash",
                            msg,
                            max_age=10,
                            path="/",
                            secure=str(config.webhook.url).startswith("https://"),
                            samesite="Lax",
                        )
                        resp.set_cookie(
                            "flash_type",
                            "success",
                            max_age=10,
                            path="/",
                            secure=str(config.webhook.url).startswith("https://"),
                            samesite="Lax",
                        )
                    except Exception:
                        pass
                    raise resp
                return web.json_response({"ok": True, "id": pid, "action": action})
            except web.HTTPException:
                raise
            except Exception as e:
                logger.error(f"admin_act_post error: {e}")
                # Redirect back with error flash if we already parsed body
                if redirect_to:
                    resp = web.HTTPSeeOther(location=redirect_to)
                    try:
                        resp.set_cookie(
                            "flash",
                            _ui_t("flash_error", "خطا در انجام عملیات"),
                            max_age=10,
                            path="/",
                            secure=str(config.webhook.url).startswith("https://"),
                            samesite="Lax",
                        )
                        resp.set_cookie(
                            "flash_type",
                            "error",
                            max_age=10,
                            path="/",
                            secure=str(config.webhook.url).startswith("https://"),
                            samesite="Lax",
                        )
                    except Exception:
                        pass
                    raise resp
                return web.Response(status=500, text="server error")

        async def admin_init(request):
            try:
                token_ok = await _require_token(request)
                if token_ok is None:
                    return web.Response(status=401, text="unauthorized")
                try:
                    from database.migrate import init_db

                    init_db()
                    return web.Response(text="ok", content_type="text/plain", charset="utf-8")
                except Exception as e:
                    logger.error(f"admin_init error: {e}")
                    return web.Response(status=500, text="init error")
            except Exception as e:
                logger.error(f"admin_init fatal: {e}")
                return web.Response(status=500, text="server error")

        # Add routes
        app.router.add_get("/", health_check)
        app.router.add_get("/admin", admin_list)
        app.router.add_get("/admin/act", admin_act)
        app.router.add_get("/admin/init", admin_init)
        app.router.add_post("/admin/act", admin_act_post)
        app.router.add_get("/db/health", db_health)
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
                        config.webhook.secret_token if config.webhook.secret_token else None
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
                    logger.error(f"Failed to set webhook after {max_retries} attempts: {e}")
                    raise

        logger.info(f"✅ Health check at: http://0.0.0.0:{config.webhook.port}/")

        # Start background maintenance tasks (rate limiter cleanup)
        try:
            await multi_rate_limiter.start_cleanup_tasks()
        except Exception as e:
            logger.warning(f"Could not start rate limiter cleanup tasks: {e}")

        # 24/7 watchdog: periodically verify DB and webhook health and auto-heal
        async def _watchdog_task():
            interval = max(60, int(os.getenv("WATCHDOG_INTERVAL_SECONDS", "300") or 300))
            expected_webhook = config.webhook.url.rstrip("/") + config.webhook.path
            from database.db import ENGINE
            from sqlalchemy import text as _text

            while True:
                try:
                    # DB ping
                    try:
                        with ENGINE.connect() as _conn:
                            _conn.execute(_text("SELECT 1"))
                    except Exception as de:
                        logger.warning(f"Watchdog DB ping failed: {de}. Attempting init_db().")
                        try:
                            from database.migrate import init_db

                            init_db()
                        except Exception as ie:
                            logger.error(f"Watchdog init_db failed: {ie}")

                    # Webhook verification
                    try:
                        info = await application.bot.get_webhook_info()
                        if (
                            not info
                            or str(info.url or "") != expected_webhook
                            or getattr(info, "last_error_date", None)
                        ):
                            await application.bot.set_webhook(
                                url=expected_webhook,
                                drop_pending_updates=False,
                                secret_token=(
                                    config.webhook.secret_token
                                    if config.webhook.secret_token
                                    else None
                                ),
                                max_connections=40,
                            )
                            logger.info("Watchdog reset webhook to expected URL")
                    except Exception as we:
                        logger.warning(f"Watchdog webhook check failed: {we}")
                except Exception as e:
                    logger.warning(f"Watchdog unexpected error: {e}")
                await asyncio.sleep(interval)

        watchdog_handle = asyncio.create_task(_watchdog_task())
        application.bot_data["watchdog"] = watchdog_handle

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
                logger.warning(f"Warning: Could not delete webhook during shutdown: {e}")

            await application.stop()
            await application.shutdown()
            # Stop watchdog
            try:
                wd = application.bot_data.get("watchdog")
                if wd:
                    wd.cancel()
            except Exception:
                pass
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

        # Initialize database schema (idempotent)
        try:
            from database.migrate import init_db

            init_db()
            logger.info("🗄️ Database initialized (create_all)")
        except Exception as e:
            logger.warning(f"DB init skipped/failed: {e}")

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

        # No JSON storage; DB is source of truth
        application.bot_data["config"] = config
        application.bot_data["broadcast_manager"] = BroadcastManager()

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
