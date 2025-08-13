#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import json
import re
import pytest


pytestmark = pytest.mark.asyncio


async def test_admin_pagination_labels_and_links(monkeypatch):
    monkeypatch.setenv("PORT", "8089")
    monkeypatch.setenv("WEBHOOK_URL", "https://example.org")
    monkeypatch.setenv("ADMIN_DASHBOARD_TOKEN", "test-token")
    monkeypatch.setenv(
        "ADMIN_UI_LABELS_JSON",
        json.dumps(
            {
                "results_total": "مجموع نتایج",
                "page": "صفحه",
                "prev": "قبلی",
                "next": "بعدی",
                "csv_button_label": "CSV",
                "xlsx_button_label": "XLSX",
            },
            ensure_ascii=False,
        ),
    )

    from database.db import session_scope
    from database.models_sql import User, Purchase
    from datetime import datetime, timedelta

    with session_scope() as s:
        u = User(telegram_user_id=555666, first_name_enc="x", last_name_enc="y", phone_enc="z")
        s.add(u)
        s.flush()
        now = datetime.utcnow()
        for i in range(12):
            s.add(
                Purchase(
                    user_id=u.id,
                    product_type="course",
                    product_id=f"pg-{i+1}",
                    status="pending",
                    created_at=now - timedelta(minutes=i),
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
        base = "http://0.0.0.0:8089"
        async with ClientSession() as sess:
            async with sess.get(f"{base}/admin?token=test-token&size=5&page=0") as r:
                assert r.status == 200
                html = await r.text()
                assert "مجموع نتایج:" in html
                assert "صفحه: 1" in html
                assert ">قبلی<" in html and ">بعدی<" in html
                assert "format=csv" in html
                assert "format=xlsx" in html

            async with sess.get(f"{base}/admin?token=test-token&size=5&page=1") as r:
                assert r.status == 200
                html = await r.text()
                assert "صفحه: 2" in html
                assert ">قبلی<" in html and ">بعدی<" in html
    finally:
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task


async def test_admin_export_links_with_filters(monkeypatch):
    monkeypatch.setenv("PORT", "8090")
    monkeypatch.setenv("WEBHOOK_URL", "https://example.org")
    monkeypatch.setenv("ADMIN_DASHBOARD_TOKEN", "test-token")
    monkeypatch.setenv(
        "ADMIN_UI_LABELS_JSON",
        json.dumps(
            {
                "csv_button_label": "CSV",
                "xlsx_button_label": "XLSX",
            },
            ensure_ascii=False,
        ),
    )

    from bot import ApplicationBuilder, setup_handlers, run_webhook_mode
    from config import config
    from aiohttp import ClientSession

    app = ApplicationBuilder().token(config.bot_token).build()
    await setup_handlers(app)

    task = asyncio.create_task(run_webhook_mode(app))
    try:
        await asyncio.sleep(0.8)
        base = "http://0.0.0.0:8090"
        async with ClientSession() as sess:
            async with sess.get(f"{base}/admin?token=test-token&status=approved&type=book&size=7&page=0") as r:
                assert r.status == 200
                html = await r.text()
                # Find export links
                csv_links = re.findall(r"href='([^']*?)'[^>]*>CSV<", html)
                xlsx_links = re.findall(r"href='([^']*?)'[^>]*>XLSX<", html)
                assert csv_links, "CSV link not found"
                assert xlsx_links, "XLSX link not found"
                for href in csv_links + xlsx_links:
                    assert "status=approved" in href
                    assert "type=book" in href
                    assert "page=0" in href
                    assert ("format=csv" in href) or ("format=xlsx" in href)
    finally:
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task


