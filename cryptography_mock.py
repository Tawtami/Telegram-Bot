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
    """Mock AESGCM class"""

    def __init__(self, *args, **kwargs):
        pass

    def encrypt(self, *args, **kwargs):
        return b'mock_encrypted_data'

    def decrypt(self, *args, **kwargs):
        return b'mock_decrypted_data'


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
