#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import os
import sys


def _capture_edit_text(fn, update):
    class _Ctx:
        user_data = {}

    class _Q:
        def __init__(self, data):
            self.data = data
            self.from_user = type("U", (), {"id": 1})

        async def answer(self, *a, **k):
            return

        async def edit_message_text(self, text, reply_markup=None, **kwargs):
            _capture_edit_text.captured = (text, reply_markup)

    class _Upd:
        def __init__(self, data):
            self.callback_query = _Q(data)
            self.effective_user = type("U", (), {"id": 1})

    async def _run():
        await fn(_Upd(update), _Ctx())

    asyncio.run(_run())
    return getattr(_capture_edit_text, "captured", ("", None))


def test_confirmation_single_lesson_back_target_and_copy():
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    import telegram_mock  # noqa: F401
    from handlers.courses import handle_paid_single_select, handle_course_registration

    # Step 1: open single lesson detail
    text, _ = _capture_edit_text(handle_paid_single_select, "paid_single_exp_math1")
    assert "ریاضی ۱ (تجربی)" in text

    # Step 2: click register -> confirmation screen
    text, kb = _capture_edit_text(handle_course_registration, "register_course_paid_exp_math1")
    assert "آیا مطمئن هستید" in text
    # Back target for single lessons
    assert any(
        "paid_single" in (btn.callback_data or "") for row in kb.inline_keyboard for btn in row
    )


def test_confirmation_comprehensive_back_target_and_copy():
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    import telegram_mock  # noqa: F401
    from handlers.courses import handle_paid_comp_select, handle_course_registration

    text, _ = _capture_edit_text(handle_paid_comp_select, "paid_comp_math")
    assert "دوره جامع" in text

    text, kb = _capture_edit_text(handle_course_registration, "register_course_paid_comp_math")
    assert "آیا مطمئن هستید" in text
    assert any(
        "paid_comprehensive" in (btn.callback_data or "")
        for row in kb.inline_keyboard
        for btn in row
    )


def test_confirmation_workshop_back_target_and_copy():
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    import telegram_mock  # noqa: F401
    from handlers.courses import handle_workshop_select, handle_course_registration

    text, _ = _capture_edit_text(handle_workshop_select, "workshop:مهر ۱۴۰۴")
    assert "همایش ماهانه (مهر ۱۴۰۴)" in text

    text, kb = _capture_edit_text(
        handle_course_registration, "register_course_paid_workshop_مهر ۱۴۰۴"
    )
    assert "آیا مطمئن هستید" in text
    assert any(
        "paid_workshops" in (btn.callback_data or "") for row in kb.inline_keyboard for btn in row
    )
