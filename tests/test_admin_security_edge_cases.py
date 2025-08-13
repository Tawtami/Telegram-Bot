#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import pytest


pytestmark = pytest.mark.asyncio


async def test_admin_requires_valid_token(monkeypatch):
    monkeypatch.setenv("PORT", "8093")
    monkeypatch.setenv("WEBHOOK_URL", "https://example.org")
    monkeypatch.setenv("ADMIN_DASHBOARD_TOKEN", "valid-token")

    from bot import ApplicationBuilder, setup_handlers, run_webhook_mode
    from config import config
    from aiohttp import ClientSession

    app = ApplicationBuilder().token(config.bot_token).build()
    await setup_handlers(app)

    task = asyncio.create_task(run_webhook_mode(app))
    try:
        await asyncio.sleep(0.8)
        base = "http://0.0.0.0:8093"
        async with ClientSession() as sess:
            async with sess.get(f"{base}/admin?token=wrong") as r:
                assert r.status == 401
    finally:
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task


async def test_admin_act_post_bad_request(monkeypatch):
    monkeypatch.setenv("PORT", "8094")
    monkeypatch.setenv("WEBHOOK_URL", "https://example.org")
    monkeypatch.setenv("ADMIN_DASHBOARD_TOKEN", "tkn")

    from bot import ApplicationBuilder, setup_handlers, run_webhook_mode
    from config import config
    from aiohttp import ClientSession

    app = ApplicationBuilder().token(config.bot_token).build()
    await setup_handlers(app)

    task = asyncio.create_task(run_webhook_mode(app))
    try:
        await asyncio.sleep(0.8)
        base = "http://0.0.0.0:8094"
        async with ClientSession() as sess:
            # First GET to set csrf
            async with sess.get(f"{base}/admin?token=tkn") as r:
                assert r.status == 200
                csrf = sess.cookie_jar.filter_cookies(base).get("csrf").value
            # Bad id and invalid action
            form = {
                "token": "tkn",
                "id": "not-int",
                "action": "invalid",
                "csrf": csrf,
            }
            async with sess.post(f"{base}/admin/act", data=form) as r:
                # Either invalid id or action should trigger 400
                assert r.status == 400
    finally:
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task


async def test_admin_act_post_csrf_mismatch(monkeypatch):
    monkeypatch.setenv("PORT", "8095")
    monkeypatch.setenv("WEBHOOK_URL", "https://example.org")
    monkeypatch.setenv("ADMIN_DASHBOARD_TOKEN", "tkn")

    # Seed a pending purchase
    from database.db import session_scope
    from database.models_sql import User, Purchase
    from datetime import datetime

    with session_scope() as s:
        u = User(telegram_user_id=123999, first_name_enc="x", last_name_enc="y", phone_enc="z")
        s.add(u)
        s.flush()
        p = Purchase(
            user_id=u.id,
            product_type="course",
            product_id="csrf-course",
            status="pending",
            created_at=datetime.utcnow(),
        )
        s.add(p)
        s.flush()
        pid = p.id

    from bot import ApplicationBuilder, setup_handlers, run_webhook_mode
    from config import config
    from sqlalchemy import select as _select
    from aiohttp import ClientSession

    app = ApplicationBuilder().token(config.bot_token).build()
    await setup_handlers(app)

    task = asyncio.create_task(run_webhook_mode(app))
    try:
        await asyncio.sleep(0.8)
        base = "http://0.0.0.0:8095"
        async with ClientSession() as sess:
            # GET to set csrf cookie, but then use a wrong csrf on purpose
            async with sess.get(f"{base}/admin?token=tkn") as r:
                assert r.status == 200
            form = {
                "token": "tkn",
                "id": str(pid),
                "action": "approve",
                "csrf": "WRONG-CSRF",
            }
            async with sess.post(f"{base}/admin/act", data=form) as r:
                assert r.status == 403

        # Verify DB state unchanged
        with session_scope() as s:
            p2 = s.execute(_select(Purchase).where(Purchase.id == pid)).scalar_one()
            assert p2.status == "pending"
            assert (p2.payment_method or None) is None
            assert (p2.transaction_id or None) is None
    finally:
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task


