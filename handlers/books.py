#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Book purchase handlers for Ostad Hatami Bot
"""

from enum import Enum
import logging
from typing import Any, Dict

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton

logger = logging.getLogger(__name__)

from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    CommandHandler,
    filters,
)
from telegram.constants import ParseMode

from config import config
from utils.rate_limiter import rate_limit_handler
from ui.keyboards import build_main_menu_keyboard
from handlers.payments import handle_payment_receipt as unified_payment_receipt
from utils.validators import Validator


# States for the book purchase conversation
class BookPurchaseStates(Enum):
    POSTAL_CODE = 1
    ADDRESS = 2
    NOTES = 3
    PAYMENT = 4


# Book details (in production, load from database)
BOOK_DETAILS = {
    "title": "انفجار خلاقیت ریاضی",
    "subtitle": "چگونه تست‌های ریاضی کنکور را حل کنم؟",
    "author": "استاد حاتمی",
    "description": (
        "📘 این کتاب، ویژه‌ی هر سه پایه ۱۰، ۱۱ و ۱۲ در رشته‌های تجربی و ریاضی است و به‌صورت کاملاً هدفمند، مباحث مهم و پرتکرار کنکور را به شیوه‌ای خلاقانه و مفهومی آموزش می‌دهد.\n\n"
        "🔹 فصل اول: دیدگاه «حل معادله»\n"
        "با تمرکز بر تجزیه چندجمله‌ای‌ها، یافتن ریشه‌ها، و تحلیل نامعادلات از طریق تعیین علامت. پایه‌ی اصلی بسیاری از تست‌های کنکور سال‌های اخیر.\n\n"
        "🔹 فصل دوم: دیدگاه «اتحادی مسئله»\n"
        "آموزش تمام اتحادهای جبری و مثلثاتی به‌همراه درک عمیق ساختار اتحادی در مسائل، فراتر از حفظ فرمول‌ها.\n\n"
        "🔹 فصل سوم: دیدگاه «این‌همانی»\n"
        'برای اولین‌بار در سطح کتب کمک‌درسی، مفهوم "این‌همانی" در حل معادلات مطرح شده که عیناً در کنکور ۱۴۰۴ نیز مشاهده شد.\n\n'
        "🔹 فصل چهارم: تحلیل نمودارهای ریاضی\n"
        "جامع‌ترین فصل برای آموزش و درک نمودارها، با کاربرد مستقیم در کنکورهای اخیر.\n\n"
        "✨ انفجار خلاقیت ریاضی نه فقط یک کتاب تست، بلکه یک مرجع مفهومی برای یادگیری، درک و تسلط واقعی بر ریاضیات است. با مطالعه‌ی هر صفحه، علاقه‌تان به ریاضی بیشتر و توان حل مسئله‌تان قوی‌تر خواهد شد."
    ),
    "price": 150000,  # تومان
    "pages": 250,
    "target_grades": ["دهم", "یازدهم", "دوازدهم"],
    "target_majors": ["ریاضی", "تجربی"],
    "shipping_info": "ارسال فقط روزهای شنبه از طریق اداره پست",
    "contact_info": {"phone": "+989381530556", "telegram": "@ostad_hatami"},
}


@rate_limit_handler("default")
async def handle_book_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /book command - Show book information"""
    # Show book details
    message_text = (
        f"📘 کتاب «{BOOK_DETAILS['title']}»\n"
        f"{BOOK_DETAILS['subtitle']}\n\n"
        f"✍ تألیف: {BOOK_DETAILS['author']}\n"
        f"📚 ویژه پایه‌های ۱۰، ۱۱ و ۱۲ رشته ریاضی و تجربی\n"
        f"📄 {BOOK_DETAILS['pages']} صفحه | 💰 قیمت: {BOOK_DETAILS['price']:,} تومان\n"
        f"📦 ارسال فقط روزهای شنبه با پست\n\n"
        f"🔍 فصل‌های اصلی:\n"
        f"1️⃣ حل خلاقانه معادلات و نامعادلات\n"
        f"2️⃣ اتحادهای مفهومی و کاربردی\n"
        f"3️⃣ تکنیک این‌همانی در تست‌ها (مطابق کنکور ۱۴۰۴)\n"
        f"4️⃣ تحلیل نمودارها با کاربرد کنکوری\n\n"
        f"✨ این کتاب فقط یک مجموعه تست نیست؛ مرجعی مفهومی برای یادگیری عمیق ریاضی است.\n\n"
        f"🛒 برای خرید، از منوی اصلی گزینه «کتاب انفجار خلاقیت» را انتخاب کنید."
    )

    keyboard = [
        [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")],
    ]

    await update.message.reply_text(
        message_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )


@rate_limit_handler("default")
async def show_book_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show book information and start purchase process"""
    query = update.callback_query
    if not query:
        return ConversationHandler.END

    await query.answer()

    # Show book details with purchase button
    message_text = (
        f"📘 کتاب «{BOOK_DETAILS['title']}»\n"
        f"{BOOK_DETAILS['subtitle']}\n\n"
        f"✍ تألیف: {BOOK_DETAILS['author']}\n"
        f"📚 ویژه پایه‌های ۱۰، ۱۱ و ۱۲ رشته ریاضی و تجربی\n"
        f"📄 {BOOK_DETAILS['pages']} صفحه | 💰 قیمت: {BOOK_DETAILS['price']:,} تومان\n"
        f"📦 ارسال فقط روزهای شنبه با پست\n\n"
        f"🔍 فصل‌های اصلی:\n"
        f"1️⃣ حل خلاقانه معادلات و نامعادلات\n"
        f"2️⃣ اتحادهای مفهومی و کاربردی\n"
        f"3️⃣ تکنیک این‌همانی در تست‌ها (مطابق کنکور ۱۴۰۴)\n"
        f"4️⃣ تحلیل نمودارها با کاربرد کنکوری\n\n"
        f"✨ این کتاب فقط یک مجموعه تست نیست؛ مرجعی مفهومی برای یادگیری عمیق ریاضی است.\n\n"
        f"🛒 برای خرید، از طریق ربات اقدام کنید."
    )

    keyboard = [
        [InlineKeyboardButton("🛍 خرید کتاب", callback_data="start_book_purchase")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_menu")],
    ]

    await query.edit_message_text(
        message_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )
    return ConversationHandler.END


@rate_limit_handler("default")
async def start_book_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start book purchase process"""
    query = update.callback_query
    if not query:
        return ConversationHandler.END

    await query.answer()

    # Store book details in context
    context.user_data["book_purchase"] = {
        "title": BOOK_DETAILS["title"],
        "price": BOOK_DETAILS["price"],
    }

    await query.edit_message_text(
        "📮 لطفاً کد پستی ۱۰ رقمی خود را وارد کنید:",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 انصراف", callback_data="cancel_book_purchase")]]
        ),
    )
    return BookPurchaseStates.POSTAL_CODE


@rate_limit_handler("default")
async def postal_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle postal code input"""
    postal_code_raw = update.message.text.strip()
    # Normalize Persian/Arabic digits to English
    postal_code = Validator.convert_to_english_digits(postal_code_raw)
    # Keep digits only
    postal_code = "".join(ch for ch in postal_code if ch.isdigit())

    # Validate postal code (10 digits)
    if not postal_code.isdigit() or len(postal_code) != 10:
        await update.message.reply_text(
            "❌ کد پستی باید ۱۰ رقم باشد.\n" "لطفاً دوباره وارد کنید:",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 انصراف", callback_data="cancel_book_purchase")]]
            ),
        )
        return BookPurchaseStates.POSTAL_CODE

    context.user_data["book_purchase"]["postal_code"] = postal_code

    await update.message.reply_text(
        "📍 لطفاً آدرس کامل پستی خود را وارد کنید:",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 انصراف", callback_data="cancel_book_purchase")]]
        ),
    )
    return BookPurchaseStates.ADDRESS


@rate_limit_handler("default")
async def address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle address input"""
    address = update.message.text.strip()

    # Validate address length
    if len(address) < 10 or len(address) > 300:
        await update.message.reply_text(
            "❌ آدرس باید بین ۱۰ تا ۳۰۰ کاراکتر باشد.\n" "لطفاً دوباره وارد کنید:",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 انصراف", callback_data="cancel_book_purchase")]]
            ),
        )
        return BookPurchaseStates.ADDRESS

    context.user_data["book_purchase"]["address"] = address

    await update.message.reply_text(
        "📝 در صورت تمایل، توضیحات اضافه را وارد کنید:",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("رد کردن", callback_data="book_skip_notes")],
                [InlineKeyboardButton("🔙 انصراف", callback_data="cancel_book_purchase")],
            ]
        ),
    )
    return BookPurchaseStates.NOTES


@rate_limit_handler("default")
async def skip_notes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Skip notes and show payment info"""
    context.user_data["book_purchase"]["notes"] = ""
    return await show_payment_info(update, context)


@rate_limit_handler("default")
async def notes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle additional notes"""
    notes = update.message.text.strip()
    context.user_data["book_purchase"]["notes"] = notes
    return await show_payment_info(update, context)


@rate_limit_handler("default")
async def show_payment_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show payment information"""
    book_data = context.user_data["book_purchase"]

    from utils.validators import Validator

    card_fmt = Validator.format_card_number(config.bot.payment_card_number)
    message_text = (
        "💳 اطلاعات پرداخت:\n\n"
        f"📖 کتاب: {book_data['title']}\n"
        f"💰 مبلغ: {book_data['price']:,} تومان\n\n"
        "1️⃣ مبلغ را به شماره کارت زیر واریز کنید:\n"
        f"{card_fmt}\n"
        f"به نام: {config.bot.payment_payee_name}\n\n"
        "2️⃣ تصویر رسید پرداخت را ارسال کنید.\n\n"
        "❗️ پس از تایید پرداخت توسط ادمین، اطلاعات ارسال کتاب به شما اعلام خواهد شد."
    )

    if isinstance(update, Update):
        if update.message:
            await update.message.reply_text(
                message_text,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "📤 ارسال رسید", callback_data="hint_upload_receipt"
                            )
                        ],
                        [InlineKeyboardButton("🔙 انصراف", callback_data="cancel_book_purchase")],
                    ]
                ),
            )
        elif update.callback_query:
            await update.callback_query.edit_message_text(
                message_text,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "📤 ارسال رسید", callback_data="hint_upload_receipt"
                            )
                        ],
                        [InlineKeyboardButton("🔙 انصراف", callback_data="cancel_book_purchase")],
                    ]
                ),
            )

    return BookPurchaseStates.PAYMENT


@rate_limit_handler("default")
async def handle_payment_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Delegate to unified payment receipt handler"""
    await unified_payment_receipt(update, context)
    return ConversationHandler.END


async def cancel_book_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel book purchase process"""
    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text(
            "❌ فرآیند خرید کتاب لغو شد.",
            reply_markup=build_main_menu_keyboard(),
        )

    if "book_purchase" in context.user_data:
        del context.user_data["book_purchase"]

    return ConversationHandler.END


def build_book_purchase_conversation() -> ConversationHandler:
    """Build the book purchase conversation handler"""
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(show_book_info, pattern="^book_info$"),
            CallbackQueryHandler(start_book_purchase, pattern="^start_book_purchase$"),
        ],
        states={
            BookPurchaseStates.POSTAL_CODE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, postal_code),
            ],
            BookPurchaseStates.ADDRESS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, address),
            ],
            BookPurchaseStates.NOTES: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, notes),
                CallbackQueryHandler(skip_notes, pattern="^book_skip_notes$"),
            ],
            BookPurchaseStates.PAYMENT: [
                MessageHandler(filters.PHOTO, handle_payment_receipt),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(cancel_book_purchase, pattern="^cancel_book_purchase$"),
            CommandHandler("cancel", cancel_book_purchase),
        ],
        name="book_purchase",
        persistent=False,
        per_chat=True,
    )


def build_book_handlers():
    """Build and return book handlers for registration in bot.py"""
    from telegram.ext import CommandHandler

    return [
        CommandHandler("book", handle_book_info),
        build_book_purchase_conversation(),
    ]
