#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unified payment receipt handler for both courses and book purchases
"""

from telegram import Update
from telegram.ext import ContextTypes

from config import config
from utils.storage import StudentStorage
from utils.rate_limiter import rate_limit_handler
from ui.keyboards import build_main_menu_keyboard


@rate_limit_handler("default")
async def handle_payment_receipt(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle incoming payment receipt photo for courses or books.

    - If context.user_data["pending_course"] is set: treat as course payment → add pending, forward to admin
    - Else if context.user_data["book_purchase"] is set: save book purchase, forward to admin
    - Else: inform user there is no pending payment

    Enforces basic file size validation using config.security.max_file_size_mb.
    """
    if not update.message or not update.message.photo:
        return

    # Enforce file size limit
    largest_photo = update.message.photo[-1]
    file_size_mb = (largest_photo.file_size or 0) / (1024 * 1024)
    if file_size_mb > config.security.max_file_size_mb:
        await update.message.reply_text(
            f"❌ حجم فایل بیش از حد مجاز است. حداکثر اندازه: {config.security.max_file_size_mb} مگابایت.",
            reply_markup=build_main_menu_keyboard(),
        )
        return

    storage: StudentStorage = context.bot_data["storage"]
    student = storage.get_student(update.effective_user.id)

    if not student:
        await update.message.reply_text(
            "❌ شما ثبت‌نام نکرده‌اید. لطفاً ابتدا ثبت‌نام کنید.",
            reply_markup=build_main_menu_keyboard(),
        )
        return

    caption = None
    success_message = None

    # Course payment
    if context.user_data.get("pending_course"):
        course_id = context.user_data["pending_course"]

        if not storage.add_pending_payment(update.effective_user.id, course_id):
            await update.message.reply_text(
                "❌ خطا در ثبت پرداخت. لطفاً دوباره تلاش کنید.",
                reply_markup=build_main_menu_keyboard(),
            )
            return

        # Load course title from JSON
        import json

        try:
            with open("data/courses.json", "r", encoding="utf-8") as f:
                all_courses = json.load(f)
            course = next(
                (c for c in all_courses if c.get("course_id") == course_id), None
            )
            course_title = course.get("title") if course else course_id
        except Exception:
            course_title = course_id

        caption = (
            f"🧾 رسید پرداخت دوره\n\n"
            f"📚 دوره: {course_title}\n"
            f"👤 کاربر: {student['first_name']} {student['last_name']}\n"
            f"📱 شماره: {student.get('phone_number', 'ثبت نشده')}\n"
            f"🆔 شناسه کاربری: {update.effective_user.id}\n"
            f"🏙 شهر: {student['city']}\n\n"
            f"برای تایید پرداخت از دستور زیر استفاده کنید:\n"
            f"/confirm_payment {update.effective_user.id}"
        )

        # Clear pending course
        del context.user_data["pending_course"]

        success_message = (
            "✅ رسید پرداخت دوره شما دریافت شد.\n\n"
            "پس از تایید توسط ادمین، دوره به لیست دوره‌های خریداری‌شده شما اضافه خواهد شد."
        )

    # Book payment
    elif context.user_data.get("book_purchase"):
        book_data = context.user_data["book_purchase"]

        if not storage.save_book_purchase(update.effective_user.id, book_data):
            await update.message.reply_text(
                "❌ خطا در ثبت سفارش کتاب. لطفاً دوباره تلاش کنید.",
                reply_markup=build_main_menu_keyboard(),
            )
            return

        caption = (
            f"🧾 رسید پرداخت کتاب\n\n"
            f"📖 کتاب: {book_data.get('title', 'انفجار خلاقیت ریاضی')}\n"
            f"👤 کاربر: {student['first_name']} {student['last_name']}\n"
            f"📱 شماره: {student.get('phone_number', 'ثبت نشده')}\n"
            f"🆔 شناسه کاربری: {update.effective_user.id}\n"
            f"📍 آدرس: {book_data.get('address', 'ثبت نشده')}\n"
            f"📮 کد پستی: {book_data.get('postal_code', 'ثبت نشده')}\n"
            f"📝 توضیحات: {book_data.get('notes', 'ندارد')}\n\n"
            f"برای تایید پرداخت از دستور زیر استفاده کنید:\n"
            f"/confirm_payment {update.effective_user.id}"
        )

        # Clear book purchase data
        del context.user_data["book_purchase"]

        success_message = (
            "✅ رسید پرداخت کتاب شما دریافت شد.\n\n"
            "پس از تایید توسط ادمین، کتاب در روز شنبه ارسال خواهد شد."
        )

    else:
        await update.message.reply_text(
            "❌ هیچ پرداختی در انتظار نیست.",
            reply_markup=build_main_menu_keyboard(),
        )
        return

    # Forward receipt to primary admin
    primary_admin_id = (
        config.bot.admin_user_ids[0] if config.bot.admin_user_ids else None
    )
    if primary_admin_id:
        try:
            await context.bot.forward_message(
                chat_id=primary_admin_id,
                from_chat_id=update.effective_chat.id,
                message_id=update.message.message_id,
            )
            await context.bot.send_message(chat_id=primary_admin_id, text=caption)
        except Exception:
            pass

    await update.message.reply_text(
        success_message, reply_markup=build_main_menu_keyboard()
    )
