#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import os
import pytest


pytestmark = pytest.mark.asyncio


async def test_help_and_menu_mocked_bot():
    # Smoke-test bot entry functions that don't require Telegram API
    # Ensures import and main callable exist
    import bot as app

    assert callable(app.main)



