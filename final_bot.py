#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Final Working Telegram Bot for Math Course Registration
ربات نهایی کارآمد تلگرام برای ثبت‌نام کلاس‌های ریاضی
"""

import json
import logging
import os
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Import configuration
from config import *

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, LOG_LEVEL)
)
logger = logging.getLogger(__name__)

class FinalMathBot:
    def __init__(self, token):
        self.token = token
        self.application = Application.builder().token(token).build()
        self.setup_handlers()
        self.ensure_data_directory()
        
    def ensure_data_directory(self):
        """Ensure data directory exists"""
        os.makedirs("data", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        if not os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)
    
    def setup_handlers(self):
        """Setup all bot handlers"""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        self.application.add_error_handler(self.error_handler)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        welcome_text = f"""
👋 سلام {user.first_name}! خوش آمدید به ربات کلاس‌های ریاضی استاد حاتمی

📚 این ربات برای ثبت‌نام در کلاس‌های ریاضی طراحی شده است.

لطفاً یکی از گزینه‌های زیر را انتخاب کنید:
        """
        
        keyboard = [
            [InlineKeyboardButton("📚 کلاس‌های ریاضی", callback_data="courses")],
            [InlineKeyboardButton("📘 کتاب انفجار خلاقیت", callback_data="book")],
            [InlineKeyboardButton("📞 اطلاعات تماس", callback_data="contact")],
            [InlineKeyboardButton("🌐 شبکه‌های اجتماعی", callback_data="social")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "courses":
            await self.show_courses(query)
        elif query.data == "book":
            await self.show_book_info(query)
        elif query.data == "contact":
            await self.show_contact_info(query)
        elif query.data == "social":
            await self.show_social_links(query)
        elif query.data == "back_to_menu":
            await self.show_main_menu(query)
    
    async def show_courses(self, query):
        """Show available courses"""
        courses_text = "📚 کلاس‌های ریاضی موجود:\n\n"
        
        for grade, subjects in COURSES.items():
            courses_text += f"🎓 پایه {grade}:\n"
            for subject, info in subjects.items():
                price_formatted = f"{info['price']:,}".replace(',', '،')
                courses_text += f"• {subject}: {price_formatted} تومان ({info['duration']})\n"
            courses_text += "\n"
        
        courses_text += "📞 برای ثبت‌نام با استاد تماس بگیرید"
        
        keyboard = [[InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(courses_text, reply_markup=reply_markup)
    
    async def show_book_info(self, query):
        """Show book information"""
        price_formatted = f"{BOOK_INFO['price']:,}".replace(',', '،')
        
        book_text = f"""
📘 کتاب {BOOK_INFO['title']}

📖 معرفی کتاب:
{BOOK_INFO['description']}

🎯 مناسب برای:
"""
        for audience in BOOK_INFO['target_audience']:
            book_text += f"• {audience}\n"
        
        book_text += f"""
💰 قیمت: {price_formatted} تومان

📞 برای خرید کتاب با استاد تماس بگیرید
        """
        
        keyboard = [[InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(book_text, reply_markup=reply_markup)
    
    async def show_contact_info(self, query):
        """Show contact information"""
        contact_text = f"""
📞 اطلاعات تماس با استاد

📱 واتساپ: {CONTACT_INFO['whatsapp']}
📞 تماس مستقیم: {CONTACT_INFO['phone']}
💬 تلگرام: {CONTACT_INFO['telegram']}

⏰ ساعات پاسخگویی:
{CONTACT_INFO['working_hours']}

📧 ایمیل: {CONTACT_INFO['email']}

📍 آدرس: {CONTACT_INFO['address']}
        """
        
        keyboard = [[InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(contact_text, reply_markup=reply_markup)
    
    async def show_social_links(self, query):
        """Show social media links"""
        social_text = f"""
🌐 شبکه‌های اجتماعی

📱 اینستاگرام: {SOCIAL_LINKS['instagram']}
📺 یوتیوب: {SOCIAL_LINKS['youtube']}
📢 کانال تلگرام: {SOCIAL_LINKS['telegram_channel']}
🌐 وب‌سایت: {SOCIAL_LINKS['website']}

📚 محتوای آموزشی رایگان:
• حل مسائل کنکور
• نکات مهم ریاضی
• ویدیوهای آموزشی
• آزمون‌های آنلاین

✅ برای اطلاع از آخرین اخبار و محتوا، کانال‌ها را دنبال کنید
        """
        
        keyboard = [[InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(social_text, reply_markup=reply_markup)
    
    async def show_main_menu(self, query):
        """Show main menu"""
        menu_text = """
📚 منوی اصلی ربات کلاس‌های ریاضی

لطفاً یکی از گزینه‌های زیر را انتخاب کنید:
        """
        
        keyboard = [
            [InlineKeyboardButton("📚 کلاس‌های ریاضی", callback_data="courses")],
            [InlineKeyboardButton("📘 کتاب انفجار خلاقیت", callback_data="book")],
            [InlineKeyboardButton("📞 اطلاعات تماس", callback_data="contact")],
            [InlineKeyboardButton("🌐 شبکه‌های اجتماعی", callback_data="social")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(menu_text, reply_markup=reply_markup)
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Exception while handling an update: {context.error}")

async def main():
    """Main function to run the bot"""
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ لطفاً توکن ربات خود را در فایل config.py وارد کنید")
        return
    
    bot = FinalMathBot(BOT_TOKEN)
    
    print("🤖 ربات کلاس‌های ریاضی در حال اجرا...")
    print("📱 برای توقف ربات، Ctrl+C را فشار دهید")
    
    try:
        await bot.application.run_polling(drop_pending_updates=True)
    except KeyboardInterrupt:
        print("\n⏹️ ربات متوقف شد.")
    except Exception as e:
        print(f"\n❌ خطا در اجرای ربات: {e}")
        logger.error(f"Bot runtime error: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 