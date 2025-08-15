#!/usr/bin/env python3
"""
Mock Cryptography module for running tests without cryptography

This provides the basic cryptography functionality that our test files need
to run without the actual cryptography package.
"""

import sys
from unittest.mock import MagicMock


# Mock Cryptography classes
class AESGCM:
    """Mock AESGCM class with deterministic reversible transform for tests"""

    def __init__(self, *args, **kwargs):
        pass

    def encrypt(self, nonce, plaintext, associated_data=None):
        # Produce nonce || plaintext (identity) to allow decrypt round-trip
        try:
            return nonce + bytes(plaintext)
        except Exception:
            return nonce + (plaintext or b"")

    def decrypt(self, nonce, ciphertext, associated_data=None):
        # Expect ciphertext as nonce || plaintext; strip first len(nonce) bytes
        pt = ciphertext[len(nonce) :]
        return pt


class Fernet:
    """Mock Fernet class"""

    def __init__(self, *args, **kwargs):
        pass

    def encrypt(self, *args, **kwargs):
        return b'mock_encrypted_data'

    def decrypt(self, *args, **kwargs):
        return b'mock_decrypted_data'


# Add to sys.modules so imports work
sys.modules['cryptography'] = MagicMock()
sys.modules['cryptography.hazmat'] = MagicMock()
sys.modules['cryptography.hazmat.primitives'] = MagicMock()
sys.modules['cryptography.hazmat.primitives.ciphers'] = MagicMock()
sys.modules['cryptography.hazmat.primitives.ciphers.aead'] = sys.modules[__name__]
sys.modules['cryptography.fernet'] = sys.modules[__name__]
