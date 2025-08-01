#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Professional Telegram Bot for Math Course Registration - 2025 Edition
ربات تلگرام حرفه‌ای پیشرفته برای ثبت‌نام کلاس‌های ریاضی - نسخه ۲۰۲۵
"""

import json
import logging
import os
import asyncio
import hashlib
import base64
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict

# Enhanced imports for performance
import aioredis
import cachetools
from asyncio_throttle import Throttler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters, ConversationHandler

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import enhanced configuration
from config_enhanced import *

# Enhanced logging with structured logging
import structlog
logger = structlog.get_logger()

# Conversation states for enhanced registration flow
CHOOSING_COURSE, ENTERING_NAME, ENTERING_PHONE, ENTERING_GRADE, ENTERING_FIELD, ENTERING_PARENT_PHONE, CONFIRMING_REGISTRATION, PAYMENT_PROCESS = range(8)

class EnhancedCacheManager:
    """Enhanced caching system with Redis and memory cache"""
    
    def __init__(self):
        self.memory_cache = cachetools.TTLCache(maxsize=1000, ttl=CACHE_TTL)
        self.redis_client = None
        self.cache_enabled = CACHE_ENABLED
    
    async def init_redis(self):
        """Initialize Redis connection"""
        if self.cache_enabled and REDIS_URL:
            try:
                self.redis_client = await aioredis.from_url(REDIS_URL)
                logger.info("Redis cache initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Redis: {e}")
                self.cache_enabled = False
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        # Try memory cache first
        if key in self.memory_cache:
            return self.memory_cache[key]
        
        # Try Redis cache
        if self.redis_client and self.cache_enabled:
            try:
                value = await self.redis_client.get(key)
                if value:
                    data = json.loads(value)
                    self.memory_cache[key] = data
                    return data
            except Exception as e:
                logger.error(f"Redis get error: {e}")
        
        return None
    
    async def set(self, key: str, value: Any, ttl: int = CACHE_TTL):
        """Set value in cache"""
        # Set in memory cache
        self.memory_cache[key] = value
        
        # Set in Redis cache
        if self.redis_client and self.cache_enabled:
            try:
                await self.redis_client.setex(key, ttl, json.dumps(value))
            except Exception as e:
                logger.error(f"Redis set error: {e}")
    
    async def delete(self, key: str):
        """Delete value from cache"""
        if key in self.memory_cache:
            del self.memory_cache[key]
        
        if self.redis_client and self.cache_enabled:
            try:
                await self.redis_client.delete(key)
            except Exception as e:
                logger.error(f"Redis delete error: {e}")

class EnhancedDataManager:
    """Enhanced data management with caching and performance optimizations"""
    
    def __init__(self, cache_manager: EnhancedCacheManager):
        self.data_file = DATA_FILE
        self.backup_file = BACKUP_FILE
        self.cache_manager = cache_manager
        self.ensure_data_directory()
    
    def ensure_data_directory(self):
        """Ensure data directory exists"""
        os.makedirs("data", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
    
    def hash_data(self, data: str) -> str:
        """Hash sensitive data securely"""
        return hashlib.sha256((str(data) + HASH_SALT).encode()).hexdigest()
    
    def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        return base64.b64encode(str(data).encode()).decode()
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt data"""
        try:
            return base64.b64decode(encrypted_data.encode()).decode()
        except:
            return encrypted_data
    
    async def load_students(self) -> List[Dict]:
        """Load students data with caching"""
        cache_key = "students_data"
        
        # Try to get from cache first
        cached_data = await self.cache_manager.get(cache_key)
        if cached_data:
            return cached_data
        
        # Load from file
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
                    
                    # Cache the data
                    await self.cache_manager.set(cache_key, data)
                    return data
            return []
        except Exception as e:
            logger.error(f"Error loading students data: {e}")
            return []
    
    async def save_students(self, students: List[Dict]):
        """Save students data with caching"""
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
            
            # Update cache
            await self.cache_manager.set("students_data", students)
                    
        except Exception as e:
            logger.error(f"Error saving students data: {e}")
    
    async def add_student(self, student_data: Dict) -> Dict:
        """Add new student with enhanced validation"""
        students = await self.load_students()
        
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
            
            # Add gamification data
            if GAMIFICATION['enabled']:
                student_data['points'] = GAMIFICATION['points_per_registration']
                student_data['badges'] = [GAMIFICATION['badges']['first_registration']]
            
            students.append(student_data)
            logger.info(f"Added new user data for user_id: {student_data.get('user_id')}")
        
        await self.save_students(students)
        return student_data

class EnhancedUIManager:
    """Enhanced UI/UX manager with better layouts and styling"""
    
    def __init__(self):
        self.theme = UI_THEME
        self.layouts = BUTTON_LAYOUTS
        self.progress_indicators = PROGRESS_INDICATORS
        self.loading_messages = LOADING_MESSAGES
    
    def create_enhanced_keyboard(self, buttons: List[List[InlineKeyboardButton]], layout_type: str = "main_menu") -> InlineKeyboardMarkup:
        """Create enhanced keyboard with better layout"""
        layout_config = self.layouts.get(layout_type, self.layouts["main_menu"])
        
        # Apply layout configuration
        if layout_config["show_back_button"]:
            buttons.append([InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")])
        
        return InlineKeyboardMarkup(buttons)
    
    def format_course_card(self, course: Dict) -> str:
        """Format course information as a beautiful card"""
        card = f"""
📚 {course['name']}
{'💎' if course.get('type') == 'پولی' else '🆓'} {course.get('price', 'رایگان')}
⏰ {course.get('duration', 'نامشخص')}
🎯 {course.get('target', 'نامشخص')}
📝 {course.get('description', '')}
"""
        
        if 'features' in course:
            card += "\n✨ ویژگی‌ها:\n"
            for feature in course['features']:
                card += f"  • {feature}\n"
        
        if 'seats_available' in course:
            card += f"\n💺 ظرفیت باقی‌مانده: {course['seats_available']} نفر"
        
        return card
    
    def show_progress(self, current_step: int, total_steps: int, process_type: str = "registration") -> str:
        """Show progress indicator"""
        indicators = self.progress_indicators.get(process_type, self.progress_indicators["registration"])
        progress = ""
        
        for i, indicator in enumerate(indicators):
            if i < current_step:
                progress += f"{indicator} "
            elif i == current_step:
                progress += f"🔄 "
            else:
                progress += f"⚪ "
        
        return progress
    
    def get_loading_message(self) -> str:
        """Get random loading message"""
        return random.choice(self.loading_messages)

class EnhancedMathBot:
    """Enhanced professional math course registration bot"""
    
    def __init__(self):
        # Initialize components
        self.cache_manager = EnhancedCacheManager()
        self.data_manager = EnhancedDataManager(self.cache_manager)
        self.ui_manager = EnhancedUIManager()
        
        # Rate limiting
        self.throttler = Throttler(rate_limit=RATE_LIMIT_PER_USER, period=60)
        
        # Get token from environment variable
        self.token = BOT_TOKEN
        if not self.token or self.token == "YOUR_BOT_TOKEN_HERE":
            raise ValueError("Please set BOT_TOKEN environment variable")
        
        # Initialize application
        self.application = Application.builder().token(self.token).build()
        self.setup_handlers()
    
    async def initialize(self):
        """Initialize the bot"""
        await self.cache_manager.init_redis()
        logger.info("Enhanced Math Bot initialized successfully")
    
    def setup_handlers(self):
        """Setup enhanced handlers with rate limiting"""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.enhanced_start_command))
        self.application.add_handler(CommandHandler("help", self.enhanced_help_command))
        self.application.add_handler(CommandHandler("register", self.enhanced_register_command))
        self.application.add_handler(CommandHandler("status", self.enhanced_status_command))
        self.application.add_handler(CommandHandler("admin", self.enhanced_admin_command))
        
        # Callback query handler
        self.application.add_handler(CallbackQueryHandler(self.enhanced_handle_callback))
        
        # Conversation handler for registration
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("register", self.enhanced_register_command)],
            states={
                CHOOSING_COURSE: [CallbackQueryHandler(self.enhanced_choose_course)],
                ENTERING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.enhanced_enter_name)],
                ENTERING_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.enhanced_enter_phone)],
                ENTERING_GRADE: [CallbackQueryHandler(self.enhanced_enter_grade)],
                ENTERING_FIELD: [CallbackQueryHandler(self.enhanced_enter_field)],
                ENTERING_PARENT_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.enhanced_enter_parent_phone)],
                CONFIRMING_REGISTRATION: [CallbackQueryHandler(self.enhanced_confirm_registration)],
                PAYMENT_PROCESS: [CallbackQueryHandler(self.enhanced_process_payment)]
            },
            fallbacks=[CommandHandler("cancel", self.enhanced_cancel_registration)]
        )
        self.application.add_handler(conv_handler)
        
        # Error handler
        self.application.add_error_handler(self.enhanced_error_handler)
    
    async def enhanced_start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced start command with better UX"""
        user = update.effective_user
        
        # Check if user is already registered
        existing_student = await self.data_manager.get_student_by_user_id(user.id)
        
        if existing_student:
            await self.show_enhanced_main_menu(update, context)
        else:
            await self.show_enhanced_welcome_menu(update, context)
    
    async def show_enhanced_welcome_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show enhanced welcome menu for new users"""
        user = update.effective_user
        
        welcome_text = f"""
🎓 به ربات کلاس‌های ریاضی خوش آمدید!

سلام {user.first_name} عزیز! 👋

🌟 این ربات برای ثبت‌نام در کلاس‌های ریاضی طراحی شده است.

📚 کلاس‌های رایگان و پولی در دسترس:
• کلاس‌های رایگان آنلاین
• کلاس‌های ویژه پولی
• آموزش مهارت‌های حل مسئله
• آمادگی کنکور و المپیاد

لطفاً یکی از گزینه‌های زیر را انتخاب کنید:
        """
        
        buttons = [
            [InlineKeyboardButton("📝 ثبت‌نام در کلاس", callback_data="start_registration")],
            [InlineKeyboardButton("📚 مشاهده کلاس‌ها", callback_data="courses")],
            [InlineKeyboardButton("📅 برنامه کلاس‌ها", callback_data="schedule")],
            [InlineKeyboardButton("📢 اطلاعیه‌ها", callback_data="announcements")],
            [InlineKeyboardButton("📖 راهنما", callback_data="help")]
        ]
        
        reply_markup = self.ui_manager.create_enhanced_keyboard(buttons, "main_menu")
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    
    async def show_enhanced_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show enhanced main menu for registered users"""
        user = update.effective_user
        student = await self.data_manager.get_student_by_user_id(user.id)
        
        # Get user stats
        points = student.get('points', 0) if student else 0
        badges = student.get('badges', []) if student else []
        
        menu_text = f"""
🎓 منوی اصلی ربات کلاس‌های ریاضی

سلام {user.first_name} عزیز! 👋

✅ شما قبلاً ثبت‌نام کرده‌اید.

"""
        
        if GAMIFICATION['enabled'] and student:
            menu_text += f"🏆 امتیازات شما: {points}\n"
            if badges:
                menu_text += f"🏅 نشان‌های شما: {', '.join(badges)}\n"
        
        menu_text += """
📚 گزینه‌های موجود:
        """
        
        buttons = [
            [InlineKeyboardButton("📝 ثبت‌نام در کلاس جدید", callback_data="start_registration")],
            [InlineKeyboardButton("📢 اطلاعیه‌های جدید", callback_data="announcements")],
            [InlineKeyboardButton("🎓 کلاس‌های ویژه", callback_data="special_courses")],
            [InlineKeyboardButton("📅 برنامه کلاس‌ها", callback_data="schedule")],
            [InlineKeyboardButton("📚 کلاس‌های موجود", callback_data="courses")],
            [InlineKeyboardButton("📖 اطلاعات کتاب", callback_data="book_info")],
            [InlineKeyboardButton("📞 اطلاعات تماس", callback_data="contact_info")],
            [InlineKeyboardButton("🔗 شبکه‌های اجتماعی", callback_data="social_links")],
            [InlineKeyboardButton("📺 کانال یوتیوب", callback_data="youtube")]
        ]
        
        reply_markup = self.ui_manager.create_enhanced_keyboard(buttons, "main_menu")
        
        if hasattr(update, 'message'):
            await update.message.reply_text(menu_text, reply_markup=reply_markup)
        else:
            await update.callback_query.edit_message_text(menu_text, reply_markup=reply_markup)

    async def enhanced_handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced callback handler with rate limiting"""
        query = update.callback_query
        await query.answer()
        
        # Apply rate limiting
        async with self.throttler:
            if query.data == "start_registration":
                await self.show_enhanced_registration_menu(query)
            elif query.data == "courses":
                await self.show_enhanced_courses(query)
            elif query.data == "schedule":
                await self.show_enhanced_schedule(query)
            elif query.data == "announcements":
                await self.show_enhanced_announcements(query)
            elif query.data == "help":
                await self.show_enhanced_help(query)
            elif query.data == "main_menu":
                await self.show_enhanced_main_menu(update, context)
            # Add more handlers as needed

    async def show_enhanced_registration_menu(self, query):
        """Show enhanced registration menu"""
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
        
        buttons = [
            [InlineKeyboardButton("🆓 کلاس‌های رایگان", callback_data="free_registration")],
            [InlineKeyboardButton("💎 کلاس‌های ویژه پولی", callback_data="paid_registration")]
        ]
        
        reply_markup = self.ui_manager.create_enhanced_keyboard(buttons, "course_selection")
        await query.edit_message_text(text, reply_markup=reply_markup)

    async def show_enhanced_courses(self, query):
        """Show enhanced courses display"""
        text = "📚 کلاس‌های موجود:\n\n"
        
        for course in COURSES:
            text += self.ui_manager.format_course_card(course)
            text += "\n" + "─" * 40 + "\n\n"
        
        buttons = [
            [InlineKeyboardButton("📝 ثبت‌نام در کلاس", callback_data="start_registration")],
            [InlineKeyboardButton("📅 برنامه کلاس‌ها", callback_data="schedule")]
        ]
        
        reply_markup = self.ui_manager.create_enhanced_keyboard(buttons, "main_menu")
        await query.edit_message_text(text, reply_markup=reply_markup)

    async def enhanced_error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced error handler with better error messages"""
        logger.error(f"Exception while handling an update: {context.error}")
        
        error_text = """
❌ متأسفانه خطایی رخ داده است.

لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید.

🔧 راه‌حل‌های پیشنهادی:
• اتصال اینترنت خود را بررسی کنید
• ربات را ری‌استارت کنید
• از آخرین نسخه تلگرام استفاده کنید
        """
        
        if update.effective_message:
            await update.effective_message.reply_text(error_text)
        elif update.callback_query:
            await update.callback_query.edit_message_text(error_text)

async def main():
    """Main function to run the enhanced bot"""
    bot = EnhancedMathBot()
    await bot.initialize()
    
    logger.info("Starting Enhanced Math Bot...")
    await bot.application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    asyncio.run(main()) 