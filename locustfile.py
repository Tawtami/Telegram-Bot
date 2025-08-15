#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os

try:
    from locust import HttpUser, task, between  # type: ignore
except Exception:  # Fallback when locust isn't installed (used in CI mocks)

    class HttpUser:
        client = type("Client", (), {"get": lambda self, *a, **k: None})()

    def task(func=None):
        def _decorator(f):
            return f

        return _decorator(func) if func else _decorator

    def between(a, b):  # noqa: N802 - keep locust API shape
        return (a, b)


class BotWebhookUser(HttpUser):
    wait_time = between(0.5, 2.0)

    @task
    def health(self):
        port = os.getenv("PORT", "8080")
        self.client.get("/", name="health")
