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
    
    # Iranian provinces and cities (simplified for demo)
    PROVINCES = {
        "تهران": ["تهران", "شهریار", "ورامین", "فیروزکوه"],
        "اصفهان": ["اصفهان", "کاشان", "نجف‌آباد", "خمینی‌شهر"],
        "خراسان رضوی": ["مشهد", "نیشابور", "سبزوار", "تربت حیدریه"],
        "فارس": ["شیراز", "مرودشت", "جهرم", "کازرون"],
        "آذربایجان شرقی": ["تبریز", "مراغه", "میانه", "اهر"],
        "مازندران": ["ساری", "بابل", "آمل", "قائم‌شهر"],
        "گیلان": ["رشت", "لاهیجان", "انزلی", "آستارا"],
        "خوزستان": ["اهواز", "دزفول", "ماهشهر", "ایذه"],
        "بوشهر": ["بوشهر", "برازجان", "گناوه", "کنگان"],
        "سایر": ["سایر شهرها"]
    }

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
        for province in Keyboards.PROVINCES.keys():
            builder.button(text=f"🏛️ {province}", callback_data=f"province:{province}")
        builder.adjust(2)
        return builder.as_markup()

    @staticmethod
    def get_city_keyboard(province: str) -> InlineKeyboardMarkup:
        """Get city selection keyboard for a province"""
        builder = InlineKeyboardBuilder()
        cities = Keyboards.PROVINCES.get(province, [])
        for city in cities:
            builder.button(text=f"🏙️ {city}", callback_data=f"city:{city}")
        builder.adjust(2)
        return builder.as_markup()

    @staticmethod
    def get_phone_keyboard() -> ReplyKeyboardMarkup:
        """Get phone number keyboard"""
        keyboard = [
            [KeyboardButton(text="📱 ارسال شماره تلفن", request_contact=True)]
        ]
        return ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True,
            one_time_keyboard=True,
            input_field_placeholder="شماره تلفن خود را وارد کنید"
        )

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
        builder.button(text="📱 تلفن", callback_data="edit_phone")
        builder.button(text="🔙 بازگشت", callback_data="back_to_confirmation")
        builder.adjust(2)
        return builder.as_markup()

    @staticmethod
    def get_main_menu_keyboard() -> InlineKeyboardMarkup:
        """Get main menu keyboard with improved design"""
        builder = InlineKeyboardBuilder()
        
        # Main features
        builder.button(text="🎓 دوره‌های رایگان", callback_data="free_courses")
        builder.button(text="💎 دوره‌های تخصصی", callback_data="paid_courses")
        builder.button(text="📚 دوره‌های خریداری شده", callback_data="purchased_courses")
        
        # Book and social
        builder.button(text="📖 کتاب انفجار خلاقیت", callback_data="buy_book")
        builder.button(text="📱 فضای مجازی", callback_data="social_media")
        builder.button(text="📞 ارتباط با ما", callback_data="contact_us")
        
        # Profile management
        builder.button(text="👤 ویرایش پروفایل", callback_data="edit_profile")
        
        builder.adjust(2, 2, 1, 1)
        return builder.as_markup()

    @staticmethod
    def get_course_keyboard(course_id: str, course_type: str) -> InlineKeyboardMarkup:
        """Get course action keyboard"""
        builder = InlineKeyboardBuilder()
        
        if course_type == "free":
            builder.button(
                text="✅ ثبت‌نام در دوره", 
                callback_data=f"enroll_course:{course_id}"
            )
        else:
            builder.button(
                text="💳 خرید دوره", 
                callback_data=f"purchase_course:{course_id}"
            )
        
        builder.button(text="🔙 بازگشت", callback_data="back_to_main")
        builder.adjust(1, 1)
        return builder.as_markup()

    @staticmethod
    def get_payment_keyboard(purchase_id: str) -> InlineKeyboardMarkup:
        """Get payment keyboard"""
        builder = InlineKeyboardBuilder()
        builder.button(
            text="📸 ارسال فیش واریزی", 
            callback_data=f"send_receipt:{purchase_id}"
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
