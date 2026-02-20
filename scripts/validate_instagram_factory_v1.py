#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
from pathlib import Path
import sys


REQUIRED_PATHS = [
    "AGENTS.md",
    "00_README/Purpose.md",
    "00_README/HowToRun.md",
    "01_RULES/Design-DNA.md",
    "01_RULES/Copy-Voice.md",
    "01_RULES/Guardrails.md",
    "01_RULES/Rubric.md",
    "01_RULES/TrendSources.md",
    "02_BRIEFS/TrendScan-Brief.md",
    "02_BRIEFS/Unit-Brief-3DTeaser.md",
    "02_BRIEFS/Unit-Brief-InteractiveFV.md",
    "02_BRIEFS/Unit-Brief-ExplainSlide.md",
    ".agents/skills/_shared/CONVENTIONS.md",
    ".agents/skills/S1_TrendScan/SKILL.md",
    ".agents/skills/S2_AxisSelect/SKILL.md",
    ".agents/skills/S3_UnitProduce/SKILL.md",
    ".agents/skills/S4_QA/SKILL.md",
    ".agents/skills/S5_ShipAndStore/SKILL.md",
    ".agents/skills/S6_RenderPolish/SKILL.md",
    "05_LOGS/runs",
    "04_OUTPUT",
    "04_OUTPUT/.gitkeep",
    "04_OUTPUT/prototype/.gitkeep",
    "04_OUTPUT/production/.gitkeep",
    "04_OUTPUT/approved/latest/.gitkeep",
    "scripts/renderpolish_c1_kv.mjs",
    "scripts/renderpolish_c2_preview.mjs",
]


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    missing = []
    for p in REQUIRED_PATHS:
        if not (repo_root / p).exists():
            missing.append(p)

    if missing:
        print("❌ Missing required paths:")
        for m in missing:
            print(f"- {m}")
        return 1

    print("✅ Structure validation PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
