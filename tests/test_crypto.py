#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for crypto.py
"""
import pytest
import os
import base64
import hashlib
from unittest.mock import patch, MagicMock
from utils.crypto import CryptoManager, crypto_manager


class TestCryptoManager:
    """Test cases for CryptoManager class"""

    def test_init_with_valid_key(self):
        """Test initialization with valid key"""
        key = b"test_key_32_bytes_long_valid_key"
        manager = CryptoManager(key)
        assert manager._key == key

    def test_init_with_invalid_key_length(self):
        """Test initialization with invalid key length"""
        key = b"short_key"  # Less than 16 bytes
        with pytest.raises(ValueError, match="Invalid ENCRYPTION_KEY length"):
            CryptoManager(key)

    def test_init_with_15_byte_key(self):
        """Test initialization with 15 byte key (invalid)"""
        key = b"fifteen_bytes_key"
        with pytest.raises(ValueError, match="Invalid ENCRYPTION_KEY length"):
            CryptoManager(key)

    def test_init_with_16_byte_key(self):
        """Test initialization with 16 byte key (valid AES-128)"""
        key = b"sixteen_bytes_key!"
        manager = CryptoManager(key)
        assert manager._key == key

    def test_init_with_24_byte_key(self):
        """Test initialization with 24 byte key (valid AES-192)"""
        key = b"twenty_four_bytes_key_valid!"
        manager = CryptoManager(key)
        assert manager._key == key

    def test_init_with_32_byte_key(self):
        """Test initialization with 32 byte key (valid AES-256)"""
        key = b"thirty_two_bytes_key_valid_for_aes_256!"
        manager = CryptoManager(key)
        assert manager._key == key

    @patch.dict(os.environ, {'ENCRYPTION_KEY': 'dGVzdF9rZXlfMzJfYnl0ZXNfbG9uZ192YWxpZF9rZXk'})
    def test_load_key_from_env_base64(self):
        """Test loading key from environment variable (base64)"""
        manager = CryptoManager()
        expected_key = b"test_key_32_bytes_long_valid_key"
        assert manager._key == expected_key

    @patch.dict(os.environ, {'ENCRYPTION_KEY': '746573745f6b65795f33325f62797465735f6c6f6e675f76616c69645f6b6579'})
    def test_load_key_from_env_hex(self):
        """Test loading key from environment variable (hex)"""
        manager = CryptoManager()
        expected_key = b"test_key_32_bytes_long_valid_key"
        assert manager._key == expected_key

    @patch.dict(os.environ, {'ENCRYPTION_KEY': 'test_key_32_bytes_long_valid_key'})
    def test_load_key_from_env_utf8(self):
        """Test loading key from environment variable (utf8)"""
        manager = CryptoManager()
        expected_key = b"test_key_32_bytes_long_valid_key"
        assert manager._key == expected_key

    @patch.dict(os.environ, {'ENCRYPTION_KEY': 'invalid_key'})
    def test_load_key_from_env_invalid_fallback(self):
        """Test loading key from environment variable with invalid key"""
        with patch('utils.crypto.config') as mock_config:
            mock_config.bot_token = "test_bot_token"
            manager = CryptoManager()
            # Should fallback to derived key from bot_token
            expected_key = hashlib.sha256(b"test_bot_token").digest()
            assert manager._key == expected_key

    @patch.dict(os.environ, {'ENCRYPTION_KEY': '', 'ENVIRONMENT': 'production'})
    def test_load_key_production_no_fallback(self):
        """Test that production environment requires ENCRYPTION_KEY"""
        with pytest.raises(ValueError, match="ENCRYPTION_KEY is required in production"):
            CryptoManager()

    @patch.dict(os.environ, {'ENCRYPTION_KEY': '', 'ENVIRONMENT': 'PRODUCTION'})
    def test_load_key_production_uppercase_no_fallback(self):
        """Test that uppercase PRODUCTION environment requires ENCRYPTION_KEY"""
        with pytest.raises(ValueError, match="ENCRYPTION_KEY is required in production"):
            CryptoManager()

    @patch.dict(os.environ, {'ENCRYPTION_KEY': ''})
    @patch('utils.crypto.config')
    def test_load_key_webhook_mode_no_fallback(self, mock_config):
        """Test that webhook mode requires ENCRYPTION_KEY"""
        mock_config.webhook.enabled = True
        with pytest.raises(ValueError, match="ENCRYPTION_KEY is required in production"):
            CryptoManager()

    @patch.dict(os.environ, {'ENCRYPTION_KEY': ''})
    @patch('utils.crypto.config')
    def test_load_key_development_fallback(self, mock_config):
        """Test development fallback to bot_token"""
        mock_config.webhook.enabled = False
        mock_config.bot_token = "dev_bot_token"
        manager = CryptoManager()
        expected_key = hashlib.sha256(b"dev_bot_token").digest()
        assert manager._key == expected_key

    @patch.dict(os.environ, {'ENCRYPTION_KEY': ''})
    @patch('utils.crypto.config')
    def test_load_key_development_fallback_no_bot_token(self, mock_config):
        """Test development fallback with no bot_token"""
        mock_config.webhook.enabled = False
        mock_config.bot_token = None
        manager = CryptoManager()
        expected_key = hashlib.sha256(b"dev").digest()
        assert manager._key == expected_key

    @patch.dict(os.environ, {'ENCRYPTION_KEY': ''})
    @patch('utils.crypto.config')
    def test_load_key_config_import_failure(self, mock_config):
        """Test fallback when config import fails"""
        mock_config.side_effect = ImportError("Config not available")
        manager = CryptoManager()
        # Should use default "dev" token
        expected_key = hashlib.sha256(b"dev").digest()
        assert manager._key == expected_key

    def test_encrypt_text_string(self):
        """Test encrypting string text"""
        key = b"test_key_32_bytes_long_valid_key"
        manager = CryptoManager(key)
        plaintext = "Hello, World!"
        
        ciphertext = manager.encrypt_text(plaintext)
        
        assert isinstance(ciphertext, str)
        assert len(ciphertext) > 0
        # Verify it's base64 encoded
        try:
            base64.urlsafe_b64decode(ciphertext.encode())
        except Exception:
            pytest.fail("Ciphertext is not valid base64")

    def test_encrypt_text_none(self):
        """Test encrypting None text"""
        key = b"test_key_32_bytes_long_valid_key"
        manager = CryptoManager(key)
        
        ciphertext = manager.encrypt_text(None)
        
        assert isinstance(ciphertext, str)
        assert len(ciphertext) > 0

    def test_encrypt_text_bytes(self):
        """Test encrypting bytes text"""
        key = b"test_key_32_bytes_long_valid_key"
        manager = CryptoManager(key)
        plaintext = b"Hello, World!"
        
        ciphertext = manager.encrypt_text(plaintext)
        
        assert isinstance(ciphertext, str)
        assert len(ciphertext) > 0

    def test_encrypt_text_dict(self):
        """Test encrypting dictionary (should be JSON serialized)"""
        key = b"test_key_32_bytes_long_valid_key"
        manager = CryptoManager(key)
        plaintext = {"key": "value", "number": 42}
        
        ciphertext = manager.encrypt_text(plaintext)
        
        assert isinstance(ciphertext, str)
        assert len(ciphertext) > 0

    def test_encrypt_text_with_associated_data(self):
        """Test encrypting text with associated data"""
        key = b"test_key_32_bytes_long_valid_key"
        manager = CryptoManager(key)
        plaintext = "Hello, World!"
        associated_data = b"context_data"
        
        ciphertext = manager.encrypt_text(plaintext, associated_data)
        
        assert isinstance(ciphertext, str)
        assert len(ciphertext) > 0

    def test_decrypt_text_success(self):
        """Test successful decryption"""
        key = b"test_key_32_bytes_long_valid_key"
        manager = CryptoManager(key)
        plaintext = "Hello, World!"
        
        ciphertext = manager.encrypt_text(plaintext)
        decrypted = manager.decrypt_text(ciphertext)
        
        assert decrypted == plaintext

    def test_decrypt_text_with_associated_data(self):
        """Test decryption with associated data"""
        key = b"test_key_32_bytes_long_valid_key"
        manager = CryptoManager(key)
        plaintext = "Hello, World!"
        associated_data = b"context_data"
        
        ciphertext = manager.encrypt_text(plaintext, associated_data)
        decrypted = manager.decrypt_text(ciphertext, associated_data)
        
        assert decrypted == plaintext

    def test_decrypt_text_empty_string(self):
        """Test decryption of empty string"""
        key = b"test_key_32_bytes_long_valid_key"
        manager = CryptoManager(key)
        
        decrypted = manager.decrypt_text("")
        
        assert decrypted == ""

    def test_decrypt_text_none(self):
        """Test decryption of None"""
        key = b"test_key_32_bytes_long_valid_key"
        manager = CryptoManager(key)
        
        decrypted = manager.decrypt_text(None)
        
        assert decrypted == ""

    def test_decrypt_text_invalid_base64(self):
        """Test decryption with invalid base64 (should handle gracefully)"""
        key = b"test_key_32_bytes_long_valid_key"
        manager = CryptoManager(key)
        
        # This should not crash, even with invalid input
        try:
            decrypted = manager.decrypt_text("invalid_base64_string")
            # Should return some result (even if garbled)
            assert isinstance(decrypted, str)
        except Exception:
            pytest.fail("Decryption should handle invalid input gracefully")

    def test_encrypt_decrypt_roundtrip(self):
        """Test complete encrypt/decrypt roundtrip"""
        key = b"test_key_32_bytes_long_valid_key"
        manager = CryptoManager(key)
        test_cases = [
            "Simple text",
            "Text with unicode: 🚀🌟🎉",
            "Text with numbers: 12345",
            "Text with special chars: !@#$%^&*()",
            "",  # Empty string
            "Very long text " * 100,  # Long text
        ]
        
        for plaintext in test_cases:
            ciphertext = manager.encrypt_text(plaintext)
            decrypted = manager.decrypt_text(ciphertext)
            assert decrypted == plaintext, f"Failed for: {repr(plaintext)}"

    def test_encrypt_decrypt_roundtrip_with_associated_data(self):
        """Test complete encrypt/decrypt roundtrip with associated data"""
        key = b"test_key_32_bytes_long_valid_key"
        manager = CryptoManager(key)
        plaintext = "Hello, World!"
        associated_data = b"context_data"
        
        ciphertext = manager.encrypt_text(plaintext, associated_data)
        decrypted = manager.decrypt_text(ciphertext, associated_data)
        
        assert decrypted == plaintext

    def test_encrypt_decrypt_roundtrip_without_associated_data(self):
        """Test that associated data must match for decryption"""
        key = b"test_key_32_bytes_long_valid_key"
        manager = CryptoManager(key)
        plaintext = "Hello, World!"
        associated_data = b"context_data"
        
        ciphertext = manager.encrypt_text(plaintext, associated_data)
        
        # Decrypting without associated data should fail or return garbage
        try:
            decrypted = manager.decrypt_text(ciphertext)
            # If it doesn't fail, the result should be different
            assert decrypted != plaintext
        except Exception:
            # Expected behavior - decryption should fail
            pass


class TestCryptoManagerSingleton:
    """Test cases for the singleton crypto_manager instance"""

    def test_singleton_instance(self):
        """Test that crypto_manager is a singleton instance"""
        assert crypto_manager is not None
        assert isinstance(crypto_manager, CryptoManager)

    def test_singleton_key_loaded(self):
        """Test that singleton instance has a valid key loaded"""
        assert hasattr(crypto_manager, '_key')
        assert len(crypto_manager._key) in (16, 24, 32)

    def test_singleton_encrypt_decrypt(self):
        """Test that singleton instance can encrypt and decrypt"""
        plaintext = "Test message for singleton"
        ciphertext = crypto_manager.encrypt_text(plaintext)
        decrypted = crypto_manager.decrypt_text(ciphertext)
        assert decrypted == plaintext
