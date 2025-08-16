#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys


def test_dry_run_structure_counts():
    # Ensure dry run has been executed before running this test
    # We only assert structure counts to avoid brittle text snapshots.
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    dr = os.path.join(root, "dry_run_output.txt")
    assert os.path.exists(dr), "Run scripts/dry_run_ui.py first"
    s = open(dr, "r", encoding="utf-8").read()
    # Count workshop blocks (parent + 10 months)
    workshops_parent = s.count("===== paid_workshops =====")
    workshop_months = s.count("===== workshop:")
    assert workshops_parent == 1 and workshop_months == 10
    # Count single lessons
    single_blocks = sum(
        s.count(x)
        for x in [
            "===== paid_single_exp_math1 =====",
            "===== paid_single_exp_math2 =====",
            "===== paid_single_exp_math3 =====",
            "===== paid_single_math_math1 =====",
            "===== paid_single_math_hesa1 =====",
            "===== paid_single_math_hesa2 =====",
            "===== paid_single_math_dis3 =====",
            "===== paid_single_math_geo3 =====",
        ]
    )
    assert single_blocks == 8
