#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ostad Hatami Math Classes Registration Bot
ربات ثبت‌نام کلاس‌های ریاضی استاد حاتمی
"""

import logging
import os
import asyncio
from typing import Dict, Any
from functools import wraps

from aiogram import Bot, Dispatcher, types, Router
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
from aiogram.types import (
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)
from aiogram.filters import Command, StateFilter
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Configure basic logging first
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
    ],
)

# Now import modules after logging is configured
from config import Config
from database import DataManager
from database.models import (
    CourseType,
    PurchaseStatus,
    PurchaseData,
    NotificationData,
    NotificationType,
)
from utils import Validator, SimpleCache, RateLimiter, BotErrorHandler

# Initialize config
try:
    config = Config()

    # Reconfigure logging with config settings
    logging.getLogger().handlers.clear()  # Clear existing handlers
    logging.basicConfig(
        level=getattr(logging, config.logging.level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            (
                logging.FileHandler("bot.log", encoding="utf-8")
                if config.logging.file_enabled
                else logging.NullHandler()
            ),
            (
                logging.StreamHandler()
                if config.logging.console_enabled
                else logging.NullHandler()
            ),
        ],
    )
except Exception as e:
    logging.error(f"Failed to initialize config: {e}")
    raise

logger = logging.getLogger(__name__)

# Bot token
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")

# Initialize components
try:
    data_manager = DataManager()
    cache_manager = SimpleCache(ttl_seconds=config.performance.cache_ttl_seconds)
    rate_limiter = RateLimiter(
        max_requests=config.performance.max_requests_per_minute, window_seconds=60
    )
    error_handler = BotErrorHandler()
except Exception as e:
    logger.error(f"Failed to initialize components: {e}")
    raise

# Initialize bot
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


class PurchaseStates(StatesGroup):
    """Purchase process states"""

    waiting_for_payment_receipt = State()
    waiting_for_address = State()
    waiting_for_postal_code = State()
    waiting_for_description = State()


class CourseEnrollmentStates(StatesGroup):
    """Course enrollment states"""

    waiting_for_confirmation = State()


# ============================================================================
# DECORATORS
# ============================================================================
def rate_limit(func):
    """Rate limiting decorator"""

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

        return await func(message_or_callback, *args, **kwargs)

    return wrapper


def maintenance_mode(func):
    """Maintenance mode decorator"""

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
        builder = InlineKeyboardBuilder()
        for grade in config.grades:
            builder.button(text=grade, callback_data=f"grade:{grade}")
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def get_major_keyboard() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        for major in config.majors:
            builder.button(text=major, callback_data=f"major:{major}")
        builder.adjust(2)
        return builder.as_markup()

    @staticmethod
    def get_province_keyboard() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        for province in config.provinces:
            builder.button(text=province, callback_data=f"province:{province}")
        builder.adjust(2)
        return builder.as_markup()

    @staticmethod
    def get_city_keyboard(province: str) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        cities = config.cities_by_province.get(province, ["سایر"])
        for city in cities:
            builder.button(text=city, callback_data=f"city:{city}")
        builder.adjust(2)
        return builder.as_markup()

    @staticmethod
    def get_phone_keyboard() -> ReplyKeyboardMarkup:
        keyboard = [
            [KeyboardButton(text="📱 ارسال شماره تلفن", request_contact=True)],
            [KeyboardButton(text="✏️ ورود دستی شماره")],
        ]
        return ReplyKeyboardMarkup(
            keyboard=keyboard, resize_keyboard=True, one_time_keyboard=True
        )

    @staticmethod
    def get_confirmation_keyboard() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(text="تایید نهایی ✅", callback_data="confirm_registration")
        builder.button(text="ویرایش اطلاعات ✏️", callback_data="edit_registration")
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def get_edit_keyboard() -> InlineKeyboardMarkup:
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
        builder = InlineKeyboardBuilder()
        builder.button(text="🎓 دوره‌های رایگان", callback_data="free_courses")
        builder.button(text="💎 دوره‌های تخصصی", callback_data="paid_courses")
        builder.button(text="📚 دوره‌های خریداری شده", callback_data="purchased_courses")
        builder.button(text="📘 تهیه کتاب انفجار خلاقیت", callback_data="buy_book")
        builder.button(text="🌐 فضای مجازی", callback_data="social_media")
        builder.button(text="📞 ارتباط با ما", callback_data="contact_us")
        builder.adjust(2)
        return builder.as_markup()

    @staticmethod
    def get_course_keyboard(course_id: str, course_type: str) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        if course_type == "free":
            builder.button(
                text="✅ ثبت‌نام در دوره", callback_data=f"enroll_course:{course_id}"
            )
        else:
            builder.button(
                text="💳 خرید دوره", callback_data=f"purchase_course:{course_id}"
            )
        builder.button(text="🔙 بازگشت", callback_data="back_to_courses")
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def get_payment_keyboard(purchase_id: str) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(
            text="📸 ارسال فیش واریزی", callback_data=f"send_receipt:{purchase_id}"
        )
        builder.button(text="🔙 بازگشت", callback_data="back_to_courses")
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def get_book_purchase_keyboard() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(text="💳 خرید کتاب", callback_data="purchase_book")
        builder.button(text="🔙 بازگشت", callback_data="back_to_main")
        builder.adjust(1)
        return builder.as_markup()

    @staticmethod
    def get_social_media_keyboard() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(text="📱 اینستاگرام", url="https://instagram.com/ostad_hatami")
        builder.button(text="📺 یوتیوب", url="https://youtube.com/@ostadhatami")
        builder.button(text="💬 گروه تلگرام", url="https://t.me/ostad_hatami_group")
        builder.button(text="📢 کانال تلگرام", url="https://t.me/ostad_hatami_channel")
        builder.button(text="🔙 بازگشت", callback_data="back_to_main")
        builder.adjust(2)
        return builder.as_markup()


# ============================================================================
# MESSAGES
# ============================================================================
class Messages:
    """Message templates"""

    @staticmethod
    def get_welcome_message(first_name: str) -> str:
        return f"""سلام {first_name} عزیز! 🌟

به ربات ثبت‌نام کلاس‌های رایگان استاد حاتمی خوش آمدید.

🎓 **کلاس‌های رایگان ریاضی در حال برگزاری است!**

برای استفاده از خدمات، لطفاً اطلاعات خود را وارد کنید."""

    @staticmethod
    def get_registration_start() -> str:
        return """🎓 **شروع ثبت‌نام**

لطفاً اطلاعات خود را به ترتیب وارد کنید."""

    @staticmethod
    def get_profile_summary(user_data: Dict[str, Any]) -> str:
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
        return """✅ **ثبت‌نام شما با موفقیت انجام شد!**

🎉 تبریک! شما در سیستم ثبت‌نام کلاس‌های رایگان استاد حاتمی ثبت شدید.

📚 **مراحل بعدی:**
• منتظر اطلاع‌رسانی کلاس‌های جدید باشید
• لینک اسکای‌روم و اطلاعات ورود برای شما ارسال خواهد شد
• در گروه تلگرام کلاس عضو شوید

🔔 **نکات مهم:**
• کلاس‌ها کاملاً رایگان هستند
• در صورت عدم حضور، از لیست حذف خواهید شد
• سوالات خود را از طریق ربات مطرح کنید

🎓 **حالا می‌توانید از منوی اصلی استفاده کنید!**"""

    @staticmethod
    def get_free_courses_message() -> str:
        return """🎓 **دوره‌های رایگان استاد حاتمی**

📚 **کلاس‌های ریاضی رایگان:**
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

📝 **برای ثبت‌نام در کلاس‌ها، روی گزینه مورد نظر کلیک کنید.**"""

    @staticmethod
    def get_paid_courses_message() -> str:
        return """💎 **دوره‌های تخصصی استاد حاتمی**

🎯 **دوره‌های موجود:**
• دوره جامع ریاضی کنکور
• دوره حل مسائل پیشرفته
• دوره آنالیز ریاضی
• دوره جبر خطی

💰 **قیمت‌ها:**
• دوره جامع: ۵۰۰,۰۰۰ تومان
• دوره پیشرفته: ۳۵۰,۰۰۰ تومان
• دوره آنالیز: ۴۰۰,۰۰۰ تومان
• دوره جبر: ۳۰۰,۰۰۰ تومان

✨ **ویژگی‌ها:**
• ویدیوهای با کیفیت بالا
• جزوات کامل
• پشتیبانی تلفنی
• گواهی پایان دوره

💳 **برای خرید دوره، روی گزینه مورد نظر کلیک کنید.**"""

    @staticmethod
    def get_book_info_message() -> str:
        return """📘 **کتاب انفجار خلاقیت**

✍️ **نویسنده:** استاد حاتمی
📄 **تعداد صفحات:** ۴۰۰ صفحه
💰 **قیمت:** ۲۵۰,۰۰۰ تومان

✨ **ویژگی‌های کتاب:**
• مثال‌های حل شده
• تمرینات متنوع
• نمونه سوالات کنکور
• پاسخ تشریحی
• تکنیک‌های حل مسائل
• نکات مهم کنکوری

🚚 **نحوه ارسال:**
• ارسال پستی به سراسر کشور
• زمان تحویل: ۲-۳ روز کاری
• هزینه ارسال: رایگان

💳 **برای خرید کتاب، روی گزینه خرید کلیک کنید.**"""

    @staticmethod
    def get_payment_info_message(amount: int, item_name: str) -> str:
        return f"""💳 **اطلاعات واریزی**

📦 **محصول:** {item_name}
💰 **مبلغ قابل پرداخت:** {amount:,} تومان

🏦 **شماره حساب:**
• بانک ملی: ۶۰۳۷-۹۹۹۹-۹۹۹۹-۹۹۹۹
• به نام: استاد حاتمی

📱 **شماره کارت:**
• ۶۰۳۷-۹۹۹۹-۹۹۹۹-۹۹۹۹

📸 **پس از واریز، لطفاً فیش واریزی را ارسال کنید.**
⚠️ **توجه:** بدون ارسال فیش، خرید شما تایید نخواهد شد."""

    @staticmethod
    def get_address_request_message() -> str:
        return """📮 **اطلاعات ارسال**

لطفاً آدرس دقیق پستی خود را وارد کنید:

🏠 **نمونه آدرس:**
تهران، خیابان ولیعصر، پلاک ۱۲۳، واحد ۴

📝 **نکات مهم:**
• آدرس باید کامل و دقیق باشد
• کد پستی را جداگانه وارد کنید
• شماره تماس گیرنده را ذکر کنید"""

    @staticmethod
    def get_postal_code_request_message() -> str:
        return """📮 **کد پستی**

لطفاً کد پستی ۱۰ رقمی خود را وارد کنید:

📝 **مثال:** ۱۲۳۴۵۶۷۸۹۰

⚠️ **نکات:**
• کد پستی باید ۱۰ رقم باشد
• فقط اعداد وارد کنید"""

    @staticmethod
    def get_description_request_message() -> str:
        return """📝 **توضیحات اضافی**

لطفاً هر توضیح اضافی که می‌خواهید را وارد کنید:

💡 **مثال:**
• زمان مناسب برای تماس
• درخواست‌های خاص
• سوالات اضافی

🔙 **در صورت عدم نیاز، روی بازگشت کلیک کنید.**"""

    @staticmethod
    def get_purchase_success_message() -> str:
        return """✅ **درخواست خرید شما ثبت شد!**

📋 **مراحل بعدی:**
• فیش واریزی شما بررسی خواهد شد
• پس از تایید، محصول برای شما ارسال می‌شود
• از طریق تلگرام با شما تماس گرفته خواهد شد

⏰ **زمان بررسی:** حداکثر ۲۴ ساعت

📞 **در صورت سوال:** @Ostad_Hatami

🔔 **اطلاع‌رسانی تایید خرید از طریق ربات انجام خواهد شد.**"""

    @staticmethod
    def get_no_purchases_message() -> str:
        return """📚 **دوره‌های خریداری شده**

😔 **هنوز دوره‌ای خریداری نکرده‌اید.**

💡 **پیشنهاد:**
• از دوره‌های رایگان استفاده کنید
• دوره‌های تخصصی را بررسی کنید
• کتاب انفجار خلاقیت را تهیه کنید

🔙 **برای بازگشت به منوی اصلی کلیک کنید.**"""

    @staticmethod
    def get_social_media_message() -> str:
        return """🌐 **فضای مجازی استاد حاتمی**

📱 **شبکه‌های اجتماعی:**
• اینستاگرام: آموزش‌های روزانه
• یوتیوب: ویدیوهای آموزشی
• تلگرام: گروه و کانال رسمی

💬 **گروه تلگرام:**
• پرسش و پاسخ
• اشتراک‌گذاری مطالب
• اطلاع‌رسانی کلاس‌ها

📢 **کانال تلگرام:**
• اخبار و اطلاعیه‌ها
• نمونه سوالات
• نکات آموزشی

🔗 **برای دسترسی، روی لینک مورد نظر کلیک کنید.**"""

    @staticmethod
    def get_contact_message() -> str:
        return """📞 **ارتباط با ما**

🧑‍🏫 **استاد حاتمی:**
• تلگرام: @Ostad_Hatami
• ایمیل: info@ostadhatami.ir
• وب‌سایت: www.ostadhatami.ir

📱 **شماره تماس:**
• ۰۹۱۲۳۴۵۶۷۸۹

⏰ **ساعات پاسخگویی:**
• شنبه تا چهارشنبه: ۹ صبح تا ۶ عصر
• جمعه: ۹ صبح تا ۲ عصر

💡 **نکات مهم:**
• سوالات درسی خود را مطرح کنید
• برای مشاوره تحصیلی تماس بگیرید
• درخواست کلاس خصوصی داشته باشید

🔔 **پاسخ‌گویی سریع از طریق تلگرام**"""


# ============================================================================
# HANDLERS
# ============================================================================
@router.message(Command("start"))
@rate_limit
@maintenance_mode
async def cmd_start(message: types.Message, state: FSMContext):
    """Handle /start command"""
    try:
        user = message.from_user

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
@rate_limit
@maintenance_mode
async def process_first_name(message: types.Message, state: FSMContext):
    """Process first name input"""
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
@rate_limit
@maintenance_mode
async def process_last_name(message: types.Message, state: FSMContext):
    """Process last name input"""
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
@rate_limit
@maintenance_mode
async def process_grade(callback: types.CallbackQuery, state: FSMContext):
    """Process grade selection"""
    try:
        await callback.answer()

        if not callback.data or ":" not in callback.data:
            await error_handler.handle_user_error(callback, "داده نامعتبر دریافت شد.")
            return

        grade = callback.data.split(":")[1]
        if grade not in config.grades:
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
            f"✅ شهر ثبت شد: {city}\n\n🔹 **مرحله ۷:** شماره تلفن همراه خود را وارد نمایید"
        )
        await callback.message.answer(
            "📱 لطفاً شماره تلفن خود را وارد کنید:",
            reply_markup=Keyboards.get_phone_keyboard(),
        )
    except Exception as e:
        await error_handler.handle_system_error(callback, e, "process_city")


@router.message(StateFilter(RegistrationStates.waiting_for_phone))
@rate_limit
@maintenance_mode
async def process_phone(message: types.Message, state: FSMContext):
    """Process phone number input"""
    try:
        phone = ""

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
        await message.answer("📝 اطلاعات شما:", reply_markup=ReplyKeyboardRemove())
        await message.answer(
            Messages.get_profile_summary(user_data),
            reply_markup=Keyboards.get_confirmation_keyboard(),
        )

        logger.info(f"User {message.from_user.id} entered phone number")

    except Exception as e:
        await error_handler.handle_system_error(message, e, "process_phone")


@router.callback_query(lambda c: c.data == "confirm_registration")
@rate_limit
@maintenance_mode
async def confirm_registration(callback: types.CallbackQuery, state: FSMContext):
    """Confirm registration"""
    try:
        await callback.answer()

        user_data = await state.get_data()
        if not user_data:
            await error_handler.handle_user_error(
                callback, "اطلاعات ثبت‌نام یافت نشد. لطفاً مجدداً ثبت‌نام کنید."
            )
            return

        user_data["user_id"] = callback.from_user.id

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


# ============================================================================
# MAIN MENU HANDLERS
# ============================================================================
@router.callback_query(lambda c: c.data == "free_courses")
@maintenance_mode
async def free_courses(callback: types.CallbackQuery):
    """Show free courses"""
    try:
        await callback.answer()
        courses = await data_manager.get_all_courses(CourseType.FREE)

        if not courses:
            await callback.message.edit_text(
                "😔 در حال حاضر دوره رایگانی موجود نیست.",
                reply_markup=Keyboards.get_main_menu_keyboard(),
            )
            return

        courses_text = Messages.get_free_courses_message() + "\n\n"
        for course in courses:
            courses_text += f"📚 **{course.title}**\n"
            courses_text += f"📝 {course.description}\n"
            courses_text += f"⏰ {course.schedule}\n"
            courses_text += f"👥 {course.current_students}/{course.max_students if course.max_students > 0 else 'نامحدود'}\n\n"

        await callback.message.edit_text(
            courses_text,
            reply_markup=Keyboards.get_course_keyboard(courses[0].course_id, "free"),
        )
    except Exception as e:
        await error_handler.handle_system_error(callback, e, "free_courses")


@router.callback_query(lambda c: c.data == "paid_courses")
@maintenance_mode
async def paid_courses(callback: types.CallbackQuery):
    """Show paid courses"""
    try:
        await callback.answer()
        courses = await data_manager.get_all_courses(CourseType.PAID)

        if not courses:
            await callback.message.edit_text(
                "😔 در حال حاضر دوره تخصصی موجود نیست.",
                reply_markup=Keyboards.get_main_menu_keyboard(),
            )
            return

        courses_text = Messages.get_paid_courses_message() + "\n\n"
        for course in courses:
            courses_text += f"💎 **{course.title}**\n"
            courses_text += f"📝 {course.description}\n"
            courses_text += f"💰 {course.price:,} تومان\n"
            courses_text += f"⏰ {course.duration}\n\n"

        await callback.message.edit_text(
            courses_text,
            reply_markup=Keyboards.get_course_keyboard(courses[0].course_id, "paid"),
        )
    except Exception as e:
        await error_handler.handle_system_error(callback, e, "paid_courses")


@router.callback_query(lambda c: c.data == "purchased_courses")
@maintenance_mode
async def purchased_courses(callback: types.CallbackQuery):
    """Show user's purchased courses"""
    try:
        await callback.answer()
        user_id = callback.from_user.id
        purchases = await data_manager.get_user_purchases(
            user_id, PurchaseStatus.APPROVED
        )

        if not purchases:
            await callback.message.edit_text(
                Messages.get_no_purchases_message(),
                reply_markup=Keyboards.get_main_menu_keyboard(),
            )
            return

        courses_text = "📚 **دوره‌های خریداری شده شما:**\n\n"
        for purchase in purchases:
            if purchase.item_type == "course":
                course = await data_manager.get_course(purchase.item_id)
                if course:
                    courses_text += f"✅ **{course.title}**\n"
                    courses_text += f"📅 تاریخ خرید: {purchase.created_date[:10]}\n"
                    courses_text += f"💰 مبلغ: {purchase.amount:,} تومان\n\n"

        await callback.message.edit_text(
            courses_text, reply_markup=Keyboards.get_main_menu_keyboard()
        )
    except Exception as e:
        await error_handler.handle_system_error(callback, e, "purchased_courses")


@router.callback_query(lambda c: c.data == "buy_book")
@maintenance_mode
async def buy_book(callback: types.CallbackQuery):
    """Show book information"""
    try:
        await callback.answer()
        await callback.message.edit_text(
            Messages.get_book_info_message(),
            reply_markup=Keyboards.get_book_purchase_keyboard(),
        )
    except Exception as e:
        await error_handler.handle_system_error(callback, e, "buy_book")


@router.callback_query(lambda c: c.data == "social_media")
@maintenance_mode
async def social_media(callback: types.CallbackQuery):
    """Show social media links"""
    try:
        await callback.answer()
        await callback.message.edit_text(
            Messages.get_social_media_message(),
            reply_markup=Keyboards.get_social_media_keyboard(),
        )
    except Exception as e:
        await error_handler.handle_system_error(callback, e, "social_media")


@router.callback_query(lambda c: c.data == "contact_us")
@maintenance_mode
async def contact_us(callback: types.CallbackQuery):
    """Show contact information"""
    try:
        await callback.answer()
        await callback.message.edit_text(
            Messages.get_contact_message(),
            reply_markup=Keyboards.get_main_menu_keyboard(),
        )
    except Exception as e:
        await error_handler.handle_system_error(callback, e, "contact_us")


@router.callback_query(lambda c: c.data == "back_to_main")
@maintenance_mode
async def back_to_main(callback: types.CallbackQuery):
    """Back to main menu"""
    try:
        await callback.answer()
        await callback.message.edit_text(
            "🎓 **منوی اصلی ربات استاد حاتمی**\n\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=Keyboards.get_main_menu_keyboard(),
        )
    except Exception as e:
        await error_handler.handle_system_error(callback, e, "back_to_main")


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
        await state.update_data(**user_data.to_dict())
        await callback.message.edit_text(
            "✏️ **ویرایش اطلاعات**\n\nکدام فیلد را می‌خواهید ویرایش کنید؟",
            reply_markup=Keyboards.get_edit_keyboard(),
        )
    except Exception as e:
        await error_handler.handle_system_error(callback, e, "edit_profile")


# ============================================================================
# COURSE ENROLLMENT HANDLERS
# ============================================================================
@router.callback_query(lambda c: c.data.startswith("enroll_course:"))
@maintenance_mode
async def enroll_course(callback: types.CallbackQuery, state: FSMContext):
    """Enroll in free course"""
    try:
        await callback.answer()
        course_id = callback.data.split(":")[1]
        user_id = callback.from_user.id

        course = await data_manager.get_course(course_id)
        if not course:
            await callback.message.edit_text("❌ دوره مورد نظر یافت نشد.")
            return

        if not course.can_enroll():
            await callback.message.edit_text("❌ این دوره در حال حاضر قابل ثبت‌نام نیست.")
            return

        # Check if user is already enrolled
        user = await data_manager.load_user_data(user_id)
        if course_id in user.enrolled_courses:
            await callback.message.edit_text("✅ شما قبلاً در این دوره ثبت‌نام کرده‌اید.")
            return

        # Enroll user
        await data_manager.update_user_courses(user_id, course_id, "add")
        await data_manager.update_course_students(course_id, 1)

        await callback.message.edit_text(
            f"✅ **ثبت‌نام موفق!**\n\n📚 **دوره:** {course.title}\n\n📅 اطلاعات کلاس برای شما ارسال خواهد شد.",
            reply_markup=Keyboards.get_main_menu_keyboard()
        )

        # Notify admin
        notification = NotificationData(
            notification_id=data_manager.generate_id(),
            notification_type=NotificationType.COURSE_PURCHASE,
            user_id=user_id,
            message=f"کاربر {user.get_full_name()} در دوره رایگان {course.title} ثبت‌نام کرد.",
            data={"course_id": course_id, "course_title": course.title}
        )
        await data_manager.save_notification(notification)

    except Exception as e:
        await error_handler.handle_system_error(callback, e, "enroll_course")


@router.callback_query(lambda c: c.data.startswith("purchase_course:"))
@maintenance_mode
async def purchase_course(callback: types.CallbackQuery, state: FSMContext):
    """Purchase paid course"""
    try:
        await callback.answer()
        course_id = callback.data.split(":")[1]
        user_id = callback.from_user.id

        course = await data_manager.get_course(course_id)
        if not course:
            await callback.message.edit_text("❌ دوره مورد نظر یافت نشد.")
            return

        # Create purchase record
        purchase = PurchaseData(
            purchase_id=data_manager.generate_id(),
            user_id=user_id,
            item_type="course",
            item_id=course_id,
            amount=course.price
        )
        await data_manager.save_purchase(purchase)

        await callback.message.edit_text(
            Messages.get_payment_info_message(course.price, course.title),
            reply_markup=Keyboards.get_payment_keyboard(purchase.purchase_id)
        )

    except Exception as e:
        await error_handler.handle_system_error(callback, e, "purchase_course")


@router.callback_query(lambda c: c.data == "purchase_book")
@maintenance_mode
async def purchase_book(callback: types.CallbackQuery, state: FSMContext):
    """Purchase book"""
    try:
        await callback.answer()
        user_id = callback.from_user.id

        # Create purchase record for book
        purchase = PurchaseData(
            purchase_id=data_manager.generate_id(),
            user_id=user_id,
            item_type="book",
            item_id="book_creativity_explosion",
            amount=250000  # 250,000 Tomans
        )
        await data_manager.save_purchase(purchase)

        await state.set_state(PurchaseStates.waiting_for_address)
        await state.update_data(purchase_id=purchase.purchase_id)

        await callback.message.edit_text(
            Messages.get_payment_info_message(250000, "کتاب انفجار خلاقیت") + "\n\n" + Messages.get_address_request_message()
        )

    except Exception as e:
        await error_handler.handle_system_error(callback, e, "purchase_book")


# ============================================================================
# PAYMENT HANDLERS
# ============================================================================
@router.callback_query(lambda c: c.data.startswith("send_receipt:"))
@maintenance_mode
async def send_receipt(callback: types.CallbackQuery, state: FSMContext):
    """Handle payment receipt"""
    try:
        await callback.answer()
        purchase_id = callback.data.split(":")[1]
        
        await state.set_state(PurchaseStates.waiting_for_payment_receipt)
        await state.update_data(purchase_id=purchase_id)

        await callback.message.edit_text(
            "📸 **ارسال فیش واریزی**\n\nلطفاً عکس فیش واریزی خود را ارسال کنید.\n\n⚠️ **نکات مهم:**\n• عکس باید واضح و خوانا باشد\n• شماره تراکنش قابل مشاهده باشد\n• مبلغ واریزی مشخص باشد"
        )

    except Exception as e:
        await error_handler.handle_system_error(callback, e, "send_receipt")


@router.message(StateFilter(PurchaseStates.waiting_for_payment_receipt))
@maintenance_mode
async def process_payment_receipt(message: types.Message, state: FSMContext):
    """Process payment receipt"""
    try:
        if not message.photo:
            await message.answer("❌ لطفاً عکس فیش واریزی را ارسال کنید.")
            return

        data = await state.get_data()
        purchase_id = data.get("purchase_id")

        # Save receipt info
        await state.update_data(receipt_file_id=message.photo[-1].file_id)

        # Notify admin
        purchase = await data_manager.get_purchase(purchase_id)
        if purchase:
            notification = NotificationData(
                notification_id=data_manager.generate_id(),
                notification_type=NotificationType.PAYMENT_RECEIVED,
                user_id=message.from_user.id,
                message=f"فیش واریزی جدید برای {purchase.item_type} دریافت شد.",
                data={
                    "purchase_id": purchase_id,
                    "amount": purchase.amount,
                    "receipt_file_id": message.photo[-1].file_id
                }
            )
            await data_manager.save_notification(notification)

        await message.answer(
            "✅ فیش واریزی شما دریافت شد.\n\n📋 **مراحل بعدی:**\n• فیش شما بررسی خواهد شد\n• پس از تایید، محصول ارسال می‌شود\n• از طریق تلگرام با شما تماس گرفته خواهد شد\n\n⏰ **زمان بررسی:** حداکثر ۲۴ ساعت",
            reply_markup=Keyboards.get_main_menu_keyboard()
        )
        await state.clear()

    except Exception as e:
        await error_handler.handle_system_error(message, e, "process_payment_receipt")


# ============================================================================
# BOOK PURCHASE HANDLERS
# ============================================================================
@router.message(StateFilter(PurchaseStates.waiting_for_address))
@maintenance_mode
async def process_address(message: types.Message, state: FSMContext):
    """Process address input"""
    try:
        if not message.text or len(message.text.strip()) < 10:
            await message.answer("❌ لطفاً آدرس کامل و دقیق خود را وارد کنید (حداقل ۱۰ کاراکتر).")
            return

        await state.update_data(address=message.text.strip())
        await state.set_state(PurchaseStates.waiting_for_postal_code)

        await message.answer(Messages.get_postal_code_request_message())

    except Exception as e:
        await error_handler.handle_system_error(message, e, "process_address")


@router.message(StateFilter(PurchaseStates.waiting_for_postal_code))
@maintenance_mode
async def process_postal_code(message: types.Message, state: FSMContext):
    """Process postal code input"""
    try:
        postal_code = message.text.strip()
        if not postal_code.isdigit() or len(postal_code) != 10:
            await message.answer("❌ لطفاً کد پستی ۱۰ رقمی معتبر وارد کنید.")
            return

        await state.update_data(postal_code=postal_code)
        await state.set_state(PurchaseStates.waiting_for_description)

        await message.answer(Messages.get_description_request_message())

    except Exception as e:
        await error_handler.handle_system_error(message, e, "process_postal_code")


@router.message(StateFilter(PurchaseStates.waiting_for_description))
@maintenance_mode
async def process_description(message: types.Message, state: FSMContext):
    """Process description input"""
    try:
        data = await state.get_data()
        description = message.text.strip() if message.text else ""
        
        # Update purchase with address info
        purchase_id = data.get("purchase_id")
        if purchase_id:
            purchase = await data_manager.get_purchase(purchase_id)
            if purchase:
                purchase.admin_notes = f"آدرس: {data.get('address')}\nکد پستی: {data.get('postal_code')}\nتوضیحات: {description}"
                await data_manager.save_purchase(purchase)

        await message.answer(
            Messages.get_purchase_success_message(),
            reply_markup=Keyboards.get_main_menu_keyboard()
        )
        await state.clear()

    except Exception as e:
        await error_handler.handle_system_error(message, e, "process_description")


@router.message(Command("stats"))
@maintenance_mode
async def view_stats(message: types.Message):
    """Admin command to view system statistics"""
    try:
        user_id = message.from_user.id

        if str(user_id) not in config.bot.admin_user_ids:
            await message.answer("❌ شما مجاز به استفاده از این دستور نیستید.")
            return

        cache_stats = cache_manager.get_stats()
        rate_limit_stats = rate_limiter.get_stats()
        db_stats = await data_manager.get_database_stats()

        stats_text = f"""📊 **آمار سیستم:**

🗄️ **دیتابیس:**
• تعداد کاربران: {db_stats.get('total_users', 0)}
• حجم فایل‌ها: {db_stats.get('total_size_mb', 0):.2f} MB

💾 **کش:**
• تعداد آیتم‌ها: {cache_stats.get('total_items', 0)}
• نرخ موفقیت: {cache_stats.get('hit_rate', 0):.1f}%

🚦 **محدودیت نرخ:**
• کاربران فعال: {rate_limit_stats.get('active_users', 0)}
• درخواست‌های مسدود شده: {rate_limit_stats.get('blocked_requests', 0)}"""

        await message.answer(stats_text)
        logger.info(f"Admin {user_id} viewed system statistics")

    except Exception as e:
        await error_handler.handle_system_error(message, e, "view_stats")


@router.message()
@rate_limit
@maintenance_mode
async def handle_unknown_message(message: types.Message):
    """Handle unknown messages"""
    try:
        user_id = message.from_user.id

        if await data_manager.user_exists(user_id):
            await message.answer(
                "❓ پیام شما قابل تشخیص نیست.\n\nبرای دسترسی به منوی اصلی، دستور /start را ارسال کنید."
            )
        else:
            await message.answer(
                "❓ پیام شما قابل تشخیص نیست.\n\nبرای شروع ثبت‌نام، دستور /start را ارسال کنید."
            )

        logger.info(
            f"Unknown message from user {user_id}: {message.text[:50] if message.text else 'No text'}"
        )

    except Exception as e:
        await error_handler.handle_system_error(message, e, "handle_unknown_message")


# ============================================================================
# MAIN FUNCTION
# ============================================================================
async def main():
    """Main function"""
    try:
        dp.include_router(router)

        logger.info("🚀 Ostad Hatami Bot starting...")
        logger.info("✅ Rate limiting enabled")
        logger.info("✅ Caching system active")
        logger.info("✅ Error handling active")

        await dp.start_polling(bot)

    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"💥 Bot crashed: {e}")
        raise
    finally:
        logger.info("🔄 Bot shutdown completed")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Bot terminated gracefully")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        raise
