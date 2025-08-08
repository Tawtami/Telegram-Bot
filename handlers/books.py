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
from utils.storage import StudentStorage
from ui.keyboards import build_main_menu_keyboard


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


async def show_book_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show book information and start purchase process"""
    query = update.callback_query
    if not query:
        return ConversationHandler.END

    await query.answer()

    # Show book details with purchase button
    message_text = (
        f"📖 {BOOK_DETAILS['title']}\n"
        f"📚 {BOOK_DETAILS['subtitle']}\n\n"
        f"👤 نویسنده: {BOOK_DETAILS['author']}\n"
        f"📄 تعداد صفحات: {BOOK_DETAILS['pages']}\n"
        f"💰 قیمت: {BOOK_DETAILS['price']:,} تومان\n"
        f"📦 {BOOK_DETAILS['shipping_info']}\n\n"
        f"📝 توضیحات:\n{BOOK_DETAILS['description']}\n\n"
        f"📞 برای خرید و اطلاعات بیشتر:\n"
        f"📱 {BOOK_DETAILS['contact_info']['phone']}\n"
        f"💬 {BOOK_DETAILS['contact_info']['telegram']}\n\n"
        "برای خرید کتاب از طریق ربات روی دکمه زیر کلیک کنید:"
    )

    keyboard = [
        [InlineKeyboardButton("🛍 خرید کتاب", callback_data="start_book_purchase")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_menu")],
    ]

    await query.edit_message_text(
        message_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML,
    )
    return ConversationHandler.END


async def start_book_purchase(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
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


async def postal_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle postal code input"""
    postal_code = update.message.text.strip()

    # Validate postal code (10 digits)
    if not postal_code.isdigit() or len(postal_code) != 10:
        await update.message.reply_text(
            "❌ کد پستی باید ۱۰ رقم باشد.\n" "لطفاً دوباره وارد کنید:",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🔙 انصراف", callback_data="cancel_book_purchase"
                        )
                    ]
                ]
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


async def address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle address input"""
    address = update.message.text.strip()

    # Validate address length
    if len(address) < 10 or len(address) > 300:
        await update.message.reply_text(
            "❌ آدرس باید بین ۱۰ تا ۳۰۰ کاراکتر باشد.\n" "لطفاً دوباره وارد کنید:",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🔙 انصراف", callback_data="cancel_book_purchase"
                        )
                    ]
                ]
            ),
        )
        return BookPurchaseStates.ADDRESS

    context.user_data["book_purchase"]["address"] = address

    await update.message.reply_text(
        "📝 در صورت تمایل، توضیحات اضافه را وارد کنید:\n"
        "(برای رد کردن این مرحله روی /skip کلیک کنید)",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 انصراف", callback_data="cancel_book_purchase")]]
        ),
    )
    return BookPurchaseStates.NOTES


async def skip_notes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Skip notes and show payment info"""
    context.user_data["book_purchase"]["notes"] = ""
    return await show_payment_info(update, context)


async def notes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle additional notes"""
    notes = update.message.text.strip()
    context.user_data["book_purchase"]["notes"] = notes
    return await show_payment_info(update, context)


async def show_payment_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show payment information"""
    book_data = context.user_data["book_purchase"]

    message_text = (
        "💳 اطلاعات پرداخت:\n\n"
        f"📖 کتاب: {book_data['title']}\n"
        f"💰 مبلغ: {book_data['price']:,} تومان\n\n"
        "1️⃣ مبلغ را به شماره کارت زیر واریز کنید:\n"
        "6037-9974-1234-5678\n"
        "به نام: استاد حاتمی\n\n"
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
                                "🔙 انصراف", callback_data="cancel_book_purchase"
                            )
                        ]
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
                                "🔙 انصراف", callback_data="cancel_book_purchase"
                            )
                        ]
                    ]
                ),
            )

    return BookPurchaseStates.PAYMENT


async def handle_payment_receipt(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle payment receipt photo"""
    if "book_purchase" not in context.user_data:
        await update.message.reply_text(
            "❌ خطا در فرآیند خرید. لطفاً دوباره تلاش کنید.",
            reply_markup=build_main_menu_keyboard(),
        )
        return ConversationHandler.END

    book_data = context.user_data["book_purchase"]
    storage: StudentStorage = context.bot_data["storage"]

    # Save book purchase data
    if not storage.save_book_purchase(update.effective_user.id, book_data):
        await update.message.reply_text(
            "❌ خطا در ثبت سفارش. لطفاً دوباره تلاش کنید.",
            reply_markup=build_main_menu_keyboard(),
        )
        return ConversationHandler.END

    # Forward receipt to admin #1 (first admin in list)
    admin_id = config.bot.admin_user_ids[0]
    student = storage.get_student(update.effective_user.id)
    caption = (
        f"🧾 رسید پرداخت کتاب\n\n"
        f"کتاب: {book_data['title']}\n"
        f"کاربر: {student['first_name']} {student['last_name']}\n"
        f"شناسه کاربری: {update.effective_user.id}\n\n"
        f"📍 آدرس:\n{book_data['address']}\n"
        f"📮 کد پستی: {book_data['postal_code']}\n"
        f"📝 توضیحات: {book_data['notes']}\n\n"
        f"برای تایید پرداخت از دستور زیر استفاده کنید:\n"
        f"/confirm_payment {update.effective_user.id}"
    )

    try:
        await context.bot.forward_message(
            chat_id=admin_id,
            from_chat_id=update.effective_chat.id,
            message_id=update.message.message_id,
        )
        await context.bot.send_message(
            chat_id=admin_id,
            text=caption,
        )
    except Exception as e:
        logger.error(f"Error forwarding receipt to admin: {e}")

    # Clear book purchase data
    del context.user_data["book_purchase"]

    await update.message.reply_text(
        "✅ سفارش کتاب شما با موفقیت ثبت شد.\n\n"
        "پس از تایید پرداخت توسط ادمین، اطلاعات ارسال کتاب به شما اعلام خواهد شد.",
        reply_markup=build_main_menu_keyboard(),
    )
    return ConversationHandler.END


async def cancel_book_purchase(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
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
                CommandHandler("skip", skip_notes),
            ],
            BookPurchaseStates.PAYMENT: [
                MessageHandler(filters.PHOTO, handle_payment_receipt),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(
                cancel_book_purchase, pattern="^cancel_book_purchase$"
            ),
            CommandHandler("cancel", cancel_book_purchase),
        ],
        name="book_purchase",
        persistent=False,
    )
