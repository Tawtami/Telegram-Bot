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
from utils.storage import StudentStorage
from ui.keyboards import build_main_menu_keyboard, build_register_keyboard

# Cache keyboard markups
_REGISTER_KEYBOARD = build_register_keyboard()
_MAIN_MENU_KEYBOARD = build_main_menu_keyboard()


async def send_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send main menu message with appropriate keyboard"""
    # Get effective chat and user
    chat = update.effective_chat
    user = update.effective_user

    if not chat or not user:
        return

    # Check if user is registered
    storage: StudentStorage = context.bot_data["storage"]
    student = storage.get_student(user.id)

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


async def handle_menu_selection(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle main menu button selections"""
    query = update.callback_query
    if not query:
        return

    await query.answer()

    # Get user and check registration
    user = update.effective_user
    if not user:
        return

    storage: StudentStorage = context.bot_data["storage"]
    student = storage.get_student(user.id)

    if not student and user.id not in config.bot.admin_user_ids:
        await query.edit_message_text(
            "⚠️ لطفاً ابتدا ثبت‌نام کنید:",
            reply_markup=_REGISTER_KEYBOARD,
        )
        return

    # Handle menu options
    option = query.data.replace("menu_", "")

    if option == "profile":
        if not student:
            await query.edit_message_text(
                "❌ پروفایل شما یافت نشد.",
                reply_markup=_REGISTER_KEYBOARD,
            )
            return

        profile_text = (
            "👤 پروفایل شما:\n\n"
            f"نام: {student['first_name']}\n"
            f"نام خانوادگی: {student['last_name']}\n"
            f"استان: {student['province']}\n"
            f"شهر: {student['city']}\n"
            f"پایه تحصیلی: {student['grade']}\n"
            f"رشته تحصیلی: {student['field']}\n\n"
            f"تاریخ ثبت‌نام: {student['registration_date'][:10]}"
        )

        await query.edit_message_text(
            profile_text,
            reply_markup=_MAIN_MENU_KEYBOARD,
        )
        return

    # Other menu options are handled by their respective handlers
    # The callback patterns are matched in bot.py


async def handle_back_to_menu(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle back to menu button"""
    query = update.callback_query
    if not query:
        return

    await query.answer()
    await send_main_menu(update, context)
