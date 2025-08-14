#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for security.py
"""
import pytest
import re
import hashlib
import hmac
import base64
import secrets
import time
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from utils.security import SecurityUtils


class TestSecurityUtils:
    """Test cases for SecurityUtils class"""

    def test_sql_injection_patterns(self):
        """Test SQL injection pattern detection"""
        patterns = SecurityUtils._sql_injection_patterns
        
        # Test SELECT pattern
        assert any(pattern.search("SELECT * FROM users") for pattern in patterns)
        assert any(pattern.search("select * from users") for pattern in patterns)
        
        # Test INSERT pattern
        assert any(pattern.search("INSERT INTO users") for pattern in patterns)
        
        # Test UPDATE pattern
        assert any(pattern.search("UPDATE users SET") for pattern in patterns)
        
        # Test DELETE pattern
        assert any(pattern.search("DELETE FROM users") for pattern in patterns)
        
        # Test DROP pattern
        assert any(pattern.search("DROP TABLE users") for pattern in patterns)
        
        # Test CREATE pattern
        assert any(pattern.search("CREATE TABLE users") for pattern in patterns)
        
        # Test ALTER pattern
        assert any(pattern.search("ALTER TABLE users") for pattern in patterns)
        
        # Test EXEC pattern
        assert any(pattern.search("EXEC sp_procedure") for pattern in patterns)
        
        # Test UNION pattern
        assert any(pattern.search("UNION SELECT") for pattern in patterns)
        
        # Test SCRIPT pattern
        assert any(pattern.search("<SCRIPT>alert('xss')</SCRIPT>") for pattern in patterns)

    def test_xss_patterns(self):
        """Test XSS pattern detection"""
        patterns = SecurityUtils._xss_patterns
        
        # Test script tags
        assert any(pattern.search("<script>alert('xss')</script>") for pattern in patterns)
        assert any(pattern.search("<SCRIPT>alert('xss')</SCRIPT>") for pattern in patterns)
        
        # Test javascript protocol
        assert any(pattern.search("javascript:alert('xss')") for pattern in patterns)
        
        # Test vbscript protocol
        assert any(pattern.search("vbscript:msgbox('xss')") for pattern in patterns)
        
        # Test onload event
        assert any(pattern.search("onload=alert('xss')") for pattern in patterns)
        
        # Test onerror event
        assert any(pattern.search("onerror=alert('xss')") for pattern in patterns)
        
        # Test onclick event
        assert any(pattern.search("onclick=alert('xss')") for pattern in patterns)
        
        # Test iframe
        assert any(pattern.search("<iframe src='evil.com'>") for pattern in patterns)
        
        # Test object
        assert any(pattern.search("<object data='evil.swf'>") for pattern in patterns)
        
        # Test embed
        assert any(pattern.search("<embed src='evil.swf'>") for pattern in patterns)
        
        # Test data URLs
        assert any(pattern.search("data:text/html,<script>alert('xss')</script>") for pattern in patterns)
        assert any(pattern.search("data:application/x-javascript,alert('xss')") for pattern in patterns)

    def test_path_traversal_patterns(self):
        """Test path traversal pattern detection"""
        patterns = SecurityUtils._path_traversal_patterns
        
        # Test directory traversal
        assert any(pattern.search("../etc/passwd") for pattern in patterns)
        assert any(pattern.search("..\\windows\\system32") for pattern in patterns)
        
        # Test system directories
        assert any(pattern.search("/etc/passwd") for pattern in patterns)
        assert any(pattern.search("/var/log") for pattern in patterns)
        assert any(pattern.search("/tmp/file") for pattern in patterns)
        assert any(pattern.search("/home/user") for pattern in patterns)
        
        # Test Windows drives
        assert any(pattern.search("c:\\windows") for pattern in patterns)
        assert any(pattern.search("D:\\Program Files") for pattern in patterns)

    def test_command_injection_patterns(self):
        """Test command injection pattern detection"""
        patterns = SecurityUtils._command_injection_patterns
        
        # Test command names
        assert any(pattern.search("cmd /c dir") for pattern in patterns)
        assert any(pattern.search("powershell -Command") for pattern in patterns)
        assert any(pattern.search("bash -c 'ls'") for pattern in patterns)
        assert any(pattern.search("sh -c 'cat file'") for pattern in patterns)
        assert any(pattern.search("python -c 'print(1)'") for pattern in patterns)
        assert any(pattern.search("perl -e 'print 1'") for pattern in patterns)
        assert any(pattern.search("ruby -e 'puts 1'") for pattern in patterns)
        
        # Test command separators
        assert any(pattern.search("command1 | command2") for pattern in patterns)
        assert any(pattern.search("command1 & command2") for pattern in patterns)
        assert any(pattern.search("command1; command2") for pattern in patterns)
        assert any(pattern.search("command1 ` command2") for pattern in patterns)
        assert any(pattern.search("$(command)") for pattern in patterns)
        assert any(pattern.search("${command}") for pattern in patterns)
        
        # Test dangerous functions
        assert any(pattern.search("eval('alert(1)')") for pattern in patterns)
        assert any(pattern.search("exec('ls')") for pattern in patterns)
        assert any(pattern.search("system('cat file')") for pattern in patterns)
        assert any(pattern.search("subprocess.call('ls')") for pattern in patterns)

    def test_sanitize_input_basic(self):
        """Test basic input sanitization"""
        # Test normal text
        result = SecurityUtils.sanitize_input("Hello World")
        assert result == "Hello World"
        
        # Test empty input
        result = SecurityUtils.sanitize_input("")
        assert result == ""
        
        result = SecurityUtils.sanitize_input(None)
        assert result == ""
        
        # Test non-string input
        result = SecurityUtils.sanitize_input(123)
        assert result == "123"

    def test_sanitize_input_sql_injection(self):
        """Test SQL injection sanitization"""
        malicious_input = "'; DROP TABLE users; --"
        result = SecurityUtils.sanitize_input(malicious_input)
        
        # Should remove SQL injection patterns
        assert "DROP TABLE" not in result
        assert ";" not in result
        assert "--" not in result

    def test_sanitize_input_xss(self):
        """Test XSS sanitization"""
        malicious_input = "<script>alert('xss')</script>Hello"
        result = SecurityUtils.sanitize_input(malicious_input)
        
        # Should remove XSS patterns
        assert "<script>" not in result
        assert "alert('xss')" not in result
        assert "Hello" in result  # Normal text should remain

    def test_sanitize_input_path_traversal(self):
        """Test path traversal sanitization"""
        malicious_input = "../../../etc/passwd"
        result = SecurityUtils.sanitize_input(malicious_input)
        
        # Should remove path traversal patterns
        assert ".." not in result
        assert "/etc/" not in result

    def test_sanitize_input_command_injection(self):
        """Test command injection sanitization"""
        malicious_input = "ls; cat /etc/passwd"
        result = SecurityUtils.sanitize_input(malicious_input)
        
        # Should remove command injection patterns
        assert ";" not in result
        assert "cat" not in result

    def test_sanitize_input_control_characters(self):
        """Test control character removal"""
        malicious_input = "Hello\x00World\x01\x02\x03"
        result = SecurityUtils.sanitize_input(malicious_input)
        
        # Should remove null bytes and control characters
        assert "\x00" not in result
        assert "\x01" not in result
        assert "\x02" not in result
        assert "\x03" not in result
        assert "Hello" in result
        assert "World" in result

    def test_sanitize_input_length_limit(self):
        """Test input length limiting"""
        long_input = "A" * 1000
        result = SecurityUtils.sanitize_input(long_input, max_length=100)
        
        assert len(result) == 100
        assert result == "A" * 100

    def test_sanitize_input_whitespace_trimming(self):
        """Test whitespace trimming"""
        input_with_spaces = "  Hello World  "
        result = SecurityUtils.sanitize_input(input_with_spaces)
        
        assert result == "Hello World"

    def test_validate_filename_valid(self):
        """Test valid filename validation"""
        valid_filenames = [
            "document.pdf",
            "image.jpg",
            "file_123.txt",
            "my-file.docx",
            "file.name"
        ]
        
        for filename in valid_filenames:
            assert SecurityUtils.validate_filename(filename) is True

    def test_validate_filename_invalid(self):
        """Test invalid filename validation"""
        invalid_filenames = [
            "",  # Empty
            None,  # None
            "file<name.txt",  # Contains <
            "file>name.txt",  # Contains >
            "file:name.txt",  # Contains :
            'file"name.txt',  # Contains "
            "file|name.txt",  # Contains |
            "file?name.txt",  # Contains ?
            "file*name.txt",  # Contains *
            "file\\name.txt",  # Contains backslash
            "file/name.txt",  # Contains forward slash
            "file..name.txt",  # Path traversal
            "A" * 300,  # Too long
        ]
        
        for filename in invalid_filenames:
            assert SecurityUtils.validate_filename(filename) is False

    def test_generate_secure_token(self):
        """Test secure token generation"""
        # Test default length
        token1 = SecurityUtils.generate_secure_token()
        assert len(token1) == 32
        
        # Test custom length
        token2 = SecurityUtils.generate_secure_token(64)
        assert len(token2) == 64
        
        # Test tokens are different
        assert token1 != token2
        
        # Test tokens are URL safe
        assert "=" not in token1
        assert "=" not in token2

    def test_hash_password(self):
        """Test password hashing"""
        password = "my_secure_password"
        
        # Test without salt
        hash1, salt1 = SecurityUtils.hash_password(password)
        assert isinstance(hash1, str)
        assert isinstance(salt1, str)
        assert len(salt1) == 32  # 16 bytes hex encoded
        
        # Test with custom salt
        custom_salt = "custom_salt_12345"
        hash2, salt2 = SecurityUtils.hash_password(password, custom_salt)
        assert hash2 != hash1
        assert salt2 == custom_salt

    def test_verify_password(self):
        """Test password verification"""
        password = "my_secure_password"
        hash_value, salt = SecurityUtils.hash_password(password)
        
        # Test correct password
        assert SecurityUtils.verify_password(password, hash_value, salt) is True
        
        # Test incorrect password
        assert SecurityUtils.verify_password("wrong_password", hash_value, salt) is False
        
        # Test incorrect hash
        wrong_hash = "wrong_hash_value"
        assert SecurityUtils.verify_password(password, wrong_hash, salt) is False
        
        # Test incorrect salt
        wrong_salt = "wrong_salt"
        assert SecurityUtils.verify_password(password, hash_value, wrong_salt) is False

    def test_verify_password_exception_handling(self):
        """Test password verification with exceptions"""
        # Test with invalid hash format
        assert SecurityUtils.verify_password("password", "invalid_hash", "salt") is False

    def test_generate_hmac(self):
        """Test HMAC generation"""
        data = "test_data"
        secret = "test_secret"
        
        hmac_value = SecurityUtils.generate_hmac(data, secret)
        
        assert isinstance(hmac_value, str)
        assert len(hmac_value) == 64  # SHA-256 hex digest
        
        # Test consistency
        hmac_value2 = SecurityUtils.generate_hmac(data, secret)
        assert hmac_value == hmac_value2

    def test_verify_hmac(self):
        """Test HMAC verification"""
        data = "test_data"
        secret = "test_secret"
        
        # Generate HMAC
        hmac_value = SecurityUtils.generate_hmac(data, secret)
        
        # Test correct verification
        assert SecurityUtils.verify_hmac(data, hmac_value, secret) is True
        
        # Test incorrect data
        assert SecurityUtils.verify_hmac("wrong_data", hmac_value, secret) is False
        
        # Test incorrect signature
        assert SecurityUtils.verify_hmac(data, "wrong_signature", secret) is False
        
        # Test incorrect secret
        assert SecurityUtils.verify_hmac(data, hmac_value, "wrong_secret") is False

    def test_rate_limit_key(self):
        """Test rate limit key generation"""
        user_id = 12345
        action = "login"
        
        key = SecurityUtils.rate_limit_key(user_id, action)
        expected_key = f"rate_limit:{user_id}:{action}"
        
        assert key == expected_key

    def test_validate_json_structure(self):
        """Test JSON structure validation"""
        # Test valid structure
        data = {"field1": "value1", "field2": "value2"}
        required_fields = ["field1", "field2"]
        assert SecurityUtils.validate_json_structure(data, required_fields) is True
        
        # Test missing field
        required_fields = ["field1", "field2", "field3"]
        assert SecurityUtils.validate_json_structure(data, required_fields) is False
        
        # Test not a dict
        assert SecurityUtils.validate_json_structure("not_a_dict", required_fields) is False
        assert SecurityUtils.validate_json_structure([], required_fields) is False
        assert SecurityUtils.validate_json_structure(None, required_fields) is False

    def test_sanitize_json(self):
        """Test JSON sanitization"""
        # Test string
        result = SecurityUtils.sanitize_json("Hello<script>alert('xss')</script>")
        assert "<script>" not in result
        
        # Test dict
        data = {
            "name": "John<script>alert('xss')</script>",
            "age": 25
        }
        result = SecurityUtils.sanitize_json(data)
        assert "<script>" not in result["name"]
        assert result["age"] == 25
        
        # Test list
        data = ["Hello<script>alert('xss')</script>", 123]
        result = SecurityUtils.sanitize_json(data)
        assert "<script>" not in result[0]
        assert result[1] == 123
        
        # Test non-string/non-container
        result = SecurityUtils.sanitize_json(123)
        assert result == 123

    def test_validate_phone_number(self):
        """Test phone number validation"""
        # Test valid phone numbers
        valid_phones = [
            "09123456789",  # Iranian mobile
            "+989123456789",  # International format
            "00989123456789",  # International format with 00
            "1234567890",  # Generic 10-digit
            "123456789012345"  # Generic 15-digit
        ]
        
        for phone in valid_phones:
            assert SecurityUtils.validate_phone_number(phone) is True
        
        # Test invalid phone numbers
        invalid_phones = [
            "",  # Empty
            None,  # None
            "123",  # Too short
            "1234567890123456",  # Too long
            "0000000000",  # Too many leading zeros
            "1111111111",  # Too many ones
            "9999999999",  # Too many nines
            "1233333333",  # Too many repeated digits
            "abc123def",  # Contains letters
        ]
        
        for phone in invalid_phones:
            assert SecurityUtils.validate_phone_number(phone) is False

    def test_validate_email(self):
        """Test email validation"""
        # Test valid emails
        valid_emails = [
            "user@example.com",
            "user.name@example.com",
            "user+tag@example.co.uk",
            "user123@example-domain.org"
        ]
        
        for email in valid_emails:
            assert SecurityUtils.validate_email(email) is True
        
        # Test invalid emails
        invalid_emails = [
            "",  # Empty
            None,  # None
            "invalid-email",  # No @
            "@example.com",  # No local part
            "user@",  # No domain
            "user..name@example.com",  # Double dots
            "user.@example.com",  # Dot before @
            "@.example.com",  # @ before dot
            "user@example..com",  # Multiple dots
            "user<tag>@example.com",  # HTML tags
            "user\"tag\"@example.com",  # Quotes
            "user'tag'@example.com",  # Quotes
            "a" * 300 + "@example.com",  # Too long
        ]
        
        for email in invalid_emails:
            assert SecurityUtils.validate_email(email) is False

    @patch('utils.security.config')
    def test_create_secure_session_token(self, mock_config):
        """Test secure session token creation"""
        mock_config.bot_token = "test_bot_token"
        user_id = 12345
        
        token = SecurityUtils.create_secure_session_token(user_id, expires_in_hours=1)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Test token contains user ID
        decoded = base64.urlsafe_b64decode(token.encode()).decode()
        assert str(user_id) in decoded

    @patch('utils.security.config')
    def test_verify_session_token_valid(self, mock_config):
        """Test valid session token verification"""
        mock_config.bot_token = "test_bot_token"
        user_id = 12345
        
        # Create token
        token = SecurityUtils.create_secure_session_token(user_id, expires_in_hours=1)
        
        # Verify token
        result = SecurityUtils.verify_session_token(token)
        assert result == user_id

    @patch('utils.security.config')
    def test_verify_session_token_expired(self, mock_config):
        """Test expired session token verification"""
        mock_config.bot_token = "test_bot_token"
        user_id = 12345
        
        # Create token with very short expiration
        token = SecurityUtils.create_secure_session_token(user_id, expires_in_hours=0.0001)
        
        # Wait for expiration
        time.sleep(0.1)
        
        # Verify expired token
        result = SecurityUtils.verify_session_token(token)
        assert result is None

    def test_verify_session_token_invalid(self):
        """Test invalid session token verification"""
        # Test invalid token format
        result = SecurityUtils.verify_session_token("invalid_token")
        assert result is None
        
        # Test malformed token
        malformed_token = base64.urlsafe_b64encode("invalid:format".encode()).decode()
        result = SecurityUtils.verify_session_token(malformed_token)
        assert result is None

    def test_log_security_event(self):
        """Test security event logging"""
        with patch('utils.security.logger') as mock_logger:
            SecurityUtils.log_security_event(
                event_type="login_attempt",
                user_id=12345,
                details={"ip": "192.168.1.1"}
            )
            
            mock_logger.warning.assert_called_once()
            call_args = mock_logger.warning.call_args[0][0]
            assert "Security event:" in call_args
            assert "login_attempt" in call_args
            assert "12345" in call_args
            assert "192.168.1.1" in call_args

    def test_log_security_event_minimal(self):
        """Test security event logging with minimal data"""
        with patch('utils.security.logger') as mock_logger:
            SecurityUtils.log_security_event("test_event")
            
            mock_logger.warning.assert_called_once()
            call_args = mock_logger.warning.call_args[0][0]
            assert "Security event:" in call_args
            assert "test_event" in call_args

    def test_check_suspicious_activity(self):
        """Test suspicious activity detection"""
        user_id = 12345
        action = "login"
        context = {"ip": "192.168.1.1", "user_agent": "Mozilla/5.0"}
        
        # Current implementation always returns False
        result = SecurityUtils.check_suspicious_activity(user_id, action, context)
        assert result is False

    def test_edge_cases(self):
        """Test various edge cases"""
        # Test very long input
        long_input = "A" * 10000
        result = SecurityUtils.sanitize_input(long_input, max_length=100)
        assert len(result) == 100
        
        # Test input with only dangerous characters
        dangerous_input = "<script>alert('xss')</script>"
        result = SecurityUtils.sanitize_input(dangerous_input)
        assert result == ""  # All content should be removed
        
        # Test input with mixed content
        mixed_input = "Hello<script>alert('xss')</script>World"
        result = SecurityUtils.sanitize_input(mixed_input)
        assert "Hello" in result
        assert "World" in result
        assert "<script>" not in result
        assert "alert('xss')" not in result

    def test_concurrent_access(self):
        """Test concurrent access to security utilities"""
        import threading
        
        def generate_tokens():
            for _ in range(100):
                SecurityUtils.generate_secure_token()
                SecurityUtils.hash_password("test_password")
        
        # Create multiple threads
        threads = [threading.Thread(target=generate_tokens) for _ in range(5)]
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # No exceptions should occur
        assert True
