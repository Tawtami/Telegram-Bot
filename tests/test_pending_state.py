#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
from datetime import datetime, timedelta
import os
import sys


def _mk_ctx():
    class _Ctx:
        def __init__(self):
            self.user_data = {}

    return _Ctx()


def _mk_update(callback_data: str):
    class _Q:
        def __init__(self, data):
            self.data = data
            self.from_user = type("U", (), {"id": 1})

        async def answer(self, *a, **k):
            return

        async def edit_message_text(self, *a, **k):
            return

    class _Upd:
        def __init__(self, data):
            self.callback_query = _Q(data)
            self.effective_user = type("U", (), {"id": 1})

    return _Upd(callback_data)


def test_confirm_clears_pending():
    # Arrange
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    import telegram_mock  # noqa: F401
    from handlers.courses import (
        handle_course_registration,
        handle_course_registration_confirm,
    )

    ctx = _mk_ctx()

    async def _run():
        # Tap register to set pending
        await handle_course_registration(_mk_update("register_course_paid_exp_math1"), ctx)
        assert "pending_course_request" in ctx.user_data
        # Confirm should clear pending_course_request
        await handle_course_registration_confirm(
            _mk_update("confirm_register_course_paid_exp_math1"), ctx
        )

    asyncio.run(_run())
    assert "pending_course_request" not in ctx.user_data


def test_auto_expire_clears_stale_then_sets_new_pending():
    # Arrange
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    import telegram_mock  # noqa: F401
    from handlers.courses import handle_course_registration

    ctx = _mk_ctx()
    # Seed stale pending older than 5 minutes
    ctx.user_data["pending_course_request"] = {
        "course_id": "some_old",
        "timestamp": datetime.utcnow() - timedelta(minutes=6),
    }

    async def _run():
        # New tap should auto-clear stale and set fresh pending for exp_math1
        await handle_course_registration(_mk_update("register_course_paid_exp_math1"), ctx)

    asyncio.run(_run())
    pend = ctx.user_data.get("pending_course_request")
    assert isinstance(pend, dict)
    assert pend.get("course_id") == "exp_math1"
    ts = pend.get("timestamp")
    assert isinstance(ts, datetime)
    assert datetime.utcnow() - ts < timedelta(minutes=5)
