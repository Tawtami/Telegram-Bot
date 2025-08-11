#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, List

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackQueryHandler

from config import config
from database.db import session_scope
from database.models_sql import User as DBUser
from database.service import get_or_create_user, audit_profile_change


def _kb(rows: List[List[InlineKeyboardButton]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(rows)


async def start_profile_edit(update: Update, context: Any) -> None:
    query = update.callback_query
    if not query:
        return
    await query.answer()
    rows = [
        [InlineKeyboardButton("📍 استان", callback_data="profile_edit:province")],
        [InlineKeyboardButton("🏙 شهر", callback_data="profile_edit:city")],
        [InlineKeyboardButton("📚 پایه تحصیلی", callback_data="profile_edit:grade")],
        [InlineKeyboardButton("🎓 رشته تحصیلی", callback_data="profile_edit:major")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_menu")],
    ]
    await query.edit_message_text("کدام مورد را می‌خواهید ویرایش کنید؟", reply_markup=_kb(rows))


async def edit_province(update: Update, context: Any) -> None:
    query = update.callback_query
    if not query:
        return
    await query.answer()
    # Show provinces with edit-specific callback
    rows = [
        [InlineKeyboardButton(p, callback_data=f"set_province:{p}")]
        for p in config.provinces
    ]
    rows.append([InlineKeyboardButton("🔙 بازگشت", callback_data="menu_profile_edit")])
    await query.edit_message_text("استان خود را انتخاب کنید:", reply_markup=_kb(rows))


async def set_province(update: Update, context: Any) -> None:
    query = update.callback_query
    if not query:
        return
    await query.answer()
    province = query.data.split(":", 1)[1]
    user_id = update.effective_user.id
    with session_scope() as session:
        db_user = (
            session.query(DBUser)
            .filter(DBUser.telegram_user_id == user_id)
            .one_or_none()
        )
        if db_user:
            audit_profile_change(
                session,
                user_id=db_user.id,
                field_name="province",
                old_value=None,
                new_value=province,
                changed_by=user_id,
            )
        get_or_create_user(session, user_id, province=province, city="")
    # Prompt city next
    cities = config.cities_by_province.get(province, [])
    rows = [
        [InlineKeyboardButton(c, callback_data=f"set_city:{c}")]
        for c in cities
    ]
    rows.append([InlineKeyboardButton("🔙 بازگشت", callback_data="menu_profile_edit")])
    await query.edit_message_text(
        f"استان {province} ثبت شد. اکنون شهر خود را انتخاب کنید:",
        reply_markup=_kb(rows),
    )


async def edit_city(update: Update, context: Any) -> None:
    query = update.callback_query
    if not query:
        return
    await query.answer()
    # Determine user's province
    user_id = update.effective_user.id
    with session_scope() as session:
        db_user = (
            session.query(DBUser)
            .filter(DBUser.telegram_user_id == user_id)
            .one_or_none()
        )
    province = db_user.province if db_user else None
    if not province:
        await query.edit_message_text(
            "ابتدا استان را تنظیم کنید.", reply_markup=_kb([[InlineKeyboardButton("🔙 بازگشت", callback_data="menu_profile_edit")]])
        )
        return
    cities = config.cities_by_province.get(province, [])
    rows = [
        [InlineKeyboardButton(c, callback_data=f"set_city:{c}")]
        for c in cities
    ]
    rows.append([InlineKeyboardButton("🔙 بازگشت", callback_data="menu_profile_edit")])
    await query.edit_message_text("شهر خود را انتخاب کنید:", reply_markup=_kb(rows))


async def set_city(update: Update, context: Any) -> None:
    query = update.callback_query
    if not query:
        return
    await query.answer()
    city = query.data.split(":", 1)[1]
    user_id = update.effective_user.id
    with session_scope() as session:
        db_user = (
            session.query(DBUser)
            .filter(DBUser.telegram_user_id == user_id)
            .one_or_none()
        )
        if db_user:
            audit_profile_change(
                session,
                user_id=db_user.id,
                field_name="city",
                old_value=None,
                new_value=city,
                changed_by=user_id,
            )
        get_or_create_user(session, user_id, city=city)
    await query.edit_message_text(
        f"🏙 شهر {city} ثبت شد.",
        reply_markup=_kb([[InlineKeyboardButton("🔙 بازگشت", callback_data="menu_profile_edit")]]),
    )


async def edit_grade(update: Update, context: Any) -> None:
    query = update.callback_query
    if not query:
        return
    await query.answer()
    rows = [
        [InlineKeyboardButton(g, callback_data=f"set_grade:{g}")]
        for g in config.grades
    ]
    rows.append([InlineKeyboardButton("🔙 بازگشت", callback_data="menu_profile_edit")])
    await query.edit_message_text("پایه تحصیلی را انتخاب کنید:", reply_markup=_kb(rows))


async def set_grade(update: Update, context: Any) -> None:
    query = update.callback_query
    if not query:
        return
    await query.answer()
    grade = query.data.split(":", 1)[1]
    user_id = update.effective_user.id
    with session_scope() as session:
        db_user = (
            session.query(DBUser)
            .filter(DBUser.telegram_user_id == user_id)
            .one_or_none()
        )
        if db_user:
            audit_profile_change(
                session,
                user_id=db_user.id,
                field_name="grade",
                old_value=None,
                new_value=grade,
                changed_by=user_id,
            )
        get_or_create_user(session, user_id, grade=grade)
    await query.edit_message_text(
        f"📚 پایه {grade} ثبت شد.",
        reply_markup=_kb([[InlineKeyboardButton("🔙 بازگشت", callback_data="menu_profile_edit")]]),
    )


async def edit_major(update: Update, context: Any) -> None:
    query = update.callback_query
    if not query:
        return
    await query.answer()
    rows = [
        [InlineKeyboardButton(m, callback_data=f"set_major:{m}")]
        for m in config.majors
    ]
    rows.append([InlineKeyboardButton("🔙 بازگشت", callback_data="menu_profile_edit")])
    await query.edit_message_text("رشته تحصیلی را انتخاب کنید:", reply_markup=_kb(rows))


async def set_major(update: Update, context: Any) -> None:
    query = update.callback_query
    if not query:
        return
    await query.answer()
    major = query.data.split(":", 1)[1]
    user_id = update.effective_user.id
    with session_scope() as session:
        db_user = (
            session.query(DBUser)
            .filter(DBUser.telegram_user_id == user_id)
            .one_or_none()
        )
        if db_user:
            audit_profile_change(
                session,
                user_id=db_user.id,
                field_name="field",
                old_value=None,
                new_value=major,
                changed_by=user_id,
            )
        get_or_create_user(session, user_id, field_of_study=major)
    await query.edit_message_text(
        f"🎓 رشته {major} ثبت شد.",
        reply_markup=_kb([[InlineKeyboardButton("🔙 بازگشت", callback_data="menu_profile_edit")]]),
    )


def build_profile_edit_handlers() -> list:
    return [
        CallbackQueryHandler(start_profile_edit, pattern=r"^menu_profile_edit$"),
        CallbackQueryHandler(edit_province, pattern=r"^profile_edit:province$"),
        CallbackQueryHandler(edit_city, pattern=r"^profile_edit:city$"),
        CallbackQueryHandler(edit_grade, pattern=r"^profile_edit:grade$"),
        CallbackQueryHandler(edit_major, pattern=r"^profile_edit:major$"),
        CallbackQueryHandler(set_province, pattern=r"^set_province:"),
        CallbackQueryHandler(set_city, pattern=r"^set_city:"),
        CallbackQueryHandler(set_grade, pattern=r"^set_grade:"),
        CallbackQueryHandler(set_major, pattern=r"^set_major:"),
    ]


