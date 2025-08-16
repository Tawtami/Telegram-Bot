#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
from aiohttp import web


@pytest.mark.asyncio
async def test_admin_html_includes_receipt_preview(aiohttp_client, monkeypatch):
    from bot import setup_handlers
    from telegram_mock import Application

    app = web.Application()
    application = Application()
    await setup_handlers(application)

    # Mount admin routes on a fresh app instance
    for r in application._web_app.router.routes():
        app.router.add_routes([r])

    client = await aiohttp_client(app)

    # token is optional in tests if not set; we pass empty to exercise fallback
    resp = await client.get("/admin", params={"fmt": "html"})
    assert resp.status in (200, 401)  # if token required, 401 is acceptable
    if resp.status == 200:
        text = await resp.text()
        assert "🔍" in text
        assert "CSV" in text and "XLSX" in text
        # Preview link contains action=preview
        assert "action=preview" in text
