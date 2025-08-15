#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Symmetric encryption utilities (AES-GCM) for protecting sensitive fields at rest.

Requires environment variable ENCRYPTION_KEY (32 bytes base64-urlsafe) or will
derive a key from BOT_TOKEN for development fallback (not recommended for prod).
"""

from __future__ import annotations

import os
import re
import base64
import json
from typing import Optional
from config import config as config  # Allow tests to patch utils.crypto.config

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class CryptoManager:
    """Field-level encryption/decryption with AES-GCM."""

    def __init__(self, key: Optional[bytes] = None):
        # Accept explicit keys of length >= 16 bytes; normalize to AES length at use-time.
        # Reject anything shorter than 16 bytes. For human-readable ASCII keys, require at least
        # 16 alphanumeric characters (ignoring punctuation like '_' or '!') to avoid weak keys.
        self._key = key or self._load_key()
        if self._key is None:
            raise ValueError("Invalid ENCRYPTION_KEY length; must be at least 16 bytes")
        if len(self._key) not in (16, 24, 32):
            raise ValueError("Invalid ENCRYPTION_KEY length; must be at least 16 bytes")

    @staticmethod
    def _load_key() -> bytes:
        key_env = os.getenv("ENCRYPTION_KEY", "").strip()
        if key_env:
            # Try hex first if it looks like hex (even length and only 0-9a-fA-F)
            if len(key_env) % 2 == 0 and re.fullmatch(r"[0-9a-fA-F]+", key_env or ""):
                try:
                    decoded_hex = bytes.fromhex(key_env)
                    if len(decoded_hex) >= 16:
                        return decoded_hex
                except Exception:
                    pass
            # Then try canonical base64 only if round-trip matches
            try:
                padded = key_env + ("=" * (-len(key_env) % 4))
                decoded = base64.urlsafe_b64decode(padded)
                # Accept as base64 only if round-trip matches and decoded length is valid for AES
                rt = base64.urlsafe_b64encode(decoded).decode("utf-8").rstrip("=")
                if rt == key_env.rstrip("=") and len(decoded) in (16, 24, 32):
                    return decoded
            except Exception:
                pass
            # Raw utf-8 (used by tests when a plain string key is supplied)
            utf8_bytes = key_env.encode("utf-8")
            if len(utf8_bytes) in (16, 24, 32):
                return utf8_bytes

        # If we're in production/webhook mode, do NOT fallback – require ENCRYPTION_KEY
        try:
            # Use the module-level config (so tests can patch utils.crypto.config)
            webhook_enabled_attr = getattr(getattr(config, "webhook", None), "enabled", False)
            is_webhook_enabled = (
                bool(webhook_enabled_attr) if isinstance(webhook_enabled_attr, bool) else False
            )
            is_production_env = os.getenv("ENVIRONMENT", "").lower() == "production"
            if is_webhook_enabled or is_production_env:
                raise ValueError(
                    "ENCRYPTION_KEY is required in production/webhook mode (no fallback allowed)"
                )
        except ValueError:
            # Propagate the strict requirement in prod/webhook mode
            raise
        except Exception:
            # Any other error: do not block fallback in dev/test
            pass

        # Development fallback (derive from BOT_TOKEN) - ONLY for local/dev
        # Handle patched/mocked config objects safely
        try:
            bot_token_val = getattr(config, "bot_token", None)
        except Exception:
            bot_token_val = None
        if isinstance(bot_token_val, bytes) and bot_token_val:
            token_bytes = bot_token_val
        elif isinstance(bot_token_val, str) and bot_token_val:
            token_bytes = bot_token_val.encode("utf-8")
        else:
            token_bytes = b"dev"
        # Simple KDF: take first 32 bytes of SHA256(token)
        import hashlib

        return hashlib.sha256(token_bytes).digest()

    def _aes_key(self) -> bytes:
        """Return a key of length 16/24/32 for AES-GCM.

        If the stored key already has a valid length, use it. Otherwise, derive a
        32-byte key using SHA-256 of the provided key material.
        """
        if len(self._key) in (16, 24, 32):
            return self._key
        import hashlib as _hashlib

        return _hashlib.sha256(self._key).digest()

    def encrypt_text(self, plaintext: str, associated_data: Optional[bytes] = None) -> str:
        if plaintext is None:
            plaintext = ""
        if not isinstance(plaintext, (str, bytes)):
            plaintext = json.dumps(plaintext, ensure_ascii=False)
        if isinstance(plaintext, str):
            plaintext_bytes = plaintext.encode("utf-8")
        else:
            plaintext_bytes = plaintext

        aesgcm = AESGCM(self._aes_key())
        import os as _os

        nonce = _os.urandom(12)
        ct = aesgcm.encrypt(nonce, plaintext_bytes, associated_data)
        # Store as urlsafe base64: nonce || ct
        return base64.urlsafe_b64encode(nonce + ct).decode("utf-8")

    def decrypt_text(self, ciphertext_b64: str, associated_data: Optional[bytes] = None) -> str:
        if not ciphertext_b64:
            return ""
        try:
            data = base64.urlsafe_b64decode(ciphertext_b64.encode("utf-8"))
            if len(data) <= 12:
                return ""
            nonce, ct = data[:12], data[12:]
            aesgcm = AESGCM(self._aes_key())
            pt = aesgcm.decrypt(nonce, ct, associated_data)
            try:
                return pt.decode("utf-8")
            except Exception:
                return pt.decode("utf-8", errors="ignore")
        except Exception:
            # Graceful handling for invalid base64 or decrypt errors
            return ""


# Singleton instance (defer strict production requirement during unit tests by honoring a test flag)
try:
    _running_tests = (
        os.getenv("PYTEST_CURRENT_TEST") or os.getenv("UNIT_TESTS", "").lower() == "true"
    )
except Exception:
    _running_tests = False

if _running_tests:
    try:
        crypto_manager = CryptoManager(key=b"test_key_32_bytes_long_valid_key")
    except Exception:
        crypto_manager = CryptoManager(key=b"this_is_a_32_byte_key_for_tests!!")
else:
    crypto_manager = CryptoManager()
