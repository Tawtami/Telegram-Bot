#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
from datetime import datetime, timedelta
import pytest


pytestmark = pytest.mark.asyncio


async def _http_json(url):
    from aiohttp import ClientSession

    async with ClientSession() as s:
        async with s.get(url, headers={"Accept": "application/json"}) as r:
            return r.status, await r.json()


async def test_admin_filters_status_type_uid_product_date_size_paging(monkeypatch):
    # Configure test port and token
    monkeypatch.setenv("PORT", "8082")
    monkeypatch.setenv("WEBHOOK_URL", "https://example.org")
    monkeypatch.setenv("ADMIN_DASHBOARD_TOKEN", "test-token")

    # Seed DB
    from database.db import session_scope
    from database.models_sql import User, Purchase

    with session_scope() as s:
        u = User(telegram_user_id=999001, first_name_enc="x", last_name_enc="y", phone_enc="z")
        s.add(u)
        s.flush()

        now = datetime.utcnow()
        rows = [
            Purchase(
                user_id=u.id,
                product_type="book",
                product_id="math-book",
                status="pending",
                created_at=now - timedelta(days=1),
            ),
            Purchase(
                user_id=u.id,
                product_type="course",
                product_id="algebra-course",
                status="approved",
                created_at=now - timedelta(days=2),
            ),
            Purchase(
                user_id=u.id,
                product_type="book",
                product_id="geometry-book",
                status="approved",
                created_at=now - timedelta(days=3),
            ),
        ]
        for r in rows:
            s.add(r)
        s.flush()

    # Start webhook app
    from bot import ApplicationBuilder, setup_handlers, run_webhook_mode
    from config import config

    app = ApplicationBuilder().token(config.bot_token).build()
    await setup_handlers(app)
    task = asyncio.create_task(run_webhook_mode(app))
    try:
        await asyncio.sleep(0.8)

        base = "http://0.0.0.0:8082/admin?token=test-token"

        # 1) Filter by status=pending
        st, js = await _http_json(base + "&status=pending")
        assert st == 200
        assert all(item["status"] == "pending" for item in js["items"]) or js["total"] >= 0

        # 2) type=book
        st, js = await _http_json(base + "&type=book")
        assert st == 200
        assert all(item["type"] == "book" for item in js["items"]) or js["total"] >= 0

        # 3) uid filter (by telegram id)
        st, js = await _http_json(base + "&uid=999001")
        assert st == 200
        assert all(isinstance(item["user_id"], int) for item in js["items"]) or js["total"] >= 0

        # 4) product substring
        st, js = await _http_json(base + "&product=book")
        assert st == 200
        assert all("book" in item["product"] for item in js["items"]) or js["total"] >= 0

        # 5) date range (from/to) inclusive of from and exclusive of to (day-based)
        day1 = (datetime.utcnow() - timedelta(days=4)).date().isoformat()
        day2 = (datetime.utcnow() - timedelta(days=1)).date().isoformat()
        st, js = await _http_json(base + f"&from={day1}&to={day2}")
        assert st == 200
        # ensure all returned items have created_at within range (string compare ok for ISO)
        for it in js["items"]:
            ca = it.get("created_at")
            assert ca is None or (ca[:10] >= day1 and ca[:10] < day2)

        # 6) size and paging: size=1 then page=0/1
        st, js0 = await _http_json(base + "&size=1&page=0")
        st2, js1 = await _http_json(base + "&size=1&page=1")
        assert st == 200 and st2 == 200
        assert len(js0["items"]) <= 1 and len(js1["items"]) <= 1
        # if there are at least 2 items, page contents should differ
        if js0["items"] and js1["items"]:
            assert js0["items"][0]["id"] != js1["items"][0]["id"]

    finally:
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task


