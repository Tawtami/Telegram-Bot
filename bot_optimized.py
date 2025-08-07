#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ostad Hatami Math Classes Registration Bot
ربات ثبت‌نام کلاس‌های ریاضی استاد حاتمی

Optimized and refactored version with modular architecture
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
from aiogram.filters import Command, StateFilter
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Configure basic logging first
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

# Import modules after logging is configured
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
from ui.keyboards import Keyboards
from ui.messages import Messages
from core.decorators import rate_limit, maintenance_mode, admin_only, registered_user_only

# Initialize config
try:
    config = Config()
    
    # Reconfigure logging with config settings
    logging.getLogger().handlers.clear()
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

# Bot token validation
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")

# Initialize components
try:
    data_manager = DataManager()
    cache_manager = SimpleCache(ttl_seconds=config.performance.cache_ttl_seconds)
    rate_limiter = RateLimiter(
        max_requests=config.performance.max_requests_per_minute, 
        window_seconds=60
    )
    error_handler = BotErrorHandler()
    validator = Validator()
except Exception as e:
    logger.error(f"Failed to initialize components: {e}")
    raise

# Initialize bot
bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
storage = MemoryStorage()
dispatcher = Dispatcher(storage=storage)

# FSM States
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


# Main router
router = Router()


# ==================== START COMMAND ====================
@router.message(Command("start"))
@rate_limit
@maintenance_mode
async def cmd_start(message: types.Message, state: FSMContext):
    """Handle /start command"""
    try:
        user_id = message.from_user.id
        first_name = message.from_user.first_name or "کاربر"
        
        # Check if user is already registered
        existing_user = data_manager.load_user_data(user_id)
        if existing_user:
            await show_main_menu_after_registration(message)
            return
        
        # Send welcome message
        welcome_msg = Messages.get_welcome_message(first_name)
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="📝 ثبت‌نام", callback_data="start_registration")
        
        await message.answer(welcome_msg, reply_markup=keyboard.as_markup())
        
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        await error_handler.handle_error(message, e)


# ==================== REGISTRATION HANDLERS ====================
@router.callback_query(lambda c: c.data == "start_registration")
@rate_limit
@maintenance_mode
async def start_registration(callback: types.CallbackQuery, state: FSMContext):
    """Start registration process"""
    try:
        await callback.message.edit_text(
            Messages.get_registration_start(),
            reply_markup=Keyboards.get_grade_keyboard()
        )
        await state.set_state(RegistrationStates.waiting_for_grade)
        
    except Exception as e:
        logger.error(f"Error starting registration: {e}")
        await error_handler.handle_error(callback.message, e)


@router.callback_query(lambda c: c.data.startswith("grade:"))
@rate_limit
@maintenance_mode
async def process_grade(callback: types.CallbackQuery, state: FSMContext):
    """Process grade selection"""
    try:
        grade = callback.data.split(":")[1]
        await state.update_data(grade=grade)
        
        await callback.message.edit_text(
            "🎓 **انتخاب رشته تحصیلی**\n\nلطفاً رشته تحصیلی خود را انتخاب کنید:",
            reply_markup=Keyboards.get_major_keyboard()
        )
        await state.set_state(RegistrationStates.waiting_for_major)
        
    except Exception as e:
        logger.error(f"Error processing grade: {e}")
        await error_handler.handle_error(callback.message, e)


@router.callback_query(lambda c: c.data.startswith("major:"))
@rate_limit
@maintenance_mode
async def process_major(callback: types.CallbackQuery, state: FSMContext):
    """Process major selection"""
    try:
        major = callback.data.split(":")[1]
        await state.update_data(major=major)
        
        await callback.message.edit_text(
            "🏛️ **انتخاب استان**\n\nلطفاً استان خود را انتخاب کنید:",
            reply_markup=Keyboards.get_province_keyboard()
        )
        await state.set_state(RegistrationStates.waiting_for_province)
        
    except Exception as e:
        logger.error(f"Error processing major: {e}")
        await error_handler.handle_error(callback.message, e)


@router.callback_query(lambda c: c.data.startswith("province:"))
@rate_limit
@maintenance_mode
async def process_province(callback: types.CallbackQuery, state: FSMContext):
    """Process province selection"""
    try:
        province = callback.data.split(":")[1]
        await state.update_data(province=province)
        
        await callback.message.edit_text(
            f"🏙️ **انتخاب شهر**\n\nاستان: {province}\n\nلطفاً شهر خود را انتخاب کنید:",
            reply_markup=Keyboards.get_city_keyboard(province)
        )
        await state.set_state(RegistrationStates.waiting_for_city)
        
    except Exception as e:
        logger.error(f"Error processing province: {e}")
        await error_handler.handle_error(callback.message, e)


@router.callback_query(lambda c: c.data.startswith("city:"))
@rate_limit
@maintenance_mode
async def process_city(callback: types.CallbackQuery, state: FSMContext):
    """Process city selection"""
    try:
        city = callback.data.split(":")[1]
        await state.update_data(city=city)
        
        await callback.message.edit_text(
            "📝 **نام**\n\nلطفاً نام خود را به فارسی وارد کنید:",
            reply_markup=Keyboards.get_back_keyboard()
        )
        await state.set_state(RegistrationStates.waiting_for_first_name)
        
    except Exception as e:
        logger.error(f"Error processing city: {e}")
        await error_handler.handle_error(callback.message, e)


@router.message(StateFilter(RegistrationStates.waiting_for_first_name))
@rate_limit
@maintenance_mode
async def process_first_name(message: types.Message, state: FSMContext):
    """Process first name input"""
    try:
        if not validator.validate_name(message.text):
            await message.answer(
                "❌ نام باید بین ۲ تا ۵۰ کاراکتر و فقط شامل حروف فارسی باشد.\nلطفاً دوباره وارد کنید:"
            )
            return
        
        await state.update_data(first_name=message.text.strip())
        
        await message.answer(
            "📝 **نام خانوادگی**\n\nلطفاً نام خانوادگی خود را به فارسی وارد کنید:",
            reply_markup=Keyboards.get_back_keyboard()
        )
        await state.set_state(RegistrationStates.waiting_for_last_name)
        
    except Exception as e:
        logger.error(f"Error processing first name: {e}")
        await error_handler.handle_error(message, e)


@router.message(StateFilter(RegistrationStates.waiting_for_last_name))
@rate_limit
@maintenance_mode
async def process_last_name(message: types.Message, state: FSMContext):
    """Process last name input"""
    try:
        if not validator.validate_name(message.text):
            await message.answer(
                "❌ نام خانوادگی باید بین ۲ تا ۵۰ کاراکتر و فقط شامل حروف فارسی باشد.\nلطفاً دوباره وارد کنید:"
            )
            return
        
        await state.update_data(last_name=message.text.strip())
        
        await message.answer(
            "📱 **شماره تلفن**\n\nلطفاً شماره تلفن خود را وارد کنید:",
            reply_markup=Keyboards.get_phone_keyboard()
        )
        await state.set_state(RegistrationStates.waiting_for_phone)
        
    except Exception as e:
        logger.error(f"Error processing last name: {e}")
        await error_handler.handle_error(message, e)


@router.message(StateFilter(RegistrationStates.waiting_for_phone))
@rate_limit
@maintenance_mode
async def process_phone(message: types.Message, state: FSMContext):
    """Process phone number input"""
    try:
        phone = message.text.strip()
        
        # Handle contact sharing
        if message.contact and message.contact.user_id == message.from_user.id:
            phone = message.contact.phone_number
        
        if not validator.validate_phone(phone):
            await message.answer(
                "❌ شماره تلفن نامعتبر است.\nلطفاً شماره معتبر وارد کنید:",
                reply_markup=Keyboards.get_phone_keyboard()
            )
            return
        
        await state.update_data(phone=phone)
        
        # Show confirmation
        data = await state.get_data()
        summary = Messages.get_profile_summary(data)
        
        await message.answer(
            summary,
            reply_markup=Keyboards.get_confirmation_keyboard(),
            reply_to_message_id=message.message_id
        )
        await state.set_state(RegistrationStates.confirmation)
        
    except Exception as e:
        logger.error(f"Error processing phone: {e}")
        await error_handler.handle_error(message, e)


@router.callback_query(lambda c: c.data == "confirm_registration")
@rate_limit
@maintenance_mode
async def confirm_registration(callback: types.CallbackQuery, state: FSMContext):
    """Confirm registration"""
    try:
        from database.models import UserData, UserStatus
        
        data = await state.get_data()
        user_id = callback.from_user.id
        
        # Create user data
        user_data = UserData(
            user_id=user_id,
            first_name=data["first_name"],
            last_name=data["last_name"],
            grade=data["grade"],
            major=data["major"],
            province=data["province"],
            city=data["city"],
            phone=data["phone"],
            status=UserStatus.ACTIVE
        )
        
        # Save user data
        data_manager.save_user_data(user_data)
        
        await callback.message.edit_text(
            Messages.get_success_message(),
            reply_markup=Keyboards.get_main_menu_keyboard()
        )
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error confirming registration: {e}")
        await error_handler.handle_error(callback.message, e)


# ==================== MAIN MENU HANDLERS ====================
@router.callback_query(lambda c: c.data == "free_courses")
@maintenance_mode
@registered_user_only
async def free_courses(callback: types.CallbackQuery):
    """Show free courses"""
    try:
        courses = data_manager.get_all_courses(course_type="free")
        
        if not courses:
            await callback.message.edit_text(
                "😔 در حال حاضر دوره رایگانی موجود نیست.",
                reply_markup=Keyboards.get_back_keyboard()
            )
            return
        
        message = Messages.get_free_courses_message()
        keyboard = InlineKeyboardBuilder()
        
        for course in courses:
            keyboard.button(
                text=f"📚 {course.title}",
                callback_data=f"view_course:{course.course_id}"
            )
        
        keyboard.button(text="🔙 بازگشت", callback_data="back_to_main")
        keyboard.adjust(1)
        
        await callback.message.edit_text(message, reply_markup=keyboard.as_markup())
        
    except Exception as e:
        logger.error(f"Error showing free courses: {e}")
        await error_handler.handle_error(callback.message, e)


@router.callback_query(lambda c: c.data == "paid_courses")
@maintenance_mode
@registered_user_only
async def paid_courses(callback: types.CallbackQuery):
    """Show paid courses"""
    try:
        courses = data_manager.get_all_courses(course_type="paid")
        
        if not courses:
            await callback.message.edit_text(
                "😔 در حال حاضر دوره تخصصی موجود نیست.",
                reply_markup=Keyboards.get_back_keyboard()
            )
            return
        
        message = Messages.get_paid_courses_message()
        keyboard = InlineKeyboardBuilder()
        
        for course in courses:
            keyboard.button(
                text=f"💎 {course.title} - {course.price:,} تومان",
                callback_data=f"view_course:{course.course_id}"
            )
        
        keyboard.button(text="🔙 بازگشت", callback_data="back_to_main")
        keyboard.adjust(1)
        
        await callback.message.edit_text(message, reply_markup=keyboard.as_markup())
        
    except Exception as e:
        logger.error(f"Error showing paid courses: {e}")
        await error_handler.handle_error(callback.message, e)


@router.callback_query(lambda c: c.data == "purchased_courses")
@maintenance_mode
@registered_user_only
async def purchased_courses(callback: types.CallbackQuery):
    """Show purchased courses"""
    try:
        user_id = callback.from_user.id
        user_data = data_manager.load_user_data(user_id)
        
        if not user_data or not user_data.purchased_courses:
            await callback.message.edit_text(
                Messages.get_no_purchases_message(),
                reply_markup=Keyboards.get_back_keyboard()
            )
            return
        
        message = "📚 **دوره‌های خریداری شده شما:**\n\n"
        keyboard = InlineKeyboardBuilder()
        
        for course_id in user_data.purchased_courses:
            course = data_manager.get_course(course_id)
            if course:
                message += f"✅ {course.title}\n"
        
        keyboard.button(text="🔙 بازگشت", callback_data="back_to_main")
        
        await callback.message.edit_text(message, reply_markup=keyboard.as_markup())
        
    except Exception as e:
        logger.error(f"Error showing purchased courses: {e}")
        await error_handler.handle_error(callback.message, e)


@router.callback_query(lambda c: c.data == "buy_book")
@maintenance_mode
@registered_user_only
async def buy_book(callback: types.CallbackQuery):
    """Show book information"""
    try:
        books = data_manager.get_all_books()
        
        if not books:
            await callback.message.edit_text(
                "😔 در حال حاضر کتابی موجود نیست.",
                reply_markup=Keyboards.get_back_keyboard()
            )
            return
        
        book = books[0]  # Assuming one book for now
        message = Messages.get_book_info_message()
        
        await callback.message.edit_text(
            message,
            reply_markup=Keyboards.get_book_purchase_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Error showing book: {e}")
        await error_handler.handle_error(callback.message, e)


@router.callback_query(lambda c: c.data == "social_media")
@maintenance_mode
async def social_media(callback: types.CallbackQuery):
    """Show social media links"""
    try:
        message = Messages.get_social_media_message()
        
        await callback.message.edit_text(
            message,
            reply_markup=Keyboards.get_social_media_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Error showing social media: {e}")
        await error_handler.handle_error(callback.message, e)


@router.callback_query(lambda c: c.data == "contact_us")
@maintenance_mode
async def contact_us(callback: types.CallbackQuery):
    """Show contact information"""
    try:
        message = Messages.get_contact_message()
        
        await callback.message.edit_text(
            message,
            reply_markup=Keyboards.get_back_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Error showing contact info: {e}")
        await error_handler.handle_error(callback.message, e)


@router.callback_query(lambda c: c.data == "back_to_main")
@maintenance_mode
async def back_to_main(callback: types.CallbackQuery):
    """Return to main menu"""
    try:
        await callback.message.edit_text(
            "🏠 **منوی اصلی**\n\nلطفاً گزینه مورد نظر خود را انتخاب کنید:",
            reply_markup=Keyboards.get_main_menu_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Error returning to main menu: {e}")
        await error_handler.handle_error(callback.message, e)


# ==================== COURSE ENROLLMENT HANDLERS ====================
@router.callback_query(lambda c: c.data.startswith("enroll_course:"))
@maintenance_mode
@registered_user_only
async def enroll_course(callback: types.CallbackQuery, state: FSMContext):
    """Enroll in free course"""
    try:
        course_id = callback.data.split(":")[1]
        user_id = callback.from_user.id
        
        # Get course
        course = data_manager.get_course(course_id)
        if not course:
            await callback.message.edit_text(
                "❌ دوره مورد نظر یافت نشد.",
                reply_markup=Keyboards.get_back_keyboard()
            )
            return
        
        if not course.can_enroll():
            await callback.message.edit_text(
                "❌ این دوره در حال حاضر قابل ثبت‌نام نیست.",
                reply_markup=Keyboards.get_back_keyboard()
            )
            return
        
        # Check if already enrolled
        user_data = data_manager.load_user_data(user_id)
        if course_id in user_data.enrolled_courses:
            await callback.message.edit_text(
                "✅ شما قبلاً در این دوره ثبت‌نام کرده‌اید.",
                reply_markup=Keyboards.get_back_keyboard()
            )
            return
        
        # Enroll user
        user_data.enrolled_courses.append(course_id)
        data_manager.save_user_data(user_data)
        
        # Update course
        course.current_students += 1
        data_manager.save_course(course)
        
        await callback.message.edit_text(
            f"✅ **ثبت‌نام موفق!**\n\n📚 **دوره:** {course.title}\n\n📅 اطلاعات کلاس برای شما ارسال خواهد شد.",
            reply_markup=Keyboards.get_main_menu_keyboard()
        )
        
        # Notify admin
        notification = NotificationData(
            notification_id=data_manager.generate_id(),
            notification_type=NotificationType.COURSE_PURCHASE,
            user_id=user_id,
            message=f"ثبت‌نام جدید در دوره رایگان: {course.title}",
            data={"course_id": course_id, "course_type": "free"}
        )
        data_manager.save_notification(notification)
        
    except Exception as e:
        logger.error(f"Error enrolling in course: {e}")
        await error_handler.handle_error(callback.message, e)


@router.callback_query(lambda c: c.data.startswith("purchase_course:"))
@maintenance_mode
@registered_user_only
async def purchase_course(callback: types.CallbackQuery, state: FSMContext):
    """Purchase paid course"""
    try:
        course_id = callback.data.split(":")[1]
        user_id = callback.from_user.id
        
        # Get course
        course = data_manager.get_course(course_id)
        if not course:
            await callback.message.edit_text(
                "❌ دوره مورد نظر یافت نشد.",
                reply_markup=Keyboards.get_back_keyboard()
            )
            return
        
        # Create purchase record
        purchase = PurchaseData(
            purchase_id=data_manager.generate_id(),
            user_id=user_id,
            item_type="course",
            item_id=course_id,
            amount=course.price,
            status=PurchaseStatus.PENDING
        )
        data_manager.save_purchase(purchase)
        
        # Show payment info
        message = Messages.get_payment_info_message(course.price, course.title)
        
        await callback.message.edit_text(
            message,
            reply_markup=Keyboards.get_payment_keyboard(purchase.purchase_id)
        )
        
    except Exception as e:
        logger.error(f"Error purchasing course: {e}")
        await error_handler.handle_error(callback.message, e)


# ==================== BOOK PURCHASE HANDLERS ====================
@router.callback_query(lambda c: c.data == "purchase_book")
@maintenance_mode
@registered_user_only
async def purchase_book(callback: types.CallbackQuery, state: FSMContext):
    """Purchase book"""
    try:
        user_id = callback.from_user.id
        books = data_manager.get_all_books()
        
        if not books:
            await callback.message.edit_text(
                "❌ کتاب مورد نظر یافت نشد.",
                reply_markup=Keyboards.get_back_keyboard()
            )
            return
        
        book = books[0]
        
        # Create purchase record
        purchase = PurchaseData(
            purchase_id=data_manager.generate_id(),
            user_id=user_id,
            item_type="book",
            item_id=book.book_id,
            amount=book.price,
            status=PurchaseStatus.PENDING
        )
        data_manager.save_purchase(purchase)
        
        await state.update_data(purchase_id=purchase.purchase_id)
        
        # Request address
        await callback.message.edit_text(
            Messages.get_address_request_message(),
            reply_markup=Keyboards.get_cancel_keyboard()
        )
        await state.set_state(PurchaseStates.waiting_for_address)
        
    except Exception as e:
        logger.error(f"Error purchasing book: {e}")
        await error_handler.handle_error(callback.message, e)


# ==================== PAYMENT HANDLERS ====================
@router.callback_query(lambda c: c.data.startswith("send_receipt:"))
@maintenance_mode
@registered_user_only
async def send_receipt(callback: types.CallbackQuery, state: FSMContext):
    """Request payment receipt"""
    try:
        purchase_id = callback.data.split(":")[1]
        await state.update_data(purchase_id=purchase_id)
        
        await callback.message.edit_text(
            "📸 **ارسال فیش واریزی**\n\nلطفاً عکس فیش واریزی خود را ارسال کنید:",
            reply_markup=Keyboards.get_cancel_keyboard()
        )
        await state.set_state(PurchaseStates.waiting_for_payment_receipt)
        
    except Exception as e:
        logger.error(f"Error requesting receipt: {e}")
        await error_handler.handle_error(callback.message, e)


@router.message(StateFilter(PurchaseStates.waiting_for_payment_receipt))
@maintenance_mode
@registered_user_only
async def process_payment_receipt(message: types.Message, state: FSMContext):
    """Process payment receipt"""
    try:
        if not message.photo:
            await message.answer(
                "❌ لطفاً عکس فیش واریزی را ارسال کنید.",
                reply_markup=Keyboards.get_cancel_keyboard()
            )
            return
        
        data = await state.get_data()
        purchase_id = data.get("purchase_id")
        
        if not purchase_id:
            await message.answer("❌ خطا در پردازش. لطفاً دوباره تلاش کنید.")
            await state.clear()
            return
        
        # Update purchase with receipt
        purchase = data_manager.get_purchase(purchase_id)
        if purchase:
            purchase.payment_receipt = message.photo[-1].file_id
            data_manager.save_purchase(purchase)
        
        # Notify admin
        notification = NotificationData(
            notification_id=data_manager.generate_id(),
            notification_type=NotificationType.PAYMENT_RECEIVED,
            user_id=message.from_user.id,
            message=f"فیش واریزی جدید دریافت شد - مبلغ: {purchase.amount:,} تومان",
            data={"purchase_id": purchase_id, "receipt_file_id": message.photo[-1].file_id}
        )
        data_manager.save_notification(notification)
        
        await message.answer(
            Messages.get_purchase_success_message(),
            reply_markup=Keyboards.get_main_menu_keyboard()
        )
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error processing payment receipt: {e}")
        await error_handler.handle_error(message, e)


# ==================== ADDRESS HANDLERS ====================
@router.message(StateFilter(PurchaseStates.waiting_for_address))
@maintenance_mode
@registered_user_only
async def process_address(message: types.Message, state: FSMContext):
    """Process address input"""
    try:
        if len(message.text.strip()) < 10:
            await message.answer(
                "❌ لطفاً آدرس کامل و دقیق خود را وارد کنید (حداقل ۱۰ کاراکتر)."
            )
            return
        
        await state.update_data(address=message.text.strip())
        
        await message.answer(
            Messages.get_postal_code_request_message(),
            reply_markup=Keyboards.get_cancel_keyboard()
        )
        await state.set_state(PurchaseStates.waiting_for_postal_code)
        
    except Exception as e:
        logger.error(f"Error processing address: {e}")
        await error_handler.handle_error(message, e)


@router.message(StateFilter(PurchaseStates.waiting_for_postal_code))
@maintenance_mode
@registered_user_only
async def process_postal_code(message: types.Message, state: FSMContext):
    """Process postal code input"""
    try:
        postal_code = message.text.strip()
        
        if not postal_code.isdigit() or len(postal_code) != 10:
            await message.answer(
                "❌ کد پستی باید ۱۰ رقم باشد. لطفاً دوباره وارد کنید:"
            )
            return
        
        await state.update_data(postal_code=postal_code)
        
        await message.answer(
            Messages.get_description_request_message(),
            reply_markup=Keyboards.get_cancel_keyboard()
        )
        await state.set_state(PurchaseStates.waiting_for_description)
        
    except Exception as e:
        logger.error(f"Error processing postal code: {e}")
        await error_handler.handle_error(message, e)


@router.message(StateFilter(PurchaseStates.waiting_for_description))
@maintenance_mode
@registered_user_only
async def process_description(message: types.Message, state: FSMContext):
    """Process description input"""
    try:
        data = await state.get_data()
        description = message.text.strip() if message.text else ""
        
        # Update purchase with address info
        purchase_id = data.get("purchase_id")
        if purchase_id:
            purchase = data_manager.get_purchase(purchase_id)
            if purchase:
                purchase.admin_notes = f"آدرس: {data.get('address', '')}\nکد پستی: {data.get('postal_code', '')}\nتوضیحات: {description}"
                data_manager.save_purchase(purchase)
        
        # Show payment info
        books = data_manager.get_all_books()
        if books:
            book = books[0]
            message_text = Messages.get_payment_info_message(book.price, book.title)
            
            await message.answer(
                message_text,
                reply_markup=Keyboards.get_payment_keyboard(purchase_id)
            )
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error processing description: {e}")
        await error_handler.handle_error(message, e)


# ==================== ADMIN HANDLERS ====================
@router.message(Command("stats"))
@admin_only
async def view_stats(message: types.Message):
    """View bot statistics (admin only)"""
    try:
        stats = data_manager.get_database_stats()
        
        stats_message = f"""📊 **آمار ربات**

👥 **کاربران:** {stats.get('total_users', 0)}
📚 **دوره‌ها:** {stats.get('total_courses', 0)}
💳 **خریدها:** {stats.get('total_purchases', 0)}
🔔 **اعلان‌ها:** {stats.get('total_notifications', 0)}
📖 **کتاب‌ها:** {stats.get('total_books', 0)}

🕒 **آخرین به‌روزرسانی:** {stats.get('last_updated', 'نامشخص')}"""
        
        await message.answer(stats_message)
        
    except Exception as e:
        logger.error(f"Error viewing stats: {e}")
        await error_handler.handle_error(message, e)


# ==================== UTILITY FUNCTIONS ====================
async def show_main_menu_after_registration(message: types.Message):
    """Show main menu after registration"""
    try:
        await message.answer(
            "🎉 **ثبت‌نام شما با موفقیت انجام شد!**\n\n"
            "حالا می‌توانید از خدمات ربات استفاده کنید:",
            reply_markup=Keyboards.get_main_menu_keyboard()
        )
    except Exception as e:
        logger.error(f"Error showing main menu: {e}")
        await error_handler.handle_error(message, e)


# ==================== ERROR HANDLERS ====================
@router.message()
@rate_limit
@maintenance_mode
async def handle_unknown_message(message: types.Message):
    """Handle unknown messages"""
    try:
        await message.answer(
            "❓ متوجه پیام شما نشدم.\n\n"
            "لطفاً از منوی اصلی استفاده کنید یا دستور /start را بزنید.",
            reply_markup=Keyboards.get_main_menu_keyboard()
        )
    except Exception as e:
        logger.error(f"Error handling unknown message: {e}")
        await error_handler.handle_error(message, e)


# ==================== MAIN FUNCTION ====================
async def main():
    """Main function"""
    try:
        logger.info("🚀 Starting Ostad Hatami Bot...")
        
        # Include routers
        dispatcher.include_router(router)
        
        # Start polling
        await dispatcher.start_polling(bot)
        
    except Exception as e:
        logger.error(f"💥 Fatal error during startup: {e}")
        raise
    finally:
        logger.info("🛑 Bot stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        raise
