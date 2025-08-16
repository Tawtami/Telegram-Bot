#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extract per-path logs from dry_run_output.txt as a fallback.
"""

from pathlib import Path
import re

src = Path("dry_run_output.txt")
if not src.exists():
    raise SystemExit("dry_run_output.txt not found. Run scripts/dry_run_ui.py first.")

s = src.read_text(encoding="utf-8")
blocks = re.findall(r"^===== (.*?) =====\n([\s\S]*?)(?=^===== |\Z)", s, flags=re.M)

work = [b for b in blocks if b[0].startswith("workshop:") or b[0] == "paid_workshops"]
sgl = [b for b in blocks if b[0].startswith("paid_single_")]


def write(name: str, arr):
    out = []
    for k, txt in arr:
        out.append(f"===== {k} =====\n")
        out.append(txt + "\n\n")
    Path(name).write_text("".join(out), encoding="utf-8")


write("dry_run_output_workshops.txt", work)
write("dry_run_output_single_lessons.txt", sgl)

print(f"workshops: {len(work)} blocks; single-lessons: {len(sgl)} blocks")
