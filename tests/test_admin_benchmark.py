#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import os
import time
import statistics
import pytest


pytestmark = pytest.mark.asyncio


async def test_admin_benchmark_optional(monkeypatch):
    # Run only if explicitly enabled to avoid CI flakiness
    if os.getenv("RUN_BENCHMARKS", "false").lower() != "true":
        pytest.skip("benchmarks disabled; set RUN_BENCHMARKS=true to enable")

    monkeypatch.setenv("PORT", "8096")
    monkeypatch.setenv("WEBHOOK_URL", "https://example.org")
    monkeypatch.setenv("ADMIN_DASHBOARD_TOKEN", "bench-token")

    from database.db import session_scope
    from database.models_sql import User, Purchase
    from datetime import datetime, timedelta

    # Seed large-ish dataset
    with session_scope() as s:
        u = User(telegram_user_id=445566, first_name_enc="x", last_name_enc="y", phone_enc="z")
        s.add(u)
        s.flush()
        now = datetime.utcnow()
        for i in range(1000):
            s.add(
                Purchase(
                    user_id=u.id,
                    product_type=("book" if i % 2 == 0 else "course"),
                    product_id=f"bench-{i}",
                    status=("approved" if i % 3 == 0 else "pending"),
                    created_at=now - timedelta(seconds=i),
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
        base = "http://0.0.0.0:8096"
        runs = []
        async with ClientSession() as sess:
            for size in (10, 25, 50):
                for page in (0, 5, 10):
                    t0 = time.perf_counter()
                    async with sess.get(
                        f"{base}/admin?token=bench-token&status=pending&type=book&size={size}&page={page}"
                    ) as r:
                        assert r.status == 200
                        await r.text()
                    runs.append(time.perf_counter() - t0)

        # Basic sanity thresholds (tunable). We just assert no huge outliers.
        p95 = statistics.quantiles(runs, n=20)[18]
        assert p95 < 1.5, f"admin list p95 too slow: {p95:.3f}s"
    finally:
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task


