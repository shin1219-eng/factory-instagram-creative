#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Research pipeline: captures -> creative_input.json (3-axis).

Axis design:
- technical: rendering / motion / material capability
- brand_story: narrative coherence / tone / color strategy
- market: Instagram-fit / trend alignment / differentiation
"""

from __future__ import annotations

import argparse
import colorsys
from dataclasses import asdict
from datetime import datetime, date
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from unitproduce_from_capture import load_capture_spec, derive_story

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_AXES_CONFIG_PATH = REPO_ROOT / "01_RULES" / "style" / "ResearchAxes.json"

DEFAULT_AXES_CONFIG: Dict[str, Any] = {
    "version": "research-axes.v1",
    "weights": {
        "technical": 0.40,
        "brand_story": 0.35,
        "market": 0.25,
    },
    "minimum_scores": {
        "technical": 30.0,
        "brand_story": 45.0,
        "market": 40.0,
    },
    "brand_story": {
        "vertical_tone_fit": {
            "apparel": ["balanced", "noir", "mist"],
            "mobility": ["noir", "balanced", "mist"],
            "gaming": ["noir", "neon", "balanced"],
            "spatial": ["balanced", "mist", "neon"],
            "luxury": ["noir", "mist", "balanced"],
            "editorial": ["mist", "balanced", "noir"],
        }
    },
    "market": {
        "vertical_trend_tags": {
            "apparel": ["drop", "silhouette", "runway", "material"],
            "mobility": ["quiet", "performance", "cockpit", "control"],
            "gaming": ["artifact", "mint", "lore", "utility"],
            "spatial": ["portal", "depth", "immersive", "field"],
            "luxury": ["craft", "scarcity", "maison", "collector"],
            "editorial": ["thesis", "campaign", "concept", "proof"],
        }
    },
}


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def iso_now() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def norm(v: float, lo: float, hi: float) -> float:
    if hi <= lo:
        return 0.0
    return clamp((v - lo) / (hi - lo), 0.0, 1.0)


def deep_merge(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(a)
    for k, v in b.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_axes_config(path: Path | None) -> Dict[str, Any]:
    config = dict(DEFAULT_AXES_CONFIG)
    if not path:
        return config
    if not path.exists():
        return config
    try:
        user_cfg = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return config
    if isinstance(user_cfg, dict):
        return deep_merge(config, user_cfg)
    return config


def find_capture_dirs(captures_day_dir: Path) -> List[Path]:
    dirs: List[Path] = []
    if not captures_day_dir.exists():
        return dirs
    for d in sorted(captures_day_dir.iterdir()):
        if not d.is_dir():
            continue
        if not (d / "shots" / "hero.png").exists():
            continue
        if not (d / "spector" / "capture.json").exists():
            continue
        dirs.append(d)
    return dirs


def parse_hex(hx: str) -> Tuple[int, int, int]:
    hx = hx.strip().lstrip("#")
    if len(hx) != 6:
        return (128, 128, 128)
    return tuple(int(hx[i : i + 2], 16) for i in (0, 2, 4))


def palette_diversity(palette: List[str]) -> float:
    if len(palette) < 2:
        return 0.0
    hsv: List[Tuple[float, float, float]] = []
    for c in palette:
        r, g, b = parse_hex(c)
        hsv.append(colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0))

    pairs = 0
    acc = 0.0
    for i in range(len(hsv)):
        for j in range(i + 1, len(hsv)):
            pairs += 1
            h1, s1, v1 = hsv[i]
            h2, s2, v2 = hsv[j]
            dh = min(abs(h1 - h2), 1.0 - abs(h1 - h2))
            ds = abs(s1 - s2)
            dv = abs(v1 - v2)
            acc += dh * 0.5 + ds * 0.3 + dv * 0.2
    return acc / max(1, pairs)


def technical_axis(spec: Any) -> Dict[str, Any]:
    m = spec.metrics
    geometry = norm(m.draw_calls, 8, 130) * 100
    shader = norm(m.unique_programs, 2, 18) * 100
    pipeline = clamp(norm(m.multipass_score, 0.05, 1.6) * 75 + norm(m.offscreen_ratio, 0.0, 0.9) * 25, 0, 100)
    motion = clamp(norm(m.draw_density, 0.02, 0.35) * 70 + norm(m.uniform_calls, 40, 320) * 30, 0, 100)
    fluidity = clamp(norm(m.uniform_calls, 80, 320) * 50 + norm(m.draw_density, 0.05, 0.35) * 35 + norm(m.offscreen_ratio, 0.0, 0.8) * 15, 0, 100)
    light = clamp(norm(m.unique_programs, 2, 18) * 45 + norm(m.multipass_score, 0.1, 1.6) * 55, 0, 100)

    score = (
        geometry * 0.20
        + shader * 0.20
        + pipeline * 0.20
        + motion * 0.15
        + fluidity * 0.15
        + light * 0.10
    )

    style_family = "solid"
    if fluidity >= max(geometry, light, pipeline):
        style_family = "fluid"
    elif light >= max(geometry, pipeline):
        style_family = "light"
    elif pipeline >= max(geometry, shader):
        style_family = "multipass"
    elif geometry >= max(shader, motion):
        style_family = "geometry"

    tags = []
    if fluidity >= 65:
        tags.append("liquid-ready")
    if light >= 65:
        tags.append("light-rich")
    if pipeline >= 60:
        tags.append("multi-layer")
    if motion >= 60:
        tags.append("motion-rich")

    return {
        "score": round(score, 3),
        "style_family": style_family,
        "subscores": {
            "geometry": round(geometry, 3),
            "shader": round(shader, 3),
            "pipeline": round(pipeline, 3),
            "motion": round(motion, 3),
            "fluidity": round(fluidity, 3),
            "light": round(light, 3),
        },
        "tags": tags,
    }


def _text_fullness(values: List[str]) -> float:
    non_empty = [v for v in values if isinstance(v, str) and v.strip()]
    if not non_empty:
        return 0.0
    avg_len = sum(len(v.strip()) for v in non_empty) / len(non_empty)
    return clamp(norm(avg_len, 12, 110), 0.0, 1.0)


def brand_story_axis(spec: Any, story: Any, config: Dict[str, Any]) -> Dict[str, Any]:
    tone_map = config.get("brand_story", {}).get("vertical_tone_fit", {})
    vertical = story.vertical
    allowed_tones = tone_map.get(vertical, ["balanced", "mist", "noir", "neon"])

    tone_fit = 100.0 if spec.profile.tone in allowed_tones else 48.0
    narrative = _text_fullness([
        story.objective,
        story.audience,
        story.promise,
        story.hook,
        story.tension,
        story.resolve,
        story.cta,
    ]) * 100
    palette_strategy = clamp(palette_diversity(spec.palette) * 250, 0, 100)
    cohesion = clamp(
        (100 if story.phase_c1 and story.phase_c2 and story.phase_c3 and story.phase_c4 else 45)
        * 0.5
        + (100 if story.nav_a and story.nav_b and story.nav_c else 45) * 0.3
        + (100 if story.campaign_name else 45) * 0.2,
        0,
        100,
    )

    score = (
        tone_fit * 0.25
        + narrative * 0.35
        + palette_strategy * 0.20
        + cohesion * 0.20
    )

    tags = [vertical]
    if narrative >= 70:
        tags.append("story-rich")
    if palette_strategy >= 65:
        tags.append("color-strategy")
    if cohesion >= 70:
        tags.append("campaign-cohesive")

    return {
        "score": round(score, 3),
        "subscores": {
            "tone_fit": round(tone_fit, 3),
            "narrative": round(narrative, 3),
            "palette_strategy": round(palette_strategy, 3),
            "cohesion": round(cohesion, 3),
        },
        "tags": tags,
    }


def market_axis(spec: Any, story: Any, signature_freq: Dict[str, int], config: Dict[str, Any]) -> Dict[str, Any]:
    vertical = story.vertical
    tag_map = config.get("market", {}).get("vertical_trend_tags", {})
    trend_tags = tag_map.get(vertical, [vertical])

    # Instagram-first heuristics: hook immediacy + mobile framing + momentum.
    hook_visual = clamp(
        norm(spec.image_metrics.contrast, 0.03, 0.28) * 45
        + norm(spec.profile.intensity, 0.30, 0.90) * 35
        + (20.0 if spec.profile.composition in {"center", "top"} else 8.0),
        0,
        100,
    )

    trend_alignment = clamp(
        (50 if vertical in {"spatial", "gaming", "apparel", "luxury", "editorial", "mobility"} else 30)
        + norm(spec.metrics.unique_programs, 2, 16) * 25
        + norm(spec.metrics.draw_density, 0.02, 0.30) * 25,
        0,
        100,
    )

    sig = f"{vertical}:{spec.profile.arch}:{spec.profile.motion}:{spec.profile.tone}"
    freq = max(1, signature_freq.get(sig, 1))
    differentiation = clamp(100 / freq, 28, 100)

    score = hook_visual * 0.40 + trend_alignment * 0.35 + differentiation * 0.25

    if hook_visual >= trend_alignment and hook_visual >= differentiation:
        market_mode = "hook-heavy"
    elif trend_alignment >= differentiation:
        market_mode = "trend-led"
    else:
        market_mode = "distinctive"

    return {
        "score": round(score, 3),
        "market_mode": market_mode,
        "subscores": {
            "instagram_fit": round(hook_visual, 3),
            "trend_alignment": round(trend_alignment, 3),
            "differentiation": round(differentiation, 3),
        },
        "trend_tags": trend_tags,
    }


def derive_design_extraction(spec: Any, story: Any, market: Dict[str, Any]) -> Dict[str, Any]:
    p = spec.profile
    m = spec.metrics
    im = spec.image_metrics

    if p.composition in {"left", "right"}:
        composition_rule = "asymmetric_single_focus"
    elif p.composition in {"top", "bottom"}:
        composition_rule = "vertical_story_stack"
    else:
        composition_rule = "center_hero_focus"

    if m.multipass_score > 1.1 or m.offscreen_ratio > 0.45:
        lighting_rule = "layered_volumetric_light"
    elif p.tone == "noir":
        lighting_rule = "high_contrast_chiaroscuro"
    elif p.tone == "mist":
        lighting_rule = "soft_diffused_glow"
    else:
        lighting_rule = "key_plus_rim_balanced"

    if p.arch == "particle":
        material_rule = "particulate_and_translucent"
    elif p.arch == "multipass":
        material_rule = "layered_glass_metal_mix"
    elif p.arch == "shader-mix":
        material_rule = "shader_gradient_surface"
    elif p.tone == "noir":
        material_rule = "metal_and_dark_lacquer"
    else:
        material_rule = "hybrid_solid_surface"

    if p.motion == "slice":
        motion_rule = "segmented_scan_motion"
    elif p.motion == "pulse":
        motion_rule = "breathing_pulse_motion"
    elif p.motion == "kinetic":
        motion_rule = "high_velocity_orbit_motion"
    elif p.motion == "float":
        motion_rule = "slow_floating_motion"
    else:
        motion_rule = "drift_motion"

    if story.vertical in {"luxury", "editorial"}:
        typography_rule = "serif_headline_sans_body"
    elif story.vertical in {"gaming", "spatial"}:
        typography_rule = "display_headline_with_tech_sans"
    else:
        typography_rule = "clean_sans_hierarchy"

    if market["market_mode"] == "hook-heavy":
        instagram_rule = "first_second_impact_priority"
    elif market["market_mode"] == "trend-led":
        instagram_rule = "trend_alignment_priority"
    else:
        instagram_rule = "distinctive_signature_priority"

    story_arc = {
        "c1": story.phase_c1,
        "c2": story.phase_c2,
        "c3": story.phase_c3,
        "c4": story.phase_c4,
    }

    return {
        "composition_rule": composition_rule,
        "lighting_rule": lighting_rule,
        "material_rule": material_rule,
        "motion_rule": motion_rule,
        "typography_rule": typography_rule,
        "instagram_rule": instagram_rule,
        "story_arc": story_arc,
        "focal_hint": {
            "center_x": round(im.center_x, 3),
            "center_y": round(im.center_y, 3),
        },
    }


def overall_score(axes: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    w = config.get("weights", {})
    wt = float(w.get("technical", 0.40))
    wb = float(w.get("brand_story", 0.35))
    wm = float(w.get("market", 0.25))
    total_w = max(1e-6, wt + wb + wm)
    score = (
        axes["technical"]["score"] * wt
        + axes["brand_story"]["score"] * wb
        + axes["market"]["score"] * wm
    ) / total_w
    return {
        "score": round(score, 3),
        "weights": {"technical": wt, "brand_story": wb, "market": wm},
    }


def pick_diverse_candidates(candidates: List[Dict[str, Any]], campaigns: int) -> List[Dict[str, Any]]:
    sorted_candidates = sorted(candidates, key=lambda x: x["research_axes"]["overall"]["score"], reverse=True)

    picked: List[Dict[str, Any]] = []
    used_verticals = set()
    used_style_families = set()
    used_market_modes = set()
    used_slugs = set()

    for c in sorted_candidates:
        if len(picked) >= campaigns:
            break
        vertical = c["vertical"]
        style_family = c["research_axes"]["technical"]["style_family"]
        market_mode = c["research_axes"]["market"]["market_mode"]
        if c["slug"] in used_slugs:
            continue
        if vertical in used_verticals:
            continue
        if style_family in used_style_families:
            continue
        if market_mode in used_market_modes:
            continue
        picked.append(c)
        used_slugs.add(c["slug"])
        used_verticals.add(vertical)
        used_style_families.add(style_family)
        used_market_modes.add(market_mode)

    for c in sorted_candidates:
        if len(picked) >= campaigns:
            break
        if c["slug"] in used_slugs:
            continue
        vertical = c["vertical"]
        if vertical in used_verticals:
            continue
        picked.append(c)
        used_slugs.add(c["slug"])
        used_verticals.add(vertical)

    for c in sorted_candidates:
        if len(picked) >= campaigns:
            break
        if c["slug"] in used_slugs:
            continue
        picked.append(c)
        used_slugs.add(c["slug"])

    return picked


def make_signature(spec: Any, vertical: str) -> str:
    return f"{vertical}:{spec.profile.arch}:{spec.profile.motion}:{spec.profile.tone}"


def build_creative_input(
    captures_day_dir: Path,
    campaigns: int,
    story_rotation: int,
    batch_id: str,
    target_date: str,
    axes_config: Dict[str, Any],
    axes_config_path: Path | None,
) -> Dict[str, Any]:
    capture_dirs = find_capture_dirs(captures_day_dir)
    if not capture_dirs:
        raise SystemExit(f"No valid captures found under: {captures_day_dir}")

    specs: List[Any] = []
    provisional: List[Dict[str, Any]] = []

    for capture_dir in capture_dirs:
        spec = load_capture_spec(capture_dir, demo_image=None, slug_override=None)
        story = derive_story(spec.slug, spec.url, spec.profile, campaign_idx=0, story_rotation=story_rotation)
        specs.append(spec)
        provisional.append(
            {
                "spec": spec,
                "story": story,
                "capture_dir": capture_dir,
                "signature": make_signature(spec, story.vertical),
            }
        )

    signature_freq: Dict[str, int] = {}
    for p in provisional:
        signature_freq[p["signature"]] = signature_freq.get(p["signature"], 0) + 1

    candidates: List[Dict[str, Any]] = []
    for p in provisional:
        spec = p["spec"]
        story = p["story"]

        tech = technical_axis(spec)
        brand = brand_story_axis(spec, story, axes_config)
        market = market_axis(spec, story, signature_freq, axes_config)
        design_extraction = derive_design_extraction(spec, story, market)
        axes = {
            "technical": tech,
            "brand_story": brand,
            "market": market,
        }
        axes["overall"] = overall_score(axes, axes_config)

        candidates.append(
            {
                "slug": spec.slug,
                "url": spec.url,
                "capture_dir": str(p["capture_dir"].resolve()),
                "hero_path": str((p["capture_dir"] / "shots" / "hero.png").resolve()),
                "capture_json_path": str((p["capture_dir"] / "spector" / "capture.json").resolve()),
                "profile": asdict(spec.profile),
                "metrics": asdict(spec.metrics),
                "image_metrics": asdict(spec.image_metrics),
                "vertical": story.vertical,
                "research_axes": axes,
                "design_extraction": design_extraction,
            }
        )

    selected = pick_diverse_candidates(candidates, campaigns=max(1, campaigns))

    campaign_items: List[Dict[str, Any]] = []
    for idx, item in enumerate(selected):
        profile_obj = item["profile"]

        class _P:
            pass

        p = _P()
        p.arch = profile_obj["arch"]
        p.motion = profile_obj["motion"]
        p.composition = profile_obj["composition"]
        p.tone = profile_obj["tone"]
        p.intensity = profile_obj["intensity"]
        p.seed = profile_obj["seed"]

        campaign_story_rotation = story_rotation + idx
        story = derive_story(
            item["slug"],
            item.get("url"),
            p,
            campaign_idx=idx,
            story_rotation=campaign_story_rotation,
        )

        campaign_items.append(
            {
                "campaign_id": story.campaign_id,
                "campaign_name": story.campaign_name,
                "target_slug": item["slug"],
                "url": item.get("url"),
                "capture_dir": item["capture_dir"],
                "story_rotation": campaign_story_rotation,
                "unit_plan": ["C1", "C2", "C3", "C4"],
                "style_profile": item["profile"],
                "story": asdict(story),
                "research_axes": item["research_axes"],
                "design_extraction": item["design_extraction"],
                "selection_reason": {
                    "technical": item["research_axes"]["technical"]["tags"],
                    "brand_story": item["research_axes"]["brand_story"]["tags"],
                    "market": [item["research_axes"]["market"]["market_mode"]],
                },
                "production_brief": {
                    "must_include": [
                        item["design_extraction"]["composition_rule"],
                        item["design_extraction"]["lighting_rule"],
                        item["design_extraction"]["material_rule"],
                        item["design_extraction"]["motion_rule"],
                    ],
                    "narrative_lock": item["design_extraction"]["story_arc"],
                },
                "evidence": {
                    "hero_path": item["hero_path"],
                    "capture_json_path": item["capture_json_path"],
                    "metrics": item["metrics"],
                    "image_metrics": item["image_metrics"],
                },
            }
        )

    min_scores = axes_config.get("minimum_scores", {})

    return {
        "schema_version": "creative-input.v2",
        "generated_at": iso_now(),
        "batch_id": batch_id,
        "target_output_date": target_date,
        "source": {
            "captures_day": captures_day_dir.name,
            "captures_dir": str(captures_day_dir.resolve()),
            "candidate_count": len(candidates),
            "selected_count": len(campaign_items),
        },
        "research_basis": {
            "technical_axis": {
                "inputs": ["spector/capture.json", "shots/hero.png"],
                "decision_points": ["geometry", "shader", "pipeline", "motion", "fluidity", "light"],
            },
            "brand_story_axis": {
                "inputs": ["story dictionary", "profile tone/composition", "palette diversity", "campaign phase lock"],
                "decision_points": ["tone_fit", "narrative", "palette_strategy", "cohesion"],
            },
            "market_axis": {
                "inputs": ["TrendSources tier context", "instagram-fit heuristics", "differentiation", "trend tags"],
                "decision_points": ["instagram_fit", "trend_alignment", "differentiation"],
            },
            "design_extraction": {
                "outputs": [
                    "composition_rule",
                    "lighting_rule",
                    "material_rule",
                    "motion_rule",
                    "typography_rule",
                    "instagram_rule",
                    "story_arc",
                ]
            },
            "source_files": [
                str((REPO_ROOT / "01_RULES" / "TrendSources.md").resolve()),
                str((REPO_ROOT / "01_RULES" / "style" / "ResearchAxes.json").resolve()),
            ],
            "axes_config_path": str((axes_config_path or DEFAULT_AXES_CONFIG_PATH).resolve()),
        },
        "global_constraints": {
            "linked_story_required": True,
            "units_per_campaign": 4,
            "campaign_count": len(campaign_items),
            "disallow_search_url": True,
            "axis_minimum_scores": {
                "technical": float(min_scores.get("technical", 30.0)),
                "brand_story": float(min_scores.get("brand_story", 45.0)),
                "market": float(min_scores.get("market", 40.0)),
            },
            "do_not_use": [
                "same-layout-repeat",
                "single-hue-all-units",
                "logo-copy",
                "long-text-burn-in",
            ],
        },
        "campaigns": campaign_items,
    }


def write_summary_md(output_dir: Path, data: Dict[str, Any]) -> None:
    lines = []
    lines.append(f"# Creative Input Summary ({data['batch_id']})")
    lines.append("")
    lines.append(f"- schema: {data.get('schema_version')}")
    lines.append(f"- generated_at: {data['generated_at']}")
    lines.append(f"- source captures: {data['source']['captures_day']}")
    lines.append(f"- candidates: {data['source']['candidate_count']}")
    lines.append(f"- selected campaigns: {len(data['campaigns'])}")
    lines.append("")

    for c in data["campaigns"]:
        st = c["story"]
        ax = c["research_axes"]
        de = c.get("design_extraction", {})
        lines.append(f"## {c['campaign_id']} / {c['target_slug']}")
        lines.append(f"- campaign_name: {c['campaign_name']}")
        lines.append(f"- vertical: {st['vertical']}")
        lines.append(f"- objective: {st['objective']}")
        lines.append(
            "- axis scores: "
            f"technical={ax['technical']['score']:.1f}, "
            f"brand_story={ax['brand_story']['score']:.1f}, "
            f"market={ax['market']['score']:.1f}, "
            f"overall={ax['overall']['score']:.1f}"
        )
        lines.append(
            "- design extraction: "
            f"{de.get('composition_rule')} / {de.get('lighting_rule')} / "
            f"{de.get('material_rule')} / {de.get('motion_rule')}"
        )
        lines.append(f"- phases: {st['phase_c1']} -> {st['phase_c2']} -> {st['phase_c3']} -> {st['phase_c4']}")
        lines.append(f"- capture_dir: {c['capture_dir']}")
        lines.append("")

    (output_dir / "SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--captures-date", type=str, default=date.today().isoformat(), help="capture date YYYY-MM-DD under 05_LOGS/captures")
    parser.add_argument("--campaigns", type=int, default=3, help="number of campaigns to select")
    parser.add_argument("--story-rotation", type=int, default=0, help="story dictionary rotation seed")
    parser.add_argument("--target-date", type=str, default=date.today().isoformat(), help="target output date YYYY-MM-DD for production stage")
    parser.add_argument("--batch-id", type=str, help="batch id override (default auto)")
    parser.add_argument("--axes-config", type=str, help="override path for research axes config json")
    args = parser.parse_args()

    captures_day_dir = REPO_ROOT / "05_LOGS" / "captures" / args.captures_date
    now_stamp = datetime.now().strftime("%H%M%S")
    batch_id = args.batch_id or f"batch-{args.captures_date}-{now_stamp}"

    out_dir = REPO_ROOT / "05_LOGS" / "research" / date.today().isoformat() / batch_id
    ensure_dir(out_dir)

    axes_config_path = Path(args.axes_config).resolve() if args.axes_config else DEFAULT_AXES_CONFIG_PATH
    axes_config = load_axes_config(axes_config_path)

    data = build_creative_input(
        captures_day_dir=captures_day_dir,
        campaigns=max(1, args.campaigns),
        story_rotation=args.story_rotation,
        batch_id=batch_id,
        target_date=args.target_date,
        axes_config=axes_config,
        axes_config_path=axes_config_path,
    )

    out_json = out_dir / "creative_input.json"
    out_json.write_text(json.dumps(data, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    write_summary_md(out_dir, data)

    print(f"creative_input: {out_json}")
    print(f"summary: {out_dir / 'SUMMARY.md'}")
    print(f"campaigns: {len(data['campaigns'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
