#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import json
import re
import pytest


pytestmark = pytest.mark.asyncio


async def test_admin_combined_filters(monkeypatch):
    monkeypatch.setenv("PORT", "8092")
    monkeypatch.setenv("WEBHOOK_URL", "https://example.org")
    monkeypatch.setenv("ADMIN_DASHBOARD_TOKEN", "test-token")
    monkeypatch.setenv(
        "ADMIN_UI_LABELS_JSON",
        json.dumps(
            {
                "orders": "سفارش‌ها",
                "status_label": "وضعیت:",
                "type_label": "نوع:",
                "from_label": "از:",
                "to_label": "تا:",
            },
            ensure_ascii=False,
        ),
    )

    from database.db import session_scope
    from database.models_sql import User, Purchase
    from datetime import datetime, timedelta

    now = datetime.utcnow()
    with session_scope() as s:
        u = User(telegram_user_id=334455, first_name_enc="x", last_name_enc="y", phone_enc="z")
        s.add(u)
        s.flush()
        samples = [
            ("book", "bk1", "approved", now - timedelta(days=3)),
            ("book", "bk2", "approved", now - timedelta(days=2)),
            ("course", "c1", "approved", now - timedelta(days=1)),
            ("book", "bk3", "pending", now),
        ]
        for t, pid, st, ts in samples:
            s.add(Purchase(user_id=u.id, product_type=t, product_id=pid, status=st, created_at=ts))

    from bot import ApplicationBuilder, setup_handlers, run_webhook_mode
    from config import config
    from aiohttp import ClientSession

    app = ApplicationBuilder().token(config.bot_token).build()
    await setup_handlers(app)

    task = asyncio.create_task(run_webhook_mode(app))
    try:
        await asyncio.sleep(0.8)
        base = "http://0.0.0.0:8092"
        async with ClientSession() as sess:
            qs = "status=approved&type=book&from={}&to={}".format(
                (now - timedelta(days=4)).date().isoformat(),
                (now - timedelta(days=1, hours=12)).date().isoformat(),
            )
            async with sess.get(f"{base}/admin?token=test-token&{qs}") as r:
                assert r.status == 200
                html = await r.text()
                # Header labels present
                assert "وضعیت:" in html and "نوع:" in html and "از:" in html and "تا:" in html
                # Only approved books within date range (bk1, bk2)
                assert "bk1" in html and "bk2" in html
                assert "bk3" not in html and "c1" not in html
    finally:
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task


