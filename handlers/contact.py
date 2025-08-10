#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Contact information handlers for Ostad Hatami Bot
"""

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from config import config
from ui.keyboards import build_main_menu_keyboard
from utils.rate_limiter import rate_limit_handler


@rate_limit_handler("default")
async def handle_contact_us(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle contact us menu"""
    query = update.callback_query
    if not query:
        return

    await query.answer()

    message_text = (
        "☎️ ارتباط با ما:\n\n"
        "📞 برای خرید کتاب و ثبت‌نام در دوره‌ها لطفاً از طریق ربات اقدام کنید.\n\n"
        "در صورت بروز مشکل:\n"
        "📱 با استاد حاتمی در ارتباط باشید:\n"
        "💬 @ostad_hatami\n"
        "📞 +989381530556\n\n"
        "📦 ارسال کتاب فقط روزهای شنبه از طریق اداره پست انجام می‌شود."
    )

    keyboard = [
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_menu")],
    ]

    await query.edit_message_text(
        message_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


def build_contact_handlers():
    """Build and return contact handlers for registration in bot.py"""
    from telegram.ext import CallbackQueryHandler

    return [
        CallbackQueryHandler(handle_contact_us, pattern=r"^contact_us$"),
    ]
