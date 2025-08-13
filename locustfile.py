#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from locust import HttpUser, task, between
import os


class BotWebhookUser(HttpUser):
    wait_time = between(0.5, 2.0)

    @task
    def health(self):
        port = os.getenv("PORT", "8080")
        self.client.get("/", name="health")


