#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Super Advanced Math Course Registration Bot 2025
ربات پیشرفته ثبت‌نام کلاس‌های ریاضی با قابلیت‌های هوش مصنوعی
"""

import asyncio
import json
import logging
import os
import redis
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

import openai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)

# Import enhanced configuration
from enhanced_config import *

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE) if os.path.exists(os.path.dirname(LOG_FILE)) else logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Redis for caching
try:
    redis_client = redis.Redis(
        host=REDIS_CONFIG["host"],
        port=REDIS_CONFIG["port"],
        db=REDIS_CONFIG["db"],
        password=REDIS_CONFIG["password"],
        decode_responses=True
    )
    redis_client.ping()
    logger.info("✅ Redis connection established")
except Exception as e:
    logger.warning(f"⚠️ Redis not available: {e}")
    redis_client = None

# Initialize OpenAI
if AI_CONFIG["openai_api_key"]:
    openai.api_key = AI_CONFIG["openai_api_key"]
    logger.info("✅ OpenAI API configured")
else:
    logger.warning("⚠️ OpenAI API key not configured")

# Conversation states
class ConversationState(Enum):
    CHOOSING_ACTION = 1
    ENTERING_NAME = 2
    ENTERING_PHONE = 3
    ENTERING_GRADE = 4
    CONFIRMING_REGISTRATION = 5
    PAYMENT_PROCESS = 6
    VOICE_INPUT = 7
    AI_CHAT = 8

# Data classes for better structure
@dataclass
class UserProfile:
    user_id: int
    name: str = ""
    phone: str = ""
    grade: str = ""
    points: int = 0
    level: int = 1
    badges: List[str] = None
    courses_enrolled: List[str] = None
    preferences: Dict = None
    created_at: str = ""
    last_active: str = ""
    language: str = "fa"
    subscription_plan: str = "free"
    
    def __post_init__(self):
        if self.badges is None:
            self.badges = []
        if self.courses_enrolled is None:
            self.courses_enrolled = []
        if self.preferences is None:
            self.preferences = {}
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.last_active:
            self.last_active = datetime.now().isoformat()

@dataclass
class CourseEnrollment:
    user_id: int
    course_id: str
    enrollment_date: str
    status: str = "active"
    progress: float = 0.0
    completion_date: str = ""

class AdvancedDataManager:
    """Advanced data management with caching and optimization"""
    
    def __init__(self):
        self.redis = redis_client
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database with proper schema"""
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                name TEXT,
                phone TEXT,
                grade TEXT,
                points INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                badges TEXT,
                courses_enrolled TEXT,
                preferences TEXT,
                created_at TEXT,
                last_active TEXT,
                language TEXT DEFAULT 'fa',
                subscription_plan TEXT DEFAULT 'free'
            )
        ''')
        
        # Enrollments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS enrollments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                course_id TEXT,
                enrollment_date TEXT,
                status TEXT DEFAULT 'active',
                progress REAL DEFAULT 0.0,
                completion_date TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Analytics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT,
                timestamp TEXT,
                data TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("✅ Database initialized")
    
    def get_user(self, user_id: int) -> Optional[UserProfile]:
        """Get user with caching"""
        # Try cache first
        if self.redis:
            cached = self.redis.get(f"user:{user_id}")
            if cached:
                data = json.loads(cached)
                return UserProfile(**data)
        
        # Get from database
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            user = UserProfile(
                user_id=row[0],
                name=row[1] or "",
                phone=row[2] or "",
                grade=row[3] or "",
                points=row[4] or 0,
                level=row[5] or 1,
                badges=json.loads(row[6]) if row[6] else [],
                courses_enrolled=json.loads(row[7]) if row[7] else [],
                preferences=json.loads(row[8]) if row[8] else {},
                created_at=row[9] or "",
                last_active=row[10] or "",
                language=row[11] or "fa",
                subscription_plan=row[12] or "free"
            )
            
            # Cache for 1 hour
            if self.redis:
                self.redis.setex(f"user:{user_id}", 3600, json.dumps(asdict(user)))
            
            return user
        return None
    
    def save_user(self, user: UserProfile):
        """Save user with caching"""
        user.last_active = datetime.now().isoformat()
        
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO users 
            (user_id, name, phone, grade, points, level, badges, courses_enrolled, 
             preferences, created_at, last_active, language, subscription_plan)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user.user_id, user.name, user.phone, user.grade, user.points, user.level,
            json.dumps(user.badges), json.dumps(user.courses_enrolled),
            json.dumps(user.preferences), user.created_at, user.last_active,
            user.language, user.subscription_plan
        ))
        
        conn.commit()
        conn.close()
        
        # Update cache
        if self.redis:
            self.redis.setex(f"user:{user.user_id}", 3600, json.dumps(asdict(user)))
    
    def track_analytics(self, user_id: int, action: str, data: Dict = None):
        """Track user analytics"""
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO analytics (user_id, action, timestamp, data)
            VALUES (?, ?, ?, ?)
        ''', (user_id, action, datetime.now().isoformat(), json.dumps(data or {})))
        
        conn.commit()
        conn.close()

class AIAssistant:
    """Advanced AI assistant with GPT integration"""
    
    def __init__(self):
        self.openai = openai if AI_CONFIG["openai_api_key"] else None
    
    async def answer_question(self, user_id: int, question: str, user_context: Dict = None) -> str:
        """Answer user questions using GPT"""
        if not self.openai:
            return "متأسفانه سرویس هوش مصنوعی در دسترس نیست."
        
        try:
            # Create context-aware prompt
            context = user_context or {}
            prompt = f"""
            You are a helpful math tutor assistant. The student is studying {context.get('current_topic', 'mathematics')} 
            and has a learning level of {context.get('level', 'intermediate')}.
            
            Student question: {question}
            
            Provide a helpful, step-by-step explanation in Persian. Be encouraging and educational.
            """
            
            response = await openai.ChatCompletion.acreate(
                model=AI_CONFIG["gpt_model"],
                messages=[
                    {"role": "system", "content": "You are a helpful math tutor assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=AI_CONFIG["max_tokens"],
                temperature=AI_CONFIG["temperature"]
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"AI error: {e}")
            return "متأسفانه خطایی در پردازش سوال شما رخ داد. لطفاً دوباره تلاش کنید."
    
    async def recommend_courses(self, user_profile: UserProfile) -> List[Dict]:
        """Recommend courses based on user profile"""
        if not self.openai:
            return COURSES[:3]  # Fallback to first 3 courses
        
        try:
            prompt = f"""
            Recommend 3 math courses for a student with:
            - Grade: {user_profile.grade}
            - Current level: {user_profile.level}
            - Enrolled courses: {user_profile.courses_enrolled}
            - Points: {user_profile.points}
            
            Available courses: {[c['name'] for c in COURSES]}
            
            Return only the course names in Persian, separated by commas.
            """
            
            response = await openai.ChatCompletion.acreate(
                model=AI_CONFIG["gpt_model"],
                messages=[
                    {"role": "system", "content": "You are a course recommendation assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.3
            )
            
            recommended_names = response.choices[0].message.content.split(',')
            recommended_courses = []
            
            for course in COURSES:
                if any(name.strip() in course['name'] for name in recommended_names):
                    recommended_courses.append(course)
            
            return recommended_courses[:3]
        except Exception as e:
            logger.error(f"Recommendation error: {e}")
            return COURSES[:3]
    
    async def personalize_message(self, user_profile: UserProfile, template: str) -> str:
        """Personalize messages based on user profile"""
        if not self.openai:
            return template
        
        try:
            prompt = f"""
            Personalize this message for a student:
            Template: {template}
            
            Student info:
            - Name: {user_profile.name}
            - Grade: {user_profile.grade}
            - Level: {user_profile.level}
            - Points: {user_profile.points}
            - Language: {user_profile.language}
            
            Make it more personal and engaging while keeping the same meaning.
            """
            
            response = await openai.ChatCompletion.acreate(
                model=AI_CONFIG["gpt_model"],
                messages=[
                    {"role": "system", "content": "You are a personalization assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.7
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Personalization error: {e}")
            return template

class GamificationSystem:
    """Advanced gamification system"""
    
    def __init__(self, data_manager: AdvancedDataManager):
        self.data_manager = data_manager
    
    def award_points(self, user_id: int, action: str) -> int:
        """Award points for actions"""
        points = GAMIFICATION_CONFIG["points_per_action"].get(action, 0)
        
        user = self.data_manager.get_user(user_id)
        if user:
            user.points += points
            user.level = self.calculate_level(user.points)
            self.data_manager.save_user(user)
            
            # Track analytics
            self.data_manager.track_analytics(user_id, "points_awarded", {
                "action": action,
                "points": points,
                "total_points": user.points
            })
        
        return points
    
    def calculate_level(self, points: int) -> int:
        """Calculate user level based on points"""
        for level, config in GAMIFICATION_CONFIG["levels"].items():
            if points >= config["min_points"]:
                continue
            return level - 1
        return len(GAMIFICATION_CONFIG["levels"])
    
    def check_achievements(self, user_id: int) -> List[str]:
        """Check for new achievements"""
        user = self.data_manager.get_user(user_id)
        if not user:
            return []
        
        new_achievements = []
        
        # Check for achievements
        if len(user.courses_enrolled) == 1 and "first_registration" not in user.badges:
            new_achievements.append("first_registration")
            user.badges.append("first_registration")
        
        if user.points >= 1000 and "veteran" not in user.badges:
            new_achievements.append("veteran")
            user.badges.append("veteran")
        
        if new_achievements:
            self.data_manager.save_user(user)
            self.data_manager.track_analytics(user_id, "achievement_unlocked", {
                "achievements": new_achievements
            })
        
        return new_achievements

class VoiceHandler:
    """Voice input/output handler"""
    
    def __init__(self):
        self.enabled = VOICE_CONFIG["enable_voice_input"]
    
    async def process_voice_message(self, voice_file) -> str:
        """Convert voice message to text"""
        if not self.enabled:
            return "دستورات صوتی غیرفعال است."
        
        try:
            # This would integrate with speech recognition service
            # For now, return a placeholder
            return "پیام صوتی شما دریافت شد. (قابلیت تشخیص صدا در حال توسعه است)"
        except Exception as e:
            logger.error(f"Voice processing error: {e}")
            return "خطا در پردازش پیام صوتی"
    
    async def text_to_speech(self, text: str) -> bytes:
        """Convert text to speech"""
        if not VOICE_CONFIG["enable_voice_output"]:
            return None
        
        try:
            # This would integrate with TTS service
            # For now, return None
            return None
        except Exception as e:
            logger.error(f"TTS error: {e}")
            return None

class SuperAdvancedBot:
    """Super advanced bot with all features"""
    
    def __init__(self):
        self.data_manager = AdvancedDataManager()
        self.ai_assistant = AIAssistant()
        self.gamification = GamificationSystem(self.data_manager)
        self.voice_handler = VoiceHandler()
        
        # Initialize application
        self.application = Application.builder().token(BOT_TOKEN).build()
        self.setup_handlers()
        
        logger.info("🚀 Super Advanced Bot initialized")
    
    def setup_handlers(self):
        """Setup all command and callback handlers"""
        
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.smart_welcome))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("profile", self.profile_command))
        self.application.add_handler(CommandHandler("courses", self.courses_command))
        self.application.add_handler(CommandHandler("ask", self.ai_chat_command))
        self.application.add_handler(CommandHandler("voice", self.voice_command))
        self.application.add_handler(CommandHandler("admin", self.admin_command))
        
        # Callback query handler
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # Message handler for voice and text
        self.application.add_handler(MessageHandler(
            filters.VOICE | filters.TEXT & ~filters.COMMAND, 
            self.handle_message
        ))
        
        # Conversation handler for registration
        conv_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.start_registration, pattern="^register$")],
            states={
                ConversationState.ENTERING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.enter_name)],
                ConversationState.ENTERING_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.enter_phone)],
                ConversationState.ENTERING_GRADE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.enter_grade)],
                ConversationState.CONFIRMING_REGISTRATION: [CallbackQueryHandler(self.confirm_registration)],
            },
            fallbacks=[CallbackQueryHandler(self.cancel_registration, pattern="^cancel$")]
        )
        self.application.add_handler(conv_handler)
    
    async def smart_welcome(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Smart welcome with personalization"""
        user = update.effective_user
        user_profile = self.data_manager.get_user(user.id)
        
        # Track analytics
        self.data_manager.track_analytics(user.id, "bot_started")
        
        if user_profile:
            # Returning user
            welcome_text = await self.ai_assistant.personalize_message(user_profile, f"""
🎉 <b>خوش برگشتی {user.first_name}!</b>

📊 <b>وضعیت شما:</b>
• سطح: {GAMIFICATION_CONFIG['levels'][user_profile.level]['name']}
• امتیازات: {user_profile.points:,} امتیاز
• کلاس‌های ثبت‌نام شده: {len(user_profile.courses_enrolled)} کلاس

🎯 <b>پیشنهاد بعدی:</b>
{await self.get_next_recommendation(user_profile)}
            """)
        else:
            # New user
            welcome_text = f"""
🚀 <b>به ربات هوشمند کلاس‌های ریاضی خوش آمدید!</b>

👋 سلام {user.first_name} عزیز!

🤖 <b>ویژگی‌های پیشرفته:</b>
• هوش مصنوعی برای پاسخ به سوالات
• مسیر یادگیری شخصی‌سازی شده
• پشتیبانی صوتی
• سیستم امتیازدهی و دستاوردها
• کلاس‌های تعاملی

🎯 <b>برای شروع:</b>
            """
        
        keyboard = self.create_smart_keyboard(user_profile)
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='HTML')
    
    def create_smart_keyboard(self, user_profile: Optional[UserProfile] = None) -> List[List[InlineKeyboardButton]]:
        """Create smart contextual keyboard"""
        if not user_profile:
            # New user keyboard
            return [
                [InlineKeyboardButton("🚀 ثبت‌نام سریع", callback_data="register")],
                [InlineKeyboardButton("📚 مشاهده کلاس‌ها", callback_data="courses")],
                [InlineKeyboardButton("❓ راهنما", callback_data="help")],
                [InlineKeyboardButton("🎯 آزمون تعیین سطح", callback_data="placement_test")]
            ]
        else:
            # Returning user keyboard
            return [
                [InlineKeyboardButton("📊 پروفایل من", callback_data="profile")],
                [InlineKeyboardButton("🎯 کلاس بعدی", callback_data="next_class")],
                [InlineKeyboardButton("💬 سوال از استاد", callback_data="ask_question")],
                [InlineKeyboardButton("📖 مواد آموزشی", callback_data="materials")],
                [InlineKeyboardButton("🎮 دستاوردها", callback_data="achievements")],
                [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu")]
            ]
    
    async def get_next_recommendation(self, user_profile: UserProfile) -> str:
        """Get personalized next recommendation"""
        if not user_profile.courses_enrolled:
            return "📚 ثبت‌نام در اولین کلاس"
        
        # Get AI recommendations
        recommended_courses = await self.ai_assistant.recommend_courses(user_profile)
        
        if recommended_courses:
            return f"📚 {recommended_courses[0]['name']}"
        
        return "🎯 ادامه یادگیری"
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        user_profile = self.data_manager.get_user(user_id)
        
        # Track analytics
        self.data_manager.track_analytics(user_id, "button_clicked", {"button": query.data})
        
        if query.data == "register":
            await self.start_registration(update, context)
        elif query.data == "courses":
            await self.show_courses(query)
        elif query.data == "profile":
            await self.show_profile(query)
        elif query.data == "help":
            await self.show_help(query)
        elif query.data == "ask_question":
            await self.start_ai_chat(query)
        elif query.data == "achievements":
            await self.show_achievements(query)
        elif query.data == "main_menu":
            await self.show_main_menu(query)
        else:
            await query.edit_message_text("این گزینه در حال توسعه است.")
    
    async def show_courses(self, query):
        """Show available courses with AI recommendations"""
        user_id = query.from_user.id
        user_profile = self.data_manager.get_user(user_id)
        
        text = "📚 <b>کلاس‌های موجود</b>\n\n"
        
        # Get AI recommendations for returning users
        if user_profile:
            recommended_courses = await self.ai_assistant.recommend_courses(user_profile)
            if recommended_courses:
                text += "🤖 <b>پیشنهادات هوشمند:</b>\n"
                for i, course in enumerate(recommended_courses, 1):
                    text += f"{i}. {course['name']} - {course['price']}\n"
                text += "\n"
        
        # Show all courses
        for course in COURSES:
            text += f"📖 <b>{course['name']}</b>\n"
            text += f"💰 {course['price']}\n"
            text += f"📅 {course['duration']}\n"
            text += f"🎯 سطح: {course['difficulty']}\n\n"
        
        keyboard = [
            [InlineKeyboardButton(f"📝 ثبت‌نام در {course['name']}", callback_data=f"enroll_{course['id']}")]
            for course in COURSES[:3]
        ]
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
    
    async def show_profile(self, query):
        """Show user profile with gamification"""
        user_id = query.from_user.id
        user_profile = self.data_manager.get_user(user_id)
        
        if not user_profile:
            await query.edit_message_text("پروفایل شما یافت نشد.")
            return
        
        level_config = GAMIFICATION_CONFIG['levels'][user_profile.level]
        
        text = f"""
📊 <b>پروفایل {query.from_user.first_name}</b>

🏆 <b>سطح:</b> {level_config['name']} (سطح {user_profile.level})
⭐ <b>امتیازات:</b> {user_profile.points:,} امتیاز
📚 <b>کلاس‌های ثبت‌نام شده:</b> {len(user_profile.courses_enrolled)} کلاس
📅 <b>عضویت از:</b> {user_profile.created_at[:10]}

🏅 <b>دستاوردها:</b>
"""
        
        for badge in user_profile.badges:
            badge_config = GAMIFICATION_CONFIG['badges'].get(badge, {})
            text += f"• {badge_config.get('name', badge)}\n"
        
        if not user_profile.badges:
            text += "هنوز دستاوردی کسب نکرده‌اید.\n"
        
        # Check for new achievements
        new_achievements = self.gamification.check_achievements(user_id)
        if new_achievements:
            text += f"\n🎉 <b>دستاورد جدید!</b>\n"
            for achievement in new_achievements:
                badge_config = GAMIFICATION_CONFIG['badges'].get(achievement, {})
                text += f"🏆 {badge_config.get('name', achievement)}\n"
        
        keyboard = [
            [InlineKeyboardButton("🎯 ادامه یادگیری", callback_data="next_class")],
            [InlineKeyboardButton("📚 کلاس‌های جدید", callback_data="courses")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
    
    async def start_ai_chat(self, query):
        """Start AI chat session"""
        text = """
🤖 <b>چت با استاد هوشمند</b>

لطفاً سوال ریاضی خود را بپرسید. من آماده کمک به شما هستم!

💡 <b>نکات:</b>
• سوالات خود را به فارسی بپرسید
• می‌توانید از پیام صوتی استفاده کنید
• برای خروج از چت، /cancel را تایپ کنید
        """
        
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
        return ConversationState.AI_CHAT
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text and voice messages"""
        user_id = update.effective_user.id
        user_profile = self.data_manager.get_user(user_id)
        
        # Handle voice messages
        if update.message.voice:
            text = await self.voice_handler.process_voice_message(update.message.voice)
            await update.message.reply_text(f"🎤 {text}")
            return
        
        text = update.message.text
        
        # Check if in AI chat mode
        if context.user_data.get('ai_chat_mode'):
            response = await self.ai_assistant.answer_question(
                user_id, text, 
                {"current_topic": "mathematics", "level": user_profile.level if user_profile else "beginner"}
            )
            await update.message.reply_text(response, parse_mode='HTML')
            return
        
        # Default response
        await update.message.reply_text(
            "برای استفاده از ربات، از منوی اصلی استفاده کنید یا /start را تایپ کنید."
        )
    
    # Registration flow methods
    async def start_registration(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start smart registration process"""
        query = update.callback_query
        await query.answer()
        
        text = """
🚀 <b>ثبت‌نام سریع و هوشمند</b>

لطفاً نام و پایه تحصیلی خود را در یک پیام بنویسید:
مثال: "علی احمدی - پایه دهم"

💡 <b>نکته:</b> می‌توانید از پیام صوتی نیز استفاده کنید
        """
        
        keyboard = [[InlineKeyboardButton("❌ انصراف", callback_data="cancel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
        return ConversationState.ENTERING_NAME
    
    async def enter_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle name and grade input"""
        text = update.message.text
        user_id = update.effective_user.id
        
        # Simple parsing (in production, use NLP)
        if " - " in text:
            name, grade = text.split(" - ", 1)
        else:
            name = text
            grade = "نامشخص"
        
        # Create user profile
        user_profile = UserProfile(
            user_id=user_id,
            name=name.strip(),
            grade=grade.strip()
        )
        
        # Award points for registration
        points = self.gamification.award_points(user_id, "registration")
        
        # Save user
        self.data_manager.save_user(user_profile)
        
        # Show confirmation
        confirmation_text = f"""
✅ <b>ثبت‌نام شما با موفقیت انجام شد!</b>

👤 <b>اطلاعات شما:</b>
• نام: {name}
• پایه: {grade}
• امتیاز کسب شده: +{points} امتیاز

🎯 <b>مرحله بعدی:</b>
پیشنهاد می‌کنم در کلاس‌های مناسب پایه شما ثبت‌نام کنید.
        """
        
        keyboard = [
            [InlineKeyboardButton("📚 مشاهده کلاس‌ها", callback_data="courses")],
            [InlineKeyboardButton("🎯 آزمون تعیین سطح", callback_data="placement_test")],
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(confirmation_text, reply_markup=reply_markup, parse_mode='HTML')
        return ConversationHandler.END
    
    # Admin methods
    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Advanced admin panel"""
        user_id = update.effective_user.id
        username = update.effective_user.username
        
        # Check admin permissions
        is_admin = any(admin.replace('@', '') == username for admin in ADMIN_IDS)
        if not is_admin:
            await update.message.reply_text("❌ دسترسی غیرمجاز!")
            return
        
        # Get analytics
        total_users = self.get_total_users()
        active_users = self.get_active_users()
        total_enrollments = self.get_total_enrollments()
        
        text = f"""
🔧 <b>پنل مدیریت پیشرفته</b>

📊 <b>آمار کلی:</b>
• کل کاربران: {total_users}
• کاربران فعال: {active_users}
• کل ثبت‌نام‌ها: {total_enrollments}

🤖 <b>وضعیت سیستم:</b>
• هوش مصنوعی: {'فعال' if AI_CONFIG['openai_api_key'] else 'غیرفعال'}
• کش: {'فعال' if redis_client else 'غیرفعال'}
• صدا: {'فعال' if VOICE_CONFIG['enable_voice_input'] else 'غیرفعال'}

📈 <b>ویژگی‌های مدیریت:</b>
        """
        
        keyboard = [
            [InlineKeyboardButton("📢 ارسال اطلاعیه", callback_data="admin_broadcast")],
            [InlineKeyboardButton("📊 آمار تفصیلی", callback_data="admin_analytics")],
            [InlineKeyboardButton("👥 مدیریت کاربران", callback_data="admin_users")],
            [InlineKeyboardButton("⚙️ تنظیمات سیستم", callback_data="admin_settings")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')
    
    # Helper methods
    def get_total_users(self) -> int:
        """Get total number of users"""
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users')
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def get_active_users(self) -> int:
        """Get number of active users (last 7 days)"""
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM users 
            WHERE last_active > datetime('now', '-7 days')
        ''')
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def get_total_enrollments(self) -> int:
        """Get total number of enrollments"""
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM enrollments')
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    # Additional command methods
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Advanced help command"""
        help_text = """
🔧 <b>راهنمای استفاده از ربات پیشرفته</b>

📝 <b>دستورات اصلی:</b>
/start - منوی اصلی ربات
/profile - پروفایل و امتیازات
/courses - مشاهده کلاس‌ها
/ask - چت با استاد هوشمند
/voice - فعال‌سازی دستورات صوتی
/help - این راهنما

🤖 <b>ویژگی‌های هوش مصنوعی:</b>
• پاسخ خودکار به سوالات ریاضی
• پیشنهادات شخصی‌سازی شده
• مسیر یادگیری هوشمند
• تحلیل پیشرفت

🎮 <b>سیستم امتیازدهی:</b>
• کسب امتیاز برای فعالیت‌ها
• دستاوردها و نشان‌ها
• سطوح مختلف کاربری
• رقابت با سایر کاربران

💎 <b>اشتراک‌های ویژه:</b>
• برنزی: دسترسی پایه
• نقره‌ای: ویژگی‌های پیشرفته
• طلایی: دسترسی کامل

📞 <b>پشتیبانی:</b>
{CONTACT_INFO['phone']}
        """
        
        keyboard = [[InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(help_text, reply_markup=reply_markup, parse_mode='HTML')
    
    async def profile_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Profile command"""
        await self.show_profile(update.callback_query if hasattr(update, 'callback_query') else None)
    
    async def courses_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Courses command"""
        await self.show_courses(update.callback_query if hasattr(update, 'callback_query') else None)
    
    async def ai_chat_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """AI chat command"""
        context.user_data['ai_chat_mode'] = True
        await update.message.reply_text(
            "🤖 چت با استاد هوشمند فعال شد! سوال خود را بپرسید.\nبرای خروج: /cancel"
        )
    
    async def voice_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Voice command"""
        if VOICE_CONFIG["enable_voice_input"]:
            await update.message.reply_text(
                "🎤 دستورات صوتی فعال است! می‌توانید پیام صوتی ارسال کنید."
            )
        else:
            await update.message.reply_text(
                "🎤 دستورات صوتی در حال توسعه است."
            )
    
    def run(self):
        """Run the bot"""
        logger.info("🚀 Starting Super Advanced Bot...")
        self.application.run_polling()

def main():
    """Main function"""
    try:
        bot = SuperAdvancedBot()
        bot.run()
    except Exception as e:
        logger.error(f"❌ Error running bot: {e}")

if __name__ == "__main__":
    main() 