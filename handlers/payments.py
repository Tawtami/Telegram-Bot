#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unified payment receipt handler for both courses and book purchases
"""

from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler

from config import config
from utils.storage import StudentStorage
from utils.rate_limiter import rate_limit_handler
from ui.keyboards import build_main_menu_keyboard
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
import hashlib
import time


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

    # Helper to build admin inline keyboard for approval/rejection (token based)
    def admin_approval_keyboard(token: str) -> InlineKeyboardMarkup:
        data_prefix = f"pay:{token}"
        return InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "✅ تأیید پرداخت", callback_data=f"{data_prefix}:approve"
                    ),
                    InlineKeyboardButton(
                        "❌ رد پرداخت", callback_data=f"{data_prefix}:reject"
                    ),
                ]
            ]
        )

    payment_meta = {}

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
            f"برای تایید/رد پرداخت از دکمه‌های زیر استفاده کنید."
        )

        payment_meta = {
            "item_type": "course",
            "item_id": course_id,
            "item_title": course_title,
        }

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
            f"برای تایید/رد پرداخت از دکمه‌های زیر استفاده کنید."
        )

        payment_meta = {
            "item_type": "book",
            "item_id": book_data.get("title", "book"),
            "item_title": book_data.get("title", "book"),
        }

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

    # Generate token to correlate notifications across admins
    token_source = f"{update.effective_user.id}:{payment_meta.get('item_type')}:{payment_meta.get('item_id')}:{time.time()}"
    token = hashlib.sha1(token_source.encode()).hexdigest()[:16]

    # Track admin messages for this token
    notifications = context.bot_data.setdefault("payment_notifications", {})
    notifications[token] = {
        "student_id": update.effective_user.id,
        "item_type": payment_meta.get("item_type"),
        "item_id": payment_meta.get("item_id"),
        "item_title": payment_meta.get("item_title"),
        "messages": [],  # list of (admin_id, message_id)
        "processed": False,
        "decision": None,
        "decided_by": None,
    }

    kb = admin_approval_keyboard(token)

    # Send to ALL admins: forward photo + details with buttons
    for admin_id in (config.bot.admin_user_ids or []):
        try:
            await context.bot.forward_message(
                chat_id=admin_id,
                from_chat_id=update.effective_chat.id,
                message_id=update.message.message_id,
            )
            sent = await context.bot.send_message(
                chat_id=admin_id, text=caption, reply_markup=kb
            )
            notifications[token]["messages"].append((admin_id, sent.message_id))
        except Exception:
            continue

    # Clear context markers
    if context.user_data.get("pending_course"):
        del context.user_data["pending_course"]
    if context.user_data.get("book_purchase"):
        del context.user_data["book_purchase"]

    await update.message.reply_text(
        success_message, reply_markup=build_main_menu_keyboard()
    )


# Callback handlers for admin approval/rejection
@rate_limit_handler("admin")
async def handle_payment_decision(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    query = update.callback_query
    if not query:
        return
    await query.answer()

    data = query.data  # format: pay:{token}:{decision}
    try:
        _, token, decision = data.split(":", 2)
    except Exception:
        return

    user_id = update.effective_user.id
    if user_id not in context.bot_data.get("config").bot.admin_user_ids:
        await query.edit_message_text("⛔️ مجاز نیست.")
        return

    storage: StudentStorage = context.bot_data["storage"]
    notifications = context.bot_data.setdefault("payment_notifications", {})
    meta = notifications.get(token)
    if not meta:
        await query.edit_message_text("⛔️ اطلاعات پرداخت یافت نشد یا منقضی شده است.")
        return

    # If already processed, disable this keyboard too
    if meta.get("processed"):
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except Exception:
            pass
        return

    # Update user data accordingly and notify
    try:
        student_id = meta["student_id"]
        item_type = meta["item_type"]
        item_id = meta["item_id"]
        item_title = meta.get("item_title") or item_id

        if decision == "approve":
            if item_type == "course":
                # Move pending course to purchased
                student = storage.get_student(student_id)
                if student and item_id:
                    # Remove from pending and add to purchased
                    pend = student.get("pending_payments", [])
                    if item_id in pend:
                        pend.remove(item_id)
                    purchased = student.get("purchased_courses", [])
                    if item_id not in purchased:
                        purchased.append(item_id)
                    student["pending_payments"] = pend
                    student["purchased_courses"] = purchased
                    storage.save_student(student)
            elif item_type == "book":
                # Mark matching book purchase as approved (flag)
                student = storage.get_student(student_id)
                if student:
                    purchases = student.get("book_purchases", [])
                    for p in reversed(purchases):
                        if p.get("title") == item_title:
                            p["approved"] = True
                            break
                    storage.save_student(student)
            # Notify student
            await context.bot.send_message(
                chat_id=student_id,
                text=(
                    f"✅ پرداخت شما برای «{item_title}» تایید شد."
                    if item_type == "book"
                    else f"✅ پرداخت شما برای دوره «{item_title}» تایید شد."
                ),
            )
            result_text = "✅ پرداخت تایید شد و به کاربر اطلاع داده شد."
        elif decision == "reject":
            await context.bot.send_message(
                chat_id=student_id,
                text=(
                    "❌ پرداخت شما تایید نشد. اگر مطمئن هستید پرداخت انجام شده، لطفاً با @ostad_hatami تماس بگیرید."
                ),
            )
            result_text = "❌ پرداخت رد شد و به کاربر اطلاع داده شد."

        # Mark processed and disable buttons for all admin messages
        meta["processed"] = True
        meta["decision"] = decision
        meta["decided_by"] = user_id

        for admin_id, msg_id in meta.get("messages", []):
            try:
                await context.bot.edit_message_reply_markup(
                    chat_id=admin_id, message_id=msg_id, reply_markup=None
                )
                await context.bot.edit_message_text(
                    chat_id=admin_id, message_id=msg_id, text=result_text
                )
            except Exception:
                continue
    except Exception:
        pass


def build_payment_handlers():
    """Build and return payment handlers for registration in bot.py"""
    from telegram.ext import MessageHandler, filters

    return [
        MessageHandler(filters.PHOTO, handle_payment_receipt),
        CallbackQueryHandler(
            handle_payment_decision,
            pattern=r"^pay:[a-f0-9]{16}:(approve|reject)$",
        ),
    ]
