#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import pytest


pytestmark = pytest.mark.asyncio


async def test_admin_post_approve_with_financial_fields(monkeypatch):
    # Configure test webhook and admin token
    monkeypatch.setenv("PORT", "8083")
    monkeypatch.setenv("WEBHOOK_URL", "https://example.org")
    monkeypatch.setenv("SKIP_WEBHOOK_REG", "true")
    monkeypatch.setenv("ADMIN_DASHBOARD_TOKEN", "test-token")

    # Seed DB with a pending purchase
    from database.db import session_scope
    from database.models_sql import User, Purchase
    from datetime import datetime

    with session_scope() as s:
        u = User(
            telegram_user_id=999111,
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
        pid = p.id

    from bot import ApplicationBuilder, setup_handlers, run_webhook_mode
    from config import config

    app = ApplicationBuilder().token(config.bot_token).build()
    await setup_handlers(app)

    # Use aiohttp client with cookie jar to get csrf and post
    from aiohttp import ClientSession

    task = asyncio.create_task(run_webhook_mode(app))
    try:
        await asyncio.sleep(1.5)
        base = "http://127.0.0.1:8083"

        async with ClientSession() as sess:
            # GET admin list to receive csrf cookie
            async with sess.get(f"{base}/admin?token=test-token") as r:
                assert r.status == 200
                # cookie jar stores csrf
            # extra fetch to ensure Set-Cookie processed in some aiohttp versions
            async with sess.get(f"{base}/admin?token=test-token") as r2:
                assert r2.status == 200

            # POST approve with financial fields
            form = {
                "token": "test-token",
                "id": str(pid),
                "action": "approve",
                "csrf": (sess.cookie_jar.filter_cookies(base).get("csrf") or {}).get("value", ""),
                "payment_method": "card",
                "transaction_id": "TXN-123456",
                "discount": "5000",
            }
            async with sess.post(f"{base}/admin/act", data=form) as r:
                assert r.status == 200
                js = await r.json()
                assert js.get("ok") is True
                assert js.get("id") == pid
                assert js.get("action") == "approve"

        # Verify DB state
        from sqlalchemy import select as _select

        with session_scope() as s:
            p2 = s.execute(_select(Purchase).where(Purchase.id == pid)).scalar_one()
            assert p2.status == "approved"
            assert (p2.payment_method or "").lower() == "card"
            assert p2.transaction_id == "TXN-123456"
            assert int(p2.discount or 0) == 5000

    finally:
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
