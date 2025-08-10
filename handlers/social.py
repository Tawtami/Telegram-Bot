#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Social media link handlers for Ostad Hatami Bot
"""

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from ui.keyboards import build_main_menu_keyboard
from utils.rate_limiter import rate_limit_handler

# Social media links
SOCIAL_LINKS = {
    "telegram": "@Ostad_Hatami",
    "phone": "+989381530556",
    "youtube": "https://youtube.com/@hamrahbaostad",
    "telegram_group": "https://t.me/hamrahbaostadgp",
}


@rate_limit_handler("default")
async def handle_social_media(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle social media menu"""
    query = update.callback_query
    if not query:
        return

    await query.answer()

    message_text = (
        "📡 همراه با استاد حاتمی\n\n"
        "🎓 مدرس ریاضی کنکور و مؤلف کتاب «انفجار خلاقیت»\n"
        "📍 با ۴۰ سال سابقه تدریس در مدارس برتر تهران\n\n"
        "🔗 شبکه‌های اجتماعی:\n"
        "📺 یوتیوب: youtube.com/@hamrahbaostad\n"
        "📣 گروه تلگرام: @hamrahbaostadgp\n"
        "💬 ارتباط مستقیم: @Ostad_Hatami"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "💬 ارتباط مستقیم",
                url=f"https://t.me/{SOCIAL_LINKS['telegram'].replace('@', '')}",
            )
        ],
        [InlineKeyboardButton("📱 تماس تلفنی", url=f"tel:{SOCIAL_LINKS['phone']}")],
        [InlineKeyboardButton("📺 یوتیوب", url=SOCIAL_LINKS["youtube"])],
        [InlineKeyboardButton("📣 گروه تلگرام", url=SOCIAL_LINKS["telegram_group"])],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_menu")],
    ]

    await query.edit_message_text(
        message_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


def build_social_handlers():
    """Build and return social handlers for registration in bot.py"""
    from telegram.ext import CallbackQueryHandler

    return [
        CallbackQueryHandler(handle_social_media, pattern=r"^social_media$"),
    ]
