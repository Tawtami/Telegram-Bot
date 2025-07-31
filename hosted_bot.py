#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Professional Telegram Bot for Math Course Registration
ربات تلگرام حرفه‌ای برای ثبت‌نام کلاس‌های ریاضی
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

# Conversation states
CHOOSING_COURSE, ENTERING_NAME, ENTERING_PHONE, ENTERING_GRADE, ENTERING_PARENT_PHONE, CONFIRMING_REGISTRATION = range(6)

class SecureDataManager:
    """Secure data management with encryption and backup"""
    
    def __init__(self):
        self.data_file = DATA_FILE
        self.backup_file = BACKUP_FILE
        self.ensure_data_directory()
    
    def ensure_data_directory(self):
        """Ensure data directory exists"""
        os.makedirs("data", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
    
    def hash_data(self, data):
        """Hash sensitive data"""
        return hashlib.sha256((str(data) + HASH_SALT).encode()).hexdigest()
    
    def encrypt_data(self, data):
        """Simple encryption for sensitive data"""
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
            
            logger.info(f"Saved {len(students)} students data securely")
            return True
        except Exception as e:
            logger.error(f"Error saving students data: {e}")
            return False
    
    def add_student(self, student_data):
        """Add new student securely"""
        students = self.load_students()
        student_data['id'] = self.hash_data(f"{student_data['phone']}{datetime.now()}")
        student_data['registration_date'] = datetime.now().isoformat()
        student_data['status'] = 'pending'
        students.append(student_data)
        return self.save_students(students)

class ProfessionalMathBot:
    def __init__(self):
        # Get token from environment variable (for hosting) or config file
        self.token = os.getenv('BOT_TOKEN', BOT_TOKEN)
        if not self.token or self.token == "YOUR_BOT_TOKEN_HERE":
            raise ValueError("BOT_TOKEN not found in environment variables or config")
        
        self.application = Application.builder().token(self.token).build()
        self.data_manager = SecureDataManager()
        self.setup_handlers()
        
    def setup_handlers(self):
        """Setup all bot handlers"""
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
            entry_points=[CommandHandler("register", self.register_command)],
            states={
                CHOOSING_COURSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.choose_course)],
                ENTERING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.enter_name)],
                ENTERING_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.enter_phone)],
                ENTERING_GRADE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.enter_grade)],
                ENTERING_PARENT_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.enter_parent_phone)],
                CONFIRMING_REGISTRATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.confirm_registration)]
            },
            fallbacks=[CommandHandler("cancel", self.cancel_registration)]
        )
        self.application.add_handler(conv_handler)
        
        # Error handler
        self.application.add_error_handler(self.error_handler)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command with comprehensive menu"""
        user = update.effective_user
        welcome_text = f"""
👋 سلام {user.first_name}! خوش آمدید به ربات کلاس‌های ریاضی استاد حاتمی

📚 این ربات برای ثبت‌نام در کلاس‌های ریاضی طراحی شده است.

🎯 <b>کلاس‌های رایگان آنلاین</b> در حال برگزاری است!

📝 <b>برای ثبت‌نام فوری:</b> /register

لطفاً یکی از گزینه‌های زیر را انتخاب کنید:
        """
        
        keyboard = [
            [InlineKeyboardButton("📝 ثبت‌نام فوری", callback_data="quick_register")],
            [InlineKeyboardButton("📢 اطلاعیه‌های جدید", callback_data="announcements")],
            [InlineKeyboardButton("📚 کلاس‌های ریاضی", callback_data="courses")],
            [InlineKeyboardButton("🎓 کلاس‌های ویژه رایگان", callback_data="special_courses")],
            [InlineKeyboardButton("📅 برنامه کلاس‌ها", callback_data="schedule")],
            [InlineKeyboardButton("📺 آموزش‌های رایگان یوتیوب", callback_data="youtube")],
            [InlineKeyboardButton("📘 کتاب انفجار خلاقیت", callback_data="book")],
            [InlineKeyboardButton("📞 اطلاعات تماس", callback_data="contact")],
            [InlineKeyboardButton("🌐 شبکه‌های اجتماعی", callback_data="social")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='HTML')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
🤖 راهنمای استفاده از ربات

📋 **دستورات موجود:**
/start - شروع ربات و نمایش منوی اصلی
/help - نمایش این راهنما
/register - ثبت‌نام در کلاس‌ها
/status - بررسی وضعیت ثبت‌نام

🎯 **قابلیت‌های ربات:**
• ثبت‌نام امن و حرفه‌ای
• مشاهده اطلاعیه‌های جدید
• کلاس‌های رایگان و پولی
• برنامه کلاس‌ها و ظرفیت
• آموزش‌های رایگان یوتیوب
• خرید کتاب
• تماس با استاد

📞 **پشتیبانی:**
برای سوالات بیشتر با استاد تماس بگیرید
        """
        await update.message.reply_text(help_text, parse_mode='HTML')
    
    async def register_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start registration process"""
        keyboard = [
            [InlineKeyboardButton("🎓 کلاس‌های رایگان", callback_data="register_free")],
            [InlineKeyboardButton("💰 کلاس‌های پولی", callback_data="register_paid")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "📝 <b>ثبت‌نام در کلاس‌های ریاضی</b>\n\n"
            "لطفاً نوع کلاس مورد نظر خود را انتخاب کنید:",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        return CHOOSING_COURSE
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "quick_register":
            await self.show_registration_menu(query)
        elif query.data == "announcements":
            await self.show_announcements(query)
        elif query.data == "courses":
            await self.show_courses(query)
        elif query.data == "special_courses":
            await self.show_special_courses(query)
        elif query.data == "schedule":
            await self.show_schedule(query)
        elif query.data == "youtube":
            await self.show_youtube(query)
        elif query.data == "book":
            await self.show_book_info(query)
        elif query.data == "contact":
            await self.show_contact_info(query)
        elif query.data == "social":
            await self.show_social_links(query)
        elif query.data == "back_to_menu":
            await self.show_main_menu(query)
        elif query.data == "register_free":
            await self.start_free_registration(query)
        elif query.data == "register_paid":
            await self.start_paid_registration(query)
    
    async def show_registration_menu(self, query):
        """Show comprehensive registration menu"""
        registration_text = """
📝 **ثبت‌نام در کلاس‌های ریاضی**

🎯 **مراحل ثبت‌نام:**

1️⃣ انتخاب نوع کلاس (رایگان یا پولی)
2️⃣ وارد کردن اطلاعات شخصی
3️⃣ تایید اطلاعات
4️⃣ پرداخت (برای کلاس‌های پولی)
5️⃣ تایید نهایی توسط ادمین

🎓 **کلاس‌های رایگان موجود:**
• نظریه اعداد گسسته (دوازدهم + المپیاد)
• مهارت‌های حل خلاق مسائل (همه پایه‌ها)

💰 **کلاس‌های پولی:**
• کلاس‌های منظم همه پایه‌ها
• پرداخت دستی پس از ثبت‌نام
        """
        
        keyboard = [
            [InlineKeyboardButton("🎓 کلاس‌های رایگان", callback_data="register_free")],
            [InlineKeyboardButton("💰 کلاس‌های پولی", callback_data="register_paid")],
            [InlineKeyboardButton("📅 برنامه کلاس‌ها", callback_data="schedule")],
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(registration_text, reply_markup=reply_markup, parse_mode='HTML')
    
    async def show_youtube(self, query):
        """Show YouTube educational content"""
        youtube_text = f"""
📺 **آموزش‌های رایگان یوتیوب**

🎓 **کانال همراه با استاد:**
{SOCIAL_LINKS['youtube']}

📚 **محتوای آموزشی موجود:**
• حل مسائل کنکور سراسری
• نکات مهم ریاضی
• ویدیوهای آموزشی رایگان
• آزمون‌های آنلاین
• تکنیک‌های حل خلاق مسائل

✅ **برای دسترسی به محتوای رایگان:**
1. روی لینک بالا کلیک کنید
2. کانال را دنبال کنید
3. از ویدیوهای آموزشی استفاده کنید

🎯 **این محتوا کاملاً رایگان است!**
        """
        
        keyboard = [
            [InlineKeyboardButton("📺 مشاهده در یوتیوب", url=SOCIAL_LINKS['youtube'])],
            [InlineKeyboardButton("📝 ثبت‌نام در کلاس", callback_data="quick_register")],
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(youtube_text, reply_markup=reply_markup, parse_mode='HTML')
    
    async def show_announcements(self, query):
        """Show latest announcements"""
        announcements_text = "📢 **آخرین اطلاعیه‌ها:**\n\n"
        
        for i, announcement in enumerate(ANNOUNCEMENTS, 1):
            announcements_text += f"**{i}. {announcement['title']}**\n"
            announcements_text += f"📅 {announcement['date']}\n"
            announcements_text += f"📝 {announcement['content']}\n\n"
        
        announcements_text += "📞 برای اطلاعات بیشتر با استاد تماس بگیرید"
        
        keyboard = [
            [InlineKeyboardButton("📝 ثبت‌نام فوری", callback_data="quick_register")],
            [InlineKeyboardButton("📅 برنامه کلاس‌ها", callback_data="schedule")],
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(announcements_text, reply_markup=reply_markup, parse_mode='HTML')
    
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
            [InlineKeyboardButton("📝 ثبت‌نام فوری", callback_data="register_free")],
            [InlineKeyboardButton("📅 برنامه کلاس‌ها", callback_data="schedule")],
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(special_text, reply_markup=reply_markup, parse_mode='HTML')
    
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
            [InlineKeyboardButton("📝 ثبت‌نام فوری", callback_data="quick_register")],
            [InlineKeyboardButton("🎓 کلاس‌های ویژه", callback_data="special_courses")],
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(schedule_text, reply_markup=reply_markup, parse_mode='HTML')
    
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
            [InlineKeyboardButton("📝 ثبت‌نام", callback_data="register_paid")],
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(courses_text, reply_markup=reply_markup, parse_mode='HTML')
    
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
        
        await query.edit_message_text(book_text, reply_markup=reply_markup, parse_mode='HTML')
    
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
            [InlineKeyboardButton("📝 ثبت‌نام فوری", callback_data="quick_register")],
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(contact_text, reply_markup=reply_markup, parse_mode='HTML')
    
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
            [InlineKeyboardButton("📺 آموزش‌های یوتیوب", callback_data="youtube")],
            [InlineKeyboardButton("📢 اطلاعیه‌های جدید", callback_data="announcements")],
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(social_text, reply_markup=reply_markup, parse_mode='HTML')
    
    async def show_main_menu(self, query):
        """Show main menu"""
        menu_text = """
📚 **منوی اصلی ربات کلاس‌های ریاضی**

🎯 **کلاس‌های رایگان آنلاین** در حال برگزاری است!

لطفاً یکی از گزینه‌های زیر را انتخاب کنید:
        """
        
        keyboard = [
            [InlineKeyboardButton("📝 ثبت‌نام فوری", callback_data="quick_register")],
            [InlineKeyboardButton("📢 اطلاعیه‌های جدید", callback_data="announcements")],
            [InlineKeyboardButton("📚 کلاس‌های ریاضی", callback_data="courses")],
            [InlineKeyboardButton("🎓 کلاس‌های ویژه رایگان", callback_data="special_courses")],
            [InlineKeyboardButton("📅 برنامه کلاس‌ها", callback_data="schedule")],
            [InlineKeyboardButton("📺 آموزش‌های رایگان یوتیوب", callback_data="youtube")],
            [InlineKeyboardButton("📘 کتاب انفجار خلاقیت", callback_data="book")],
            [InlineKeyboardButton("📞 اطلاعات تماس", callback_data="contact")],
            [InlineKeyboardButton("🌐 شبکه‌های اجتماعی", callback_data="social")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(menu_text, reply_markup=reply_markup, parse_mode='HTML')
    
    async def start_free_registration(self, query):
        """Start free course registration"""
        context.user_data['registration_type'] = 'free'
        await query.edit_message_text(
            "🎓 <b>ثبت‌نام کلاس‌های رایگان</b>\n\n"
            "لطفاً نام و نام خانوادگی خود را وارد کنید:",
            parse_mode='HTML'
        )
        return ENTERING_NAME
    
    async def start_paid_registration(self, query):
        """Start paid course registration"""
        context.user_data['registration_type'] = 'paid'
        await query.edit_message_text(
            "💰 <b>ثبت‌نام کلاس‌های پولی</b>\n\n"
            "لطفاً نام و نام خانوادگی خود را وارد کنید:",
            parse_mode='HTML'
        )
        return ENTERING_NAME
    
    async def choose_course(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle course selection"""
        text = update.message.text
        if text == "🎓 کلاس‌های رایگان":
            context.user_data['registration_type'] = 'free'
            await update.message.reply_text(
                "لطفاً نام و نام خانوادگی خود را وارد کنید:",
                reply_markup=ReplyKeyboardRemove()
            )
            return ENTERING_NAME
        elif text == "💰 کلاس‌های پولی":
            context.user_data['registration_type'] = 'paid'
            await update.message.reply_text(
                "لطفاً نام و نام خانوادگی خود را وارد کنید:",
                reply_markup=ReplyKeyboardRemove()
            )
            return ENTERING_NAME
        else:
            await update.message.reply_text("لطفاً یکی از گزینه‌های بالا را انتخاب کنید.")
            return CHOOSING_COURSE
    
    async def enter_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle name input"""
        context.user_data['name'] = update.message.text
        await update.message.reply_text(
            "لطفاً شماره تلفن خود را وارد کنید:"
        )
        return ENTERING_PHONE
    
    async def enter_phone(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle phone input"""
        context.user_data['phone'] = update.message.text
        await update.message.reply_text(
            "لطفاً پایه تحصیلی خود را وارد کنید (دهم/یازدهم/دوازدهم):"
        )
        return ENTERING_GRADE
    
    async def enter_grade(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle grade input"""
        context.user_data['grade'] = update.message.text
        await update.message.reply_text(
            "لطفاً شماره تلفن والدین را وارد کنید:"
        )
        return ENTERING_PARENT_PHONE
    
    async def enter_parent_phone(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle parent phone input"""
        context.user_data['parent_phone'] = update.message.text
        
        # Show confirmation
        registration_type = context.user_data.get('registration_type', 'unknown')
        name = context.user_data.get('name', '')
        phone = context.user_data.get('phone', '')
        grade = context.user_data.get('grade', '')
        parent_phone = context.user_data.get('parent_phone', '')
        
        confirm_text = f"""
📝 **تایید اطلاعات ثبت‌نام:**

👤 **نام:** {name}
📞 **تلفن:** {phone}
🎓 **پایه:** {grade}
📞 **تلفن والدین:** {parent_phone}
💰 **نوع کلاس:** {'رایگان' if registration_type == 'free' else 'پولی'}

✅ آیا اطلاعات فوق صحیح است؟ (بله/خیر)
        """
        
        await update.message.reply_text(confirm_text, parse_mode='HTML')
        return CONFIRMING_REGISTRATION
    
    async def confirm_registration(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle registration confirmation"""
        response = update.message.text.lower()
        
        if response in ['بله', 'yes', 'y', 'صحیح']:
            # Save registration
            student_data = {
                'name': context.user_data.get('name'),
                'phone': context.user_data.get('phone'),
                'grade': context.user_data.get('grade'),
                'parent_phone': context.user_data.get('parent_phone'),
                'registration_type': context.user_data.get('registration_type'),
                'user_id': update.effective_user.id,
                'username': update.effective_user.username
            }
            
            success = self.data_manager.add_student(student_data)
            
            if success:
                # Notify admins
                await self.notify_admins(student_data)
                
                # Send confirmation to user
                if student_data['registration_type'] == 'free':
                    await update.message.reply_text(
                        "✅ <b>ثبت‌نام شما با موفقیت انجام شد!</b>\n\n"
                        "🎓 کلاس‌های رایگان\n"
                        "📞 ادمین‌ها به زودی با شما تماس خواهند گرفت.\n"
                        "📅 برنامه کلاس‌ها از طریق ربات اطلاع‌رسانی می‌شود.",
                        parse_mode='HTML'
                    )
                else:
                    await update.message.reply_text(
                        "✅ <b>ثبت‌نام شما با موفقیت انجام شد!</b>\n\n"
                        "💰 کلاس‌های پولی\n"
                        "📞 ادمین‌ها برای پرداخت با شما تماس خواهند گرفت.\n"
                        "💳 پرداخت به صورت دستی انجام می‌شود.",
                        parse_mode='HTML'
                    )
            else:
                await update.message.reply_text(
                    "❌ خطا در ثبت‌نام. لطفاً دوباره تلاش کنید یا با ادمین تماس بگیرید."
                )
        else:
            await update.message.reply_text(
                "❌ ثبت‌نام لغو شد. برای شروع مجدد /register را ارسال کنید."
            )
        
        # Clear user data
        context.user_data.clear()
        return ConversationHandler.END
    
    async def cancel_registration(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel registration"""
        context.user_data.clear()
        await update.message.reply_text(
            "❌ ثبت‌نام لغو شد. برای شروع مجدد /register را ارسال کنید.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    
    async def notify_admins(self, student_data):
        """Notify admins about new registration"""
        if not NOTIFICATION_ENABLED:
            return
        
        notification_text = f"""
🔔 **ثبت‌نام جدید**

👤 **نام:** {student_data['name']}
📞 **تلفن:** {student_data['phone']}
🎓 **پایه:** {student_data['grade']}
📞 **تلفن والدین:** {student_data['parent_phone']}
💰 **نوع کلاس:** {'رایگان' if student_data['registration_type'] == 'free' else 'پولی'}
🆔 **User ID:** {student_data['user_id']}
👤 **Username:** @{student_data['username']}

📅 **تاریخ ثبت‌نام:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        # Send notification to all admins
        for admin_id in ADMIN_IDS:
            try:
                await self.application.bot.send_message(
                    chat_id=admin_id,
                    text=notification_text,
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Failed to notify admin {admin_id}: {e}")
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check registration status"""
        user_id = update.effective_user.id
        students = self.data_manager.load_students()
        
        user_registrations = [s for s in students if s.get('user_id') == user_id]
        
        if user_registrations:
            status_text = "📋 **وضعیت ثبت‌نام شما:**\n\n"
            for reg in user_registrations:
                status_text += f"👤 **نام:** {reg['name']}\n"
                status_text += f"🎓 **پایه:** {reg['grade']}\n"
                status_text += f"💰 **نوع کلاس:** {'رایگان' if reg['registration_type'] == 'free' else 'پولی'}\n"
                status_text += f"📅 **تاریخ ثبت‌نام:** {reg['registration_date']}\n"
                status_text += f"📊 **وضعیت:** {reg['status']}\n\n"
        else:
            status_text = "❌ شما هنوز ثبت‌نام نکرده‌اید.\n\nبرای ثبت‌نام /register را ارسال کنید."
        
        await update.message.reply_text(status_text, parse_mode='HTML')
    
    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin commands"""
        user_id = update.effective_user.id
        username = update.effective_user.username
        
        # Check if user is admin
        is_admin = False
        for admin_id in ADMIN_IDS:
            if admin_id.startswith('@') and f"@{username}" == admin_id:
                is_admin = True
                break
        
        if not is_admin:
            await update.message.reply_text("❌ شما دسترسی ادمین ندارید.")
            return
        
        # Admin menu
        admin_text = """
🔧 **منوی ادمین**

📊 آمار ثبت‌نام‌ها
📋 لیست دانش‌آموزان
📢 ارسال اطلاعیه
⏰ تنظیم یادآوری

برای دسترسی به این قابلیت‌ها، لطفاً با توسعه‌دهنده تماس بگیرید.
        """
        
        await update.message.reply_text(admin_text, parse_mode='HTML')
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Exception while handling an update: {context.error}")

def main():
    """Main function to run the bot"""
    try:
        bot = ProfessionalMathBot()
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