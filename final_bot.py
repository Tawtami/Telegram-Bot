#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ربات تلگرام استاد حاتمی - نسخه نهایی
Telegram Bot for Ostad Hatami - Final Version
"""

import json
import logging
import os
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters, ConversationHandler

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Conversation states
ENTERING_FIRST_NAME, ENTERING_LAST_NAME, ENTERING_PHONE, ENTERING_CITY, ENTERING_GRADE, ENTERING_FIELD = range(6)

# Bot configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")

class UserDataManager:
    """مدیریت داده‌های کاربران"""
    
    def __init__(self):
        self.data_dir = "data/users"
        self.ensure_data_directory()
    
    def ensure_data_directory(self):
        """ایجاد دایرکتوری داده‌ها در صورت عدم وجود"""
        os.makedirs(self.data_dir, exist_ok=True)
    
    def get_user_file_path(self, user_id: int) -> str:
        """مسیر فایل کاربر"""
        return os.path.join(self.data_dir, f"user_{user_id}.json")
    
    def save_user_data(self, user_id: int, user_data: Dict[str, Any]) -> bool:
        """ذخیره اطلاعات کاربر"""
        try:
            file_path = self.get_user_file_path(user_id)
            user_data['user_id'] = user_id
            user_data['registration_date'] = datetime.now().isoformat()
            user_data['last_updated'] = datetime.now().isoformat()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(user_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"User data saved for user_id: {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving user data for user_id {user_id}: {e}")
            return False
    
    def load_user_data(self, user_id: int) -> Optional[Dict[str, Any]]:
        """بارگذاری اطلاعات کاربر"""
        try:
            file_path = self.get_user_file_path(user_id)
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
        except Exception as e:
            logger.error(f"Error loading user data for user_id {user_id}: {e}")
            return None
    
    def user_exists(self, user_id: int) -> bool:
        """بررسی وجود کاربر"""
        return os.path.exists(self.get_user_file_path(user_id))

class OstadHatamiBot:
    """ربات اصلی استاد حاتمی"""
    
    def __init__(self):
        self.data_manager = UserDataManager()
        self.application = Application.builder().token(BOT_TOKEN).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        """تنظیم هندلرهای ربات"""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("menu", self.show_main_menu))
        self.application.add_handler(CommandHandler("help", self.help_command))
        
        # Registration conversation handler
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("register", self.start_registration)],
            states={
                ENTERING_FIRST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.enter_first_name)],
                ENTERING_LAST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.enter_last_name)],
                ENTERING_PHONE: [
                    MessageHandler(filters.CONTACT, self.enter_phone_contact),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.enter_phone_manual)
                ],
                ENTERING_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.enter_city)],
                ENTERING_GRADE: [CallbackQueryHandler(self.enter_grade)],
                ENTERING_FIELD: [CallbackQueryHandler(self.enter_field)]
            },
            fallbacks=[CommandHandler("cancel", self.cancel_registration)]
        )
        self.application.add_handler(conv_handler)
        
        # Callback query handler
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # Error handler
        self.application.add_error_handler(self.error_handler)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """دستور شروع ربات"""
        user = update.effective_user
        
        # بررسی ثبت‌نام کاربر
        if self.data_manager.user_exists(user.id):
            await self.show_main_menu(update, context)
        else:
            welcome_text = f"سلام {user.first_name} خوش آمدی، برای استفاده از ربات اول حتما باید در ربات ثبت‌نام کنی."
            
            keyboard = [
                [InlineKeyboardButton("📝 ثبت‌نام در ربات", callback_data="start_registration")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    
    async def start_registration(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """شروع فرآیند ثبت‌نام"""
        user = update.effective_user
        
        if self.data_manager.user_exists(user.id):
            await update.message.reply_text("شما قبلاً ثبت‌نام کرده‌اید!")
            await self.show_main_menu(update, context)
            return ConversationHandler.END
        
        context.user_data['user_id'] = user.id
        
        await update.message.reply_text(
            "🎓 ثبت‌نام در ربات استاد حاتمی\n\n"
            "لطفاً نام خود را وارد کنید:",
            reply_markup=ReplyKeyboardRemove()
        )
        
        return ENTERING_FIRST_NAME
    
    async def enter_first_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """دریافت نام"""
        context.user_data['first_name'] = update.message.text
        
        await update.message.reply_text("لطفاً نام خانوادگی خود را وارد کنید:")
        return ENTERING_LAST_NAME
    
    async def enter_last_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """دریافت نام خانوادگی"""
        context.user_data['last_name'] = update.message.text
        
        keyboard = [
            [KeyboardButton("📱 ارسال شماره تلفن", request_contact=True)],
            [KeyboardButton("✏️ ورود دستی شماره")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        
        await update.message.reply_text(
            "لطفاً شماره تلفن خود را وارد کنید:\n\n"
            "می‌توانید از دکمه ارسال شماره استفاده کنید یا به صورت دستی وارد کنید.",
            reply_markup=reply_markup
        )
        return ENTERING_PHONE
    
    async def enter_phone_contact(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """دریافت شماره از طریق دکمه share_contact"""
        contact = update.message.contact
        context.user_data['phone'] = contact.phone_number
        
        await update.message.reply_text(
            "لطفاً شهر محل سکونت خود را وارد کنید:",
            reply_markup=ReplyKeyboardRemove()
        )
        return ENTERING_CITY
    
    async def enter_phone_manual(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """دریافت شماره به صورت دستی"""
        phone = update.message.text
        if not phone.startswith('+98') and not phone.startswith('09'):
            await update.message.reply_text("لطفاً شماره تلفن معتبر وارد کنید (مثال: 09123456789)")
            return ENTERING_PHONE
        
        context.user_data['phone'] = phone
        
        await update.message.reply_text(
            "لطفاً شهر محل سکونت خود را وارد کنید:",
            reply_markup=ReplyKeyboardRemove()
        )
        return ENTERING_CITY
    
    async def enter_city(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """دریافت شهر"""
        context.user_data['city'] = update.message.text
        
        keyboard = [
            [InlineKeyboardButton("پایه ۹", callback_data="grade_9")],
            [InlineKeyboardButton("پایه ۱۰", callback_data="grade_10")],
            [InlineKeyboardButton("پایه ۱۱", callback_data="grade_11")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text("لطفاً پایه تحصیلی خود را انتخاب کنید:", reply_markup=reply_markup)
        return ENTERING_GRADE
    
    async def enter_grade(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """دریافت پایه تحصیلی"""
        query = update.callback_query
        await query.answer()
        
        grade = query.data.replace('grade_', '')
        context.user_data['grade'] = grade
        
        keyboard = [
            [InlineKeyboardButton("ریاضی", callback_data="field_math")],
            [InlineKeyboardButton("تجربی", callback_data="field_bio")],
            [InlineKeyboardButton("انسانی", callback_data="field_human")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text("لطفاً رشته تحصیلی خود را انتخاب کنید:", reply_markup=reply_markup)
        return ENTERING_FIELD
    
    async def enter_field(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """دریافت رشته تحصیلی و تکمیل ثبت‌نام"""
        query = update.callback_query
        await query.answer()
        
        field = query.data.replace('field_', '')
        field_names = {
            'math': 'ریاضی',
            'bio': 'تجربی', 
            'human': 'انسانی'
        }
        context.user_data['field'] = field_names.get(field, field)
        
        # ذخیره اطلاعات کاربر
        user_id = context.user_data['user_id']
        user_data = {
            'first_name': context.user_data['first_name'],
            'last_name': context.user_data['last_name'],
            'phone': context.user_data['phone'],
            'city': context.user_data['city'],
            'grade': context.user_data['grade'],
            'field': context.user_data['field']
        }
        
        if self.data_manager.save_user_data(user_id, user_data):
            await query.edit_message_text(
                "✅ ثبت‌نام شما با موفقیت انجام شد!\n\n"
                "حالا می‌توانید از امکانات ربات استفاده کنید.",
                reply_markup=ReplyKeyboardRemove()
            )
            
            # نمایش منوی اصلی
            await self.show_main_menu(update, context)
        else:
            await query.edit_message_text(
                "❌ خطا در ثبت‌نام. لطفاً دوباره تلاش کنید.",
                reply_markup=ReplyKeyboardRemove()
            )
        
        return ConversationHandler.END
    
    async def cancel_registration(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """لغو ثبت‌نام"""
        await update.message.reply_text(
            "❌ ثبت‌نام لغو شد.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    
    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش منوی اصلی"""
        user = update.effective_user
        
        if not self.data_manager.user_exists(user.id):
            await update.message.reply_text("لطفاً ابتدا ثبت‌نام کنید.")
            return
        
        menu_text = f"🎓 منوی اصلی ربات استاد حاتمی\n\nسلام {user.first_name} عزیز! 👋\n\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:"
        
        keyboard = [
            [InlineKeyboardButton("🎓 دوره‌های استاد حاتمی", callback_data="courses")],
            [InlineKeyboardButton("📘 تهیه کتاب انفجار خلاقیت", callback_data="book")],
            [InlineKeyboardButton("📞 ارتباط با ما", callback_data="contact")],
            [InlineKeyboardButton("🌐 یوتیوب / اینستاگرام", callback_data="social")],
            [InlineKeyboardButton("💬 کانال و گروه همراه با استاد", callback_data="channel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if hasattr(update, 'message'):
            await update.message.reply_text(menu_text, reply_markup=reply_markup)
        else:
            await update.callback_query.edit_message_text(menu_text, reply_markup=reply_markup)
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پردازش کلیک دکمه‌ها"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "start_registration":
            await self.start_registration(update, context)
        elif query.data == "courses":
            await self.show_courses(query)
        elif query.data == "book":
            await self.show_book_info(query)
        elif query.data == "contact":
            await self.show_contact_info(query)
        elif query.data == "social":
            await self.show_social_links(query)
        elif query.data == "channel":
            await self.show_channel_info(query)
        elif query.data == "back_to_menu":
            await self.show_main_menu(update, context)
    
    async def show_courses(self, query):
        """نمایش دوره‌های استاد حاتمی"""
        courses_text = """🎓 دوره‌های استاد حاتمی

📚 دوره‌های موجود:

1️⃣ نظریه اعداد و ریاضی گسسته
   💰 قیمت: ۵۰۰,۰۰۰ تومان
   📅 مدت: دوره کامل
   🎯 مناسب: پایه دوازدهم ریاضی + المپیاد

2️⃣ مهارت‌های حل خلاق مسائل ریاضی
   💰 قیمت: رایگان
   📅 مدت: جمعه‌ها ساعت ۳
   🎯 مناسب: پایه‌های دهم، یازدهم و دوازدهم

3️⃣ کلاس‌های پایه (دهم، یازدهم، دوازدهم)
   💰 قیمت: رایگان
   📅 مدت: جمعه‌ها
   🎯 مناسب: همه پایه‌ها"""
        
        keyboard = [
            [InlineKeyboardButton("📝 ثبت‌نام در دوره", callback_data="register_course")],
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(courses_text, reply_markup=reply_markup)
    
    async def show_book_info(self, query):
        """نمایش اطلاعات کتاب"""
        book_text = """📘 کتاب انفجار خلاقیت

📖 اطلاعات کتاب:
   ✍️ نویسنده: استاد حاتمی
   📄 تعداد صفحات: ۴۰۰ صفحه
   💰 قیمت: ۲۵۰,۰۰۰ تومان

✨ ویژگی‌های کتاب:
   • مثال‌های حل شده
   • تمرینات متنوع
   • نمونه سوالات کنکور
   • پاسخ تشریحی

📞 برای سفارش کتاب با ما تماس بگیرید:"""
        
        keyboard = [
            [InlineKeyboardButton("📞 تماس برای سفارش", callback_data="contact")],
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(book_text, reply_markup=reply_markup)
    
    async def show_contact_info(self, query):
        """نمایش اطلاعات تماس"""
        contact_text = """📞 ارتباط با ما

📱 شماره تماس: ۰۹۱۲۳۴۵۶۷۸۹
📧 ایمیل: info@ostadhatami.ir
🏢 آدرس: تهران، ایران

⏰ ساعات کاری:
   شنبه تا چهارشنبه: ۹ صبح تا ۶ عصر

💬 پشتیبانی تلگرام: @Ostad_Hatami"""
        
        keyboard = [
            [InlineKeyboardButton("💬 پیام به پشتیبانی", callback_data="support_message")],
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(contact_text, reply_markup=reply_markup)
    
    async def show_social_links(self, query):
        """نمایش لینک‌های شبکه‌های اجتماعی"""
        social_text = """🌐 شبکه‌های اجتماعی استاد حاتمی

📺 یوتیوب:
   آموزش‌های رایگان ریاضی
   حل مسئله‌های خلاقانه
   تکنیک‌های حل مسئله

📸 اینستاگرام:
   نکات آموزشی روزانه
   نمونه سوالات
   اخبار و اطلاعیه‌ها"""
        
        keyboard = [
            [InlineKeyboardButton("📺 کانال یوتیوب", url="https://youtube.com/@OstadHatami")],
            [InlineKeyboardButton("📸 پیج اینستاگرام", url="https://instagram.com/OstadHatami")],
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(social_text, reply_markup=reply_markup)
    
    async def show_channel_info(self, query):
        """نمایش اطلاعات کانال و گروه"""
        channel_text = """💬 کانال و گروه همراه با استاد

📢 کانال تلگرام:
   • اخبار و اطلاعیه‌های کلاس‌ها
   • نمونه سوالات و پاسخ‌ها
   • نکات آموزشی مفید

👥 گروه مشاوره:
   • پرسش و پاسخ
   • رفع اشکال
   • مشاوره تحصیلی"""
        
        keyboard = [
            [InlineKeyboardButton("📢 عضویت در کانال", url="https://t.me/OstadHatamiChannel")],
            [InlineKeyboardButton("👥 عضویت در گروه", url="https://t.me/OstadHatamiGroup")],
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(channel_text, reply_markup=reply_markup)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """دستور راهنما"""
        help_text = """🔧 راهنمای استفاده از ربات

📝 دستورات اصلی:
/start - شروع ربات
/register - ثبت‌نام در ربات
/menu - نمایش منوی اصلی
/help - این راهنما

📚 امکانات ربات:
• ثبت‌نام در دوره‌های ریاضی
• تهیه کتاب انفجار خلاقیت
• ارتباط با پشتیبانی
• دسترسی به شبکه‌های اجتماعی
• عضویت در کانال و گروه

💡 نکات مهم:
• برای استفاده از ربات ابتدا باید ثبت‌نام کنید
• تمام اطلاعات شما به صورت امن ذخیره می‌شود
• در صورت بروز مشکل با پشتیبانی تماس بگیرید"""
        
        keyboard = [[InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(help_text, reply_markup=reply_markup)
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """مدیریت خطاها"""
        logger.error(f"Exception while handling an update: {context.error}")
        
        error_text = """❌ متأسفانه خطایی رخ داده است.

لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید.

📞 پشتیبانی: @Ostad_Hatami"""
        
        if update.effective_message:
            await update.effective_message.reply_text(error_text)
        elif update.callback_query:
            await update.callback_query.edit_message_text(error_text)

async def main():
    """تابع اصلی"""
    bot = OstadHatamiBot()
    logger.info("Bot started successfully")
    await bot.application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    asyncio.run(main()) 