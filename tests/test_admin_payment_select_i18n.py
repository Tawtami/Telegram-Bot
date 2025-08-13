#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import json
import re
import pytest


pytestmark = pytest.mark.asyncio


async def test_admin_payment_select_with_i18n_and_order(monkeypatch):
    monkeypatch.setenv("PORT", "8084")
    monkeypatch.setenv("WEBHOOK_URL", "https://example.org")
    monkeypatch.setenv("ADMIN_DASHBOARD_TOKEN", "test-token")
    monkeypatch.setenv("PAYMENT_METHODS", "card,cash,transfer")
    monkeypatch.setenv("DEFAULT_PAYMENT_METHOD", "transfer")
    monkeypatch.setenv("PAYMENT_PLACEHOLDER_SHOW_DEFAULT", "true")
    monkeypatch.setenv("PAYMENT_DEFAULT_FIRST", "true")
    monkeypatch.setenv(
        "PAYMENT_METHOD_LABELS_JSON",
        json.dumps(
            {"card": "کارت بانکی", "cash": "نقدی", "transfer": "کارت به کارت"},
            ensure_ascii=False,
        ),
    )
    monkeypatch.setenv(
        "ADMIN_UI_LABELS_JSON",
        json.dumps(
            {
                "admin_title": "مدیریت سفارش‌ها",
                "orders": "سفارش‌ها",
                "not_found": "موردی یافت نشد",
            },
            ensure_ascii=False,
        ),
    )

    from database.db import session_scope
    from database.models_sql import User, Purchase
    from datetime import datetime

    with session_scope() as s:
        u = User(
            telegram_user_id=111222,
            first_name_enc="x",
            last_name_enc="y",
            phone_enc="z",
        )
        s.add(u)
        s.flush()
        p = Purchase(
            user_id=u.id,
            product_type="course",
            product_id="algebra-course",
            status="pending",
            created_at=datetime.utcnow(),
        )
        s.add(p)
        s.flush()

    from bot import ApplicationBuilder, setup_handlers, run_webhook_mode
    from config import config

    app = ApplicationBuilder().token(config.bot_token).build()
    await setup_handlers(app)

    from aiohttp import ClientSession

    task = asyncio.create_task(run_webhook_mode(app))
    try:
        await asyncio.sleep(0.8)
        base = "http://127.0.0.1:8084"
        async with ClientSession() as sess:
            async with sess.get(f"{base}/admin?token=test-token") as r:
                assert r.status == 200
                html = await r.text()

        # Snapshot-like assertions on select
        # Placeholder contains default label
        assert "انتخاب روش پرداخت (پیش‌فرض: کارت به کارت)" in html

        # Options should be ordered with default first: transfer, card, cash
        m = re.search(r"<select name='payment_method'[^>]*>(.*?)</select>", html, re.S)
        assert m, "payment_method select not found"
        inner = m.group(1)
        # Ignore placeholder; check first three non-empty options
        opts = re.findall(r"<option value='([^']*)'[^>]*>([^<]*)</option>", inner)
        # First is placeholder with value ''
        assert opts[0][0] == ""
        # Next should be transfer
        assert opts[1] == ("transfer", "کارت به کارت")
        assert opts[2] == ("card", "کارت بانکی")
        assert opts[3] == ("cash", "نقدی")
    finally:
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
