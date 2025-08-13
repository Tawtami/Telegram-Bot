#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pytest


def test_parse_admin_filters_smoke():
    # Import and smoke-test helper exists
    from bot import _parse_admin_filters  # noqa: F401

    assert callable(_parse_admin_filters)


