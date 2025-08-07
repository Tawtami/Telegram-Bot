#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Registration flow using python-telegram-bot (async)
Flow: first_name -> last_name -> province -> city -> grade -> field -> confirm
"""
from __future__ import annotations

from typing import Dict, Any
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    ConversationHandler,
    CallbackContext,
    CallbackQueryHandler,
    MessageHandler,
    CommandHandler,
    filters,
)

from utils.storage import Student, StudentStorage
from utils.keyboards import (
    build_register_keyboard,
    build_back_keyboard,
    build_provinces_keyboard,
    build_cities_keyboard,
    build_grades_keyboard,
    build_majors_keyboard,
    build_main_menu_keyboard,
)
from ui.messages import Messages
from config import Config

FIRST_NAME, LAST_NAME, PROVINCE, CITY, GRADE, FIELD, CONFIRM = range(7)


def _is_persian_text(text: str) -> bool:
    import re

    return bool(re.fullmatch(r"[\u0600-\u06FF\s]{2,50}", text or ""))


async def start_registration(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    await update.callback_query.message.edit_text(
        "📝 نام خود را وارد کنید:", reply_markup=build_back_keyboard("cancel_reg")
    )
    return FIRST_NAME


async def first_name(update: Update, context: CallbackContext):
    name = (update.message.text or "").strip()
    if not _is_persian_text(name):
        await update.message.reply_text("❌ نام باید فارسی و بین ۲ تا ۵۰ کاراکتر باشد.")
        return FIRST_NAME
    context.user_data["first_name"] = name
    await update.message.reply_text(
        "📝 نام خانوادگی را وارد کنید:", reply_markup=build_back_keyboard("cancel_reg")
    )
    return LAST_NAME


async def last_name(update: Update, context: CallbackContext):
    name = (update.message.text or "").strip()
    if not _is_persian_text(name):
        await update.message.reply_text(
            "❌ نام خانوادگی باید فارسی و بین ۲ تا ۵۰ کاراکتر باشد."
        )
        return LAST_NAME
    context.user_data["last_name"] = name

    config: Config = context.bot_data["config"]
    await update.message.reply_text(
        "🏛️ استان خود را انتخاب کنید:",
        reply_markup=build_provinces_keyboard(config.provinces),
    )
    return PROVINCE


async def province(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    province = update.callback_query.data.split(":", 1)[1]
    context.user_data["province"] = province

    config: Config = context.bot_data["config"]
    await update.callback_query.message.edit_text(
        f"🏙️ شهر خود را انتخاب کنید (استان: {province}):",
        reply_markup=build_cities_keyboard(config.cities_by_province.get(province, [])),
    )
    return CITY


async def city(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    city = update.callback_query.data.split(":", 1)[1]
    context.user_data["city"] = city

    config: Config = context.bot_data["config"]
    await update.callback_query.message.edit_text(
        "🎓 مقطع تحصیلی را انتخاب کنید:",
        reply_markup=build_grades_keyboard(config.grades),
    )
    return GRADE


async def grade(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    grade = update.callback_query.data.split(":", 1)[1]
    context.user_data["grade"] = grade

    config: Config = context.bot_data["config"]
    await update.callback_query.message.edit_text(
        "📚 رشته تحصیلی را انتخاب کنید:",
        reply_markup=build_majors_keyboard(["تجربی", "ریاضی", "انسانی"]),
    )
    return FIELD


async def field(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    field = update.callback_query.data.split(":", 1)[1]
    context.user_data["field"] = field

    data = context.user_data
    summary = (
        f"📋 خلاصه اطلاعات:\n\n"
        f"👤 {data.get('first_name')} {data.get('last_name')}\n"
        f"🏛️ {data.get('province')} - 🏙️ {data.get('city')}\n"
        f"🎓 {data.get('grade')} - 📚 {data.get('field')}\n\n"
        f"✅ برای تایید ثبت‌نام، دکمه زیر را بزنید."
    )
    from telegram import InlineKeyboardMarkup, InlineKeyboardButton

    kb = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("✅ تایید", callback_data="confirm_reg")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="cancel_reg")],
        ]
    )
    await update.callback_query.message.edit_text(summary, reply_markup=kb)
    return CONFIRM


async def confirm(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    storage: StudentStorage = context.bot_data["storage"]
    user_id = update.effective_user.id

    student = Student(
        user_id=user_id,
        first_name=context.user_data.get("first_name", ""),
        last_name=context.user_data.get("last_name", ""),
        province=context.user_data.get("province", ""),
        city=context.user_data.get("city", ""),
        grade=context.user_data.get("grade", ""),
        field=context.user_data.get("field", ""),
    )
    storage.upsert_student(student)

    from utils.keyboards import build_main_menu_keyboard

    await update.callback_query.message.edit_text(
        Messages.get_success_message(), reply_markup=build_main_menu_keyboard()
    )
    return ConversationHandler.END


async def cancel(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    await update.callback_query.message.edit_text("❌ ثبت‌نام لغو شد.")
    return ConversationHandler.END


def build_registration_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_registration, pattern=r"^start_registration$")
        ],
        states={
            FIRST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, first_name)],
            LAST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, last_name)],
            PROVINCE: [CallbackQueryHandler(province, pattern=r"^province:.*")],
            CITY: [CallbackQueryHandler(city, pattern=r"^city:.*")],
            GRADE: [CallbackQueryHandler(grade, pattern=r"^grade:.*")],
            FIELD: [CallbackQueryHandler(field, pattern=r"^major:.*")],
            CONFIRM: [CallbackQueryHandler(confirm, pattern=r"^confirm_reg$")],
        },
        fallbacks=[
            CallbackQueryHandler(cancel, pattern=r"^(cancel_reg|back_to_main)$")
        ],
        allow_reentry=True,
    )
