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
    
    contact_info = config.contact_info
    message_text = (
        "☎️ اطلاعات تماس:\n\n"
        f"📱 تلفن: {contact_info['phone']}\n"
        f"📧 ایمیل: {contact_info['email']}\n"
        f"🌐 وبسایت: {contact_info['website']}\n"
        f"📱 تلگرام: {contact_info['telegram']}\n\n"
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