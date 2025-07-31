#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hosted Telegram Bot for Math Course Registration
ربات تلگرام برای هاستینگ - ثبت‌نام کلاس‌های ریاضی
"""

import json
import logging
import os
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import configuration
from config import *

# Configure logging for hosting
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class HostedMathBot:
    def __init__(self):
        # Get token from environment variable (for hosting) or config file
        self.token = os.getenv('BOT_TOKEN', BOT_TOKEN)
        if not self.token or self.token == "YOUR_BOT_TOKEN_HERE":
            raise ValueError("BOT_TOKEN not found in environment variables or config")
        
        self.application = Application.builder().token(self.token).build()
        self.setup_handlers()
        self.ensure_data_directory()
        
    def ensure_data_directory(self):
        """Ensure data directory exists"""
        os.makedirs("data", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
    
    def setup_handlers(self):
        """Setup all bot handlers"""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        self.application.add_error_handler(self.error_handler)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        welcome_text = f"""
👋 سلام {user.first_name}! خوش آمدید به ربات کلاس‌های ریاضی استاد حاتمی

📚 این ربات برای ثبت‌نام در کلاس‌های ریاضی طراحی شده است.

🎯 **کلاس‌های رایگان آنلاین** در حال برگزاری است!

لطفاً یکی از گزینه‌های زیر را انتخاب کنید:
        """
        
        keyboard = [
            [InlineKeyboardButton("📢 اطلاعیه‌های جدید", callback_data="announcements")],
            [InlineKeyboardButton("📝 ثبت‌نام در کلاس", callback_data="register")],
            [InlineKeyboardButton("📚 کلاس‌های ریاضی", callback_data="courses")],
            [InlineKeyboardButton("🎓 کلاس‌های ویژه رایگان", callback_data="special_courses")],
            [InlineKeyboardButton("📅 برنامه کلاس‌ها", callback_data="schedule")],
            [InlineKeyboardButton("📘 کتاب انفجار خلاقیت", callback_data="book")],
            [InlineKeyboardButton("📞 اطلاعات تماس", callback_data="contact")],
            [InlineKeyboardButton("🌐 شبکه‌های اجتماعی", callback_data="social")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
🤖 راهنمای استفاده از ربات

📋 **دستورات موجود:**
/start - شروع ربات و نمایش منوی اصلی
/help - نمایش این راهنما

🎯 **قابلیت‌های ربات:**
• مشاهده اطلاعیه‌های جدید
• ثبت‌نام در کلاس‌های مختلف
• مشاهده برنامه کلاس‌ها
• اطلاعات کلاس‌های رایگان
• خرید کتاب
• تماس با استاد

📞 **پشتیبانی:**
برای سوالات بیشتر با استاد تماس بگیرید
        """
        await update.message.reply_text(help_text)
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "announcements":
            await self.show_announcements(query)
        elif query.data == "register":
            await self.show_registration(query)
        elif query.data == "courses":
            await self.show_courses(query)
        elif query.data == "special_courses":
            await self.show_special_courses(query)
        elif query.data == "schedule":
            await self.show_schedule(query)
        elif query.data == "book":
            await self.show_book_info(query)
        elif query.data == "contact":
            await self.show_contact_info(query)
        elif query.data == "social":
            await self.show_social_links(query)
        elif query.data == "back_to_menu":
            await self.show_main_menu(query)
    
    async def show_announcements(self, query):
        """Show latest announcements"""
        announcements_text = "📢 **آخرین اطلاعیه‌ها:**\n\n"
        
        for i, announcement in enumerate(ANNOUNCEMENTS, 1):
            announcements_text += f"**{i}. {announcement['title']}**\n"
            announcements_text += f"📅 {announcement['date']}\n"
            announcements_text += f"📝 {announcement['content']}\n\n"
        
        announcements_text += "📞 برای اطلاعات بیشتر با استاد تماس بگیرید"
        
        keyboard = [
            [InlineKeyboardButton("📝 ثبت‌نام فوری", callback_data="register")],
            [InlineKeyboardButton("📅 برنامه کلاس‌ها", callback_data="schedule")],
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(announcements_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def show_special_courses(self, query):
        """Show special free courses"""
        special_text = "🎓 **کلاس‌های ویژه رایگان:**\n\n"
        
        for course_name, course_info in SPECIAL_COURSES.items():
            special_text += f"**📚 {course_name}**\n"
            special_text += f"🎯 مناسب: {course_info['target']}\n"
            special_text += f"📅 شروع: {course_info.get('start_date', 'به زودی')}\n"
            special_text += f"⏰ زمان: {course_info.get('schedule', 'تعیین خواهد شد')}\n"
            special_text += f"💻 پلتفرم: {course_info.get('platform', 'آنلاین')}\n"
            if 'deadline' in course_info:
                special_text += f"⏳ مهلت ثبت‌نام: {course_info['deadline']}\n"
            special_text += f"💰 هزینه: {course_info['type']}\n\n"
        
        special_text += "✅ **این کلاس‌ها کاملاً رایگان هستند!**"
        
        keyboard = [
            [InlineKeyboardButton("📝 ثبت‌نام فوری", callback_data="register")],
            [InlineKeyboardButton("📅 برنامه کلاس‌ها", callback_data="schedule")],
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(special_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def show_schedule(self, query):
        """Show current class schedule"""
        schedule_text = "📅 **برنامه کلاس‌های فعلی:**\n\n"
        
        for date, schedule_info in CURRENT_SCHEDULE.items():
            schedule_text += f"**📆 {date}**\n"
            schedule_text += f"⏰ ساعت: {schedule_info['time']}\n"
            schedule_text += f"👥 شرکت‌کنندگان: {schedule_info['participants']}\n"
            schedule_text += f"📚 رشته‌ها: {schedule_info['subjects']}\n"
            schedule_text += f"💻 پلتفرم: {schedule_info['platform']}\n"
            schedule_text += f"⚠️ نکته: {schedule_info['note']}\n\n"
        
        schedule_text += "📊 **وضعیت ظرفیت کلاس‌ها:**\n"
        for grade, capacity in CLASS_CAPACITY.items():
            status_emoji = "🟢" if capacity['status'] == "در حال ثبت‌نام" else "🔴"
            schedule_text += f"{status_emoji} {grade}: {capacity['current']}/{capacity['max']} ({capacity['status']})\n"
        
        keyboard = [
            [InlineKeyboardButton("📝 ثبت‌نام فوری", callback_data="register")],
            [InlineKeyboardButton("🎓 کلاس‌های ویژه", callback_data="special_courses")],
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(schedule_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def show_courses(self, query):
        """Show available courses"""
        courses_text = "📚 **کلاس‌های ریاضی موجود:**\n\n"
        
        for grade, subjects in COURSES.items():
            courses_text += f"**🎓 پایه {grade}:**\n"
            for subject, info in subjects.items():
                price_formatted = f"{info['price']:,}".replace(',', '،')
                courses_text += f"• {subject}: {price_formatted} تومان ({info['duration']})\n"
            courses_text += "\n"
        
        courses_text += "🎓 **کلاس‌های رایگان هم موجود است!**\n"
        courses_text += "📞 برای ثبت‌نام با استاد تماس بگیرید"
        
        keyboard = [
            [InlineKeyboardButton("🎓 کلاس‌های رایگان", callback_data="special_courses")],
            [InlineKeyboardButton("📝 ثبت‌نام", callback_data="register")],
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(courses_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def show_registration(self, query):
        """Show registration form"""
        registration_text = """
📝 **ثبت‌نام در کلاس‌های ریاضی**

🎯 **مراحل ثبت‌نام:**

1️⃣ ابتدا کلاس مورد نظر خود را انتخاب کنید
2️⃣ اطلاعات تماس خود را ارسال کنید  
3️⃣ منتظر تماس استاد باشید

🎓 **کلاس‌های رایگان موجود:**
• نظریه اعداد گسسته (دوازدهم + المپیاد)
• مهارت‌های حل خلاق مسائل (همه پایه‌ها)

📞 **یا مستقیماً با استاد تماس بگیرید:**
        """
        
        keyboard = [
            [InlineKeyboardButton("🎓 کلاس‌های رایگان", callback_data="special_courses")],
            [InlineKeyboardButton("📚 مشاهده کلاس‌ها", callback_data="courses")],
            [InlineKeyboardButton("📅 برنامه کلاس‌ها", callback_data="schedule")],
            [InlineKeyboardButton("📞 تماس مستقیم", callback_data="contact")],
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(registration_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def show_book_info(self, query):
        """Show book information"""
        price_formatted = f"{BOOK_INFO['price']:,}".replace(',', '،')
        
        book_text = f"""
📘 **کتاب {BOOK_INFO['title']}**

📖 **معرفی کتاب:**
{BOOK_INFO['description']}

🎯 **مناسب برای:**
"""
        for audience in BOOK_INFO['target_audience']:
            book_text += f"• {audience}\n"
        
        book_text += f"""
💰 **قیمت:** {price_formatted} تومان

📞 برای خرید کتاب با استاد تماس بگیرید
        """
        
        keyboard = [
            [InlineKeyboardButton("📞 تماس برای خرید", callback_data="contact")],
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(book_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def show_contact_info(self, query):
        """Show contact information"""
        contact_text = f"""
📞 **اطلاعات تماس با استاد**

📱 **واتساپ:** {CONTACT_INFO['whatsapp']}
📞 **تماس مستقیم:** {CONTACT_INFO['phone']}
💬 **تلگرام:** {CONTACT_INFO['telegram']}

⏰ **ساعات پاسخگویی:**
{CONTACT_INFO['working_hours']}

📧 **ایمیل:** {CONTACT_INFO['email']}

📍 **آدرس:** {CONTACT_INFO['address']}

🎯 **برای ثبت‌نام فوری تماس بگیرید!**
        """
        
        keyboard = [
            [InlineKeyboardButton("📝 ثبت‌نام فوری", callback_data="register")],
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(contact_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def show_social_links(self, query):
        """Show social media links"""
        social_text = f"""
🌐 **شبکه‌های اجتماعی**

📱 **اینستاگرام:** {SOCIAL_LINKS['instagram']}
📺 **یوتیوب:** {SOCIAL_LINKS['youtube']}
📢 **کانال تلگرام:** {SOCIAL_LINKS['telegram_channel']}
🌐 **وب‌سایت:** {SOCIAL_LINKS['website']}

📚 **محتوای آموزشی رایگان:**
• حل مسائل کنکور
• نکات مهم ریاضی
• ویدیوهای آموزشی
• آزمون‌های آنلاین

✅ برای اطلاع از آخرین اخبار و محتوا، کانال‌ها را دنبال کنید
        """
        
        keyboard = [
            [InlineKeyboardButton("📢 اطلاعیه‌های جدید", callback_data="announcements")],
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(social_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def show_main_menu(self, query):
        """Show main menu"""
        menu_text = """
📚 **منوی اصلی ربات کلاس‌های ریاضی**

🎯 **کلاس‌های رایگان آنلاین** در حال برگزاری است!

لطفاً یکی از گزینه‌های زیر را انتخاب کنید:
        """
        
        keyboard = [
            [InlineKeyboardButton("📢 اطلاعیه‌های جدید", callback_data="announcements")],
            [InlineKeyboardButton("📝 ثبت‌نام در کلاس", callback_data="register")],
            [InlineKeyboardButton("📚 کلاس‌های ریاضی", callback_data="courses")],
            [InlineKeyboardButton("🎓 کلاس‌های ویژه رایگان", callback_data="special_courses")],
            [InlineKeyboardButton("📅 برنامه کلاس‌ها", callback_data="schedule")],
            [InlineKeyboardButton("📘 کتاب انفجار خلاقیت", callback_data="book")],
            [InlineKeyboardButton("📞 اطلاعات تماس", callback_data="contact")],
            [InlineKeyboardButton("🌐 شبکه‌های اجتماعی", callback_data="social")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(menu_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Exception while handling an update: {context.error}")

def main():
    """Main function to run the bot"""
    try:
        bot = HostedMathBot()
        logger.info("🤖 ربات کلاس‌های ریاضی در حال راه‌اندازی...")
        
        # Start the bot
        bot.application.run_polling(drop_pending_updates=True)
        
    except ValueError as e:
        logger.error(f"❌ خطا در تنظیمات: {e}")
        logger.error("💡 لطفاً BOT_TOKEN را در متغیرهای محیطی تنظیم کنید")
    except Exception as e:
        logger.error(f"❌ خطا در اجرای ربات: {e}")

if __name__ == "__main__":
    main() 