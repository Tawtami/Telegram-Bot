#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dry run UI renderer: invokes handlers to produce representative texts
for menus/submenus without hitting Telegram network.
"""

import asyncio
from types import SimpleNamespace
from typing import cast, Any

# Ensure telegram mocks are loaded
import sys, os, types

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import telegram_mock  # noqa: F401
import sqlalchemy_mock  # noqa: F401

# Loosen rate limiting for dry-run so all paths render in one go
os.environ.setdefault("MAX_REQUESTS_PER_MINUTE", "1000")

# Inject minimal DB/service stubs to bypass real DB deps before importing handlers
fake_db = types.ModuleType('database.db')
from contextlib import contextmanager


@contextmanager
def _noop_session_scope():
    yield SimpleNamespace()


# Help static type checkers recognize dynamically injected attributes
setattr(fake_db, 'session_scope', cast(Any, _noop_session_scope))
sys.modules['database.db'] = fake_db

fake_service = types.ModuleType('database.service')
for name in [
    'get_or_create_user',
    'create_purchase',
    'get_course_participants_by_slug',
    'get_daily_question',
    'submit_answer',
    'approve_or_reject_purchase',
    'get_pending_purchases',
]:
    setattr(fake_service, name, lambda *a, **k: None)
sys.modules['database.service'] = fake_service

fake_models = types.ModuleType('database.models_sql')


class _Dummy:
    pass


setattr(fake_models, 'User', cast(Any, _Dummy))
setattr(fake_models, 'Purchase', cast(Any, _Dummy))
sys.modules['database.models_sql'] = fake_models

from handlers.courses import (
    handle_paid_menu,
    handle_paid_single,
    handle_paid_single_select,
    handle_paid_private,
    handle_paid_comprehensive,
    handle_paid_comp_select,
    handle_paid_workshops,
    handle_workshop_select,
)


class DummyMsg:
    def __init__(self):
        self.texts = []
        self.markups = []

    async def reply_text(self, text, reply_markup=None, **kwargs):
        self.texts.append(text)
        self.markups.append(reply_markup)


OUTPUTS = []


class DummyQuery:
    def __init__(self, data):
        self.data = data
        self.from_user = SimpleNamespace(id=123)

    async def answer(self, *args, **kwargs):
        return

    async def edit_message_text(self, text, reply_markup=None, **kwargs):
        btns = []
        if reply_markup and getattr(reply_markup, "inline_keyboard", None):
            btns = [
                [getattr(btn, "text", "?") for btn in row] for row in reply_markup.inline_keyboard
            ]
        OUTPUTS.append({"key": self.data, "text": text, "buttons": btns})


class DummyUpdate:
    def __init__(self, data):
        self.callback_query = DummyQuery(data)
        self.effective_message = DummyMsg()
        self.effective_user = SimpleNamespace(id=123)


class DummyContext:
    def __init__(self):
        self.user_data = {}


async def run():
    ctx = DummyContext()
    # Paid menu
    await handle_paid_menu(DummyUpdate("paid_menu"), ctx)
    # Single lesson menu
    await handle_paid_single(DummyUpdate("paid_single"), ctx)
    # Single lesson selections
    for key in [
        "paid_single_exp_math1",
        "paid_single_exp_math2",
        "paid_single_exp_math3",
        "paid_single_math_math1",
        "paid_single_math_hesa1",
        "paid_single_math_hesa2",
        "paid_single_math_dis3",
        "paid_single_math_geo3",
    ]:
        await handle_paid_single_select(DummyUpdate(key), ctx)

    # Private
    await handle_paid_private(DummyUpdate("paid_private"), ctx)

    # Comprehensive menu and selections
    await handle_paid_comprehensive(DummyUpdate("paid_comprehensive"), ctx)
    for key in ["paid_comp_exp", "paid_comp_math"]:
        await handle_paid_comp_select(DummyUpdate(key), ctx)

    # Workshops menu and one selection per month
    await handle_paid_workshops(DummyUpdate("paid_workshops"), ctx)
    from utils.workshops import get_workshop_months

    for month in get_workshop_months():
        await handle_workshop_select(DummyUpdate(f"workshop:{month}"), ctx)

    # Write outputs to file in UTF-8
    from pathlib import Path

    lines = []
    for item in OUTPUTS:
        lines.append(f"===== {item['key']} =====\n")
        lines.append(item['text'] + "\n")
        if item['buttons']:
            lines.append(
                "[Buttons] " + ", ".join([" | ".join(row) for row in item['buttons']]) + "\n\n"
            )
        else:
            lines.append("\n")
    Path("dry_run_output.txt").write_text("".join(lines), encoding="utf-8")

    # Also split per-path outputs for faster review
    buckets = {
        "courses": ["paid_menu", "paid_single", "paid_private"],
        "comprehensive": ["paid_comprehensive", "paid_comp_exp", "paid_comp_math"],
        "single_lessons": [
            "paid_single_exp_math1",
            "paid_single_exp_math2",
            "paid_single_exp_math3",
            "paid_single_math_math1",
            "paid_single_math_hesa1",
            "paid_single_math_hesa2",
            "paid_single_math_dis3",
            "paid_single_math_geo3",
        ],
        "workshops": ["paid_workshops"],
    }
    # Add dynamic workshop selections
    for m in get_workshop_months():
        buckets["workshops"].append(f"workshop:{m}")

    for name, keys in buckets.items():
        out_lines = []
        for item in OUTPUTS:
            if item["key"] in keys:
                out_lines.append(f"===== {item['key']} =====\n")
                out_lines.append(item["text"] + "\n")
                if item["buttons"]:
                    out_lines.append(
                        "[Buttons] "
                        + ", ".join([" | ".join(row) for row in item["buttons"]])
                        + "\n\n"
                    )
                else:
                    out_lines.append("\n")
        Path(f"dry_run_output_{name}.txt").write_text("".join(out_lines), encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(run())
