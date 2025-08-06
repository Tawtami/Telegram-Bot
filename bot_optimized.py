#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ostad Hatami Math Classes Registration Bot - Optimized Version
ربات ثبت‌نام کلاس‌های ریاضی استاد حاتمی - نسخه بهینه‌شده
"""

import asyncio
import logging
import time
from functools import wraps
from typing import Dict, Any, Optional

from aiogram import Bot, Dispatcher, types, Router
from aiogram.fsm import State, StatesGroup
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

# Import optimized modules
from config import config
from database import DataManager
from database.models import UserData, UserStatus
from utils import (
    Validator,
    cache_manager,
    rate_limiter,
    monitor,
    error_handler,
    SecurityUtils,
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.logging.level),
    format=config.logging.format,
    handlers=[
        (
            logging.FileHandler("bot.log", encoding="utf-8")
            if config.logging.file_enabled
            else None
        ),
        logging.StreamHandler() if config.logging.console_enabled else None,
    ],
)
logger = logging.getLogger(__name__)

# Performance logger
if config.logging.performance_log_enabled:
    perf_logger = logging.getLogger("performance")
    perf_handler = logging.FileHandler("performance.log", encoding="utf-8")
    perf_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
    perf_logger.addHandler(perf_handler)
    perf_logger.setLevel(logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=config.bot_token, parse_mode="HTML")
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()

# Initialize data manager
data_manager = DataManager()


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
        user_id = None

        # Extract user_id from args
        for arg in args:
            if hasattr(arg, "from_user"):
                user_id = arg.from_user.id
                break
            elif hasattr(arg, "message") and hasattr(arg.message, "from_user"):
                user_id = arg.message.from_user.id
                break

        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            await monitor.log_request_time(func.__name__, duration, user_id)
            return result
        except Exception as e:
            await monitor.log_error(type(e).__name__, func.__name__, user_id)
            await error_handler.handle_error(e, func.__name__, user_id)
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

        if user_id:
            # Check rate limit
            is_allowed = await rate_limiter.is_allowed(str(user_id))
            if not is_allowed:
                await error_handler.handle_user_error(
                    message_or_callback, "⚠️ لطفاً کمی صبر کنید و دوباره تلاش کنید."
                )
                return

            # Log user activity
            await monitor.log_user_activity(user_id)

        return await func(message_or_callback, *args, **kwargs)

    return wrapper


def maintenance_mode(func):
    """Decorator to check maintenance mode"""

    @wraps(func)
    async def wrapper(message_or_callback, *args, **kwargs):
        if config.bot.maintenance_mode:
            user_id = None
            if hasattr(message_or_callback, "from_user"):
                user_id = message_or_callback.from_user.id

            # Allow admin users during maintenance
            if user_id in config.bot.admin_user_ids:
                return await func(message_or_callback, *args, **kwargs)

            await error_handler.handle_user_error(
                message_or_callback,
                "🔧 ربات در حال تعمیر و نگهداری است. لطفاً بعداً تلاش کنید.",
            )
            return

        return await func(message_or_callback, *args, **kwargs)

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
        for grade in config.grades:
            builder.button(text=grade, callback_data=f"grade:{grade}")
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def get_major_keyboard() -> InlineKeyboardMarkup:
        """Build major selection keyboard"""
        builder = InlineKeyboardBuilder()
        for major in config.majors:
            builder.button(text=major, callback_data=f"major:{major}")
        builder.adjust(2)
        return builder.as_markup()

    @staticmethod
    def get_province_keyboard() -> InlineKeyboardMarkup:
        """Build province selection keyboard"""
        builder = InlineKeyboardBuilder()
        for province in config.provinces:
            builder.button(text=province, callback_data=f"province:{province}")
        builder.adjust(2)
        return builder.as_markup()

    @staticmethod
    def get_city_keyboard(province: str) -> InlineKeyboardMarkup:
        """Build city selection keyboard for a province"""
        builder = InlineKeyboardBuilder()
        cities = config.cities_by_province.get(province, ["سایر"])
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
        builder.button(text="📊 آمار و اطلاعات", callback_data="view_stats")
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
        return config.bot.welcome_message_template.format(first_name=first_name)

    @staticmethod
    def get_registration_start() -> str:
        """Get registration start message"""
        return """🎓 **شروع ثبت‌نام**

لطفاً اطلاعات خود را به ترتیب وارد کنید.
هر مرحله را با دقت تکمیل نمایید."""

    @staticmethod
    def get_profile_summary(user_data: UserData) -> str:
        """Get profile summary message"""
        return f"""📝 **اطلاعات ثبت‌شده:**

👤 **نام:** {user_data.first_name}
👤 **نام خانوادگی:** {user_data.last_name}
🎓 **پایه:** {user_data.grade}
📚 **رشته:** {user_data.major}
📍 **شهر:** {user_data.city}، {user_data.province}
📞 **شماره:** {user_data.phone}

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

        # Check if user exists
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
async def process_first_name(message: types.Message, state: FSMContext):
    """Process first name input with enhanced validation"""
    try:
        if not message.text:
            await error_handler.handle_user_error(message, "لطفاً نام خود را وارد کنید.")
            return

        # Validate and sanitize input
        is_valid, result = Validator.validate_name(message.text, "نام")
        if not is_valid:
            await error_handler.handle_user_error(message, result)
            return

        first_name = result  # result contains the sanitized name

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
async def process_last_name(message: types.Message, state: FSMContext):
    """Process last name input with enhanced validation"""
    try:
        if not message.text:
            await error_handler.handle_user_error(
                message, "لطفاً نام خانوادگی خود را وارد کنید."
            )
            return

        # Validate and sanitize input
        is_valid, result = Validator.validate_name(message.text, "نام خانوادگی")
        if not is_valid:
            await error_handler.handle_user_error(message, result)
            return

        last_name = result

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
async def process_grade(callback: types.CallbackQuery, state: FSMContext):
    """Process grade selection"""
    try:
        await callback.answer()

        if not callback.data or ":" not in callback.data:
            await error_handler.handle_user_error(callback, "داده نامعتبر دریافت شد.")
            return

        grade = callback.data.split(":")[1]
        is_valid, result = Validator.validate_grade(grade)
        if not is_valid:
            await error_handler.handle_user_error(callback, result)
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
async def process_major(callback: types.CallbackQuery, state: FSMContext):
    """Process major selection"""
    try:
        await callback.answer()
        major = callback.data.split(":")[1]

        is_valid, result = Validator.validate_major(major)
        if not is_valid:
            await error_handler.handle_user_error(callback, result)
            return

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
async def process_province(callback: types.CallbackQuery, state: FSMContext):
    """Process province selection"""
    try:
        await callback.answer()
        province = callback.data.split(":")[1]

        is_valid, result = Validator.validate_province(province)
        if not is_valid:
            await error_handler.handle_user_error(callback, result)
            return

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
async def process_city(callback: types.CallbackQuery, state: FSMContext):
    """Process city selection"""
    try:
        await callback.answer()
        city = callback.data.split(":")[1]

        user_data = await state.get_data()
        province = user_data.get("province", "تهران")

        is_valid, result = Validator.validate_city(city, province)
        if not is_valid:
            await error_handler.handle_user_error(callback, result)
            return

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

        # Validate phone number
        is_valid, result = Validator.validate_phone(phone)
        if not is_valid:
            await error_handler.handle_user_error(message, result)
            return

        normalized_phone = result  # result contains the normalized phone
        await state.update_data(phone=normalized_phone)

        # Get all user data
        user_data_dict = await state.get_data()
        user_data_dict["user_id"] = message.from_user.id

        # Create UserData object
        user_data = UserData(
            user_id=message.from_user.id,
            first_name=user_data_dict["first_name"],
            last_name=user_data_dict["last_name"],
            grade=user_data_dict["grade"],
            major=user_data_dict["major"],
            province=user_data_dict["province"],
            city=user_data_dict["city"],
            phone=normalized_phone,
            status=UserStatus.PENDING,
        )

        await state.set_state(RegistrationStates.confirmation)
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
async def confirm_registration(callback: types.CallbackQuery, state: FSMContext):
    """Confirm registration with comprehensive validation"""
    try:
        await callback.answer()

        user_data_dict = await state.get_data()
        if not user_data_dict:
            await error_handler.handle_user_error(
                callback, "اطلاعات ثبت‌نام یافت نشد. لطفاً مجدداً ثبت‌نام کنید."
            )
            return

        # Validate all required fields
        is_valid, errors = Validator.validate_user_data(user_data_dict)
        if not is_valid:
            error_message = "\n".join(errors[:3])  # Show first 3 errors
            await error_handler.handle_user_error(
                callback, f"اطلاعات ناقص:\n{error_message}"
            )
            return

        # Create UserData object
        user_data = UserData(
            user_id=callback.from_user.id,
            first_name=user_data_dict["first_name"],
            last_name=user_data_dict["last_name"],
            grade=user_data_dict["grade"],
            major=user_data_dict["major"],
            province=user_data_dict["province"],
            city=user_data_dict["city"],
            phone=user_data_dict["phone"],
            status=UserStatus.ACTIVE,
        )

        # Save user data
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


# ============================================================================
# MAIN MENU HANDLERS
# ============================================================================
@performance_monitor
async def show_main_menu(message: types.Message):
    """Show main menu for registered users"""
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
    """Show main menu after successful registration"""
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
@performance_monitor
@rate_limit
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


@router.callback_query(lambda c: c.data == "view_stats")
@performance_monitor
@rate_limit
async def view_stats(callback: types.CallbackQuery):
    """Show user statistics (admin only)"""
    try:
        await callback.answer()

        user_id = callback.from_user.id
        if user_id not in config.bot.admin_user_ids:
            await error_handler.handle_user_error(callback, "دسترسی غیرمجاز.")
            return

        # Get statistics
        stats = await data_manager.get_database_stats()

        stats_text = f"""📊 **آمار سیستم:**

👥 **کاربران:**
• کل کاربران: {stats['users']['total_users']}
• کاربران فعال: {stats['users']['active_users']}
• ثبت‌نام‌های اخیر: {stats['users']['recent_registrations']}

💾 **کش:**
• ضربه‌های کش: {stats['cache']['hits']}
• عدم ضربه‌های کش: {stats['cache']['misses']}
• نرخ ضربه: {stats['cache']['hit_rate_percent']}%

🗄️ **پشتیبان:**
• تعداد پشتیبان‌ها: {stats['backup']['count']}
• آخرین پشتیبان: {stats['backup']['last_backup'] or 'هیچ'}"""

        await callback.message.edit_text(stats_text)

    except Exception as e:
        await error_handler.handle_system_error(callback, e, "view_stats")


# ============================================================================
# CLEANUP AND MAINTENANCE
# ============================================================================
async def cleanup_task():
    """Periodic cleanup task"""
    while True:
        try:
            # Clean up expired cache entries
            await cache_manager.clear_all()

            # Clean up old rate limiter entries
            await rate_limiter.cleanup_old_entries()

            # Clear old performance data
            await monitor.clear_old_data()

            # Create backup if enabled
            if config.database.backup_enabled:
                await data_manager.create_backup()

            # Log performance stats
            stats = await monitor.get_stats()
            if config.logging.performance_log_enabled:
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
        # Validate configuration
        config.validate()

        # Include router
        dp.include_router(router)

        # Start cleanup task
        cleanup_task_handle = asyncio.create_task(cleanup_task())

        # Start rate limiter cleanup
        await rate_limiter.start_cleanup_task()

        logger.info("🚀 Ostad Hatami Bot starting with optimizations...")
        logger.info(f"✅ Configuration: {config.to_dict()}")
        logger.info("✅ Rate limiting enabled")
        logger.info("✅ Caching system active")
        logger.info("✅ Performance monitoring enabled")
        logger.info("✅ Enhanced error handling active")
        logger.info("✅ Security features enabled")

        # Start polling
        await dp.start_polling(bot)

    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"💥 Bot crashed: {e}")
        raise
    finally:
        # Cleanup
        if "cleanup_task_handle" in locals():
            cleanup_task_handle.cancel()

        await rate_limiter.stop_cleanup_task()

        # Log final stats
        final_stats = await monitor.get_stats()
        logger.info(f"📊 Final performance stats: {final_stats}")

        logger.info("🔄 Bot shutdown completed")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Bot terminated gracefully")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        raise
