#!/usr/bin/env python3
"""
Comprehensive tests for utils/security.py to achieve 100% coverage
"""

import pytest
import re
import hashlib
import hmac
import base64
import secrets
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from utils.security import SecurityUtils
from config import config


class TestSecurityUtils:
    """Test SecurityUtils class for 100% coverage"""

    def test_sanitize_input_empty_input(self):
        """Test sanitize_input with empty/None input"""
        assert SecurityUtils.sanitize_input("") == ""
        assert SecurityUtils.sanitize_input(None) == ""
        assert SecurityUtils.sanitize_input(0) == ""  # 0 is falsy, so returns empty string

    def test_sanitize_input_basic_sanitization(self):
        """Test basic input sanitization"""
        # Test null bytes removal
        assert SecurityUtils.sanitize_input("test\x00string") == "teststring"

        # Test control characters removal
        assert SecurityUtils.sanitize_input("test\x01\x02\x03string") == "teststring"

        # Test whitespace trimming
        assert SecurityUtils.sanitize_input("  test  ") == "test"

    def test_sanitize_input_sql_injection_patterns(self):
        """Test SQL injection pattern removal"""
        malicious_input = "SELECT * FROM users; DROP TABLE users; -- comment"
        sanitized = SecurityUtils.sanitize_input(malicious_input)

        # Should remove SQL keywords and comments
        assert "SELECT" not in sanitized
        assert "DROP" not in sanitized
        assert "--" not in sanitized
        assert "FROM users" in sanitized  # Should remain

    def test_sanitize_input_xss_patterns(self):
        """Test XSS pattern removal"""
        malicious_input = "<script>alert('xss')</script>javascript:void(0)"
        sanitized = SecurityUtils.sanitize_input(malicious_input)

        assert "<script" not in sanitized
        assert "javascript:" not in sanitized
        assert "alert('xss')" in sanitized  # Should remain

    def test_sanitize_input_path_traversal_patterns(self):
        """Test path traversal pattern removal"""
        malicious_input = "../../../etc/passwd c:\\windows\\system32"
        sanitized = SecurityUtils.sanitize_input(malicious_input)

        assert "../" not in sanitized
        assert "c:\\" not in sanitized
        assert "etc/passwd" in sanitized  # Should remain

    def test_sanitize_input_command_injection_patterns(self):
        """Test command injection pattern removal"""
        malicious_input = "cmd /c dir; powershell Get-Process | bash"
        sanitized = SecurityUtils.sanitize_input(malicious_input)

        assert "cmd" not in sanitized
        assert "powershell" not in sanitized
        assert "bash" not in sanitized
        assert "dir" in sanitized  # Should remain

    def test_sanitize_input_length_limit(self):
        """Test length limiting functionality"""
        long_input = "a" * 100
        sanitized = SecurityUtils.sanitize_input(long_input, max_length=50)
        assert len(sanitized) == 50
        assert sanitized == "a" * 50

    def test_validate_filename_valid(self):
        """Test filename validation with valid names"""
        valid_names = ["document.pdf", "image_123.jpg", "file-name.txt", "a" * 255]  # Max length

        for name in valid_names:
            assert SecurityUtils.validate_filename(name) is True

    def test_validate_filename_invalid(self):
        """Test filename validation with invalid names"""
        invalid_names = [
            "",  # Empty
            None,  # None
            "file<name.txt",  # Dangerous character
            "file:name.txt",  # Dangerous character
            "file|name.txt",  # Dangerous character
            "file?name.txt",  # Dangerous character
            "file*name.txt",  # Dangerous character
            "file\\name.txt",  # Dangerous character
            "file/name.txt",  # Dangerous character
            "file..name.txt",  # Path traversal
            "a" * 256,  # Too long
        ]

        for name in invalid_names:
            assert SecurityUtils.validate_filename(name) is False

    def test_generate_secure_token(self):
        """Test secure token generation"""
        token1 = SecurityUtils.generate_secure_token(16)
        token2 = SecurityUtils.generate_secure_token(32)

        assert len(token1) > 0
        assert len(token2) > 0
        assert token1 != token2  # Should be different each time
        assert isinstance(token1, str)
        assert isinstance(token2, str)

    def test_hash_password_without_salt(self):
        """Test password hashing without providing salt"""
        password = "testpassword123"
        hashed, salt = SecurityUtils.hash_password(password)

        assert isinstance(hashed, str)
        assert isinstance(salt, str)
        assert len(salt) == 32  # 16 bytes hex encoded
        assert hashed != password

    def test_hash_password_with_salt(self):
        """Test password hashing with provided salt"""
        password = "testpassword123"
        custom_salt = "custom_salt_123"
        hashed, salt = SecurityUtils.hash_password(password, custom_salt)

        assert hashed != password
        assert salt == custom_salt

    def test_verify_password_success(self):
        """Test successful password verification"""
        password = "testpassword123"
        hashed, salt = SecurityUtils.hash_password(password)

        assert SecurityUtils.verify_password(password, hashed, salt) is True

    def test_verify_password_failure(self):
        """Test failed password verification"""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed, salt = SecurityUtils.hash_password(password)

        assert SecurityUtils.verify_password(wrong_password, hashed, salt) is False

    def test_verify_password_exception_handling(self):
        """Test password verification with exception handling"""
        # Mock hash_password to raise an exception
        with patch.object(SecurityUtils, 'hash_password', side_effect=Exception("Test error")):
            result = SecurityUtils.verify_password("password", "hash", "salt")
            assert result is False

    def test_generate_hmac(self):
        """Test HMAC generation"""
        data = "test data"
        secret = "secret_key"
        hmac_result = SecurityUtils.generate_hmac(data, secret)

        assert isinstance(hmac_result, str)
        assert len(hmac_result) == 64  # SHA256 hex digest length

    def test_verify_hmac_success(self):
        """Test successful HMAC verification"""
        data = "test data"
        secret = "secret_key"
        signature = SecurityUtils.generate_hmac(data, secret)

        assert SecurityUtils.verify_hmac(data, signature, secret) is True

    def test_verify_hmac_failure(self):
        """Test failed HMAC verification"""
        data = "test data"
        secret = "secret_key"
        wrong_signature = "wrong_signature"

        assert SecurityUtils.verify_hmac(data, wrong_signature, secret) is False

    def test_rate_limit_key(self):
        """Test rate limit key generation"""
        user_id = 12345
        action = "login"
        key = SecurityUtils.rate_limit_key(user_id, action)

        assert key == "rate_limit:12345:login"
        assert isinstance(key, str)

    def test_validate_json_structure_valid(self):
        """Test JSON structure validation with valid data"""
        data = {"name": "test", "age": 25, "email": "test@example.com"}
        required_fields = ["name", "age"]

        assert SecurityUtils.validate_json_structure(data, required_fields) is True

    def test_validate_json_structure_invalid(self):
        """Test JSON structure validation with invalid data"""
        # Missing required field
        data = {"name": "test", "age": 25}
        required_fields = ["name", "age", "email"]

        assert SecurityUtils.validate_json_structure(data, required_fields) is False

    def test_validate_json_structure_not_dict(self):
        """Test JSON structure validation with non-dict data"""
        data = "not a dict"
        required_fields = ["name"]

        assert SecurityUtils.validate_json_structure(data, required_fields) is False

    def test_sanitize_json_string(self):
        """Test JSON sanitization with string data"""
        malicious_string = "<script>alert('xss')</script>"
        sanitized = SecurityUtils.sanitize_json(malicious_string)

        assert "<script" not in sanitized
        assert "alert('xss')" in sanitized

    def test_sanitize_json_dict(self):
        """Test JSON sanitization with dictionary data"""
        data = {"name": "<script>alert('xss')</script>", "description": "normal text"}
        sanitized = SecurityUtils.sanitize_json(data)

        assert "<script" not in sanitized["name"]
        assert sanitized["description"] == "normal text"

    def test_sanitize_json_list(self):
        """Test JSON sanitization with list data"""
        data = [
            "<script>alert('xss')</script>",
            "normal text",
            {"nested": "<iframe>malicious</iframe>"},
        ]
        sanitized = SecurityUtils.sanitize_json(data)

        assert "<script" not in sanitized[0]
        assert sanitized[1] == "normal text"
        assert "<iframe" not in sanitized[2]["nested"]

    def test_sanitize_json_other_types(self):
        """Test JSON sanitization with other data types"""
        data = 123
        sanitized = SecurityUtils.sanitize_json(data)
        assert sanitized == 123

    def test_validate_phone_number_valid(self):
        """Test phone number validation with valid numbers"""
        valid_numbers = [
            "1234567890",
            "+12345678901",
            "123-456-7890",
            "(123) 456-7890",
            "123.456.7890",
        ]

        for phone in valid_numbers:
            assert SecurityUtils.validate_phone_number(phone) is True

    def test_validate_phone_number_invalid(self):
        """Test phone number validation with invalid numbers"""
        invalid_numbers = [
            "",  # Empty
            None,  # None
            "123",  # Too short
            "12345678901234567890",  # Too long
            "0000000000",  # Too many leading zeros
            "1111111111",  # Too many ones
            "9999999999",  # Too many nines
            "123456666666",  # Too many repeated digits
        ]

        for phone in invalid_numbers:
            assert SecurityUtils.validate_phone_number(phone) is False

    def test_validate_email_valid(self):
        """Test email validation with valid emails"""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.org",
            "123@456.com",
        ]

        for email in valid_emails:
            assert SecurityUtils.validate_email(email) is True

    def test_validate_email_invalid(self):
        """Test email validation with invalid emails"""
        invalid_emails = [
            "",  # Empty
            None,  # None
            "invalid-email",  # No @ symbol
            "@example.com",  # No local part
            "user@",  # No domain
            "user..name@example.com",  # Double dots
            "user.@example.com",  # Dot immediately before @
            "user@.example.com",  # @ before dot
            "user@example..com",  # Multiple consecutive dots
            "user<tag>@example.com",  # HTML tags
            "a" * 255 + "@example.com",  # Too long
        ]

        for email in invalid_emails:
            assert SecurityUtils.validate_email(email) is False

    @patch('utils.security.config')
    def test_create_secure_session_token(self, mock_config):
        """Test secure session token creation"""
        mock_config.bot_token = "test_bot_token"
        user_id = 12345
        expires_in_hours = 24

        token = SecurityUtils.create_secure_session_token(user_id, expires_in_hours)

        assert isinstance(token, str)
        assert len(token) > 0

        # Decode and verify structure
        decoded = base64.urlsafe_b64decode(token.encode()).decode()
        parts = decoded.split(":")
        assert len(parts) == 3
        assert parts[0] == str(user_id)

    @patch('utils.security.config')
    def test_verify_session_token_valid(self, mock_config):
        """Test valid session token verification"""
        mock_config.bot_token = "test_bot_token"
        user_id = 12345

        # Create a token
        token = SecurityUtils.create_secure_session_token(user_id, 24)

        # Verify it
        result = SecurityUtils.verify_session_token(token)
        assert result == user_id

    def test_verify_session_token_invalid_format(self):
        """Test session token verification with invalid format"""
        # Token with wrong number of parts
        invalid_token = base64.urlsafe_b64encode("invalid:format".encode()).decode()

        result = SecurityUtils.verify_session_token(invalid_token)
        assert result is None

    @patch('utils.security.config')
    def test_verify_session_token_expired(self, mock_config):
        """Test session token verification with expired token"""
        mock_config.bot_token = "test_bot_token"
        # Create a token that expired 1 hour ago
        timestamp = (datetime.utcnow() - timedelta(hours=1)).timestamp()
        token_data = f"12345:{timestamp}"
        signature = SecurityUtils.generate_hmac(token_data, "test_bot_token")
        full_token_data = f"{token_data}:{signature}"
        token = base64.urlsafe_b64encode(full_token_data.encode()).decode()

        result = SecurityUtils.verify_session_token(token)
        assert result is None

    @patch('utils.security.config')
    def test_verify_session_token_invalid_signature(self, mock_config):
        """Test session token verification with invalid signature"""
        mock_config.bot_token = "test_bot_token"
        # Create a token with a signature that doesn't match the expected HMAC
        timestamp = (datetime.utcnow() + timedelta(hours=1)).timestamp()
        token_data = f"12345:{timestamp}"
        # Generate HMAC with wrong secret
        wrong_signature = SecurityUtils.generate_hmac(token_data, "wrong_secret")
        full_token_data = f"{token_data}:{wrong_signature}"
        token = base64.urlsafe_b64encode(full_token_data.encode()).decode()

        result = SecurityUtils.verify_session_token(token)
        assert result is None

    def test_verify_session_token_exception_handling(self):
        """Test session token verification with exception handling"""
        # Invalid base64
        result = SecurityUtils.verify_session_token("invalid_base64!")
        assert result is None

    @patch('utils.security.logger')
    def test_log_security_event(self, mock_logger):
        """Test security event logging"""
        event_type = "login_attempt"
        user_id = 12345
        details = {"ip": "192.168.1.1", "user_agent": "test"}

        SecurityUtils.log_security_event(event_type, user_id, details)

        mock_logger.warning.assert_called_once()
        log_call = mock_logger.warning.call_args[0][0]
        assert "Security event:" in log_call
        assert event_type in log_call

    @patch('utils.security.logger')
    def test_log_security_event_no_details(self, mock_logger):
        """Test security event logging without details"""
        event_type = "logout"
        user_id = 12345

        SecurityUtils.log_security_event(event_type, user_id)

        mock_logger.warning.assert_called_once()

    @patch('utils.security.logger')
    def test_log_security_event_no_user_id(self, mock_logger):
        """Test security event logging without user_id"""
        event_type = "system_alert"
        details = {"message": "test alert"}

        SecurityUtils.log_security_event(event_type, details=details)

        mock_logger.warning.assert_called_once()

    def test_check_suspicious_activity(self):
        """Test suspicious activity checking"""
        user_id = 12345
        action = "login"
        context = {"ip": "192.168.1.1"}

        # Current implementation always returns False
        result = SecurityUtils.check_suspicious_activity(user_id, action, context)
        assert result is False

    def test_security_patterns_compilation(self):
        """Test that security patterns are properly compiled"""
        # Test SQL injection patterns
        assert len(SecurityUtils._sql_injection_patterns) == 3
        for pattern in SecurityUtils._sql_injection_patterns:
            assert isinstance(pattern, re.Pattern)

        # Test XSS patterns
        assert len(SecurityUtils._xss_patterns) == 3
        for pattern in SecurityUtils._xss_patterns:
            assert isinstance(pattern, re.Pattern)

        # Test path traversal patterns
        assert len(SecurityUtils._path_traversal_patterns) == 3
        for pattern in SecurityUtils._path_traversal_patterns:
            assert isinstance(pattern, re.Pattern)

        # Test command injection patterns
        assert len(SecurityUtils._command_injection_patterns) == 3
        for pattern in SecurityUtils._command_injection_patterns:
            assert isinstance(pattern, re.Pattern)

    def test_hash_password_imports(self):
        """Test that hash_password properly imports required modules"""
        # This test ensures the import statements work correctly
        password = "test"
        hashed, salt = SecurityUtils.hash_password(password)
        assert isinstance(hashed, str)
        assert isinstance(salt, str)

    def test_edge_cases_sanitize_input(self):
        """Test edge cases for sanitize_input"""
        # Test with very long input
        long_input = "a" * 10000
        sanitized = SecurityUtils.sanitize_input(long_input, max_length=100)
        assert len(sanitized) == 100

        # Test with mixed malicious content
        mixed_input = "normal<script>alert('xss')</script>text; DROP TABLE users; --"
        sanitized = SecurityUtils.sanitize_input(mixed_input)
        assert "<script" not in sanitized
        assert "DROP" not in sanitized
        assert "--" not in sanitized
        assert "normal" in sanitized
        assert "text" in sanitized

    def test_edge_cases_validate_phone_number(self):
        """Test edge cases for phone number validation"""
        # Test with various separators
        phone_with_separators = "+1 (234) 567-8901 ext. 123"
        assert SecurityUtils.validate_phone_number(phone_with_separators) is True

        # Test with international format
        international_phone = "+44 20 7946 0958"
        assert SecurityUtils.validate_phone_number(international_phone) is True

    def test_edge_cases_validate_email(self):
        """Test edge cases for email validation"""
        # Test with subdomains
        subdomain_email = "user@sub.domain.example.com"
        assert SecurityUtils.validate_email(subdomain_email) is True

        # Test with numbers in domain
        numeric_domain = "user@domain123.com"
        assert SecurityUtils.validate_email(numeric_domain) is True
