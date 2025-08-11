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
import asyncio
from database.db import session_scope
from database.service import (
    get_or_create_user,
    create_purchase,
    add_receipt,
    approve_or_reject_purchase,
)


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
        # Create DB purchase pending
        with session_scope() as session:
            u = get_or_create_user(session, update.effective_user.id)
            purchase = create_purchase(
                session,
                user_id=u.id,
                product_type="course",
                product_id=course_id,
                status="pending",
            )
        # Notify admins of new pending course purchase
        try:
            from utils.admin_notify import notify_admins
            await notify_admins(
                context,
                context.bot_data.get("config").bot.admin_user_ids,
                f"🧾 پرداخت دوره در انتظار | کاربر {update.effective_user.id} | دوره: {course_id}",
            )
        except Exception:
            pass

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
        # Create DB purchase pending (book)
        with session_scope() as session:
            u = get_or_create_user(session, update.effective_user.id)
            purchase = create_purchase(
                session,
                user_id=u.id,
                product_type="book",
                product_id=book_data.get("title", "book"),
                status="pending",
            )
        # Notify admins of new pending book purchase
        try:
            from utils.admin_notify import notify_admins
            await notify_admins(
                context,
                context.bot_data.get("config").bot.admin_user_ids,
                f"🧾 پرداخت کتاب در انتظار | کاربر {update.effective_user.id} | محصول: {book_data.get('title','book')}",
            )
        except Exception:
            pass

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

    # Prevent duplicate receipts: block re-use of the same Telegram file_unique_id for 7 days
    receipts_index = context.bot_data.setdefault("receipts_index", {})  # id -> ts
    file_uid = getattr(largest_photo, "file_unique_id", None)
    now_ts = time.time()
    retention = 7 * 24 * 3600
    # Purge old
    try:
        to_del = [k for k, ts in receipts_index.items() if now_ts - ts > retention]
        for k in to_del:
            del receipts_index[k]
    except Exception:
        pass
    if file_uid and file_uid in receipts_index:
        await update.message.reply_text(
            "⚠️ این رسید قبلاً ارسال شده است و قابل استفاده مجدد نیست.",
            reply_markup=build_main_menu_keyboard(),
        )
        return

    # Prevent duplicate receipts: accept only one active token per user+item for 2 minutes
    notifications = context.bot_data.setdefault("payment_notifications", {})
    recent_tokens = [
        t
        for t, meta in notifications.items()
        if meta.get("student_id") == update.effective_user.id
        and not meta.get("processed")
    ]
    # If there is a very recent open token for same type+id, reject to prevent spam/dupes
    for t in recent_tokens:
        meta = notifications.get(t) or {}
        if (
            meta.get("item_type") == payment_meta.get("item_type")
            and meta.get("item_id") == payment_meta.get("item_id")
            and time.time() - meta.get("created_at", 0) < 120
        ):
            await update.message.reply_text(
                "⚠️ رسید شما قبلاً دریافت شده و در حال بررسی است.",
                reply_markup=build_main_menu_keyboard(),
            )
            return

    # Generate token to correlate notifications across admins
    token_source = f"{update.effective_user.id}:{payment_meta.get('item_type')}:{payment_meta.get('item_id')}:{time.time()}"
    token = hashlib.sha1(token_source.encode()).hexdigest()[:16]

    # Track admin messages for this token
    notifications[token] = {
        "student_id": update.effective_user.id,
        "item_type": payment_meta.get("item_type"),
        "item_id": payment_meta.get("item_id"),
        "item_title": payment_meta.get("item_title"),
        "messages": [],  # list of (admin_id, message_id)
        "processed": False,
        "decision": None,
        "decided_by": None,
        "created_at": time.time(),
        "decided_at": None,
        "file_unique_id": file_uid,
    }

    kb = admin_approval_keyboard(token)

    # Send to ALL admins: forward photo + details with buttons
    for admin_id in config.bot.admin_user_ids or []:
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

    # Clear context markers and record receipt id
    if file_uid:
        receipts_index[file_uid] = now_ts

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

        # Atomic decision in DB
        from sqlalchemy import select
        from database.models_sql import User as DBUser, Purchase as DBPurchase

        with session_scope() as session:
            db_user = session.execute(
                select(DBUser).where(DBUser.telegram_user_id == student_id)
            ).scalar_one_or_none()
            db_purchase = session.execute(
                select(DBPurchase)
                .where(
                    DBPurchase.user_id == (db_user.id if db_user else -1),
                    DBPurchase.product_type
                    == ("book" if item_type == "book" else "course"),
                    DBPurchase.product_id == item_id,
                    DBPurchase.status == "pending",
                )
                .order_by(DBPurchase.created_at.desc())
            ).scalar_one_or_none()
            if db_purchase:
                approve_or_reject_purchase(session, db_purchase.id, user_id, decision)

        # Notify student
        await context.bot.send_message(
            chat_id=student_id,
            text=(
                f"✅ پرداخت شما برای «{item_title}» تایید شد."
                if decision == "approve"
                else f"❌ پرداخت شما برای «{item_title}» ناموفق بود. اگر مطمئن هستید پرداخت انجام شده، لطفاً با @ostad_hatami تماس بگیرید."
            ),
        )
        result_text = (
            "✅ پرداخت تایید شد و به کاربر اطلاع داده شد."
            if decision == "approve"
            else "❌ پرداخت رد شد و به کاربر اطلاع داده شد."
        )
        # Notify admins with concise status update
        try:
            from utils.admin_notify import notify_admins
            await notify_admins(
                context,
                context.bot_data.get("config").bot.admin_user_ids,
                f"📊 وضعیت پرداخت {item_type} «{item_title}» برای کاربر {student_id}: {('تایید' if decision=='approve' else 'رد')}",
            )
        except Exception:
            pass

        # Mark processed and disable buttons for all admin messages
        meta["processed"] = True
        meta["decision"] = decision
        meta["decided_by"] = user_id
        meta["decided_at"] = time.time()

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
        # Pagination handler for orders_ui
        CallbackQueryHandler(
            lambda u, c: c.application.create_task(_orders_page(u, c)),
            pattern=r"^orders_page:\d+(:book|:course|:all)?:(-|\d+)?$",
        ),
    ]


async def _orders_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    await query.answer()
    if (
        update.effective_user.id
        not in context.bot_data.get("config").bot.admin_user_ids
    ):
        await query.edit_message_text("⛔️ مجاز نیست.")
        return
    try:
        parts = query.data.split(":")  # orders_page:page:type:user
        page = max(0, int(parts[1]))
        type_filter = (parts[2] if len(parts) > 2 else "all") or "all"
        user_str = parts[3] if len(parts) > 3 else "-"
        user_filter = int(user_str) if user_str.isdigit() else None
    except Exception:
        page, type_filter, user_filter = 0, "all", None

    notifications = context.bot_data.get("payment_notifications", {})
    pending = [(t, m) for t, m in notifications.items() if not m.get("processed")]
    if type_filter in ("book", "course"):
        pending = [(t, m) for t, m in pending if m.get("item_type") == type_filter]
    if user_filter is not None:
        pending = [
            (t, m) for t, m in pending if int(m.get("student_id", 0)) == user_filter
        ]
    if not pending:
        await query.edit_message_text("مورد در انتظاری وجود ندارد.")
        return

    page_size = 5
    ordered = list(
        sorted(pending, key=lambda kv: kv[1].get("created_at", 0), reverse=True)
    )
    start = page * page_size
    end = start + page_size
    slice_items = ordered[start:end]

    from telegram import InlineKeyboardMarkup, InlineKeyboardButton

    lines = [f"🕒 پرداخت‌های در انتظار (صفحه {page+1})"]
    rows = []
    for token, meta in slice_items:
        title = meta.get("item_title", "")
        student_id = meta.get("student_id")
        lines.append(
            f"• {meta.get('item_type')} «{title}» | کاربر {student_id} | توکن: {token}"
        )
        rows.append(
            [
                InlineKeyboardButton("✅ تایید", callback_data=f"pay:{token}:approve"),
                InlineKeyboardButton("❌ رد", callback_data=f"pay:{token}:reject"),
            ]
        )
    nav = []
    if start > 0:
        nav.append(
            InlineKeyboardButton(
                "⬅️ قبلی",
                callback_data=f"orders_page:{page-1}:{type_filter}:{user_filter if user_filter is not None else '-'}",
            )
        )
    if end < len(ordered):
        nav.append(
            InlineKeyboardButton(
                "بعدی ➡️",
                callback_data=f"orders_page:{page+1}:{type_filter}:{user_filter if user_filter is not None else '-'}",
            )
        )
    if nav:
        rows.append(nav)

    await query.edit_message_text(
        "\n".join(lines), reply_markup=InlineKeyboardMarkup(rows) if rows else None
    )
