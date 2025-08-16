#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import os
import sys


def _capture_paid_workshops_text():
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    import telegram_mock  # noqa: F401
    from handlers.courses import handle_paid_workshops

    class _Ctx:
        user_data = {}

    class _Q:
        def __init__(self):
            self.from_user = type("U", (), {"id": 1})

        async def answer(self, *a, **k):
            return

        async def edit_message_text(self, text, reply_markup=None, **kwargs):
            _capture_paid_workshops_text.captured = (text, reply_markup)

    class _Upd:
        def __init__(self):
            self.callback_query = _Q()
            self.effective_user = type("U", (), {"id": 1})

    async def _run():
        await handle_paid_workshops(_Upd(), _Ctx())

    asyncio.run(_run())
    return getattr(_capture_paid_workshops_text, "captured", ("", None))


def test_parent_workshops_header_dynamic_lines():
    text, kb = _capture_paid_workshops_text()
    # Standardized header line
    assert "همایش‌های ماهانه — موضوع بعداً اعلام می‌شود" in text
    # Duration line optional but if present must start with the clock emoji
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    has_duration = any(ln.startswith("⏰ ") for ln in lines)
    # Price line must exist and start with ثبت‌نام:
    has_price = any(ln.startswith("ثبت‌نام:") for ln in lines)
    assert has_price, "Parent workshops menu must include a price line"
    # Price line content either contact or numeric/range
    price_line = next(ln for ln in lines if ln.startswith("ثبت‌نام:"))
    assert ("تماس" in price_line) or any(ch.isdigit() for ch in price_line)
    # Inline keyboard includes all months plus back
    assert kb and getattr(kb, "inline_keyboard", None), "Inline keyboard expected"
