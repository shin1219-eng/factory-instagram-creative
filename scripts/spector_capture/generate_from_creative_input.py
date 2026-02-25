#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Production pipeline: creative_input.json -> C1-C4 outputs.

This script is the "creative production" stage.
It consumes pre-organized creative_input.json and generates linked unit sets.
"""

from __future__ import annotations

import argparse
from datetime import date, datetime
import json
from pathlib import Path
import shutil
import subprocess
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[2]
UNITPRODUCE = Path(__file__).resolve().parent / "unitproduce_from_capture.py"


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def run_unitproduce(
    capture_dir: str,
    out_date: str,
    version: str,
    story_rotation: int,
    campaign_start: int,
    family_shift: int,
) -> str:
    cmd = [
        "python3",
        str(UNITPRODUCE),
        "--capture",
        capture_dir,
        "--date",
        out_date,
        "--version",
        version,
        "--campaigns",
        "1",
        "--campaign-start",
        str(campaign_start),
        "--story-rotation",
        str(story_rotation),
        "--family-shift",
        str(family_shift),
        "--print-profile",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return proc.stdout


def parse_generated_unit_dirs(stdout: str) -> List[str]:
    out: List[str] = []
    for line in stdout.splitlines():
        line = line.strip()
        if line.startswith("- /") and line.endswith("/demo"):
            out.append(line[2:].strip())
    return out


def parse_campaign_start(campaign_id: str | None) -> int:
    if not campaign_id:
        return 0
    if campaign_id.startswith("cp"):
        try:
            return max(0, int(campaign_id[2:]) - 1)
        except ValueError:
            return 0
    return 0


def axis_gate(campaign: Dict[str, Any], constraints: Dict[str, Any]) -> tuple[bool, str]:
    mins = constraints.get("axis_minimum_scores", {}) if isinstance(constraints, dict) else {}
    axes = campaign.get("research_axes", {})
    tech = float((axes.get("technical") or {}).get("score", 0.0))
    brand = float((axes.get("brand_story") or {}).get("score", 0.0))
    market = float((axes.get("market") or {}).get("score", 0.0))
    min_tech = float(mins.get("technical", 0.0))
    min_brand = float(mins.get("brand_story", 0.0))
    min_market = float(mins.get("market", 0.0))
    ok = tech >= min_tech and brand >= min_brand and market >= min_market
    msg = (
        f"tech={tech:.1f}/{min_tech:.1f}, "
        f"brand={brand:.1f}/{min_brand:.1f}, "
        f"market={market:.1f}/{min_market:.1f}"
    )
    return ok, msg


def load_story_payload(demo_dirs: List[Path]) -> Dict[str, Any]:
    for d in demo_dirs:
        p = d / "story.json"
        if p.exists():
            try:
                payload = json.loads(p.read_text(encoding="utf-8"))
                if isinstance(payload, dict):
                    return payload
            except Exception:
                continue
    return {}


def campaign_signature_from_story(story: Dict[str, Any]) -> str:
    if not story:
        return ""
    systems = story.get("systems") or {}
    sig = str(systems.get("signature") or "")
    family = str(story.get("family") or "")
    vertical = str(story.get("vertical") or "")
    phases = "|".join(
        [
            str(story.get("phase_c1") or ""),
            str(story.get("phase_c2") or ""),
            str(story.get("phase_c3") or ""),
            str(story.get("phase_c4") or ""),
        ]
    )
    return f"{vertical}|{family}|{sig}|{phases}"


def cleanup_demo_dirs(dirs: List[Path]) -> None:
    # remove unit directories (.../<unit>/demo -> remove parent unit dir)
    for demo in dirs:
        unit_dir = demo.parent
        if unit_dir.exists():
            shutil.rmtree(unit_dir, ignore_errors=True)


def write_ad_review(
    run_dir: Path,
    out_date: str,
    version: str,
    run_tag: str,
    executions: List[Dict[str, Any]],
    skipped: List[Dict[str, Any]],
) -> Path:
    lines: List[str] = []
    lines.append(f"# AD Review ({run_tag})")
    lines.append("")
    lines.append(f"- date: {out_date}")
    lines.append(f"- version: {version}")
    lines.append(f"- generated: {datetime.now().replace(microsecond=0).isoformat()}")
    lines.append("")
    lines.append("## Checklist")
    lines.append("- [ ] C1→C4で物語が連結している")
    lines.append("- [ ] family / composition / motion が重複しすぎていない")
    lines.append("- [ ] 1秒目フックが明確")
    lines.append("- [ ] CTAまでの流れが途切れていない")
    lines.append("- [ ] 参照元URLとの距離感（丸パクリ回避）が適切")
    lines.append("")
    lines.append("## Candidates")
    for e in executions:
        story = e.get("story_payload") or {}
        systems = story.get("systems") or {}
        lines.append(
            "- "
            f"{e.get('campaign_id')} / {e.get('target_slug')} / "
            f"family={story.get('family', '-')} / "
            f"signature={systems.get('signature', '-')}"
        )
    if skipped:
        lines.append("")
        lines.append("## Skipped")
        for s in skipped:
            lines.append(f"- {s.get('campaign_id')} / {s.get('target_slug')}: {s.get('reason')}")
    lines.append("")
    lines.append("## Selection")
    lines.append("1. Primary: ")
    lines.append("2. Secondary: ")
    lines.append("3. Hold: ")
    lines.append("")
    lines.append("## Direction Notes")
    lines.append("- 強いテーマ1本に絞る")
    lines.append("- C1のモチーフをC2/C3/C4で変奏し、別物にしない")
    lines.append("- コピーは後工程前提で余白を確保")
    lines.append("")

    out = run_dir / f"AD_REVIEW_{version}.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def build_index_html(inbox_dir: Path, units: List[Path], name: str) -> Path:
    html = [
        "<!doctype html>",
        '<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{name}</title>",
        "<style>body{font-family:ui-sans-serif,system-ui;padding:20px;background:#0a0d12;color:#e6e9ef}a{color:#7dd3fc;text-decoration:none}a:hover{text-decoration:underline}li{margin:8px 0}</style>",
        "</head><body>",
        f"<h1>{name}</h1>",
        "<ul>",
    ]
    for unit_dir in sorted(units):
        rel = unit_dir.relative_to(inbox_dir)
        html.append(f'<li><a href="{rel.as_posix()}/index.html">{rel.parent.name}</a></li>')
    html += ["</ul>", "</body></html>"]

    index_path = inbox_dir / f"INDEX_{name.replace(' ', '_')}.html"
    index_path.write_text("\n".join(html) + "\n", encoding="utf-8")
    return index_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--creative-input", required=True, help="path to creative_input.json")
    parser.add_argument("--date", type=str, default=date.today().isoformat(), help="output date YYYY-MM-DD")
    parser.add_argument("--version", type=str, default="v05", help="output version suffix")
    parser.add_argument("--run-tag", type=str, help="run tag for index/log names")
    parser.add_argument("--max-regen", type=int, default=2, help="max retries on duplicate campaign signature")
    parser.add_argument("--regen-story-step", type=int, default=11, help="story_rotation increment on retry")
    parser.add_argument("--regen-family-step", type=int, default=1, help="family_shift increment on retry")
    args = parser.parse_args()

    creative_input_path = Path(args.creative_input).resolve()
    if not creative_input_path.exists():
        raise SystemExit(f"creative input not found: {creative_input_path}")

    data = json.loads(creative_input_path.read_text(encoding="utf-8"))
    campaigns: List[Dict[str, Any]] = data.get("campaigns") or []
    if not campaigns:
        raise SystemExit("creative_input has no campaigns")
    global_constraints: Dict[str, Any] = data.get("global_constraints") or {}

    run_tag = args.run_tag or f"{data.get('batch_id', 'batch')}_{args.version}"

    generated_demo_dirs: List[Path] = []
    exec_logs: List[Dict[str, Any]] = []
    skipped: List[Dict[str, Any]] = []
    seen_campaign_signatures: set[str] = set()

    for campaign in campaigns:
        capture_dir = campaign.get("capture_dir")
        if not capture_dir:
            raise SystemExit(f"campaign missing capture_dir: {campaign}")

        ok, gate_msg = axis_gate(campaign, global_constraints)
        if not ok:
            skipped.append(
                {
                    "campaign_id": campaign.get("campaign_id"),
                    "target_slug": campaign.get("target_slug"),
                    "reason": f"axis_gate_failed: {gate_msg}",
                }
            )
            continue

        base_story_rotation = int(campaign.get("story_rotation", 0))
        campaign_start = parse_campaign_start(campaign.get("campaign_id"))
        accepted = False
        attempt_logs: List[Dict[str, Any]] = []

        for attempt in range(max(0, args.max_regen) + 1):
            trial_story_rotation = base_story_rotation + attempt * max(1, args.regen_story_step)
            trial_family_shift = attempt * max(1, args.regen_family_step)
            stdout = run_unitproduce(
                capture_dir=capture_dir,
                out_date=args.date,
                version=args.version,
                story_rotation=trial_story_rotation,
                campaign_start=campaign_start,
                family_shift=trial_family_shift,
            )
            demo_dirs = [Path(p) for p in parse_generated_unit_dirs(stdout)]
            story_payload = load_story_payload(demo_dirs)
            campaign_signature = campaign_signature_from_story(story_payload)
            is_duplicate = bool(campaign_signature) and campaign_signature in seen_campaign_signatures

            attempt_logs.append(
                {
                    "attempt": attempt,
                    "story_rotation": trial_story_rotation,
                    "family_shift": trial_family_shift,
                    "campaign_signature": campaign_signature,
                    "duplicate": is_duplicate,
                    "stdout": stdout,
                    "generated_demo_dirs": [str(p) for p in demo_dirs],
                }
            )

            if is_duplicate:
                cleanup_demo_dirs(demo_dirs)
                continue

            accepted = True
            if campaign_signature:
                seen_campaign_signatures.add(campaign_signature)
            generated_demo_dirs.extend(demo_dirs)
            exec_logs.append(
                {
                    "campaign_id": campaign.get("campaign_id"),
                    "target_slug": campaign.get("target_slug"),
                    "capture_dir": capture_dir,
                    "campaign_start": campaign_start,
                    "axis_gate": gate_msg,
                    "attempts": attempt_logs,
                    "story_payload": story_payload,
                    "final_signature": campaign_signature,
                    "generated_demo_dirs": [str(p) for p in demo_dirs],
                }
            )
            break

        if not accepted:
            skipped.append(
                {
                    "campaign_id": campaign.get("campaign_id"),
                    "target_slug": campaign.get("target_slug"),
                    "reason": "duplicate_signature_exhausted",
                    "attempts": attempt_logs,
                }
            )

    out_month = datetime.strptime(args.date, "%Y-%m-%d").strftime("%Y-%m")
    inbox_dir = REPO_ROOT / "04_OUTPUT" / "production" / out_month / args.date / "inbox"
    # demo dir format: .../inbox/<unit>/demo
    unit_demo_dirs = []
    seen = set()
    for p in generated_demo_dirs:
        key = str(p.resolve()) if p.exists() else str(p)
        if key in seen:
            continue
        if p.exists() and p.parent.parent == inbox_dir:
            unit_demo_dirs.append(p)
            seen.add(key)

    index_name = f"{run_tag}_12set"
    index_path = build_index_html(inbox_dir, unit_demo_dirs, index_name)

    run_dir = creative_input_path.parent
    run_manifest_path = run_dir / f"generation_result_{args.version}.json"
    ad_review_path = write_ad_review(
        run_dir=run_dir,
        out_date=args.date,
        version=args.version,
        run_tag=run_tag,
        executions=exec_logs,
        skipped=skipped,
    )

    run_manifest = {
        "generated_at": datetime.now().replace(microsecond=0).isoformat(),
        "creative_input": str(creative_input_path),
        "output_date": args.date,
        "version": args.version,
        "run_tag": run_tag,
        "index_path": str(index_path),
        "generated_demo_dirs": [str(p) for p in unit_demo_dirs],
        "campaign_signatures": sorted(seen_campaign_signatures),
        "ad_review_path": str(ad_review_path),
        "executions": exec_logs,
        "skipped": skipped,
    }
    run_manifest_path.write_text(json.dumps(run_manifest, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

    print(f"generated_units: {len(unit_demo_dirs)}")
    print(f"skipped_campaigns: {len(skipped)}")
    print(f"index: {index_path}")
    print(f"ad_review: {ad_review_path}")
    print(f"manifest: {run_manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
