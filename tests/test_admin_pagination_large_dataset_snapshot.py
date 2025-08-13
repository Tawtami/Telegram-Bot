#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import json
import pytest


pytestmark = pytest.mark.asyncio


async def test_admin_pagination_large_dataset(monkeypatch):
    monkeypatch.setenv("PORT", "8091")
    monkeypatch.setenv("WEBHOOK_URL", "https://example.org")
    monkeypatch.setenv("ADMIN_DASHBOARD_TOKEN", "test-token")
    monkeypatch.setenv(
        "ADMIN_UI_LABELS_JSON",
        json.dumps({"results_total": "مجموع نتایج", "page": "صفحه", "prev": "قبلی", "next": "بعدی"}, ensure_ascii=False),
    )

    from database.db import session_scope
    from database.models_sql import User, Purchase
    from datetime import datetime, timedelta

    with session_scope() as s:
        u = User(telegram_user_id=112233, first_name_enc="x", last_name_enc="y", phone_enc="z")
        s.add(u)
        s.flush()
        now = datetime.utcnow()
        for i in range(51):
            s.add(Purchase(user_id=u.id, product_type="course", product_id=f"L{i+1}", status="pending", created_at=now - timedelta(seconds=i)))

    from bot import ApplicationBuilder, setup_handlers, run_webhook_mode
    from config import config
    from aiohttp import ClientSession

    app = ApplicationBuilder().token(config.bot_token).build()
    await setup_handlers(app)

    task = asyncio.create_task(run_webhook_mode(app))
    try:
        await asyncio.sleep(0.8)
        base = "http://0.0.0.0:8091"
        async with ClientSession() as sess:
            async with sess.get(f"{base}/admin?token=test-token&size=10&page=0") as r:
                assert r.status == 200
                html = await r.text()
                assert "مجموع نتایج: 51" in html
                assert "صفحه: 1" in html
                assert ">قبلی<" in html and ">بعدی<" in html

            async with sess.get(f"{base}/admin?token=test-token&size=10&page=5") as r:
                assert r.status == 200
                html = await r.text()
                assert "صفحه: 6" in html
                assert ">قبلی<" in html and ">بعدی<" in html
    finally:
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task


