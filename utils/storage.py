#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Any


@dataclass
class Student:
    user_id: int
    first_name: str
    last_name: str
    province: str
    city: str
    grade: str
    field: str
    free_courses: List[str] = field(default_factory=list)
    purchased_courses: List[str] = field(default_factory=list)
    book_purchases: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class StudentStorage:
    def __init__(self, json_path: str = "data/students.json") -> None:
        self.json_path = json_path
        os.makedirs(os.path.dirname(self.json_path), exist_ok=True)
        self._lock = threading.Lock()
        if not os.path.exists(self.json_path):
            with open(self.json_path, "w", encoding="utf-8") as f:
                json.dump({"students": []}, f, ensure_ascii=False, indent=2)

    def _load(self) -> Dict[str, Any]:
        try:
            with open(self.json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, dict) or "students" not in data:
                    return {"students": []}
                return data
        except (FileNotFoundError, json.JSONDecodeError):
            return {"students": []}

    def _save(self, data: Dict[str, Any]) -> None:
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_student(self, user_id: int) -> Optional[Student]:
        data = self._load()
        for s in data["students"]:
            if s.get("user_id") == user_id:
                return Student(**s)
        return None

    def upsert_student(self, student: Student) -> None:
        with self._lock:
            data = self._load()
            updated = False
            for i, s in enumerate(data["students"]):
                if s.get("user_id") == student.user_id:
                    data["students"][i] = student.to_dict()
                    updated = True
                    break
            if not updated:
                data["students"].append(student.to_dict())
            self._save(data)

    def add_free_course(self, user_id: int, course_id: str) -> None:
        with self._lock:
            data = self._load()
            for s in data["students"]:
                if s.get("user_id") == user_id:
                    courses = s.setdefault("free_courses", [])
                    if course_id not in courses:
                        courses.append(course_id)
                    self._save(data)
                    return

    def add_purchased_course(self, user_id: int, course_id: str) -> None:
        with self._lock:
            data = self._load()
            for s in data["students"]:
                if s.get("user_id") == user_id:
                    courses = s.setdefault("purchased_courses", [])
                    if course_id not in courses:
                        courses.append(course_id)
                    self._save(data)
                    return

    def add_book_purchase(self, user_id: int, purchase: Dict[str, Any]) -> None:
        with self._lock:
            data = self._load()
            for s in data["students"]:
                if s.get("user_id") == user_id:
                    purchases = s.setdefault("book_purchases", [])
                    purchases.append(purchase)
                    self._save(data)
                    return
