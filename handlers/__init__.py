#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Handler modules for Ostad Hatami Bot
"""

import logging

logger = logging.getLogger(__name__)

# Try to import handlers with fallback for missing telegram modules
try:
    from .registration import build_registration_conversation
    from .menu import build_menu_handlers
    from .courses import build_course_handlers
    from .books import build_book_handlers
    from .payments import build_payment_handlers
    from .contact import build_contact_handlers
    from .social import build_social_handlers

    HANDLERS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"⚠️ Warning: Some handlers not available due to missing dependencies: {e}")
    HANDLERS_AVAILABLE = False

    # Create dummy functions for development
    def build_registration_conversation():
        return None

    def build_menu_handlers():
        return []

    def build_course_handlers():
        return []

    def build_book_handlers():
        return []

    def build_payment_handlers():
        return []

    def build_contact_handlers():
        return []

    def build_social_handlers():
        return []


__all__ = [
    "build_registration_conversation",
    "build_menu_handlers",
    "build_course_handlers",
    "build_book_handlers",
    "build_payment_handlers",
    "build_contact_handlers",
    "build_social_handlers",
    "HANDLERS_AVAILABLE",
]
