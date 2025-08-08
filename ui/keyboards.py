#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Keyboard layouts for Telegram Bot (PTB-based)
"""

from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List


def build_register_keyboard() -> InlineKeyboardMarkup:
    """Get registration keyboard"""
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("📝 ثبت‌نام", callback_data="start_registration")]]
    )


def build_back_keyboard(callback_data: str = "back_to_main") -> InlineKeyboardMarkup:
    """Get back button keyboard"""
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("🔙 بازگشت", callback_data=callback_data)]]
    )


def build_grades_keyboard(grades: List[str]) -> InlineKeyboardMarkup:
    """Get grade selection keyboard"""
    rows = [
        [InlineKeyboardButton(f"🎓 {g}", callback_data=f"grade:{g}")] for g in grades
    ]
    rows.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_city")])
    return InlineKeyboardMarkup(rows)


def build_majors_keyboard(majors: List[str]) -> InlineKeyboardMarkup:
    """Get major selection keyboard"""
    rows = [
        [InlineKeyboardButton(f"📚 {m}", callback_data=f"major:{m}")] for m in majors
    ]
    rows.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_grade")])
    return InlineKeyboardMarkup(rows)


def build_provinces_keyboard(provinces: List[str]) -> InlineKeyboardMarkup:
    """Get province selection keyboard"""
    rows = [
        [InlineKeyboardButton(f"🏛️ {p}", callback_data=f"province:{p}")]
        for p in provinces
    ]
    # In registration flow, going back from province step returns to start/cancel
    rows.append([InlineKeyboardButton("🔙 بازگشت", callback_data="cancel_reg")])
    return InlineKeyboardMarkup(rows)


def build_cities_keyboard(cities: List[str]) -> InlineKeyboardMarkup:
    """Get city selection keyboard for a province"""
    rows = [[InlineKeyboardButton(f"🏙️ {c}", callback_data=f"city:{c}")] for c in cities]
    rows.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_province")])
    return InlineKeyboardMarkup(rows)


def build_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Get main menu keyboard"""
    rows = [
        [InlineKeyboardButton(text="🎓 دوره‌های رایگان", callback_data="free_courses")],
        [InlineKeyboardButton(text="💼 دوره‌های تخصصی", callback_data="paid_courses")],
        [
            InlineKeyboardButton(
                text="🛒 دوره‌های خریداری‌شده", callback_data="purchased_courses"
            )
        ],
        [InlineKeyboardButton(text="📖 کتاب انفجار خلاقیت", callback_data="book_info")],
        [InlineKeyboardButton(text="🌐 شبکه‌های اجتماعی", callback_data="social_media")],
        [InlineKeyboardButton(text="☎️ ارتباط با ما", callback_data="contact_us")],
        [InlineKeyboardButton(text="👤 پروفایل من", callback_data="profile")],
    ]
    return InlineKeyboardMarkup(rows)


def build_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Get confirmation keyboard"""
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("✅ تایید", callback_data="confirm_reg")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="cancel_reg")],
        ]
    )
