#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CallbackQueryHandler, CallbackContext

from handlers.menu import ensure_registered


async def social_media(update: Update, context: CallbackContext):
    if not await ensure_registered(update, context):
        await update.callback_query.answer("لطفاً ابتدا ثبت‌نام کنید.", show_alert=True)
        return
    kb = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "📸 اینستاگرام", url="https://instagram.com/ostadhatami_official"
                )
            ],
            [InlineKeyboardButton("🎬 یوتیوب", url="https://youtube.com/@ostadhatami")],
            [
                InlineKeyboardButton(
                    "📢 کانال تلگرام", url="https://t.me/OstadHatamiChannel"
                )
            ],
            [
                InlineKeyboardButton(
                    "👥 گروه تلگرام", url="https://t.me/OstadHatamiGroup"
                )
            ],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")],
        ]
    )
    await update.callback_query.answer()
    await update.callback_query.message.edit_text("🌐 شبکه‌های اجتماعی", reply_markup=kb)


def register_social_handlers(app: Application):
    app.add_handler(CallbackQueryHandler(social_media, pattern=r"^social_media$"))
