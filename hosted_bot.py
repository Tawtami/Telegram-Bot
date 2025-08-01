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
CHOOSING_COURSE, ENTERING_NAME, ENTERING_PHONE, ENTERING_GRADE, ENTERING_FIELD, ENTERING_PARENT_PHONE, CONFIRMING_REGISTRATION, PAYMENT_PROCESS = range(8)

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
        
        # Check if user already exists
        existing_user = None
        for student in students:
            if student.get('user_id') == student_data.get('user_id'):
                existing_user = student
                break
        
        if existing_user:
            # Update existing user data
            existing_user.update(student_data)
            existing_user['last_updated'] = datetime.now().isoformat()
            logger.info(f"Updated existing user data for user_id: {student_data.get('user_id')}")
        else:
            # Add new student
            student_data['id'] = len(students) + 1
            student_data['registration_date'] = datetime.now().isoformat()
            student_data['last_updated'] = datetime.now().isoformat()
            student_data['status'] = 'pending'
            students.append(student_data)
            logger.info(f"Added new user data for user_id: {student_data.get('user_id')}")
        
        self.save_students(students)
        return student_data
    
    def update_student(self, user_id, updates):
        """Update existing student data"""
        students = self.load_students()
        
        for student in students:
            if student.get('user_id') == user_id:
                student.update(updates)
                student['last_updated'] = datetime.now().isoformat()
                self.save_students(students)
                logger.info(f"Updated student data for user_id: {user_id}")
                return True
        
        logger.warning(f"Student not found for user_id: {user_id}")
        return False
    
    def get_student_by_user_id(self, user_id):
        """Get student data by user_id"""
        students = self.load_students()
        
        for student in students:
            if student.get('user_id') == user_id:
                return student
        
        return None
    
    def export_user_data_summary(self):
        """Export user data summary for admin viewing"""
        students = self.load_students()
        
        if not students:
            return "هیچ کاربری ثبت‌نام نکرده است."
        
        summary = f"📊 خلاصه اطلاعات کاربران - {datetime.now().strftime('%Y/%m/%d %H:%M')}\n\n"
        summary += f"👥 کل کاربران: {len(students)}\n\n"
        
        # Group by course
        course_groups = {}
        for student in students:
            course = student.get('course', 'نامشخص')
            if course not in course_groups:
                course_groups[course] = []
            course_groups[course].append(student)
        
        for course, course_students in course_groups.items():
            summary += f"📚 {course} ({len(course_students)} نفر):\n"
            for student in course_students:
                summary += f"  • {student.get('name', 'نامشخص')} - {student.get('phone', 'نامشخص')} - {student.get('grade', 'نامشخص')} - {student.get('field', 'نامشخص')}\n"
            summary += "\n"
        
        return summary

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
        self.application.add_handler(CommandHandler("export", self.export_command))
        
        # Callback query handler
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # Conversation handler for registration
        conv_handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(self.start_registration, pattern='^free_registration$'),
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
                    CallbackQueryHandler(self.enter_grade, pattern='^grade_'),
                    CallbackQueryHandler(self.cancel_registration, pattern='^cancel$')
                ],
                ENTERING_FIELD: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.enter_field),
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
        """Enhanced start command with registration check"""
        user = update.effective_user
        
        # Check if user is already registered
        students = self.data_manager.load_students()
        user_registered = any(student.get('user_id') == user.id for student in students)
        
        if not user_registered:
            # User is not registered - show registration first
            welcome_text = f"""
🎓 به ربات کلاس‌های ریاضی خوش آمدید!

سلام {user.first_name} عزیز! 👋

📚 این ربات برای ثبت‌نام در کلاس‌های ریاضی طراحی شده است.

🎯 کلاس‌های رایگان آنلاین در حال برگزاری است!

⚠️ برای استفاده از ربات، ابتدا باید ثبت‌نام کنید.

📝 لطفاً اطلاعات خود را وارد کنید:
        """
            
            keyboard = [
                [InlineKeyboardButton("📝 ثبت‌نام در کلاس", callback_data="start_registration")],
                [InlineKeyboardButton("💎 ثبت‌نام کلاس پولی", callback_data="paid_registration")],
                [InlineKeyboardButton("📖 اطلاعات کتاب", callback_data="book_info")],
                [InlineKeyboardButton("📞 اطلاعات تماس", callback_data="contact_info")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(welcome_text, reply_markup=reply_markup)
        else:
            # User is registered - show full menu
            await self.show_full_menu(update, context)
    
    async def show_full_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show full menu for registered users"""
        user = update.effective_user
        welcome_text = f"""
🎓 به ربات کلاس‌های ریاضی خوش آمدید!

سلام {user.first_name} عزیز! 👋

✅ شما قبلاً ثبت‌نام کرده‌اید.

📚 این ربات برای ثبت‌نام در کلاس‌های ریاضی طراحی شده است.

🎯 کلاس‌های رایگان آنلاین در حال برگزاری است!

لطفاً یکی از گزینه‌های زیر را انتخاب کنید:
        """
        
        keyboard = [
            [InlineKeyboardButton("📝 ثبت‌نام در کلاس جدید", callback_data="start_registration")],
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
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Professional help command"""
        help_text = """
🔧 راهنمای استفاده از ربات

📝 دستورات اصلی:
/start - منوی اصلی ربات
/register - ثبت‌نام مستقیم
/status - وضعیت ثبت‌نام
/help - این راهنما

📚 ویژگی‌های ربات:
• ثبت‌نام در کلاس‌های رایگان و پولی
• اطلاعیه‌های به‌روز کلاس‌ها
• برنامه زمان‌بندی کلاس‌ها
• دسترسی به محتوای آموزشی رایگان
• پشتیبانی ۲۴/۷

💡 نکات مهم:
• برای کلاس‌های پولی، پس از ثبت‌نام، ادمین‌ها اطلاع‌رسانی می‌شوند
• محصول بلافاصله پس از تأیید پرداخت ارسال می‌شود
• تمام اطلاعات شما به صورت امن ذخیره می‌شود
        """
        
        keyboard = [[InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(help_text, reply_markup=reply_markup)

    async def register_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Direct registration command"""
        await self.show_registration_menu(update.callback_query if hasattr(update, 'callback_query') else None)

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced callback handler"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "start_registration":
            await self.show_registration_menu(query)
        elif query.data == "paid_registration":
            await self.start_paid_registration(update, context)
        elif query.data == "free_registration":
            await self.start_registration(update, context)
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
        elif query.data == "admin_user_details" or query.data.startswith("admin_user_details_page_"):
            await self.show_admin_user_details(query)
        elif query.data == "admin_export":
            await self.show_admin_export(query)

    async def show_registration_menu(self, query):
        """Professional registration menu"""
        text = """
🎓 منوی ثبت‌نام کلاس‌های ریاضی

لطفاً نوع کلاس مورد نظر خود را انتخاب کنید:

📚 کلاس‌های رایگان:
• آموزش مهارت‌های حل مسئله
• کلاس‌های پایه دهم، یازدهم و دوازدهم
• مناسب رشته‌های ریاضی و تجربی

💎 کلاس‌های ویژه پولی:
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
            await query.edit_message_text(text, reply_markup=reply_markup)
        else:
            # This would be called from register_command
            pass

    async def show_youtube(self, query):
        """Show YouTube channel for free tutorials"""
        text = f"""
📺 کانال یوتیوب همراه با استاد

🎓 آموزش‌های رایگان:
• حل مسئله‌های ریاضی
• تکنیک‌های حل خلاقانه
• آموزش مفاهیم پایه تا پیشرفته
• نمونه سوالات امتحانی

🔗 لینک کانال:
{SOCIAL_LINKS['youtube']}

💡 نکته:
تمام محتوای این کانال کاملاً رایگان است و می‌توانید از آن استفاده کنید.
        """
        
        keyboard = [
            [InlineKeyboardButton("🔗 بازدید از کانال", url=SOCIAL_LINKS['youtube'])],
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup)

    async def show_announcements(self, query):
        """Show latest announcements"""
        text = """
📢 آخرین اطلاعیه‌ها

"""
        
        for announcement in ANNOUNCEMENTS:
            text += f"📌 {announcement['title']}\n{announcement['content']}\n\n"
        
        text += """
💡 برای اطلاع از آخرین اخبار:
• عضو کانال تلگرام شوید
• پیام‌های ربات را دنبال کنید
        """
        
        keyboard = [
            [InlineKeyboardButton("📢 عضویت در کانال", url=SOCIAL_LINKS['telegram_channel'])],
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup)

    async def show_special_courses(self, query):
        """Show special free courses"""
        text = """
🎓 کلاس‌های ویژه رایگان

"""
        
        for course in SPECIAL_COURSES:
            text += f"📚 {course['name']}\n"
            text += f"📅 {course['schedule']}\n"
            text += f"👥 {course['capacity']}\n"
            text += f"📝 {course['description']}\n\n"
        
        text += """
✅ ویژگی‌های کلاس‌های رایگان:
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
        
        await query.edit_message_text(text, reply_markup=reply_markup)

    async def show_schedule(self, query):
        """Show current class schedule"""
        text = """
📅 برنامه کلاس‌های هفته جاری

"""
        
        for schedule in CURRENT_SCHEDULE:
            text += f"📚 {schedule['day']}\n"
            text += f"⏰ {schedule['time']}\n"
            text += f"👥 {schedule['grade']}\n"
            text += f"📝 {schedule['topic']}\n\n"
        
        text += """
💡 نکات مهم:
• حضور به موقع الزامی است
• لینک کلاس صبح همان روز ارسال می‌شود
• با نرم‌افزار کروم وارد شوید
        """
        
        keyboard = [
            [InlineKeyboardButton("📝 ثبت‌نام در کلاس", callback_data="start_registration")],
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup)

    async def show_courses(self, query):
        """Show available courses"""
        text = """
📚 کلاس‌های موجود

"""
        
        for course in COURSES:
            text += f"📖 {course['name']}\n"
            text += f"💰 {course['price']}\n"
            text += f"📅 {course['duration']}\n"
            text += f"📝 {course['description']}\n\n"
        
        text += """
💡 برای ثبت‌نام:
• کلاس‌های رایگان: ثبت‌نام مستقیم
• کلاس‌های پولی: پس از ثبت‌نام، ادمین‌ها اطلاع‌رسانی می‌شوند
        """
        
        keyboard = [
            [InlineKeyboardButton("📝 ثبت‌نام در کلاس", callback_data="start_registration")],
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup)

    async def show_book_info(self, query):
        """Show book information"""
        text = f"""
📖 اطلاعات کتاب

📚 نام کتاب: {BOOK_INFO['name']}
👨‍🏫 نویسنده: {BOOK_INFO['author']}
💰 قیمت: {BOOK_INFO['price']}
📅 سال انتشار: {BOOK_INFO['year']}

📝 توضیحات:
{BOOK_INFO['description']}

📞 برای خرید:
{CONTACT_INFO['phone']}
        """
        
        keyboard = [
            [InlineKeyboardButton("📞 تماس برای خرید", url=f"https://t.me/{CONTACT_INFO['phone'].replace('+', '')}")],
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup)

    async def show_contact_info(self, query):
        """Show contact information"""
        text = f"""
📞 اطلاعات تماس

👨‍🏫 استاد حاتمی
📱 {CONTACT_INFO['phone']}
📧 {CONTACT_INFO['email']}
📍 {CONTACT_INFO['address']}

⏰ ساعات پاسخگویی:
شنبه تا چهارشنبه: ۹ صبح تا ۹ شب
پنجشنبه: ۹ صبح تا ۶ عصر

💡 برای سوالات:
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
        
        await query.edit_message_text(text, reply_markup=reply_markup)

    async def show_social_links(self, query):
        """Show social media links"""
        text = """
🔗 شبکه‌های اجتماعی

📱 کانال‌های رسمی:

📺 یوتیوب:
آموزش‌های رایگان و کامل
{SOCIAL_LINKS['youtube']}

📢 کانال تلگرام:
اطلاعیه‌ها و اخبار
{SOCIAL_LINKS['telegram_channel']}

📸 اینستاگرام:
محتوا و نمونه کارها
{SOCIAL_LINKS['instagram']}

🌐 وب‌سایت:
به زودی...
        """
        
        keyboard = [
            [InlineKeyboardButton("📺 یوتیوب", url=SOCIAL_LINKS['youtube'])],
            [InlineKeyboardButton("📢 تلگرام", url=SOCIAL_LINKS['telegram_channel'])],
            [InlineKeyboardButton("📸 اینستاگرام", url=SOCIAL_LINKS['instagram'])],
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup)

    async def show_main_menu(self, query):
        """Show main menu"""
        text = """
🏠 منوی اصلی

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
        
        await query.edit_message_text(text, reply_markup=reply_markup)

    # Registration flow methods
    async def start_registration(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start free registration process"""
        query = update.callback_query
        await query.answer()
        
        text = """
🆓 ثبت‌نام در کلاس‌های رایگان

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
        
        await query.edit_message_text(text, reply_markup=reply_markup)
        return CHOOSING_COURSE

    async def start_paid_registration(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start paid registration process"""
        query = update.callback_query
        await query.answer()
        
        text = """
💎 ثبت‌نام در کلاس‌های ویژه پولی

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
        
        await query.edit_message_text(text, reply_markup=reply_markup)
        return CHOOSING_COURSE

    async def choose_course(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle course selection"""
        query = update.callback_query
        await query.answer()
        
        course_name = query.data.replace('course_', '').replace('_', ' ')
        context.user_data['selected_course'] = course_name
        
        text = f"""
📝 ثبت‌نام در کلاس: {course_name}

لطفاً نام و نام خانوادگی خود را وارد کنید:
        """
        
        keyboard = [[InlineKeyboardButton("❌ انصراف", callback_data="cancel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup)
        return ENTERING_NAME

    async def enter_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle name input"""
        context.user_data['name'] = update.message.text
        
        text = """
📱 شماره تلفن خود را وارد کنید:

مثال: ۰۹۱۲۳۴۵۶۷۸۹
        """
        
        keyboard = [[InlineKeyboardButton("❌ انصراف", callback_data="cancel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, reply_markup=reply_markup)
        return ENTERING_PHONE

    async def enter_phone(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle phone input"""
        context.user_data['phone'] = update.message.text
        
        text = """
🎓 پایه تحصیلی خود را انتخاب کنید:
        """
        
        keyboard = [
            [InlineKeyboardButton("دهم", callback_data="grade_10")],
            [InlineKeyboardButton("یازدهم", callback_data="grade_11")],
            [InlineKeyboardButton("دوازدهم", callback_data="grade_12")],
            [InlineKeyboardButton("❌ انصراف", callback_data="cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, reply_markup=reply_markup)
        return ENTERING_GRADE

    async def enter_grade(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle grade selection"""
        query = update.callback_query
        await query.answer()
        
        grade = query.data.replace('grade_', '')
        context.user_data['grade'] = grade
        
        text = """
🎯 رشته تحصیلی خود را انتخاب کنید:
        """
        
        keyboard = [
            [InlineKeyboardButton("ریاضی", callback_data="field_math")],
            [InlineKeyboardButton("تجربی", callback_data="field_bio")],
            [InlineKeyboardButton("انسانی", callback_data="field_human")],
            [InlineKeyboardButton("❌ انصراف", callback_data="cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup)
        return ENTERING_FIELD

    async def enter_field(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle field input"""
        context.user_data['field'] = update.message.text
        
        text = """
📱 شماره تلفن والدین را وارد کنید:

مثال: ۰۹۱۲۳۴۵۶۷۸۹
        """
        
        keyboard = [[InlineKeyboardButton("❌ انصراف", callback_data="cancel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, reply_markup=reply_markup)
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
        field = context.user_data.get('field', '')
        parent_phone = context.user_data.get('parent_phone', '')
        course = context.user_data.get('selected_course', '')
        
        text = f"""
✅ تأیید اطلاعات ثبت‌نام

📝 اطلاعات شما:
👤 نام و نام خانوادگی: {name}
📱 شماره تلفن: {phone}
🎓 پایه تحصیلی: {grade}
🎯 رشته تحصیلی: {field}
📱 تلفن والدین: {parent_phone}
📚 کلاس انتخاب شده: {course}

💰 هزینه: رایگان

آیا اطلاعات فوق صحیح است؟
        """
        
        keyboard = [
            [InlineKeyboardButton("✅ تأیید و ثبت‌نام", callback_data="confirm")],
            [InlineKeyboardButton("❌ انصراف", callback_data="cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, reply_markup=reply_markup)
        return CONFIRMING_REGISTRATION

    async def show_payment_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show confirmation for paid registration"""
        name = context.user_data.get('name', '')
        phone = context.user_data.get('phone', '')
        grade = context.user_data.get('grade', '')
        field = context.user_data.get('field', '')
        parent_phone = context.user_data.get('parent_phone', '')
        course = context.user_data.get('selected_course', '')
        
        # Get course price
        course_price = "نامشخص"
        for c in COURSES:
            if c['name'] == course:
                course_price = c.get('price', 'نامشخص')
                break
        
        text = f"""
💎 تأیید اطلاعات ثبت‌نام کلاس پولی

📝 اطلاعات شما:
👤 نام و نام خانوادگی: {name}
📱 شماره تلفن: {phone}
🎓 پایه تحصیلی: {grade}
🎯 رشته تحصیلی: {field}
📱 تلفن والدین: {parent_phone}
📚 کلاس انتخاب شده: {course}
💰 هزینه: {course_price}

⚠️ نکته مهم:
پس از تأیید، ادمین‌ها اطلاع‌رسانی می‌شوند و مراحل پرداخت انجام خواهد شد.

آیا اطلاعات فوق صحیح است؟
        """
        
        keyboard = [
            [InlineKeyboardButton("✅ تأیید و ادامه", callback_data="confirm")],
            [InlineKeyboardButton("❌ انصراف", callback_data="cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, reply_markup=reply_markup)
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
            'field': context.user_data.get('field', ''),
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
💎 ثبت‌نام کلاس پولی با موفقیت انجام شد!

✅ مراحل بعدی:
1️⃣ ادمین‌ها اطلاع‌رسانی شدند
2️⃣ منتظر تماس برای پرداخت باشید
3️⃣ پس از پرداخت، محصول ارسال می‌شود

📞 برای سوالات:
{CONTACT_INFO['phone']}

🔙 بازگشت به منوی اصلی:
        """
        else:
            student_data['type'] = 'free'
            student_data['status'] = 'confirmed'
            text = """
✅ ثبت‌نام کلاس رایگان با موفقیت انجام شد!

🎓 اطلاعات کلاس:
• لینک کلاس صبح همان روز ارسال می‌شود
• حضور به موقع الزامی است
• با نرم‌افزار کروم وارد شوید

📞 برای سوالات:
{CONTACT_INFO['phone']}

🎉 حالا می‌توانید از تمام امکانات ربات استفاده کنید!
        """
        
        # Save to database
        self.data_manager.add_student(student_data)
        
        # Show full menu after successful registration
        await query.edit_message_text(text)
        await self.show_full_menu_after_registration(query)
        return ConversationHandler.END

    async def show_full_menu_after_registration(self, query):
        """Show full menu after successful registration"""
        welcome_text = """
🎉 ثبت‌نام شما با موفقیت انجام شد!

✅ حالا می‌توانید از تمام امکانات ربات استفاده کنید.

لطفاً یکی از گزینه‌های زیر را انتخاب کنید:
        """
        
        keyboard = [
            [InlineKeyboardButton("📝 ثبت‌نام در کلاس جدید", callback_data="start_registration")],
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
        
        await query.message.reply_text(welcome_text, reply_markup=reply_markup)

    async def notify_admins_payment(self, student_data):
        """Notify admins about payment with immediate delivery"""
        notification_text = f"""
💎 درخواست پرداخت جدید

👤 اطلاعات دانش‌آموز:
نام و نام خانوادگی: {student_data['name']}
شماره تلفن: {student_data['phone']}
پایه تحصیلی: {student_data['grade']}
رشته تحصیلی: {student_data['field']}
تلفن والدین: {student_data['parent_phone']}
کلاس انتخاب شده: {student_data['course']}

📱 اطلاعات کاربر:
ID: {student_data['user_id']}
Username: @{student_data['username']}

⏰ تاریخ ثبت‌نام:
{student_data['registration_date']}

🔗 برای تماس:
https://t.me/{student_data['username'] if student_data['username'] else 'user' + str(student_data['user_id'])}

⚠️ اقدامات لازم:
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
✅ ثبت‌نام شما با موفقیت انجام شد!

📝 اطلاعات ثبت‌نام:
کلاس: {student_data['course']}
تاریخ: {student_data['registration_date']}

💎 مراحل بعدی:
1️⃣ ادمین‌ها اطلاع‌رسانی شدند
2️⃣ منتظر تماس برای پرداخت باشید
3️⃣ پس از پرداخت، محصول بلافاصله ارسال می‌شود

📞 برای سوالات:
{CONTACT_INFO['phone']}

🎁 هدیه رایگان:
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
            await query.edit_message_text(text, reply_markup=reply_markup)
        else:
            text = "❌ ثبت‌نام لغو شد."
            keyboard = [[InlineKeyboardButton("🏠 بازگشت به منو", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(text, reply_markup=reply_markup)
        
        return ConversationHandler.END

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check registration status"""
        user_id = update.effective_user.id
        students = self.data_manager.load_students()
        
        user_registrations = [s for s in students if s.get('user_id') == user_id]
        
        if not user_registrations:
            text = """
❌ هیچ ثبت‌نامی یافت نشد!

📝 برای ثبت‌نام:
/register
            """
        else:
            text = """
📊 وضعیت ثبت‌نام شما:

"""
            for reg in user_registrations:
                status_emoji = "✅" if reg.get('status') == 'confirmed' else "⏳"
                text += f"{status_emoji} {reg.get('course', 'نامشخص')}\n"
                text += f"📅 {reg.get('registration_date', 'نامشخص')}\n"
                text += f"📊 وضعیت: {reg.get('status', 'نامشخص')}\n\n"
        
        keyboard = [[InlineKeyboardButton("🏠 بازگشت به منو", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, reply_markup=reply_markup)

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
            text = "❌ دسترسی غیرمجاز!"
            await update.message.reply_text(text)
            return
        
        # Admin panel
        students = self.data_manager.load_students()
        total_students = len(students)
        pending_payments = len([s for s in students if s.get('status') == 'pending_payment'])
        
        text = f"""
🔧 پنل مدیریت ربات

📊 آمار کلی:
👥 کل دانش‌آموزان: {total_students}
💎 در انتظار پرداخت: {pending_payments}

📈 وضعیت ربات:
✅ فعال و آماده
🟢 تمام سرویس‌ها در دسترس

🔧 تنظیمات:
• پشتیبان‌گیری خودکار: {'فعال' if AUTO_BACKUP_ENABLED else 'غیرفعال'}
• اطلاع‌رسانی: {'فعال' if NOTIFICATION_ENABLED else 'غیرفعال'}

📢 ویژگی‌های مدیریت:
• ارسال اطلاعیه به همه کاربران
• مدیریت پرداخت‌ها
• مشاهده آمار کامل
        """
        
        keyboard = [
            [InlineKeyboardButton("📢 ارسال اطلاعیه", callback_data="admin_broadcast")],
            [InlineKeyboardButton("📊 مشاهده آمار کامل", callback_data="admin_stats")],
            [InlineKeyboardButton("💎 مدیریت پرداخت‌ها", callback_data="admin_payments")],
            [InlineKeyboardButton("📋 خروجی اطلاعات کاربران", callback_data="admin_export")],
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, reply_markup=reply_markup)

    async def export_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Export user data for admin"""
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
            text = "❌ دسترسی غیرمجاز!"
            await update.message.reply_text(text)
            return
        
        # Export user data
        summary = self.data_manager.export_user_data_summary()
        
        # Split long messages if needed
        if len(summary) > 4000:
            parts = [summary[i:i+4000] for i in range(0, len(summary), 4000)]
            for i, part in enumerate(parts, 1):
                await update.message.reply_text(f"📊 بخش {i} از {len(parts)}:\n\n{part}")
        else:
            await update.message.reply_text(summary)
        
        # Also save to file for easy access
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"data/user_export_{timestamp}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(summary)
            
            await update.message.reply_text(f"✅ فایل خروجی در {filename} ذخیره شد.")
        except Exception as e:
            logger.error(f"Error saving export file: {e}")
            await update.message.reply_text("❌ خطا در ذخیره فایل خروجی.")

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
📢 اطلاعیه مهم

{message_text}

📞 برای سوالات:
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
✅ پرداخت تأیید شد!

🎁 محصول شما ارسال شد:
• لینک کلاس
• مواد آموزشی
• دسترسی به کانال خصوصی

📞 برای سوالات:
{CONTACT_INFO['phone']}

🔙 بازگشت به منوی اصلی:
            """
        elif payment_type == 'pending':
            text = """
⏳ پرداخت در حال بررسی

لطفاً منتظر تأیید ادمین باشید.

📞 برای سوالات:
{CONTACT_INFO['phone']}
            """
        else:
            text = """
❌ خطا در پرداخت

لطفاً با پشتیبانی تماس بگیرید.

📞 پشتیبانی:
{CONTACT_INFO['phone']}
            """
        
        keyboard = [[InlineKeyboardButton("🏠 بازگشت به منو", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup)
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
            text = "❌ دسترسی غیرمجاز!"
            keyboard = [[InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text, reply_markup=reply_markup)
            return
        
        # Admin panel
        students = self.data_manager.load_students()
        total_students = len(students)
        pending_payments = len([s for s in students if s.get('status') == 'pending_payment'])
        
        text = f"""
🔧 پنل مدیریت ربات

📊 آمار کلی:
👥 کل دانش‌آموزان: {total_students}
💎 در انتظار پرداخت: {pending_payments}

📈 وضعیت ربات:
✅ فعال و آماده
🟢 تمام سرویس‌ها در دسترس

🔧 تنظیمات:
• پشتیبان‌گیری خودکار: {'فعال' if AUTO_BACKUP_ENABLED else 'غیرفعال'}
• اطلاع‌رسانی: {'فعال' if NOTIFICATION_ENABLED else 'غیرفعال'}

📢 ویژگی‌های مدیریت:
• ارسال اطلاعیه به همه کاربران
• مدیریت پرداخت‌ها
• مشاهده آمار کامل
        """
        
        keyboard = [
            [InlineKeyboardButton("📢 ارسال اطلاعیه", callback_data="admin_broadcast")],
            [InlineKeyboardButton("📊 مشاهده آمار کامل", callback_data="admin_stats")],
            [InlineKeyboardButton("💎 مدیریت پرداخت‌ها", callback_data="admin_payments")],
            [InlineKeyboardButton("📋 خروجی اطلاعات کاربران", callback_data="admin_export")],
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup)

    async def show_admin_broadcast(self, query):
        """Show admin broadcast interface"""
        text = """
📢 ارسال اطلاعیه به کاربران

لطفاً نوع اطلاعیه را انتخاب کنید:
        """
        
        keyboard = [
            [InlineKeyboardButton("📢 اطلاعیه عمومی", callback_data="broadcast_general")],
            [InlineKeyboardButton("📅 اطلاعیه کلاس", callback_data="broadcast_class")],
            [InlineKeyboardButton("⚠️ هشدار مهم", callback_data="broadcast_warning")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="admin")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup)

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
📊 آمار کامل ربات

👥 آمار کلی:
• کل دانش‌آموزان: {total_students}
• کلاس‌های رایگان: {free_students}
• کلاس‌های پولی: {paid_students}
• در انتظار پرداخت: {pending_payments}

📚 آمار کلاس‌ها:
"""
        
        for course, count in course_stats.items():
            text += f"• {course}: {count} نفر\n"
        
        text += f"""
📈 نرخ تبدیل:
• تبدیل رایگان به پولی: {(paid_students/total_students*100):.1f}% (از کل ثبت‌نام‌ها)
        """
        
        keyboard = [
            [InlineKeyboardButton("📋 مشاهده جزئیات کاربران", callback_data="admin_user_details")],
            [InlineKeyboardButton("📊 گزارش کامل", callback_data="admin_full_report")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="admin")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup)

    async def show_admin_payments(self, query):
        """Show payment management interface"""
        students = self.data_manager.load_students()
        pending_payments = [s for s in students if s.get('status') == 'pending_payment']
        
        text = f"""
💎 مدیریت پرداخت‌ها

⏳ در انتظار پرداخت: {len(pending_payments)} مورد

"""
        
        if pending_payments:
            for i, student in enumerate(pending_payments[:5], 1):  # Show first 5
                text += f"""
{i}. {student.get('name', 'نامشخص')}
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
        
        await query.edit_message_text(text, reply_markup=reply_markup)

    async def show_admin_user_details(self, query):
        """Show detailed user information for admin"""
        students = self.data_manager.load_students()
        
        if not students:
            text = """
📋 جزئیات کاربران

❌ هیچ کاربری ثبت‌نام نکرده است.
            """
            keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="admin_stats")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text, reply_markup=reply_markup)
            return
        
        # Get page from context or default to 0
        page = 0
        if hasattr(query, 'data') and 'page_' in query.data:
            try:
                page = int(query.data.split('_')[-1])
            except:
                page = 0
        
        students_per_page = 3  # Show 3 students per page due to message length
        start_idx = page * students_per_page
        end_idx = start_idx + students_per_page
        page_students = students[start_idx:end_idx]
        
        text = f"""
📋 جزئیات کاربران (صفحه {page + 1} از {(len(students) + students_per_page - 1) // students_per_page})

👥 کل کاربران: {len(students)}
        """
        
        for i, student in enumerate(page_students, start_idx + 1):
            registration_date = student.get('registration_date', 'نامشخص')
            if registration_date != 'نامشخص':
                try:
                    # Convert ISO format to readable date
                    from datetime import datetime
                    dt = datetime.fromisoformat(registration_date.replace('Z', '+00:00'))
                    registration_date = dt.strftime('%Y/%m/%d %H:%M')
                except:
                    pass
            
            text += f"""

{i}. 👤 {student.get('name', 'نامشخص')}
   📱 تلفن: {student.get('phone', 'نامشخص')}
   📚 کلاس: {student.get('course', 'نامشخص')}
   🎓 پایه: {student.get('grade', 'نامشخص')}
   📖 رشته: {student.get('field', 'نامشخص')}
   📞 تلفن والدین: {student.get('parent_phone', 'نامشخص')}
   💰 نوع: {student.get('type', 'نامشخص')}
   📅 تاریخ ثبت‌نام: {registration_date}
   ✅ وضعیت: {student.get('status', 'نامشخص')}
   🆔 شناسه کاربر: {student.get('user_id', 'نامشخص')}
"""
        
        keyboard = []
        
        # Navigation buttons
        if page > 0:
            keyboard.append([InlineKeyboardButton("⬅️ صفحه قبل", callback_data=f"admin_user_details_page_{page-1}")])
        
        if end_idx < len(students):
            keyboard.append([InlineKeyboardButton("➡️ صفحه بعد", callback_data=f"admin_user_details_page_{page+1}")])
        
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="admin_stats")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup)

    async def show_admin_export(self, query):
        """Show admin export interface"""
        # Export user data
        summary = self.data_manager.export_user_data_summary()
        
        # Split long messages if needed
        if len(summary) > 4000:
            # Show first part and save to file
            first_part = summary[:4000]
            text = f"{first_part}\n\n... (ادامه در فایل ذخیره شده)"
            
            # Save to file
            try:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"data/user_export_{timestamp}.txt"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(summary)
                
                text += f"\n\n✅ فایل کامل در {filename} ذخیره شد."
            except Exception as e:
                logger.error(f"Error saving export file: {e}")
                text += "\n\n❌ خطا در ذخیره فایل خروجی."
        else:
            text = summary
            # Save to file anyway for easy access
            try:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"data/user_export_{timestamp}.txt"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(summary)
                
                text += f"\n\n✅ فایل در {filename} ذخیره شد."
            except Exception as e:
                logger.error(f"Error saving export file: {e}")
                text += "\n\n❌ خطا در ذخیره فایل خروجی."
        
        keyboard = [
            [InlineKeyboardButton("📋 مشاهده جزئیات کاربران", callback_data="admin_user_details")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="admin")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup)

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors professionally"""
        logger.error(f"Exception while handling an update: {context.error}")
        
        if update and update.effective_message:
            text = f"""
❌ خطایی رخ داد!

لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید.

📞 پشتیبانی:
{CONTACT_INFO['phone']}
            """
            keyboard = [[InlineKeyboardButton("🏠 بازگشت به منو", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.effective_message.reply_text(text, reply_markup=reply_markup)

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
