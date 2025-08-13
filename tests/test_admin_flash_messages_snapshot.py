#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import json
import pytest


pytestmark = pytest.mark.asyncio


async def test_admin_flash_messages_i18n(monkeypatch):
    monkeypatch.setenv("PORT", "8086")
    monkeypatch.setenv("WEBHOOK_URL", "https://example.org")
    monkeypatch.setenv("ADMIN_DASHBOARD_TOKEN", "test-token")
    monkeypatch.setenv(
        "ADMIN_UI_LABELS_JSON",
        json.dumps(
            {
                "approve_button": "تایید",
                "reject_button": "رد",
                "flash_approve_success": "با موفقیت تایید شد.",
                "flash_reject_success": "با موفقیت رد شد.",
                "flash_error": "خطا در انجام عملیات",
            },
            ensure_ascii=False,
        ),
    )

    from database.db import session_scope
    from database.models_sql import User, Purchase
    from datetime import datetime

    with session_scope() as s:
        u = User(
            telegram_user_id=919293,
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

    from aiohttp import ClientSession

    task = asyncio.create_task(run_webhook_mode(app))
    try:
        await asyncio.sleep(0.8)
        base = "http://0.0.0.0:8086"
        async with ClientSession() as sess:
            # First GET to set csrf
            async with sess.get(f"{base}/admin?token=test-token") as r:
                assert r.status == 200
                csrf = sess.cookie_jar.filter_cookies(base).get("csrf").value

            # Approve to trigger success flash
            form = {
                "token": "test-token",
                "id": str(pid),
                "action": "approve",
                "csrf": csrf,
                "redirect": f"/admin?token=test-token",
            }
            async with sess.post(f"{base}/admin/act", data=form) as r:
                # Redirect sets flash cookies (captured by cookie jar)
                assert r.status in (200, 303, 302)

            # Now GET again should render flash text
            async with sess.get(f"{base}/admin?token=test-token") as r:
                assert r.status == 200
                html = await r.text()
                assert "با موفقیت تایید شد." in html

    finally:
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

async def test_admin_flash_messages_reject_i18n(monkeypatch):
    monkeypatch.setenv("PORT", "8087")
    monkeypatch.setenv("WEBHOOK_URL", "https://example.org")
    monkeypatch.setenv("ADMIN_DASHBOARD_TOKEN", "test-token")
    monkeypatch.setenv(
        "ADMIN_UI_LABELS_JSON",
        json.dumps(
            {
                "approve_button": "تایید",
                "reject_button": "رد",
                "flash_approve_success": "با موفقیت تایید شد.",
                "flash_reject_success": "با موفقیت رد شد.",
                "flash_error": "خطا در انجام عملیات",
            },
            ensure_ascii=False,
        ),
    )

    from database.db import session_scope
    from database.models_sql import User, Purchase
    from datetime import datetime

    with session_scope() as s:
        u = User(
            telegram_user_id=919294,
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

    from aiohttp import ClientSession

    task = asyncio.create_task(run_webhook_mode(app))
    try:
        await asyncio.sleep(0.8)
        base = "http://0.0.0.0:8087"
        async with ClientSession() as sess:
            # First GET to set csrf
            async with sess.get(f"{base}/admin?token=test-token") as r:
                assert r.status == 200
                csrf = sess.cookie_jar.filter_cookies(base).get("csrf").value

            # Reject to trigger success flash
            form = {
                "token": "test-token",
                "id": str(pid),
                "action": "reject",
                "csrf": csrf,
                "redirect": f"/admin?token=test-token",
            }
            async with sess.post(f"{base}/admin/act", data=form) as r:
                assert r.status in (200, 303, 302)

            # Now GET again should render flash text
            async with sess.get(f"{base}/admin?token=test-token") as r:
                assert r.status == 200
                html = await r.text()
                assert "با موفقیت رد شد." in html

    finally:
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
