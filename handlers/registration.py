#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Registration handlers for Ostad Hatami Bot
Implements 6-step registration process with validation
"""

import re
from enum import Enum
from typing import Dict, Any

from telegram import Update, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from config import config
from utils.storage import StudentStorage
from ui.keyboards import (
    build_register_keyboard,
    build_grades_keyboard,
    build_majors_keyboard,
    build_provinces_keyboard,
    build_cities_keyboard,
    build_confirmation_keyboard,
)


# States for the registration conversation
class RegistrationStates(Enum):
    FIRST_NAME = 1
    LAST_NAME = 2
    PROVINCE = 3
    CITY = 4
    GRADE = 5
    FIELD = 6
    CONFIRM = 7


def _is_persian_text(text: str) -> bool:
    """Validate Persian text input"""
    if not text or len(text) < 2 or len(text) > 50:
        return False
    return bool(re.fullmatch(r"[\u0600-\u06FF\s]{2,50}", text))


async def start_registration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start registration process"""
    context.user_data.clear()  # Clear any previous registration data
    context.user_data["registration"] = {}  # Initialize with minimal structure
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        "👋 به فرآیند ثبت‌نام خوش آمدید!\n\n" "لطفاً نام خود را به فارسی وارد کنید:",
    )
    return RegistrationStates.FIRST_NAME


async def first_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle first name input"""
    name = update.message.text.strip()
    if not _is_persian_text(name):
        await update.message.reply_text(
            "❌ نام باید فارسی و بین ۲ تا ۵۰ کاراکتر باشد.\n" "لطفاً دوباره وارد کنید:"
        )
        return RegistrationStates.FIRST_NAME

    context.user_data["first_name"] = name
    await update.message.reply_text("لطفاً نام خانوادگی خود را به فارسی وارد کنید:")
    return RegistrationStates.LAST_NAME


async def last_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle last name input"""
    name = update.message.text.strip()
    if not _is_persian_text(name):
        await update.message.reply_text(
            "❌ نام خانوادگی باید فارسی و بین ۲ تا ۵۰ کاراکتر باشد.\n"
            "لطفاً دوباره وارد کنید:"
        )
        return RegistrationStates.LAST_NAME

    context.user_data["last_name"] = name
    await update.message.reply_text(
        "لطفاً استان خود را انتخاب کنید:",
        reply_markup=build_provinces_keyboard(config.provinces),
    )
    return RegistrationStates.PROVINCE


async def province(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle province selection"""
    query = update.callback_query
    await query.answer()

    province = query.data.replace("province:", "")
    if province not in config.provinces:
        await query.edit_message_text(
            "❌ استان نامعتبر است. لطفاً دوباره انتخاب کنید:",
            reply_markup=build_provinces_keyboard(config.provinces),
        )
        return RegistrationStates.PROVINCE

    context.user_data["province"] = province
    await query.edit_message_text(
        f"استان {province}\n\nلطفاً شهر خود را انتخاب کنید:",
        reply_markup=build_cities_keyboard(config.cities_by_province[province]),
    )
    return RegistrationStates.CITY


async def city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle city selection"""
    query = update.callback_query
    await query.answer()

    city = query.data.replace("city:", "")
    province = context.user_data.get("province", "")
    if not province or city not in config.cities_by_province[province]:
        await query.edit_message_text(
            "❌ شهر نامعتبر است. لطفاً دوباره انتخاب کنید:",
            reply_markup=build_cities_keyboard(config.cities_by_province[province]),
        )
        return RegistrationStates.CITY

    context.user_data["city"] = city
    await query.edit_message_text(
        "لطفاً پایه تحصیلی خود را انتخاب کنید:",
        reply_markup=build_grades_keyboard(config.grades),
    )
    return RegistrationStates.GRADE


async def grade(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle grade selection"""
    query = update.callback_query
    await query.answer()

    grade = query.data.replace("grade:", "")
    if grade not in config.grades:
        await query.edit_message_text(
            "❌ پایه نامعتبر است. لطفاً دوباره انتخاب کنید:",
            reply_markup=build_grades_keyboard(config.grades),
        )
        return RegistrationStates.GRADE

    context.user_data["grade"] = grade
    await query.edit_message_text(
        "لطفاً رشته تحصیلی خود را انتخاب کنید:",
        reply_markup=build_majors_keyboard(config.majors),
    )
    return RegistrationStates.FIELD


async def field(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle field of study selection"""
    query = update.callback_query
    await query.answer()

    field = query.data.replace("major:", "")
    if field not in config.majors:
        await query.edit_message_text(
            "❌ رشته نامعتبر است. لطفاً دوباره انتخاب کنید:",
            reply_markup=build_majors_keyboard(config.majors),
        )
        return RegistrationStates.FIELD

    context.user_data["field"] = field

    # Show confirmation message with all data
    user_data = context.user_data
    confirmation_text = (
        "📋 لطفاً اطلاعات وارد شده را تایید کنید:\n\n"
        f"👤 نام: {user_data['first_name']}\n"
        f"👤 نام خانوادگی: {user_data['last_name']}\n"
        f"📍 استان: {user_data['province']}\n"
        f"🏙 شهر: {user_data['city']}\n"
        f"📚 پایه تحصیلی: {user_data['grade']}\n"
        f"🎓 رشته تحصیلی: {user_data['field']}\n\n"
        "آیا اطلاعات فوق صحیح است؟"
    )

    await query.edit_message_text(
        confirmation_text,
        reply_markup=build_confirmation_keyboard(),
    )
    return RegistrationStates.CONFIRM


async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle registration confirmation"""
    query = update.callback_query
    await query.answer()

    if query.data == "cancel_reg":
        await query.edit_message_text(
            "❌ ثبت‌نام لغو شد. می‌توانید با کلیک روی دکمه زیر دوباره شروع کنید:",
            reply_markup=build_register_keyboard(),
        )
        return ConversationHandler.END

    # Save user data
    storage: StudentStorage = context.bot_data["storage"]
    user_data = {"user_id": update.effective_user.id, **context.user_data}

    if not storage.save_student(user_data):
        await query.edit_message_text(
            "❌ خطا در ذخیره اطلاعات. لطفاً دوباره تلاش کنید:",
            reply_markup=build_register_keyboard(),
        )
        return ConversationHandler.END

    await query.edit_message_text(
        "✅ ثبت‌نام شما با موفقیت انجام شد!\n\n"
        "اکنون می‌توانید از امکانات ربات استفاده کنید.",
    )

    # Show main menu
    from handlers.menu import send_main_menu

    await send_main_menu(update, context)

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel registration"""
    await update.message.reply_text(
        "❌ ثبت‌نام لغو شد. می‌توانید با کلیک روی دکمه زیر دوباره شروع کنید:",
        reply_markup=build_register_keyboard(),
    )
    return ConversationHandler.END


def build_registration_conversation() -> ConversationHandler:
    """Build the registration conversation handler"""
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_registration, pattern="^start_registration$")
        ],
        states={
            RegistrationStates.FIRST_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, first_name)
            ],
            RegistrationStates.LAST_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, last_name)
            ],
            RegistrationStates.PROVINCE: [
                CallbackQueryHandler(province, pattern="^province:")
            ],
            RegistrationStates.CITY: [CallbackQueryHandler(city, pattern="^city:")],
            RegistrationStates.GRADE: [CallbackQueryHandler(grade, pattern="^grade:")],
            RegistrationStates.FIELD: [CallbackQueryHandler(field, pattern="^major:")],
            RegistrationStates.CONFIRM: [
                CallbackQueryHandler(confirm, pattern="^(confirm|cancel)_reg$")
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        name="registration",
        persistent=False,
    )
