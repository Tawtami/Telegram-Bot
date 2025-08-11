#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple migration bootstrap: create tables if not exist.
For production use Alembic; this provides a quick start.
"""

from database.db import ENGINE, Base
from database.models_sql import *  # noqa


def init_db():
    Base.metadata.create_all(ENGINE)


if __name__ == "__main__":
    init_db()
    print("DB initialized.")


