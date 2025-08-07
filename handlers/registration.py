#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Registration handlers for Ostad Hatami Bot
"""

import logging
from typing import Dict, Any
from aiogram import Router, types
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, StateFilter
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import Config
from database import DataManager
from database.models import UserData, UserStatus
from utils import Validator, BotErrorHandler
from ui.keyboards import Keyboards
from ui.messages import Messages
from core.decorators import rate_limit, maintenance_mode

logger = logging.getLogger(__name__)
router = Router()

# Initialize components
config = Config()
data_manager = DataManager()
validator = Validator()
error_handler = BotErrorHandler()


class RegistrationStates(StatesGroup):
    """Registration process states"""

    waiting_for_first_name = State()
    waiting_for_last_name = State()
    waiting_for_grade = State()
    waiting_for_major = State()
    waiting_for_province = State()
    waiting_for_city = State()
    confirmation = State()
    editing = State()


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


@router.callback_query(lambda c: c.data == "start_registration")
@rate_limit
@maintenance_mode
async def start_registration(callback: types.CallbackQuery, state: FSMContext):
    """Start registration process"""
    try:
        await callback.message.edit_text(
            Messages.get_registration_start(),
            reply_markup=Keyboards.get_grade_keyboard(),
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
            reply_markup=Keyboards.get_major_keyboard(),
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
            reply_markup=Keyboards.get_province_keyboard(),
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
            reply_markup=Keyboards.get_city_keyboard(province),
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
            reply_markup=Keyboards.get_back_keyboard(),
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
            reply_markup=Keyboards.get_back_keyboard(),
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

        # Show confirmation
        data = await state.get_data()
        summary = Messages.get_profile_summary(data)

        await message.answer(
            summary,
            reply_markup=Keyboards.get_confirmation_keyboard(),
            reply_to_message_id=message.message_id,
        )
        await state.set_state(RegistrationStates.confirmation)

    except Exception as e:
        logger.error(f"Error processing last name: {e}")
        await error_handler.handle_error(message, e)


@router.callback_query(lambda c: c.data == "confirm_registration")
@rate_limit
@maintenance_mode
async def confirm_registration(callback: types.CallbackQuery, state: FSMContext):
    """Confirm registration"""
    try:
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
            phone="",  # Phone not required in specification
            status=UserStatus.ACTIVE,
        )

        # Save user data
        data_manager.save_user_data(user_data.to_dict())

        await callback.message.edit_text(
            Messages.get_success_message(),
            reply_markup=Keyboards.get_main_menu_keyboard(),
        )
        await state.clear()

    except Exception as e:
        logger.error(f"Error confirming registration: {e}")
        await error_handler.handle_error(callback.message, e)


async def show_main_menu_after_registration(message: types.Message):
    """Show main menu after registration"""
    try:
        await message.answer(
            "🎉 **ثبت‌نام شما با موفقیت انجام شد!**\n\n"
            "حالا می‌توانید از خدمات ربات استفاده کنید:",
            reply_markup=Keyboards.get_main_menu_keyboard(),
        )
    except Exception as e:
        logger.error(f"Error showing main menu: {e}")
        await error_handler.handle_error(message, e)
