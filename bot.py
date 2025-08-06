#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ostad Hatami Math Classes Registration Bot
ربات ثبت‌نام کلاس‌های ریاضی استاد حاتمی
"""

import json
import logging
import os
import re
import asyncio
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Set
from pathlib import Path
from functools import wraps

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
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure advanced logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# Performance logger
perf_logger = logging.getLogger("performance")
perf_handler = logging.FileHandler("performance.log", encoding="utf-8")
perf_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
perf_logger.addHandler(perf_handler)
perf_logger.setLevel(logging.INFO)

# Bot token from environment
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")


# Performance monitoring
class PerformanceMonitor:
    def __init__(self):
        self.request_times = defaultdict(list)
        self.error_counts = defaultdict(int)
        self.user_activity = defaultdict(int)

    def log_request_time(self, handler_name: str, duration: float):
        self.request_times[handler_name].append(duration)
        if duration > 1.0:  # Log slow requests
            perf_logger.warning(f"Slow request: {handler_name} took {duration:.2f}s")

    def log_error(self, error_type: str):
        self.error_counts[error_type] += 1

    def log_user_activity(self, user_id: int):
        self.user_activity[user_id] += 1

    def get_stats(self) -> Dict[str, Any]:
        avg_times = {}
        for handler, times in self.request_times.items():
            if times:
                avg_times[handler] = sum(times) / len(times)

        return {
            "average_response_times": avg_times,
            "error_counts": dict(self.error_counts),
            "active_users": len(self.user_activity),
            "total_requests": sum(len(times) for times in self.request_times.values()),
        }


monitor = PerformanceMonitor()


# Rate limiting
class RateLimiter:
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)

    def is_allowed(self, user_id: int) -> bool:
        now = time.time()
        user_requests = self.requests[user_id]

        # Remove old requests
        user_requests[:] = [
            req_time
            for req_time in user_requests
            if now - req_time < self.window_seconds
        ]

        if len(user_requests) >= self.max_requests:
            return False

        user_requests.append(now)
        return True

    def cleanup_old_requests(self):
        """Cleanup old requests to prevent memory leaks"""
        now = time.time()
        for user_id in list(self.requests.keys()):
            self.requests[user_id][:] = [
                req_time
                for req_time in self.requests[user_id]
                if now - req_time < self.window_seconds
            ]
            if not self.requests[user_id]:
                del self.requests[user_id]


rate_limiter = RateLimiter()


# Cache system
class SimpleCache:
    def __init__(self, ttl_seconds: int = 300):
        self.cache = {}
        self.ttl = ttl_seconds

    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return value
            else:
                del self.cache[key]
        return None

    def set(self, key: str, value: Any):
        self.cache[key] = (value, time.time())

    def clear_expired(self):
        """Clear expired cache entries"""
        now = time.time()
        expired_keys = [
            key
            for key, (_, timestamp) in self.cache.items()
            if now - timestamp >= self.ttl
        ]
        for key in expired_keys:
            del self.cache[key]


cache = SimpleCache()

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


# ============================================================================
# VALIDATION
# ============================================================================
class Validator:
    """Optimized data validation utilities"""

    # Compile regex patterns once for better performance
    _name_pattern = re.compile(
        r"^[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFFa-zA-Z\s]+$"
    )
    _phone_patterns = [
        re.compile(r"^\+98[0-9]{10}$"),
        re.compile(r"^09[0-9]{9}$"),
        re.compile(r"^9[0-9]{9}$"),
        re.compile(r"^0[0-9]{10}$"),
    ]

    @classmethod
    def validate_name(cls, name: str) -> bool:
        """Validate Persian/Arabic names with optimized regex"""
        if not name or len(name.strip()) < 2:
            return False
        return bool(cls._name_pattern.match(name.strip()))

    @classmethod
    def validate_phone(cls, phone: str) -> bool:
        """Validate Iranian phone numbers with optimized regex"""
        phone = re.sub(r"[\s\-]", "", phone)
        return any(pattern.match(phone) for pattern in cls._phone_patterns)

    @staticmethod
    def normalize_phone(phone: str) -> str:
        """Normalize phone number to standard format"""
        phone = re.sub(r"[\s\-]", "", phone)
        if phone.startswith("+98"):
            return phone
        elif phone.startswith("09"):
            return "+98" + phone[1:]
        elif phone.startswith("9"):
            return "+98" + phone
        elif phone.startswith("0"):
            return "+98" + phone[1:]
        else:
            return phone


# ============================================================================
# DATA STORAGE
# ============================================================================
class DataManager:
    """Optimized user data storage management with caching"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        self.users_dir = Path("users")
        self.users_dir.mkdir(exist_ok=True)
        self._file_locks = defaultdict(asyncio.Lock)
        self._initialized = True

    def get_user_file_path(self, user_id: int) -> Path:
        """Get path to user's JSON file"""
        return self.users_dir / f"user_{user_id}.json"

    async def save_user_data(self, user_data: Dict[str, Any]) -> bool:
        """Save user data to JSON file with async file operations and locking"""
        user_id = user_data.get("user_id")
        if not user_id:
            logger.error("User ID is required for saving data")
            return False

        async with self._file_locks[user_id]:
            try:
                file_path = self.get_user_file_path(user_id)

                # Update timestamps
                now = datetime.now().isoformat()
                if "registration_date" not in user_data:
                    user_data["registration_date"] = now
                user_data["last_updated"] = now

                # Use asyncio for file operations
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None, self._write_file_sync, file_path, user_data
                )

                # Update cache
                cache.set(f"user_{user_id}", user_data)

                logger.info(f"User data saved for user_id: {user_id}")
                return True

            except Exception as e:
                logger.error(f"Error saving user data for user_id {user_id}: {e}")
                monitor.log_error("save_user_data_error")
                return False

    def _write_file_sync(self, file_path: Path, user_data: Dict[str, Any]):
        """Synchronous file write operation"""
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(user_data, f, ensure_ascii=False, indent=2)

    async def load_user_data(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Load user data from JSON file with caching"""
        # Check cache first
        cache_key = f"user_{user_id}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data

        async with self._file_locks[user_id]:
            try:
                file_path = self.get_user_file_path(user_id)
                if not file_path.exists():
                    return None

                # Use asyncio for file operations
                loop = asyncio.get_event_loop()
                data = await loop.run_in_executor(None, self._read_file_sync, file_path)

                # Cache the result
                if data:
                    cache.set(cache_key, data)

                return data

            except Exception as e:
                logger.error(f"Error loading user data for user_id {user_id}: {e}")
                monitor.log_error("load_user_data_error")
                return None

    def _read_file_sync(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Synchronous file read operation"""
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def user_exists(self, user_id: int) -> bool:
        """Check if user exists (sync version)"""
        return self.get_user_file_path(user_id).exists()

    async def user_exists_async(self, user_id: int) -> bool:
        """Check if user exists with caching (async version)"""
        # Check cache first
        cache_key = f"user_{user_id}"
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return True

        # Check file system
        file_path = self.get_user_file_path(user_id)
        exists = await asyncio.get_event_loop().run_in_executor(None, file_path.exists)

        return exists


# ============================================================================
# CONFIGURATION
# ============================================================================
class Config:
    """Centralized configuration management"""

    # Bot settings
    MAX_REQUESTS_PER_MINUTE = int(os.getenv("MAX_REQUESTS_PER_MINUTE", "10"))
    CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "300"))
    CLEANUP_INTERVAL_SECONDS = int(os.getenv("CLEANUP_INTERVAL_SECONDS", "300"))

    # Data settings
    USERS_DIR = os.getenv("USERS_DIR", "users")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # Educational data
    GRADES = ["دهم", "یازدهم", "دوازدهم"]
    MAJORS = ["ریاضی", "تجربی", "انسانی", "هنر"]
    PROVINCES = [
        "تهران",
        "خراسان رضوی",
        "اصفهان",
        "فارس",
        "آذربایجان شرقی",
        "مازندران",
        "گیلان",
        "خوزستان",
        "قم",
        "البرز",
        "سایر",
    ]

    CITIES_BY_PROVINCE = {
        "تهران": ["تهران", "شهریار", "ورامین", "دماوند", "فیروزکوه"],
        "خراسان رضوی": ["مشهد", "نیشابور", "سبزوار", "تربت حیدریه", "کاشمر"],
        "اصفهان": ["اصفهان", "کاشان", "نجف‌آباد", "خمینی‌شهر", "شاهین‌شهر"],
        "فارس": ["شیراز", "مرودشت", "جهرم", "فسا", "کازرون"],
        "آذربایجان شرقی": ["تبریز", "مراغه", "میانه", "اهر", "بناب"],
        "مازندران": ["ساری", "بابل", "آمل", "قائم‌شهر", "نوشهر"],
        "گیلان": ["رشت", "انزلی", "لاهیجان", "آستارا", "تالش"],
        "خوزستان": ["اهواز", "دزفول", "ماهشهر", "ایذه", "شوشتر"],
        "قم": ["قم"],
        "البرز": ["کرج", "فردیس", "محمدشهر", "ماهدشت", "اشتهارد"],
        "سایر": ["سایر"],
    }

    # Contact information
    CONTACT_INFO = {
        "phone": "۰۹۱۲۳۴۵۶۷۸۹",
        "telegram": "@Ostad_Hatami",
        "email": "info@ostadhatami.ir",
        "website": "www.ostadhatami.ir",
    }


# Initialize optimized components with config
rate_limiter = RateLimiter(
    max_requests=Config.MAX_REQUESTS_PER_MINUTE, window_seconds=60
)
cache = SimpleCache(ttl_seconds=Config.CACHE_TTL_SECONDS)

# Legacy constants for compatibility
GRADES = Config.GRADES
MAJORS = Config.MAJORS
PROVINCES = Config.PROVINCES
CITIES_BY_PROVINCE = Config.CITIES_BY_PROVINCE


# ============================================================================
# KEYBOARDS
# ============================================================================
class Keyboards:
    """Keyboard builders"""

    @staticmethod
    def get_grade_keyboard() -> InlineKeyboardMarkup:
        """Build grade selection keyboard"""
        builder = InlineKeyboardBuilder()
        for grade in Config.GRADES:
            builder.button(text=grade, callback_data=f"grade:{grade}")
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def get_major_keyboard() -> InlineKeyboardMarkup:
        """Build major selection keyboard"""
        builder = InlineKeyboardBuilder()
        for major in Config.MAJORS:
            builder.button(text=major, callback_data=f"major:{major}")
        builder.adjust(2)
        return builder.as_markup()

    @staticmethod
    def get_province_keyboard() -> InlineKeyboardMarkup:
        """Build province selection keyboard"""
        builder = InlineKeyboardBuilder()
        for province in Config.PROVINCES:
            builder.button(text=province, callback_data=f"province:{province}")
        builder.adjust(2)
        return builder.as_markup()

    @staticmethod
    def get_city_keyboard(province: str) -> InlineKeyboardMarkup:
        """Build city selection keyboard for a province"""
        builder = InlineKeyboardBuilder()
        cities = Config.CITIES_BY_PROVINCE.get(province, ["سایر"])
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
# ERROR HANDLERS
# ============================================================================
class BotErrorHandler:
    """Centralized error handling"""

    @staticmethod
    async def handle_user_error(message_or_callback, error_message: str):
        """Handle user-facing errors"""
        try:
            if hasattr(message_or_callback, "answer"):
                await message_or_callback.answer(f"❌ {error_message}")
            elif hasattr(message_or_callback, "message"):
                await message_or_callback.message.answer(f"❌ {error_message}")
        except Exception as e:
            logger.error(f"Error sending error message: {e}")

    @staticmethod
    async def handle_system_error(message_or_callback, error: Exception, context: str):
        """Handle system errors"""
        error_id = int(time.time())
        logger.error(f"System error [{error_id}] in {context}: {error}")
        monitor.log_error(f"system_error_{context}")

        try:
            error_msg = (
                f"خطای سیستمی رخ داده است. کد خطا: {error_id}\nلطفاً دوباره تلاش کنید."
            )
            if hasattr(message_or_callback, "answer"):
                await message_or_callback.answer(error_msg)
            elif hasattr(message_or_callback, "message"):
                await message_or_callback.message.answer(error_msg)
        except Exception as e:
            logger.error(f"Error sending system error message: {e}")


error_handler = BotErrorHandler()


# ============================================================================
# HANDLERS
# ============================================================================
@router.message(Command("start"))
@performance_monitor
@rate_limit
async def cmd_start(message: types.Message, state: FSMContext):
    """Handle /start command with optimized performance"""
    try:
        user = message.from_user
        data_manager = DataManager()

        # Check if user exists with caching
        if await data_manager.user_exists_async(user.id):
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
    """Process first name input with validation and error handling"""
    try:
        if not message.text:
            await error_handler.handle_user_error(message, "لطفاً نام خود را وارد کنید.")
            return

        first_name = message.text.strip()

        if not Validator.validate_name(first_name):
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
async def process_last_name(message: types.Message, state: FSMContext):
    """Process last name input with validation and error handling"""
    try:
        if not message.text:
            await error_handler.handle_user_error(
                message, "لطفاً نام خانوادگی خود را وارد کنید."
            )
            return

        last_name = message.text.strip()

        if not Validator.validate_name(last_name):
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
async def process_grade(callback: types.CallbackQuery, state: FSMContext):
    """Process grade selection with error handling"""
    try:
        await callback.answer()

        if not callback.data or ":" not in callback.data:
            await error_handler.handle_user_error(callback, "داده نامعتبر دریافت شد.")
            return

        grade = callback.data.split(":")[1]
        if grade not in Config.GRADES:
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
async def process_major(callback: types.CallbackQuery, state: FSMContext):
    """Process major selection"""
    await callback.answer()
    major = callback.data.split(":")[1]
    await state.update_data(major=major)
    await state.set_state(RegistrationStates.waiting_for_province)

    await callback.message.edit_text(
        f"✅ رشته تحصیلی ثبت شد: {major}\n\n🔹 **مرحله ۵:** استان خود را انتخاب کنید",
        reply_markup=Keyboards.get_province_keyboard(),
    )


@router.callback_query(lambda c: c.data.startswith("province:"))
async def process_province(callback: types.CallbackQuery, state: FSMContext):
    """Process province selection"""
    await callback.answer()
    province = callback.data.split(":")[1]
    await state.update_data(province=province)
    await state.set_state(RegistrationStates.waiting_for_city)

    await callback.message.edit_text(
        f"✅ استان ثبت شد: {province}\n\n🔹 **مرحله ۶:** شهر خود را انتخاب کنید",
        reply_markup=Keyboards.get_city_keyboard(province),
    )


@router.callback_query(lambda c: c.data.startswith("city:"))
async def process_city(callback: types.CallbackQuery, state: FSMContext):
    """Process city selection"""
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

        data_manager = DataManager()
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
async def edit_registration(callback: types.CallbackQuery, state: FSMContext):
    """Show edit options"""
    await callback.answer()
    await state.set_state(RegistrationStates.editing)
    await callback.message.edit_text(
        "✏️ **ویرایش اطلاعات**\n\nکدام فیلد را می‌خواهید ویرایش کنید؟",
        reply_markup=Keyboards.get_edit_keyboard(),
    )


@router.callback_query(lambda c: c.data.startswith("edit_"))
async def handle_edit_field(callback: types.CallbackQuery, state: FSMContext):
    """Handle field editing"""
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


@router.callback_query(lambda c: c.data == "back_to_confirmation")
async def back_to_confirmation(callback: types.CallbackQuery, state: FSMContext):
    """Go back to confirmation"""
    await callback.answer()
    user_data = await state.get_data()
    await state.set_state(RegistrationStates.confirmation)
    await callback.message.edit_text(
        Messages.get_profile_summary(user_data),
        reply_markup=Keyboards.get_confirmation_keyboard(),
    )


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
async def view_classes(callback: types.CallbackQuery):
    """Show available classes"""
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


@router.callback_query(lambda c: c.data == "buy_book")
async def buy_book(callback: types.CallbackQuery):
    """Show book information"""
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


@router.callback_query(lambda c: c.data == "contact_teacher")
async def contact_teacher(callback: types.CallbackQuery):
    """Show contact information"""
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


@router.callback_query(lambda c: c.data == "edit_profile")
async def edit_profile(callback: types.CallbackQuery, state: FSMContext):
    """Edit user profile"""
    await callback.answer()
    data_manager = DataManager()
    user_data = data_manager.load_user_data(callback.from_user.id)

    if not user_data:
        await callback.message.edit_text("❌ اطلاعات کاربری یافت نشد.")
        return

    await state.set_state(RegistrationStates.editing)
    await state.update_data(**user_data)
    await callback.message.edit_text(
        "✏️ **ویرایش اطلاعات**\n\nکدام فیلد را می‌خواهید ویرایش کنید؟",
        reply_markup=Keyboards.get_edit_keyboard(),
    )


@router.message()
@performance_monitor
@rate_limit
async def handle_unknown_message(message: types.Message):
    """Handle unknown messages with better user guidance"""
    try:
        user_id = message.from_user.id
        data_manager = DataManager()

        # Check if user is registered
        if await data_manager.user_exists_async(user_id):
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
            cache.clear_expired()

            # Clean up old rate limiter entries
            rate_limiter.cleanup_old_requests()

            # Log performance stats
            stats = monitor.get_stats()
            perf_logger.info(f"Performance stats: {stats}")

            # Wait 5 minutes before next cleanup
            await asyncio.sleep(300)

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

        # Start cleanup task
        cleanup_task_handle = asyncio.create_task(cleanup_task())

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
        if "cleanup_task_handle" in locals():
            cleanup_task_handle.cancel()

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
