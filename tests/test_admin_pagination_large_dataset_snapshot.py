#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import json
import pytest


pytestmark = pytest.mark.asyncio


async def test_admin_pagination_large_dataset(monkeypatch):
    monkeypatch.setenv("PORT", "8094")
    monkeypatch.setenv("WEBHOOK_URL", "https://example.org")
    monkeypatch.setenv("SKIP_WEBHOOK_REG", "true")
    monkeypatch.setenv("ADMIN_DASHBOARD_TOKEN", "test-token")

    from database.db import session_scope
    from database.models_sql import User, Purchase
    from datetime import datetime, timedelta

    now = datetime.utcnow()
    with session_scope() as s:
        # Use timestamp to ensure unique telegram_user_id
        timestamp = int(now.timestamp() * 1000)
        u = User(
            telegram_user_id=timestamp,
            first_name="x",
            last_name="y",
            phone="z",
        )
        s.add(u)
        s.flush()
        for i in range(120):
            s.add(
                Purchase(
                    user_id=u.id,
                    product_type="book" if i % 2 == 0 else "course",
                    product_id=f"p{i}",
                    status="pending",
                    created_at=now - timedelta(minutes=i),
                )
            )
        s.commit()

    from bot import ApplicationBuilder, setup_handlers, run_webhook_mode
    from config import config
    from aiohttp import ClientSession

    app = ApplicationBuilder().token(config.bot_token).build()
    await setup_handlers(app)

    task = asyncio.create_task(run_webhook_mode(app))
    try:
        await asyncio.sleep(0.8)
        base = "http://127.0.0.1:8094"
        async with ClientSession() as sess:
            async with sess.get(f"{base}/admin?token=test-token&page=2") as r:
                assert r.status == 200
                html = await r.text()
                assert "سفارش‌ها" in html
    finally:
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
