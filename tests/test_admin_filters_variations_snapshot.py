#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import json
import re
import pytest


pytestmark = pytest.mark.asyncio


async def test_admin_filters_status_and_type(monkeypatch):
    monkeypatch.setenv("PORT", "8088")
    monkeypatch.setenv("WEBHOOK_URL", "https://example.org")
    monkeypatch.setenv("SKIP_WEBHOOK_REG", "true")
    monkeypatch.setenv("ADMIN_DASHBOARD_TOKEN", "test-token")
    monkeypatch.setenv(
        "ADMIN_UI_LABELS_JSON",
        json.dumps(
            {
                "orders": "سفارش‌ها",
                "status_label": "وضعیت:",
                "type_label": "نوع:",
                "type_course": "دوره",
                "type_book": "کتاب",
                "results_total": "مجموع نتایج",
                "page": "صفحه",
            },
            ensure_ascii=False,
        ),
    )

    from database.db import session_scope
    from database.models_sql import User, Purchase
    from datetime import datetime, timedelta

    # Seed a mix of purchases
    with session_scope() as s:
        # Use timestamp to ensure unique telegram_user_id
        import time

        timestamp = int(time.time() * 1000)
        u = User(
            telegram_user_id=timestamp,
            first_name_enc="x",
            last_name_enc="y",
            phone_enc="z",
        )
        s.add(u)
        s.flush()
        now = datetime.utcnow()
        samples = [
            ("course", "math-1", "pending", now),
            ("book", "bk-1", "approved", now - timedelta(days=1)),
            ("course", "math-2", "rejected", now - timedelta(days=2)),
        ]
        for t, pid, st, ts in samples:
            s.add(
                Purchase(
                    user_id=u.id,
                    product_type=t,
                    product_id=pid,
                    status=st,
                    created_at=ts,
                )
            )

    from bot import ApplicationBuilder, setup_handlers, run_webhook_mode
    from config import config
    from aiohttp import ClientSession

    app = ApplicationBuilder().token(config.bot_token).build()
    await setup_handlers(app)

    task = asyncio.create_task(run_webhook_mode(app))
    try:
        await asyncio.sleep(0.8)
        base = "http://127.0.0.1:8088"
        async with ClientSession() as sess:
            # Filter approved
            async with sess.get(f"{base}/admin?token=test-token&status=approved") as r:
                assert r.status == 200
                html = await r.text()
                assert "سفارش‌ها (approved)" in html
                # Table should contain approved row
                assert "approved" in html

            # Filter type=book
            async with sess.get(f"{base}/admin?token=test-token&type=book") as r:
                assert r.status == 200
                html = await r.text()
                # Header exists
                assert "نوع:" in html
                # Contains book entries
                assert "book" in html

    finally:
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
