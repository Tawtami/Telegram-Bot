#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Course management handlers for Ostad Hatami Bot
"""

from typing import Any, Dict
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

import logging
from config import config
from database.db import session_scope
from utils.rate_limiter import rate_limit_handler
from ui.keyboards import build_main_menu_keyboard
from database.db import session_scope
from database.service import get_or_create_user, create_purchase
from utils.admin_notify import send_paginated_list
from database.service import get_course_participants_by_slug
from database.service import get_daily_question, submit_answer
from sqlalchemy import select
from database.models_sql import User as DBUser

logger = logging.getLogger(__name__)


@rate_limit_handler("default")
async def handle_free_courses(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle free courses menu"""
    query = update.callback_query
    if not query:
        return

    await query.answer()

    # Load free courses from JSON file
    import json

    try:
        with open("data/courses.json", "r", encoding="utf-8") as f:
            all_courses = json.load(f)
        free_courses = [
            course
            for course in all_courses
            if course["course_type"] == "free" and course["is_active"]
        ]
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        free_courses = []

    if not free_courses:
        await query.edit_message_text(
            "📚 در حال حاضر دوره رایگانی موجود نیست.\n\n" "🔙 بازگشت به منوی اصلی:",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_menu")]]
            ),
            parse_mode=ParseMode.HTML,
        )
        return

    # Build course list with registration buttons
    keyboard = []
    message_text = "🎓 کلاس‌های رایگان جمعه با استاد حاتمی\n\n"

    for course in free_courses:
        schedule_info = f"⏰ {course['schedule']}"
        if "platform" in course:
            schedule_info += f" | 📍 {course['platform']}"
        if "max_students" in course and course["max_students"] > 0:
            schedule_info += f" | 👥 حداکثر {course['max_students']} نفر"

        message_text += (
            f"📚 {course['title']}\n"
            f"📝 {course['description']}\n"
            f"{schedule_info}\n\n"
        )

        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"📝 ثبت‌نام در {course['title']}",
                    callback_data=f"register_course_free_{course['course_id']}",
                )
            ]
        )

    message_text += "🎓 **دوره‌های رایگان نیازی به پرداخت ندارند!**\n\n"
    message_text += "📩 برای ثبت‌نام سریع:\n👉 @ostad_hatami\n\n✏️ فقط بنویس: اسمت + پایه + کلاس + شهر"

    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_menu")])

    await query.edit_message_text(
        message_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        disable_web_page_preview=True,
    )


@rate_limit_handler("default")
async def handle_paid_courses(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle paid courses menu"""
    query = update.callback_query
    if not query:
        return

    await query.answer()

    # Load paid courses from JSON file
    import json

    try:
        with open("data/courses.json", "r", encoding="utf-8") as f:
            all_courses = json.load(f)
        paid_courses = [
            course
            for course in all_courses
            if course["course_type"] == "paid" and course["is_active"]
        ]
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        paid_courses = []

    if not paid_courses:
        await query.edit_message_text(
            "💼 در حال حاضر دوره تخصصی‌ای موجود نیست.\n\n" "🔙 بازگشت به منوی اصلی:",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_menu")]]
            ),
            parse_mode=ParseMode.HTML,
        )
        return

    # Build course list with details and registration buttons
    keyboard = []
    message_text = "💼 دوره‌های تخصصی:\n\n"

    for i, course in enumerate(paid_courses, 1):
        message_text += f"{i}. {course['title']}\n"
        message_text += f"📝 {course['description']}\n"

        if "price" in course and course["price"] > 0:
            message_text += f"💰 قیمت: {course['price']:,} تومان\n"
        else:
            message_text += f"💰 قیمت: تماس بگیرید\n"

        if "duration" in course:
            message_text += f"⏱️ مدت: {course['duration']}\n"
        if "schedule" in course:
            message_text += f"📅 زمان: {course['schedule']}\n"
        if "start_date" in course:
            message_text += f"🚀 شروع: {course['start_date']}\n"

        # Add features if available
        if "features" in course:
            message_text += "✨ ویژگی‌ها:\n"
            for feature in course["features"]:
                message_text += f"• {feature}\n"

        # Add modules if available
        if "modules" in course:
            message_text += "📚 محورهای دوره:\n"
            for j, module in enumerate(course["modules"], 1):
                message_text += f"{j}. {module}\n"

        message_text += "\n"

        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"📝 ثبت‌نام در {course['title']}",
                    callback_data=f"register_course_paid_{course['course_id']}",
                )
            ]
        )

    message_text += "📞 برای ثبت‌نام و اطلاعات بیشتر:\n"
    message_text += "📱 +989381530556\n"
    message_text += "💬 @ostad_hatami\n"

    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_menu")])

    await query.edit_message_text(
        message_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        disable_web_page_preview=True,
    )


@rate_limit_handler("default")
async def handle_purchased_courses(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle purchased courses menu"""
    query = update.callback_query
    if not query:
        return

    await query.answer()

    # Build user's courses from SQL purchases
    from sqlalchemy import select
    from database.models_sql import Purchase, User as DBUser

    with session_scope() as session:
        db_user = session.execute(
            select(DBUser).where(DBUser.telegram_user_id == query.from_user.id)
        ).scalar_one_or_none()
        if not db_user:
            await query.edit_message_text(
                "❌ ابتدا ثبت‌نام کنید.",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_menu")]]
                ),
            )
            return
        rows = list(
            session.execute(
                select(Purchase).where(Purchase.user_id == db_user.id)
            ).scalars()
        )
    user_courses = {
        "free_courses": [
            p.product_id
            for p in rows
            if p.product_type == "course" and p.status == "approved"
        ],
        "purchased_courses": [
            p.product_id
            for p in rows
            if p.product_type == "course" and p.status != "approved"
        ],
    }

    if not user_courses["purchased_courses"] and not user_courses["free_courses"]:
        await query.edit_message_text(
            "🛒 سبد خرید من:\n\n"
            "شما هنوز در هیچ دوره‌ای ثبت‌نام نکرده‌اید.\n\n"
            "🎓 برای ثبت‌نام در دوره‌های رایگان:\n"
            "📚 دوره‌های رایگان جمعه\n\n"
            "💼 برای دوره‌های تخصصی:\n"
            "📞 تماس با @ostad_hatami",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_menu")]]
            ),
        )
        return

    # Load course details from JSON
    import json

    try:
        with open("data/courses.json", "r", encoding="utf-8") as f:
            all_courses = json.load(f)
        course_details = {c["course_id"]: c for c in all_courses}
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        course_details = {}

    # Build courses list
    message_text = "🛒 سبد خرید من:\n\n"
    keyboard = []

    # Show free courses
    if user_courses["free_courses"]:
        message_text += "🎓 دوره‌های رایگان:\n"
        for course_id in user_courses["free_courses"]:
            if course_id in course_details:
                course = course_details[course_id]
                message_text += f"📚 {course['title']}\n"
                if course.get("schedule"):
                    message_text += f"📅 {course['schedule']}\n"
                if course.get("platform"):
                    message_text += f"📍 {course['platform']}\n"
                message_text += "✅ **وضعیت:** فعال\n\n"

    # Show purchased courses
    if user_courses["purchased_courses"]:
        message_text += "💼 دوره‌های تخصصی:\n"
        for course_id in user_courses["purchased_courses"]:
            if course_id in course_details:
                course = course_details[course_id]
                message_text += f"📚 {course['title']}\n"

                # Check if course is approved (has link)
                if course.get("link"):
                    message_text += "✅ **وضعیت:** تایید شده\n"
                    keyboard.append(
                        [
                            InlineKeyboardButton(
                                text=f"🔗 ورود به {course['title']}", url=course["link"]
                            )
                        ]
                    )
                else:
                    message_text += "⏳ **وضعیت:** در انتظار تایید ادمین\n"
                    message_text += f"📝 {course.get('description', '')}\n"
                    if course.get("schedule"):
                        message_text += f"📅 {course['schedule']}\n"
                message_text += "\n"

    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_menu")])

    await query.edit_message_text(
        message_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        disable_web_page_preview=True,
    )


@rate_limit_handler("default")
async def handle_course_registration(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle course registration"""
    query = update.callback_query
    if not query:
        return

    await query.answer()

    # Parse course type and ID
    # Expected format: register_course_<type>_<course_id>
    prefix = "register_course_"
    if not query.data.startswith(prefix):
        return
    rest = query.data[len(prefix) :]
    try:
        course_type, course_id = rest.split("_", 1)
    except ValueError:
        course_type, course_id = "paid", rest
    # no JSON storage

    # Load course details from JSON
    import json

    try:
        with open("data/courses.json", "r", encoding="utf-8") as f:
            all_courses = json.load(f)
        course = next((c for c in all_courses if c["course_id"] == course_id), None)
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        course = None

    if course_type == "free":
        # Register free course in SQL as approved purchase
        try:
            with session_scope() as session:
                u = get_or_create_user(session, query.from_user.id)
                create_purchase(
                    session,
                    user_id=u.id,
                    product_type="course",
                    product_id=course_id,
                    status="approved",
                )
            # JSON reflection removed; SQL is the source of truth
            course_title = course["title"] if course else "دوره رایگان"
            await query.edit_message_text(
                f"✅ ثبت‌نام شما در {course_title} با موفقیت انجام شد!\n\n"
                f"📅 زمان: {course.get('schedule', 'به زودی اعلام می‌شود')}\n"
                f"📍 پلتفرم: {course.get('platform', 'اسکای‌روم')}\n\n"
                "🎓 این دوره کاملاً رایگان است و نیازی به پرداخت ندارد.",
                reply_markup=build_main_menu_keyboard(),
            )
            # Push updated participant list to admins
            try:
                from config import config as app_config

                with session_scope() as session:
                    uids = get_course_participants_by_slug(
                        session, course_id, status="approved"
                    )
                lines = [str(uid) for uid in uids]
                from utils.performance_monitor import monitor

                try:
                    monitor.increment_hourly("participant_pushes")
                except Exception:
                    pass
                await send_paginated_list(
                    context,
                    app_config.bot.admin_user_ids,
                    f"🎓 فهرست شرکت‌کنندگان دوره رایگان {course_title}",
                    lines,
                )
            except Exception:
                pass
        except Exception:
            await query.edit_message_text(
                "❌ خطا در ثبت‌نام. لطفاً دوباره تلاش کنید.",
                reply_markup=build_main_menu_keyboard(),
            )
    else:
        # Show payment info for paid course
        course_title = course["title"] if course else "دوره تخصصی"
        course_price = course.get("price", 0) if course else 0

        payment_text = f"💳 اطلاعات پرداخت برای {course_title}:\n\n"

        if course_price > 0:
            payment_text += f"💰 مبلغ: {course_price:,} تومان\n\n"
        else:
            payment_text += "💰 مبلغ: تماس بگیرید\n\n"

        payment_text += (
            "1️⃣ مبلغ را به شماره کارت زیر واریز کنید:\n"
            f"{config.bot.payment_card_number}\n"
            f"به نام: {config.bot.payment_payee_name}\n\n"
            "2️⃣ تصویر رسید پرداخت را ارسال کنید.\n\n"
            "❗️ پس از تایید پرداخت توسط ادمین، دوره به لیست دوره‌های خریداری‌شده شما اضافه خواهد شد."
        )

        await query.edit_message_text(
            payment_text,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 انصراف", callback_data="back_to_menu")]]
            ),
        )

        # Store course ID for payment verification
        context.user_data["pending_course"] = course_id


def build_course_handlers():
    """Build and return course handlers for registration in bot.py"""
    from telegram.ext import CallbackQueryHandler

    return [
        CallbackQueryHandler(handle_free_courses, pattern=r"^courses_free$"),
        CallbackQueryHandler(handle_paid_courses, pattern=r"^courses_paid$"),
        CallbackQueryHandler(handle_purchased_courses, pattern=r"^courses_purchased$"),
        CallbackQueryHandler(handle_course_registration, pattern=r"^register_course_"),
        CallbackQueryHandler(handle_daily_quiz, pattern=r"^daily_quiz$"),
        CallbackQueryHandler(handle_quiz_answer, pattern=r"^quiz:\d+:\d+$"),
    ]


# ---------------------
# Learning: daily quiz (basic inline flow)
# ---------------------


async def handle_daily_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    await query.answer()
    user = query.from_user
    with session_scope() as session:
        db_user = session.execute(
            select(DBUser).where(DBUser.telegram_user_id == user.id)
        ).scalar_one_or_none()
        if not db_user:
            await query.edit_message_text("❌ ابتدا ثبت‌نام کنید.")
            return
        q = get_daily_question(session, db_user.grade or "دهم")
    if not q:
        await query.edit_message_text("سوال روز موجود نیست. فردا دوباره تلاش کنید.")
        return
    choices = (q.options or {}).get("choices", [])
    rows = [
        [InlineKeyboardButton(text=c, callback_data=f"quiz:{q.id}:{i}")]
        for i, c in enumerate(choices[:8])
    ]
    rows.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_menu")])
    await query.edit_message_text(
        f"سوال روز ({q.grade})\n\n{q.question_text}",
        reply_markup=InlineKeyboardMarkup(rows),
    )


async def handle_quiz_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    await query.answer()
    data = (query.data or "").split(":")
    if len(data) != 3:
        return
    _, qid, sel = data
    try:
        qid = int(qid)
        sel = int(sel)
    except ValueError:
        return
    with session_scope() as session:
        u = session.execute(
            select(DBUser).where(DBUser.telegram_user_id == query.from_user.id)
        ).scalar_one_or_none()
        if not u:
            await query.edit_message_text("❌ ابتدا ثبت‌نام کنید.")
            return
        correct = submit_answer(session, u.id, qid, sel)
    if correct:
        await query.edit_message_text("✅ پاسخ صحیح! آفرین! 🎉")
    else:
        await query.edit_message_text("❌ پاسخ نادرست. دوباره تلاش کن! 💪")
