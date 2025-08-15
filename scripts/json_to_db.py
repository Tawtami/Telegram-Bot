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
import logging
from pathlib import Path

from database.db import session_scope
from database.service import get_or_create_user
from database.models_sql import QuizQuestion
from sqlalchemy import select


def run(dry_run: bool = True):
    students_file = Path("data/students.json")
    if not students_file.exists():
        logging.getLogger(__name__).warning("students.json not found; skipping")
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
    logging.getLogger(__name__).info(("Dry-run: " if dry_run else "Migrated: ") + str(count))


def seed_quiz_from_json(json_path: str) -> int:
    data = json.loads(Path(json_path).read_text(encoding="utf-8"))
    rows = data if isinstance(data, list) else data.get("questions", [])
    inserted = 0
    with session_scope() as session:
        for row in rows:
            try:
                grade = row.get("grade") or "دهم"
                difficulty = int(row.get("difficulty") or 1)
                question_text = (row.get("question_text") or "").strip()
                choices = row.get("choices") or []
                correct_index = int(row.get("correct_index") or 0)
                if not question_text or not choices:
                    continue
                exists = (
                    session.execute(
                        select(QuizQuestion).where(
                            QuizQuestion.grade == grade,
                            QuizQuestion.question_text == question_text,
                        )
                    )
                    .scalars()
                    .first()
                )
                if exists:
                    continue
                session.add(
                    QuizQuestion(
                        grade=grade,
                        difficulty=difficulty,
                        question_text=question_text,
                        options={"choices": choices},
                        correct_index=correct_index,
                    )
                )
                inserted += 1
            except Exception:
                continue
    return inserted


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--seed-quiz", type=str, help="path to quiz json file")
    args = ap.parse_args()
    if args.seed_quiz:
        n = seed_quiz_from_json(args.seed_quiz)
        logging.getLogger(__name__).info(f"Inserted {n} quiz questions")
    else:
        run(dry_run=args.dry_run)
