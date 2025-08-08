#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Contact information handlers for Ostad Hatami Bot
"""

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from config import config
from ui.keyboards import build_main_menu_keyboard


async def handle_contact_us(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle contact us menu"""
    query = update.callback_query
    if not query:
        return

    await query.answer()

    message_text = (
        "☎️ ارتباط با ما:\n\n"
        "📞 برای ثبت‌نام در دوره‌ها، خرید کتاب و پشتیبانی:\n\n"
        "📱 شماره تماس:\n"
        "+989381530556\n\n"
        "💬 تلگرام مستقیم:\n"
        "@ostad_hatami\n\n"
        "📦 اطلاعیه مهم درباره ارسال کتاب انفجار خلاقیت ریاضی:\n"
        "ارسال کتاب فقط روزهای شنبه از طریق اداره پست انجام می‌شود.\n\n"
        "⏰ ساعات پاسخگویی:\n"
        "شنبه تا چهارشنبه: ۹ الی ۱۸\n"
        "پنجشنبه: ۹ الی ۱۳"
    )

    keyboard = [
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_menu")],
    ]

    await query.edit_message_text(
        message_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
