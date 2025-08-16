#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pytest


pytestmark = pytest.mark.asyncio


async def test_admin_payment_select_i18n(monkeypatch):
    monkeypatch.setenv("PORT", "8090")
    monkeypatch.setenv("WEBHOOK_URL", "https://example.org")
    monkeypatch.setenv("SKIP_WEBHOOK_REG", "true")
    monkeypatch.setenv("ADMIN_DASHBOARD_TOKEN", "test-token")

    from database.db import session_scope
    from database.models_sql import User, Purchase

    with session_scope() as s:
        u = User(telegram_user_id=111111118, first_name="x", last_name="y", phone="z")
        s.add(u)
        s.flush()
        s.add(Purchase(user_id=u.id, product_type="book", product_id="bk1", status="pending"))
        s.commit()

    from bot import ApplicationBuilder, setup_handlers, run_webhook_mode
    from config import config

    app = ApplicationBuilder().token(config.bot_token).build()
    await setup_handlers(app)

    import asyncio
    from aiohttp import ClientSession

    task = asyncio.create_task(run_webhook_mode(app))
    try:
        await asyncio.sleep(0.8)
        base = "http://127.0.0.1:8090"
        async with ClientSession() as sess:
            async with sess.get(f"{base}/admin?token=test-token") as r:
                assert r.status == 200
                html = await r.text()
                assert "پرداخت" in html or "payment" in html
    finally:
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
