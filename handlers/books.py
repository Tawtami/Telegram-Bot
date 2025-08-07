#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CallbackQueryHandler, MessageHandler, CallbackContext, ConversationHandler, CommandHandler, filters

from handlers.menu import ensure_registered
from utils.storage import StudentStorage

ASK_ADDRESS, ASK_POSTAL, ASK_NOTES, WAIT_RECEIPT = range(4)

BOOK_INFO = {
    "title": "کتاب انفجار خلاقیت",
    "price": 280000,
}


async def book_info(update: Update, context: CallbackContext):
    if not await ensure_registered(update, context):
        await update.callback_query.answer("لطفاً ابتدا ثبت‌نام کنید.", show_alert=True)
        return
    text = f"📖 {BOOK_INFO['title']}\nقیمت: {BOOK_INFO['price']:,} تومان"
    kb = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🛒 خرید کتاب", callback_data="buy_book")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")],
        ]
    )
    await update.callback_query.answer()
    await update.callback_query.message.edit_text(text, reply_markup=kb)


async def buy_book(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    await update.callback_query.message.edit_text("📍 آدرس کامل پستی را وارد کنید:")
    return ASK_ADDRESS


async def ask_address(update: Update, context: CallbackContext):
    address = (update.message.text or "").strip()
    if len(address) < 10:
        await update.message.reply_text("❌ آدرس باید حداقل ۱۰ کاراکتر باشد.")
        return ASK_ADDRESS
    context.user_data["address"] = address
    await update.message.reply_text("📮 کد پستی ۱۰ رقمی را وارد کنید:")
    return ASK_POSTAL


async def ask_postal(update: Update, context: CallbackContext):
    postal = (update.message.text or "").strip()
    if not (postal.isdigit() and len(postal) == 10):
        await update.message.reply_text("❌ کد پستی باید ۱۰ رقم باشد.")
        return ASK_POSTAL
    context.user_data["postal_code"] = postal
    await update.message.reply_text("📝 توضیحات اختیاری را وارد کنید (یا /skip را بزنید):")
    return ASK_NOTES


async def skip_notes(update: Update, context: CallbackContext):
    context.user_data["notes"] = ""
    return await _request_receipt(update, context)


async def notes(update: Update, context: CallbackContext):
    context.user_data["notes"] = (update.message.text or "").strip()
    return await _request_receipt(update, context)


async def _request_receipt(update: Update, context: CallbackContext):
    await update.message.reply_text(
        f"💳 مبلغ {BOOK_INFO['price']:,} تومان را واریز کنید و فیش را ارسال نمایید."
    )
    return WAIT_RECEIPT


async def receipt_photo(update: Update, context: CallbackContext):
    if not update.message.photo:
        await update.message.reply_text("❌ لطفاً عکس فیش را ارسال کنید.")
        return WAIT_RECEIPT

    storage: StudentStorage = context.bot_data["storage"]
    user_id = update.effective_user.id
    purchase = {
        "title": BOOK_INFO["title"],
        "address": context.user_data.get("address", ""),
        "postal_code": context.user_data.get("postal_code", ""),
        "notes": context.user_data.get("notes", ""),
        "receipt_file_id": update.message.photo[-1].file_id,
    }
    storage.add_book_purchase(user_id, purchase)

    # Notify admin #1
    admins = context.bot_data["config"].bot.admin_user_ids
    if admins:
        await context.bot.send_photo(chat_id=admins[0], photo=update.message.photo[-1].file_id, caption=f"خرید کتاب جدید از کاربر {user_id}")

    await update.message.reply_text("✅ خرید شما ثبت شد. منتظر تایید بمانید.")
    return ConversationHandler.END


def register_book_handlers(app: Application):
    app.add_handler(CallbackQueryHandler(book_info, pattern=r"^book_info$"))
    app.add_handler(
        ConversationHandler(
            entry_points=[CallbackQueryHandler(buy_book, pattern=r"^buy_book$")],
            states={
                ASK_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_address)],
                ASK_POSTAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_postal)],
                ASK_NOTES: [
                    CommandHandler("skip", skip_notes),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, notes),
                ],
                WAIT_RECEIPT: [MessageHandler(filters.PHOTO, receipt_photo)],
            },
            fallbacks=[],
            allow_reentry=True,
        )
    )
