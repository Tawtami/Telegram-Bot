#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON -> SQL migration script (skeleton)
Usage:
  python scripts/json_to_db.py --dry-run
  python scripts/json_to_db.py
"""

import argparse
import json
from pathlib import Path

from database.db import session_scope
from database.service import get_or_create_user


def run(dry_run: bool = True):
    students_file = Path("data/students.json")
    if not students_file.exists():
        print("students.json not found; skipping")
        return
    data = json.loads(students_file.read_text(encoding="utf-8")) or {}
    students = data.get("students", [])
    count = 0
    for s in students:
        if dry_run:
            count += 1
            continue
        with session_scope() as session:
            get_or_create_user(
                session,
                telegram_user_id=int(s.get("user_id")),
                first_name=s.get("first_name"),
                last_name=s.get("last_name"),
                phone=s.get("phone_number"),
                province=s.get("province"),
                city=s.get("city"),
                grade=s.get("grade"),
                field_of_study=s.get("field"),
            )
        count += 1
    print(("Dry-run: " if dry_run else "Migrated: ") + str(count))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    run(dry_run=args.dry_run)
