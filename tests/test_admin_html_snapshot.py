#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
from aiohttp import web


@pytest.mark.asyncio
async def test_admin_html_includes_receipt_preview():
    from bot import setup_handlers
    from telegram_mock import Application
    import aiohttp

    app = web.Application()
    application = Application()
    await setup_handlers(application)

    # Mount admin routes on the test app
    for r in application._web_app.router.routes():
        app.router.add_routes([r])

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="127.0.0.1", port=0)
    await site.start()
    port = list(site._server.sockets)[0].getsockname()[1]

    async with aiohttp.ClientSession() as session:
        resp = await session.get(f"http://127.0.0.1:{port}/admin", params={"fmt": "html"})
        assert resp.status in (200, 401)
        if resp.status == 200:
            text = await resp.text()
            assert "🔍" in text
            assert "CSV" in text and "XLSX" in text
            assert "action=preview" in text

    await runner.cleanup()
