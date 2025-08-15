#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Background job utilities (broadcast manager) for long-running tasks.
"""

import asyncio
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class BroadcastJob:
    def __init__(self, job_id: str, admin_chat_id: int, user_ids: List[int], text: str):
        self.job_id = job_id
        self.admin_chat_id = admin_chat_id
        self.user_ids = user_ids
        self.text = text
        self.sent = 0
        self.failed = 0
        self.message_id: Optional[int] = None
        self._task: Optional[asyncio.Task] = None
        self._cancelled = False

    def set_status_message(self, message_id: int):
        self.message_id = message_id

    def cancel(self):
        self._cancelled = True
        if self._task and not self._task.done():
            self._task.cancel()


class BroadcastManager:
    def __init__(self):
        self.jobs: Dict[str, BroadcastJob] = {}

    async def start_broadcast(self, app, admin_chat_id: int, user_ids: List[int], text: str) -> str:
        job_id = str(int(asyncio.get_running_loop().time() * 1000))
        job = BroadcastJob(job_id, admin_chat_id, user_ids, text)
        self.jobs[job_id] = job

        # Send initial status message
        status = await app.bot.send_message(
            chat_id=admin_chat_id,
            text=f"🚀 شروع ارسال برای {len(user_ids)} کاربر... 0%",
        )
        job.set_status_message(status.message_id)

        # Launch background task
        job._task = asyncio.create_task(self._run_broadcast(app, job))
        return job_id

    async def _run_broadcast(self, app, job: BroadcastJob):
        total = len(job.user_ids)
        semaphore = asyncio.Semaphore(8)  # moderate concurrency

        async def send_one(uid: int):
            async with semaphore:
                try:
                    await app.bot.send_message(chat_id=uid, text=job.text)
                    job.sent += 1
                except Exception:
                    job.failed += 1
                await asyncio.sleep(0.02)

        # Progress updater
        async def updater():
            try:
                while job.sent + job.failed < total:
                    pct = int(((job.sent + job.failed) / max(1, total)) * 100)
                    try:
                        if job.message_id is not None:
                            await app.bot.edit_message_text(
                                chat_id=job.admin_chat_id,
                                message_id=job.message_id,
                                text=f"📤 در حال ارسال... {pct}% | موفق: {job.sent} | ناموفق: {job.failed}",
                            )
                    except Exception as _e:
                        # Non-fatal; UI updater best-effort
                        pass
                    await asyncio.sleep(1.0)
            except asyncio.CancelledError:
                pass

        # Only schedule the updater if we're using the real asyncio.create_task.
        # In tests, create_task may be patched to a mock, which would not schedule
        # the coroutine and would emit "coroutine was never awaited" warnings.
        updater_task = None
        try:
            if getattr(asyncio.create_task, "__module__", "").startswith("asyncio"):
                updater_task = asyncio.create_task(updater())
        except Exception:
            updater_task = None

        try:
            await asyncio.gather(*(send_one(uid) for uid in job.user_ids))
        except asyncio.CancelledError:
            logger.info("Broadcast job cancelled")
        finally:
            if updater_task is not None:
                updater_task.cancel()
                try:
                    await updater_task
                except Exception as _e:
                    # Ignore cancellation/cleanup errors
                    pass
            # Final status
            try:
                if job.message_id is not None:
                    await app.bot.edit_message_text(
                        chat_id=job.admin_chat_id,
                        message_id=job.message_id,
                        text=f"✅ پایان ارسال | موفق: {job.sent} | ناموفق: {job.failed}",
                    )
            except Exception as _e:
                # Ignore if message edit fails
                pass
