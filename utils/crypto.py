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

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class CryptoManager:
    """Field-level encryption/decryption with AES-GCM."""

    def __init__(self, key: Optional[bytes] = None):
        self._key = key or self._load_key()
        if len(self._key) not in (16, 24, 32):
            # Ensure AES-128/192/256
            raise ValueError("Invalid ENCRYPTION_KEY length; must be 16/24/32 bytes")

    @staticmethod
    def _load_key() -> bytes:
        key_env = os.getenv("ENCRYPTION_KEY", "").strip()
        if key_env:
            try:
                # Support both raw bytes (hex/base64) and urlsafe b64
                try:
                    return base64.urlsafe_b64decode(key_env)
                except Exception:
                    pass
                try:
                    return bytes.fromhex(key_env)
                except Exception:
                    pass
                return key_env.encode("utf-8")
            except Exception:
                pass

        # If we're in production/webhook mode, do NOT fallback – require ENCRYPTION_KEY
        try:
            from config import config as app_config

            if (
                app_config.webhook.enabled
                or os.getenv("ENVIRONMENT", "").lower() == "production"
            ):
                raise ValueError(
                    "ENCRYPTION_KEY is required in production/webhook mode (no fallback allowed)"
                )
        except Exception:
            # If config import fails, best-effort: honor ENVIRONMENT var
            if os.getenv("ENVIRONMENT", "").lower() == "production":
                raise

        # Development fallback (derive from BOT_TOKEN) - ONLY for local/dev
        from config import config

        token = (config.bot_token or "dev").encode("utf-8")
        # Simple KDF: take first 32 bytes of SHA256(token)
        import hashlib

        return hashlib.sha256(token).digest()

    def encrypt_text(
        self, plaintext: str, associated_data: Optional[bytes] = None
    ) -> str:
        if plaintext is None:
            plaintext = ""
        if not isinstance(plaintext, (str, bytes)):
            plaintext = json.dumps(plaintext, ensure_ascii=False)
        if isinstance(plaintext, str):
            plaintext_bytes = plaintext.encode("utf-8")
        else:
            plaintext_bytes = plaintext

        aesgcm = AESGCM(self._key)
        import os as _os

        nonce = _os.urandom(12)
        ct = aesgcm.encrypt(nonce, plaintext_bytes, associated_data)
        # Store as urlsafe base64: nonce || ct
        return base64.urlsafe_b64encode(nonce + ct).decode("utf-8")

    def decrypt_text(
        self, ciphertext_b64: str, associated_data: Optional[bytes] = None
    ) -> str:
        if not ciphertext_b64:
            return ""
        data = base64.urlsafe_b64decode(ciphertext_b64.encode("utf-8"))
        nonce, ct = data[:12], data[12:]
        aesgcm = AESGCM(self._key)
        pt = aesgcm.decrypt(nonce, ct, associated_data)
        try:
            return pt.decode("utf-8")
        except Exception:
            return pt.decode("utf-8", errors="ignore")


# Singleton instance
crypto_manager = CryptoManager()
