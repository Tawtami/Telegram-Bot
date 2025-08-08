#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Social media link handlers for Ostad Hatami Bot
"""

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from ui.keyboards import build_main_menu_keyboard

# Social media links
SOCIAL_LINKS = {
    "telegram": "@ostad_hatami",
    "phone": "+989381530556",
    "instagram": "https://instagram.com/ostad_hatami",
    "youtube": "https://youtube.com/@ostad_hatami",
    "telegram_channel": "https://t.me/ostad_hatami_channel",
    "telegram_group": "https://t.me/ostad_hatami_group",
}


async def handle_social_media(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle social media menu"""
    query = update.callback_query
    if not query:
        return

    await query.answer()

    keyboard = [
        [
            InlineKeyboardButton(
                "💬 تلگرام مستقیم",
                url=f"https://t.me/{SOCIAL_LINKS['telegram'].replace('@', '')}",
            )
        ],
        [InlineKeyboardButton("📱 تماس تلفنی", url=f"tel:{SOCIAL_LINKS['phone']}")],
        [InlineKeyboardButton("📸 Instagram", url=SOCIAL_LINKS["instagram"])],
        [InlineKeyboardButton("🎥 YouTube", url=SOCIAL_LINKS["youtube"])],
        [InlineKeyboardButton("📢 کانال تلگرام", url=SOCIAL_LINKS["telegram_channel"])],
        [InlineKeyboardButton("👥 گروه تلگرام", url=SOCIAL_LINKS["telegram_group"])],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_menu")],
    ]

    await query.edit_message_text(
        "🌐 شبکه‌های اجتماعی و ارتباطی استاد حاتمی:\n\n"
        "📞 برای ارتباط مستقیم و ثبت‌نام در دوره‌ها:\n"
        f"💬 {SOCIAL_LINKS['telegram']}\n"
        f"📱 {SOCIAL_LINKS['phone']}\n\n"
        "برای دنبال کردن ما در شبکه‌های اجتماعی روی لینک‌های زیر کلیک کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
