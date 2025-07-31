#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram Bot for Math Course Registration
ربات تلگرام برای ثبت‌نام کلاس‌های ریاضی
"""

import json
import logging
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes, ConversationHandler

# Import configuration
from config import *

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, LOG_LEVEL)
)
logger = logging.getLogger(__name__)

# Conversation states
CHOOSING_ACTION, REGISTERING_NAME, REGISTERING_LASTNAME, REGISTERING_GRADE, REGISTERING_FIELD, REGISTERING_CITY, REGISTERING_PHONE = range(7)

class MathBot:
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
    
    def load_students(self):
        """Load students data from JSON file"""
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
    
    def save_student(self, student_data):
        """Save student data to JSON file"""
        students = self.load_students()
        students.append(student_data)
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(students, f, ensure_ascii=False, indent=2)
    
    def is_registered(self, user_id):
        """Check if user is already registered"""
        students = self.load_students()
        return any(student.get('telegram_id') == user_id for student in students)
    
    def setup_handlers(self):
        """Setup all bot handlers"""
        
        # Conversation handler for registration
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', self.start_command)],
            states={
                CHOOSING_ACTION: [
                    CallbackQueryHandler(self.handle_action_choice, pattern='^register$'),
                    CallbackQueryHandler(self.handle_action_choice, pattern='^menu$')
                ],
                REGISTERING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.register_name)],
                REGISTERING_LASTNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.register_lastname)],
                REGISTERING_GRADE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.register_grade)],
                REGISTERING_FIELD: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.register_field)],
                REGISTERING_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.register_city)],
                REGISTERING_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.register_phone)]
            },
            fallbacks=[CommandHandler('cancel', self.cancel_registration)]
        )
        
        self.application.add_handler(conv_handler)
        
        # Main menu handlers
        self.application.add_handler(CallbackQueryHandler(self.handle_menu_choice, pattern='^courses$'))
        self.application.add_handler(CallbackQueryHandler(self.handle_menu_choice, pattern='^book$'))
        self.application.add_handler(CallbackQueryHandler(self.handle_menu_choice, pattern='^contact$'))
        self.application.add_handler(CallbackQueryHandler(self.handle_menu_choice, pattern='^social$'))
        self.application.add_handler(CallbackQueryHandler(self.handle_menu_choice, pattern='^back_to_menu$'))
        
        # Error handler
        self.application.add_error_handler(self.error_handler)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        
        # Check if user is already registered
        if self.is_registered(user.id):
            await self.show_main_menu(update, context)
            return ConversationHandler.END
        
        # Welcome message for new users
        welcome_text = MESSAGES["welcome"].format(name=user.first_name) + """

لطفاً برای ادامه، گزینه زیر را انتخاب کنید:
        """
        
        keyboard = [
            [InlineKeyboardButton("📋 ثبت‌نام در کلاس‌ها", callback_data="register")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
        return CHOOSING_ACTION
    
    async def handle_action_choice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle action choice (register or menu)"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "register":
            await self.start_registration(update, context)
            return REGISTERING_NAME
        elif query.data == "menu":
            await self.show_main_menu(update, context)
            return ConversationHandler.END
    
    async def start_registration(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start the registration process"""
        query = update.callback_query
        await query.edit_message_text("لطفاً نام خود را وارد کنید:")
        return REGISTERING_NAME
    
    async def register_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Register student's first name"""
        context.user_data['name'] = update.message.text
        await update.message.reply_text("لطفاً نام خانوادگی خود را وارد کنید:")
        return REGISTERING_LASTNAME
    
    async def register_lastname(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Register student's last name"""
        context.user_data['lastname'] = update.message.text
        
        keyboard = [
            ["دهم"],
            ["یازدهم"],
            ["دوازدهم"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text("لطفاً پایه تحصیلی خود را انتخاب کنید:", reply_markup=reply_markup)
        return REGISTERING_GRADE
    
    async def register_grade(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Register student's grade"""
        context.user_data['grade'] = update.message.text
        
        keyboard = [
            ["ریاضی"],
            ["تجربی"],
            ["انسانی"],
            ["هنر"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text("لطفاً رشته تحصیلی خود را انتخاب کنید:", reply_markup=reply_markup)
        return REGISTERING_FIELD
    
    async def register_field(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Register student's field of study"""
        context.user_data['field'] = update.message.text
        await update.message.reply_text("لطفاً استان و شهر خود را وارد کنید (مثال: تهران - تهران):")
        return REGISTERING_CITY
    
    async def register_city(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Register student's city"""
        context.user_data['city'] = update.message.text
        
        # Create phone number keyboard
        keyboard = [[KeyboardButton("📱 ارسال شماره موبایل", request_contact=True)]]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text("لطفاً شماره موبایل خود را وارد کنید یا روی دکمه ارسال شماره کلیک کنید:", reply_markup=reply_markup)
        return REGISTERING_PHONE
    
    async def register_phone(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Register student's phone number"""
        if update.message.contact:
            phone = update.message.contact.phone_number
        else:
            phone = update.message.text
        
        context.user_data['phone'] = phone
        
        # Save student data
        student_data = {
            'telegram_id': update.effective_user.id,
            'name': context.user_data['name'],
            'lastname': context.user_data['lastname'],
            'grade': context.user_data['grade'],
            'field': context.user_data['field'],
            'city': context.user_data['city'],
            'phone': phone,
            'registration_date': datetime.now().isoformat()
        }
        
        self.save_student(student_data)
        
        # Remove keyboard
        await update.message.reply_text(MESSAGES["registration_success"], reply_markup=ReplyKeyboardMarkup([[]], resize_keyboard=True))
        
        # Show main menu
        await self.show_main_menu(update, context)
        return ConversationHandler.END
    
    async def cancel_registration(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel registration process"""
        await update.message.reply_text(MESSAGES["registration_cancelled"])
        return ConversationHandler.END
    
    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show main menu after registration"""
        menu_text = """
🏫 منوی اصلی ربات کلاس‌های ریاضی

لطفاً گزینه مورد نظر خود را انتخاب کنید:
        """
        
        keyboard = [
            [InlineKeyboardButton("🏫 دوره‌های آموزشی", callback_data="courses")],
            [InlineKeyboardButton("📘 کتاب انفجار خلاقیت ریاضی", callback_data="book")],
            [InlineKeyboardButton("📞 ارتباط با استاد", callback_data="contact")],
            [InlineKeyboardButton("🌐 شبکه‌های اجتماعی", callback_data="social")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(menu_text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(menu_text, reply_markup=reply_markup)
    
    async def handle_menu_choice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle main menu choices"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "courses":
            await self.show_courses(update, context)
        elif query.data == "book":
            await self.show_book_info(update, context)
        elif query.data == "contact":
            await self.show_contact_info(update, context)
        elif query.data == "social":
            await self.show_social_links(update, context)
        elif query.data == "back_to_menu":
            await self.show_main_menu(update, context)
    
    async def show_courses(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show available courses"""
        courses_text = "🏫 دوره‌های آموزشی موجود:\n\n"
        
        for grade, courses in COURSES.items():
            courses_text += f"📚 پایه {grade}:\n"
            for course_name, course_info in courses.items():
                price_formatted = f"{course_info['price']:,}".replace(',', '،')
                courses_text += f"• {course_name} - {course_info['type']}\n"
                courses_text += f"  مدت: {course_info['duration']}\n"
                courses_text += f"  💰 قیمت: {price_formatted} تومان\n\n"
        
        courses_text += "📞 برای ثبت‌نام در کلاس‌ها با استاد تماس بگیرید"
        
        keyboard = [[InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(courses_text, reply_markup=reply_markup)
    
    async def show_book_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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

📥 دانلود نسخه PDF: در دسترس نیست
📺 ویدیو معرفی: در دسترس نیست

📞 برای خرید کتاب با استاد تماس بگیرید
        """
        
        keyboard = [[InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(book_text, reply_markup=reply_markup)
    
    async def show_contact_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        
        await update.callback_query.edit_message_text(contact_text, reply_markup=reply_markup)
    
    async def show_social_links(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        
        await update.callback_query.edit_message_text(social_text, reply_markup=reply_markup)
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Exception while handling an update: {context.error}")
    
    async def run(self):
        """Run the bot"""
        print("🤖 ربات کلاس‌های ریاضی در حال اجرا...")
        print("📱 برای توقف ربات، Ctrl+C را فشار دهید")
        try:
            await self.application.run_polling(drop_pending_updates=True)
        except KeyboardInterrupt:
            print("\n⏹️ ربات متوقف شد.")
        except Exception as e:
            print(f"\n❌ خطا در اجرای ربات: {e}")
            logger.error(f"Bot runtime error: {e}")

if __name__ == "__main__":
    import asyncio
    
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ لطفاً توکن ربات خود را در فایل config.py وارد کنید")
        exit(1)
    
    bot = MathBot(BOT_TOKEN)
    asyncio.run(bot.run()) 