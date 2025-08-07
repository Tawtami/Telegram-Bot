#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bot handlers module
"""

from .registration import router as registration_router
from .courses import router as courses_router
from .purchases import router as purchases_router
from .main_menu import router as main_menu_router
from .admin import router as admin_router

__all__ = [
    "registration_router",
    "courses_router", 
    "purchases_router",
    "main_menu_router",
    "admin_router",
]
