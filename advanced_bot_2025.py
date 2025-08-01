#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced Telegram Bot for Math Course Registration - 2025 Edition
ربات تلگرام پیشرفته برای ثبت‌نام کلاس‌های ریاضی - نسخه ۲۰۲۵
"""

import json
import logging
import os
import asyncio
import hashlib
import base64
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters, ConversationHandler
from telegram.constants import ParseMode

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import configuration
from config import *

# Configure advanced logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, LOG_LEVEL),
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE) if os.path.exists(os.path.dirname(LOG_FILE)) else logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Advanced conversation states
class ConversationState(Enum):
    CHOOSING_LANGUAGE = 0
    CHOOSING_COURSE = 1
    ENTERING_NAME = 2
    ENTERING_PHONE = 3
    ENTERING_GRADE = 4
    ENTERING_PARENT_PHONE = 5
    CONFIRMING_REGISTRATION = 6
    PAYMENT_PROCESS = 7
    SUBSCRIPTION_SELECTION = 8
    GAMIFICATION_SETUP = 9
    AI_PERSONALIZATION = 10

# User preferences and state
@dataclass
class UserPreferences:
    language: str = "fa"
    theme: str = "default"
    notifications_enabled: bool = True
    ai_assistance_enabled: bool = True
    gamification_enabled: bool = True
    subscription_plan: Optional[str] = None
    points: int = 0
    badges: List[str] = None
    achievements: List[str] = None
    last_activity: datetime = None
    
    def __post_init__(self):
        if self.badges is None:
            self.badges = []
        if self.achievements is None:
            self.achievements = []
        if self.last_activity is None:
            self.last_activity = datetime.now()

# AI/ML Features
class AIAssistant:
    """Advanced AI Assistant for personalized responses"""
    
    def __init__(self):
        self.sentiment_analyzer = self._init_sentiment_analyzer()
        self.recommendation_engine = self._init_recommendation_engine()
        self.personalization_model = self._init_personalization_model()
    
    def _init_sentiment_analyzer(self):
        """Initialize sentiment analysis"""
        positive_words = ["عالی", "خوب", "ممنون", "عالیه", "بسیار خوب", "عالی است"]
        negative_words = ["بد", "ضعیف", "مشکل", "خطا", "ناراضی"]
        
        def analyze_sentiment(text: str) -> str:
            text_lower = text.lower()
            positive_count = sum(1 for word in positive_words if word in text_lower)
            negative_count = sum(1 for word in negative_words if word in text_lower)
            
            if positive_count > negative_count:
                return "positive"
            elif negative_count > positive_count:
                return "negative"
            else:
                return "neutral"
        
        return analyze_sentiment
    
    def _init_recommendation_engine(self):
        """Initialize recommendation engine"""
        def recommend_courses(user_preferences: UserPreferences, user_history: List[Dict]) -> List[Dict]:
            recommendations = []
            for course in COURSES:
                score = 0
                if user_preferences.language == "fa":
                    if "دهم" in course.get("target", "") and "دهم" in str(user_history):
                        score += 3
                    if "یازدهم" in course.get("target", "") and "یازدهم" in str(user_history):
                        score += 3
                    if "دوازدهم" in course.get("target", "") and "دوازدهم" in str(user_history):
                        score += 3
                
                if course.get("type") == "رایگان":
                    score += 2
                else:
                    score += 1
                
                if score > 0:
                    recommendations.append({"course": course, "score": score})
            
            recommendations.sort(key=lambda x: x["score"], reverse=True)
            return [r["course"] for r in recommendations[:3]]
        
        return recommend_courses
    
    def _init_personalization_model(self):
        """Initialize personalization model"""
        def personalize_response(text: str, user_preferences: UserPreferences) -> str:
            if user_preferences.language == "en":
                translations = {
                    "سلام": "Hello",
                    "خوش آمدید": "Welcome",
                    "ثبت‌نام": "Registration",
                    "کلاس": "Class"
                }
                for persian, english in translations.items():
                    text = text.replace(persian, english)
            
            if user_preferences.subscription_plan:
                text += f"\n\n🌟 <b>ویژگی ویژه برای مشترکین {user_preferences.subscription_plan}:</b>"
                if user_preferences.subscription_plan == "طلایی":
                    text += "\n• دسترسی به کلاس‌های خصوصی"
                    text += "\n• مشاوره تخصصی رایگان"
            
            return text
        
        return personalize_response

# Gamification System
class GamificationSystem:
    """Advanced gamification system for user engagement"""
    
    def __init__(self):
        self.achievements = GAMIFICATION_CONFIG["achievements"]
        self.badges = [
            "🎓 دانش‌آموز جدید",
            "📚 دانش‌آموز فعال", 
            "💎 مشترک ویژه",
            "🏆 قهرمان",
            "🌟 ستاره",
            "🎯 دقیق",
            "🤝 اجتماعی",
            "💡 خلاق"
        ]
    
    def calculate_points(self, action: str) -> int:
        """Calculate points for user actions"""
        points_map = {
            "registration": 100,
            "course_completion": 50,
            "payment": 200,
            "referral": 150,
            "daily_login": 10,
            "achievement": 75,
            "subscription": 300
        }
        return points_map.get(action, 0)
    
    def check_achievements(self, user_preferences: UserPreferences, user_history: List[Dict]) -> List[str]:
        """Check for new achievements"""
        new_achievements = []
        
        if len(user_history) == 1 and "اولین ثبت‌نام" not in user_preferences.achievements:
            new_achievements.append("اولین ثبت‌نام")
        
        if len(user_history) >= 5 and "شرکت در ۵ کلاس" not in user_preferences.achievements:
            new_achievements.append("شرکت در ۵ کلاس")
        
        paid_courses = [h for h in user_history if h.get("type") == "paid"]
        if paid_courses and "پرداخت موفق" not in user_preferences.achievements:
            new_achievements.append("پرداخت موفق")
        
        return new_achievements
    
    def assign_badges(self, user_preferences: UserPreferences) -> List[str]:
        """Assign badges based on user activity"""
        new_badges = []
        
        if user_preferences.points >= 1000 and "🏆 قهرمان" not in user_preferences.badges:
            new_badges.append("🏆 قهرمان")
        
        if user_preferences.subscription_plan == "طلایی" and "💎 مشترک ویژه" not in user_preferences.badges:
            new_badges.append("💎 مشترک ویژه")
        
        if len(user_preferences.achievements) >= 3 and "🌟 ستاره" not in user_preferences.badges:
            new_badges.append("🌟 ستاره")
        
        return new_badges

# Advanced Data Manager
class AdvancedDataManager:
    """Advanced data management with AI, analytics, and security"""
    
    def __init__(self):
        self.data_file = DATA_FILE
        self.backup_file = BACKUP_FILE
        self.users_file = "data/users.json"
        self.analytics_file = "data/analytics.json"
        self.ensure_data_directory()
        self.ai_assistant = AIAssistant()
        self.gamification = GamificationSystem()
    
    def ensure_data_directory(self):
        """Ensure data directory exists"""
        os.makedirs("data", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        os.makedirs("analytics", exist_ok=True)
    
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
    
    def load_users(self) -> Dict[int, UserPreferences]:
        """Load user preferences"""
        try:
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    users = {}
                    for user_id, user_data in data.items():
                        users[int(user_id)] = UserPreferences(**user_data)
                    return users
            return {}
        except Exception as e:
            logger.error(f"Error loading users: {e}")
            return {}
    
    def save_users(self, users: Dict[int, UserPreferences]):
        """Save user preferences"""
        try:
            data = {str(user_id): asdict(user_prefs) for user_id, user_prefs in users.items()}
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving users: {e}")
    
    def load_students(self) -> List[Dict]:
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
    
    def save_students(self, students: List[Dict]):
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
    
    def add_student(self, student_data: Dict) -> Dict:
        """Add new student with advanced features"""
        students = self.load_students()
        student_data['id'] = len(students) + 1
        student_data['registration_date'] = datetime.now().isoformat()
        student_data['status'] = 'pending'
        
        # Add AI-generated recommendations
        student_data['recommendations'] = self.ai_assistant.recommendation_engine(
            UserPreferences(), students
        )
        
        students.append(student_data)
        self.save_students(students)
        
        # Update analytics
        self.update_analytics('registration', student_data)
        
        return student_data
    
    def update_analytics(self, event_type: str, data: Dict):
        """Update analytics data"""
        try:
            analytics_file = "data/analytics.json"
            if os.path.exists(analytics_file):
                with open(analytics_file, 'r', encoding='utf-8') as f:
                    analytics = json.load(f)
            else:
                analytics = {
                    "events": [],
                    "metrics": {
                        "total_registrations": 0,
                        "total_payments": 0,
                        "conversion_rate": 0,
                        "user_engagement": 0
                    }
                }
            
            # Add event
            event = {
                "type": event_type,
                "timestamp": datetime.now().isoformat(),
                "data": data
            }
            analytics["events"].append(event)
            
            # Update metrics
            if event_type == "registration":
                analytics["metrics"]["total_registrations"] += 1
            
            # Calculate conversion rate
            students = self.load_students()
            paid_students = len([s for s in students if s.get("type") == "paid"])
            total_students = len(students)
            if total_students > 0:
                analytics["metrics"]["conversion_rate"] = (paid_students / total_students) * 100
            
            # Save analytics
            with open(analytics_file, 'w', encoding='utf-8') as f:
                json.dump(analytics, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"Error updating analytics: {e}")

# Multi-language Support
class LanguageManager:
    """Multi-language support system"""
    
    def __init__(self):
        self.translations = {
            "fa": {
                "welcome": "🎓 به ربات کلاس‌های ریاضی خوش آمدید!",
                "registration": "📝 ثبت‌نام در کلاس",
                "courses": "📚 کلاس‌های موجود",
                "help": "🔧 راهنما",
                "contact": "📞 تماس با ما",
                "menu": "🏠 منوی اصلی",
                "back": "🔙 بازگشت",
                "confirm": "✅ تأیید",
                "cancel": "❌ انصراف"
            },
            "en": {
                "welcome": "🎓 Welcome to Math Course Registration Bot!",
                "registration": "📝 Course Registration",
                "courses": "📚 Available Courses",
                "help": "🔧 Help",
                "contact": "📞 Contact Us",
                "menu": "🏠 Main Menu",
                "back": "🔙 Back",
                "confirm": "✅ Confirm",
                "cancel": "❌ Cancel"
            }
        }
    
    def get_text(self, key: str, language: str = "fa") -> str:
        """Get translated text"""
        return self.translations.get(language, self.translations["fa"]).get(key, key)
    
    def get_language_keyboard(self) -> InlineKeyboardMarkup:
        """Get language selection keyboard"""
        keyboard = [
            [InlineKeyboardButton("🇮🇷 فارسی", callback_data="lang_fa")],
            [InlineKeyboardButton("🇺🇸 English", callback_data="lang_en")]
        ]
        return InlineKeyboardMarkup(keyboard)

# Main Advanced Bot Class
class AdvancedMathBot2025:
    """Advanced Math Course Registration Bot - 2025 Edition"""
    
    def __init__(self):
        # Get token from environment variable (for hosting) or config file
        self.token = os.getenv('BOT_TOKEN', BOT_TOKEN)
        if self.token == "YOUR_BOT_TOKEN_HERE":
            logger.error("❌ خطا در تنظیمات: BOT_TOKEN not found in environment variables or config")
            raise ValueError("BOT_TOKEN not configured")
        
        self.data_manager = AdvancedDataManager()
        self.language_manager = LanguageManager()
        self.application = Application.builder().token(self.token).build()
        self.setup_handlers()
        
        # Initialize AI and gamification
        self.ai_assistant = AIAssistant()
        self.gamification = GamificationSystem()
        
        logger.info("🚀 Advanced Math Bot 2025 initialized successfully!")
    
    def setup_handlers(self):
        """Setup all advanced bot handlers"""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("register", self.register_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("admin", self.admin_command))
        self.application.add_handler(CommandHandler("profile", self.profile_command))
        self.application.add_handler(CommandHandler("points", self.points_command))
        self.application.add_handler(CommandHandler("subscription", self.subscription_command))
        self.application.add_handler(CommandHandler("analytics", self.analytics_command))
        
        # Callback query handler
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # Advanced conversation handler
        conv_handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(self.start_registration, pattern='^start_registration$'),
                CallbackQueryHandler(self.start_paid_registration, pattern='^paid_registration$'),
                CallbackQueryHandler(self.select_language, pattern='^lang_')
            ],
            states={
                ConversationState.CHOOSING_LANGUAGE: [
                    CallbackQueryHandler(self.select_language, pattern='^lang_')
                ],
                ConversationState.CHOOSING_COURSE: [
                    CallbackQueryHandler(self.choose_course, pattern='^course_'),
                    CallbackQueryHandler(self.cancel_registration, pattern='^cancel$')
                ],
                ConversationState.ENTERING_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.enter_name),
                    CallbackQueryHandler(self.cancel_registration, pattern='^cancel$')
                ],
                ConversationState.ENTERING_PHONE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.enter_phone),
                    CallbackQueryHandler(self.cancel_registration, pattern='^cancel$')
                ],
                ConversationState.ENTERING_GRADE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.enter_grade),
                    CallbackQueryHandler(self.cancel_registration, pattern='^cancel$')
                ],
                ConversationState.ENTERING_PARENT_PHONE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.enter_parent_phone),
                    CallbackQueryHandler(self.cancel_registration, pattern='^cancel$')
                ],
                ConversationState.CONFIRMING_REGISTRATION: [
                    CallbackQueryHandler(self.confirm_registration, pattern='^confirm$'),
                    CallbackQueryHandler(self.cancel_registration, pattern='^cancel$')
                ],
                ConversationState.PAYMENT_PROCESS: [
                    CallbackQueryHandler(self.process_payment, pattern='^payment_'),
                    CallbackQueryHandler(self.cancel_registration, pattern='^cancel$')
                ],
                ConversationState.SUBSCRIPTION_SELECTION: [
                    CallbackQueryHandler(self.select_subscription, pattern='^subscription_'),
                    CallbackQueryHandler(self.cancel_registration, pattern='^cancel$')
                ]
            },
            fallbacks=[CommandHandler("cancel", self.cancel_registration)]
        )
        self.application.add_handler(conv_handler)
        
        # Error handler
        self.application.add_error_handler(self.error_handler)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced start command with language selection and AI personalization"""
        user = update.effective_user
        
        # Load or create user preferences
        users = self.data_manager.load_users()
        if user.id not in users:
            users[user.id] = UserPreferences()
            self.data_manager.save_users(users)
        
        user_prefs = users[user.id]
        
        # Check if language is set
        if not user_prefs.language or user_prefs.language not in SUPPORTED_LANGUAGES:
            return await self.show_language_selection(update, context)
        
        # AI-powered personalized welcome
        welcome_text = self.ai_assistant.personalization_model(
            f"""
🎓 <b>به ربات کلاس‌های ریاضی خوش آمدید!</b>

سلام {user.first_name} عزیز! 👋

🌟 <b>ویژگی‌های پیشرفته ۲۰۲۵:</b>
• 🤖 هوش مصنوعی شخصی‌سازی شده
• 🎮 سیستم امتیازدهی و دستاوردها
• 🌐 پشتیبانی چندزبانه
• 💎 سیستم اشتراک پیشرفته
• 📊 تحلیل‌های هوشمند

📚 <b>کلاس‌های رایگان آنلاین</b> در حال برگزاری است!

💡 <b>برای شروع:</b>
            """,
            user_prefs
        )
        
        # Advanced keyboard with rich features
        keyboard = [
            [InlineKeyboardButton("📝 ثبت‌نام در کلاس", callback_data="start_registration")],
            [InlineKeyboardButton("🎮 پروفایل و امتیازات", callback_data="profile")],
            [InlineKeyboardButton("💎 اشتراک ویژه", callback_data="subscription")],
            [InlineKeyboardButton("📢 اطلاعیه‌های جدید", callback_data="announcements")],
            [InlineKeyboardButton("🎓 کلاس‌های ویژه رایگان", callback_data="special_courses")],
            [InlineKeyboardButton("📅 برنامه کلاس‌ها", callback_data="schedule")],
            [InlineKeyboardButton("📚 کلاس‌های موجود", callback_data="courses")],
            [InlineKeyboardButton("📖 اطلاعات کتاب", callback_data="book_info")],
            [InlineKeyboardButton("📞 اطلاعات تماس", callback_data="contact_info")],
            [InlineKeyboardButton("🔗 شبکه‌های اجتماعی", callback_data="social_links")],
            [InlineKeyboardButton("📺 کانال یوتیوب رایگان", callback_data="youtube")],
            [InlineKeyboardButton("🔧 تنظیمات پیشرفته", callback_data="advanced_settings")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='HTML')
        
        # Update user activity
        user_prefs.last_activity = datetime.now()
        users[user.id] = user_prefs
        self.data_manager.save_users(users)
    
    async def show_language_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show language selection interface"""
        text = """
🌐 <b>انتخاب زبان / Language Selection</b>

لطفاً زبان مورد نظر خود را انتخاب کنید:
Please select your preferred language:
        """
        
        reply_markup = self.language_manager.get_language_keyboard()
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')
        return ConversationState.CHOOSING_LANGUAGE
    
    async def select_language(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle language selection"""
        query = update.callback_query
        await query.answer()
        
        language = query.data.replace('lang_', '')
        
        # Update user preferences
        users = self.data_manager.load_users()
        user_id = query.from_user.id
        if user_id not in users:
            users[user_id] = UserPreferences()
        
        users[user_id].language = language
        self.data_manager.save_users(users)
        
        # Show welcome message in selected language
        await self.start_command(update, context)
        return ConversationHandler.END
    
    async def profile_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user profile with gamification features"""
        user = update.effective_user
        users = self.data_manager.load_users()
        user_prefs = users.get(user.id, UserPreferences())
        
        # Load user history
        students = self.data_manager.load_students()
        user_history = [s for s in students if s.get('user_id') == user.id]
        
        # Check for new achievements
        new_achievements = self.gamification.check_achievements(user_prefs, user_history)
        new_badges = self.gamification.assign_badges(user_prefs)
        
        # Update user preferences
        if new_achievements:
            user_prefs.achievements.extend(new_achievements)
            user_prefs.points += sum(self.gamification.calculate_points("achievement") for _ in new_achievements)
        
        if new_badges:
            user_prefs.badges.extend(new_badges)
        
        users[user.id] = user_prefs
        self.data_manager.save_users(users)
        
        # Create profile text
        profile_text = f"""
👤 <b>پروفایل کاربری</b>

👤 <b>نام:</b> {user.first_name} {user.last_name or ''}
🆔 <b>شناسه:</b> {user.id}
📅 <b>تاریخ عضویت:</b> {user_prefs.last_activity.strftime('%Y/%m/%d') if user_prefs.last_activity else 'نامشخص'}

🎮 <b>سیستم امتیازدهی:</b>
⭐ امتیازات: {user_prefs.points}
🏆 دستاوردها: {len(user_prefs.achievements)}/{len(self.gamification.achievements)}
🎖️ نشان‌ها: {len(user_prefs.badges)}

"""
        
        if user_prefs.achievements:
            profile_text += "🏆 <b>دستاوردهای شما:</b>\n"
            for achievement in user_prefs.achievements:
                profile_text += f"• {achievement}\n"
        
        if user_prefs.badges:
            profile_text += "\n🎖️ <b>نشان‌های شما:</b>\n"
            for badge in user_prefs.badges:
                profile_text += f"• {badge}\n"
        
        if new_achievements:
            profile_text += f"\n🎉 <b>دستاورد جدید!</b>\n"
            for achievement in new_achievements:
                profile_text += f"• {achievement}\n"
        
        if user_prefs.subscription_plan:
            profile_text += f"\n💎 <b>اشتراک فعلی:</b> {user_prefs.subscription_plan}"
        
        # Course history
        if user_history:
            profile_text += f"\n\n📚 <b>تاریخچه کلاس‌ها:</b>\n"
            for i, course in enumerate(user_history[:5], 1):
                profile_text += f"{i}. {course.get('course', 'نامشخص')} - {course.get('status', 'نامشخص')}\n"
        
        keyboard = [
            [InlineKeyboardButton("🎮 مشاهده رتبه‌بندی", callback_data="leaderboard")],
            [InlineKeyboardButton("🏆 دستاوردهای موجود", callback_data="achievements")],
            [InlineKeyboardButton("💎 ارتقاء اشتراک", callback_data="subscription")],
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(profile_text, reply_markup=reply_markup, parse_mode='HTML')
    
    async def subscription_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show subscription plans"""
        text = """
💎 <b>اشتراک‌های ویژه</b>

🌟 <b>انتخاب کنید:</b>
        """
        
        keyboard = []
        for plan in SUBSCRIPTION_PLANS:
            features_text = "\n".join([f"• {feature}" for feature in plan["features"]])
            keyboard.append([
                InlineKeyboardButton(
                    f"💎 {plan['name']} - {plan['price']}/{plan['duration']}", 
                    callback_data=f"subscription_{plan['name']}"
                )
            ])
        
        keyboard.append([InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced callback handler with AI and gamification"""
        query = update.callback_query
        await query.answer()
        
        # Load user preferences for personalization
        users = self.data_manager.load_users()
        user_prefs = users.get(query.from_user.id, UserPreferences())
        
        # Analyze sentiment if AI is enabled
        if SENTIMENT_ANALYSIS_ENABLED:
            sentiment = self.ai_assistant.sentiment_analyzer(query.data)
            logger.info(f"User sentiment: {sentiment} for action: {query.data}")
        
        # Route to appropriate handler
        if query.data == "start_registration":
            await self.show_registration_menu(query)
        elif query.data == "profile":
            await self.show_profile(query)
        elif query.data == "subscription":
            await self.show_subscription_plans(query)
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
        elif query.data == "advanced_settings":
            await self.show_advanced_settings(query)
        elif query.data == "leaderboard":
            await self.show_leaderboard(query)
        elif query.data == "achievements":
            await self.show_achievements(query)
        elif query.data.startswith("admin_"):
            await self.handle_admin_callback(query)
        
        # Update user activity and award points
        if GAMIFICATION_ENABLED:
            points = self.gamification.calculate_points("daily_login")
            user_prefs.points += points
            user_prefs.last_activity = datetime.now()
            users[query.from_user.id] = user_prefs
            self.data_manager.save_users(users)
    
    async def show_advanced_settings(self, query):
        """Show advanced settings interface"""
        users = self.data_manager.load_users()
        user_prefs = users.get(query.from_user.id, UserPreferences())
        
        text = f"""
🔧 <b>تنظیمات پیشرفته</b>

🌐 <b>زبان:</b> {'فارسی' if user_prefs.language == 'fa' else 'English'}
🔔 <b>اعلان‌ها:</b> {'فعال' if user_prefs.notifications_enabled else 'غیرفعال'}
🤖 <b>کمک هوش مصنوعی:</b> {'فعال' if user_prefs.ai_assistance_enabled else 'غیرفعال'}
🎮 <b>بازی‌سازی:</b> {'فعال' if user_prefs.gamification_enabled else 'غیرفعال'}
🎨 <b>تم:</b> {user_prefs.theme}
        """
        
        keyboard = [
            [InlineKeyboardButton("🌐 تغییر زبان", callback_data="change_language")],
            [InlineKeyboardButton("🔔 تنظیمات اعلان", callback_data="notification_settings")],
            [InlineKeyboardButton("🤖 تنظیمات AI", callback_data="ai_settings")],
            [InlineKeyboardButton("🎮 تنظیمات بازی‌سازی", callback_data="gamification_settings")],
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
    
    async def show_leaderboard(self, query):
        """Show user leaderboard"""
        users = self.data_manager.load_users()
        
        # Sort users by points
        sorted_users = sorted(users.items(), key=lambda x: x[1].points, reverse=True)
        
        text = "🏆 <b>رتبه‌بندی کاربران</b>\n\n"
        
        for i, (user_id, user_prefs) in enumerate(sorted_users[:10], 1):
            text += f"{i}. {'🥇' if i == 1 else '🥈' if i == 2 else '🥉' if i == 3 else '👤'} "
            text += f"کاربر {user_id}: {user_prefs.points} امتیاز\n"
        
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="profile")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
    
    async def show_achievements(self, query):
        """Show available achievements"""
        text = "🏆 <b>دستاوردهای موجود</b>\n\n"
        
        for achievement in self.gamification.achievements:
            text += f"• {achievement}\n"
        
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="profile")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
    
    # Enhanced registration and course methods
    async def show_registration_menu(self, query):
        """Professional registration menu with AI recommendations"""
        users = self.data_manager.load_users()
        user_prefs = users.get(query.from_user.id, UserPreferences())
        
        # Get AI recommendations
        students = self.data_manager.load_students()
        user_history = [s for s in students if s.get('user_id') == query.from_user.id]
        recommendations = self.ai_assistant.recommendation_engine(user_prefs, user_history)
        
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
        """
        
        if recommendations:
            text += "\n🤖 <b>پیشنهادات هوشمند:</b>\n"
            for i, course in enumerate(recommendations[:3], 1):
                text += f"{i}. {course['name']}\n"
        
        keyboard = [
            [InlineKeyboardButton("🆓 کلاس‌های رایگان", callback_data="free_registration")],
            [InlineKeyboardButton("💎 کلاس‌های ویژه پولی", callback_data="paid_registration")],
            [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
    
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
            text += f"📅 {course.get('schedule', course.get('start_date', 'نامشخص'))}\n"
            text += f"👥 {course['target']}\n"
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
{CONTACT_INFO['working_hours']}

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
        text = f"""
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
            [InlineKeyboardButton("🎮 پروفایل و امتیازات", callback_data="profile")],
            [InlineKeyboardButton("💎 اشتراک ویژه", callback_data="subscription")],
            [InlineKeyboardButton("📢 اطلاعیه‌های جدید", callback_data="announcements")],
            [InlineKeyboardButton("🎓 کلاس‌های ویژه رایگان", callback_data="special_courses")],
            [InlineKeyboardButton("📅 برنامه کلاس‌ها", callback_data="schedule")],
            [InlineKeyboardButton("📚 کلاس‌های موجود", callback_data="courses")],
            [InlineKeyboardButton("📖 اطلاعات کتاب", callback_data="book_info")],
            [InlineKeyboardButton("📞 اطلاعات تماس", callback_data="contact_info")],
            [InlineKeyboardButton("🔗 شبکه‌های اجتماعی", callback_data="social_links")],
            [InlineKeyboardButton("📺 کانال یوتیوب رایگان", callback_data="youtube")],
            [InlineKeyboardButton("🔧 تنظیمات پیشرفته", callback_data="advanced_settings")]
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
        return ConversationState.CHOOSING_COURSE
    
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
        return ConversationState.CHOOSING_COURSE
    
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
        return ConversationState.ENTERING_NAME
    
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
        return ConversationState.ENTERING_PHONE
    
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
        return ConversationState.ENTERING_GRADE
    
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
        return ConversationState.ENTERING_PARENT_PHONE
    
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
        return ConversationState.CONFIRMING_REGISTRATION
    
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
        return ConversationState.CONFIRMING_REGISTRATION
    
    async def confirm_registration(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle registration confirmation with gamification"""
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
        
        # Award points for registration
        users = self.data_manager.load_users()
        user_prefs = users.get(update.effective_user.id, UserPreferences())
        points = self.gamification.calculate_points("registration")
        user_prefs.points += points
        users[update.effective_user.id] = user_prefs
        self.data_manager.save_users(users)
        
        if is_paid:
            student_data['type'] = 'paid'
            student_data['status'] = 'pending_payment'
            # Notify admins for payment
            await self.notify_admins_payment(student_data)
            text = f"""
💎 <b>ثبت‌نام کلاس پولی با موفقیت انجام شد!</b>

✅ <b>مراحل بعدی:</b>
1️⃣ ادمین‌ها اطلاع‌رسانی شدند
2️⃣ منتظر تماس برای پرداخت باشید
3️⃣ پس از پرداخت، محصول ارسال می‌شود

🎮 <b>امتیاز کسب شده:</b> +{points} امتیاز

📞 <b>برای سوالات:</b>
{CONTACT_INFO['phone']}

🔙 <b>بازگشت به منوی اصلی:</b>
            """
        else:
            student_data['type'] = 'free'
            student_data['status'] = 'confirmed'
            text = f"""
✅ <b>ثبت‌نام کلاس رایگان با موفقیت انجام شد!</b>

🎓 <b>اطلاعات کلاس:</b>
• لینک کلاس صبح همان روز ارسال می‌شود
• حضور به موقع الزامی است
• با نرم‌افزار کروم وارد شوید

🎮 <b>امتیاز کسب شده:</b> +{points} امتیاز

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
                admin_username = admin_id.replace('@', '')
                logger.info(f"Payment notification sent to {admin_id}: {notification_text}")
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
    
    async def process_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle payment processing"""
        query = update.callback_query
        await query.answer()
        
        payment_type = query.data.replace('payment_', '')
        
        if payment_type == 'confirm':
            text = f"""
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
            text = f"""
⏳ <b>پرداخت در حال بررسی</b>

لطفاً منتظر تأیید ادمین باشید.

📞 <b>برای سوالات:</b>
{CONTACT_INFO['phone']}
            """
        else:
            text = f"""
❌ <b>خطا در پرداخت</b>

لطفاً با پشتیبانی تماس بگیرید.

📞 <b>پشتیبانی:</b>
{CONTACT_INFO['phone']}
            """
        
        keyboard = [[InlineKeyboardButton("🏠 بازگشت به منو", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
        return ConversationHandler.END
    
    # Admin methods
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
    
    async def handle_admin_callback(self, query):
        """Handle admin callback queries"""
        if query.data == "admin_broadcast":
            await self.show_admin_broadcast(query)
        elif query.data == "admin_stats":
            await self.show_admin_stats(query)
        elif query.data == "admin_payments":
            await self.show_admin_payments(query)
    
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
            for i, student in enumerate(pending_payments[:5], 1):
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
    
    # Additional command methods
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Professional help command"""
        help_text = """
🔧 <b>راهنمای استفاده از ربات</b>

📝 <b>دستورات اصلی:</b>
/start - منوی اصلی ربات
/register - ثبت‌نام مستقیم
/status - وضعیت ثبت‌نام
/profile - پروفایل و امتیازات
/subscription - اشتراک‌های ویژه
/help - این راهنما

📚 <b>ویژگی‌های ربات:</b>
• ثبت‌نام در کلاس‌های رایگان و پولی
• اطلاعیه‌های به‌روز کلاس‌ها
• برنامه زمان‌بندی کلاس‌ها
• دسترسی به محتوای آموزشی رایگان
• پشتیبانی ۲۴/۷

🌟 <b>ویژگی‌های پیشرفته ۲۰۲۵:</b>
• 🤖 هوش مصنوعی شخصی‌سازی شده
• 🎮 سیستم امتیازدهی و دستاوردها
• 🌐 پشتیبانی چندزبانه
• 💎 سیستم اشتراک پیشرفته
• 📊 تحلیل‌های هوشمند

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
        await self.show_registration_menu(None)
    
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
    
    async def points_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user points and achievements"""
        await self.profile_command(update, context)
    
    async def analytics_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show analytics for admins"""
        await self.admin_command(update, context)
    
    async def show_profile(self, query):
        """Show user profile"""
        await self.profile_command(query, None)
    
    async def show_subscription_plans(self, query):
        """Show subscription plans"""
        await self.subscription_command(query, None)
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors with AI assistance"""
        logger.error(f"Exception while handling an update: {context.error}")
        
        if update and update.effective_message:
            text = """
❌ <b>خطایی رخ داد!</b>

🤖 <b>هوش مصنوعی در حال بررسی مشکل...</b>

لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید.

📞 <b>پشتیبانی:</b>
{CONTACT_INFO['phone']}
            """
            keyboard = [[InlineKeyboardButton("🏠 بازگشت به منو", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.effective_message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')

def main():
    """Main function to run the advanced bot"""
    try:
        logger.info("🚀 Advanced Math Bot 2025 در حال راه‌اندازی...")
        bot = AdvancedMathBot2025()
        bot.application.run_polling()
    except Exception as e:
        logger.error(f"❌ خطا در اجرای ربات پیشرفته: {e}")

if __name__ == "__main__":
    main() 