#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced validation utilities for Ostad Hatami Bot
"""

import re
import html
from typing import Optional, List, Dict, Any
from config import config


class Validator:
    """Enhanced data validation utilities with security features"""

    # Compile regex patterns once for better performance
    # Persian-only names (with space and hyphen), 2-50 chars
    _name_pattern = re.compile(r"^[آ-یٔ\s\-]{2,50}$")
    _phone_patterns = [
        re.compile(r"^\+98[0-9]{10}$"),
        re.compile(r"^09[0-9]{9}$"),
        re.compile(r"^9[0-9]{9}$"),
        re.compile(r"^0[0-9]{10}$"),
    ]
    _email_pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    _url_pattern = re.compile(r"^https?://[^\s/$.?#].[^\s]*$")

    # Digit maps for Persian and Arabic-Indic numerals to ASCII
    _persian_digits = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
    _arabic_digits = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")

    # Security patterns
    _sql_injection_pattern = re.compile(
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b)",
        re.IGNORECASE,
    )
    _xss_pattern = re.compile(
        r"(<script|javascript:|vbscript:|onload=|onerror=|onclick=)", re.IGNORECASE
    )

    @classmethod
    def sanitize_input(cls, text: str, max_length: Optional[int] = None) -> str:
        """Sanitize user input to prevent XSS and injection attacks"""
        if not text:
            return ""

        # Convert to string if needed
        text = str(text)

        # Remove HTML tags and entities
        text = html.escape(text)

        # Remove potential SQL injection patterns
        text = cls._sql_injection_pattern.sub("", text)

        # Remove potential XSS patterns
        text = cls._xss_pattern.sub("", text)

        # Trim whitespace
        text = text.strip()

        # Apply length limit if specified
        if max_length and len(text) > max_length:
            text = text[:max_length]

        return text

    @classmethod
    def convert_to_english_digits(cls, text: str) -> str:
        """Convert Persian/Arabic-Indic digits to ASCII English digits."""
        if not isinstance(text, str):
            return text
        # First convert Persian digits, then Arabic-Indic
        converted = text.translate(cls._persian_digits)
        converted = converted.translate(cls._arabic_digits)
        return converted

    @classmethod
    def validate_name(cls, name: str, field_name: str = "نام") -> tuple[bool, str]:
        """Validate Persian/Arabic names with enhanced error messages"""
        if not name:
            return False, f"{field_name} نمی‌تواند خالی باشد."

        # Sanitize input if enabled
        if config.security.enable_input_sanitization:
            name = cls.sanitize_input(name, config.security.max_name_length)

        # Check length
        if len(name.strip()) < config.security.min_name_length:
            return (
                False,
                f"{field_name} باید حداقل {config.security.min_name_length} حرف باشد.",
            )

        if len(name.strip()) > config.security.max_name_length:
            return (
                False,
                f"{field_name} نمی‌تواند بیشتر از {config.security.max_name_length} حرف باشد.",
            )

        # Check pattern
        if not cls._name_pattern.match(name.strip()):
            return (
                False,
                f"{field_name} باید فقط شامل حروف فارسی، عربی یا انگلیسی باشد.",
            )

        return True, name.strip()

    @classmethod
    def validate_phone(cls, phone: str) -> tuple[bool, str]:
        """Validate Iranian phone numbers with enhanced validation"""
        if not phone:
            return False, "شماره تلفن نمی‌تواند خالی باشد."

        # Sanitize input
        phone = cls.convert_to_english_digits(phone)
        phone = re.sub(r"[\s\-\(\)]", "", phone)

        # Check if any pattern matches
        for pattern in cls._phone_patterns:
            if pattern.match(phone):
                normalized = cls.normalize_phone(phone)
                # Ensure normalized is strictly ASCII digits (no Persian digits)
                normalized = cls.convert_to_english_digits(normalized)
                return True, normalized

        return (
            False,
            "شماره تلفن نامعتبر است. لطفاً شماره معتبر وارد کنید (مثال: 09121234567)",
        )

    @classmethod
    def validate_email(cls, email: str) -> tuple[bool, str]:
        """Validate email addresses"""
        if not email:
            return False, "ایمیل نمی‌تواند خالی باشد."

        email = email.strip().lower()

        if not cls._email_pattern.match(email):
            return False, "فرمت ایمیل نامعتبر است."

        return True, email

    @classmethod
    def validate_url(cls, url: str) -> tuple[bool, str]:
        """Validate URLs"""
        if not url:
            return False, "آدرس وب نمی‌تواند خالی باشد."

        url = url.strip()

        if not cls._url_pattern.match(url):
            return False, "فرمت آدرس وب نامعتبر است."

        return True, url

    @classmethod
    def validate_grade(cls, grade: str) -> tuple[bool, str]:
        """Validate educational grade"""
        if not grade:
            return False, "پایه تحصیلی باید انتخاب شود."

        if grade not in config.grades:
            return False, "پایه تحصیلی نامعتبر است."

        return True, grade

    @classmethod
    def validate_major(cls, major: str) -> tuple[bool, str]:
        """Validate educational major"""
        if not major:
            return False, "رشته تحصیلی باید انتخاب شود."

        if major not in config.majors:
            return False, "رشته تحصیلی نامعتبر است."

        return True, major

    @classmethod
    def validate_province(cls, province: str) -> tuple[bool, str]:
        """Validate province selection"""
        if not province:
            return False, "استان باید انتخاب شود."

        if province not in config.provinces:
            return False, "استان نامعتبر است."

        return True, province

    @classmethod
    def validate_city(cls, city: str, province: str) -> tuple[bool, str]:
        """Validate city selection for a province"""
        if not city:
            return False, "شهر باید انتخاب شود."

        valid_cities = config.cities_by_province.get(province, [])
        if city not in valid_cities:
            return False, "شهر نامعتبر برای استان انتخاب شده است."

        return True, city

    @classmethod
    def validate_user_data(cls, user_data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate complete user registration data"""
        errors = []

        # Validate required fields
        required_fields = {
            "first_name": "نام",
            "last_name": "نام خانوادگی",
            "grade": "پایه تحصیلی",
            "major": "رشته تحصیلی",
            "province": "استان",
            "city": "شهر",
            "phone": "شماره تلفن",
        }

        for field, field_name in required_fields.items():
            if field not in user_data or not user_data[field]:
                errors.append(f"{field_name} الزامی است.")

        # Validate individual fields if they exist
        if "first_name" in user_data and user_data["first_name"]:
            is_valid, error = cls.validate_name(user_data["first_name"], "نام")
            if not is_valid:
                errors.append(error)

        if "last_name" in user_data and user_data["last_name"]:
            is_valid, error = cls.validate_name(user_data["last_name"], "نام خانوادگی")
            if not is_valid:
                errors.append(error)

        if "phone" in user_data and user_data["phone"]:
            is_valid, error = cls.validate_phone(user_data["phone"])
            if not is_valid:
                errors.append(error)

        if "grade" in user_data and user_data["grade"]:
            is_valid, error = cls.validate_grade(user_data["grade"])
            if not is_valid:
                errors.append(error)

        if "major" in user_data and user_data["major"]:
            is_valid, error = cls.validate_major(user_data["major"])
            if not is_valid:
                errors.append(error)

        if "province" in user_data and user_data["province"]:
            is_valid, error = cls.validate_province(user_data["province"])
            if not is_valid:
                errors.append(error)

        if "city" in user_data and user_data["city"] and "province" in user_data:
            is_valid, error = cls.validate_city(user_data["city"], user_data["province"])
            if not is_valid:
                errors.append(error)

        return len(errors) == 0, errors

    @staticmethod
    def normalize_phone(phone: str) -> str:
        """Normalize phone number to standard format"""
        phone = re.sub(r"[\s\-]", "", phone)
        if phone.startswith("+98"):
            return phone
        elif phone.startswith("09"):
            return "+98" + phone[1:]
        elif phone.startswith("9"):
            return "+98" + phone
        elif phone.startswith("0"):
            return "+98" + phone[1:]
        else:
            return phone

    @classmethod
    def validate_file_upload(cls, file_info: Dict[str, Any]) -> tuple[bool, str]:
        """Validate file uploads"""
        if not file_info:
            return False, "فایل یافت نشد."

        # Check file size
        file_size_mb = file_info.get("file_size", 0) / (1024 * 1024)
        if file_size_mb > config.security.max_file_size_mb:
            return (
                False,
                f"حجم فایل نمی‌تواند بیشتر از {config.security.max_file_size_mb} مگابایت باشد.",
            )

        # Check file type
        file_name = file_info.get("file_name", "")
        file_extension = file_name.split(".")[-1].lower() if "." in file_name else ""

        if file_extension not in config.security.allowed_file_types:
            return (
                False,
                f"نوع فایل مجاز نیست. فایل‌های مجاز: {', '.join(config.security.allowed_file_types)}",
            )

        return True, "فایل معتبر است."

    @staticmethod
    def format_card_number(card: str) -> str:
        """Return card number grouped in blocks of 4 digits with spaces.

        Non-digits are stripped first; if formatting fails, original string is returned.
        """
        if not card:
            return ""
        import re

        digits = re.sub(r"\D+", "", str(card))
        if len(digits) < 12:
            return card
        groups = [digits[i : i + 4] for i in range(0, len(digits), 4)]
        return " ".join(groups)
