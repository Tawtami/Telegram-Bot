#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Keyboard layouts for Ostad Hatami Bot
"""

from typing import Dict, List
from aiogram.types import (
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder


class Keyboards:
    """Keyboard layouts for the bot"""

    # Educational data
    GRADES = ["دهم", "یازدهم", "دوازدهم"]
    MAJORS = ["ریاضی", "تجربی", "انسانی"]

    # Import from config
    @staticmethod
    def get_provinces():
        from config import Config

        config = Config()
        return config.provinces

    @staticmethod
    def get_cities_by_province():
        from config import Config

        config = Config()
        return config.cities_by_province

    @staticmethod
    def get_grade_keyboard() -> InlineKeyboardMarkup:
        """Get grade selection keyboard"""
        builder = InlineKeyboardBuilder()
        for grade in Keyboards.GRADES:
            builder.button(text=f"🎓 {grade}", callback_data=f"grade:{grade}")
        builder.adjust(3)
        return builder.as_markup()

    @staticmethod
    def get_major_keyboard() -> InlineKeyboardMarkup:
        """Get major selection keyboard"""
        builder = InlineKeyboardBuilder()
        for major in Keyboards.MAJORS:
            builder.button(text=f"📚 {major}", callback_data=f"major:{major}")
        builder.adjust(3)
        return builder.as_markup()

    @staticmethod
    def get_province_keyboard() -> InlineKeyboardMarkup:
        """Get province selection keyboard"""
        builder = InlineKeyboardBuilder()
        provinces = Keyboards.get_provinces()
        for province in provinces:
            builder.button(text=f"🏛️ {province}", callback_data=f"province:{province}")
        builder.adjust(2)
        return builder.as_markup()

    @staticmethod
    def get_city_keyboard(province: str) -> InlineKeyboardMarkup:
        """Get city selection keyboard for a province"""
        builder = InlineKeyboardBuilder()
        cities_by_province = Keyboards.get_cities_by_province()
        cities = cities_by_province.get(province, [])
        for city in cities:
            builder.button(text=f"🏙️ {city}", callback_data=f"city:{city}")

        # Add back button
        builder.button(text="🔙 بازگشت", callback_data="back_to_province")
        builder.adjust(2)
        return builder.as_markup()

    @staticmethod
    def get_confirmation_keyboard() -> InlineKeyboardMarkup:
        """Get confirmation keyboard"""
        builder = InlineKeyboardBuilder()
        builder.button(text="✅ تایید اطلاعات", callback_data="confirm_registration")
        builder.button(text="✏️ ویرایش", callback_data="edit_registration")
        builder.adjust(2)
        return builder.as_markup()

    @staticmethod
    def get_edit_keyboard() -> InlineKeyboardMarkup:
        """Get edit profile keyboard"""
        builder = InlineKeyboardBuilder()
        builder.button(text="📝 نام", callback_data="edit_first_name")
        builder.button(text="📝 نام خانوادگی", callback_data="edit_last_name")
        builder.button(text="🎓 مقطع", callback_data="edit_grade")
        builder.button(text="📚 رشته", callback_data="edit_major")
        builder.button(text="🏛️ استان", callback_data="edit_province")
        builder.button(text="🏙️ شهر", callback_data="edit_city")

        builder.button(text="🔙 بازگشت", callback_data="back_to_confirmation")
        builder.adjust(2)
        return builder.as_markup()

    @staticmethod
    def get_main_menu_keyboard() -> InlineKeyboardMarkup:
        """Get main menu keyboard matching specification exactly"""
        builder = InlineKeyboardBuilder()

        # Main menu options as per specification
        builder.button(text="🎓 دوره‌های رایگان", callback_data="free_courses")
        builder.button(text="💎 دوره‌های تخصصی (پولی)", callback_data="paid_courses")
        builder.button(text="📚 دوره‌های خریداری شده", callback_data="purchased_courses")
        builder.button(text="📖 کتاب انفجار خلاقیت", callback_data="book_info")
        builder.button(text="📱 شبکه‌های اجتماعی", callback_data="social_media")
        builder.button(text="📞 ارتباط با ما", callback_data="contact_us")

        builder.adjust(1, 1, 1, 1, 1, 1)  # Each button on its own row for clarity
        return builder.as_markup()

    @staticmethod
    def get_free_course_register_keyboard() -> InlineKeyboardMarkup:
        """Get free course registration keyboard"""
        builder = InlineKeyboardBuilder()
        builder.button(
            text="✅ ثبت‌نام در دوره رایگان", callback_data="register_free_course"
        )
        builder.button(text="🔙 بازگشت", callback_data="back_to_main")
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def get_paid_courses_keyboard() -> InlineKeyboardMarkup:
        """Get paid courses selection keyboard"""
        builder = InlineKeyboardBuilder()
        builder.button(
            text="🔥 دوره فشرده ریاضی", callback_data="course:intensive_math"
        )
        builder.button(
            text="⚡ دوره تست‌زنی پیشرفته", callback_data="course:advanced_test"
        )
        builder.button(
            text="🎯 حل تست‌های دشوار", callback_data="course:difficult_tests"
        )
        builder.button(text="🔙 بازگشت", callback_data="back_to_main")
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def get_book_purchase_keyboard() -> InlineKeyboardMarkup:
        """Get book purchase keyboard"""
        builder = InlineKeyboardBuilder()
        builder.button(text="🛒 خرید کتاب", callback_data="buy_book")
        builder.button(text="🔙 بازگشت", callback_data="back_to_main")
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def get_social_media_keyboard() -> InlineKeyboardMarkup:
        """Get social media links keyboard"""
        builder = InlineKeyboardBuilder()
        builder.button(
            text="📸 اینستاگرام", url="https://instagram.com/ostadhatami_official"
        )
        builder.button(text="🎬 یوتوب", url="https://youtube.com/@ostadhatami")
        builder.button(text="📢 کانال تلگرام", url="https://t.me/OstadHatamiChannel")
        builder.button(text="👥 گروه تلگرام", url="https://t.me/OstadHatamiGroup")
        builder.button(text="💬 پشتیبانی", url="https://t.me/Ostad_Hatami")
        builder.button(text="🔙 بازگشت", callback_data="back_to_main")
        builder.adjust(2, 2, 1, 1)
        return builder.as_markup()

    @staticmethod
    def get_contact_keyboard() -> InlineKeyboardMarkup:
        """Get contact information keyboard"""
        builder = InlineKeyboardBuilder()
        builder.button(text="💬 تلگرام", url="https://t.me/Ostad_Hatami")
        builder.button(text="🌐 وبسایت", url="https://ostadhatami.ir")
        builder.button(text="🔙 بازگشت", callback_data="back_to_main")
        builder.adjust(2, 1)
        return builder.as_markup()

    @staticmethod
    def get_course_keyboard(course_id: str, course_type: str) -> InlineKeyboardMarkup:
        """Get course action keyboard"""
        builder = InlineKeyboardBuilder()

        if course_type == "free":
            builder.button(
                text="✅ ثبت‌نام در دوره", callback_data=f"enroll_course:{course_id}"
            )
        else:
            builder.button(
                text="💳 خرید دوره", callback_data=f"purchase_course:{course_id}"
            )

        builder.button(text="🔙 بازگشت", callback_data="back_to_main")
        builder.adjust(1, 1)
        return builder.as_markup()

    @staticmethod
    def get_payment_keyboard(purchase_id: str) -> InlineKeyboardMarkup:
        """Get payment keyboard"""
        builder = InlineKeyboardBuilder()
        builder.button(
            text="📸 ارسال فیش واریزی", callback_data=f"send_receipt:{purchase_id}"
        )
        builder.button(text="🔙 بازگشت", callback_data="back_to_main")
        builder.adjust(1, 1)
        return builder.as_markup()

    @staticmethod
    def get_book_purchase_keyboard() -> InlineKeyboardMarkup:
        """Get book purchase keyboard"""
        builder = InlineKeyboardBuilder()
        builder.button(text="📖 خرید کتاب", callback_data="purchase_book")
        builder.button(text="🔙 بازگشت", callback_data="back_to_main")
        builder.adjust(1, 1)
        return builder.as_markup()

    @staticmethod
    def get_social_media_keyboard() -> InlineKeyboardMarkup:
        """Get social media keyboard"""
        builder = InlineKeyboardBuilder()
        builder.button(text="📸 اینستاگرام", url="https://instagram.com/ostad_hatami")
        builder.button(text="📺 یوتیوب", url="https://youtube.com/@ostad_hatami")
        builder.button(text="👥 گروه تلگرام", url="https://t.me/ostad_hatami_group")
        builder.button(text="📢 کانال تلگرام", url="https://t.me/ostad_hatami_channel")
        builder.button(text="🔙 بازگشت", callback_data="back_to_main")
        builder.adjust(2, 2, 1)
        return builder.as_markup()

    @staticmethod
    def get_back_keyboard() -> InlineKeyboardMarkup:
        """Get back button keyboard"""
        builder = InlineKeyboardBuilder()
        builder.button(text="🔙 بازگشت", callback_data="back_to_main")
        return builder.as_markup()

    @staticmethod
    def get_cancel_keyboard() -> InlineKeyboardMarkup:
        """Get cancel button keyboard"""
        builder = InlineKeyboardBuilder()
        builder.button(text="❌ انصراف", callback_data="cancel_operation")
        return builder.as_markup()
