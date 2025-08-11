#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import List, Optional


async def notify_admins(
    context, admin_ids: List[int], text: str, parse_mode: Optional[str] = None
):
    for admin_id in admin_ids or []:
        try:
            await context.bot.send_message(
                chat_id=admin_id, text=text, parse_mode=parse_mode
            )
        except Exception:
            continue


async def send_paginated_list(
    context, admin_ids: List[int], title: str, lines: List[str], page_size: int = 50
):
    if not lines:
        await notify_admins(context, admin_ids, f"{title}\n— خالی —")
        return
    page = []
    for i, ln in enumerate(lines, 1):
        page.append(ln)
        if i % page_size == 0:
            await notify_admins(context, admin_ids, f"{title}\n" + "\n".join(page))
            page = []
    if page:
        await notify_admins(context, admin_ids, f"{title}\n" + "\n".join(page))
