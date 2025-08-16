#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import types
import pytest


@pytest.mark.asyncio
async def test_profile_shows_address_and_receipts(monkeypatch):
    from database.db import session_scope
    from database.models_sql import User, Purchase, Receipt
    from bot import profile_command

    class Msg:
        def __init__(self):
            self.sent = []

        async def reply_text(self, text, **k):
            self.sent.append(text)

    class Upd:
        def __init__(self, uid):
            self.effective_user = types.SimpleNamespace(id=uid)
            self.message = Msg()

    class Ctx:
        bot_data = {}

    uid = 999123
    with session_scope() as s:
        u = User(telegram_user_id=uid, first_name="علی", last_name="رضایی", phone="09120000000")
        u.address = "تهران، خیابان تست"
        u.postal_code = "1234567890"
        s.add(u)
        s.flush()
        p = Purchase(user_id=u.id, product_type="course", product_id="exp_math1", status="pending")
        s.add(p)
        s.flush()
        r = Receipt(purchase_id=p.id, telegram_file_id="FILE_ID_X", file_unique_id="UNIQ_X")
        s.add(r)
        s.flush()

    upd = Upd(uid)
    ctx = Ctx()
    await profile_command(upd, ctx)
    full_text = "\n".join(upd.message.sent)
    assert "آدرس" in full_text
    assert "کد پستی" in full_text
    assert "FILE_ID_X" in full_text


@pytest.mark.asyncio
async def test_admin_approve_reject_with_receipt(monkeypatch):
    from handlers.payments import handle_payment_decision

    class Q:
        def __init__(self, data, uid):
            self.data = data
            self.from_user = types.SimpleNamespace(id=uid)

        async def answer(self):
            return

        async def edit_message_text(self, *a, **k):
            return

        async def edit_message_reply_markup(self, **k):
            return

    class Upd:
        def __init__(self, data, uid):
            self.callback_query = Q(data, uid)
            self.effective_user = types.SimpleNamespace(id=uid)

    class Ctx:
        def __init__(self):
            self.bot_data = {
                "config": types.SimpleNamespace(bot=types.SimpleNamespace(admin_user_ids=[111]))
            }
            self.args = []

        class Bot:
            async def send_message(self, *a, **k):
                return

        bot = Bot()

    token = "tok12345678"
    ctx = Ctx()
    ctx.bot_data["payment_notifications"] = {
        token: {
            "student_id": 555,
            "item_type": "course",
            "item_id": "exp_math1",
            "item_title": "exp_math1",
            "messages": [],
            "processed": False,
            "created_at": 0,
        }
    }

    upd = Upd(f"pay:{token}:approve", 111)
    await handle_payment_decision(upd, ctx)
    assert ctx.bot_data["payment_notifications"][token]["processed"] is True
