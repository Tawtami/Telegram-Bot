#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Symmetric encryption utilities (AES-GCM) for protecting sensitive fields at rest.

Requires environment variable ENCRYPTION_KEY (32 bytes base64-urlsafe) or will
derive a key from BOT_TOKEN for development fallback (not recommended for prod).
"""

from __future__ import annotations

import os
import base64
import json
from typing import Optional
from config import config as config  # Allow tests to patch utils.crypto.config

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class CryptoManager:
    """Field-level encryption/decryption with AES-GCM."""

    def __init__(self, key: Optional[bytes] = None):
        # Accept any explicit key length >= 16 bytes; normalize to a valid AES key
        # length (16/24/32) at use-time. Reject keys shorter than 16 bytes.
        self._key = key or self._load_key()
        if self._key is None or len(self._key) < 16:
            raise ValueError("Invalid ENCRYPTION_KEY length; must be at least 16 bytes")

    @staticmethod
    def _load_key() -> bytes:
        key_env = os.getenv("ENCRYPTION_KEY", "").strip()
        if key_env:
            # Prefer canonical base64 only if round-trip matches (avoid misdetecting plain text)
            try:
                padded = key_env + ("=" * (-len(key_env) % 4))
                decoded = base64.urlsafe_b64decode(padded)
                # Round-trip to ensure it was really base64
                rt = base64.urlsafe_b64encode(decoded).decode("utf-8").rstrip("=")
                if rt == key_env.rstrip("=") and len(decoded) >= 16:
                    return decoded
            except Exception:
                pass
            # Try hex
            try:
                decoded_hex = bytes.fromhex(key_env)
                if len(decoded_hex) >= 16:
                    return decoded_hex
            except Exception:
                pass
            # Raw utf-8 (used by tests when a plain string key is supplied)
            utf8_bytes = key_env.encode("utf-8")
            if len(utf8_bytes) >= 16:
                return utf8_bytes

        # If we're in production/webhook mode, do NOT fallback – require ENCRYPTION_KEY
        try:
            from config import config as app_config

            if app_config.webhook.enabled or os.getenv("ENVIRONMENT", "").lower() == "production":
                raise ValueError(
                    "ENCRYPTION_KEY is required in production/webhook mode (no fallback allowed)"
                )
        except Exception:
            # If config import fails, best-effort: honor ENVIRONMENT var
            if os.getenv("ENVIRONMENT", "").lower() == "production":
                raise

        # Development fallback (derive from BOT_TOKEN) - ONLY for local/dev
        token = (config.bot_token or "dev").encode("utf-8")
        # Simple KDF: take first 32 bytes of SHA256(token)
        import hashlib

        return hashlib.sha256(token).digest()

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
        data = base64.urlsafe_b64decode(ciphertext_b64.encode("utf-8"))
        nonce, ct = data[:12], data[12:]
        aesgcm = AESGCM(self._aes_key())
        pt = aesgcm.decrypt(nonce, ct, associated_data)
        try:
            return pt.decode("utf-8")
        except Exception:
            return pt.decode("utf-8", errors="ignore")


# Singleton instance
crypto_manager = CryptoManager()
