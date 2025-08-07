#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CallbackQueryHandler, CallbackContext

from handlers.menu import ensure_registered
from utils.storage import StudentStorage

FREE_COURSE_ID = "free_friday"
PAID_COURSES = {
    "intensive_math": {
        "title": "دوره فشرده ریاضی کنکور",
        "price": 2500000,
        "desc": "۳ ماهه – ۲۴ جلسه",
    },
    "advanced_test": {
        "title": "دوره تست‌زنی پیشرفته",
        "price": 1800000,
        "desc": "۲ ماهه – ۱۶ جلسه",
    },
}


async def free_courses(update: Update, context: CallbackContext):
    if not await ensure_registered(update, context):
        await update.callback_query.answer("لطفاً ابتدا ثبت‌نام کنید.", show_alert=True)
        return
    text = (
        "🎓 دوره‌های رایگان\n\n"
        "📅 جمعه‌ها – کلاس آنلاین\n"
        "برای ثبت‌نام دکمه زیر را بزنید"
    )
    kb = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("✅ ثبت‌نام در دوره رایگان", callback_data=f"enroll_free:{FREE_COURSE_ID}")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")],
        ]
    )
    await update.callback_query.answer()
    await update.callback_query.message.edit_text(text, reply_markup=kb)


async def enroll_free(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    storage: StudentStorage = context.bot_data["storage"]
    user_id = update.effective_user.id
    storage.add_free_course(user_id, FREE_COURSE_ID)
    await update.callback_query.message.edit_text(
        "✅ ثبت‌نام شما در دوره رایگان انجام شد.",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]]
        ),
    )


async def paid_courses(update: Update, context: CallbackContext):
    if not await ensure_registered(update, context):
        await update.callback_query.answer("لطفاً ابتدا ثبت‌نام کنید.", show_alert=True)
        return

    rows = []
    text = "💼 دوره‌های پولی\n\nبرای مشاهده جزئیات، دوره را انتخاب کنید"
    for cid, c in PAID_COURSES.items():
        rows.append([InlineKeyboardButton(f"{c['title']} – {c['price']:,} تومان", callback_data=f"paid:{cid}")])
    rows.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")])
    await update.callback_query.answer()
    await update.callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(rows))


async def paid_detail(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    cid = update.callback_query.data.split(":", 1)[1]
    c = PAID_COURSES.get(cid)
    if not c:
        await update.callback_query.message.reply_text("❌ دوره یافت نشد")
        return
    text = (
        f"💼 {c['title']}\n{c['desc']}\nقیمت: {c['price']:,} تومان\n\n"
        "برای خرید، فیش پرداخت را ارسال کنید."
    )
    kb = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📤 ارسال فیش", callback_data=f"send_receipt_course:{cid}")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="paid_courses")],
        ]
    )
    await update.callback_query.message.edit_text(text, reply_markup=kb)


async def purchased_courses(update: Update, context: CallbackContext):
    if not await ensure_registered(update, context):
        await update.callback_query.answer("لطفاً ابتدا ثبت‌نام کنید.", show_alert=True)
        return
    storage: StudentStorage = context.bot_data["storage"]
    user_id = update.effective_user.id
    student = storage.get_student(user_id)
    courses = student.purchased_courses if student else []
    if not courses:
        await update.callback_query.answer()
        await update.callback_query.message.edit_text(
            "😔 هنوز دوره‌ای خریداری نکرده‌اید.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]]
            ),
        )
        return
    text = "🛒 دوره‌های خریداری‌شده:\n\n" + "\n".join([f"✅ {cid}" for cid in courses])
    await update.callback_query.answer()
    await update.callback_query.message.edit_text(
        text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]])
    )


def register_course_handlers(app: Application):
    app.add_handler(CallbackQueryHandler(free_courses, pattern=r"^free_courses$"))
    app.add_handler(CallbackQueryHandler(enroll_free, pattern=r"^enroll_free:.*"))
    app.add_handler(CallbackQueryHandler(paid_courses, pattern=r"^paid_courses$"))
    app.add_handler(CallbackQueryHandler(paid_detail, pattern=r"^paid:.*"))
    app.add_handler(CallbackQueryHandler(purchased_courses, pattern=r"^purchased_courses$"))
