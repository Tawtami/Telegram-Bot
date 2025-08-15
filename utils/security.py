#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Security utilities for Ostad Hatami Bot
"""

import re
import hashlib
import hmac
import base64
import secrets
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from config import config

logger = logging.getLogger(__name__)


class SecurityUtils:
    """Security utilities for input validation and sanitization"""

    # Security patterns
    _sql_injection_patterns = [
        re.compile(
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b)",
            re.IGNORECASE,
        ),
        re.compile(r"(--|/\*|\*/|xp_|sp_)", re.IGNORECASE),
        re.compile(r"(\b(OR|AND)\b\s+\d+\s*=\s*\d+)", re.IGNORECASE),
    ]

    _xss_patterns = [
        re.compile(r"(<script|javascript:|vbscript:|onload=|onerror=|onclick=)", re.IGNORECASE),
        re.compile(r"(<iframe|<object|<embed)", re.IGNORECASE),
        re.compile(r"(data:text/html|data:application/x-javascript)", re.IGNORECASE),
    ]

    _path_traversal_patterns = [
        re.compile(r"(\.\./|\.\.\\)"),
        re.compile(r"(/etc/|/var/|/tmp/|/home/)"),
        re.compile(r"(c:\\|d:\\)", re.IGNORECASE),
    ]

    _command_injection_patterns = [
        re.compile(r"(\b(cmd|powershell|bash|sh|python|perl|ruby)\b)", re.IGNORECASE),
        re.compile(r"(\||&|;|`|\$\(|\$\{)", re.IGNORECASE),
        re.compile(r"(eval\(|exec\(|system\(|subprocess\.)", re.IGNORECASE),
    ]

    @classmethod
    def sanitize_input(cls, text: str, max_length: Optional[int] = None) -> str:
        """Sanitize user input to prevent various attacks"""
        if not text:
            return ""

        # Convert to string
        text = str(text)

        # Remove null bytes
        text = text.replace("\x00", "")

        # Remove control characters except newlines and tabs
        text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)

        # Remove XSS patterns completely but preserve surrounding safe text
        # Strip <script>..</script> blocks FIRST (before SQL patterns) so inner content is removed too
        text = re.sub(
            r"<\s*script[^>]*>.*?<\s*/\s*script\s*>", "", text, flags=re.IGNORECASE | re.DOTALL
        )
        text = re.sub(r"javascript:\s*[^\s]+", "", text, flags=re.IGNORECASE)
        text = re.sub(r"vbscript:\s*[^\s]+", "", text, flags=re.IGNORECASE)
        # Also strip orphan script tags if present
        text = text.replace("<script>", "").replace("</script>", "")
        # Then apply additional dangerous tag/protocol filters
        for pattern in cls._xss_patterns:
            text = pattern.sub("", text)

        # Remove SQL injection patterns completely (after XSS removal)
        for pattern in cls._sql_injection_patterns:
            text = pattern.sub("", text)

        # Remove path traversal patterns completely
        for pattern in cls._path_traversal_patterns:
            text = pattern.sub("", text)

        # Remove command separators first
        text = re.sub(r"[|&;`]+|\$\(|\$\{", "", text)
        # Remove common shell command invocations but retain plain words
        text = re.sub(
            r"\b(cat|ls|dir|rm|del|powershell|bash|sh|python|perl|ruby)\b",
            "",
            text,
            flags=re.IGNORECASE,
        )

        # Clean up any leftover empty angle brackets produced by prior substitutions
        text = text.replace("<>", "").replace("</>", "")

        # Trim whitespace
        text = text.strip()

        # Apply length limit
        if max_length and len(text) > max_length:
            text = text[:max_length]

        return text

    @classmethod
    def validate_filename(cls, filename: str) -> bool:
        """Validate filename for security"""
        if not filename:
            return False

        # Check for dangerous characters
        dangerous_chars = ["<", ">", ":", '"', "|", "?", "*", "\\", "/"]
        if any(char in filename for char in dangerous_chars):
            return False

        # Check for path traversal
        if ".." in filename:
            return False

        # Check length
        if len(filename) > 255:
            return False

        return True

    @classmethod
    def generate_secure_token(cls, length: int = 32) -> str:
        """Generate a secure random token"""
        # Generate a token composed of urlsafe characters only. Ensure deterministic length.
        # token_urlsafe returns ~1.33 * n length; tests expect exact length.
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
        return "".join(secrets.choice(alphabet) for _ in range(length))

    @classmethod
    def hash_password(cls, password: str, salt: Optional[str] = None) -> tuple[str, str]:
        """Hash password with salt"""
        if salt is None:
            salt = secrets.token_hex(16)

        # Use PBKDF2 for password hashing
        import hashlib
        import os

        # Generate hash using PBKDF2
        hash_obj = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            100000,  # iterations
        )

        return base64.b64encode(hash_obj).decode("utf-8"), salt

    @classmethod
    def verify_password(cls, password: str, hashed_password: str, salt: str) -> bool:
        """Verify password against hash"""
        try:
            computed_hash, _ = cls.hash_password(password, salt)
            return hmac.compare_digest(computed_hash, hashed_password)
        except Exception:
            return False

    @classmethod
    def generate_hmac(cls, data: str, secret: str) -> str:
        """Generate HMAC for data integrity"""
        return hmac.new(secret.encode("utf-8"), data.encode("utf-8"), hashlib.sha256).hexdigest()

    @classmethod
    def verify_hmac(cls, data: str, signature: str, secret: str) -> bool:
        """Verify HMAC signature"""
        expected_signature = cls.generate_hmac(data, secret)
        return hmac.compare_digest(expected_signature, signature)

    @classmethod
    def rate_limit_key(cls, user_id: int, action: str) -> str:
        """Generate rate limit key for user and action"""
        return f"rate_limit:{user_id}:{action}"

    @classmethod
    def validate_json_structure(cls, data: Dict[str, Any], required_fields: List[str]) -> bool:
        """Validate JSON structure for required fields"""
        if not isinstance(data, dict):
            return False

        return all(field in data for field in required_fields)

    @classmethod
    def sanitize_json(cls, data: Any) -> Any:
        """Recursively sanitize JSON data"""
        if isinstance(data, str):
            return cls.sanitize_input(data)
        elif isinstance(data, dict):
            return {key: cls.sanitize_json(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [cls.sanitize_json(item) for item in data]
        else:
            return data

    @classmethod
    def validate_phone_number(cls, phone: str) -> bool:
        """Enhanced phone number validation with security checks"""
        if not phone:
            return False

        # Remove all non-digit characters
        digits_only = re.sub(r"\D", "", phone)

        # Check for reasonable length
        if len(digits_only) < 10 or len(digits_only) > 15:
            return False

        # Check for suspicious patterns
        suspicious_patterns = [
            r"^0{5,}",  # Too many leading zeros
            r"^1{5,}",  # Too many ones
            r"^9{5,}",  # Too many nines
            r"(\d)\1{5,}",  # Too many repeated digits
        ]

        for pattern in suspicious_patterns:
            if re.search(pattern, digits_only):
                return False

        return True

    @classmethod
    def validate_email(cls, email: str) -> bool:
        """Enhanced email validation with security checks"""
        if not email:
            return False

        # Basic email pattern
        email_pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
        if not email_pattern.match(email):
            return False

        # Check for suspicious patterns
        suspicious_patterns = [
            r"\.\.",  # Double dots
            r"\.@",  # Dot before @
            r"@\.",  # @ before dot
            r"\.{2,}",  # Multiple consecutive dots
            r'[<>"\']',  # HTML tags or quotes
        ]

        for pattern in suspicious_patterns:
            if re.search(pattern, email):
                return False

        # Check length
        if len(email) > 254:  # RFC 5321 limit
            return False

        return True

    @classmethod
    def create_secure_session_token(cls, user_id: int, expires_in_hours: int = 24) -> str:
        """Create a secure session token"""
        timestamp = datetime.utcnow().timestamp()
        expires_at = timestamp + (expires_in_hours * 3600)

        # Create token data (integer seconds to avoid microsecond drift in tests)
        token_data = f"{user_id}:{int(expires_at)}"

        # Generate HMAC signature
        signature = cls.generate_hmac(token_data, config.bot_token)

        # Combine data and signature
        full_token = f"{token_data}:{signature}"

        return base64.urlsafe_b64encode(full_token.encode()).decode()

    @classmethod
    def verify_session_token(cls, token: str) -> Optional[int]:
        """Verify session token and return user ID if valid"""
        try:
            # Decode token
            decoded = base64.urlsafe_b64decode(token.encode()).decode()

            # Split into parts
            parts = decoded.split(":")
            if len(parts) != 3:
                return None

            user_id_str, expires_at_str, signature = parts

            # Verify signature
            token_data = f"{user_id_str}:{expires_at_str}"
            if not cls.verify_hmac(token_data, signature, config.bot_token):
                return None

            # Check expiration
            expires_at = float(expires_at_str)
            # Allow slight clock skew tolerance of 1 second in tests
            if datetime.utcnow().timestamp() > (expires_at + 1.0):
                return None

            return int(user_id_str)

        except Exception:
            return None

    @classmethod
    def log_security_event(
        cls,
        event_type: str,
        user_id: Optional[int] = None,
        details: Optional[Dict] = None,
    ):
        """Log security events"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "details": details or {},
        }

        logger.warning(f"Security event: {log_data}")

    @classmethod
    def check_suspicious_activity(cls, user_id: int, action: str, context: Dict[str, Any]) -> bool:
        """Check for suspicious user activity"""
        # This is a basic implementation - could be enhanced with ML or more sophisticated rules

        suspicious_patterns = [
            # Rapid repeated actions
            {"pattern": "rapid_requests", "threshold": 10, "window": 60},
            # Unusual input patterns
            {"pattern": "long_inputs", "threshold": 1000, "field": "text_length"},
            # Geographic anomalies (if location data available)
            {"pattern": "location_mismatch", "field": "location"},
        ]

        # For now, return False (not suspicious)
        # In a real implementation, you would check against user history and patterns
        return False
