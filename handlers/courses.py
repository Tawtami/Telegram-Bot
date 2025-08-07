#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CallbackContext,
    ConversationHandler,
    MessageHandler,
    filters,
)

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

WAIT_RECEIPT = range(1)


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
            [
                InlineKeyboardButton(
                    "✅ ثبت‌نام در دوره رایگان",
                    callback_data=f"enroll_free:{FREE_COURSE_ID}",
                )
            ],
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
        rows.append(
            [
                InlineKeyboardButton(
                    f"{c['title']} – {c['price']:,} تومان", callback_data=f"paid:{cid}"
                )
            ]
        )
    rows.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")])
    await update.callback_query.answer()
    await update.callback_query.message.edit_text(
        text, reply_markup=InlineKeyboardMarkup(rows)
    )


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
            [
                InlineKeyboardButton(
                    "📤 ارسال فیش", callback_data=f"send_receipt_course:{cid}"
                )
            ],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="paid_courses")],
        ]
    )
    await update.callback_query.message.edit_text(text, reply_markup=kb)


async def send_receipt_course(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    cid = update.callback_query.data.split(":", 1)[1]
    context.user_data["pending_course_id"] = cid
    await update.callback_query.message.edit_text(
        "📸 لطفاً عکس فیش پرداخت دوره را ارسال کنید"
    )
    return WAIT_RECEIPT


async def receive_course_receipt(update: Update, context: CallbackContext):
    if not update.message.photo:
        await update.message.reply_text("❌ لطفاً عکس فیش را ارسال کنید.")
        return WAIT_RECEIPT
    user_id = update.effective_user.id
    cid = context.user_data.get("pending_course_id")
    photo_id = update.message.photo[-1].file_id

    # Forward to all admins with approve/reject buttons
    admins = context.bot_data["config"].bot.admin_user_ids
    if admins:
        kb = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "✅ تایید", callback_data=f"approve_course:{user_id}:{cid}"
                    ),
                    InlineKeyboardButton(
                        "❌ رد", callback_data=f"reject_course:{user_id}:{cid}"
                    ),
                ]
            ]
        )
        for admin_id in admins:
            await context.bot.send_photo(
                chat_id=admin_id,
                photo=photo_id,
                caption=f"فیش پرداخت دوره برای کاربر {user_id} ({cid})",
                reply_markup=kb,
            )

    await update.message.reply_text("✅ فیش دریافت شد. منتظر تایید ادمین بمانید.")
    return ConversationHandler.END


async def approve_course(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    _, user_id_str, cid = update.callback_query.data.split(":", 2)
    user_id = int(user_id_str)
    storage: StudentStorage = context.bot_data["storage"]
    storage.add_purchased_course(user_id, cid)

    # Notify user
    try:
        c = PAID_COURSES.get(cid)
        title = c["title"] if c else cid
        await context.bot.send_message(
            chat_id=user_id,
            text=f"✅ خرید دوره '{title}' تایید شد.",
        )
    except Exception:
        pass

    await update.callback_query.message.edit_text(
        "✅ تایید شد و به لیست خرید اضافه گردید."
    )


async def reject_course(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    await update.callback_query.message.edit_text("❌ پرداخت رد شد.")


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
        text,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]]
        ),
    )


def register_course_handlers(app: Application):
    app.add_handler(CallbackQueryHandler(free_courses, pattern=r"^free_courses$"))
    app.add_handler(CallbackQueryHandler(enroll_free, pattern=r"^enroll_free:.*"))
    app.add_handler(CallbackQueryHandler(paid_courses, pattern=r"^paid_courses$"))
    app.add_handler(CallbackQueryHandler(paid_detail, pattern=r"^paid:.*"))
    app.add_handler(
        ConversationHandler(
            entry_points=[
                CallbackQueryHandler(
                    send_receipt_course, pattern=r"^send_receipt_course:.*"
                )
            ],
            states={
                WAIT_RECEIPT: [MessageHandler(filters.PHOTO, receive_course_receipt)],
            },
            fallbacks=[],
            allow_reentry=True,
        )
    )
    app.add_handler(
        CallbackQueryHandler(purchased_courses, pattern=r"^purchased_courses$")
    )
    app.add_handler(CallbackQueryHandler(approve_course, pattern=r"^approve_course:.*"))
    app.add_handler(CallbackQueryHandler(reject_course, pattern=r"^reject_course:.*"))
