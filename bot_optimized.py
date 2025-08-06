#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ostad Hatami Math Classes Registration Bot - Optimized Version
ربات ثبت‌نام کلاس‌های ریاضی استاد حاتمی - نسخه بهینه‌شده
"""

import json
import logging
import os
import re
import asyncio
import time
import gzip
import pickle
import statistics
from collections import defaultdict, OrderedDict
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Set, List, Tuple
from pathlib import Path
from functools import wraps
from dataclasses import dataclass, asdict
from enum import Enum
import html
import hashlib
import hmac
import base64
import secrets
from traceback import format_exc

from aiogram import Bot, Dispatcher, types, Router
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)
from aiogram.filters import Command, StateFilter
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import optimized modules
from config import Config
from database import DataManager
from utils import (
    Validator,
    SimpleCache,
    RateLimiter,
    PerformanceMonitor,
    BotErrorHandler,
    SecurityUtils,
)

# Configure advanced logging
logging.basicConfig(
    level=getattr(logging, Config.logging.level),
    format="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
    handlers=[
        (
            logging.FileHandler("bot.log", encoding="utf-8")
            if Config.logging.file_enabled
            else logging.NullHandler()
        ),
        (
            logging.StreamHandler()
            if Config.logging.console_enabled
            else logging.NullHandler()
        ),
    ],
)
logger = logging.getLogger(__name__)

# Performance logger
if Config.logging.performance_log_enabled:
    perf_logger = logging.getLogger("performance")
    perf_handler = logging.FileHandler("performance.log", encoding="utf-8")
    perf_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
    perf_logger.addHandler(perf_handler)
    perf_logger.setLevel(logging.INFO)

# Bot token from environment
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")

# Initialize optimized components
config = Config()
data_manager = DataManager()
cache_manager = SimpleCache(ttl_seconds=config.performance.cache_ttl_seconds)
rate_limiter = RateLimiter(
    max_requests=config.performance.max_requests_per_minute, window_seconds=60
)
monitor = PerformanceMonitor()
error_handler = BotErrorHandler()
security_utils = SecurityUtils()

# Initialize bot and dispatcher with optimizations
bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()


# ============================================================================
# FSM STATES
# ============================================================================
class RegistrationStates(StatesGroup):
    """Registration process states"""

    waiting_for_first_name = State()
    waiting_for_last_name = State()
    waiting_for_grade = State()
    waiting_for_major = State()
    waiting_for_province = State()
    waiting_for_city = State()
    waiting_for_phone = State()
    confirmation = State()
    editing = State()


# ============================================================================
# DECORATORS
# ============================================================================
def performance_monitor(func):
    """Decorator to monitor function performance"""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            monitor.log_request_time(func.__name__, duration)
            return result
        except Exception as e:
            monitor.log_error(type(e).__name__)
            logger.error(f"Error in {func.__name__}: {e}")
            raise

    return wrapper


def rate_limit(func):
    """Decorator to apply rate limiting"""

    @wraps(func)
    async def wrapper(message_or_callback, *args, **kwargs):
        user_id = None
        if hasattr(message_or_callback, "from_user"):
            user_id = message_or_callback.from_user.id
        elif hasattr(message_or_callback, "message") and hasattr(
            message_or_callback.message, "from_user"
        ):
            user_id = message_or_callback.message.from_user.id

        if user_id and not rate_limiter.is_allowed(user_id):
            if hasattr(message_or_callback, "answer"):
                await message_or_callback.answer(
                    "⚠️ لطفاً کمی صبر کنید و دوباره تلاش کنید.", show_alert=True
                )
            return

        if user_id:
            monitor.log_user_activity(user_id)

        return await func(message_or_callback, *args, **kwargs)

    return wrapper


def maintenance_mode(func):
    """Decorator to check maintenance mode"""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        if config.bot.maintenance_mode:
            message_or_callback = args[0] if args else None
            if hasattr(message_or_callback, "answer"):
                await message_or_callback.answer(
                    "🔧 ربات در حال تعمیر و نگهداری است. لطفاً کمی صبر کنید.",
                    show_alert=True,
                )
            return
        return await func(*args, **kwargs)

    return wrapper


# ============================================================================
# KEYBOARDS
# ============================================================================
class Keyboards:
    """Keyboard builders"""

    @staticmethod
    def get_grade_keyboard() -> InlineKeyboardMarkup:
        """Build grade selection keyboard"""
        builder = InlineKeyboardBuilder()
        for grade in config.educational.grades:
            builder.button(text=grade, callback_data=f"grade:{grade}")
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def get_major_keyboard() -> InlineKeyboardMarkup:
        """Build major selection keyboard"""
        builder = InlineKeyboardBuilder()
        for major in config.educational.majors:
            builder.button(text=major, callback_data=f"major:{major}")
        builder.adjust(2)
        return builder.as_markup()

    @staticmethod
    def get_province_keyboard() -> InlineKeyboardMarkup:
        """Build province selection keyboard"""
        builder = InlineKeyboardBuilder()
        for province in config.educational.provinces:
            builder.button(text=province, callback_data=f"province:{province}")
        builder.adjust(2)
        return builder.as_markup()

    @staticmethod
    def get_city_keyboard(province: str) -> InlineKeyboardMarkup:
        """Build city selection keyboard for a province"""
        builder = InlineKeyboardBuilder()
        cities = config.educational.cities_by_province.get(province, ["سایر"])
        for city in cities:
            builder.button(text=city, callback_data=f"city:{city}")
        builder.adjust(2)
        return builder.as_markup()

    @staticmethod
    def get_phone_keyboard() -> ReplyKeyboardMarkup:
        """Build phone number input keyboard"""
        keyboard = [
            [KeyboardButton(text="📱 ارسال شماره تلفن", request_contact=True)],
            [KeyboardButton(text="✏️ ورود دستی شماره")],
        ]
        return ReplyKeyboardMarkup(
            keyboard=keyboard, resize_keyboard=True, one_time_keyboard=True
        )

    @staticmethod
    def get_confirmation_keyboard() -> InlineKeyboardMarkup:
        """Build confirmation keyboard"""
        builder = InlineKeyboardBuilder()
        builder.button(text="تایید نهایی ✅", callback_data="confirm_registration")
        builder.button(text="ویرایش اطلاعات ✏️", callback_data="edit_registration")
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def get_edit_keyboard() -> InlineKeyboardMarkup:
        """Build edit fields keyboard"""
        builder = InlineKeyboardBuilder()
        fields = [
            ("نام", "edit_first_name"),
            ("نام خانوادگی", "edit_last_name"),
            ("پایه تحصیلی", "edit_grade"),
            ("رشته تحصیلی", "edit_major"),
            ("استان", "edit_province"),
            ("شهر", "edit_city"),
            ("شماره تلفن", "edit_phone"),
        ]

        for field_name, callback_data in fields:
            builder.button(text=field_name, callback_data=callback_data)

        builder.button(text="🔙 بازگشت", callback_data="back_to_confirmation")
        builder.adjust(2)
        return builder.as_markup()

    @staticmethod
    def get_main_menu_keyboard() -> InlineKeyboardMarkup:
        """Build main menu keyboard"""
        builder = InlineKeyboardBuilder()
        builder.button(
            text="🗓 مشاهده کلاس‌های قابل ثبت‌نام", callback_data="view_classes"
        )
        builder.button(text="📘 تهیه کتاب انفجار خلاقیت", callback_data="buy_book")
        builder.button(
            text="🧑‍🏫 ارتباط با استاد حاتمی", callback_data="contact_teacher"
        )
        builder.button(text="⚙️ ویرایش اطلاعات", callback_data="edit_profile")
        builder.adjust(1)
        return builder.as_markup()


# ============================================================================
# MESSAGES
# ============================================================================
class Messages:
    """Message templates"""

    @staticmethod
    def get_welcome_message(first_name: str) -> str:
        """Get welcome message"""
        return f"""سلام {first_name} عزیز! 🌟

به ربات ثبت‌نام کلاس‌های رایگان استاد حاتمی خوش آمدید.

🎓 **کلاس‌های رایگان ریاضی در حال برگزاری است!**

برای استفاده از خدمات، لطفاً اطلاعات خود را وارد کنید.
دقت فرمایید اطلاعات به‌درستی وارد شود."""

    @staticmethod
    def get_registration_start() -> str:
        """Get registration start message"""
        return """🎓 **شروع ثبت‌نام**

لطفاً اطلاعات خود را به ترتیب وارد کنید.
هر مرحله را با دقت تکمیل نمایید."""

    @staticmethod
    def get_profile_summary(user_data: Dict[str, Any]) -> str:
        """Get profile summary message"""
        return f"""📝 **اطلاعات ثبت‌شده:**

👤 **نام:** {user_data.get('first_name', '')}
👤 **نام خانوادگی:** {user_data.get('last_name', '')}
🎓 **پایه:** {user_data.get('grade', '')}
📚 **رشته:** {user_data.get('major', '')}
📍 **شهر:** {user_data.get('city', '')}، {user_data.get('province', '')}
📞 **شماره:** {user_data.get('phone', '')}

لطفاً اطلاعات را بررسی کرده و تایید کنید."""

    @staticmethod
    def get_success_message() -> str:
        """Get success message"""
        return """✅ **ثبت‌نام شما با موفقیت انجام شد!**

🎉 تبریک! شما در سیستم ثبت‌نام کلاس‌های رایگان استاد حاتمی ثبت شدید.

📚 **مراحل بعدی:**
• منتظر اطلاع‌رسانی کلاس‌های جدید باشید
• لینک اسکای‌روم و اطلاعات ورود برای شما ارسال خواهد شد
• در گروه تلگرام کلاس عضو شوید

🔔 **نکات مهم:**
• کلاس‌ها کاملاً رایگان هستند
• در صورت عدم حضور، از لیست حذف خواهید شد
• سوالات خود را از طریق ربات مطرح کنید"""


# ============================================================================
# HANDLERS
# ============================================================================
@router.message(Command("start"))
@performance_monitor
@rate_limit
@maintenance_mode
async def cmd_start(message: types.Message, state: FSMContext):
    """Handle /start command with optimized performance"""
    try:
        user = message.from_user

        # Check if user exists with caching
        if await data_manager.user_exists(user.id):
            await show_main_menu(message)
            return

        await state.clear()
        welcome_text = Messages.get_welcome_message(user.first_name or "کاربر")
        await message.answer(welcome_text)

        await state.set_state(RegistrationStates.waiting_for_first_name)
        await message.answer(
            Messages.get_registration_start()
            + "\n\n🔹 **مرحله ۱:** نام خود را وارد نمایید"
        )

        logger.info(f"New user started registration: {user.id}")

    except Exception as e:
        await error_handler.handle_system_error(message, e, "cmd_start")


@router.message(StateFilter(RegistrationStates.waiting_for_first_name))
@performance_monitor
@rate_limit
@maintenance_mode
async def process_first_name(message: types.Message, state: FSMContext):
    """Process first name input with validation and error handling"""
    try:
        if not message.text:
            await error_handler.handle_user_error(message, "لطفاً نام خود را وارد کنید.")
            return

        first_name = message.text.strip()

        if not Validator.validate_name(first_name, config.security):
            await error_handler.handle_user_error(
                message,
                "نام وارد شده نامعتبر است. لطفاً نام صحیح وارد کنید (حداقل ۲ حرف).",
            )
            return

        await state.update_data(first_name=first_name)
        await state.set_state(RegistrationStates.waiting_for_last_name)
        await message.answer(
            "✅ نام ثبت شد.\n\n🔹 **مرحله ۲:** نام خانوادگی خود را وارد نمایید"
        )

        logger.info(f"User {message.from_user.id} entered first name")

    except Exception as e:
        await error_handler.handle_system_error(message, e, "process_first_name")


@router.message(StateFilter(RegistrationStates.waiting_for_last_name))
@performance_monitor
@rate_limit
@maintenance_mode
async def process_last_name(message: types.Message, state: FSMContext):
    """Process last name input with validation and error handling"""
    try:
        if not message.text:
            await error_handler.handle_user_error(
                message, "لطفاً نام خانوادگی خود را وارد کنید."
            )
            return

        last_name = message.text.strip()

        if not Validator.validate_name(last_name, config.security):
            await error_handler.handle_user_error(
                message,
                "نام خانوادگی وارد شده نامعتبر است. لطفاً نام خانوادگی صحیح وارد کنید.",
            )
            return

        await state.update_data(last_name=last_name)
        await state.set_state(RegistrationStates.waiting_for_grade)
        await message.answer(
            "✅ نام خانوادگی ثبت شد.\n\n🔹 **مرحله ۳:** پایه تحصیلی خود را مشخص نمایید",
            reply_markup=Keyboards.get_grade_keyboard(),
        )

        logger.info(f"User {message.from_user.id} entered last name")

    except Exception as e:
        await error_handler.handle_system_error(message, e, "process_last_name")


@router.callback_query(lambda c: c.data.startswith("grade:"))
@performance_monitor
@rate_limit
@maintenance_mode
async def process_grade(callback: types.CallbackQuery, state: FSMContext):
    """Process grade selection with error handling"""
    try:
        await callback.answer()

        if not callback.data or ":" not in callback.data:
            await error_handler.handle_user_error(callback, "داده نامعتبر دریافت شد.")
            return

        grade = callback.data.split(":")[1]
        if grade not in config.educational.grades:
            await error_handler.handle_user_error(
                callback, "پایه تحصیلی انتخاب شده نامعتبر است."
            )
            return

        await state.update_data(grade=grade)
        await state.set_state(RegistrationStates.waiting_for_major)

        await callback.message.edit_text(
            f"✅ پایه تحصیلی ثبت شد: {grade}\n\n🔹 **مرحله ۴:** رشته تحصیلی خود را انتخاب کنید",
            reply_markup=Keyboards.get_major_keyboard(),
        )

        logger.info(f"User {callback.from_user.id} selected grade: {grade}")

    except Exception as e:
        await error_handler.handle_system_error(callback, e, "process_grade")


@router.callback_query(lambda c: c.data.startswith("major:"))
@performance_monitor
@rate_limit
@maintenance_mode
async def process_major(callback: types.CallbackQuery, state: FSMContext):
    """Process major selection"""
    try:
        await callback.answer()
        major = callback.data.split(":")[1]
        await state.update_data(major=major)
        await state.set_state(RegistrationStates.waiting_for_province)

        await callback.message.edit_text(
            f"✅ رشته تحصیلی ثبت شد: {major}\n\n🔹 **مرحله ۵:** استان خود را انتخاب کنید",
            reply_markup=Keyboards.get_province_keyboard(),
        )
    except Exception as e:
        await error_handler.handle_system_error(callback, e, "process_major")


@router.callback_query(lambda c: c.data.startswith("province:"))
@performance_monitor
@rate_limit
@maintenance_mode
async def process_province(callback: types.CallbackQuery, state: FSMContext):
    """Process province selection"""
    try:
        await callback.answer()
        province = callback.data.split(":")[1]
        await state.update_data(province=province)
        await state.set_state(RegistrationStates.waiting_for_city)

        await callback.message.edit_text(
            f"✅ استان ثبت شد: {province}\n\n🔹 **مرحله ۶:** شهر خود را انتخاب کنید",
            reply_markup=Keyboards.get_city_keyboard(province),
        )
    except Exception as e:
        await error_handler.handle_system_error(callback, e, "process_province")


@router.callback_query(lambda c: c.data.startswith("city:"))
@performance_monitor
@rate_limit
@maintenance_mode
async def process_city(callback: types.CallbackQuery, state: FSMContext):
    """Process city selection"""
    try:
        await callback.answer()
        city = callback.data.split(":")[1]
        await state.update_data(city=city)
        await state.set_state(RegistrationStates.waiting_for_phone)

        await callback.message.edit_text(
            f"✅ شهر ثبت شد: {city}\n\n🔹 **مرحله ۷:** شماره تلفن همراه خود را وارد نمایید",
        )

        await callback.message.answer(
            "📱 لطفاً شماره تلفن خود را وارد کنید:",
            reply_markup=Keyboards.get_phone_keyboard(),
        )
    except Exception as e:
        await error_handler.handle_system_error(callback, e, "process_city")


@router.message(StateFilter(RegistrationStates.waiting_for_phone))
@performance_monitor
@rate_limit
@maintenance_mode
async def process_phone(message: types.Message, state: FSMContext):
    """Process phone number input with comprehensive validation"""
    try:
        phone = ""

        # Handle contact sharing
        if message.contact:
            phone = message.contact.phone_number
            logger.info(f"User {message.from_user.id} shared contact: {phone}")
        elif message.text:
            phone = message.text.strip()
        else:
            await error_handler.handle_user_error(
                message, "لطفاً شماره تلفن خود را وارد کنید."
            )
            return

        if not Validator.validate_phone(phone):
            await error_handler.handle_user_error(
                message,
                "شماره تلفن نامعتبر است. لطفاً شماره معتبر وارد کنید (مثال: 09121234567)",
            )
            return

        normalized_phone = Validator.normalize_phone(phone)
        await state.update_data(phone=normalized_phone)

        user_data = await state.get_data()
        user_data["user_id"] = message.from_user.id

        await state.set_state(RegistrationStates.confirmation)
        # Send confirmation message with keyboard removal
        await message.answer("📝 اطلاعات شما:", reply_markup=ReplyKeyboardRemove())

        await message.answer(
            Messages.get_profile_summary(user_data),
            reply_markup=Keyboards.get_confirmation_keyboard(),
        )

        logger.info(f"User {message.from_user.id} entered phone number")

    except Exception as e:
        await error_handler.handle_system_error(message, e, "process_phone")


@router.callback_query(lambda c: c.data == "confirm_registration")
@performance_monitor
@rate_limit
@maintenance_mode
async def confirm_registration(callback: types.CallbackQuery, state: FSMContext):
    """Confirm registration with comprehensive error handling"""
    try:
        await callback.answer()

        user_data = await state.get_data()
        if not user_data:
            await error_handler.handle_user_error(
                callback, "اطلاعات ثبت‌نام یافت نشد. لطفاً مجدداً ثبت‌نام کنید."
            )
            return

        user_data["user_id"] = callback.from_user.id

        # Validate all required fields
        required_fields = [
            "first_name",
            "last_name",
            "grade",
            "major",
            "province",
            "city",
            "phone",
        ]
        missing_fields = [
            field for field in required_fields if not user_data.get(field)
        ]

        if missing_fields:
            await error_handler.handle_user_error(
                callback,
                f"اطلاعات ناقص: {', '.join(missing_fields)}. لطفاً ویرایش کنید.",
            )
            return

        success = await data_manager.save_user_data(user_data)

        if success:
            await callback.message.edit_text(Messages.get_success_message())
            await show_main_menu_after_registration(callback.message)
            await state.clear()

            logger.info(
                f"User {callback.from_user.id} registration completed successfully"
            )
        else:
            await error_handler.handle_user_error(
                callback, "خطا در ثبت‌نام. لطفاً دوباره تلاش کنید."
            )

    except Exception as e:
        await error_handler.handle_system_error(callback, e, "confirm_registration")


@router.callback_query(lambda c: c.data == "edit_registration")
@maintenance_mode
async def edit_registration(callback: types.CallbackQuery, state: FSMContext):
    """Show edit options"""
    try:
        await callback.answer()
        await state.set_state(RegistrationStates.editing)
        await callback.message.edit_text(
            "✏️ **ویرایش اطلاعات**\n\nکدام فیلد را می‌خواهید ویرایش کنید؟",
            reply_markup=Keyboards.get_edit_keyboard(),
        )
    except Exception as e:
        await error_handler.handle_system_error(callback, e, "edit_registration")


@router.callback_query(lambda c: c.data.startswith("edit_"))
@maintenance_mode
async def handle_edit_field(callback: types.CallbackQuery, state: FSMContext):
    """Handle field editing"""
    try:
        await callback.answer()
        field = callback.data.split("_", 1)[1]

        if field == "first_name":
            await state.set_state(RegistrationStates.waiting_for_first_name)
            await callback.message.edit_text("🔹 نام جدید خود را وارد نمایید:")
        elif field == "last_name":
            await state.set_state(RegistrationStates.waiting_for_last_name)
            await callback.message.edit_text("🔹 نام خانوادگی جدید خود را وارد نمایید:")
        elif field == "grade":
            await state.set_state(RegistrationStates.waiting_for_grade)
            await callback.message.edit_text(
                "🔹 پایه تحصیلی جدید خود را انتخاب کنید:",
                reply_markup=Keyboards.get_grade_keyboard(),
            )
        elif field == "major":
            await state.set_state(RegistrationStates.waiting_for_major)
            await callback.message.edit_text(
                "🔹 رشته تحصیلی جدید خود را انتخاب کنید:",
                reply_markup=Keyboards.get_major_keyboard(),
            )
        elif field == "province":
            await state.set_state(RegistrationStates.waiting_for_province)
            await callback.message.edit_text(
                "🔹 استان جدید خود را انتخاب کنید:",
                reply_markup=Keyboards.get_province_keyboard(),
            )
        elif field == "city":
            user_data = await state.get_data()
            province = user_data.get("province", "تهران")
            await state.set_state(RegistrationStates.waiting_for_city)
            await callback.message.edit_text(
                "🔹 شهر جدید خود را انتخاب کنید:",
                reply_markup=Keyboards.get_city_keyboard(province),
            )
        elif field == "phone":
            await state.set_state(RegistrationStates.waiting_for_phone)
            await callback.message.edit_text(
                "🔹 شماره تلفن جدید خود را وارد نمایید:",
                reply_markup=Keyboards.get_phone_keyboard(),
            )
    except Exception as e:
        await error_handler.handle_system_error(callback, e, "handle_edit_field")


@router.callback_query(lambda c: c.data == "back_to_confirmation")
@maintenance_mode
async def back_to_confirmation(callback: types.CallbackQuery, state: FSMContext):
    """Go back to confirmation"""
    try:
        await callback.answer()
        user_data = await state.get_data()
        await state.set_state(RegistrationStates.confirmation)
        await callback.message.edit_text(
            Messages.get_profile_summary(user_data),
            reply_markup=Keyboards.get_confirmation_keyboard(),
        )
    except Exception as e:
        await error_handler.handle_system_error(callback, e, "back_to_confirmation")


# ============================================================================
# MAIN MENU HANDLERS
# ============================================================================
@performance_monitor
async def show_main_menu(message: types.Message):
    """Show main menu for registered users with error handling"""
    try:
        await message.answer(
            "🎓 **منوی اصلی ربات استاد حاتمی**\n\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=Keyboards.get_main_menu_keyboard(),
        )
        logger.info(f"Main menu shown to user {message.from_user.id}")
    except Exception as e:
        await error_handler.handle_system_error(message, e, "show_main_menu")


@performance_monitor
async def show_main_menu_after_registration(message: types.Message):
    """Show main menu after successful registration with error handling"""
    try:
        await message.answer(
            "🎓 **منوی اصلی ربات استاد حاتمی**\n\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=Keyboards.get_main_menu_keyboard(),
        )
        logger.info(f"Post-registration main menu shown to user {message.from_user.id}")
    except Exception as e:
        await error_handler.handle_system_error(
            message, e, "show_main_menu_after_registration"
        )


@router.callback_query(lambda c: c.data == "view_classes")
@maintenance_mode
async def view_classes(callback: types.CallbackQuery):
    """Show available classes"""
    try:
        await callback.answer()
        classes_text = """🗓 **کلاس‌های قابل ثبت‌نام:**

📚 **کلاس‌های ریاضی:**
• نظریه اعداد و ریاضی گسسته
• مهارت‌های حل خلاق مسائل ریاضی
• کلاس‌های پایه (دهم، یازدهم، دوازدهم)

⏰ **زمان کلاس‌ها:**
• جمعه‌ها ساعت ۱۵:۰۰
• مدت هر جلسه: ۹۰ دقیقه

🎯 **ویژگی‌ها:**
• کاملاً رایگان
• کلاس زنده در اسکای‌روم
• پشتیبانی ۲۴/۷
• محتوای تکمیلی

📝 **برای ثبت‌نام در کلاس‌ها، منتظر اطلاع‌رسانی باشید.**"""
        await callback.message.edit_text(classes_text)
    except Exception as e:
        await error_handler.handle_system_error(callback, e, "view_classes")


@router.callback_query(lambda c: c.data == "buy_book")
@maintenance_mode
async def buy_book(callback: types.CallbackQuery):
    """Show book information"""
    try:
        await callback.answer()
        book_text = """📘 **کتاب انفجار خلاقیت**

✍️ **نویسنده:** استاد حاتمی
📄 **تعداد صفحات:** ۴۰۰ صفحه
💰 **قیمت:** ۲۵۰,۰۰۰ تومان

✨ **ویژگی‌های کتاب:**
• مثال‌های حل شده
• تمرینات متنوع
• نمونه سوالات کنکور
• پاسخ تشریحی

📞 **برای سفارش کتاب:**
• تماس: ۰۹۱۲۳۴۵۶۷۸۹
• تلگرام: @Ostad_Hatami
• ایمیل: info@ostadhatami.ir"""
        await callback.message.edit_text(book_text)
    except Exception as e:
        await error_handler.handle_system_error(callback, e, "buy_book")


@router.callback_query(lambda c: c.data == "contact_teacher")
@maintenance_mode
async def contact_teacher(callback: types.CallbackQuery):
    """Show contact information"""
    try:
        await callback.answer()
        contact_text = """🧑‍🏫 **ارتباط با استاد حاتمی**

📞 **شماره تماس:** ۰۹۱۲۳۴۵۶۷۸۹
💬 **تلگرام:** @Ostad_Hatami
📧 **ایمیل:** info@ostadhatami.ir
🌐 **وب‌سایت:** www.ostadhatami.ir

⏰ **ساعات پاسخگویی:**
• شنبه تا چهارشنبه: ۹ صبح تا ۶ عصر
• جمعه: ۹ صبح تا ۲ عصر

💡 **نکات مهم:**
• سوالات درسی خود را مطرح کنید
• برای مشاوره تحصیلی تماس بگیرید
• درخواست کلاس خصوصی داشته باشید"""
        await callback.message.edit_text(contact_text)
    except Exception as e:
        await error_handler.handle_system_error(callback, e, "contact_teacher")


@router.callback_query(lambda c: c.data == "edit_profile")
@maintenance_mode
async def edit_profile(callback: types.CallbackQuery, state: FSMContext):
    """Edit user profile"""
    try:
        await callback.answer()
        user_data = await data_manager.load_user_data(callback.from_user.id)

        if not user_data:
            await callback.message.edit_text("❌ اطلاعات کاربری یافت نشد.")
            return

        await state.set_state(RegistrationStates.editing)
        await state.update_data(**user_data)
        await callback.message.edit_text(
            "✏️ **ویرایش اطلاعات**\n\nکدام فیلد را می‌خواهید ویرایش کنید؟",
            reply_markup=Keyboards.get_edit_keyboard(),
        )
    except Exception as e:
        await error_handler.handle_system_error(callback, e, "edit_profile")


@router.message(Command("stats"))
@maintenance_mode
async def view_stats(message: types.Message):
    """Admin command to view system statistics"""
    try:
        user_id = message.from_user.id

        # Check if user is admin
        if str(user_id) not in config.bot.admin_user_ids:
            await message.answer("❌ شما مجاز به استفاده از این دستور نیستید.")
            return

        # Get system statistics
        cache_stats = cache_manager.get_stats()
        rate_limit_stats = rate_limiter.get_stats()
        monitor_stats = monitor.get_stats()
        db_stats = await data_manager.get_database_stats()

        stats_text = f"""📊 **آمار سیستم:**

🗄️ **دیتابیس:**
• تعداد کاربران: {db_stats.get('total_users', 0)}
• حجم فایل‌ها: {db_stats.get('total_size_mb', 0):.2f} MB
• آخرین پشتیبان: {db_stats.get('last_backup', 'N/A')}

💾 **کش:**
• تعداد آیتم‌ها: {cache_stats.get('total_items', 0)}
• نرخ موفقیت: {cache_stats.get('hit_rate', 0):.1f}%
• تعداد حذف‌ها: {cache_stats.get('evictions', 0)}

🚦 **محدودیت نرخ:**
• کاربران فعال: {rate_limit_stats.get('active_users', 0)}
• درخواست‌های مسدود شده: {rate_limit_stats.get('blocked_requests', 0)}

📈 **عملکرد:**
• درخواست‌های کل: {monitor_stats.get('total_requests', 0)}
• کاربران فعال: {monitor_stats.get('active_users', 0)}
• زمان پاسخ متوسط: {monitor_stats.get('average_response_time', 0):.3f}s"""

        await message.answer(stats_text)
        logger.info(f"Admin {user_id} viewed system statistics")

    except Exception as e:
        await error_handler.handle_system_error(message, e, "view_stats")


@router.message()
@performance_monitor
@rate_limit
@maintenance_mode
async def handle_unknown_message(message: types.Message):
    """Handle unknown messages with better user guidance"""
    try:
        user_id = message.from_user.id

        # Check if user is registered
        if await data_manager.user_exists(user_id):
            await message.answer(
                "❓ پیام شما قابل تشخیص نیست.\n\n"
                + "برای دسترسی به منوی اصلی، دستور /start را ارسال کنید."
            )
        else:
            await message.answer(
                "❓ پیام شما قابل تشخیص نیست.\n\n"
                + "برای شروع ثبت‌نام، دستور /start را ارسال کنید."
            )

        logger.info(
            f"Unknown message from user {user_id}: {message.text[:50] if message.text else 'No text'}"
        )

    except Exception as e:
        await error_handler.handle_system_error(message, e, "handle_unknown_message")


# ============================================================================
# CLEANUP AND MAINTENANCE
# ============================================================================
async def cleanup_task():
    """Periodic cleanup task"""
    while True:
        try:
            # Clean up expired cache entries
            await cache_manager.clear_expired()

            # Clean up old rate limiter entries
            rate_limiter.cleanup_old_requests()

            # Check performance alerts
            monitor.check_alerts()

            # Create backup if enabled
            if config.database.backup_enabled:
                await data_manager.create_backup()

            # Log performance stats
            stats = monitor.get_stats()
            if Config.logging.performance_log_enabled:
                perf_logger.info(f"Performance stats: {stats}")

            # Wait before next cleanup
            await asyncio.sleep(config.performance.cleanup_interval_seconds)

        except Exception as e:
            logger.error(f"Error in cleanup task: {e}")
            await asyncio.sleep(60)  # Wait 1 minute on error


# ============================================================================
# MAIN FUNCTION
# ============================================================================
async def main():
    """Main function with graceful shutdown and health monitoring"""
    try:
        dp.include_router(router)

        logger.info("🚀 Ostad Hatami Bot starting with optimizations...")
        logger.info("✅ Rate limiting enabled")
        logger.info("✅ Caching system active")
        logger.info("✅ Performance monitoring enabled")
        logger.info("✅ Advanced error handling active")

        # Start polling
        await dp.start_polling(bot)

    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"💥 Bot crashed: {e}")
        raise
    finally:
        # Cleanup
        # Log final stats
        final_stats = monitor.get_stats()
        logger.info(f"📊 Final performance stats: {final_stats}")

        logger.info("🔄 Bot shutdown completed")


if __name__ == "__main__":
    import asyncio

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Bot terminated gracefully")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        raise
