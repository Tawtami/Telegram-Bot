#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Workshop utilities: provide a single source of truth for workshop months.

Primary source: data/courses.json (strict). There is no fallback; months
MUST exist in JSON for menus and dry-run to render.

To add a new workshop:
1) Add an entry in `data/courses.json` with course_id="workshop_{ماه}"
   e.g., "workshop_مهر ۱۴۰۴" and appropriate metadata.
2) `get_workshop_months()` will pick it up automatically for both the
   handler UI and dry-run generator.
3) Run `python scripts/dry_run_ui.py` and `python scripts/extract_logs.py`
   to verify menus/logs.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple
import json


MONTH_ORDER = {
    "فروردین": 1,
    "اردیبهشت": 2,
    "خرداد": 3,
    "تیر": 4,
    "مرداد": 5,
    "شهریور": 6,
    "مهر": 7,
    "آبان": 8,
    "آذر": 9,
    "دی": 10,
    "بهمن": 11,
    "اسفند": 12,
}


def _parse_month_key(month_str: str) -> Tuple[int, int]:
    """Return sort key (year, month_index) for strings like 'مهر ۱۴۰۴'."""
    try:
        parts = (month_str or "").split()
        # Expected: [month_name, year]
        name = parts[0]
        year = int(parts[1]) if len(parts) > 1 else 0
        m_idx = MONTH_ORDER.get(name, 0)
        return (year, m_idx)
    except Exception:
        return (0, 0)


def get_workshop_months(courses_json_path: str | Path = "data/courses.json") -> List[str]:
    """Extract workshop months from courses.json (strict, no fallback), sorted by year+month.

    Returns a list like ["مهر ۱۴۰۴", ..., "تیر ۱۴۰۵"]. Raises if JSON missing or empty.
    """
    p = Path(courses_json_path)
    if not p.exists():
        raise FileNotFoundError(f"courses.json not found at {p}")
    data = json.loads(p.read_text(encoding="utf-8"))
    months: List[str] = []
    for item in data if isinstance(data, list) else []:
        if not isinstance(item, dict):
            continue
        cid = (item.get("course_id") or "").strip()
        if cid.startswith("workshop_") and len(cid.split("_", 1)) == 2:
            month = cid.split("_", 1)[1]
            if month and month not in months:
                months.append(month)
    # Sort by (year, month_index)
    months.sort(key=_parse_month_key)
    if not months:
        raise ValueError("No workshop months found in courses.json")
    return months
