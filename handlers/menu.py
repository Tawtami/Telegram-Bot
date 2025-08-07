#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, CallbackContext
from telegram.constants import ParseMode

from utils.keyboards import build_main_menu_keyboard
from utils.storage import StudentStorage
from ui.messages import Messages


async def ensure_registered(update: Update, context: CallbackContext) -> bool:
    storage: StudentStorage = context.bot_data["storage"]
    user_id = update.effective_user.id
    if user_id in context.bot_data["config"].bot.admin_user_ids:
        return True
    return storage.get_student(user_id) is not None


async def send_main_menu(update: Update, context: CallbackContext):
    await update.effective_chat.send_message(
        "🏠 منوی اصلی", reply_markup=build_main_menu_keyboard(), parse_mode=ParseMode.HTML
    )


async def back_to_main(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    await update.callback_query.message.edit_text(
        "🏠 منوی اصلی", reply_markup=build_main_menu_keyboard()
    )


def register_menu_handlers(app: Application):
    app.add_handler(CallbackQueryHandler(back_to_main, pattern=r"^back_to_main$"))
    # Expose function for other modules
    register_menu_handlers.send_main_menu = send_main_menu  # type: ignore
