#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
from pathlib import Path
import sys
import re


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
    "02_BRIEFS/Unit-Brief-HP.md",
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
    "scripts/renderpolish_preview.mjs",
    "vendor/three/three.min.js",
]


RUN_PATTERN = re.compile(r"^(\d{4}-\d{2}-\d{2})_run_(\d+)\.md$")


def parse_meta(html_text: str, name: str) -> str | None:
    match = re.search(rf'<meta\s+name=\"{re.escape(name)}\"\s+content=\"([^\"]+)\"\s*/?>', html_text)
    if match:
        return match.group(1).strip()
    return None


def find_latest_production(root: Path) -> Path | None:
    prod_root = root / "04_OUTPUT" / "production"
    if not prod_root.exists():
        return None
    candidates = []
    for date_dir in prod_root.rglob("*"):
        if date_dir.is_dir() and date_dir.name.count("-") == 2:
            approved = date_dir / "approved"
            if approved.exists():
                candidates.append(approved)
    if not candidates:
        return None
    return sorted(candidates)[-1]


def parse_run_ids(run_path: Path) -> tuple[str, int] | None:
    m = RUN_PATTERN.match(run_path.name)
    if not m:
        return None
    return (m.group(1), int(m.group(2)))


def parse_run_meta(run_path: Path) -> tuple[list[str], list[str]]:
    text = run_path.read_text(encoding="utf-8")
    palettes = []
    layouts = []
    for line in text.splitlines():
        if line.startswith("Palette IDs:"):
            palettes = [x.strip() for x in line.split(":", 1)[1].split(",") if x.strip()]
        if line.startswith("Layout IDs:"):
            layouts = [x.strip() for x in line.split(":", 1)[1].split(",") if x.strip()]
    return palettes, layouts


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

    latest_prod = find_latest_production(repo_root)
    if latest_prod:
        units = sorted([p for p in latest_prod.iterdir() if p.is_dir() and p.name.startswith("C")])
        if units:
            palette_ids = []
            layout_ids = []
            for unit in units:
                demo = unit / "demo" / "index.html"
                if not demo.exists():
                    print(f"❌ Missing demo/index.html in {unit}")
                    return 1
                html_text = demo.read_text(encoding="utf-8")
                palette = parse_meta(html_text, "palette-id")
                layout = parse_meta(html_text, "layout-id")
                if not palette or not layout:
                    print(f"❌ Missing palette-id/layout-id meta in {demo}")
                    return 1
                palette_ids.append(palette)
                layout_ids.append(layout)

            if len(set(palette_ids)) != len(palette_ids):
                print("❌ palette_id must be unique across C1/C2/C3/C4")
                return 1
            if len(set(layout_ids)) != len(layout_ids):
                print("❌ layout_id must be unique across C1/C2/C3/C4")
                return 1

            run_dir = repo_root / "05_LOGS" / "runs"
            run_files = []
            for p in run_dir.glob("*_run_*.md"):
                parsed = parse_run_ids(p)
                if parsed:
                    run_files.append((parsed[0], parsed[1], p))
            run_files = sorted(run_files)
            if run_files:
                current_run = run_files[-1][2]
                previous_runs = [p for _, _, p in run_files[:-1]][-3:]
                prior_palettes = set()
                prior_layouts = set()
                for r in previous_runs:
                    palettes, layouts = parse_run_meta(r)
                    if not palettes or not layouts:
                        print(f"❌ Missing Palette IDs / Layout IDs in {r}")
                        return 1
                    prior_palettes.update(palettes)
                    prior_layouts.update(layouts)

                if set(palette_ids) & prior_palettes:
                    print("❌ palette_id repeats within last 3 runs")
                    return 1
                if set(layout_ids) & prior_layouts:
                    print("❌ layout_id repeats within last 3 runs")
                    return 1

    print("✅ Structure validation PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
