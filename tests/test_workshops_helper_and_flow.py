#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import os
import sys


def test_get_workshop_months_reads_from_courses_json():
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from utils.workshops import get_workshop_months

    months = get_workshop_months()
    assert isinstance(months, list) and months, "months list should not be empty"
    # Should be sorted by (year, month)
    # Simple monotonic check using parse key again
    from utils.workshops import _parse_month_key

    keys = [_parse_month_key(m) for m in months]
    assert keys == sorted(keys), "months must be sorted by year+month"
    # Must contain known timeframe months from the provided JSON
    assert "مهر ۱۴۰۴" in months and "تیر ۱۴۰۵" in months


def test_workshop_detail_has_expected_body_text():
    # Minimal async invocation of workshop select to render one month
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    import telegram_mock  # noqa: F401

    from handlers.courses import handle_workshop_select

    class _DummyQuery:
        def __init__(self, data):
            self.data = data
            self.from_user = type("U", (), {"id": 1})

        async def answer(self, *a, **k):
            return

        async def edit_message_text(self, text, **kwargs):
            test_workshop_detail_has_expected_body_text.captured = text

    class _DummyUpdate:
        def __init__(self, data):
            self.callback_query = _DummyQuery(data)
            self.effective_user = type("U", (), {"id": 1})

    class _DummyContext:
        user_data = {}

    async def _run():
        upd = _DummyUpdate("workshop:مهر ۱۴۰۴")
        await handle_workshop_select(upd, _DummyContext())

    asyncio.run(_run())
    body = getattr(test_workshop_detail_has_expected_body_text, "captured", "")
    assert "همایش ماهانه (مهر ۱۴۰۴) — موضوع بعداً اعلام می‌شود." in body
