#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CallbackQueryHandler, CallbackContext

from handlers.menu import ensure_registered


async def contact_us(update: Update, context: CallbackContext):
    if not await ensure_registered(update, context):
        await update.callback_query.answer("لطفاً ابتدا ثبت‌نام کنید.", show_alert=True)
        return
    text = (
        "📞 ارتباط با ما\n\n"
        "تلگرام: @Ostad_Hatami\nایمیل: info@ostadhatami.ir\nوب‌سایت: ostadhatami.ir"
    )
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]])
    await update.callback_query.answer()
    await update.callback_query.message.edit_text(text, reply_markup=kb)


def register_contact_handlers(app: Application):
    app.add_handler(CallbackQueryHandler(contact_us, pattern=r"^contact_us$"))
