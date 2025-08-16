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
import time
from config import config
from datetime import datetime, timedelta
from database.db import session_scope
from utils.rate_limiter import rate_limit_handler
from ui.keyboards import build_main_menu_keyboard
from database.service import get_or_create_user, create_purchase
from utils.admin_notify import send_paginated_list
from database.service import get_course_participants_by_slug
from database.service import get_daily_question, submit_answer
from sqlalchemy import select
from database.models_sql import User as DBUser
from database.service import approve_or_reject_purchase, get_pending_purchases

logger = logging.getLogger(__name__)


@rate_limit_handler("default")
async def handle_courses_overview(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a concise Farsi overview of all available programs and the book."""
    query = update.callback_query
    if query:
        await query.answer()
    text = (
        "معرفی کامل دوره‌ها و کتاب استاد حاتمی:\n\n"
        "🔰 دوره ۱ | مهارت‌های خلاق در حل مسائل ریاضی (رایگان)\n"
        "• پایه‌های ۱۰، ۱۱، ۱۲ (ریاضی/تجربی) | زمان: عصرهای جمعه | آنلاین در اسکای‌روم\n\n"
        "🔰 دوره ۲ | کلاس‌های تک‌درس (تخصصی)\n"
        "• دروس تجربی: ریاضی ۱، ۲، ۳ | دروس ریاضی: ریاضی ۱، حسابان ۱ و ۲، گسسته، هندسه ۳\n"
        "• ۲۰ تا ۲۵ جلسه | هر جلسه ۹۰ دقیقه | جلسه‌ای ۱۵۰ هزار ت | پرداخت کل قبل از شروع\n\n"
        "🔰 دوره ۳ | کلاس‌های خصوصی آنلاین ریاضی\n"
        "• پایه‌های ۱۰ تا ۱۲، ریاضی/تجربی | هزینه: با هماهنگی استاد\n\n"
        "🔰 دوره ۴ | دوره جامع پایه تا کنکور\n"
        "• ۴۰ جلسه | هر جلسه ۹۰ دقیقه | جلسه‌ای ۱۵۰ هزار ت\n\n"
        "🔰 دوره ۵ | همایش‌ها و کارگاه‌های ماهانه (حل مسائل خاص)\n"
        "• پایه‌های ۱۰، ۱۱، ۱۲ | ثبت‌نام ۱۰۰ هزار ت | اعلام زمان ماهانه\n\n"
        "🕒 همه جلسات: ۹۰ دقیقه | 📍 پلتفرم: اسکای‌روم\n\n"
        "📘 کتاب «انفجار خلاقیت»\n"
        "• قیمت: ۶۸۰ هزار ت | ارسال پستی برای اعضای کانال رایگان (تهران ~۱۰۰ هزار ت)\n"
        "• برای ارسال: نام کامل، آدرس، کدپستی و شماره همراه لازم است.\n\n"
        "برای مشاهده دوره‌های رایگان/تخصصی یا خرید کتاب، از دکمه‌های زیر استفاده کنید."
    )
    kb = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🎓 دوره‌های رایگان", callback_data="courses_free")],
            [InlineKeyboardButton("💼 دوره‌های تخصصی", callback_data="courses_paid")],
            [InlineKeyboardButton("📖 کتاب انفجار خلاقیت", callback_data="book_info")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_menu")],
        ]
    )
    if query:
        await query.edit_message_text(text, reply_markup=kb)
    else:
        await update.effective_message.reply_text(text, reply_markup=kb)


@rate_limit_handler("default")
async def handle_free_courses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle free courses menu"""
    query = update.callback_query
    if not query:
        return

    await query.answer()

    # Load free courses with caching
    import json, os
    from utils.cache import cache_manager

    c = cache_manager.get_cache("courses")
    all_courses = c._get_sync("all_courses")
    if all_courses is None:
        try:
            with open("data/courses.json", "r", encoding="utf-8") as f:
                all_courses = json.load(f)
        except Exception:
            all_courses = []
        c._set_sync("all_courses", all_courses, ttl=600)
    free_courses = [
        course
        for course in all_courses
        if course.get("course_type") == "free" and course.get("is_active")
    ]

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
            f"📚 {course['title']}\n" f"📝 {course['description']}\n" f"{schedule_info}\n\n"
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
    message_text += (
        "📩 برای ثبت‌نام سریع:\n👉 @ostad_hatami\n\n✏️ فقط بنویس: اسمت + پایه + کلاس + شهر"
    )

    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_menu")])

    await query.edit_message_text(
        message_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        disable_web_page_preview=True,
    )


@rate_limit_handler("default")
async def handle_paid_courses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle paid courses menu showing exactly the 4 categories required."""
    query = update.callback_query
    if not query:
        return

    await query.answer()

    text = (
        "دوره‌های تخصصی:\n\n"
        "1) کلاس‌های تک‌درس — ۲۰ تا ۲۵ جلسه، هر جلسه ۹۰ دقیقه — جلسه‌ای ۱۵۰ هزار ت (پرداخت کامل قبل از شروع)\n\n"
        "2) کلاس خصوصی آنلاین — پایه‌های ۱۰ تا ۱۲ (ریاضی/تجربی) — هزینه با هماهنگی استاد\n\n"
        "3) دوره جامع پایه تا کنکور — ۴۰ جلسه (۹۰ دقیقه) — جلسه‌ای ۱۵۰ هزار ت\n\n"
        "4) همایش/کارگاه‌های ماهانه — ثبت‌نام ۱۰۰ هزار ت (موضوع هر ماه بعداً اعلام می‌شود)\n"
    )

    kb = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("کلاس‌های تک‌درس", callback_data="paid_single")],
            [InlineKeyboardButton("کلاس خصوصی", callback_data="paid_private")],
            [InlineKeyboardButton("دوره جامع تا کنکور", callback_data="paid_comprehensive")],
            [InlineKeyboardButton("همایش/کارگاه ماهانه", callback_data="paid_workshops")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_menu")],
        ]
    )

    await query.edit_message_text(text, reply_markup=kb)


@rate_limit_handler("default")
async def handle_paid_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """High-level paid menu splitting into 4 options."""
    query = update.callback_query
    if not query:
        return
    await query.answer()
    text = (
        "💼 دوره‌های تخصصی:\n\n"
        "1) کلاس‌های آموزشی تک‌درس (تجربی/ریاضی) — مخصوص امتحان نهایی و آزمون‌های آزمایشی\n"
        "2) کلاس‌های خصوصی آنلاین ریاضی — هماهنگی مستقیم با استاد\n"
        "3) دوره جامع پایه تا کنکور — ۴۰ جلسه (۱۵۰هزار/جلسه)\n"
        "4) همایش‌های کارگاه‌های ماهانه — موضوع هر ماه بعداً اعلام می‌شود\n"
    )
    kb = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("1) تک‌درس", callback_data="paid_single")],
            [InlineKeyboardButton("2) خصوصی آنلاین", callback_data="paid_private")],
            [InlineKeyboardButton("3) دوره جامع", callback_data="paid_comprehensive")],
            [InlineKeyboardButton("4) همایش ماهانه", callback_data="paid_workshops")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_menu")],
        ]
    )
    await query.edit_message_text(text, reply_markup=kb)


@rate_limit_handler("default")
async def handle_paid_single(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return
    await query.answer()
    kb = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("تجربی: ریاضی ۱", callback_data="paid_single_exp_math1")],
            [InlineKeyboardButton("تجربی: ریاضی ۲", callback_data="paid_single_exp_math2")],
            [InlineKeyboardButton("تجربی: ریاضی ۳", callback_data="paid_single_exp_math3")],
            [InlineKeyboardButton("ریاضی: ریاضی ۱", callback_data="paid_single_math_math1")],
            [InlineKeyboardButton("ریاضی: حسابان ۱", callback_data="paid_single_math_hesa1")],
            [InlineKeyboardButton("ریاضی: حسابان ۲", callback_data="paid_single_math_hesa2")],
            [InlineKeyboardButton("ریاضی: گسسته ۳", callback_data="paid_single_math_dis3")],
            [InlineKeyboardButton("ریاضی: هندسه ۳", callback_data="paid_single_math_geo3")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="paid_menu")],
        ]
    )
    await query.edit_message_text(
        "کلاس‌های تک‌درس (۲۰–۲۵ جلسه، ۹۰ دقیقه، ۱۵۰هزار/جلسه) — مخصوص امتحان نهایی/آزمون‌های آزمایشی",
        reply_markup=kb,
    )


@rate_limit_handler("default")
async def handle_paid_single_select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show detail and register button for a selected single-lesson course."""
    query = update.callback_query
    if not query:
        return
    await query.answer()
    slug_map = {
        "paid_single_exp_math1": ("ریاضی ۱ (تجربی)", "exp_math1"),
        "paid_single_exp_math2": ("ریاضی ۲ (تجربی)", "exp_math2"),
        "paid_single_exp_math3": ("ریاضی ۳ (تجربی)", "exp_math3"),
        "paid_single_math_math1": ("ریاضی ۱ (ریاضی)", "math_math1"),
        "paid_single_math_hesa1": ("حسابان ۱", "hesaban1"),
        "paid_single_math_hesa2": ("حسابان ۲", "hesaban2"),
        "paid_single_math_dis3": ("گسسته ۳", "discrete3"),
        "paid_single_math_geo3": ("هندسه ۳", "geometry3"),
    }
    key = query.data
    title, slug = slug_map.get(key, ("تک‌درس", "single_unknown"))
    # Try enrich from data/courses.json if exists
    try:
        import json
        from utils.cache import cache_manager

        c = cache_manager.get_cache("courses")
        all_courses = c._get_sync("all_courses")
        if all_courses is None:
            with open("data/courses.json", "r", encoding="utf-8") as f:
                all_courses = json.load(f)
            c._set_sync("all_courses", all_courses, ttl=600)
        # Find any paid course matching our slug key by course_id or title contains
        course = next(
            (
                co
                for co in all_courses
                if isinstance(co, dict)
                and co.get("course_type") == "paid"
                and (co.get("course_id") == slug or slug in (co.get("course_id") or ""))
            ),
            None,
        )
        if course:
            price = course.get("price", 150000)
            duration = course.get("duration", "۹۰ دقیقه")
            desc = course.get("description", "مخصوص امتحان نهایی و آزمون‌های آزمایشی مؤسسات.")
            schedule = course.get("schedule", "برنامه به‌زودی اعلام می‌شود")
            sessions = course.get("sessions", "۲۰–۲۵ جلسه")
            platform = course.get("platform", "اسکای‌روم")
            notes = course.get("notes", "پرداخت کامل قبل از شروع دوره")
        else:
            price = 150000
            duration = "۹۰ دقیقه"
            desc = "مخصوص امتحان نهایی و آزمون‌های آزمایشی مؤسسات."
            schedule = "برنامه به‌زودی اعلام می‌شود"
            sessions = "۲۰–۲۵ جلسه"
            platform = "اسکای‌روم"
            notes = "پرداخت کامل قبل از شروع دوره"
    except Exception:
        price = 150000
        duration = "۹۰ دقیقه"
        desc = "مخصوص امتحان نهایی و آزمون‌های آزمایشی مؤسسات."
        schedule = "برنامه به‌زودی اعلام می‌شود"
        sessions = "۲۰–۲۵ جلسه"
        platform = "اسکای‌روم"
        notes = "پرداخت کامل قبل از شروع دوره"
    # Clamp negative/None price to 0 and format safely
    try:
        _price_single = int(price or 0)
    except Exception:
        _price_single = 0
    _price_single = max(_price_single, 0)
    price_text = (
        f"💰 جلسه‌ای {_price_single:,} ریال" if _price_single > 0 else "💰 هزینه: تماس بگیرید"
    )
    text = (
        f"🧠 {title}\n"
        f"📚 {sessions} | ⏰ {duration}\n"
        f"{price_text}\n"
        f"📅 {schedule}\n"
        f"🌐 {platform}\n"
        f"📝 {desc}\n"
        f"📌 {notes}\n\n"
        "برای ادامه، پرداخت را انجام دهید و رسید را ارسال کنید."
    )
    kb = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "📝 ثبت‌نام (نمایش اطلاعات پرداخت)", callback_data=f"register_course_paid_{slug}"
                )
            ],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="paid_single")],
        ]
    )
    await query.edit_message_text(text, reply_markup=kb)


@rate_limit_handler("default")
async def handle_paid_private(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return
    await query.answer()
    text = (
        "کلاس‌های خصوصی آنلاین ریاضی:\n"
        "هماهنگی مستقیم با استاد:\n"
        "📞 +989381530556\n"
        "💬 @ostad_hatami\n\n"
        "هزینه کلاس خصوصی: تماس بگیرید (بر اساس زمان و درس انتخابی)."
    )
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 بازگشت", callback_data="paid_menu")]]
        ),
    )


@rate_limit_handler("default")
async def handle_paid_comprehensive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return
    await query.answer()
    kb = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("بخش تجربی", callback_data="paid_comp_exp")],
            [InlineKeyboardButton("بخش ریاضی", callback_data="paid_comp_math")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="paid_menu")],
        ]
    )
    await query.edit_message_text(
        "دوره جامع پایه تا کنکور — ۴۰ جلسه (۹۰ دقیقه)، ۱۵۰هزار/جلسه",
        reply_markup=kb,
    )


@rate_limit_handler("default")
async def handle_paid_comp_select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return
    await query.answer()
    is_exp = query.data == "paid_comp_exp"
    if is_exp:
        title = "دوره جامع پایه تا کنکور (بخش تجربی)"
        desc = "پوشش کامل مباحث ریاضی تجربی در ۴۰ جلسه"
        slug = "comp_exp"
    else:
        title = "دوره جامع پایه تا کنکور (بخش ریاضی)"
        desc = "پوشش مباحث ریاضی ۱، حسابان ۱ و حسابان ۲ در ۴۰ جلسه"
        slug = "comp_math"
    # Try enrich from data
    try:
        import json
        from utils.cache import cache_manager

        c = cache_manager.get_cache("courses")
        all_courses = c._get_sync("all_courses")
        if all_courses is None:
            with open("data/courses.json", "r", encoding="utf-8") as f:
                all_courses = json.load(f)
            c._set_sync("all_courses", all_courses, ttl=600)
        course = next(
            (co for co in all_courses if isinstance(co, dict) and co.get("course_id") == slug),
            None,
        )
        price = (course.get("price") if course else 150000) or 150000
        duration = (course.get("duration") if course else "۹۰ دقیقه") or "۹۰ دقیقه"
        schedule = (
            course.get("schedule") if course else "اعلام برنامه پس از ثبت‌نام"
        ) or "اعلام برنامه پس از ثبت‌نام"
        sessions = (course.get("sessions") if course else "۴۰ جلسه") or "۴۰ جلسه"
        platform = (course.get("platform") if course else "اسکای‌روم") or "اسکای‌روم"
        notes = (
            course.get("notes") if course else "پرداخت جلسه‌ای ۱۵۰هزار تومان"
        ) or "پرداخت جلسه‌ای ۱۵۰هزار تومان"
    except Exception:
        price = 150000
        duration = "۹۰ دقیقه"
        schedule = "اعلام برنامه پس از ثبت‌نام"
        sessions = "۴۰ جلسه"
        platform = "اسکای‌روم"
        notes = "پرداخت جلسه‌ای ۱۵۰هزار تومان"
    # Clamp negative/None price to 0 and format safely
    try:
        _price_comp = int(price or 0)
    except Exception:
        _price_comp = 0
    _price_comp = max(_price_comp, 0)
    text = (
        f"📚 {title}\n{desc}\n" f"{sessions} | ⏰ {duration}\n" f"💰 جلسه‌ای {_price_comp:,} ریال\n"
        if _price_comp > 0
        else "💰 هزینه: تماس بگیرید\n"
        f"📅 {schedule}\n"
        f"🌐 {platform}\n"
        f"📌 {notes}\n\n"
        "برای ادامه، پرداخت را انجام دهید و رسید را ارسال کنید."
    )
    kb = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "📝 ثبت‌نام (نمایش اطلاعات پرداخت)", callback_data=f"register_course_paid_{slug}"
                )
            ],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="paid_comprehensive")],
        ]
    )
    await query.edit_message_text(text, reply_markup=kb)


@rate_limit_handler("default")
async def handle_paid_workshops(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return
    await query.answer()
    # Single source of truth for months
    from utils.workshops import get_workshop_months

    months = get_workshop_months()
    rows = [[InlineKeyboardButton(m, callback_data=f"workshop:{m}")] for m in months]
    rows.append([InlineKeyboardButton("🔙 بازگشت", callback_data="paid_menu")])

    # Derive dynamic duration/price from JSON for parent menu
    duration_line = ""
    price_line = ""
    try:
        import json
        from utils.cache import cache_manager

        c = cache_manager.get_cache("courses")
        all_courses = c._get_sync("all_courses")
        if all_courses is None:
            with open("data/courses.json", "r", encoding="utf-8") as f:
                all_courses = json.load(f)
            c._set_sync("all_courses", all_courses, ttl=600)

        # Collect workshop entries
        workshop_entries = []
        for m in months:
            cid = f"workshop_{m}"
            co = next(
                (x for x in all_courses if isinstance(x, dict) and x.get("course_id") == cid),
                None,
            )
            if co:
                workshop_entries.append(co)

        # Duration: show if all the same and non-empty
        durations = [str(co.get("duration") or "").strip() for co in workshop_entries]
        uniq_durations = {d for d in durations if d}
        if len(uniq_durations) == 1:
            duration_line = f"\n⏰ {next(iter(uniq_durations))}"

        # Price: show thousands sep; if multiple unique positives, show range; otherwise contact
        prices = []
        for co in workshop_entries:
            try:
                pv = int(co.get("price") or 0)
            except Exception:
                pv = 0
            prices.append(max(pv, 0))
        pos_prices = [p for p in prices if p > 0]
        if pos_prices:
            pmin, pmax = min(pos_prices), max(pos_prices)
            if pmin == pmax:
                price_line = f"\nثبت‌نام: {pmin:,} ریال"
            else:
                price_line = f"\nثبت‌نام: {pmin:,}–{pmax:,} ریال"
        else:
            price_line = "\nثبت‌نام: تماس بگیرید"
    except Exception:
        # If anything goes wrong, keep minimal header
        duration_line = ""
        price_line = ""

    header_text = "همایش‌های ماهانه — موضوع بعداً اعلام می‌شود" + duration_line + price_line
    await query.edit_message_text(header_text, reply_markup=InlineKeyboardMarkup(rows))


@rate_limit_handler("default")
async def handle_workshop_select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return
    await query.answer()
    month = query.data.split(":", 1)[1]
    slug = f"workshop_{month}"
    # Enrich from data if available
    try:
        import json
        from utils.cache import cache_manager

        c = cache_manager.get_cache("courses")
        all_courses = c._get_sync("all_courses")
        if all_courses is None:
            with open("data/courses.json", "r", encoding="utf-8") as f:
                all_courses = json.load(f)
            c._set_sync("all_courses", all_courses, ttl=600)
        course = next(
            (co for co in all_courses if isinstance(co, dict) and co.get("course_id") == slug), None
        )
        # Normalize display title to use parentheses regardless of stored title
        title = (course.get("title") if course else None) or f"همایش ماهانه ({month})"
        # Prefer stored description, but normalize generic phrasing to our agreed style
        desc = course.get("description") if course else None
        default_desc = f"همایش ماهانه ({month}) — موضوع بعداً اعلام می‌شود."
        if not desc:
            desc = default_desc
        else:
            # If it's a generic placeholder (e.g., uses "متعاقباً" or similar), standardize it
            if "متعاقباً" in desc or ("موضوع" in desc and "اعلام" in desc):
                desc = default_desc
        price = (course.get("price") if course else 100000) or 100000
        duration = (course.get("duration") if course else "۹۰ دقیقه") or "۹۰ دقیقه"
        schedule = (course.get("schedule") if course else "اعلام تاریخ دقیق") or "اعلام تاریخ دقیق"
        platform = (course.get("platform") if course else "اسکای‌روم") or "اسکای‌روم"
        notes = (
            course.get("notes") if course else "ثبت‌نام: ۱۰۰ هزار تومان"
        ) or "ثبت‌نام: ۱۰۰ هزار تومان"
    except Exception:
        title = f"همایش ماهانه ({month})"
        desc = f"همایش ماهانه ({month}) — موضوع بعداً اعلام می‌شود."
        price = 100000
        duration = "۹۰ دقیقه"
        schedule = "اعلام تاریخ دقیق"
        platform = "اسکای‌روم"
        notes = "ثبت‌نام: ۱۰۰ هزار تومان"
    text = (
        f"📅 {title}\n"
        f"📝 {desc}\n"
        f"⏰ {duration}\n"
        f"💰 {price:,} ریال\n"
        f"📅 {schedule}\n"
        f"🌐 {platform}\n"
        f"📌 {notes}"
    )
    kb = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "📝 ثبت‌نام (نمایش اطلاعات پرداخت)", callback_data=f"register_course_paid_{slug}"
                )
            ],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="paid_workshops")],
        ]
    )
    await query.edit_message_text(text, reply_markup=kb)


@rate_limit_handler("default")
async def handle_purchased_courses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
            session.execute(select(Purchase).where(Purchase.user_id == db_user.id)).scalars()
        )
    user_courses = {
        "free_courses": [
            p.product_id for p in rows if p.product_type == "course" and p.status == "approved"
        ],
        "purchased_courses": [
            p.product_id for p in rows if p.product_type == "course" and p.status != "approved"
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

    # Load course details from cache
    import json
    from utils.cache import cache_manager

    c = cache_manager.get_cache("courses")
    all_courses = c._get_sync("all_courses")
    if all_courses is None:
        try:
            with open("data/courses.json", "r", encoding="utf-8") as f:
                all_courses = json.load(f)
        except Exception:
            all_courses = []
        c._set_sync("all_courses", all_courses, ttl=600)
    course_details = {
        c["course_id"]: c for c in all_courses if isinstance(c, dict) and c.get("course_id")
    }

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
async def handle_course_registration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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

    # Auto-expire stale pending request (>5 minutes) and debounce duplicate taps (<2 minutes)
    pending = context.user_data.get("pending_course_request")
    now_dt = datetime.utcnow()
    if isinstance(pending, dict):
        ts = pending.get("timestamp")
        try:
            # Support legacy float timestamp
            if isinstance(ts, (int, float)):
                ts_dt = datetime.utcfromtimestamp(float(ts))
            else:
                ts_dt = ts if isinstance(ts, datetime) else None
        except Exception:
            ts_dt = None
        # Auto-clear if stale > 5 minutes
        if ts_dt and now_dt - ts_dt > timedelta(minutes=5):
            context.user_data.pop("pending_course_request", None)
            pending = None
        # Debounce duplicates within 2 minutes
        elif (
            ts_dt
            and pending.get("course_id") == course_id
            and (now_dt - ts_dt) < timedelta(minutes=2)
        ):
            return

    # Load course details from cache
    import json
    from utils.cache import cache_manager

    c = cache_manager.get_cache("courses")
    all_courses = c._get_sync("all_courses")
    if all_courses is None:
        try:
            with open("data/courses.json", "r", encoding="utf-8") as f:
                all_courses = json.load(f)
        except Exception:
            all_courses = []
        c._set_sync("all_courses", all_courses, ttl=600)
    course = next(
        (c for c in all_courses if isinstance(c, dict) and c.get("course_id") == course_id),
        None,
    )

    if course_type == "free":
        # Register free course in SQL as PENDING (awaiting admin approval)
        try:
            from utils.admin_notify import notify_admins
            from config import config as app_config

            with session_scope() as session:
                u = get_or_create_user(session, query.from_user.id)
                p = create_purchase(
                    session,
                    user_id=u.id,
                    product_type="course",
                    product_id=course_id,
                    status="pending",
                )
            course_title = course["title"] if course else "دوره رایگان"
            # Inform user
            await query.edit_message_text(
                f"📝 درخواست ثبت‌نام شما در {course_title} ثبت شد و منتظر تأیید ادمین است.\n\n"
                "پس از تأیید، اطلاعات ورود اسکای‌روم از طریق ربات به شما اعلام می‌شود.",
                reply_markup=build_main_menu_keyboard(),
            )
            # Notify admins
            try:
                await notify_admins(
                    context,
                    app_config.bot.admin_user_ids,
                    (
                        "🔔 درخواست جدید دوره رایگان\n"
                        f"کاربر: {query.from_user.id}\n"
                        f"دوره: {course_id}"
                    ),
                )
            except Exception:
                pass
        except Exception:
            await query.edit_message_text(
                "❌ خطا در ثبت‌نام. لطفاً دوباره تلاش کنید.",
                reply_markup=build_main_menu_keyboard(),
            )
    else:
        # Ask for confirmation before showing payment info
        course_title = course["title"] if course else "دوره تخصصی"
        # Determine back target based on slug
        if course_id.startswith("workshop_"):
            back_target = "paid_workshops"
        elif course_id in ("comp_exp", "comp_math"):
            back_target = "paid_comprehensive"
        else:
            back_target = "paid_single"

        confirm_text = (
            f"📝 ثبت‌نام در «{course_title}»\n\n"
            f"آیا مطمئن هستید که می‌خواهید در «{course_title}» ثبت‌نام کنید؟"
        )
        kb = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "✅ تایید", callback_data=f"confirm_register_course_paid_{course_id}"
                    )
                ],
                [InlineKeyboardButton("🔙 بازگشت", callback_data=back_target)],
            ]
        )
        await query.edit_message_text(confirm_text, reply_markup=kb)
        # Save for next step with timestamp (data-driven structure)
        context.user_data["pending_course_request"] = {
            "course_id": course_id,
            "timestamp": now_dt,
        }


@rate_limit_handler("default")
async def handle_course_registration_confirm(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Show final payment info after user confirms registration for paid course."""
    query = update.callback_query
    if not query:
        return
    await query.answer()
    prefix = "confirm_register_course_paid_"
    if not (query.data or "").startswith(prefix):
        return
    course_id = (query.data or "")[len(prefix) :]

    # Load course details from cache
    import json
    from utils.cache import cache_manager

    c = cache_manager.get_cache("courses")
    all_courses = c._get_sync("all_courses")
    if all_courses is None:
        try:
            with open("data/courses.json", "r", encoding="utf-8") as f:
                all_courses = json.load(f)
        except Exception:
            all_courses = []
        c._set_sync("all_courses", all_courses, ttl=600)
    course = next(
        (c for c in all_courses if isinstance(c, dict) and c.get("course_id") == course_id),
        None,
    )

    course_title = course["title"] if course else "دوره تخصصی"
    course_price = course.get("price", 0) if course else 0

    payment_text = f"💳 اطلاعات پرداخت برای {course_title}:\n\n"

    if course_price > 0:
        payment_text += f"💰 مبلغ: {course_price:,} ریال\n\n"
    else:
        payment_text += "💰 مبلغ: تماس بگیرید\n\n"

    from utils.validators import Validator
    card_fmt = Validator.format_card_number(config.bot.payment_card_number)
    payment_text += (
        "1️⃣ مبلغ را به شماره کارت زیر واریز کنید:\n"
        f"{card_fmt}\n"
        f"به نام: {config.bot.payment_payee_name}\n\n"
        "2️⃣ تصویر رسید پرداخت را ارسال کنید.\n\n"
        "❗️ پس از تایید پرداخت توسط ادمین، دوره به لیست دوره‌های خریداری‌شده شما اضافه خواهد شد.\n\n"
        "ℹ️ در صورت هرگونه مشکل در پرداخت، با پشتیبانی تماس بگیرید."
    )

    await query.edit_message_text(
        payment_text,
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("📤 ارسال رسید", callback_data="hint_upload_receipt")],
                [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")],
            ]
        ),
    )

    # Store course ID for payment verification & clear pending request state
    context.user_data["pending_course"] = course_id
    context.user_data.pop("pending_course_request", None)


def build_course_handlers():
    """Build and return course handlers for registration in bot.py"""
    from telegram.ext import CallbackQueryHandler, CommandHandler

    return [
        CallbackQueryHandler(handle_courses_overview, pattern=r"^courses_overview$"),
        CallbackQueryHandler(handle_free_courses, pattern=r"^courses_free$"),
        CallbackQueryHandler(handle_paid_courses, pattern=r"^courses_paid$"),
        CallbackQueryHandler(handle_purchased_courses, pattern=r"^courses_purchased$"),
        CallbackQueryHandler(handle_course_registration, pattern=r"^register_course_"),
        CallbackQueryHandler(
            handle_course_registration_confirm,
            pattern=r"^confirm_register_course_paid_",
        ),
        CallbackQueryHandler(handle_daily_quiz, pattern=r"^daily_quiz$"),
        CallbackQueryHandler(handle_quiz_answer, pattern=r"^quiz:\d+:\d+$"),
        CallbackQueryHandler(handle_paid_menu, pattern=r"^paid_menu$"),
        CallbackQueryHandler(handle_paid_single, pattern=r"^paid_single$"),
        CallbackQueryHandler(handle_paid_single_select, pattern=r"^paid_single_"),
        CallbackQueryHandler(handle_paid_private, pattern=r"^paid_private$"),
        CallbackQueryHandler(handle_paid_comprehensive, pattern=r"^paid_comprehensive$"),
        CallbackQueryHandler(handle_paid_comp_select, pattern=r"^paid_comp_(exp|math)$"),
        CallbackQueryHandler(handle_paid_workshops, pattern=r"^paid_workshops$"),
        CallbackQueryHandler(handle_workshop_select, pattern=r"^workshop:"),
        # Admin commands
        CommandHandler("pending", admin_list_pending),
        CommandHandler("approve", admin_approve),
        CommandHandler("reject", admin_reject),
        CommandHandler("export_pending", admin_export_pending_csv),
        CommandHandler("export_free", admin_export_free_grade),
        CommandHandler("export_workshop", admin_export_workshop),
        CommandHandler("export_paid", admin_export_paid),
    ]


# ---------------------
# Admin helpers (approve free registrations)
# ---------------------


async def admin_list_pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from config import config as app_config

    if update.effective_user.id not in app_config.bot.admin_user_ids:
        return
    with session_scope() as session:
        rows = get_pending_purchases(session, limit=200)
    if not rows:
        await update.effective_message.reply_text("درخواست معلقی وجود ندارد.")
        return
    lines = [
        f"#{r['purchase_id']} | {r['user_id']} | {r['product_type']} | {r['product_id']}"
        for r in rows
    ]
    await update.effective_message.reply_text("درخواست‌های معلق:\n" + "\n".join(lines))


async def admin_export_pending_csv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Export pending requests to CSV for admins (to prepare Skyroom accounts, etc.)."""
    from config import config as app_config

    if update.effective_user.id not in app_config.bot.admin_user_ids:
        return
    with session_scope() as session:
        rows = get_pending_purchases(session, limit=1000)
        ids = [r["user_id"] for r in rows]
        users = {}
        if ids:
            q = session.execute(select(DBUser).where(DBUser.id.in_(ids))).scalars().all()
            for u in q:
                users[int(u.id)] = u
    import csv, io

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            "purchase_id",
            "user_id",
            "telegram_user_id",
            "full_name",
            "product_type",
            "product_id",
            "created_at",
        ]
    )
    for r in rows:
        u = users.get(int(r["user_id"]))
        full_name = (
            " ".join(filter(None, [getattr(u, "first_name", ""), getattr(u, "last_name", "")]))
            if u
            else ""
        )
        writer.writerow(
            [
                r["purchase_id"],
                r["user_id"],
                getattr(u, "telegram_user_id", 0) if u else 0,
                full_name,
                r["product_type"],
                r["product_id"],
                r["created_at"],
            ]
        )
    buf.seek(0)
    await update.effective_message.reply_document(
        document=io.BytesIO(buf.getvalue().encode("utf-8")),
        filename="pending_requests.csv",
        caption="📄 درخواست‌های معلق (CSV)",
    )


async def admin_export_free_grade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Export approved FREE course participants for a grade."""
    from config import config as app_config

    if update.effective_user.id not in app_config.bot.admin_user_ids:
        return
    if not context.args:
        await update.effective_message.reply_text("فرمت: /export_free <پایه>")
        return
    grade = context.args[0]
    from database.models_sql import Purchase, User as DBUser

    with session_scope() as session:
        q = session.execute(
            select(
                DBUser.telegram_user_id, DBUser.first_name, DBUser.last_name, Purchase.product_id
            )
            .join(Purchase, Purchase.user_id == DBUser.id)
            .where(
                Purchase.product_type == "course",
                Purchase.status == "approved",
                DBUser.grade == grade,
                Purchase.product_id.like("free_%"),
            )
            .order_by(Purchase.created_at.desc())
        )
        rows = list(q)
    import csv, io

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["telegram_user_id", "full_name", "free_course_slug"])
    for r in rows:
        full_name = " ".join(filter(None, [r.first_name or "", r.last_name or ""]))
        writer.writerow([int(r.telegram_user_id or 0), full_name, r.product_id])
    buf.seek(0)
    await update.effective_message.reply_document(
        document=io.BytesIO(buf.getvalue().encode("utf-8")),
        filename=f"free_grade_{grade}.csv",
        caption=f"📄 رایگان‌های تاییدشده پایه {grade}",
    )


async def admin_export_workshop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Export workshop registrations (pending by default). Usage: /export_workshop <ماه> [status]"""
    from config import config as app_config

    if update.effective_user.id not in app_config.bot.admin_user_ids:
        return
    if not context.args:
        await update.effective_message.reply_text("فرمت: /export_workshop <ماه> [pending|approved]")
        return
    month = (
        " ".join(context.args[:-1])
        if len(context.args) > 1 and context.args[-1] in ("pending", "approved")
        else " ".join(context.args)
    )
    status = (
        context.args[-1]
        if context.args and context.args[-1] in ("pending", "approved")
        else "pending"
    )
    slug = f"workshop_{month}"
    from database.models_sql import Purchase, User as DBUser

    with session_scope() as session:
        q = session.execute(
            select(DBUser.telegram_user_id, DBUser.first_name, DBUser.last_name)
            .join(Purchase, Purchase.user_id == DBUser.id)
            .where(
                Purchase.product_type == "course",
                Purchase.product_id == slug,
                Purchase.status == status,
            )
            .order_by(Purchase.created_at.asc())
        )
        rows = list(q)
    import csv, io

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["telegram_user_id", "full_name", "status", "slug"])
    for r in rows:
        full_name = " ".join(filter(None, [r.first_name or "", r.last_name or ""]))
        writer.writerow([int(r.telegram_user_id or 0), full_name, status, slug])
    buf.seek(0)
    await update.effective_message.reply_document(
        document=io.BytesIO(buf.getvalue().encode("utf-8")),
        filename=f"workshop_{month}_{status}.csv",
        caption=f"📄 ثبت‌نام‌های همایش {month} ({status})",
    )


async def admin_export_paid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Export paid registrations by slug. Usage: /export_paid <slug> [pending|approved]"""
    from config import config as app_config

    if update.effective_user.id not in app_config.bot.admin_user_ids:
        return
    if not context.args:
        await update.effective_message.reply_text("فرمت: /export_paid <slug> [pending|approved]")
        return
    slug = context.args[0]
    status = (
        context.args[1]
        if len(context.args) > 1 and context.args[1] in ("pending", "approved")
        else "pending"
    )
    from database.models_sql import Purchase, User as DBUser

    with session_scope() as session:
        q = session.execute(
            select(DBUser.telegram_user_id, DBUser.first_name, DBUser.last_name)
            .join(Purchase, Purchase.user_id == DBUser.id)
            .where(
                Purchase.product_type == "course",
                Purchase.product_id == slug,
                Purchase.status == status,
            )
            .order_by(Purchase.created_at.asc())
        )
        rows = list(q)
    import csv, io

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["telegram_user_id", "full_name", "status", "slug"])
    for r in rows:
        full_name = " ".join(filter(None, [r.first_name or "", r.last_name or ""]))
        writer.writerow([int(r.telegram_user_id or 0), full_name, status, slug])
    buf.seek(0)
    await update.effective_message.reply_document(
        document=io.BytesIO(buf.getvalue().encode("utf-8")),
        filename=f"paid_{slug}_{status}.csv",
        caption=f"📄 ثبت‌نام‌های دوره {slug} ({status})",
    )


async def admin_approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from config import config as app_config

    if update.effective_user.id not in app_config.bot.admin_user_ids:
        return
    if not context.args:
        await update.effective_message.reply_text("فرمت: /approve <purchase_id>")
        return
    try:
        pid = int(context.args[0])
    except Exception:
        await update.effective_message.reply_text("شناسه نامعتبر است.")
        return
    with session_scope() as session:
        p = approve_or_reject_purchase(session, pid, update.effective_user.id, "approve")
    if not p:
        await update.effective_message.reply_text("عدم موفقیت در تأیید (شاید قبلاً رسیدگی شده).")
        return
    # Inform user with Skyroom convention
    try:
        # Fetch user's name for username
        with session_scope() as session:
            u = session.execute(select(DBUser).where(DBUser.id == p.user_id)).scalar_one_or_none()
        full_name = (
            " ".join(filter(None, [getattr(u, 'first_name', ''), getattr(u, 'last_name', '')]))
            or "کاربر"
        )
        await context.bot.send_message(
            chat_id=int(getattr(u, 'telegram_user_id', 0)),
            text=(
                "✅ ثبت‌نام شما تأیید شد.\n"
                f"👤 نام کاربری اسکای‌روم: {full_name}\n"
                f"🔑 رمز عبور اسکای‌روم: {int(getattr(u, 'telegram_user_id', 0))}\n"
                "ℹ️ در صورت نیاز، رمز را می‌توانید بعداً تغییر دهید."
            ),
        )
    except Exception:
        pass
    await update.effective_message.reply_text("✅ تأیید شد و به کاربر اطلاع داده شد.")


async def admin_reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from config import config as app_config

    if update.effective_user.id not in app_config.bot.admin_user_ids:
        return
    if not context.args:
        await update.effective_message.reply_text("فرمت: /reject <purchase_id>")
        return
    try:
        pid = int(context.args[0])
    except Exception:
        await update.effective_message.reply_text("شناسه نامعتبر است.")
        return
    with session_scope() as session:
        p = approve_or_reject_purchase(session, pid, update.effective_user.id, "reject")
    if not p:
        await update.effective_message.reply_text("عدم موفقیت در رد (شاید قبلاً رسیدگی شده).")
        return
    await update.effective_message.reply_text("⛔️ رد شد.")


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
