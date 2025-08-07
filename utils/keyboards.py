#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from typing import List, Dict


def build_register_keyboard() -> InlineKeyboardMarkup:
    kb = [[InlineKeyboardButton(text="📝 ثبت‌نام", callback_data="start_registration")]]
    return InlineKeyboardMarkup(kb)


def build_back_keyboard(callback_data: str = "back_to_main") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton(text="🔙 بازگشت", callback_data=callback_data)]])


def build_grades_keyboard(grades: List[str]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(f"🎓 {g}", callback_data=f"grade:{g}")] for g in grades]
    rows.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_city")])
    return InlineKeyboardMarkup(rows)


def build_majors_keyboard(majors: List[str]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(f"📚 {m}", callback_data=f"major:{m}")] for m in majors]
    rows.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_grade")])
    return InlineKeyboardMarkup(rows)


def build_provinces_keyboard(provinces: List[str]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(f"🏛️ {p}", callback_data=f"province:{p}")] for p in provinces]
    rows.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_major")])
    return InlineKeyboardMarkup(rows)


def build_cities_keyboard(cities: List[str]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(f"🏙️ {c}", callback_data=f"city:{c}")] for c in cities]
    rows.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_province")])
    return InlineKeyboardMarkup(rows)


def build_main_menu_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="📚 دوره‌های رایگان", callback_data="free_courses")],
        [InlineKeyboardButton(text="💼 دوره‌های پولی", callback_data="paid_courses")],
        [InlineKeyboardButton(text="🛒 دوره‌های خریداری‌شده", callback_data="purchased_courses")],
        [InlineKeyboardButton(text="📖 کتاب انفجار خلاقیت", callback_data="book_info")],
        [InlineKeyboardButton(text="🌐 شبکه‌های اجتماعی", callback_data="social_media")],
        [InlineKeyboardButton(text="☎️ ارتباط با ما", callback_data="contact_us")],
        [InlineKeyboardButton(text="👤 پروفایل من", callback_data="profile")],
    ]
    return InlineKeyboardMarkup(rows)
