#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CallbackQueryHandler, CallbackContext
from telegram.constants import ParseMode

from utils.keyboards import build_main_menu_keyboard, build_register_keyboard
from utils.storage import StudentStorage
from ui.messages import Messages


async def ensure_registered(update: Update, context: CallbackContext) -> bool:
    storage: StudentStorage = context.bot_data["storage"]
    user_id = update.effective_user.id
    if user_id in context.bot_data["config"].bot.admin_user_ids:
        return True
    return storage.get_student(user_id) is not None


async def send_main_menu(update: Update, context: CallbackContext):
    # If not registered and not admin, show welcome with register button
    user_id = update.effective_user.id
    if user_id not in context.bot_data["config"].bot.admin_user_ids:
        storage: StudentStorage = context.bot_data["storage"]
        if not storage.get_student(user_id):
            first_name = update.effective_user.first_name or "کاربر"
            await update.effective_chat.send_message(
                Messages.get_welcome_message(first_name),
                reply_markup=build_register_keyboard(),
                parse_mode=ParseMode.HTML,
            )
            return

    await update.effective_chat.send_message(
        "🏠 منوی اصلی",
        reply_markup=build_main_menu_keyboard(),
        parse_mode=ParseMode.HTML,
    )


async def back_to_main(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    # Reuse the same gating logic used for /start
    # Convert callback context to a chat send by calling send_main_menu
    await send_main_menu(update, context)


async def profile(update: Update, context: CallbackContext):
    if not await ensure_registered(update, context):
        await update.callback_query.answer("لطفاً ابتدا ثبت‌نام کنید.", show_alert=True)
        return
    storage: StudentStorage = context.bot_data["storage"]
    user_id = update.effective_user.id
    s = storage.get_student(user_id)
    if not s:
        await update.callback_query.answer("ثبت‌نام یافت نشد.", show_alert=True)
        return
    text = (
        f"👤 پروفایل من\n\n"
        f"نام: {s.first_name} {s.last_name}\n"
        f"استان/شهر: {s.province} / {s.city}\n"
        f"مقطع: {s.grade} – رشته: {s.field}\n"
        f"دوره‌های رایگان: {len(s.free_courses)}\n"
        f"دوره‌های خریداری‌شده: {len(s.purchased_courses)}\n"
    )
    kb = InlineKeyboardMarkup(
        [[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]]
    )
    await update.callback_query.answer()
    await update.callback_query.message.edit_text(text, reply_markup=kb)


def register_menu_handlers(app: Application):
    app.add_handler(CallbackQueryHandler(back_to_main, pattern=r"^back_to_main$"))
    app.add_handler(CallbackQueryHandler(profile, pattern=r"^profile$"))
    # Expose function for other modules
    register_menu_handlers.send_main_menu = send_main_menu  # type: ignore
