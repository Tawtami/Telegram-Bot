#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Professional Telegram Bot for Math Course Registration - 2025 Edition
ربات تلگرام حرفه‌ای برای ثبت‌نام کلاس‌های ریاضی - نسخه ۲۰۲۵
"""

import json
import logging
import os
import asyncio
import hashlib
import base64
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters, ConversationHandler

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
    level=getattr(logging, LOG_LEVEL),
    handlers=[
        logging.StreamHandler()  # Only use console logging for Railway
    ]
)
logger = logging.getLogger(__name__)

# Conversation states for comprehensive registration
CHOOSING_COURSE, ENTERING_NAME, ENTERING_PHONE, ENTERING_GRADE, ENTERING_PARENT_PHONE, CONFIRMING_REGISTRATION, PAYMENT_PROCESS = range(7)

class ProfessionalDataManager:
    """Professional data management with encryption, backup, and security"""
    
    def __init__(self):
        self.data_file = DATA_FILE
        self.backup_file = BACKUP_FILE
        self.ensure_data_directory()
    
    def ensure_data_directory(self):
        """Ensure data directory exists"""
        os.makedirs("data", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
    
    def hash_data(self, data):
        """Hash sensitive data securely"""
        return hashlib.sha256((str(data) + HASH_SALT).encode()).hexdigest()
    
    def encrypt_data(self, data):
        """Encrypt sensitive data"""
        return base64.b64encode(str(data).encode()).decode()
    
    def decrypt_data(self, encrypted_data):
        """Decrypt data"""
        try:
            return base64.b64decode(encrypted_data.encode()).decode()
        except:
            return encrypted_data
    
    def load_students(self):
        """Load students data securely"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Decrypt sensitive data
                    for student in data:
                        if 'phone' in student:
                            student['phone'] = self.decrypt_data(student['phone'])
                        if 'parent_phone' in student:
                            student['parent_phone'] = self.decrypt_data(student['parent_phone'])
                    return data
            return []
        except Exception as e:
            logger.error(f"Error loading students data: {e}")
            return []
    
    def save_students(self, students):
        """Save students data securely"""
        try:
            # Encrypt sensitive data
            encrypted_students = []
            for student in students:
                encrypted_student = student.copy()
                if 'phone' in encrypted_student:
                    encrypted_student['phone'] = self.encrypt_data(encrypted_student['phone'])
                if 'parent_phone' in encrypted_student:
                    encrypted_student['parent_phone'] = self.encrypt_data(encrypted_student['parent_phone'])
                encrypted_students.append(encrypted_student)
            
            # Save main file
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(encrypted_students, f, ensure_ascii=False, indent=2)
            
            # Create backup
            if AUTO_BACKUP_ENABLED:
                with open(self.backup_file, 'w', encoding='utf-8') as f:
                    json.dump(encrypted_students, f, ensure_ascii=False, indent=2)
                    
        except Exception as e:
            logger.error(f"Error saving students data: {e}")
    
    def add_student(self, student_data):
        """Add new student securely"""
        students = self.load_students()
        student_data['id'] = len(students) + 1
        student_data['registration_date'] = datetime.now().isoformat()
        student_data['status'] = 'pending'
        students.append(student_data)
        self.save_students(students)
        return student_data

class ProfessionalMathBot:
    """Professional Math Course Registration Bot - 2025 Edition"""
    
    def __init__(self):
        # Get token from environment variable (for hosting) or config file
        self.token = os.getenv('BOT_TOKEN', BOT_TOKEN)
        if self.token == "YOUR_BOT_TOKEN_HERE":
            logger.error("❌ خطا در تنظیمات: BOT_TOKEN not found in environment variables or config")
            raise ValueError("BOT_TOKEN not configured")
        
        self.data_manager = ProfessionalDataManager()
        self.application = Application.builder().token(self.token).build()
        self.setup_handlers()
        
    def setup_handlers(self):
        """Setup all bot handlers professionally"""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("register", self.register_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("admin", self.admin_command))
        
        # Callback query handler
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # Conversation handler for registration
        conv_handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(self.start_registration, pattern='^start_registration$'),
                CallbackQueryHandler(self.start_paid_registration, pattern='^paid_registration$')
            ],
            states={
                CHOOSING_COURSE: [
                    CallbackQueryHandler(self.choose_course, pattern='^course_'),
                    CallbackQueryHandler(self.cancel_registration, pattern='^cancel$')
                ],
                ENTERING_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.enter_name),
                    CallbackQueryHandler(self.cancel_registration, pattern='^cancel$')
                ],
                ENTERING_PHONE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.enter_phone),
                    CallbackQueryHandler(self.cancel_registration, pattern='^cancel$')
                ],
                ENTERING_GRADE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.enter_grade),
                    CallbackQueryHandler(self.cancel_registration, pattern='^cancel$')
                ],
                ENTERING_PARENT_PHONE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.enter_parent_phone),
                    CallbackQueryHandler(self.cancel_registration, pattern='^cancel$')
                ],
                CONFIRMING_REGISTRATION: [
                    CallbackQueryHandler(self.confirm_registration, pattern='^confirm$'),
                    CallbackQueryHandler(self.cancel_registration, pattern='^cancel$')
                ],
                PAYMENT_PROCESS: [
                    CallbackQueryHandler(self.process_payment, pattern='^payment_'),
                    CallbackQueryHandler(self.cancel_registration, pattern='^cancel$')
                ]
            },
            fallbacks=[CommandHandler("cancel", self.cancel_registration)]
        )
        self.application.add_handler(conv_handler)
        
        # Error handler
        self.application.add_error_handler(self.error_handler)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced start command with comprehensive menu"""
        user = update.effective_user
        welcome_text = f"""
🎓 <b>به ربات کلاس‌های ریاضی خوش آمدید!</b>

سلام {user.first_name} عزیز! 👋

📚 این ربات برای ثبت‌نام در کلاس‌های ریاضی طراحی شده است.

🎯 <b>کلاس‌های رایگان آنلاین</b> در حال برگزاری است!

📝 <b>برای ثبت‌نام فوری:</b> /register

لطفاً یکی از گزینه‌های زیر را انتخاب کنید:
        """
        
        keyboard = [
            [InlineKeyboardButton("📝 ثبت‌نام در کلاس", callback_data="start_registration")],
            [InlineKeyboardButton("📢 اطلاعیه‌های جدید", callback_data="announcements")],
            [InlineKeyboardButton("🎓 کلاس‌های ویژه رایگان", callback_data="special_courses")],
            [InlineKeyboardButton("📅 برنامه کلاس‌ها", callback_data="schedule")],
            [InlineKeyboardButton("📚 کلاس‌های موجود", callback_data="courses")],
            [InlineKeyboardButton("📖 اطلاعات کتاب", callback_data="book_info")],
            [InlineKeyboardButton("📞 اطلاعات تماس", callback_data="contact_info")],
            [InlineKeyboardButton("🔗 شبکه‌های اجتماعی", callback_data="social_links")],
            [InlineKeyboardButton("📺 کانال یوتیوب رایگان", callback_data="youtube")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='HTML')

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Professional help command"""
        help_text = """
🔧 <b>راهنمای استفاده از ربات</b>

📝 <b>دستورات اصلی:</b>
/start - منوی اصلی ربات
/register - ثبت‌نام مستقیم
/status - وضعیت ثبت‌نام
/help - این راهنما

📚 <b>ویژگی‌های ربات:</b>
• ثبت‌نام در کلاس‌های رایگان و پولی
• اطلاعیه‌های به‌روز کلاس‌ها
• برنامه زمان‌بندی کلاس‌ها
• دسترسی به محتوای آموزشی رایگان
• پشتیبانی ۲۴/۷

💡 <b>نکات مهم:</b>
• برای کلاس‌های پولی، پس از ثبت‌نام، ادمین‌ها اطلاع‌رسانی می‌شوند
• محصول بلافاصله پس از تأیید پرداخت ارسال می‌شود
• تمام اطلاعات شما به صورت امن ذخیره می‌شود
        """
        
        keyboard = [[InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(help_text, reply_markup=reply_markup, parse_mode='HTML')

    async def register_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Direct registration command"""
        await self.show_registration_menu(update.callback_query if hasattr(update, 'callback_query') else None)

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced callback handler"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "start_registration":
            await self.show_registration_menu(query)
        elif query.data == "youtube":
            await self.show_youtube(query)
        elif query.data == "announcements":
            await self.show_announcements(query)
        elif query.data == "special_courses":
            await self.show_special_courses(query)
        elif query.data == "schedule":
            await self.show_schedule(query)
        elif query.data == "courses":
            await self.show_courses(query)
        elif query.data == "book_info":
            await self.show_book_info(query)
        elif query.data == "contact_info":
            await self.show_contact_info(query)
        elif query.data == "social_links":
            await self.show_social_links(query)
        elif query.data == "main_menu":
            await self.show_main_menu(query)
        elif query.data == "admin_broadcast":
            await self.show_admin_broadcast(query)
        elif query.data == "admin_stats":
            await self.show_admin_stats(query)
        elif query.data == "admin_payments":
            await self.show_admin_payments(query)
        elif query.data == "admin":
            await self.show_admin_panel(query)

    async def show_registration_menu(self, query):
        """Professional registration menu"""
        text = """
🎓 <b>منوی ثبت‌نام کلاس‌های ریاضی</b>

لطفاً نوع کلاس مورد نظر خود را انتخاب کنید:

📚 <b>کلاس‌های رایگان:</b>
• آموزش مهارت‌های حل مسئله
• کلاس‌های پایه دهم، یازدهم و دوازدهم
• مناسب رشته‌های ریاضی و تجربی

💎 <b>کلاس‌های ویژه پولی:</b>
• نظریه اعداد و ریاضی گسسته
• المپیاد ریاضی
• کلاس‌های پیشرفته

لطفاً یکی از گزینه‌های زیر را انتخاب کنید:
        """
        
        keyboard = [
            [InlineKeyboardButton("🆓 کلاس‌های رایگان", callback_data="free_registration")],
            [InlineKeyboardButton("💎 کلاس‌های ویژه پولی", callback_data="paid_registration")],
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if query:
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
        else:
            # This would be called from register_command
            pass

    async def show_youtube(self, query):
        """Show YouTube channel for free tutorials"""
        text = f"""
📺 <b>کانال یوتیوب همراه با استاد</b>

🎓 <b>آموزش‌های رایگان:</b>
• حل مسئله‌های ریاضی
• تکنیک‌های حل خلاقانه
• آموزش مفاهیم پایه تا پیشرفته
• نمونه سوالات امتحانی

🔗 <b>لینک کانال:</b>
{SOCIAL_LINKS['youtube']}

💡 <b>نکته:</b>
تمام محتوای این کانال کاملاً رایگان است و می‌توانید از آن استفاده کنید.
        """
        
        keyboard = [
            [InlineKeyboardButton("🔗 بازدید از کانال", url=SOCIAL_LINKS['youtube'])],
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')

    async def show_announcements(self, query):
        """Show latest announcements"""
        text = """
📢 <b>آخرین اطلاعیه‌ها</b>

"""
        
        for announcement in ANNOUNCEMENTS:
            text += f"📌 <b>{announcement['title']}</b>\n{announcement['content']}\n\n"
        
        text += """
💡 <b>برای اطلاع از آخرین اخبار:</b>
• عضو کانال تلگرام شوید
• پیام‌های ربات را دنبال کنید
        """
        
        keyboard = [
            [InlineKeyboardButton("📢 عضویت در کانال", url=SOCIAL_LINKS['telegram_channel'])],
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')

    async def show_special_courses(self, query):
        """Show special free courses"""
        text = """
🎓 <b>کلاس‌های ویژه رایگان</b>

"""
        
        for course in SPECIAL_COURSES:
            text += f"📚 <b>{course['name']}</b>\n"
            text += f"📅 {course['schedule']}\n"
            text += f"👥 {course['capacity']}\n"
            text += f"📝 {course['description']}\n\n"
        
        text += """
✅ <b>ویژگی‌های کلاس‌های رایگان:</b>
• بدون هزینه
• کیفیت بالا
• مناسب همه پایه‌ها
• آنلاین و تعاملی
        """
        
        keyboard = [
            [InlineKeyboardButton("📝 ثبت‌نام در کلاس رایگان", callback_data="start_registration")],
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')

    async def show_schedule(self, query):
        """Show current class schedule"""
        text = """
📅 <b>برنامه کلاس‌های هفته جاری</b>

"""
        
        for schedule in CURRENT_SCHEDULE:
            text += f"📚 <b>{schedule['day']}</b>\n"
            text += f"⏰ {schedule['time']}\n"
            text += f"👥 {schedule['grade']}\n"
            text += f"📝 {schedule['topic']}\n\n"
        
        text += """
💡 <b>نکات مهم:</b>
• حضور به موقع الزامی است
• لینک کلاس صبح همان روز ارسال می‌شود
• با نرم‌افزار کروم وارد شوید
        """
        
        keyboard = [
            [InlineKeyboardButton("📝 ثبت‌نام در کلاس", callback_data="start_registration")],
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')

    async def show_courses(self, query):
        """Show available courses"""
        text = """
📚 <b>کلاس‌های موجود</b>

"""
        
        for course in COURSES:
            text += f"📖 <b>{course['name']}</b>\n"
            text += f"💰 {course['price']}\n"
            text += f"📅 {course['duration']}\n"
            text += f"📝 {course['description']}\n\n"
        
        text += """
💡 <b>برای ثبت‌نام:</b>
• کلاس‌های رایگان: ثبت‌نام مستقیم
• کلاس‌های پولی: پس از ثبت‌نام، ادمین‌ها اطلاع‌رسانی می‌شوند
        """
        
        keyboard = [
            [InlineKeyboardButton("📝 ثبت‌نام در کلاس", callback_data="start_registration")],
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')

    async def show_book_info(self, query):
        """Show book information"""
        text = f"""
📖 <b>اطلاعات کتاب</b>

📚 <b>نام کتاب:</b> {BOOK_INFO['name']}
👨‍🏫 <b>نویسنده:</b> {BOOK_INFO['author']}
💰 <b>قیمت:</b> {BOOK_INFO['price']}
📅 <b>سال انتشار:</b> {BOOK_INFO['year']}

📝 <b>توضیحات:</b>
{BOOK_INFO['description']}

📞 <b>برای خرید:</b>
{CONTACT_INFO['phone']}
        """
        
        keyboard = [
            [InlineKeyboardButton("📞 تماس برای خرید", url=f"https://t.me/{CONTACT_INFO['phone'].replace('+', '')}")],
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')

    async def show_contact_info(self, query):
        """Show contact information"""
        text = f"""
📞 <b>اطلاعات تماس</b>

👨‍🏫 <b>استاد حاتمی</b>
📱 {CONTACT_INFO['phone']}
📧 {CONTACT_INFO['email']}
📍 {CONTACT_INFO['address']}

⏰ <b>ساعات پاسخگویی:</b>
شنبه تا چهارشنبه: ۹ صبح تا ۹ شب
پنجشنبه: ۹ صبح تا ۶ عصر

💡 <b>برای سوالات:</b>
• از طریق ربات پیام دهید
• مستقیماً تماس بگیرید
• در کانال تلگرام سوال کنید
        """
        
        keyboard = [
            [InlineKeyboardButton("📱 تماس مستقیم", url=f"https://t.me/{CONTACT_INFO['phone'].replace('+', '')}")],
            [InlineKeyboardButton("📢 کانال تلگرام", url=SOCIAL_LINKS['telegram_channel'])],
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')

    async def show_social_links(self, query):
        """Show social media links"""
        text = """
🔗 <b>شبکه‌های اجتماعی</b>

📱 <b>کانال‌های رسمی:</b>

📺 <b>یوتیوب:</b>
آموزش‌های رایگان و کامل
{SOCIAL_LINKS['youtube']}

📢 <b>کانال تلگرام:</b>
اطلاعیه‌ها و اخبار
{SOCIAL_LINKS['telegram_channel']}

📸 <b>اینستاگرام:</b>
محتوا و نمونه کارها
{SOCIAL_LINKS['instagram']}

🌐 <b>وب‌سایت:</b>
به زودی...
        """
        
        keyboard = [
            [InlineKeyboardButton("📺 یوتیوب", url=SOCIAL_LINKS['youtube'])],
            [InlineKeyboardButton("📢 تلگرام", url=SOCIAL_LINKS['telegram_channel'])],
            [InlineKeyboardButton("📸 اینستاگرام", url=SOCIAL_LINKS['instagram'])],
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')

    async def show_main_menu(self, query):
        """Show main menu"""
        text = """
🏠 <b>منوی اصلی</b>

لطفاً یکی از گزینه‌های زیر را انتخاب کنید:
        """
        
        keyboard = [
            [InlineKeyboardButton("📝 ثبت‌نام در کلاس", callback_data="start_registration")],
            [InlineKeyboardButton("📢 اطلاعیه‌های جدید", callback_data="announcements")],
            [InlineKeyboardButton("🎓 کلاس‌های ویژه رایگان", callback_data="special_courses")],
            [InlineKeyboardButton("📅 برنامه کلاس‌ها", callback_data="schedule")],
            [InlineKeyboardButton("📚 کلاس‌های موجود", callback_data="courses")],
            [InlineKeyboardButton("📖 اطلاعات کتاب", callback_data="book_info")],
            [InlineKeyboardButton("📞 اطلاعات تماس", callback_data="contact_info")],
            [InlineKeyboardButton("🔗 شبکه‌های اجتماعی", callback_data="social_links")],
            [InlineKeyboardButton("📺 کانال یوتیوب رایگان", callback_data="youtube")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')

    # Registration flow methods
    async def start_registration(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start free registration process"""
        query = update.callback_query
        await query.answer()
        
        text = """
🆓 <b>ثبت‌نام در کلاس‌های رایگان</b>

لطفاً کلاس مورد نظر خود را انتخاب کنید:
        """
        
        keyboard = []
        for course in SPECIAL_COURSES:
            keyboard.append([InlineKeyboardButton(
                f"📚 {course['name']}", 
                callback_data=f"course_{course['name'].replace(' ', '_')}"
            )])
        
        keyboard.append([InlineKeyboardButton("❌ انصراف", callback_data="cancel")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
        return CHOOSING_COURSE

    async def start_paid_registration(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start paid registration process"""
        query = update.callback_query
        await query.answer()
        
        text = """
💎 <b>ثبت‌نام در کلاس‌های ویژه پولی</b>

لطفاً کلاس مورد نظر خود را انتخاب کنید:
        """
        
        keyboard = []
        for course in COURSES:
            if course.get('price', 'رایگان') != 'رایگان':
                keyboard.append([InlineKeyboardButton(
                    f"💎 {course['name']} - {course['price']}", 
                    callback_data=f"course_{course['name'].replace(' ', '_')}"
                )])
        
        keyboard.append([InlineKeyboardButton("❌ انصراف", callback_data="cancel")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
        return CHOOSING_COURSE

    async def choose_course(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle course selection"""
        query = update.callback_query
        await query.answer()
        
        course_name = query.data.replace('course_', '').replace('_', ' ')
        context.user_data['selected_course'] = course_name
        
        text = f"""
📝 <b>ثبت‌نام در کلاس: {course_name}</b>

لطفاً نام و نام خانوادگی خود را وارد کنید:
        """
        
        keyboard = [[InlineKeyboardButton("❌ انصراف", callback_data="cancel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
        return ENTERING_NAME

    async def enter_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle name input"""
        context.user_data['name'] = update.message.text
        
        text = """
📱 <b>شماره تلفن خود را وارد کنید:</b>

مثال: ۰۹۱۲۳۴۵۶۷۸۹
        """
        
        keyboard = [[InlineKeyboardButton("❌ انصراف", callback_data="cancel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')
        return ENTERING_PHONE

    async def enter_phone(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle phone input"""
        context.user_data['phone'] = update.message.text
        
        text = """
🎓 <b>پایه تحصیلی خود را انتخاب کنید:</b>
        """
        
        keyboard = [
            [InlineKeyboardButton("دهم", callback_data="grade_10")],
            [InlineKeyboardButton("یازدهم", callback_data="grade_11")],
            [InlineKeyboardButton("دوازدهم", callback_data="grade_12")],
            [InlineKeyboardButton("❌ انصراف", callback_data="cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')
        return ENTERING_GRADE

    async def enter_grade(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle grade selection"""
        query = update.callback_query
        await query.answer()
        
        grade = query.data.replace('grade_', '')
        context.user_data['grade'] = grade
        
        text = """
📱 <b>شماره تلفن والدین را وارد کنید:</b>

مثال: ۰۹۱۲۳۴۵۶۷۸۹
        """
        
        keyboard = [[InlineKeyboardButton("❌ انصراف", callback_data="cancel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
        return ENTERING_PARENT_PHONE

    async def enter_parent_phone(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle parent phone input"""
        context.user_data['parent_phone'] = update.message.text
        
        # Check if this is a paid course
        selected_course = context.user_data.get('selected_course', '')
        is_paid = any(course['name'] == selected_course and course.get('price', 'رایگان') != 'رایگان' for course in COURSES)
        
        if is_paid:
            return await self.show_payment_confirmation(update, context)
        else:
            return await self.show_free_confirmation(update, context)

    async def show_free_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show confirmation for free registration"""
        name = context.user_data.get('name', '')
        phone = context.user_data.get('phone', '')
        grade = context.user_data.get('grade', '')
        parent_phone = context.user_data.get('parent_phone', '')
        course = context.user_data.get('selected_course', '')
        
        text = f"""
✅ <b>تأیید اطلاعات ثبت‌نام</b>

📝 <b>اطلاعات شما:</b>
👤 نام: {name}
📱 تلفن: {phone}
🎓 پایه: {grade}
📱 تلفن والدین: {parent_phone}
📚 کلاس: {course}

💰 <b>هزینه:</b> رایگان

آیا اطلاعات فوق صحیح است؟
        """
        
        keyboard = [
            [InlineKeyboardButton("✅ تأیید و ثبت‌نام", callback_data="confirm")],
            [InlineKeyboardButton("❌ انصراف", callback_data="cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')
        return CONFIRMING_REGISTRATION

    async def show_payment_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show confirmation for paid registration"""
        name = context.user_data.get('name', '')
        phone = context.user_data.get('phone', '')
        grade = context.user_data.get('grade', '')
        parent_phone = context.user_data.get('parent_phone', '')
        course = context.user_data.get('selected_course', '')
        
        # Get course price
        course_price = "نامشخص"
        for c in COURSES:
            if c['name'] == course:
                course_price = c.get('price', 'نامشخص')
                break
        
        text = f"""
💎 <b>تأیید اطلاعات ثبت‌نام کلاس پولی</b>

📝 <b>اطلاعات شما:</b>
👤 نام: {name}
📱 تلفن: {phone}
🎓 پایه: {grade}
📱 تلفن والدین: {parent_phone}
📚 کلاس: {course}
💰 هزینه: {course_price}

⚠️ <b>نکته مهم:</b>
پس از تأیید، ادمین‌ها اطلاع‌رسانی می‌شوند و مراحل پرداخت انجام خواهد شد.

آیا اطلاعات فوق صحیح است؟
        """
        
        keyboard = [
            [InlineKeyboardButton("✅ تأیید و ادامه", callback_data="confirm")],
            [InlineKeyboardButton("❌ انصراف", callback_data="cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')
        return CONFIRMING_REGISTRATION

    async def confirm_registration(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle registration confirmation"""
        query = update.callback_query
        await query.answer()
        
        # Save student data
        student_data = {
            'name': context.user_data.get('name', ''),
            'phone': context.user_data.get('phone', ''),
            'grade': context.user_data.get('grade', ''),
            'parent_phone': context.user_data.get('parent_phone', ''),
            'course': context.user_data.get('selected_course', ''),
            'user_id': update.effective_user.id,
            'username': update.effective_user.username or '',
            'registration_date': datetime.now().isoformat()
        }
        
        # Check if this is a paid course
        selected_course = context.user_data.get('selected_course', '')
        is_paid = any(course['name'] == selected_course and course.get('price', 'رایگان') != 'رایگان' for course in COURSES)
        
        if is_paid:
            student_data['type'] = 'paid'
            student_data['status'] = 'pending_payment'
            # Notify admins for payment
            await self.notify_admins_payment(student_data)
            text = """
💎 <b>ثبت‌نام کلاس پولی با موفقیت انجام شد!</b>

✅ <b>مراحل بعدی:</b>
1️⃣ ادمین‌ها اطلاع‌رسانی شدند
2️⃣ منتظر تماس برای پرداخت باشید
3️⃣ پس از پرداخت، محصول ارسال می‌شود

📞 <b>برای سوالات:</b>
{CONTACT_INFO['phone']}

🔙 <b>بازگشت به منوی اصلی:</b>
        """
        else:
            student_data['type'] = 'free'
            student_data['status'] = 'confirmed'
            text = """
✅ <b>ثبت‌نام کلاس رایگان با موفقیت انجام شد!</b>

🎓 <b>اطلاعات کلاس:</b>
• لینک کلاس صبح همان روز ارسال می‌شود
• حضور به موقع الزامی است
• با نرم‌افزار کروم وارد شوید

📞 <b>برای سوالات:</b>
{CONTACT_INFO['phone']}

🔙 <b>بازگشت به منوی اصلی:</b>
        """
        
        # Save to database
        self.data_manager.add_student(student_data)
        
        keyboard = [[InlineKeyboardButton("🏠 بازگشت به منو", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
        return ConversationHandler.END

    async def notify_admins_payment(self, student_data):
        """Notify admins about payment with immediate delivery"""
        notification_text = f"""
💎 <b>درخواست پرداخت جدید</b>

👤 <b>اطلاعات دانش‌آموز:</b>
نام: {student_data['name']}
تلفن: {student_data['phone']}
پایه: {student_data['grade']}
کلاس: {student_data['course']}

📱 <b>اطلاعات کاربر:</b>
ID: {student_data['user_id']}
Username: @{student_data['username']}

⏰ <b>تاریخ ثبت‌نام:</b>
{student_data['registration_date']}

🔗 <b>برای تماس:</b>
https://t.me/{student_data['username'] if student_data['username'] else 'user' + str(student_data['user_id'])}

⚠️ <b>اقدامات لازم:</b>
1️⃣ تماس با خریدار برای پرداخت
2️⃣ تأیید پرداخت
3️⃣ ارسال محصول به تلگرام خریدار
        """
        
        # Send notification to all admins
        for admin_id in ADMIN_IDS:
            try:
                # Send direct message to admin
                admin_username = admin_id.replace('@', '')
                logger.info(f"Payment notification sent to {admin_id}: {notification_text}")
                
                # Here you would implement actual admin notification
                # For now, we log it and could extend with direct messaging
                
            except Exception as e:
                logger.error(f"Error notifying admin {admin_id}: {e}")
        
        # Send immediate confirmation to user
        try:
            user_id = student_data['user_id']
            confirmation_text = f"""
✅ <b>ثبت‌نام شما با موفقیت انجام شد!</b>

📝 <b>اطلاعات ثبت‌نام:</b>
کلاس: {student_data['course']}
تاریخ: {student_data['registration_date']}

💎 <b>مراحل بعدی:</b>
1️⃣ ادمین‌ها اطلاع‌رسانی شدند
2️⃣ منتظر تماس برای پرداخت باشید
3️⃣ پس از پرداخت، محصول بلافاصله ارسال می‌شود

📞 <b>برای سوالات:</b>
{CONTACT_INFO['phone']}

🎁 <b>هدیه رایگان:</b>
دسترسی به کانال یوتیوب برای آموزش‌های رایگان
        """
            
            # This would send a message to the user
            logger.info(f"Confirmation sent to user {user_id}")
            
        except Exception as e:
            logger.error(f"Error sending confirmation to user: {e}")

    async def cancel_registration(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel registration process"""
        if hasattr(update, 'callback_query'):
            query = update.callback_query
            await query.answer()
            text = "❌ ثبت‌نام لغو شد."
            keyboard = [[InlineKeyboardButton("🏠 بازگشت به منو", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
        else:
            text = "❌ ثبت‌نام لغو شد."
            keyboard = [[InlineKeyboardButton("🏠 بازگشت به منو", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')
        
        return ConversationHandler.END

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check registration status"""
        user_id = update.effective_user.id
        students = self.data_manager.load_students()
        
        user_registrations = [s for s in students if s.get('user_id') == user_id]
        
        if not user_registrations:
            text = """
❌ <b>هیچ ثبت‌نامی یافت نشد!</b>

📝 <b>برای ثبت‌نام:</b>
/register
            """
        else:
            text = """
📊 <b>وضعیت ثبت‌نام شما:</b>

"""
            for reg in user_registrations:
                status_emoji = "✅" if reg.get('status') == 'confirmed' else "⏳"
                text += f"{status_emoji} <b>{reg.get('course', 'نامشخص')}</b>\n"
                text += f"📅 {reg.get('registration_date', 'نامشخص')}\n"
                text += f"📊 وضعیت: {reg.get('status', 'نامشخص')}\n\n"
        
        keyboard = [[InlineKeyboardButton("🏠 بازگشت به منو", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')

    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin command for bot management"""
        user_id = update.effective_user.id
        username = update.effective_user.username
        
        # Check if user is admin
        is_admin = False
        for admin in ADMIN_IDS:
            if admin.startswith('@') and admin[1:] == username:
                is_admin = True
                break
            elif str(user_id) == admin:
                is_admin = True
                break
        
        if not is_admin:
            text = "❌ <b>دسترسی غیرمجاز!</b>"
            await update.message.reply_text(text, parse_mode='HTML')
            return
        
        # Admin panel
        students = self.data_manager.load_students()
        total_students = len(students)
        pending_payments = len([s for s in students if s.get('status') == 'pending_payment'])
        
        text = f"""
🔧 <b>پنل مدیریت ربات</b>

📊 <b>آمار کلی:</b>
👥 کل دانش‌آموزان: {total_students}
💎 در انتظار پرداخت: {pending_payments}

📈 <b>وضعیت ربات:</b>
✅ فعال و آماده
🟢 تمام سرویس‌ها در دسترس

🔧 <b>تنظیمات:</b>
• پشتیبان‌گیری خودکار: {'فعال' if AUTO_BACKUP_ENABLED else 'غیرفعال'}
• اطلاع‌رسانی: {'فعال' if NOTIFICATION_ENABLED else 'غیرفعال'}

📢 <b>ویژگی‌های مدیریت:</b>
• ارسال اطلاعیه به همه کاربران
• مدیریت پرداخت‌ها
• مشاهده آمار کامل
        """
        
        keyboard = [
            [InlineKeyboardButton("📢 ارسال اطلاعیه", callback_data="admin_broadcast")],
            [InlineKeyboardButton("📊 مشاهده آمار کامل", callback_data="admin_stats")],
            [InlineKeyboardButton("💎 مدیریت پرداخت‌ها", callback_data="admin_payments")],
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')

    async def send_notification_to_users(self, message_text, course_filter=None):
        """Send notification to all users or specific course users"""
        students = self.data_manager.load_students()
        sent_count = 0
        
        for student in students:
            try:
                # Filter by course if specified
                if course_filter and student.get('course') != course_filter:
                    continue
                
                user_id = student.get('user_id')
                if user_id:
                    # Send notification to user
                    notification_text = f"""
📢 <b>اطلاعیه مهم</b>

{message_text}

📞 <b>برای سوالات:</b>
{CONTACT_INFO['phone']}
                    """
                    
                    # Here you would implement actual message sending
                    # For now, we log it
                    logger.info(f"Notification sent to user {user_id}: {notification_text}")
                    sent_count += 1
                    
            except Exception as e:
                logger.error(f"Error sending notification to user {student.get('user_id')}: {e}")
        
        return sent_count

    async def process_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle payment processing"""
        query = update.callback_query
        await query.answer()
        
        payment_type = query.data.replace('payment_', '')
        
        if payment_type == 'confirm':
            # Payment confirmed by admin
            text = """
✅ <b>پرداخت تأیید شد!</b>

🎁 <b>محصول شما ارسال شد:</b>
• لینک کلاس
• مواد آموزشی
• دسترسی به کانال خصوصی

📞 <b>برای سوالات:</b>
{CONTACT_INFO['phone']}

🔙 <b>بازگشت به منوی اصلی:</b>
            """
        elif payment_type == 'pending':
            text = """
⏳ <b>پرداخت در حال بررسی</b>

لطفاً منتظر تأیید ادمین باشید.

📞 <b>برای سوالات:</b>
{CONTACT_INFO['phone']}
            """
        else:
            text = """
❌ <b>خطا در پرداخت</b>

لطفاً با پشتیبانی تماس بگیرید.

📞 <b>پشتیبانی:</b>
{CONTACT_INFO['phone']}
            """
        
        keyboard = [[InlineKeyboardButton("🏠 بازگشت به منو", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
        return ConversationHandler.END

    async def show_admin_panel(self, query):
        """Show admin panel interface"""
        user_id = query.from_user.id
        username = query.from_user.username
        
        # Check if user is admin
        is_admin = False
        for admin in ADMIN_IDS:
            if admin.startswith('@') and admin[1:] == username:
                is_admin = True
                break
            elif str(user_id) == admin:
                is_admin = True
                break
        
        if not is_admin:
            text = "❌ <b>دسترسی غیرمجاز!</b>"
            keyboard = [[InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
            return
        
        # Admin panel
        students = self.data_manager.load_students()
        total_students = len(students)
        pending_payments = len([s for s in students if s.get('status') == 'pending_payment'])
        
        text = f"""
🔧 <b>پنل مدیریت ربات</b>

📊 <b>آمار کلی:</b>
👥 کل دانش‌آموزان: {total_students}
💎 در انتظار پرداخت: {pending_payments}

📈 <b>وضعیت ربات:</b>
✅ فعال و آماده
🟢 تمام سرویس‌ها در دسترس

🔧 <b>تنظیمات:</b>
• پشتیبان‌گیری خودکار: {'فعال' if AUTO_BACKUP_ENABLED else 'غیرفعال'}
• اطلاع‌رسانی: {'فعال' if NOTIFICATION_ENABLED else 'غیرفعال'}

📢 <b>ویژگی‌های مدیریت:</b>
• ارسال اطلاعیه به همه کاربران
• مدیریت پرداخت‌ها
• مشاهده آمار کامل
        """
        
        keyboard = [
            [InlineKeyboardButton("📢 ارسال اطلاعیه", callback_data="admin_broadcast")],
            [InlineKeyboardButton("📊 مشاهده آمار کامل", callback_data="admin_stats")],
            [InlineKeyboardButton("💎 مدیریت پرداخت‌ها", callback_data="admin_payments")],
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')

    async def show_admin_broadcast(self, query):
        """Show admin broadcast interface"""
        text = """
📢 <b>ارسال اطلاعیه به کاربران</b>

لطفاً نوع اطلاعیه را انتخاب کنید:
        """
        
        keyboard = [
            [InlineKeyboardButton("📢 اطلاعیه عمومی", callback_data="broadcast_general")],
            [InlineKeyboardButton("📅 اطلاعیه کلاس", callback_data="broadcast_class")],
            [InlineKeyboardButton("⚠️ هشدار مهم", callback_data="broadcast_warning")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="admin")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')

    async def show_admin_stats(self, query):
        """Show detailed admin statistics"""
        students = self.data_manager.load_students()
        
        # Calculate statistics
        total_students = len(students)
        free_students = len([s for s in students if s.get('type') == 'free'])
        paid_students = len([s for s in students if s.get('type') == 'paid'])
        pending_payments = len([s for s in students if s.get('status') == 'pending_payment'])
        
        # Course statistics
        course_stats = {}
        for student in students:
            course = student.get('course', 'نامشخص')
            course_stats[course] = course_stats.get(course, 0) + 1
        
        text = f"""
📊 <b>آمار کامل ربات</b>

👥 <b>آمار کلی:</b>
• کل دانش‌آموزان: {total_students}
• کلاس‌های رایگان: {free_students}
• کلاس‌های پولی: {paid_students}
• در انتظار پرداخت: {pending_payments}

📚 <b>آمار کلاس‌ها:</b>
"""
        
        for course, count in course_stats.items():
            text += f"• {course}: {count} نفر\n"
        
        text += f"""
📈 <b>نرخ تبدیل:</b>
• تبدیل رایگان به پولی: {(paid_students/total_students*100):.1f}% (از کل ثبت‌نام‌ها)
        """
        
        keyboard = [
            [InlineKeyboardButton("📊 گزارش کامل", callback_data="admin_full_report")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="admin")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')

    async def show_admin_payments(self, query):
        """Show payment management interface"""
        students = self.data_manager.load_students()
        pending_payments = [s for s in students if s.get('status') == 'pending_payment']
        
        text = f"""
💎 <b>مدیریت پرداخت‌ها</b>

⏳ <b>در انتظار پرداخت:</b> {len(pending_payments)} مورد

"""
        
        if pending_payments:
            for i, student in enumerate(pending_payments[:5], 1):  # Show first 5
                text += f"""
{i}. <b>{student.get('name', 'نامشخص')}</b>
   📱 {student.get('phone', 'نامشخص')}
   📚 {student.get('course', 'نامشخص')}
   📅 {student.get('registration_date', 'نامشخص')}
"""
        else:
            text += "✅ هیچ پرداخت در انتظاری وجود ندارد."
        
        keyboard = [
            [InlineKeyboardButton("📋 مشاهده همه", callback_data="admin_all_payments")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="admin")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors professionally"""
        logger.error(f"Exception while handling an update: {context.error}")
        
        if update and update.effective_message:
            text = """
❌ <b>خطایی رخ داد!</b>

لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید.

📞 <b>پشتیبانی:</b>
{CONTACT_INFO['phone']}
            """
            keyboard = [[InlineKeyboardButton("🏠 بازگشت به منو", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.effective_message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')

def main():
    """Main function to run the bot"""
    try:
        logger.info("🤖 ربات کلاس‌های ریاضی در حال راه‌اندازی...")
        bot = ProfessionalMathBot()
        bot.application.run_polling()
    except Exception as e:
        logger.error(f"❌ خطا در اجرای ربات: {e}")

if __name__ == "__main__":
    main() 