#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import json
import re
import pytest


pytestmark = pytest.mark.asyncio


async def test_admin_filters_i18n_labels(monkeypatch):
    monkeypatch.setenv("PORT", "8085")
    monkeypatch.setenv("WEBHOOK_URL", "https://example.org")
    monkeypatch.setenv("SKIP_WEBHOOK_REG", "true")
    monkeypatch.setenv("ADMIN_DASHBOARD_TOKEN", "test-token")
    monkeypatch.setenv(
        "ADMIN_UI_LABELS_JSON",
        json.dumps(
            {
                "admin_title": "مدیریت سفارش‌ها",
                "orders": "سفارش‌ها",
                "status_label": "وضعیت:",
                "status_pending": "در انتظار",
                "status_approved": "تایید شده",
                "status_rejected": "رد شده",
                "type_label": "نوع:",
                "type_all": "همه",
                "type_course": "دوره",
                "type_book": "کتاب",
                "uid_label": "شناسه کاربر:",
                "uid_placeholder": "شناسه تلگرام",
                "product_label": "محصول:",
                "product_placeholder": "عنوان/شناسه",
                "from_label": "از:",
                "to_label": "تا:",
                "page_size_label": "سایز صفحه:",
                "filter_button": "اعمال فیلتر",
                "csv_button_label": "CSV",
                "xlsx_button_label": "XLSX",
                "results_total": "مجموع نتایج",
                "page": "صفحه",
                "th_id": "شناسه",
                "th_user": "کاربر",
                "th_type": "نوع",
                "th_product": "محصول",
                "th_created": "ایجاد",
                "th_status": "وضعیت",
                "th_action": "اقدام",
                "prev": "قبلی",
                "next": "بعدی",
                "not_found": "موردی یافت نشد",
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
        base = "http://127.0.0.1:8085"
        async with ClientSession() as sess:
            async with sess.get(f"{base}/admin?token=test-token") as r:
                assert r.status == 200
                html = await r.text()

        # Verify key labels exist
        assert "وضعیت:" in html
        assert ">در انتظار<" in html
        assert ">تایید شده<" in html
        assert ">رد شده<" in html
        assert "نوع:" in html
        assert ">همه<" in html
        assert ">دوره<" in html
        assert ">کتاب<" in html
        assert "شناسه کاربر:" in html
        assert "placeholder='شناسه تلگرام'" in html
        assert "محصول:" in html
        assert "placeholder='عنوان/شناسه'" in html
        assert "از:" in html and "تا:" in html
        assert "سایز صفحه:" in html
        assert ">اعمال فیلتر<" in html
        # Table headers
        assert "<th>شناسه</th>" in html
        assert "<th>کاربر</th>" in html
        assert "<th>نوع</th>" in html
        assert "<th>محصول</th>" in html
        assert "<th>ایجاد</th>" in html
        assert "<th>وضعیت</th>" in html
        assert "<th>اقدام</th>" in html
        # Pager
        assert ">قبلی<" in html and ">بعدی<" in html
    finally:
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
