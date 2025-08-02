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
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from aiogram import Bot, Dispatcher, types, Router
from aiogram.fsm import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    InlineKeyboardMarkup, ReplyKeyboardMarkup, 
    KeyboardButton, ReplyKeyboardRemove
)
from aiogram.filters import Command, StateFilter
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Bot token from environment
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
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
# VALIDATION
# ============================================================================
class Validator:
    """Data validation utilities"""
    
    @staticmethod
    def validate_name(name: str) -> bool:
        """Validate Persian/Arabic names"""
        if not name or len(name.strip()) < 2:
            return False
        pattern = r'^[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFFa-zA-Z\s]+$'
        return bool(re.match(pattern, name.strip()))
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Validate Iranian phone numbers"""
        phone = re.sub(r'[\s\-]', '', phone)
        patterns = [
            r'^\+98[0-9]{10}$',
            r'^09[0-9]{9}$',
            r'^9[0-9]{9}$',
            r'^0[0-9]{10}$'
        ]
        return any(re.match(pattern, phone) for pattern in patterns)
    
    @staticmethod
    def normalize_phone(phone: str) -> str:
        """Normalize phone number to standard format"""
        phone = re.sub(r'[\s\-]', '', phone)
        if phone.startswith('+98'):
            return phone
        elif phone.startswith('09'):
            return '+98' + phone[1:]
        elif phone.startswith('9'):
            return '+98' + phone
        elif phone.startswith('0'):
            return '+98' + phone[1:]
        else:
            return phone

# ============================================================================
# DATA STORAGE
# ============================================================================
class DataManager:
    """User data storage management"""
    
    def __init__(self):
        self.users_dir = Path("users")
        self.users_dir.mkdir(exist_ok=True)
    
    def get_user_file_path(self, user_id: int) -> Path:
        """Get path to user's JSON file"""
        return self.users_dir / f"user_{user_id}.json"
    
    def save_user_data(self, user_data: Dict[str, Any]) -> bool:
        """Save user data to JSON file"""
        try:
            user_id = user_data.get('user_id')
            if not user_id:
                logger.error("User ID is required for saving data")
                return False
            
            file_path = self.get_user_file_path(user_id)
            user_data['registration_date'] = datetime.now().isoformat()
            user_data['last_updated'] = datetime.now().isoformat()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(user_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"User data saved for user_id: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving user data: {e}")
            return False
    
    def load_user_data(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Load user data from JSON file"""
        try:
            file_path = self.get_user_file_path(user_id)
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
            
        except Exception as e:
            logger.error(f"Error loading user data for user_id {user_id}: {e}")
            return None
    
    def user_exists(self, user_id: int) -> bool:
        """Check if user exists"""
        return self.get_user_file_path(user_id).exists()

# ============================================================================
# CONSTANTS
# ============================================================================
GRADES = ["دهم", "یازدهم", "دوازدهم"]
MAJORS = ["ریاضی", "تجربی", "انسانی", "هنر"]
PROVINCES = ["تهران", "خراسان رضوی", "اصفهان", "فارس", "آذربایجان شرقی", 
             "مازندران", "گیلان", "خوزستان", "قم", "البرز", "سایر"]

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
    "سایر": ["سایر"]
}

# ============================================================================
# KEYBOARDS
# ============================================================================
class Keyboards:
    """Keyboard builders"""
    
    @staticmethod
    def get_grade_keyboard() -> InlineKeyboardMarkup:
        """Build grade selection keyboard"""
        builder = InlineKeyboardBuilder()
        for grade in GRADES:
            builder.button(text=grade, callback_data=f"grade:{grade}")
        builder.adjust(1)
        return builder.as_markup()
    
    @staticmethod
    def get_major_keyboard() -> InlineKeyboardMarkup:
        """Build major selection keyboard"""
        builder = InlineKeyboardBuilder()
        for major in MAJORS:
            builder.button(text=major, callback_data=f"major:{major}")
        builder.adjust(2)
        return builder.as_markup()
    
    @staticmethod
    def get_province_keyboard() -> InlineKeyboardMarkup:
        """Build province selection keyboard"""
        builder = InlineKeyboardBuilder()
        for province in PROVINCES:
            builder.button(text=province, callback_data=f"province:{province}")
        builder.adjust(2)
        return builder.as_markup()
    
    @staticmethod
    def get_city_keyboard(province: str) -> InlineKeyboardMarkup:
        """Build city selection keyboard for a province"""
        builder = InlineKeyboardBuilder()
        cities = CITIES_BY_PROVINCE.get(province, ["سایر"])
        for city in cities:
            builder.button(text=city, callback_data=f"city:{city}")
        builder.adjust(2)
        return builder.as_markup()
    
    @staticmethod
    def get_phone_keyboard() -> ReplyKeyboardMarkup:
        """Build phone number input keyboard"""
        keyboard = [
            [KeyboardButton(text="📱 ارسال شماره تلفن", request_contact=True)],
            [KeyboardButton(text="✏️ ورود دستی شماره")]
        ]
        return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True, one_time_keyboard=True)
    
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
            ("شماره تلفن", "edit_phone")
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
        builder.button(text="🗓 مشاهده کلاس‌های قابل ثبت‌نام", callback_data="view_classes")
        builder.button(text="📘 تهیه کتاب انفجار خلاقیت", callback_data="buy_book")
        builder.button(text="🧑‍🏫 ارتباط با استاد حاتمی", callback_data="contact_teacher")
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
async def cmd_start(message: types.Message, state: FSMContext):
    """Handle /start command"""
    user = message.from_user
    data_manager = DataManager()
    
    if data_manager.user_exists(user.id):
        await show_main_menu(message)
        return
    
    await state.clear()
    welcome_text = Messages.get_welcome_message(user.first_name)
    await message.answer(welcome_text)
    
    await state.set_state(RegistrationStates.waiting_for_first_name)
    await message.answer(
        Messages.get_registration_start() + "\n\n🔹 **مرحله ۱:** نام خود را وارد نمایید"
    )

@router.message(StateFilter(RegistrationStates.waiting_for_first_name))
async def process_first_name(message: types.Message, state: FSMContext):
    """Process first name input"""
    first_name = message.text.strip()
    
    if not Validator.validate_name(first_name):
        await message.answer("❌ نام وارد شده نامعتبر است. لطفاً نام صحیح وارد کنید (حداقل ۲ حرف).")
        return
    
    await state.update_data(first_name=first_name)
    await state.set_state(RegistrationStates.waiting_for_last_name)
    await message.answer("✅ نام ثبت شد.\n\n🔹 **مرحله ۲:** نام خانوادگی خود را وارد نمایید")

@router.message(StateFilter(RegistrationStates.waiting_for_last_name))
async def process_last_name(message: types.Message, state: FSMContext):
    """Process last name input"""
    last_name = message.text.strip()
    
    if not Validator.validate_name(last_name):
        await message.answer("❌ نام خانوادگی وارد شده نامعتبر است. لطفاً نام خانوادگی صحیح وارد کنید.")
        return
    
    await state.update_data(last_name=last_name)
    await state.set_state(RegistrationStates.waiting_for_grade)
    await message.answer(
        "✅ نام خانوادگی ثبت شد.\n\n🔹 **مرحله ۳:** پایه تحصیلی خود را مشخص نمایید",
        reply_markup=Keyboards.get_grade_keyboard()
    )

@router.callback_query(lambda c: c.data.startswith("grade:"))
async def process_grade(callback: types.CallbackQuery, state: FSMContext):
    """Process grade selection"""
    await callback.answer()
    grade = callback.data.split(":")[1]
    await state.update_data(grade=grade)
    await state.set_state(RegistrationStates.waiting_for_major)
    
    await callback.message.edit_text(
        f"✅ پایه تحصیلی ثبت شد: {grade}\n\n🔹 **مرحله ۴:** رشته تحصیلی خود را انتخاب کنید",
        reply_markup=Keyboards.get_major_keyboard()
    )

@router.callback_query(lambda c: c.data.startswith("major:"))
async def process_major(callback: types.CallbackQuery, state: FSMContext):
    """Process major selection"""
    await callback.answer()
    major = callback.data.split(":")[1]
    await state.update_data(major=major)
    await state.set_state(RegistrationStates.waiting_for_province)
    
    await callback.message.edit_text(
        f"✅ رشته تحصیلی ثبت شد: {major}\n\n🔹 **مرحله ۵:** استان خود را انتخاب کنید",
        reply_markup=Keyboards.get_province_keyboard()
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
        reply_markup=Keyboards.get_city_keyboard(province)
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
        reply_markup=ReplyKeyboardRemove()
    )
    
    await callback.message.answer(
        "📱 لطفاً شماره تلفن خود را وارد کنید:",
        reply_markup=Keyboards.get_phone_keyboard()
    )

@router.message(StateFilter(RegistrationStates.waiting_for_phone))
async def process_phone(message: types.Message, state: FSMContext):
    """Process phone number input"""
    phone = message.text.strip()
    
    if message.contact:
        phone = message.contact.phone_number
    
    if not Validator.validate_phone(phone):
        await message.answer("❌ شماره تلفن نامعتبر است. لطفاً شماره معتبر وارد کنید (مثال: 09121234567)")
        return
    
    normalized_phone = Validator.normalize_phone(phone)
    await state.update_data(phone=normalized_phone)
    
    user_data = await state.get_data()
    user_data['user_id'] = message.from_user.id
    
    await state.set_state(RegistrationStates.confirmation)
    await message.answer(
        Messages.get_profile_summary(user_data),
        reply_markup=Keyboards.get_confirmation_keyboard(),
        reply_markup=ReplyKeyboardRemove()
    )

@router.callback_query(lambda c: c.data == "confirm_registration")
async def confirm_registration(callback: types.CallbackQuery, state: FSMContext):
    """Confirm registration"""
    await callback.answer()
    
    user_data = await state.get_data()
    user_data['user_id'] = callback.from_user.id
    
    data_manager = DataManager()
    if data_manager.save_user_data(user_data):
        await callback.message.edit_text(Messages.get_success_message())
        await show_main_menu_after_registration(callback.message)
    else:
        await callback.message.edit_text("❌ خطا در ثبت‌نام. لطفاً دوباره تلاش کنید.")

@router.callback_query(lambda c: c.data == "edit_registration")
async def edit_registration(callback: types.CallbackQuery, state: FSMContext):
    """Show edit options"""
    await callback.answer()
    await state.set_state(RegistrationStates.editing)
    await callback.message.edit_text(
        "✏️ **ویرایش اطلاعات**\n\nکدام فیلد را می‌خواهید ویرایش کنید؟",
        reply_markup=Keyboards.get_edit_keyboard()
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
            reply_markup=Keyboards.get_grade_keyboard()
        )
    elif field == "major":
        await state.set_state(RegistrationStates.waiting_for_major)
        await callback.message.edit_text(
            "🔹 رشته تحصیلی جدید خود را انتخاب کنید:",
            reply_markup=Keyboards.get_major_keyboard()
        )
    elif field == "province":
        await state.set_state(RegistrationStates.waiting_for_province)
        await callback.message.edit_text(
            "🔹 استان جدید خود را انتخاب کنید:",
            reply_markup=Keyboards.get_province_keyboard()
        )
    elif field == "city":
        user_data = await state.get_data()
        province = user_data.get('province', 'تهران')
        await state.set_state(RegistrationStates.waiting_for_city)
        await callback.message.edit_text(
            "🔹 شهر جدید خود را انتخاب کنید:",
            reply_markup=Keyboards.get_city_keyboard(province)
        )
    elif field == "phone":
        await state.set_state(RegistrationStates.waiting_for_phone)
        await callback.message.edit_text(
            "🔹 شماره تلفن جدید خود را وارد نمایید:",
            reply_markup=Keyboards.get_phone_keyboard()
        )

@router.callback_query(lambda c: c.data == "back_to_confirmation")
async def back_to_confirmation(callback: types.CallbackQuery, state: FSMContext):
    """Go back to confirmation"""
    await callback.answer()
    user_data = await state.get_data()
    await state.set_state(RegistrationStates.confirmation)
    await callback.message.edit_text(
        Messages.get_profile_summary(user_data),
        reply_markup=Keyboards.get_confirmation_keyboard()
    )

# ============================================================================
# MAIN MENU HANDLERS
# ============================================================================
async def show_main_menu(message: types.Message):
    """Show main menu for registered users"""
    await message.answer(
        "🎓 **منوی اصلی ربات استاد حاتمی**\n\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=Keyboards.get_main_menu_keyboard()
    )

async def show_main_menu_after_registration(message: types.Message):
    """Show main menu after successful registration"""
    await message.answer(
        "🎓 **منوی اصلی ربات استاد حاتمی**\n\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=Keyboards.get_main_menu_keyboard()
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
        reply_markup=Keyboards.get_edit_keyboard()
    )

@router.message()
async def handle_unknown_message(message: types.Message):
    """Handle unknown messages"""
    await message.answer(
        "❓ پیام شما قابل تشخیص نیست.\n\nبرای شروع مجدد، دستور /start را ارسال کنید."
    )

# ============================================================================
# MAIN FUNCTION
# ============================================================================
async def main():
    """Main function"""
    dp.include_router(router)
    logger.info("🚀 Ostad Hatami Bot starting...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 