#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration management for Ostad Hatami Bot
Centralized settings with environment variable support
"""

import os
from typing import Dict, List, Any
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class DatabaseConfig:
    """Database configuration settings"""

    type: str = "json"  # json, sqlite, postgresql
    path: str = "data"
    backup_enabled: bool = True
    backup_interval_hours: int = 24
    max_backup_files: int = 7


@dataclass
class PerformanceConfig:
    """Performance and caching settings"""

    cache_ttl_seconds: int = 300
    max_requests_per_minute: int = 10
    cleanup_interval_seconds: int = 300
    max_concurrent_users: int = 1000
    request_timeout_seconds: int = 30
    enable_compression: bool = True


@dataclass
class SecurityConfig:
    """Security and validation settings"""

    max_name_length: int = 50
    min_name_length: int = 2
    allowed_phone_formats: List[str] = None
    enable_input_sanitization: bool = True
    max_file_size_mb: int = 10
    allowed_file_types: List[str] = None

    def __post_init__(self):
        if self.allowed_phone_formats is None:
            self.allowed_phone_formats = [
                r"^\+98[0-9]{10}$",
                r"^09[0-9]{9}$",
                r"^9[0-9]{9}$",
                r"^0[0-9]{10}$",
            ]
        if self.allowed_file_types is None:
            self.allowed_file_types = ["jpg", "jpeg", "png", "pdf"]


@dataclass
class LoggingConfig:
    """Logging configuration"""

    level: str = "INFO"
    format: str = (
        "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
    )
    file_enabled: bool = True
    console_enabled: bool = True
    max_file_size_mb: int = 10
    backup_count: int = 5
    performance_log_enabled: bool = True


@dataclass
class BotConfig:
    """Bot-specific configuration"""

    name: str = "Ostad Hatami Math Classes Bot"
    version: str = "2.0.0"
    admin_user_ids: List[int] = None
    maintenance_mode: bool = False
    welcome_message_template: str = None
    support_contact: str = "@Ostad_Hatami"

    def __post_init__(self):
        if self.admin_user_ids is None:
            self.admin_user_ids = []
        if self.welcome_message_template is None:
            self.welcome_message_template = """سلام {first_name} عزیز! 🌟

به ربات ثبت‌نام کلاس‌های رایگان استاد حاتمی خوش آمدید.

🎓 **کلاس‌های رایگان ریاضی در حال برگزاری است!**

برای استفاده از خدمات، لطفاً اطلاعات خود را وارد کنید.
دقت فرمایید اطلاعات به‌درستی وارد شود."""


class Config:
    """Main configuration class"""

    def __init__(self):
        # Bot token (required)
        self.bot_token = os.getenv("BOT_TOKEN")
        if not self.bot_token:
            raise ValueError("BOT_TOKEN environment variable is required")

        # Initialize configuration sections
        self.database = DatabaseConfig(
            type=os.getenv("DB_TYPE", "json"),
            path=os.getenv("DB_PATH", "data"),
            backup_enabled=os.getenv("DB_BACKUP_ENABLED", "true").lower() == "true",
            backup_interval_hours=int(os.getenv("DB_BACKUP_INTERVAL_HOURS", "24")),
            max_backup_files=int(os.getenv("DB_MAX_BACKUP_FILES", "7")),
        )

        self.performance = PerformanceConfig(
            cache_ttl_seconds=int(os.getenv("CACHE_TTL_SECONDS", "300")),
            max_requests_per_minute=int(os.getenv("MAX_REQUESTS_PER_MINUTE", "10")),
            cleanup_interval_seconds=int(os.getenv("CLEANUP_INTERVAL_SECONDS", "300")),
            max_concurrent_users=int(os.getenv("MAX_CONCURRENT_USERS", "1000")),
            request_timeout_seconds=int(os.getenv("REQUEST_TIMEOUT_SECONDS", "30")),
            enable_compression=os.getenv("ENABLE_COMPRESSION", "true").lower()
            == "true",
        )

        self.security = SecurityConfig(
            max_name_length=int(os.getenv("MAX_NAME_LENGTH", "50")),
            min_name_length=int(os.getenv("MIN_NAME_LENGTH", "2")),
            enable_input_sanitization=os.getenv(
                "ENABLE_INPUT_SANITIZATION", "true"
            ).lower()
            == "true",
            max_file_size_mb=int(os.getenv("MAX_FILE_SIZE_MB", "10")),
        )

        self.logging = LoggingConfig(
            level=os.getenv("LOG_LEVEL", "INFO"),
            file_enabled=os.getenv("LOG_FILE_ENABLED", "true").lower() == "true",
            console_enabled=os.getenv("LOG_CONSOLE_ENABLED", "true").lower() == "true",
            max_file_size_mb=int(os.getenv("LOG_MAX_FILE_SIZE_MB", "10")),
            backup_count=int(os.getenv("LOG_BACKUP_COUNT", "5")),
            performance_log_enabled=os.getenv("PERFORMANCE_LOG_ENABLED", "true").lower()
            == "true",
        )

        self.bot = BotConfig(
            admin_user_ids=[
                int(uid)
                for uid in os.getenv("ADMIN_USER_IDS", "").split(",")
                if uid.strip()
            ],
            maintenance_mode=os.getenv("MAINTENANCE_MODE", "false").lower() == "true",
        )

        # Educational data
        self.grades = ["دهم", "یازدهم", "دوازدهم"]
        self.majors = ["ریاضی", "تجربی", "انسانی", "هنر"]
        self.provinces = [
            "تهران",
            "خراسان رضوی",
            "اصفهان",
            "فارس",
            "آذربایجان شرقی",
            "مازندران",
            "گیلان",
            "خوزستان",
            "قم",
            "البرز",
            "سایر",
        ]

        self.cities_by_province = {
            "تهران": ["تهران", "شهریار", "ورامین", "دماوند", "فیروزکوه"],
            "خراسان رضوی": ["مشهد", "نیشابور", "سبزوار", "تربت حیدریه", "کاشمر"],
            "اصفهان": ["اصفهان", "کاشان", "نجف‌آباد", "خمینی‌شهر", "شاهین‌شهر"],
            "فارس": ["شیراز", "مرودشت", "جهرم", "فسا", "کازرون"],
            "آذربایجان شرقی": ["تبریز", "مراغه", "میانه", "اهر", "بناب"],
            "مازندران": ["ساری", "بابل", "آمل", "قائم‌شهر", "نوشهر"],
            "گیلان": ["رشت", "انزلی", "لاهیجان", "آستارا", "تالش"],
            "خوزستان": ["اهواز", "دزفول", "ماهشهر", "ایذه", "شوشتر"],
            "قم": ["قم"],
            "البرز": ["کرج", "فردیس", "محمدشهر", "ماهدشت", "اشتهارد"],
            "سایر": ["سایر"],
        }

        # Contact information
        self.contact_info = {
            "phone": "۰۹۱۲۳۴۵۶۷۸۹",
            "telegram": "@Ostad_Hatami",
            "email": "info@ostadhatami.ir",
            "website": "www.ostadhatami.ir",
        }

    def validate(self) -> bool:
        """Validate configuration settings"""
        try:
            assert self.bot_token, "BOT_TOKEN is required"
            assert self.performance.cache_ttl_seconds > 0, "Cache TTL must be positive"
            assert (
                self.performance.max_requests_per_minute > 0
            ), "Max requests must be positive"
            assert self.security.min_name_length > 0, "Min name length must be positive"
            assert (
                self.security.max_name_length > self.security.min_name_length
            ), "Max name length must be greater than min"
            return True
        except AssertionError as e:
            raise ValueError(f"Configuration validation failed: {e}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for logging"""
        return {
            "bot_token": "***" if self.bot_token else None,
            "database": {
                "type": self.database.type,
                "path": self.database.path,
                "backup_enabled": self.database.backup_enabled,
            },
            "performance": {
                "cache_ttl_seconds": self.performance.cache_ttl_seconds,
                "max_requests_per_minute": self.performance.max_requests_per_minute,
                "max_concurrent_users": self.performance.max_concurrent_users,
            },
            "security": {
                "max_name_length": self.security.max_name_length,
                "min_name_length": self.security.min_name_length,
                "enable_input_sanitization": self.security.enable_input_sanitization,
            },
            "logging": {
                "level": self.logging.level,
                "file_enabled": self.logging.file_enabled,
                "console_enabled": self.logging.console_enabled,
            },
            "bot": {
                "name": self.bot.name,
                "version": self.bot.version,
                "maintenance_mode": self.bot.maintenance_mode,
            },
        }


# Global configuration instance
config = Config()
