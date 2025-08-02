#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ربات تلگرام استاد حاتمی - نسخه بهینه‌سازی شده ۲۰۰ برابری
Telegram Bot for Ostad Hatami - 200X Optimized Version
"""

import json
import logging
import os
import asyncio
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
from pathlib import Path

# Enhanced imports
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Core Telegram imports
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters, ConversationHandler

# Performance & Caching
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    from cachetools import TTLCache
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False

# AI & Analytics
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import structlog
    STRUCTLOG_AVAILABLE = True
except ImportError:
    STRUCTLOG_AVAILABLE = False

# Import configuration
from config_optimized import *

# ============================================================================
# ENHANCED LOGGING SETUP
# ============================================================================
if STRUCTLOG_AVAILABLE:
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    logger = structlog.get_logger()
else:
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=getattr(logging, SYSTEM["log_level"]),
        handlers=[
            logging.FileHandler('bot_optimized.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)

# ============================================================================
# CONVERSATION STATES
# ============================================================================
(
    ENTERING_FIRST_NAME, ENTERING_LAST_NAME, ENTERING_PHONE, 
    ENTERING_CITY, ENTERING_GRADE, ENTERING_FIELD, ENTERING_EMAIL,
    ENTERING_BIRTH_DATE, ENTERING_PARENT_PHONE, ENTERING_GOALS
) = range(10)

# ============================================================================
# ENHANCED DATA MODELS
# ============================================================================
@dataclass
class UserProfile:
    """Enhanced user profile with advanced features"""
    user_id: int
    first_name: str
    last_name: str
    phone: str
    city: str
    grade: str
    field: str
    email: Optional[str] = None
    birth_date: Optional[str] = None
    parent_phone: Optional[str] = None
    goals: Optional[str] = None
    points: int = 0
    level: str = "newcomer"
    badges: List[str] = None
    courses_enrolled: List[str] = None
    registration_date: str = None
    last_active: str = None
    preferences: Dict[str, Any] = None
    achievements: List[str] = None
    study_time: int = 0  # in minutes
    quiz_scores: Dict[str, float] = None
    feedback_given: int = 0
    referrals: int = 0
    
    def __post_init__(self):
        if self.badges is None:
            self.badges = []
        if self.courses_enrolled is None:
            self.courses_enrolled = []
        if self.preferences is None:
            self.preferences = {}
        if self.achievements is None:
            self.achievements = []
        if self.quiz_scores is None:
            self.quiz_scores = {}
        if self.registration_date is None:
            self.registration_date = datetime.now().isoformat()
        if self.last_active is None:
            self.last_active = datetime.now().isoformat()

@dataclass
class CourseProgress:
    """Course progress tracking"""
    user_id: int
    course_id: str
    progress_percentage: float = 0.0
    lessons_completed: int = 0
    total_lessons: int = 0
    quiz_scores: List[float] = None
    time_spent: int = 0  # in minutes
    last_accessed: str = None
    enrollment_date: str = None
    
    def __post_init__(self):
        if self.quiz_scores is None:
            self.quiz_scores = []
        if self.last_accessed is None:
            self.last_accessed = datetime.now().isoformat()
        if self.enrollment_date is None:
            self.enrollment_date = datetime.now().isoformat()

# ============================================================================
# ENHANCED CACHE MANAGER
# ============================================================================
class EnhancedCacheManager:
    """Advanced caching system with Redis and memory cache"""
    
    def __init__(self):
        self.redis_client = None
        self.memory_cache = None
        self._init_cache()
    
    def _init_cache(self):
        """Initialize cache systems"""
        # Memory cache
        if CACHE_AVAILABLE:
            self.memory_cache = TTLCache(
                maxsize=MEMORY_CACHE_SIZE,
                ttl=CACHE_TTL
            )
        
        # Redis cache
        if REDIS_AVAILABLE and REDIS_URL:
            try:
                self.redis_client = redis.from_url(REDIS_URL)
                logger.info("Redis cache initialized successfully")
            except Exception as e:
                logger.warning(f"Redis cache initialization failed: {e}")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        # Try memory cache first
        if self.memory_cache and key in self.memory_cache:
            logger.debug(f"Cache hit (memory): {key}")
            return self.memory_cache[key]
        
        # Try Redis cache
        if self.redis_client:
            try:
                value = await self.redis_client.get(key)
                if value:
                    data = json.loads(value)
                    # Store in memory cache for faster access
                    if self.memory_cache:
                        self.memory_cache[key] = data
                    logger.debug(f"Cache hit (Redis): {key}")
                    return data
            except Exception as e:
                logger.error(f"Redis get error: {e}")
        
        logger.debug(f"Cache miss: {key}")
        return None
    
    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value in cache"""
        ttl = ttl or CACHE_TTL
        
        # Set in memory cache
        if self.memory_cache:
            self.memory_cache[key] = value
        
        # Set in Redis cache
        if self.redis_client:
            try:
                await self.redis_client.setex(
                    key, 
                    ttl, 
                    json.dumps(value, ensure_ascii=False)
                )
                logger.debug(f"Cache set: {key}")
                return True
            except Exception as e:
                logger.error(f"Redis set error: {e}")
                return False
        
        return True
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        # Delete from memory cache
        if self.memory_cache and key in self.memory_cache:
            del self.memory_cache[key]
        
        # Delete from Redis cache
        if self.redis_client:
            try:
                await self.redis_client.delete(key)
                logger.debug(f"Cache delete: {key}")
                return True
            except Exception as e:
                logger.error(f"Redis delete error: {e}")
                return False
        
        return True
    
    async def clear(self) -> bool:
        """Clear all cache"""
        # Clear memory cache
        if self.memory_cache:
            self.memory_cache.clear()
        
        # Clear Redis cache
        if self.redis_client:
            try:
                await self.redis_client.flushdb()
                logger.info("Cache cleared successfully")
                return True
            except Exception as e:
                logger.error(f"Redis clear error: {e}")
                return False
        
        return True

# ============================================================================
# ENHANCED DATA MANAGER
# ============================================================================
class EnhancedDataManager:
    """Advanced data management with encryption and backup"""
    
    def __init__(self, cache_manager: EnhancedCacheManager):
        self.cache_manager = cache_manager
        self.data_dir = Path("data/users")
        self.backup_dir = Path("data/backups")
        self.ensure_directories()
    
    def ensure_directories(self):
        """Create necessary directories"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def _encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        if not ENCRYPTION_ENABLED or not ENCRYPTION_KEY:
            return data
        
        try:
            from cryptography.fernet import Fernet
            key = hashlib.sha256(ENCRYPTION_KEY.encode()).digest()
            f = Fernet(key)
            return f.encrypt(data.encode()).decode()
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            return data
    
    def _decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        if not ENCRYPTION_ENABLED or not ENCRYPTION_KEY:
            return encrypted_data
        
        try:
            from cryptography.fernet import Fernet
            key = hashlib.sha256(ENCRYPTION_KEY.encode()).digest()
            f = Fernet(key)
            return f.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            return encrypted_data
    
    def get_user_file_path(self, user_id: int) -> Path:
        """Get user data file path"""
        return self.data_dir / f"user_{user_id}.json"
    
    async def save_user_data(self, user_profile: UserProfile) -> bool:
        """Save user data with encryption and caching"""
        try:
            # Update last active
            user_profile.last_active = datetime.now().isoformat()
            
            # Convert to dict
            user_data = asdict(user_profile)
            
            # Encrypt sensitive data
            if ENCRYPTION_ENABLED:
                user_data['phone'] = self._encrypt_data(user_data['phone'])
                if user_data.get('parent_phone'):
                    user_data['parent_phone'] = self._encrypt_data(user_data['parent_phone'])
                if user_data.get('email'):
                    user_data['email'] = self._encrypt_data(user_data['email'])
            
            # Save to file
            file_path = self.get_user_file_path(user_profile.user_id)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(user_data, f, ensure_ascii=False, indent=2)
            
            # Cache user data
            cache_key = f"user:{user_profile.user_id}"
            await self.cache_manager.set(cache_key, user_data)
            
            logger.info(f"User data saved for user_id: {user_profile.user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving user data for user_id {user_profile.user_id}: {e}")
            return False
    
    async def load_user_data(self, user_id: int) -> Optional[UserProfile]:
        """Load user data with caching and decryption"""
        try:
            # Try cache first
            cache_key = f"user:{user_id}"
            cached_data = await self.cache_manager.get(cache_key)
            
            if cached_data:
                # Decrypt sensitive data
                if ENCRYPTION_ENABLED:
                    cached_data['phone'] = self._decrypt_data(cached_data['phone'])
                    if cached_data.get('parent_phone'):
                        cached_data['parent_phone'] = self._decrypt_data(cached_data['parent_phone'])
                    if cached_data.get('email'):
                        cached_data['email'] = self._decrypt_data(cached_data['email'])
                
                return UserProfile(**cached_data)
            
            # Load from file
            file_path = self.get_user_file_path(user_id)
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    user_data = json.load(f)
                
                # Decrypt sensitive data
                if ENCRYPTION_ENABLED:
                    user_data['phone'] = self._decrypt_data(user_data['phone'])
                    if user_data.get('parent_phone'):
                        user_data['parent_phone'] = self._decrypt_data(user_data['parent_phone'])
                    if user_data.get('email'):
                        user_data['email'] = self._decrypt_data(user_data['email'])
                
                # Cache the data
                await self.cache_manager.set(cache_key, user_data)
                
                return UserProfile(**user_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error loading user data for user_id {user_id}: {e}")
            return None
    
    async def user_exists(self, user_id: int) -> bool:
        """Check if user exists"""
        # Try cache first
        cache_key = f"user:{user_id}"
        cached_data = await self.cache_manager.get(cache_key)
        if cached_data:
            return True
        
        # Check file
        file_path = self.get_user_file_path(user_id)
        return file_path.exists()
    
    async def delete_user_data(self, user_id: int) -> bool:
        """Delete user data"""
        try:
            # Remove from cache
            cache_key = f"user:{user_id}"
            await self.cache_manager.delete(cache_key)
            
            # Remove file
            file_path = self.get_user_file_path(user_id)
            if file_path.exists():
                file_path.unlink()
            
            logger.info(f"User data deleted for user_id: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting user data for user_id {user_id}: {e}")
            return False
    
    async def create_backup(self) -> bool:
        """Create backup of all user data"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"backup_{timestamp}.json"
            
            all_users = []
            for file_path in self.data_dir.glob("user_*.json"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        user_data = json.load(f)
                        all_users.append(user_data)
                except Exception as e:
                    logger.error(f"Error reading {file_path}: {e}")
            
            backup_data = {
                "timestamp": timestamp,
                "total_users": len(all_users),
                "users": all_users
            }
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Backup created: {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            return False

# ============================================================================
# ENHANCED UI MANAGER
# ============================================================================
class EnhancedUIManager:
    """Advanced UI/UX manager with themes and layouts"""
    
    def __init__(self):
        self.theme = UI_THEME
        self.layouts = BUTTON_LAYOUTS
        self.progress_indicators = PROGRESS_INDICATORS
    
    def create_enhanced_keyboard(self, buttons: List[List[str]], layout: str = "normal") -> InlineKeyboardMarkup:
        """Create enhanced keyboard with custom layout"""
        keyboard = []
        buttons_per_row = self.layouts.get(layout, 1)
        
        for i in range(0, len(buttons), buttons_per_row):
            row = []
            for j in range(buttons_per_row):
                if i + j < len(buttons):
                    button_text, callback_data = buttons[i + j]
                    row.append(InlineKeyboardButton(button_text, callback_data=callback_data))
            keyboard.append(row)
        
        return InlineKeyboardMarkup(keyboard)
    
    def format_course_card(self, course: Dict[str, Any], user_level: str = "newcomer") -> str:
        """Format course information as a beautiful card"""
        price_color = self.theme["free_color"] if course["price"] == 0 else self.theme["premium_color"]
        level_color = self.theme["info_color"]
        
        card = f"""
{price_color} **{course['name']}**

📊 **سطح:** {level_color} {course['level']}
💰 **قیمت:** {price_color} {format_price(course['price'], course['currency'])}
⏱️ **مدت:** {level_color} {course['duration']}
👨‍🏫 **مدرس:** {level_color} {course['instructor']}
⭐ **امتیاز:** {self.theme['success_color']} {course['rating']}/5.0
👥 **دانشجویان:** {level_color} {course['students']:,} نفر

🎯 **مخاطبین:**
"""
        for target in course['target']:
            card += f"   • {target}\n"
        
        card += "\n✨ **ویژگی‌ها:**\n"
        for feature in course['features']:
            card += f"   • {feature}\n"
        
        return card.strip()
    
    def format_user_profile(self, user_profile: UserProfile) -> str:
        """Format user profile beautifully"""
        badge_info = get_badge_info(user_profile.level)
        badge_icon = badge_info.get('icon', '🆕')
        
        profile = f"""
{self.theme['primary_color']} **پروفایل کاربری**

👤 **نام:** {user_profile.first_name} {user_profile.last_name}
📱 **شماره:** {user_profile.phone}
🏙️ **شهر:** {user_profile.city}
🎓 **پایه:** {GRADES.get(user_profile.grade, user_profile.grade)}
📚 **رشته:** {user_profile.field}

{badge_icon} **سطح:** {badge_info.get('name', 'تازه‌وارد')}
⭐ **امتیاز:** {user_profile.points:,}
📅 **تاریخ عضویت:** {user_profile.registration_date[:10]}
🕐 **آخرین فعالیت:** {user_profile.last_active[:10]}

📊 **آمار:**
   • دوره‌های ثبت‌نام شده: {len(user_profile.courses_enrolled)}
   • زمان مطالعه: {format_duration(user_profile.study_time * 60)}
   • بازخورد داده شده: {user_profile.feedback_given}
   • معرفی شده: {user_profile.referrals}
"""
        
        if user_profile.achievements:
            profile += "\n🏆 **دستاوردها:**\n"
            for achievement in user_profile.achievements[:5]:  # Show top 5
                profile += f"   • {achievement}\n"
        
        return profile.strip()
    
    def show_progress(self, current: int, total: int, style: str = "dots") -> str:
        """Show progress indicator"""
        if not self.progress_indicators["enabled"]:
            return ""
        
        percentage = (current / total) * 100 if total > 0 else 0
        
        if style == "dots":
            filled = int(percentage / 10)
            empty = 10 - filled
            return f"{self.progress_indicators['color'] * filled}{'⚪' * empty} {percentage:.1f}%"
        elif style == "bars":
            filled = int(percentage / 5)
            empty = 20 - filled
            return f"█{'█' * filled}{'░' * empty} {percentage:.1f}%"
        else:
            return f"{percentage:.1f}%"
    
    def create_welcome_message(self, user_name: str, user_level: str = "newcomer") -> str:
        """Create personalized welcome message"""
        badge_info = get_badge_info(user_level)
        badge_icon = badge_info.get('icon', '🆕')
        
        welcome = f"""
{self.theme['primary_color']} **خوش آمدید!**

سلام {user_name} عزیز! 👋

{badge_icon} شما در سطح **{badge_info.get('name', 'تازه‌وارد')}** هستید.

🎓 **امکانات ربات:**
   • دوره‌های آموزشی با کیفیت
   • سیستم امتیازدهی و نشان‌ها
   • پشتیبانی ۲۴/۷
   • محتوای شخصی‌سازی شده
   • تحلیل پیشرفت تحصیلی

🚀 **برای شروع، یکی از گزینه‌های زیر را انتخاب کنید:**
"""
        return welcome.strip()

# ============================================================================
# AI & RECOMMENDATION ENGINE
# ============================================================================
class AIRecommendationEngine:
    """AI-powered recommendation system"""
    
    def __init__(self):
        self.openai_client = None
        self._init_ai()
    
    def _init_ai(self):
        """Initialize AI client"""
        if OPENAI_AVAILABLE and OPENAI_API_KEY:
            try:
                openai.api_key = OPENAI_API_KEY
                self.openai_client = openai
                logger.info("OpenAI client initialized successfully")
            except Exception as e:
                logger.warning(f"OpenAI initialization failed: {e}")
    
    async def get_personalized_recommendations(self, user_profile: UserProfile) -> List[Dict[str, Any]]:
        """Get personalized course recommendations"""
        if not self.openai_client:
            return self._get_basic_recommendations(user_profile)
        
        try:
            prompt = f"""
            Based on this user profile, recommend the best courses:
            - Grade: {user_profile.grade}
            - Field: {user_profile.field}
            - Level: {user_profile.level}
            - Goals: {user_profile.goals or 'Not specified'}
            - Previous courses: {user_profile.courses_enrolled}
            
            Available courses: {list(COURSES.keys())}
            
            Return only the course IDs in order of recommendation, separated by commas.
            """
            
            response = await asyncio.to_thread(
                self.openai_client.ChatCompletion.create,
                model=AI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=AI_MAX_TOKENS,
                temperature=0.7
            )
            
            recommended_ids = response.choices[0].message.content.strip().split(',')
            recommended_courses = []
            
            for course_id in recommended_ids:
                course_id = course_id.strip()
                if course_id in COURSES:
                    recommended_courses.append(COURSES[course_id])
            
            return recommended_courses
            
        except Exception as e:
            logger.error(f"AI recommendation error: {e}")
            return self._get_basic_recommendations(user_profile)
    
    def _get_basic_recommendations(self, user_profile: UserProfile) -> List[Dict[str, Any]]:
        """Get basic recommendations based on user profile"""
        recommendations = []
        
        # Add free courses for newcomers
        if user_profile.level == "newcomer":
            recommendations.extend(get_free_courses())
        
        # Add courses matching user's field
        for course in COURSES.values():
            if course["status"] == "active":
                if user_profile.field == "ریاضی" and "ریاضی" in course["name"]:
                    recommendations.append(course)
                elif user_profile.field == "تجربی" and "تجربی" in course["name"]:
                    recommendations.append(course)
                elif user_profile.field == "انسانی" and "انسانی" in course["name"]:
                    recommendations.append(course)
        
        # Add premium courses for advanced users
        if user_profile.level in ["learner", "expert", "master"]:
            recommendations.extend(get_premium_courses())
        
        return recommendations[:5]  # Return top 5 recommendations
    
    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of user feedback"""
        if not self.openai_client:
            return {"sentiment": "neutral", "confidence": 0.5}
        
        try:
            prompt = f"""
            Analyze the sentiment of this Persian text:
            "{text}"
            
            Return only: positive, negative, or neutral
            """
            
            response = await asyncio.to_thread(
                self.openai_client.ChatCompletion.create,
                model=AI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10,
                temperature=0.3
            )
            
            sentiment = response.choices[0].message.content.strip().lower()
            return {"sentiment": sentiment, "confidence": 0.8}
            
        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
            return {"sentiment": "neutral", "confidence": 0.5}
    
    async def generate_study_plan(self, user_profile: UserProfile) -> str:
        """Generate personalized study plan"""
        if not self.openai_client:
            return self._get_basic_study_plan(user_profile)
        
        try:
            prompt = f"""
            Create a personalized study plan for a {user_profile.grade} grade student in {user_profile.field} field.
            Goals: {user_profile.goals or 'Improve academic performance'}
            
            Return a structured study plan in Persian with daily/weekly schedule.
            """
            
            response = await asyncio.to_thread(
                self.openai_client.ChatCompletion.create,
                model=AI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Study plan generation error: {e}")
            return self._get_basic_study_plan(user_profile)
    
    def _get_basic_study_plan(self, user_profile: UserProfile) -> str:
        """Get basic study plan"""
        return f"""
📚 **برنامه مطالعه شخصی‌سازی شده**

🎯 **اهداف:** {user_profile.goals or 'بهبود عملکرد تحصیلی'}

📅 **برنامه هفتگی:**

**شنبه تا چهارشنبه:**
   • ۱۷:۰۰ - ۱۸:۰۰: مطالعه دروس {user_profile.field}
   • ۱۸:۰۰ - ۱۹:۰۰: حل تمرین
   • ۱۹:۰۰ - ۲۰:۰۰: مرور مطالب

**پنجشنبه:**
   • ۱۴:۰۰ - ۱۶:۰۰: کلاس‌های رایگان استاد حاتمی
   • ۱۶:۰۰ - ۱۷:۰۰: حل مسئله

**جمعه:**
   • ۱۰:۰۰ - ۱۲:۰۰: مرور هفتگی
   • ۱۵:۰۰ - ۱۷:۰۰: کلاس‌های تخصصی

💡 **نکات مهم:**
   • هر روز حداقل ۲ ساعت مطالعه
   • حل حداقل ۵ مسئله در روز
   • مرور مطالب هفته قبل
   • شرکت در کلاس‌های آنلاین
        """.strip()

# ============================================================================
# GAMIFICATION SYSTEM
# ============================================================================
class GamificationSystem:
    """Advanced gamification system"""
    
    def __init__(self, data_manager: EnhancedDataManager):
        self.data_manager = data_manager
    
    async def award_points(self, user_id: int, action: str, points: int = None) -> bool:
        """Award points to user for specific action"""
        try:
            user_profile = await self.data_manager.load_user_data(user_id)
            if not user_profile:
                return False
            
            # Get points for action
            if points is None:
                points = GAMIFICATION["points_system"].get(action, 0)
            
            # Award points
            user_profile.points += points
            
            # Check for level up
            old_level = user_profile.level
            new_level = get_user_level(user_profile.points)
            
            if new_level != old_level:
                user_profile.level = new_level
                badge_info = get_badge_info(new_level)
                user_profile.badges.append(badge_info.get('name', new_level))
                
                # Save updated profile
                await self.data_manager.save_user_data(user_profile)
                
                logger.info(f"User {user_id} leveled up from {old_level} to {new_level}")
                return True
            
            # Save updated profile
            await self.data_manager.save_user_data(user_profile)
            logger.info(f"Awarded {points} points to user {user_id} for {action}")
            return True
            
        except Exception as e:
            logger.error(f"Error awarding points: {e}")
            return False
    
    async def get_leaderboard(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """Get top users leaderboard"""
        try:
            leaderboard = []
            
            # Get all user files
            for file_path in self.data_manager.data_dir.glob("user_*.json"):
                try:
                    user_id = int(file_path.stem.split('_')[1])
                    user_profile = await self.data_manager.load_user_data(user_id)
                    
                    if user_profile:
                        leaderboard.append({
                            'user_id': user_id,
                            'name': f"{user_profile.first_name} {user_profile.last_name}",
                            'points': user_profile.points,
                            'level': user_profile.level,
                            'badge_icon': get_badge_info(user_profile.level).get('icon', '🆕')
                        })
                except Exception as e:
                    logger.error(f"Error reading user file {file_path}: {e}")
            
            # Sort by points and return top N
            leaderboard.sort(key=lambda x: x['points'], reverse=True)
            return leaderboard[:top_n]
            
        except Exception as e:
            logger.error(f"Error getting leaderboard: {e}")
            return []
    
    async def check_achievements(self, user_id: int) -> List[str]:
        """Check and award achievements"""
        try:
            user_profile = await self.data_manager.load_user_data(user_id)
            if not user_profile:
                return []
            
            new_achievements = []
            
            # Check various achievements
            if user_profile.points >= 1000 and "امتیاز ۱۰۰۰" not in user_profile.achievements:
                new_achievements.append("امتیاز ۱۰۰۰")
            
            if len(user_profile.courses_enrolled) >= 3 and "دانشجوی فعال" not in user_profile.achievements:
                new_achievements.append("دانشجوی فعال")
            
            if user_profile.study_time >= 1000 and "مطالعه‌گر سخت‌کوش" not in user_profile.achievements:
                new_achievements.append("مطالعه‌گر سخت‌کوش")
            
            if user_profile.feedback_given >= 10 and "نظر دهنده" not in user_profile.achievements:
                new_achievements.append("نظر دهنده")
            
            if user_profile.referrals >= 5 and "معرف" not in user_profile.achievements:
                new_achievements.append("معرف")
            
            # Add new achievements
            if new_achievements:
                user_profile.achievements.extend(new_achievements)
                await self.data_manager.save_user_data(user_profile)
                
                # Award bonus points for achievements
                await self.award_points(user_id, "achievement", len(new_achievements) * 50)
            
            return new_achievements
            
        except Exception as e:
            logger.error(f"Error checking achievements: {e}")
            return []

# ============================================================================
# RATE LIMITING & SECURITY
# ============================================================================
class RateLimiter:
    """Rate limiting system"""
    
    def __init__(self):
        self.user_requests = {}
        self.ip_requests = {}
    
    def is_allowed(self, user_id: int, ip: str = None) -> bool:
        """Check if request is allowed"""
        now = datetime.now()
        
        # Check user rate limit
        if user_id in self.user_requests:
            user_times = self.user_requests[user_id]
            # Remove old requests
            user_times = [t for t in user_times if (now - t).seconds < 60]
            
            if len(user_times) >= RATE_LIMIT_PER_USER:
                return False
            
            user_times.append(now)
            self.user_requests[user_id] = user_times
        else:
            self.user_requests[user_id] = [now]
        
        # Check IP rate limit
        if ip:
            if ip in self.ip_requests:
                ip_times = self.ip_requests[ip]
                ip_times = [t for t in ip_times if (now - t).seconds < 60]
                
                if len(ip_times) >= RATE_LIMIT_PER_IP:
                    return False
                
                ip_times.append(now)
                self.ip_requests[ip] = ip_times
            else:
                self.ip_requests[ip] = [now]
        
        return True

# ============================================================================
# MAIN OPTIMIZED BOT CLASS
# ============================================================================
class OptimizedOstadHatamiBot:
    """200X Optimized Telegram Bot for Ostad Hatami"""
    
    def __init__(self):
        # Initialize core components
        self.cache_manager = EnhancedCacheManager()
        self.data_manager = EnhancedDataManager(self.cache_manager)
        self.ui_manager = EnhancedUIManager()
        self.ai_engine = AIRecommendationEngine()
        self.gamification = GamificationSystem(self.data_manager)
        self.rate_limiter = RateLimiter()
        
        # Initialize bot application
        self.application = Application.builder().token(BOT_TOKEN).build()
        
        # Setup handlers
        self.setup_handlers()
        
        logger.info("Optimized Ostad Hatami Bot initialized successfully")
    
    def setup_handlers(self):
        """Setup all bot handlers"""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("menu", self.show_main_menu))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("profile", self.show_profile))
        self.application.add_handler(CommandHandler("leaderboard", self.show_leaderboard))
        self.application.add_handler(CommandHandler("study_plan", self.show_study_plan))
        self.application.add_handler(CommandHandler("recommendations", self.show_recommendations))
        
        # Enhanced registration conversation handler
        conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler("register", self.start_registration),
                CallbackQueryHandler(self.start_registration, pattern="^start_registration$")
            ],
            states={
                ENTERING_FIRST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.enter_first_name)],
                ENTERING_LAST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.enter_last_name)],
                ENTERING_PHONE: [
                    MessageHandler(filters.CONTACT, self.enter_phone_contact),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.enter_phone_manual)
                ],
                ENTERING_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.enter_city)],
                ENTERING_GRADE: [CallbackQueryHandler(self.enter_grade)],
                ENTERING_FIELD: [CallbackQueryHandler(self.enter_field)],
                ENTERING_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.enter_email)],
                ENTERING_BIRTH_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.enter_birth_date)],
                ENTERING_PARENT_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.enter_parent_phone)],
                ENTERING_GOALS: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.enter_goals)]
            },
            fallbacks=[CommandHandler("cancel", self.cancel_registration)]
        )
        self.application.add_handler(conv_handler)
        
        # Callback query handler
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # Error handler
        self.application.add_error_handler(self.error_handler)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced start command with personalization"""
        user = update.effective_user
        
        # Rate limiting
        if not self.rate_limiter.is_allowed(user.id):
            await update.message.reply_text(ERROR_MESSAGES["rate_limit_exceeded"])
            return
        
        # Check if user exists
        if await self.data_manager.user_exists(user.id):
            user_profile = await self.data_manager.load_user_data(user.id)
            welcome_text = self.ui_manager.create_welcome_message(
                user.first_name, 
                user_profile.level
            )
            
            # Award daily login points
            await self.gamification.award_points(user.id, "daily_login")
            
            # Check achievements
            new_achievements = await self.gamification.check_achievements(user.id)
            if new_achievements:
                welcome_text += f"\n\n🏆 **دستاورد جدید:** {', '.join(new_achievements)}"
            
            await self.show_main_menu(update, context)
        else:
            welcome_text = f"سلام {user.first_name} خوش آمدی! 🎓\n\nبرای استفاده از ربات ابتدا باید ثبت‌نام کنی."
            
            buttons = [
                ["📝 ثبت‌نام در ربات", "start_registration"],
                ["ℹ️ راهنمای استفاده", "help_info"]
            ]
            keyboard = self.ui_manager.create_enhanced_keyboard(buttons, "wide")
            
            await update.message.reply_text(welcome_text, reply_markup=keyboard)
    
    async def start_registration(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced registration start"""
        user = update.effective_user
        
        if await self.data_manager.user_exists(user.id):
            await update.message.reply_text("شما قبلاً ثبت‌نام کرده‌اید! ✅")
            await self.show_main_menu(update, context)
            return ConversationHandler.END
        
        context.user_data['user_id'] = user.id
        
        welcome_text = """
🎓 **ثبت‌نام در ربات استاد حاتمی**

خوش آمدید! برای شروع، لطفاً اطلاعات خود را وارد کنید.

📝 **مرحله ۱ از ۱۰:** نام
لطفاً نام خود را وارد کنید:
        """.strip()
        
        await update.message.reply_text(welcome_text, reply_markup=ReplyKeyboardRemove())
        return ENTERING_FIRST_NAME
    
    async def enter_first_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced first name input"""
        context.user_data['first_name'] = update.message.text
        
        progress = self.ui_manager.show_progress(1, 10)
        text = f"""
✅ نام ثبت شد: {update.message.text}

{progress}

📝 **مرحله ۲ از ۱۰:** نام خانوادگی
لطفاً نام خانوادگی خود را وارد کنید:
        """.strip()
        
        await update.message.reply_text(text)
        return ENTERING_LAST_NAME
    
    async def enter_last_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced last name input"""
        context.user_data['last_name'] = update.message.text
        
        progress = self.ui_manager.show_progress(2, 10)
        text = f"""
✅ نام خانوادگی ثبت شد: {update.message.text}

{progress}

📝 **مرحله ۳ از ۱۰:** شماره تلفن
لطفاً شماره تلفن خود را وارد کنید:
        """.strip()
        
        keyboard = [
            [KeyboardButton("📱 ارسال شماره تلفن", request_contact=True)],
            [KeyboardButton("✏️ ورود دستی شماره")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        
        await update.message.reply_text(text, reply_markup=reply_markup)
        return ENTERING_PHONE
    
    async def enter_phone_contact(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced phone contact input"""
        contact = update.message.contact
        context.user_data['phone'] = contact.phone_number
        
        progress = self.ui_manager.show_progress(3, 10)
        text = f"""
✅ شماره تلفن ثبت شد: {contact.phone_number}

{progress}

📝 **مرحله ۴ از ۱۰:** شهر
لطفاً شهر محل سکونت خود را وارد کنید:
        """.strip()
        
        await update.message.reply_text(text, reply_markup=ReplyKeyboardRemove())
        return ENTERING_CITY
    
    async def enter_phone_manual(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced manual phone input"""
        phone = update.message.text
        
        if not validate_phone(phone):
            await update.message.reply_text(ERROR_MESSAGES["invalid_phone"])
            return ENTERING_PHONE
        
        context.user_data['phone'] = phone
        
        progress = self.ui_manager.show_progress(3, 10)
        text = f"""
✅ شماره تلفن ثبت شد: {phone}

{progress}

📝 **مرحله ۴ از ۱۰:** شهر
لطفاً شهر محل سکونت خود را وارد کنید:
        """.strip()
        
        await update.message.reply_text(text, reply_markup=ReplyKeyboardRemove())
        return ENTERING_CITY
    
    async def enter_city(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced city input"""
        context.user_data['city'] = update.message.text
        
        progress = self.ui_manager.show_progress(4, 10)
        text = f"""
✅ شهر ثبت شد: {update.message.text}

{progress}

📝 **مرحله ۵ از ۱۰:** پایه تحصیلی
لطفاً پایه تحصیلی خود را انتخاب کنید:
        """.strip()
        
        buttons = [
            ["پایه ۹", "grade_9"],
            ["پایه ۱۰", "grade_10"],
            ["پایه ۱۱", "grade_11"]
        ]
        keyboard = self.ui_manager.create_enhanced_keyboard(buttons, "wide")
        
        await update.message.reply_text(text, reply_markup=keyboard)
        return ENTERING_GRADE
    
    async def enter_grade(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced grade selection"""
        query = update.callback_query
        await query.answer()
        
        grade = query.data.replace('grade_', '')
        context.user_data['grade'] = grade
        
        progress = self.ui_manager.show_progress(5, 10)
        text = f"""
✅ پایه تحصیلی ثبت شد: {GRADES.get(grade, grade)}

{progress}

📝 **مرحله ۶ از ۱۰:** رشته تحصیلی
لطفاً رشته تحصیلی خود را انتخاب کنید:
        """.strip()
        
        buttons = [
            ["ریاضی", "field_math"],
            ["تجربی", "field_bio"],
            ["انسانی", "field_human"]
        ]
        keyboard = self.ui_manager.create_enhanced_keyboard(buttons, "wide")
        
        await query.edit_message_text(text, reply_markup=keyboard)
        return ENTERING_FIELD
    
    async def enter_field(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced field selection"""
        query = update.callback_query
        await query.answer()
        
        field = query.data.replace('field_', '')
        field_names = {
            'math': 'ریاضی',
            'bio': 'تجربی', 
            'human': 'انسانی'
        }
        context.user_data['field'] = field_names.get(field, field)
        
        progress = self.ui_manager.show_progress(6, 10)
        text = f"""
✅ رشته تحصیلی ثبت شد: {context.user_data['field']}

{progress}

📝 **مرحله ۷ از ۱۰:** ایمیل (اختیاری)
لطفاً ایمیل خود را وارد کنید یا /skip را بزنید:
        """.strip()
        
        await query.edit_message_text(text, reply_markup=ReplyKeyboardRemove())
        return ENTERING_EMAIL
    
    async def enter_email(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced email input"""
        email = update.message.text
        
        if email.lower() == '/skip':
            context.user_data['email'] = None
        elif not validate_email(email):
            await update.message.reply_text(ERROR_MESSAGES["invalid_email"])
            return ENTERING_EMAIL
        else:
            context.user_data['email'] = email
        
        progress = self.ui_manager.show_progress(7, 10)
        text = f"""
✅ ایمیل ثبت شد: {email if email != '/skip' else 'ثبت نشده'}

{progress}

📝 **مرحله ۸ از ۱۰:** تاریخ تولد (اختیاری)
لطفاً تاریخ تولد خود را وارد کنید (YYYY-MM-DD) یا /skip را بزنید:
        """.strip()
        
        await update.message.reply_text(text)
        return ENTERING_BIRTH_DATE
    
    async def enter_birth_date(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced birth date input"""
        birth_date = update.message.text
        
        if birth_date.lower() == '/skip':
            context.user_data['birth_date'] = None
        else:
            try:
                datetime.strptime(birth_date, "%Y-%m-%d")
                context.user_data['birth_date'] = birth_date
            except ValueError:
                await update.message.reply_text("لطفاً تاریخ را در فرمت صحیح وارد کنید (YYYY-MM-DD)")
                return ENTERING_BIRTH_DATE
        
        progress = self.ui_manager.show_progress(8, 10)
        text = f"""
✅ تاریخ تولد ثبت شد: {birth_date if birth_date != '/skip' else 'ثبت نشده'}

{progress}

📝 **مرحله ۹ از ۱۰:** شماره تلفن والدین (اختیاری)
لطفاً شماره تلفن والدین را وارد کنید یا /skip را بزنید:
        """.strip()
        
        await update.message.reply_text(text)
        return ENTERING_PARENT_PHONE
    
    async def enter_parent_phone(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced parent phone input"""
        parent_phone = update.message.text
        
        if parent_phone.lower() == '/skip':
            context.user_data['parent_phone'] = None
        elif not validate_phone(parent_phone):
            await update.message.reply_text(ERROR_MESSAGES["invalid_phone"])
            return ENTERING_PARENT_PHONE
        else:
            context.user_data['parent_phone'] = parent_phone
        
        progress = self.ui_manager.show_progress(9, 10)
        text = f"""
✅ شماره تلفن والدین ثبت شد: {parent_phone if parent_phone != '/skip' else 'ثبت نشده'}

{progress}

📝 **مرحله ۱۰ از ۱۰:** اهداف تحصیلی
لطفاً اهداف تحصیلی خود را بنویسید:
        """.strip()
        
        await update.message.reply_text(text)
        return ENTERING_GOALS
    
    async def enter_goals(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced goals input and registration completion"""
        query = update.callback_query if hasattr(update, 'callback_query') else None
        
        if query:
            await query.answer()
            goals = query.data
        else:
            goals = update.message.text
        
        context.user_data['goals'] = goals
        
        # Create user profile
        user_id = context.user_data['user_id']
        user_profile = UserProfile(
            user_id=user_id,
            first_name=context.user_data['first_name'],
            last_name=context.user_data['last_name'],
            phone=context.user_data['phone'],
            city=context.user_data['city'],
            grade=context.user_data['grade'],
            field=context.user_data['field'],
            email=context.user_data.get('email'),
            birth_date=context.user_data.get('birth_date'),
            parent_phone=context.user_data.get('parent_phone'),
            goals=goals
        )
        
        # Save user data
        if await self.data_manager.save_user_data(user_profile):
            # Award registration points
            await self.gamification.award_points(user_id, "registration", 100)
            
            # Check achievements
            new_achievements = await self.gamification.check_achievements(user_id)
            
            completion_text = f"""
🎉 **ثبت‌نام شما با موفقیت انجام شد!**

✅ تمام اطلاعات شما ذخیره شد
⭐ ۱۰۰ امتیاز برای ثبت‌نام دریافت کردید
{badge_info.get('icon', '🆕')} سطح شما: {badge_info.get('name', 'تازه‌وارد')}

🚀 حالا می‌توانید از تمام امکانات ربات استفاده کنید!
            """.strip()
            
            if new_achievements:
                completion_text += f"\n\n🏆 **دستاورد جدید:** {', '.join(new_achievements)}"
            
            if query:
                await query.edit_message_text(completion_text, reply_markup=ReplyKeyboardRemove())
            else:
                await update.message.reply_text(completion_text, reply_markup=ReplyKeyboardRemove())
            
            # Show main menu
            await self.show_main_menu(update, context)
        else:
            error_text = "❌ خطا در ثبت‌نام. لطفاً دوباره تلاش کنید."
            if query:
                await query.edit_message_text(error_text, reply_markup=ReplyKeyboardRemove())
            else:
                await update.message.reply_text(error_text, reply_markup=ReplyKeyboardRemove())
        
        return ConversationHandler.END
    
    async def cancel_registration(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel registration"""
        await update.message.reply_text(
            "❌ ثبت‌نام لغو شد. می‌توانید دوباره با /register شروع کنید.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    
    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced main menu with personalization"""
        user = update.effective_user
        
        if not await self.data_manager.user_exists(user.id):
            await update.message.reply_text("لطفاً ابتدا ثبت‌نام کنید.")
            return
        
        user_profile = await self.data_manager.load_user_data(user.id)
        
        menu_text = self.ui_manager.create_welcome_message(user.first_name, user_profile.level)
        
        buttons = [
            ["🎓 دوره‌های آموزشی", "courses"],
            ["📘 کتاب انفجار خلاقیت", "book"],
            ["📊 پروفایل من", "profile"],
            ["🏆 جدول امتیازات", "leaderboard"],
            ["📚 برنامه مطالعه", "study_plan"],
            ["🎯 پیشنهادات شخصی", "recommendations"],
            ["📞 ارتباط با ما", "contact"],
            ["🌐 شبکه‌های اجتماعی", "social"],
            ["💬 کانال و گروه", "channel"],
            ["❓ راهنما", "help"]
        ]
        
        keyboard = self.ui_manager.create_enhanced_keyboard(buttons, "compact")
        
        if hasattr(update, 'message'):
            await update.message.reply_text(menu_text, reply_markup=keyboard)
        else:
            await update.callback_query.edit_message_text(menu_text, reply_markup=keyboard)
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced callback handler"""
        query = update.callback_query
        await query.answer()
        
        callback_data = query.data
        
        if callback_data == "start_registration":
            await self.start_registration(update, context)
        elif callback_data == "courses":
            await self.show_courses(query)
        elif callback_data == "book":
            await self.show_book_info(query)
        elif callback_data == "profile":
            await self.show_profile_callback(query)
        elif callback_data == "leaderboard":
            await self.show_leaderboard_callback(query)
        elif callback_data == "study_plan":
            await self.show_study_plan_callback(query)
        elif callback_data == "recommendations":
            await self.show_recommendations_callback(query)
        elif callback_data == "contact":
            await self.show_contact_info(query)
        elif callback_data == "social":
            await self.show_social_links(query)
        elif callback_data == "channel":
            await self.show_channel_info(query)
        elif callback_data == "help":
            await self.help_command_callback(query)
        elif callback_data == "back_to_menu":
            await self.show_main_menu(update, context)
        elif callback_data.startswith("enroll_"):
            course_id = callback_data.replace("enroll_", "")
            await self.enroll_in_course(query, course_id)
        elif callback_data.startswith("course_"):
            course_id = callback_data.replace("course_", "")
            await self.show_course_details(query, course_id)
    
    async def show_courses(self, query):
        """Enhanced courses display with AI recommendations"""
        user_id = query.from_user.id
        user_profile = await self.data_manager.load_user_data(user_id)
        
        if not user_profile:
            await query.edit_message_text("لطفاً ابتدا ثبت‌نام کنید.")
            return
        
        # Get personalized recommendations
        recommendations = await self.ai_engine.get_personalized_recommendations(user_profile)
        
        courses_text = "🎓 **دوره‌های آموزشی استاد حاتمی**\n\n"
        
        if recommendations:
            courses_text += "🎯 **پیشنهادات شخصی برای شما:**\n\n"
            for i, course in enumerate(recommendations[:3], 1):
                courses_text += self.ui_manager.format_course_card(course, user_profile.level)
                courses_text += f"\n\n"
        
        courses_text += "📚 **همه دوره‌ها:**\n\n"
        
        for course in get_active_courses():
            price_emoji = "🆓" if course["price"] == 0 else "💎"
            courses_text += f"{price_emoji} **{course['name']}**\n"
            courses_text += f"💰 {format_price(course['price'], course['currency'])} | "
            courses_text += f"⭐ {course['rating']}/5.0 | "
            courses_text += f"👥 {course['students']:,} دانشجو\n\n"
        
        buttons = [
            ["💎 دوره‌های ویژه", "premium_courses"],
            ["🆓 دوره‌های رایگان", "free_courses"],
            ["📊 مقایسه دوره‌ها", "compare_courses"],
            ["🔙 بازگشت به منو", "back_to_menu"]
        ]
        keyboard = self.ui_manager.create_enhanced_keyboard(buttons, "wide")
        
        await query.edit_message_text(courses_text, reply_markup=keyboard)
    
    async def show_profile_callback(self, query):
        """Show user profile via callback"""
        user_id = query.from_user.id
        user_profile = await self.data_manager.load_user_data(user_id)
        
        if not user_profile:
            await query.edit_message_text("لطفاً ابتدا ثبت‌نام کنید.")
            return
        
        profile_text = self.ui_manager.format_user_profile(user_profile)
        
        buttons = [
            ["📊 آمار پیشرفت", "progress_stats"],
            ["🏆 دستاوردها", "achievements"],
            ["⚙️ تنظیمات", "settings"],
            ["🔙 بازگشت به منو", "back_to_menu"]
        ]
        keyboard = self.ui_manager.create_enhanced_keyboard(buttons, "wide")
        
        await query.edit_message_text(profile_text, reply_markup=keyboard)
    
    async def show_leaderboard_callback(self, query):
        """Show leaderboard via callback"""
        leaderboard = await self.gamification.get_leaderboard(10)
        
        leaderboard_text = "🏆 **جدول امتیازات برتر**\n\n"
        
        for i, user in enumerate(leaderboard, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            leaderboard_text += f"{medal} {user['badge_icon']} **{user['name']}**\n"
            leaderboard_text += f"   ⭐ {user['points']:,} امتیاز | {user['level']}\n\n"
        
        buttons = [
            ["🔄 به‌روزرسانی", "leaderboard"],
            ["📊 آمار کلی", "global_stats"],
            ["🔙 بازگشت به منو", "back_to_menu"]
        ]
        keyboard = self.ui_manager.create_enhanced_keyboard(buttons, "wide")
        
        await query.edit_message_text(leaderboard_text, reply_markup=keyboard)
    
    async def show_study_plan_callback(self, query):
        """Show personalized study plan via callback"""
        user_id = query.from_user.id
        user_profile = await self.data_manager.load_user_data(user_id)
        
        if not user_profile:
            await query.edit_message_text("لطفاً ابتدا ثبت‌نام کنید.")
            return
        
        study_plan = await self.ai_engine.generate_study_plan(user_profile)
        
        buttons = [
            ["📅 برنامه هفتگی", "weekly_plan"],
            ["📊 تحلیل پیشرفت", "progress_analysis"],
            ["🎯 اهداف تحصیلی", "academic_goals"],
            ["🔙 بازگشت به منو", "back_to_menu"]
        ]
        keyboard = self.ui_manager.create_enhanced_keyboard(buttons, "wide")
        
        await query.edit_message_text(study_plan, reply_markup=keyboard)
    
    async def show_recommendations_callback(self, query):
        """Show personalized recommendations via callback"""
        user_id = query.from_user.id
        user_profile = await self.data_manager.load_user_data(user_id)
        
        if not user_profile:
            await query.edit_message_text("لطفاً ابتدا ثبت‌نام کنید.")
            return
        
        recommendations = await self.ai_engine.get_personalized_recommendations(user_profile)
        
        recommendations_text = "🎯 **پیشنهادات شخصی برای شما**\n\n"
        recommendations_text += f"بر اساس پروفایل شما ({user_profile.field} - پایه {user_profile.grade}):\n\n"
        
        for i, course in enumerate(recommendations, 1):
            recommendations_text += f"{i}. {self.ui_manager.format_course_card(course, user_profile.level)}\n\n"
        
        buttons = [
            ["📚 همه دوره‌ها", "courses"],
            ["🎓 دوره‌های مرتبط", "related_courses"],
            ["🔙 بازگشت به منو", "back_to_menu"]
        ]
        keyboard = self.ui_manager.create_enhanced_keyboard(buttons, "wide")
        
        await query.edit_message_text(recommendations_text, reply_markup=keyboard)
    
    async def show_book_info(self, query):
        """Enhanced book information display"""
        book = BOOKS["creative_explosion"]
        
        book_text = f"""
📘 **{book['name']}**

✍️ **نویسنده:** {book['author']}
📄 **تعداد صفحات:** {book['pages']} صفحه
💰 **قیمت:** {format_price(book['price'], book['currency'])}
📚 **ناشر:** {book['publisher']}
🌐 **زبان:** {book['language']}
📦 **فرمت:** {book['format']}
📊 **امتیاز:** ⭐ {book['rating']}/5.0 ({book['reviews']} نظر)

✨ **ویژگی‌های کتاب:**
"""
        for feature in book['features']:
            book_text += f"   • {feature}\n"
        
        book_text += f"""
🚚 **ارسال:** {book['shipping']}
📦 **موجودی:** {book['availability']}

📞 **برای سفارش با ما تماس بگیرید:**
        """
        
        buttons = [
            ["📞 تماس برای سفارش", "contact"],
            ["📖 نمونه صفحات", "book_sample"],
            ["⭐ نظرات خریداران", "book_reviews"],
            ["🔙 بازگشت به منو", "back_to_menu"]
        ]
        keyboard = self.ui_manager.create_enhanced_keyboard(buttons, "wide")
        
        await query.edit_message_text(book_text, reply_markup=keyboard)
    
    async def show_contact_info(self, query):
        """Enhanced contact information display"""
        contact = CONTACT_INFO
        
        contact_text = f"""
📞 **ارتباط با ما**

📱 **شماره تماس:** {contact['phone']}
📧 **ایمیل:** {contact['email']}
🌐 **وب‌سایت:** {contact['website']}
💬 **پشتیبانی تلگرام:** {contact['telegram_support']}

🏢 **آدرس:** {contact['address']}

⏰ **ساعات کاری:**
   • {contact['working_hours']['weekdays']}
   • {contact['working_hours']['weekend']}
   • {contact['working_hours']['holidays']}

⚡ **زمان پاسخگویی:** {contact['response_time']}
        """
        
        buttons = [
            ["💬 پیام به پشتیبانی", "support_message"],
            ["📞 تماس مستقیم", "direct_call"],
            ["📧 ارسال ایمیل", "send_email"],
            ["🔙 بازگشت به منو", "back_to_menu"]
        ]
        keyboard = self.ui_manager.create_enhanced_keyboard(buttons, "wide")
        
        await query.edit_message_text(contact_text, reply_markup=keyboard)
    
    async def show_social_links(self, query):
        """Enhanced social media links display"""
        social = SOCIAL_MEDIA
        
        social_text = """
🌐 **شبکه‌های اجتماعی استاد حاتمی**

📺 **یوتیوب:**
   • آموزش‌های رایگان ریاضی
   • حل مسئله‌های خلاقانه
   • تکنیک‌های حل مسئله
   • {social['youtube']['subscribers']} مشترک
   • {social['youtube']['videos']} ویدیو

📸 **اینستاگرام:**
   • نکات آموزشی روزانه
   • نمونه سوالات
   • اخبار و اطلاعیه‌ها
   • {social['instagram']['followers']} فالوور
   • {social['instagram']['posts']} پست
        """.format(social=social)
        
        buttons = [
            ["📺 کانال یوتیوب", "youtube_channel"],
            ["📸 پیج اینستاگرام", "instagram_page"],
            ["📱 اپلیکیشن موبایل", "mobile_app"],
            ["🔙 بازگشت به منو", "back_to_menu"]
        ]
        keyboard = self.ui_manager.create_enhanced_keyboard(buttons, "wide")
        
        await query.edit_message_text(social_text, reply_markup=keyboard)
    
    async def show_channel_info(self, query):
        """Enhanced channel and group information display"""
        social = SOCIAL_MEDIA
        
        channel_text = f"""
💬 **کانال و گروه همراه با استاد**

📢 **کانال تلگرام:**
   • اخبار و اطلاعیه‌های کلاس‌ها
   • نمونه سوالات و پاسخ‌ها
   • نکات آموزشی مفید
   • {social['telegram_channel']['members']} عضو

👥 **گروه مشاوره:**
   • پرسش و پاسخ
   • رفع اشکال
   • مشاوره تحصیلی
   • {social['telegram_group']['members']} عضو
        """
        
        buttons = [
            ["📢 عضویت در کانال", "join_channel"],
            ["👥 عضویت در گروه", "join_group"],
            ["📋 قوانین گروه", "group_rules"],
            ["🔙 بازگشت به منو", "back_to_menu"]
        ]
        keyboard = self.ui_manager.create_enhanced_keyboard(buttons, "wide")
        
        await query.edit_message_text(channel_text, reply_markup=keyboard)
    
    async def help_command_callback(self, query):
        """Enhanced help command via callback"""
        help_text = """
🔧 **راهنمای استفاده از ربات**

📝 **دستورات اصلی:**
/start - شروع ربات
/register - ثبت‌نام در ربات
/menu - نمایش منوی اصلی
/profile - نمایش پروفایل
/leaderboard - جدول امتیازات
/study_plan - برنامه مطالعه
/recommendations - پیشنهادات شخصی
/help - این راهنما

📚 **امکانات ربات:**
• ثبت‌نام در دوره‌های ریاضی
• تهیه کتاب انفجار خلاقیت
• سیستم امتیازدهی و نشان‌ها
• پشتیبانی ۲۴/۷
• محتوای شخصی‌سازی شده
• تحلیل پیشرفت تحصیلی
• برنامه مطالعه هوشمند

💡 **نکات مهم:**
• برای استفاده از ربات ابتدا باید ثبت‌نام کنید
• تمام اطلاعات شما به صورت امن ذخیره می‌شود
• در صورت بروز مشکل با پشتیبانی تماس بگیرید
• امتیازات خود را با فعالیت‌های مختلف افزایش دهید
        """
        
        buttons = [
            ["📖 راهنمای کامل", "full_guide"],
            ["❓ سوالات متداول", "faq"],
            ["📞 پشتیبانی", "contact"],
            ["🔙 بازگشت به منو", "back_to_menu"]
        ]
        keyboard = self.ui_manager.create_enhanced_keyboard(buttons, "wide")
        
        await query.edit_message_text(help_text, reply_markup=keyboard)
    
    async def enroll_in_course(self, query, course_id: str):
        """Enroll user in a course"""
        user_id = query.from_user.id
        user_profile = await self.data_manager.load_user_data(user_id)
        
        if not user_profile:
            await query.edit_message_text("لطفاً ابتدا ثبت‌نام کنید.")
            return
        
        course = get_course_by_id(course_id)
        if not course:
            await query.edit_message_text("دوره مورد نظر یافت نشد.")
            return
        
        # Check if already enrolled
        if course_id in user_profile.courses_enrolled:
            await query.edit_message_text("شما قبلاً در این دوره ثبت‌نام کرده‌اید! ✅")
            return
        
        # Enroll user
        user_profile.courses_enrolled.append(course_id)
        await self.data_manager.save_user_data(user_profile)
        
        # Award points
        await self.gamification.award_points(user_id, "course_enrollment", 50)
        
        # Check achievements
        new_achievements = await self.gamification.check_achievements(user_id)
        
        success_text = f"""
✅ **ثبت‌نام موفق!**

🎓 شما با موفقیت در دوره **{course['name']}** ثبت‌نام شدید!

⭐ ۵۰ امتیاز برای ثبت‌نام دریافت کردید
📊 تعداد دوره‌های شما: {len(user_profile.courses_enrolled)}
        """
        
        if new_achievements:
            success_text += f"\n🏆 **دستاورد جدید:** {', '.join(new_achievements)}"
        
        buttons = [
            ["📚 مشاهده دوره", f"course_{course_id}"],
            ["🎓 دوره‌های من", "my_courses"],
            ["🔙 بازگشت به منو", "back_to_menu"]
        ]
        keyboard = self.ui_manager.create_enhanced_keyboard(buttons, "wide")
        
        await query.edit_message_text(success_text, reply_markup=keyboard)
    
    async def show_course_details(self, query, course_id: str):
        """Show detailed course information"""
        user_id = query.from_user.id
        user_profile = await self.data_manager.load_user_data(user_id)
        
        course = get_course_by_id(course_id)
        if not course:
            await query.edit_message_text("دوره مورد نظر یافت نشد.")
            return
        
        course_text = self.ui_manager.format_course_card(course, user_profile.level if user_profile else "newcomer")
        
        # Check enrollment status
        is_enrolled = user_profile and course_id in user_profile.courses_enrolled
        
        if is_enrolled:
            buttons = [
                ["📖 ادامه دوره", f"continue_{course_id}"],
                ["📊 پیشرفت", f"progress_{course_id}"],
                ["🔙 بازگشت", "courses"]
            ]
        else:
            buttons = [
                ["📝 ثبت‌نام در دوره", f"enroll_{course_id}"],
                ["📖 نمونه محتوا", f"sample_{course_id}"],
                ["🔙 بازگشت", "courses"]
            ]
        
        keyboard = self.ui_manager.create_enhanced_keyboard(buttons, "wide")
        await query.edit_message_text(course_text, reply_markup=keyboard)
    
    async def show_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user profile via command"""
        user_id = update.effective_user.id
        user_profile = await self.data_manager.load_user_data(user_id)
        
        if not user_profile:
            await update.message.reply_text("لطفاً ابتدا ثبت‌نام کنید.")
            return
        
        profile_text = self.ui_manager.format_user_profile(user_profile)
        await update.message.reply_text(profile_text)
    
    async def show_leaderboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show leaderboard via command"""
        leaderboard = await self.gamification.get_leaderboard(10)
        
        leaderboard_text = "🏆 **جدول امتیازات برتر**\n\n"
        
        for i, user in enumerate(leaderboard, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            leaderboard_text += f"{medal} {user['badge_icon']} **{user['name']}**\n"
            leaderboard_text += f"   ⭐ {user['points']:,} امتیاز | {user['level']}\n\n"
        
        await update.message.reply_text(leaderboard_text)
    
    async def show_study_plan(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show study plan via command"""
        user_id = update.effective_user.id
        user_profile = await self.data_manager.load_user_data(user_id)
        
        if not user_profile:
            await update.message.reply_text("لطفاً ابتدا ثبت‌نام کنید.")
            return
        
        study_plan = await self.ai_engine.generate_study_plan(user_profile)
        await update.message.reply_text(study_plan)
    
    async def show_recommendations(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show recommendations via command"""
        user_id = update.effective_user.id
        user_profile = await self.data_manager.load_user_data(user_id)
        
        if not user_profile:
            await update.message.reply_text("لطفاً ابتدا ثبت‌نام کنید.")
            return
        
        recommendations = await self.ai_engine.get_personalized_recommendations(user_profile)
        
        recommendations_text = "🎯 **پیشنهادات شخصی برای شما**\n\n"
        
        for i, course in enumerate(recommendations, 1):
            recommendations_text += f"{i}. {course['name']}\n"
            recommendations_text += f"   💰 {format_price(course['price'], course['currency'])} | "
            recommendations_text += f"⭐ {course['rating']}/5.0\n\n"
        
        await update.message.reply_text(recommendations_text)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced help command"""
        help_text = """
🔧 **راهنمای استفاده از ربات**

📝 **دستورات اصلی:**
/start - شروع ربات
/register - ثبت‌نام در ربات
/menu - نمایش منوی اصلی
/profile - نمایش پروفایل
/leaderboard - جدول امتیازات
/study_plan - برنامه مطالعه
/recommendations - پیشنهادات شخصی
/help - این راهنما

📚 **امکانات ربات:**
• ثبت‌نام در دوره‌های ریاضی
• تهیه کتاب انفجار خلاقیت
• سیستم امتیازدهی و نشان‌ها
• پشتیبانی ۲۴/۷
• محتوای شخصی‌سازی شده
• تحلیل پیشرفت تحصیلی
• برنامه مطالعه هوشمند

💡 **نکات مهم:**
• برای استفاده از ربات ابتدا باید ثبت‌نام کنید
• تمام اطلاعات شما به صورت امن ذخیره می‌شود
• در صورت بروز مشکل با پشتیبانی تماس بگیرید
• امتیازات خود را با فعالیت‌های مختلف افزایش دهید
        """
        
        await update.message.reply_text(help_text)
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced error handler"""
        logger.error(f"Exception while handling an update: {context.error}")
        
        error_text = f"""
❌ **متأسفانه خطایی رخ داده است.**

🔧 **اطلاعات خطا:**
   • نوع: {type(context.error).__name__}
   • زمان: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📞 **پشتیبانی:** @Ostad_Hatami

لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید.
        """
        
        if update.effective_message:
            await update.effective_message.reply_text(error_text)
        elif update.callback_query:
            await update.callback_query.edit_message_text(error_text)

# ============================================================================
# MAIN FUNCTION
# ============================================================================
async def main():
    """Main function to run the optimized bot"""
    try:
        # Validate bot token
        if not BOT_TOKEN:
            raise ValueError("BOT_TOKEN environment variable is required")
        
        # Create and run bot
        bot = OptimizedOstadHatamiBot()
        
        logger.info("🚀 Optimized Ostad Hatami Bot starting...")
        logger.info(f"📊 Version: {SYSTEM['version']}")
        logger.info(f"🔧 Debug Mode: {SYSTEM['debug_mode']}")
        logger.info(f"💾 Cache Enabled: {CACHE_ENABLED}")
        logger.info(f"🤖 AI Enabled: {AI_ENABLED}")
        logger.info(f"🎮 Gamification Enabled: {GAMIFICATION['enabled']}")
        
        # Start the bot
        await bot.application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 