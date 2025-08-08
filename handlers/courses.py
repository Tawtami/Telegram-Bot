#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Course management handlers for Ostad Hatami Bot
"""

from typing import Any, Dict
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from config import config
from utils.storage import StudentStorage
from ui.keyboards import build_main_menu_keyboard


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
    except:
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

    message_text += "📩 ثبت‌نام سریع فقط با یه پیام به:\n👉 @ostad_hatami\n\n✏️ فقط بنویس: اسمت + پایه + کلاس + شهر"

    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_menu")])

    await query.edit_message_text(
        message_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML,
    )


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
    except:
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
        parse_mode=ParseMode.HTML,
    )


async def handle_purchased_courses(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle purchased courses menu"""
    query = update.callback_query
    if not query:
        return

    await query.answer()

    # Get user's purchased courses
    storage: StudentStorage = context.bot_data["storage"]
    student = storage.get_student(query.from_user.id)

    if not student or not student.get("purchased_courses"):
        await query.edit_message_text(
            "🛒 دوره‌های خریداری‌شده:\n\n" "شما هنوز هیچ دوره‌ای خریداری نکرده‌اید.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_menu")]]
            ),
        )
        return

    # Example course details (in production, load from database)
    course_details = {
        "paid1": {
            "title": "دوره جامع ریاضی کنکور",
            "link": "https://skyroom.online/course1",
        },
        "paid2": {
            "title": "دوره فشرده هندسه",
            "link": "https://skyroom.online/course2",
        },
    }

    # Build purchased courses list
    message_text = "🛒 دوره‌های خریداری‌شده:\n\n"
    keyboard = []

    for course_id in student["purchased_courses"]:
        if course_id in course_details:
            course = course_details[course_id]
            message_text += f"📚 {course['title']}\n"
            keyboard.append(
                [
                    InlineKeyboardButton(
                        text=f"🔗 ورود به {course['title']}", url=course["link"]
                    )
                ]
            )

    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_menu")])

    await query.edit_message_text(
        message_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML,
    )


async def handle_course_registration(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle course registration"""
    query = update.callback_query
    if not query:
        return

    await query.answer()

    # Parse course type and ID
    _, course_type, course_id = query.data.split("_", 2)
    storage: StudentStorage = context.bot_data["storage"]

    if course_type == "free":
        # Register for free course
        if storage.save_course_registration(query.from_user.id, course_id):
            await query.edit_message_text(
                "✅ ثبت‌نام شما در دوره رایگان با موفقیت انجام شد.\n\n"
                "جزئیات دوره به زودی برای شما ارسال خواهد شد.",
                reply_markup=build_main_menu_keyboard(),
            )
        else:
            await query.edit_message_text(
                "❌ خطا در ثبت‌نام. لطفاً دوباره تلاش کنید.",
                reply_markup=build_main_menu_keyboard(),
            )
    else:
        # Show payment info for paid course
        await query.edit_message_text(
            "💳 اطلاعات پرداخت:\n\n"
            "1️⃣ مبلغ را به شماره کارت زیر واریز کنید:\n"
            "6037-9974-1234-5678\n"
            "به نام: استاد حاتمی\n\n"
            "2️⃣ تصویر رسید پرداخت را ارسال کنید.\n\n"
            "❗️ پس از تایید پرداخت توسط ادمین، دوره به لیست دوره‌های خریداری‌شده شما اضافه خواهد شد.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 انصراف", callback_data="back_to_menu")]]
            ),
        )

        # Store course ID for payment verification
        context.user_data["pending_course"] = course_id


async def handle_payment_receipt(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle payment receipt photo"""
    if not context.user_data.get("pending_course"):
        await update.message.reply_text(
            "❌ هیچ دوره‌ای در انتظار پرداخت نیست.",
            reply_markup=build_main_menu_keyboard(),
        )
        return

    course_id = context.user_data["pending_course"]
    storage: StudentStorage = context.bot_data["storage"]

    # Add to pending payments
    if not storage.add_pending_payment(update.effective_user.id, course_id):
        await update.message.reply_text(
            "❌ خطا در ثبت پرداخت. لطفاً دوباره تلاش کنید.",
            reply_markup=build_main_menu_keyboard(),
        )
        return

    # Forward receipt to admins
    student = storage.get_student(update.effective_user.id)
    caption = (
        f"🧾 رسید پرداخت دوره\n\n"
        f"کاربر: {student['first_name']} {student['last_name']}\n"
        f"شناسه کاربری: {update.effective_user.id}\n"
        f"شناسه دوره: {course_id}\n\n"
        f"برای تایید پرداخت از دستور زیر استفاده کنید:\n"
        f"/confirm_payment {update.effective_user.id}"
    )

    for admin_id in config.bot.admin_user_ids:
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
            logger.error(f"Error forwarding receipt to admin {admin_id}: {e}")

    # Clear pending course
    del context.user_data["pending_course"]

    await update.message.reply_text(
        "✅ رسید پرداخت شما دریافت شد.\n\n"
        "پس از تایید توسط ادمین، دوره به لیست دوره‌های خریداری‌شده شما اضافه خواهد شد.",
        reply_markup=build_main_menu_keyboard(),
    )
