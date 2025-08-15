#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main menu handlers for Ostad Hatami Bot
"""

from typing import Any

from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from config import config
from database.db import session_scope
from utils.rate_limiter import rate_limit_handler
from ui.keyboards import build_main_menu_keyboard, build_register_keyboard
from database.db import session_scope
from database.models_sql import User
from sqlalchemy import select
from utils.admin_notify import send_paginated_list
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

# Cache keyboard markups
_REGISTER_KEYBOARD = build_register_keyboard()
_MAIN_MENU_KEYBOARD = build_main_menu_keyboard()


@rate_limit_handler("default")
async def send_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send main menu message with appropriate keyboard"""
    # Get effective chat and user
    chat = update.effective_chat
    user = update.effective_user

    if not chat or not user:
        return

    # Check if user is registered in SQL DB
    with session_scope() as session:
        student = session.execute(
            select(User).where(User.telegram_user_id == user.id)
        ).scalar_one_or_none()

    if not student and user.id not in config.bot.admin_user_ids:
        # User needs to register first
        welcome_text = config.bot.welcome_message_template.format(
            first_name=user.first_name or "کاربر"
        )
        await chat.send_message(
            text=welcome_text,
            reply_markup=_REGISTER_KEYBOARD,
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    # Show main menu
    await chat.send_message(
        text="🏠 منوی اصلی",
        reply_markup=build_main_menu_keyboard(),
        parse_mode=ParseMode.HTML,
    )


@rate_limit_handler("default")
async def handle_menu_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle main menu button selections"""
    query = update.callback_query
    if not query:
        return

    await query.answer()

    # Get user and check registration
    user = update.effective_user
    if not user:
        return

    # Check registration against SQL DB (single source of truth)
    from sqlalchemy import select
    from database.db import session_scope
    from database.models_sql import User as DBUser

    with session_scope() as session:
        db_user = session.execute(
            select(DBUser).where(DBUser.telegram_user_id == user.id)
        ).scalar_one_or_none()

    if not db_user and user.id not in config.bot.admin_user_ids:
        await query.edit_message_text(
            "⚠️ لطفاً ابتدا ثبت‌نام کنید:",
            reply_markup=_REGISTER_KEYBOARD,
        )
        return

    # Handle menu options
    if query.data == "menu_profile":
        option = "profile"
    else:
        option = query.data.replace("menu_", "")

    if option == "profile":
        if not db_user:
            await query.edit_message_text(
                "❌ پروفایل شما یافت نشد.",
                reply_markup=_REGISTER_KEYBOARD,
            )
            return
        profile_text = (
            "👤 **پروفایل شما**\n\n"
            f"📍 **استان:** {db_user.province or '—'}\n"
            f"🏙 **شهر:** {db_user.city or '—'}\n"
            f"📚 **پایه تحصیلی:** {db_user.grade or '—'}\n"
            f"🎓 **رشته تحصیلی:** {db_user.field_of_study or '—'}\n\n"
            "ℹ️ برای حفظ حریم خصوصی، نام و شماره تماس نمایش داده نمی‌شود."
        )

        kb = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("✏️ ویرایش پروفایل", callback_data="menu_profile_edit")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_menu")],
            ]
        )
        await query.edit_message_text(profile_text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
        return

    # Other menu options are handled by their respective handlers
    # The callback patterns are matched in bot.py


@rate_limit_handler("default")
async def handle_back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle back to menu button"""
    query = update.callback_query
    if not query:
        return

    await query.answer()
    await send_main_menu(update, context)


def build_menu_handlers():
    """Build and return menu handlers for registration in bot.py"""
    from telegram.ext import (
        MessageHandler,
        CallbackQueryHandler,
        filters,
        CommandHandler,
    )

    handlers = [
        MessageHandler(filters.Regex(r"^🏠 منوی اصلی$"), send_main_menu),
        CallbackQueryHandler(handle_menu_selection, pattern=r"^menu_"),
        CallbackQueryHandler(handle_back_to_menu, pattern=r"^back_to_menu$"),
    ]

    # Admin list commands (SQL-based)
    async def list_books_cmd(update, context):
        if update.effective_user.id not in config.bot.admin_user_ids:
            return
        from database.service import get_approved_book_buyers

        with session_scope() as session:
            buyers = get_approved_book_buyers(session, limit=1000)
        lines = [f"{b['user_id']} | {b['product_id']} | {b['created_at'].date()}" for b in buyers]
        if len(lines) > 400:
            import csv, io

            buf = io.StringIO()
            writer = csv.writer(buf)
            writer.writerow(["user_id", "product_id", "created_at"])
            for b in buyers:
                writer.writerow([b["user_id"], b["product_id"], b["created_at"].date()])
            buf.seek(0)
            await update.effective_message.reply_document(
                document=io.BytesIO(buf.getvalue().encode("utf-8")),
                filename="book_buyers.csv",
                caption="📚 خریداران کتاب (CSV)",
            )
        else:
            await send_paginated_list(
                context,
                [update.effective_user.id],
                "📚 خریداران کتاب (تاییدشده)",
                lines,
            )

    async def list_free_cmd(update, context):
        if update.effective_user.id not in config.bot.admin_user_ids:
            return
        if not context.args:
            await update.effective_message.reply_text("فرمت: /list_free <پایه>")
            return
        grade = context.args[0]
        from database.service import get_free_course_participants_by_grade

        with session_scope() as session:
            uids = get_free_course_participants_by_grade(session, grade)
        lines = [str(uid) for uid in uids]
        if len(lines) > 400:
            import csv, io

            buf = io.StringIO()
            writer = csv.writer(buf)
            writer.writerow(["user_id"])
            for uid in uids:
                writer.writerow([uid])
            buf.seek(0)
            await update.effective_message.reply_document(
                document=io.BytesIO(buf.getvalue().encode("utf-8")),
                filename=f"free_grade_{grade}.csv",
                caption=f"🎓 شرکت‌کنندگان رایگان پایه {grade} (CSV)",
            )
        else:
            await send_paginated_list(
                context,
                [update.effective_user.id],
                f"🎓 شرکت‌کنندگان رایگان پایه {grade}",
                lines,
            )

    async def list_special_cmd(update, context):
        if update.effective_user.id not in config.bot.admin_user_ids:
            return
        if not context.args:
            await update.effective_message.reply_text("فرمت: /list_special <slug>")
            return
        slug = context.args[0]
        from database.service import get_course_participants_by_slug

        with session_scope() as session:
            uids = get_course_participants_by_slug(session, slug)
        lines = [str(uid) for uid in uids]
        if len(lines) > 400:
            import csv, io

            buf = io.StringIO()
            writer = csv.writer(buf)
            writer.writerow(["user_id"])
            for uid in uids:
                writer.writerow([uid])
            buf.seek(0)
            await update.effective_message.reply_document(
                document=io.BytesIO(buf.getvalue().encode("utf-8")),
                filename=f"course_{slug}.csv",
                caption=f"💼 شرکت‌کنندگان دوره {slug} (CSV)",
            )
        else:
            await send_paginated_list(
                context,
                [update.effective_user.id],
                f"💼 شرکت‌کنندگان دوره {slug}",
                lines,
            )

    handlers.extend(
        [
            CommandHandler("list_books", list_books_cmd),
            CommandHandler("list_free", list_free_cmd),
            CommandHandler("list_special", list_special_cmd),
        ]
    )

    # Profile edit and history handlers (callbacks and commands)
    async def profile_edit_callback(update, context):
        query = update.callback_query
        if not query:
            return
        await query.answer()
        # For brevity, ask user to re-run registration flow to edit; in future, design a stepwise editor
        await query.edit_message_text(
            "برای ویرایش، لطفاً مجدداً ثبت‌نام را اجرا کنید: /register",
            reply_markup=_MAIN_MENU_KEYBOARD,
        )

    async def profile_history_cmd(update, context):
        if update.effective_user.id not in config.bot.admin_user_ids:
            return
        if not context.args:
            await update.effective_message.reply_text("فرمت: /profile_history <telegram_user_id>")
            return
        try:
            target = int(context.args[0])
        except Exception:
            await update.effective_message.reply_text("شناسه نامعتبر است.")
            return
        from database.models_sql import User as DBUser, ProfileChange

        with session_scope() as session:
            db_user = session.execute(
                select(DBUser).where(DBUser.telegram_user_id == target)
            ).scalar_one_or_none()
            if not db_user:
                await update.effective_message.reply_text("کاربر یافت نشد.")
                return
            rows = (
                session.query(ProfileChange)
                .filter(ProfileChange.user_id == db_user.id)
                .order_by(ProfileChange.timestamp.desc())
                .limit(50)
                .all()
            )
        lines = [f"{r.timestamp:%Y-%m-%d %H:%M} | {r.field_name}" for r in rows]
        await send_paginated_list(
            context,
            [update.effective_user.id],
            f"🕒 تاریخچه ویرایش پروفایل {target}",
            lines,
        )

    handlers.extend(
        [
            # menu_profile_edit is provided by handlers.profile.build_profile_edit_handlers
            CommandHandler("profile_history", profile_history_cmd),
        ]
    )
    return handlers
