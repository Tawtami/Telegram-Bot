#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
from aiohttp import web


@pytest.mark.asyncio
async def test_admin_html_includes_receipt_preview():
    from bot import setup_handlers

    # Use the mock Application provided by telegram_mock via import side-effects
    from telegram_mock import MagicMock

    Application = MagicMock
    from aiohttp.test_utils import TestServer, TestClient

    app = web.Application()
    application = Application()
    await setup_handlers(application)

    # Mount admin routes on the test app
    for r in application._web_app.router.routes():
        app.router.add_routes([r])

    server = TestServer(app)
    await server.start_server()
    client = TestClient(server)
    await client.start_server()

    resp = await client.get("/admin", params={"fmt": "html"})
    assert resp.status in (200, 401)
    if resp.status == 200:
        text = await resp.text()
        assert "🔍" in text
        assert "CSV" in text and "XLSX" in text
        assert "action=preview" in text

    await client.close()
    await server.close()
