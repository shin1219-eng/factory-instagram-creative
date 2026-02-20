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
    "04_OUTPUT/prototype",
    "04_OUTPUT/production",
    "scripts/renderpolish_c2_preview.mjs",
    "package.json",
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

    # Gate check: if C2 prompt packs exist, demo/preview must exist per date folder
    gate_missing = []
    prompt_packs = list(
        repo_root.glob(
            "04_OUTPUT/production/**/inbox/C2_InteractiveFV_*_prompt-pack.md"
        )
    )
    for pack in prompt_packs:
        date_dir = pack.parent.parent
        demo = date_dir / "demo" / "index.html"
        preview = date_dir / "preview" / "preview.png"
        if not demo.exists():
            gate_missing.append(f"{demo} (from {pack})")
        if not preview.exists():
            gate_missing.append(f"{preview} (from {pack})")

    if gate_missing:
        print("❌ Gate check failed (missing demo/preview for C2 prompt packs):")
        for m in gate_missing:
            print(f"- {m}")
        return 1

    print("✅ Structure validation PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
