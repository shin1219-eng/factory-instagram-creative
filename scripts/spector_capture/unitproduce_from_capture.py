#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Generate C1-C4 units from a Spector capture directory.

Rebuilt from scratch (v2 architecture):
- capture analysis (metrics + image)
- campaign story generation
- family-based templates (fluid / brutal / cinematic)
- linked campaign output (C1-C4)
"""

from __future__ import annotations

import argparse
import colorsys
from dataclasses import dataclass
from datetime import date, datetime
import hashlib
import json
from pathlib import Path
from string import Template
from typing import Dict, List, Tuple

from PIL import Image, ImageDraw

REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class CaptureMetrics:
    total_commands: int
    draw_calls: int
    draw_arrays: int
    draw_elements: int
    clear_calls: int
    viewport_calls: int
    scissor_calls: int
    framebuffer_binds: int
    use_program_calls: int
    unique_programs: int
    texture_ops: int
    uniform_calls: int
    state_changes: int
    offscreen_ratio: float
    draw_density: float
    multipass_score: float


@dataclass
class ImageMetrics:
    brightness: float
    contrast: float
    saturation: float
    edge_density: float
    center_x: float
    center_y: float


@dataclass
class StyleProfile:
    arch: str
    motion: str
    composition: str
    tone: str
    intensity: float
    style_family: str
    seed: int


@dataclass
class StorySpec:
    campaign_id: str
    campaign_name: str
    story_id: str
    vertical: str
    objective: str
    audience: str
    promise: str
    motif: str
    scene: str
    hook: str
    tension: str
    resolve: str
    cta: str
    c1_title: str
    c1_sub: str
    c2_title: str
    c3_title: str
    c3_sub: str
    c4_title: str
    c4_quote: str
    nav_a: str
    nav_b: str
    nav_c: str
    phase_c1: str
    phase_c2: str
    phase_c3: str
    phase_c4: str


@dataclass
class CaptureSpec:
    slug: str
    url: str | None
    palette: List[str]
    hero_path: Path
    metrics: CaptureMetrics
    image_metrics: ImageMetrics
    profile: StyleProfile
    story: StorySpec


FAMILY_VARIANTS = [
    "fluid",
    "organic",
    "spectral",
    "brutal",
    "grid",
    "industrial",
    "cinematic",
    "editorial",
    "luxe",
]

FAMILY_MODE = {
    "fluid": "fluid",
    "organic": "fluid",
    "spectral": "fluid",
    "brutal": "brutal",
    "grid": "brutal",
    "industrial": "brutal",
    "cinematic": "cinematic",
    "editorial": "cinematic",
    "luxe": "cinematic",
}

FAMILY_TYPEFACE = {
    "fluid": "'Syne',sans-serif",
    "organic": "'Sora',sans-serif",
    "spectral": "'Outfit',sans-serif",
    "brutal": "'Archivo Black',sans-serif",
    "grid": "'Bebas Neue',sans-serif",
    "industrial": "'Space Grotesk',sans-serif",
    "cinematic": "'Cormorant Garamond',serif",
    "editorial": "'Prata',serif",
    "luxe": "'Playfair Display',serif",
}


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def slugify(text: str) -> str:
    return "".join(ch if ch.isalnum() else "-" for ch in text).strip("-")[:80]


def hex_color(rgb: Tuple[int, int, int]) -> str:
    r, g, b = (int(clamp(c, 0, 255)) for c in rgb)
    return "#%02x%02x%02x" % (r, g, b)


def parse_hex(hx: str) -> Tuple[int, int, int]:
    hx = hx.strip().lstrip("#")
    if len(hx) != 6:
        return (128, 128, 128)
    return tuple(int(hx[i : i + 2], 16) for i in (0, 2, 4))


def mix_hex(a: str, b: str, t: float) -> str:
    ar, ag, ab = parse_hex(a)
    br, bg, bb = parse_hex(b)
    t = clamp(t, 0.0, 1.0)
    return hex_color((
        int(ar + (br - ar) * t),
        int(ag + (bg - ag) * t),
        int(ab + (bb - ab) * t),
    ))


def hue_shift(hx: str, deg: float, sat_mul: float = 1.0, val_mul: float = 1.0) -> str:
    r, g, b = parse_hex(hx)
    h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
    h = (h + deg / 360.0) % 1.0
    s = clamp(s * sat_mul, 0.0, 1.0)
    v = clamp(v * val_mul, 0.0, 1.0)
    rr, gg, bb = colorsys.hsv_to_rgb(h, s, v)
    return hex_color((int(rr * 255), int(gg * 255), int(bb * 255)))


def luminance(hx: str) -> float:
    r, g, b = parse_hex(hx)
    srgb = [r / 255.0, g / 255.0, b / 255.0]

    def to_lin(c: float) -> float:
        if c <= 0.04045:
            return c / 12.92
        return ((c + 0.055) / 1.055) ** 2.4

    r_lin, g_lin, b_lin = (to_lin(c) for c in srgb)
    return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin


def text_color(bg: str) -> str:
    return "#101014" if luminance(bg) > 0.45 else "#f4f5f8"


def extract_palette(image_path: Path, n: int = 6) -> List[str]:
    img = Image.open(image_path).convert("RGB").resize((240, 240))
    quant = img.quantize(colors=40, method=Image.Quantize.MEDIANCUT).convert("RGB")
    colors = quant.getcolors(240 * 240) or []
    colors.sort(reverse=True)

    picked: List[Tuple[int, int, int]] = []
    for _, rgb in colors:
        if not picked:
            picked.append(rgb)
        else:
            d = min(
                ((rgb[0] - p[0]) ** 2 + (rgb[1] - p[1]) ** 2 + (rgb[2] - p[2]) ** 2) ** 0.5
                for p in picked
            )
            if d > 32:
                picked.append(rgb)
        if len(picked) >= n:
            break

    if not picked:
        picked = [(14, 16, 20), (34, 38, 45), (66, 72, 86), (210, 212, 220)]

    while len(picked) < n:
        base = picked[len(picked) % len(picked)]
        picked.append((min(255, base[0] + 18), min(255, base[1] + 20), min(255, base[2] + 24)))

    palette = [hex_color(c) for c in picked[:n]]

    # Add one hue-shift accent if overly neutral.
    avg_sat = 0.0
    for hx in palette:
        r, g, b = parse_hex(hx)
        _, s, _ = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
        avg_sat += s
    avg_sat /= max(1, len(palette))
    if avg_sat < 0.18:
        palette[-1] = hue_shift(palette[0], 140, sat_mul=1.8, val_mul=1.2)

    return palette


def load_capture_metrics(capture_json: Path | None) -> CaptureMetrics:
    if not capture_json or not capture_json.exists():
        return CaptureMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.0, 0.0, 0.0)

    try:
        data = json.loads(capture_json.read_text(encoding="utf-8"))
    except Exception:
        return CaptureMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.0, 0.0, 0.0)

    commands = data.get("commands") or []
    if not isinstance(commands, list):
        commands = []

    by_name: Dict[str, int] = {}
    unique_programs = set()

    for cmd in commands:
        if not isinstance(cmd, dict):
            continue
        name = cmd.get("name")
        if isinstance(name, str):
            by_name[name] = by_name.get(name, 0) + 1
        if name == "useProgram":
            args = cmd.get("commandArguments")
            if isinstance(args, list) and args:
                first = args[0]
                if isinstance(first, dict):
                    tag = first.get("__SPECTOR_Object_TAG")
                    if isinstance(tag, dict) and tag.get("id") is not None:
                        unique_programs.add(tag.get("id"))

    total = len(commands)
    draw_arrays = by_name.get("drawArrays", 0)
    draw_elements = by_name.get("drawElements", 0)
    draw_calls = draw_arrays + draw_elements

    clear_calls = by_name.get("clear", 0)
    viewport_calls = by_name.get("viewport", 0)
    scissor_calls = by_name.get("scissor", 0)
    framebuffer_binds = by_name.get("bindFramebuffer", 0)
    use_program_calls = by_name.get("useProgram", 0)
    texture_ops = by_name.get("bindTexture", 0) + by_name.get("activeTexture", 0)

    uniform_calls = sum(v for k, v in by_name.items() if k.startswith("uniform"))
    state_changes = (
        by_name.get("enable", 0)
        + by_name.get("disable", 0)
        + by_name.get("depthMask", 0)
        + by_name.get("colorMask", 0)
        + by_name.get("frontFace", 0)
        + by_name.get("blendFunc", 0)
    )

    offscreen_ratio = framebuffer_binds / max(1, draw_calls)
    draw_density = draw_calls / max(1, total)
    multipass_score = (
        clear_calls * 0.8
        + viewport_calls * 0.7
        + scissor_calls * 0.6
        + framebuffer_binds * 0.9
    ) / max(1, draw_calls)

    return CaptureMetrics(
        total_commands=total,
        draw_calls=draw_calls,
        draw_arrays=draw_arrays,
        draw_elements=draw_elements,
        clear_calls=clear_calls,
        viewport_calls=viewport_calls,
        scissor_calls=scissor_calls,
        framebuffer_binds=framebuffer_binds,
        use_program_calls=use_program_calls,
        unique_programs=len(unique_programs),
        texture_ops=texture_ops,
        uniform_calls=uniform_calls,
        state_changes=state_changes,
        offscreen_ratio=offscreen_ratio,
        draw_density=draw_density,
        multipass_score=multipass_score,
    )


def compute_image_metrics(hero: Path) -> ImageMetrics:
    img = Image.open(hero).convert("RGB").resize((128, 128))
    w, h = img.size
    px = list(img.getdata())

    lum_values: List[float] = []
    sat_values: List[float] = []
    total_w = 0.0
    cx = 0.0
    cy = 0.0

    for y in range(h):
        for x in range(w):
            r, g, b = px[y * w + x]
            lum = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0
            _, s, _ = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
            lum_values.append(lum)
            sat_values.append(s)
            wgt = lum + 0.04
            total_w += wgt
            cx += x * wgt
            cy += y * wgt

    brightness = sum(lum_values) / max(1, len(lum_values))
    mean = brightness
    variance = sum((v - mean) ** 2 for v in lum_values) / max(1, len(lum_values))
    contrast = variance ** 0.5
    saturation = sum(sat_values) / max(1, len(sat_values))

    edge_total = 0.0
    edge_count = 0
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            c = px[y * w + x]
            l = px[y * w + (x - 1)]
            r = px[y * w + (x + 1)]
            u = px[(y - 1) * w + x]
            d = px[(y + 1) * w + x]
            gx = abs(c[0] - l[0]) + abs(c[1] - l[1]) + abs(c[2] - l[2])
            gx += abs(r[0] - c[0]) + abs(r[1] - c[1]) + abs(r[2] - c[2])
            gy = abs(c[0] - u[0]) + abs(c[1] - u[1]) + abs(c[2] - u[2])
            gy += abs(d[0] - c[0]) + abs(d[1] - c[1]) + abs(d[2] - c[2])
            edge_total += (gx + gy) / (255.0 * 12.0)
            edge_count += 1

    edge_density = edge_total / max(1, edge_count)
    center_x = cx / max(1e-6, total_w) / max(1, w - 1)
    center_y = cy / max(1e-6, total_w) / max(1, h - 1)

    return ImageMetrics(
        brightness=brightness,
        contrast=contrast,
        saturation=saturation,
        edge_density=edge_density,
        center_x=center_x,
        center_y=center_y,
    )


def derive_profile(slug: str, metrics: CaptureMetrics, image: ImageMetrics) -> StyleProfile:
    if metrics.draw_calls >= 100 and metrics.offscreen_ratio < 0.12:
        arch = "particle"
    elif metrics.multipass_score > 1.2 or metrics.offscreen_ratio > 0.6:
        arch = "multipass"
    elif metrics.unique_programs >= 10:
        arch = "shader-mix"
    elif metrics.draw_calls <= 16:
        arch = "minimal"
    else:
        arch = "solid"

    if metrics.viewport_calls + metrics.scissor_calls >= 20:
        motion = "slice"
    elif metrics.uniform_calls >= 170:
        motion = "pulse"
    elif image.center_y < 0.42:
        motion = "float"
    elif image.edge_density > 0.18:
        motion = "kinetic"
    else:
        motion = "drift"

    if image.center_x < 0.40:
        composition = "left"
    elif image.center_x > 0.60:
        composition = "right"
    elif image.center_y < 0.40:
        composition = "top"
    elif image.center_y > 0.62:
        composition = "bottom"
    else:
        composition = "center"

    if image.saturation > 0.35 and image.contrast > 0.20:
        tone = "neon"
    elif image.brightness < 0.30:
        tone = "noir"
    elif image.brightness > 0.62:
        tone = "mist"
    else:
        tone = "balanced"

    intensity = clamp(
        0.22 + metrics.draw_density * 0.62 + min(0.25, metrics.unique_programs / 36.0) + clamp(image.edge_density * 1.3, 0.0, 0.4),
        0.20,
        1.0,
    )

    family = "brutal"
    if arch in {"particle", "shader-mix"} and tone in {"balanced", "mist", "neon"}:
        family = "fluid"
    elif tone == "noir" or arch == "multipass":
        family = "cinematic"

    fingerprint = (
        f"{slug}|{metrics.total_commands}|{metrics.draw_calls}|{metrics.uniform_calls}|"
        f"{image.brightness:.4f}|{image.saturation:.4f}|{image.center_x:.4f}|{image.center_y:.4f}"
    )
    seed = int(hashlib.sha1(fingerprint.encode("utf-8")).hexdigest()[:8], 16)

    return StyleProfile(
        arch=arch,
        motion=motion,
        composition=composition,
        tone=tone,
        intensity=intensity,
        style_family=family,
        seed=seed,
    )


def pick_vertical(slug: str, url: str | None, profile: StyleProfile) -> str:
    text = f"{slug} {url or ''}".lower()
    map_kw = {
        "apparel": ["kuon", "taillet", "fashion", "wear", "atelier"],
        "mobility": ["polestar", "auto", "car", "mobility"],
        "gaming": ["rtfkt", "madbox", "game", "spline"],
        "spatial": ["spatial", "oncyber", "immersive", "lusion", "activetheory"],
        "luxury": ["richard", "mille", "joopiter", "moooi"],
        "editorial": ["design", "studio", "islands", "embraced", "chartogne"],
    }
    for vertical, kws in map_kw.items():
        if any(k in text for k in kws):
            return vertical

    if profile.style_family == "fluid":
        return "spatial"
    if profile.style_family == "cinematic":
        return "luxury"
    return "editorial"


def derive_story(
    spec_slug: str,
    url: str | None,
    profile: StyleProfile,
    campaign_idx: int = 0,
    story_rotation: int = 0,
) -> StorySpec:
    vertical = pick_vertical(spec_slug, url, profile)

    packs: Dict[str, Dict[str, List[str] | List[Tuple[str, str, str]]]] = {
        "apparel": {
            "campaign_name": ["Drape Protocol", "Edge Tailoring", "Quiet Runway"],
            "objective": [
                "Launch a capsule apparel drop with premium perception.",
                "Translate tailoring craft into social-first conversion assets.",
                "Position the line as a cultural statement, not just products.",
            ],
            "audience": [
                "Style-aware urban shoppers, 20-35.",
                "Early-adopter fashion communities.",
                "Design-led buyers evaluating detail before price.",
            ],
            "promise": [
                "Material narrative and silhouette clarity before price.",
                "Motion-first proof for fabric behavior and fit.",
                "Styling confidence through disciplined sequencing.",
            ],
            "motif": ["Moving fabric and seam lines.", "Tailored edges and folds.", "Wind-cut silhouettes and layered planes."],
            "scene": ["A garment form crossing wind and light.", "A textile object rotating under studio beams.", "A silhouette field in constant motion."],
            "hook": ["A silhouette appears before product details.", "Movement is shown before labels.", "The first frame behaves like runway teaser."],
            "tension": ["Texture and fit are hard to trust online.", "Still-only LPs fail to prove drape.", "Brand tone drifts between editorial and commerce."],
            "resolve": ["Motion reveals drape, stitch rhythm, proportion.", "C1-C4 turns form into purchase confidence.", "Design language stays consistent to offer."],
            "cta": ["Reserve early access for the first drop.", "Join launch-night priority list.", "Unlock pre-order with fit guide access."],
            "c1_title": ["Silhouette In Motion", "Material Before Logo", "Runway Field"],
            "c1_sub": ["Fabric behavior becomes the hero.", "Craft appears before branding.", "Movement defines collection identity."],
            "c2_title": ["Fit Signal Interface", "Drape Control Surface", "Lookbook Reactor"],
            "c3_title": ["Capsule Story", "Tailoring Evidence Flow", "Collection Conversion Arc"],
            "c3_sub": ["From material logic to styling proof.", "Show the why before the what.", "Narrative and commerce aligned by motion."],
            "c4_title": ["Apparel Experience House", "Capsule Launch Platform", "Brand + Drop System"],
            "c4_quote": ["Movement is proof of quality.", "Fit is a story, not a spec.", "A garment earns trust in motion."],
            "nav": [("Concept", "Fit Proof", "Drop"), ("Material", "Lookbook", "Reserve"), ("Story", "Details", "Launch")],
        },
        "spatial": {
            "campaign_name": ["Depth Protocol", "Portal Sequence", "Field Engine"],
            "objective": [
                "Showcase immersive platform use cases for brands.",
                "Turn wow demos into conversion-ready narratives.",
                "Present spatial interaction as practical campaign format.",
            ],
            "audience": [
                "Creative directors and innovation leads.",
                "Brand strategists seeking immersive differentiation.",
                "Experience teams evaluating spatial prototypes.",
            ],
            "promise": [
                "Interaction depth that supports business storytelling.",
                "Immersion with clear hierarchy and next action.",
                "Spatial craft linked to campaign outcomes.",
            ],
            "motif": ["Spatial fields and layered portals.", "Depth rails and volumetric rings.", "Reactive grids with portal seams."],
            "scene": ["A floating environment stitched by light paths.", "Portals opening as viewers move.", "A 3D field shifts around content anchors."],
            "hook": ["Depth changes as the viewer moves.", "Scene response creates immediate curiosity.", "Interaction reveals narrative skeleton."],
            "tension": ["Most demos look impressive but feel empty.", "Immersive pages lack business endpoint.", "Motion quality is high, message clarity low."],
            "resolve": ["Every motion maps to content intention.", "Story arc drives from wonder to CTA.", "C1-C4 keeps immersion and conversion aligned."],
            "cta": ["Request a custom prototype sprint.", "Book an immersive concept workshop.", "Start a 7-day spatial pilot."],
            "c1_title": ["Spatial Prelude", "Portal Ignition", "Depth As Hook"],
            "c1_sub": ["Scene reacts with narrative intent.", "Immersion starts in first frame.", "Space itself carries the message."],
            "c2_title": ["Immersive Front Volume", "Depth Interface Layer", "Portal Interaction Deck"],
            "c3_title": ["Experience Flow", "Spatial Campaign Story", "Immersion To Action Path"],
            "c3_sub": ["Context, interaction, conversion in one path.", "Each section answers why this world matters.", "Visual depth tied to strategic purpose."],
            "c4_title": ["Spatial Program Site", "Immersive Campaign Hub", "3D Narrative Platform"],
            "c4_quote": ["Depth needs purpose to become memory.", "Interaction is a means, not the end.", "Immersion must land in action."],
            "nav": [("World", "Flow", "Pilot"), ("Portal", "Narrative", "Launch"), ("Depth", "Proof", "Request")],
        },
        "gaming": {
            "campaign_name": ["Artifact Run", "Season Pulse", "Signal Arena"],
            "objective": [
                "Promote a digital collectible or season drop.",
                "Increase whitelist conversion with clearer lore.",
                "Connect gameplay utility and identity in one campaign.",
            ],
            "audience": ["Community-first players and collectors.", "Drop hunters and NFT-native gamers.", "Discord-native world-building audiences."],
            "promise": ["High-energy identity with rarity clarity.", "Lore, utility, and release timing aligned.", "Visual behavior signals value, not noise."],
            "motif": ["Shard clusters and signal scans.", "Core fragments and orbiting glyphs.", "Pulse grids and rarity beacons."],
            "scene": ["A core artifact generating pulses.", "An arena object triggering layered effects.", "A relic field opening in sequence."],
            "hook": ["An unknown object emits structured noise.", "The drop begins as visual anomaly.", "First motion hints at rarity tier."],
            "tension": ["Hype grows fast but trust fades quickly.", "Drop pages over-index on noise.", "Community wants proof of utility."],
            "resolve": ["Visual system ties rarity, utility, timing.", "Sequence explains why to join now.", "C1-C4 proves value before mint CTA."],
            "cta": ["Join whitelist and unlock pre-mint info.", "Enter allowlist before reveal window.", "Claim early signal access now."],
            "c1_title": ["Artifact Awakening", "Rarity Pulse", "Season Zero Trigger"],
            "c1_sub": ["Rarity starts with visual behavior.", "Signal indicates tier before copy.", "Lore ignition in one scene."],
            "c2_title": ["Drop Control Deck", "Rarity Radar UI", "Mint Signal Console"],
            "c3_title": ["Season Architecture", "Lore + Utility Flow", "Campaign To Mint Narrative"],
            "c3_sub": ["Lore, utility, and release moments aligned.", "Utility shown, not promised.", "Community action guided by sequence."],
            "c4_title": ["Community Hub", "Season Launch Site", "Drop Conversion Platform"],
            "c4_quote": ["Signal without utility is only noise.", "Hype is easy. Trust is designed.", "Rarity needs narrative discipline."],
            "nav": [("Lore", "Utility", "Mint"), ("World", "Proof", "Join"), ("Signal", "Tiers", "Access")],
        },
        "luxury": {
            "campaign_name": ["Ritual Surface", "Maison Tempo", "Precision Aura"],
            "objective": ["Build prestige for high-value products.", "Increase private preview requests.", "Translate craftsmanship into digital authority."],
            "audience": ["Affluent customers and collectors.", "Detail-obsessed buyers avoiding loud ads.", "Premium audiences expecting restraint."],
            "promise": ["Scarcity and craft through tempo.", "Material authenticity via controlled reveals.", "Prestige built by discipline, not excess."],
            "motif": ["Metal edges and slow reveals.", "Micro-detail highlights and shadow bands.", "Deep contrast and ceremonial motion."],
            "scene": ["A crafted object under ritual lighting.", "A detail-led reveal in darkness.", "Material facets emerging in rhythm."],
            "hook": ["A detail appears before full object.", "First frame withholds, then rewards.", "Close-up craftsmanship starts story."],
            "tension": ["Luxury online often feels generic.", "Templates reduce high-value authority.", "Craft stories are rarely paced right."],
            "resolve": ["Pacing and material cues restore authority.", "Campaign moves from intrigue to appointment.", "Each scene reinforces scarcity and trust."],
            "cta": ["Schedule private preview access.", "Request collector-only appointment.", "Unlock private viewing invitation."],
            "c1_title": ["Ritual Surface", "Detail Before Name", "Maison Signal"],
            "c1_sub": ["Craft detail first, logo second.", "Authority starts in restraint.", "Scarcity conveyed through pacing."],
            "c2_title": ["Collector Viewport", "Private Preview Interface", "Craft Lens Panel"],
            "c3_title": ["Craft Ledger", "Prestige Narrative", "From Detail To Access"],
            "c3_sub": ["Material origin, process, final form connected.", "Every module reinforces authority.", "No noise, only controlled meaning."],
            "c4_title": ["Maison Platform", "Collector Access Site", "Luxury Narrative House"],
            "c4_quote": ["Precision is emotional language.", "Restraint is conversion strategy.", "Craft should never be rushed."],
            "nav": [("Craft", "Legacy", "Access"), ("Detail", "Story", "Preview"), ("Maison", "Proof", "Invite")],
        },
        "editorial": {
            "campaign_name": ["Intent Grid", "Signal Essay", "Campaign Thesis"],
            "objective": ["Turn abstract references into clear campaign.", "Move from exploration to client-ready narrative.", "Build social-to-LP campaign with clarity."],
            "audience": ["Brand teams evaluating direction.", "Founders needing design with business intent.", "Marketing teams selecting concepts."],
            "promise": ["Coherent argument from hook to offer.", "Experiment without losing strategic clarity.", "One narrative line across C1-C4."],
            "motif": ["Editorial panels and rhythm grids.", "Thesis blocks and pacing lines.", "Typography + geometry as one voice."],
            "scene": ["Typography and form move in sequence.", "Manifesto panel system with depth.", "Concept modules unfold across sections."],
            "hook": ["Clear thesis appears in first second.", "First frame states intent, not style.", "Viewer gets topic before details."],
            "tension": ["Beautiful visuals fail when purpose is unclear.", "Assets drift when structure is weak.", "Aesthetic quality can hide strategy gaps."],
            "resolve": ["Each section answers what/why/next.", "Story spine prevents template output.", "Campaign closes with concrete offer."],
            "cta": ["Start with one-week concept sprint.", "Book campaign architecture session.", "Approve pilot and ship first posts."],
            "c1_title": ["Intent Before Style", "Thesis Frame", "Purpose In Motion"],
            "c1_sub": ["Form is selected to carry a message.", "Concept appears instantly.", "Aesthetic follows narrative intent."],
            "c2_title": ["Narrative Front View", "Concept Signal HUD", "Story Control Surface"],
            "c3_title": ["Campaign Logic", "Narrative Evidence Page", "From Idea To Offer"],
            "c3_sub": ["Concept statement to conversion-ready structure.", "Sections explain value in sequence.", "Narrative quality drives design quality."],
            "c4_title": ["Brand Narrative Site", "Campaign Program Platform", "Concept To Conversion House"],
            "c4_quote": ["Aesthetics are only step one.", "Design must carry intent.", "Narrative quality is product quality."],
            "nav": [("Thesis", "Proof", "Offer"), ("Intent", "Flow", "Action"), ("Concept", "Evidence", "Start")],
        },
    }

    pool = packs.get(vertical, packs["editorial"])

    core_seed = int(
        hashlib.sha1(f"{spec_slug}|{url or ''}|{profile.seed}|{story_rotation}|{vertical}".encode("utf-8")).hexdigest()[:8],
        16,
    )
    slot = (core_seed + campaign_idx) % 3

    def pick(key: str, offset: int = 0) -> str:
        vals = pool[key]
        if not isinstance(vals, list) or not vals:
            return ""
        return str(vals[(slot + offset) % len(vals)])

    nav_values = pool.get("nav", [])
    nav = ("Story", "Flow", "Action")
    if isinstance(nav_values, list) and nav_values:
        nav = nav_values[(slot + 1) % len(nav_values)]
    nav_a, nav_b, nav_c = nav

    phase_sets = [
        ("Hook", "Mechanism", "Proof", "Offer"),
        ("Tease", "Interaction", "Narrative", "Action"),
        ("Ignition", "System", "Evidence", "Conversion"),
    ]
    phase_c1, phase_c2, phase_c3, phase_c4 = phase_sets[slot]

    campaign_id = f"cp{campaign_idx + 1:02d}"
    campaign_name = pick("campaign_name", 2)
    story_id = f"{vertical}-{profile.arch}-{profile.motion}-{campaign_id}"

    return StorySpec(
        campaign_id=campaign_id,
        campaign_name=campaign_name,
        story_id=story_id,
        vertical=vertical,
        objective=pick("objective", 0),
        audience=pick("audience", 3),
        promise=pick("promise", 5),
        motif=pick("motif", 7),
        scene=pick("scene", 9),
        hook=pick("hook", 1),
        tension=pick("tension", 4),
        resolve=pick("resolve", 6),
        cta=pick("cta", 8),
        c1_title=pick("c1_title", 10),
        c1_sub=pick("c1_sub", 12),
        c2_title=pick("c2_title", 14),
        c3_title=pick("c3_title", 16),
        c3_sub=pick("c3_sub", 18),
        c4_title=pick("c4_title", 20),
        c4_quote=pick("c4_quote", 22),
        nav_a=nav_a,
        nav_b=nav_b,
        nav_c=nav_c,
        phase_c1=phase_c1,
        phase_c2=phase_c2,
        phase_c3=phase_c3,
        phase_c4=phase_c4,
    )


def select_family(spec: CaptureSpec, campaign_idx: int, family_shift: int = 0) -> str:
    start = int(hashlib.sha1(f"{spec.slug}|{spec.profile.seed}".encode("utf-8")).hexdigest()[:8], 16) % len(FAMILY_VARIANTS)
    ordered = FAMILY_VARIANTS[start:] + FAMILY_VARIANTS[:start]

    preferred = {
        "fluid": ["fluid", "organic", "spectral"],
        "brutal": ["brutal", "grid", "industrial"],
        "cinematic": ["cinematic", "editorial", "luxe"],
    }.get(spec.profile.style_family, [])

    if preferred:
        preferred_ordered = [f for f in preferred if f in ordered]
        remaining = [f for f in ordered if f not in preferred_ordered]
        ordered = preferred_ordered + remaining

    return ordered[(campaign_idx + max(0, family_shift)) % len(ordered)]


def family_mode(family: str) -> str:
    return FAMILY_MODE.get(family, "cinematic")


def synthesize_systems(spec: CaptureSpec, story: StorySpec, family: str, campaign_idx: int) -> Dict[str, str]:
    mode = family_mode(family)
    motion_system = {
        "slice": "segmented-pan",
        "pulse": "breathing-loop",
        "float": "levitation-drift",
        "kinetic": "high-orbit",
        "drift": "ambient-drift",
    }.get(spec.profile.motion, "ambient-drift")
    light_system = {
        "fluid": "volumetric-soft",
        "brutal": "hard-key-rim",
        "cinematic": "chiaroscuro-rim",
    }[mode]
    material_system = {
        "fluid": "glass-liquid",
        "brutal": "matte-solid",
        "cinematic": "metal-velvet",
    }[mode]
    camera_system = {
        "left": "offset-left",
        "right": "offset-right",
        "top": "tilt-top",
        "bottom": "tilt-bottom",
        "center": "hero-center",
    }.get(spec.profile.composition, "hero-center")
    layout_system = {
        "fluid": "curved-flow-layout",
        "brutal": "modular-grid-layout",
        "cinematic": "editorial-sequence-layout",
    }[mode]
    typography_system = FAMILY_TYPEFACE.get(family, "'Syne',sans-serif")
    background_system = {
        "fluid": "radial-fluid-gradient",
        "brutal": "split-tone-planes",
        "cinematic": "dark-vignette-gradient",
    }[mode]
    object_system = {
        "fluid": "blob-field",
        "brutal": "solid-stack",
        "cinematic": "ring-ribbon-scene",
    }[mode]
    signature = f"{family}|{layout_system}|{object_system}|{camera_system}|{motion_system}"
    return {
        "mode": mode,
        "background_system": background_system,
        "object_system": object_system,
        "light_system": light_system,
        "camera_system": camera_system,
        "typography_system": typography_system,
        "layout_system": layout_system,
        "motion_system": motion_system,
        "material_system": material_system,
        "signature": signature,
        "story_phase": f"{story.phase_c1}>{story.phase_c2}>{story.phase_c3}>{story.phase_c4}",
    }


def load_capture_spec(capture_dir: Path, demo_image: Path | None, slug_override: str | None) -> CaptureSpec:
    meta_path = capture_dir / "meta.json"
    url = None
    slug = capture_dir.name
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        url = meta.get("url")
        slug = meta.get("slug") or slug

    hero = capture_dir / "shots" / "hero.png"
    if demo_image:
        hero = demo_image
    if not hero.exists():
        raise FileNotFoundError(f"hero image not found: {hero}")

    if slug_override:
        slug = slug_override
    if not slug or slug.strip() in {".", ".."}:
        slug = "demo"

    palette = extract_palette(hero)
    metrics = load_capture_metrics(capture_dir / "spector" / "capture.json")
    image_metrics = compute_image_metrics(hero)
    profile = derive_profile(slug, metrics, image_metrics)
    story = derive_story(slug, url, profile)

    return CaptureSpec(
        slug=slugify(slug),
        url=url,
        palette=palette,
        hero_path=hero,
        metrics=metrics,
        image_metrics=image_metrics,
        profile=profile,
        story=story,
    )


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_file(path: Path, content: str) -> None:
    ensure_dir(path.parent)
    path.write_text(content, encoding="utf-8")


def build_theme(spec: CaptureSpec, campaign_idx: int) -> Dict[str, str | float]:
    p = list(spec.palette)
    shift = campaign_idx % len(p)
    p = p[shift:] + p[:shift]

    tone = spec.profile.tone
    if tone == "noir":
        bg0 = mix_hex(p[0], "#030407", 0.55)
        bg1 = mix_hex(p[1], "#0f131b", 0.60)
    elif tone == "mist":
        bg0 = mix_hex(p[0], "#eef2f7", 0.66)
        bg1 = mix_hex(p[1], "#dbe4ef", 0.54)
    elif tone == "neon":
        bg0 = mix_hex(p[0], "#070b18", 0.62)
        bg1 = mix_hex(p[1], hue_shift(p[2], 36, sat_mul=1.4, val_mul=1.05), 0.38)
    else:
        bg0 = mix_hex(p[0], "#0a0d14", 0.36)
        bg1 = mix_hex(p[1], "#151a24", 0.42)

    accent = hue_shift(p[2], 90 + campaign_idx * 27, sat_mul=1.25, val_mul=1.12)
    accent_alt = hue_shift(p[3], -120 + campaign_idx * 21, sat_mul=1.16, val_mul=1.1)
    edge = mix_hex(p[4], "#ffffff", 0.24)
    ink = text_color(bg0)
    ink_soft = mix_hex(ink, bg0, 0.42)

    return {
        "bg0": bg0,
        "bg1": bg1,
        "accent": accent,
        "accent_alt": accent_alt,
        "edge": edge,
        "ink": ink,
        "ink_soft": ink_soft,
        "intensity": spec.profile.intensity,
    }


def palette_id(theme: Dict[str, str | float], campaign_id: str, unit: str) -> str:
    raw = "|".join(
        [
            str(theme["bg0"]),
            str(theme["bg1"]),
            str(theme["accent"]),
            str(theme["accent_alt"]),
            campaign_id,
            unit,
        ]
    )
    return "pal-" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:10]


def layout_id(systems: Dict[str, str], campaign_id: str, unit: str) -> str:
    raw = "|".join(
        [
            systems.get("signature", ""),
            systems.get("layout_system", ""),
            systems.get("camera_system", ""),
            campaign_id,
            unit,
        ]
    )
    return "lay-" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:10]


def family_tokens(family: str) -> Tuple[str, str, str]:
    tokens = {
        "fluid": ("FLOW", "FIELD", "GATE"),
        "organic": ("GROWTH", "BIOME", "PULSE"),
        "spectral": ("PRISM", "WAVE", "AURA"),
        "brutal": ("BLOCK", "SYSTEM", "GRID"),
        "grid": ("MESH", "CELL", "STACK"),
        "industrial": ("FORGE", "RAIL", "CORE"),
        "cinematic": ("SCENE", "TEMPO", "LIGHT"),
        "editorial": ("THESIS", "FRAME", "PACE"),
        "luxe": ("RITUAL", "DETAIL", "GLOW"),
    }
    return tokens.get(family, ("SCENE", "FORM", "MOVE"))


def make_preview(path: Path, theme: Dict[str, str | float], family: str, unit: str) -> None:
    w, h = 1080, 1920
    img = Image.new("RGB", (w, h), str(theme["bg0"]))
    draw = ImageDraw.Draw(img, "RGBA")

    draw.rectangle([0, 0, w, int(h * 0.42)], fill=str(theme["bg1"]))
    accent = str(theme["accent"])
    alt = str(theme["accent_alt"])

    mode = family_mode(family)
    if family == "organic":
        draw.polygon([(180, 500), (540, 310), (900, 620), (790, 1180), (300, 1280)], outline=accent, width=10)
        draw.ellipse([260, 620, 830, 1360], fill=(0, 0, 0, 0), outline=alt, width=7)
    elif family == "spectral":
        draw.polygon([(120, 360), (960, 360), (850, 1300), (220, 1480)], fill=(0, 0, 0, 0), outline=accent, width=10)
        draw.rectangle([210, 770, 890, 830], outline=alt, width=8)
    elif mode == "fluid":
        draw.ellipse([170, 360, 910, 1140], fill=(0, 0, 0, 0), outline=accent, width=10)
        draw.ellipse([260, 620, 800, 1320], fill=(0, 0, 0, 0), outline=alt, width=8)
    elif family == "grid":
        for i in range(6):
            draw.line([(140 + i * 140, 360), (140 + i * 140, 1540)], fill=accent if i % 2 else alt, width=6)
        for j in range(6):
            draw.line([(140, 360 + j * 200), (940, 360 + j * 200)], fill=alt if j % 2 else accent, width=6)
    elif family == "industrial":
        draw.polygon([(140, 520), (920, 430), (980, 860), (210, 940)], outline=accent, width=10)
        draw.rectangle([170, 1060, 910, 1210], outline=alt, width=10)
        draw.rectangle([240, 1300, 840, 1440], outline=accent, width=10)
    elif mode == "brutal":
        draw.rectangle([120, 260, 960, 760], outline=accent, width=10)
        draw.rectangle([120, 840, 560, 1400], outline=alt, width=10)
        draw.rectangle([580, 840, 960, 1400], outline=accent, width=10)
    elif family == "editorial":
        draw.rectangle([140, 380, 940, 560], outline=accent, width=9)
        draw.rectangle([140, 650, 940, 920], outline=alt, width=9)
        draw.rectangle([140, 1010, 940, 1460], outline=accent, width=9)
    elif family == "luxe":
        draw.ellipse([180, 420, 900, 1180], fill=(0, 0, 0, 0), outline=accent, width=9)
        draw.polygon([(540, 510), (860, 820), (540, 1140), (220, 820)], outline=alt, width=9)
    else:
        draw.polygon([(130, 300), (950, 520), (860, 1510), (220, 1320)], outline=accent, width=10)
        draw.rectangle([150, 1540, 930, 1660], fill=alt)

    marker = {"C1": 0, "C2": 1, "C3": 2, "C4": 3}.get(unit, 0)
    draw.rectangle([120 + marker * 90, 1760, 176 + marker * 90, 1820], fill=accent)
    img.save(path)


def shared_three_setup(theme: Dict[str, str | float]) -> str:
    return Template(
        """
const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(2, window.devicePixelRatio || 1));
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.0 + $intensity * 0.18;
document.body.appendChild(renderer.domElement);
const scene = new THREE.Scene();
scene.fog = new THREE.Fog(0x05070c, 6, 26);
const camera = new THREE.PerspectiveCamera(48, window.innerWidth / window.innerHeight, 0.1, 120);
camera.position.set(0.0, 0.4, 7.0);
scene.add(new THREE.AmbientLight(0x8d97a5, 0.58));
const key = new THREE.PointLight(0xffffff, 1.9, 24);
key.position.set(3.0, 4.0, 6.0);
scene.add(key);
window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});
"""
    ).substitute(intensity=f"{float(theme['intensity']):.3f}")


def render_c1(
    spec: CaptureSpec,
    story: StorySpec,
    theme: Dict[str, str | float],
    family: str,
    systems: Dict[str, str],
    palette_sig: str,
    layout_sig: str,
) -> str:
    mode = family_mode(family)
    if family == "fluid":
        scene_code = Template(
            """
const geo = new THREE.PlaneGeometry(9, 9, 1, 1);
const mat = new THREE.ShaderMaterial({
  uniforms: {
    uTime: { value: 0 },
    uA: { value: new THREE.Color("$accent") },
    uB: { value: new THREE.Color("$accent_alt") },
    uC: { value: new THREE.Color("$bg1") }
  },
  vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
  fragmentShader: `
    varying vec2 vUv;
    uniform float uTime;
    uniform vec3 uA;
    uniform vec3 uB;
    uniform vec3 uC;
    float blob(vec2 p, vec2 c, float r){ return r / length(p-c); }
    void main(){
      vec2 p = vUv * 2.0 - 1.0;
      float t = uTime * 0.45;
      float f = 0.0;
      f += blob(p, vec2(sin(t)*0.45, cos(t*1.2)*0.3), 0.26);
      f += blob(p, vec2(cos(t*1.3)*0.4, sin(t*0.7)*0.36), 0.24);
      f += blob(p, vec2(sin(t*0.9)*0.52, sin(t*1.1)*0.4), 0.20);
      float m = smoothstep(1.1, 2.5, f);
      vec3 col = mix(uC, mix(uA, uB, vUv.y), m);
      gl_FragColor = vec4(col, 1.0);
    }
  `
});
const plane = new THREE.Mesh(geo, mat);
scene.add(plane);
let t = 0;
function animate(){
  t += 0.016;
  mat.uniforms.uTime.value = t;
  renderer.render(scene, camera);
  requestAnimationFrame(animate);
}
animate();
"""
        ).substitute(accent=theme["accent"], accent_alt=theme["accent_alt"], bg1=theme["bg1"])
    elif family == "organic":
        scene_code = Template(
            """
const root = new THREE.Group();
scene.add(root);
const geo = new THREE.IcosahedronGeometry(1.8, 64);
const mat = new THREE.ShaderMaterial({
  uniforms: {
    uTime: { value: 0.0 },
    uA: { value: new THREE.Color("$accent") },
    uB: { value: new THREE.Color("$accent_alt") }
  },
  wireframe: false,
  vertexShader: `
    uniform float uTime;
    varying vec3 vN;
    void main(){
      vN = normalize(normalMatrix * normal);
      vec3 p = position + normal * (0.16 * sin(uTime*1.2 + position.y*3.1));
      gl_Position = projectionMatrix * modelViewMatrix * vec4(p, 1.0);
    }
  `,
  fragmentShader: `
    uniform vec3 uA; uniform vec3 uB;
    varying vec3 vN;
    void main(){
      float m = clamp(vN.y * 0.5 + 0.5, 0.0, 1.0);
      gl_FragColor = vec4(mix(uA, uB, m), 1.0);
    }
  `
});
const blob = new THREE.Mesh(geo, mat);
root.add(blob);
let t = 0;
function animate(){
  t += 0.015;
  mat.uniforms.uTime.value = t;
  root.rotation.y += 0.0035;
  root.rotation.x = Math.sin(t*0.45)*0.22;
  renderer.render(scene, camera);
  requestAnimationFrame(animate);
}
animate();
"""
        ).substitute(accent=theme["accent"], accent_alt=theme["accent_alt"])
    elif family == "spectral":
        scene_code = Template(
            """
const root = new THREE.Group();
scene.add(root);
for (let i=0;i<12;i++){
  const c = new THREE.CatmullRomCurve3([
    new THREE.Vector3(-2.1, -0.8 + i*0.13, 0.2),
    new THREE.Vector3(-0.4, 0.8 - i*0.08, 0.9),
    new THREE.Vector3(0.8, -0.5 + i*0.03, -0.6),
    new THREE.Vector3(2.2, 0.5 - i*0.06, 0.2),
  ]);
  const t = new THREE.Mesh(
    new THREE.TubeGeometry(c, 180, 0.03 + i*0.006, 14, false),
    new THREE.MeshPhysicalMaterial({color:i%2?"$accent":"$accent_alt",metalness:0.65,roughness:0.16,clearcoat:0.7})
  );
  t.position.z = -i*0.12;
  root.add(t);
}
let t = 0;
function animate(){
  t += 0.012;
  root.rotation.z = Math.sin(t*0.8)*0.14;
  root.position.y = Math.sin(t*0.6)*0.09;
  renderer.render(scene, camera);
  requestAnimationFrame(animate);
}
animate();
"""
        ).substitute(accent=theme["accent"], accent_alt=theme["accent_alt"])
    elif family == "grid":
        scene_code = Template(
            """
const root = new THREE.Group();
scene.add(root);
for (let x=-5;x<=5;x++){
  for (let y=-4;y<=4;y++){
    const m = new THREE.Mesh(
      new THREE.BoxGeometry(0.24, 0.24, 0.24),
      new THREE.MeshStandardMaterial({ color: (x+y)%2?"$accent":"$accent_alt", metalness:0.24, roughness:0.58 })
    );
    m.position.set(x*0.45, y*0.45, -Math.abs(x*y)*0.02);
    root.add(m);
  }
}
let t = 0;
function animate(){
  t += 0.014;
  root.rotation.y = Math.sin(t*0.42)*0.3;
  root.rotation.x = Math.sin(t*0.31)*0.2;
  renderer.render(scene, camera);
  requestAnimationFrame(animate);
}
animate();
"""
        ).substitute(accent=theme["accent"], accent_alt=theme["accent_alt"])
    elif family == "industrial":
        scene_code = Template(
            """
const root = new THREE.Group();
scene.add(root);
for (let i=0;i<18;i++){
  const beam = new THREE.Mesh(
    new THREE.CylinderGeometry(0.05 + (i%3)*0.01, 0.05 + (i%3)*0.01, 3.2, 24),
    new THREE.MeshStandardMaterial({ color: i%2 ? "$accent":"$edge", metalness:0.55, roughness:0.35 })
  );
  beam.position.set((i%6-2.5)*0.65, -0.8 + Math.floor(i/6)*0.9, -i*0.15);
  beam.rotation.z = Math.PI * 0.5;
  beam.rotation.y = i*0.13;
  root.add(beam);
}
let t=0;
function animate(){
  t += 0.013;
  root.rotation.y = Math.sin(t*0.52)*0.36;
  root.position.y = Math.sin(t*0.7)*0.08;
  renderer.render(scene, camera);
  requestAnimationFrame(animate);
}
animate();
"""
        ).substitute(accent=theme["accent"], edge=theme["edge"])
    elif family == "editorial":
        scene_code = Template(
            """
const root = new THREE.Group();
scene.add(root);
for (let i=0;i<7;i++){
  const p = new THREE.Mesh(
    new THREE.PlaneGeometry(4.2, 0.46, 1, 1),
    new THREE.MeshStandardMaterial({ color: i%2 ? "$accent":"$accent_alt", side:THREE.DoubleSide, metalness:0.18, roughness:0.42, transparent:true, opacity:0.62 })
  );
  p.position.set(0, -1.3 + i*0.44, -i*0.5);
  p.rotation.set(-0.22 + i*0.04, 0.08 + i*0.05, 0.04);
  root.add(p);
}
let t=0;
function animate(){
  t += 0.01;
  root.rotation.y = Math.sin(t*0.45)*0.2;
  renderer.render(scene, camera);
  requestAnimationFrame(animate);
}
animate();
"""
        ).substitute(accent=theme["accent"], accent_alt=theme["accent_alt"])
    elif family == "luxe":
        scene_code = Template(
            """
const root = new THREE.Group();
scene.add(root);
const gem = new THREE.Mesh(
  new THREE.OctahedronGeometry(1.3, 1),
  new THREE.MeshPhysicalMaterial({ color: "$accent", metalness:0.55, roughness:0.08, transmission:0.5, thickness:0.5, clearcoat:0.9 })
);
root.add(gem);
for (let i=0;i<5;i++){
  const ring = new THREE.Mesh(
    new THREE.TorusGeometry(1.8 + i*0.26, 0.025, 16, 180),
    new THREE.MeshPhysicalMaterial({ color: i%2 ? "$accent_alt":"$edge", metalness:0.8, roughness:0.2, clearcoat:0.8 })
  );
  ring.rotation.set(Math.PI/2 + i*0.1, i*0.16, i*0.08);
  ring.position.z = -i*0.38;
  root.add(ring);
}
let t=0;
function animate(){
  t += 0.011;
  gem.rotation.x = t*0.22;
  gem.rotation.y = t*0.3;
  root.rotation.z = Math.sin(t*0.65)*0.14;
  renderer.render(scene, camera);
  requestAnimationFrame(animate);
}
animate();
"""
        ).substitute(accent=theme["accent"], accent_alt=theme["accent_alt"], edge=theme["edge"])
    elif mode == "brutal":
        scene_code = Template(
            """
const root = new THREE.Group();
scene.add(root);
for (let i = 0; i < 48; i++) {
  const m = new THREE.Mesh(
    new THREE.BoxGeometry(0.3 + (i%3)*0.12, 0.3 + (i%4)*0.18, 0.3 + (i%2)*0.14),
    new THREE.MeshStandardMaterial({ color: i%2 ? "$accent" : "$accent_alt", metalness: 0.35, roughness: 0.46 })
  );
  const x = (i % 8 - 3.5) * 0.56;
  const y = (Math.floor(i / 8) - 2.5) * 0.62;
  m.position.set(x, y, - (i % 6) * 0.25);
  m.rotation.set(i * 0.04, i * 0.08, i * 0.03);
  root.add(m);
}
let t = 0;
function animate(){
  t += 0.012;
  root.rotation.y = Math.sin(t*0.6) * 0.45;
  root.rotation.x = Math.sin(t*0.3) * 0.2;
  renderer.render(scene, camera);
  requestAnimationFrame(animate);
}
animate();
"""
        ).substitute(accent=theme["accent"], accent_alt=theme["accent_alt"])
    else:
        scene_code = Template(
            """
const root = new THREE.Group();
scene.add(root);
for (let i = 0; i < 7; i++) {
  const ring = new THREE.Mesh(
    new THREE.TorusGeometry(0.9 + i * 0.2, 0.04 + i * 0.006, 18, 190),
    new THREE.MeshPhysicalMaterial({ color: i%2 ? "$accent" : "$accent_alt", metalness: 0.72, roughness: 0.22, clearcoat: 0.6 })
  );
  ring.rotation.set(Math.PI/2 + i*0.08, i*0.2, i*0.06);
  ring.position.z = -i * 0.55;
  root.add(ring);
}
let t = 0;
function animate(){
  t += 0.01;
  root.rotation.z = Math.sin(t*1.2) * 0.15;
  root.position.y = Math.sin(t*0.8) * 0.12;
  renderer.render(scene, camera);
  requestAnimationFrame(animate);
}
animate();
"""
        ).substitute(accent=theme["accent"], accent_alt=theme["accent_alt"])

    css = "font-family:%s;" % FAMILY_TYPEFACE.get(family, "'Syne',sans-serif")
    tmpl = Template(
        """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<meta name="palette-id" content="$palette_id" />
<meta name="layout-id" content="$layout_id" />
<meta name="system-signature" content="$system_signature" />
<title>C1_$slug</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Archivo+Black&family=Bebas+Neue&family=Cormorant+Garamond:wght@500;700&family=Outfit:wght@400;700&family=Playfair+Display:wght@500;700&family=Prata&family=Sora:wght@400;700&family=Space+Grotesk:wght@400;600;700&family=Syne:wght@400;700&display=swap');
:root{--bg0:$bg0;--bg1:$bg1;--ink:$ink;--edge:$edge;}
html,body{margin:0;width:100%;height:100%;overflow:hidden;background:linear-gradient(160deg,var(--bg1),var(--bg0));$font}
canvas{display:block}
.info{position:fixed;left:4vw;bottom:6vh;z-index:3;color:var(--ink);max-width:min(56ch,90vw)}
.info h1{margin:0 0 8px;font-size:clamp(34px,6vw,84px);line-height:.9}
.info p{margin:0;opacity:.8}
.badge{position:fixed;left:4vw;top:3vh;z-index:3;color:var(--ink);letter-spacing:.12em;font-size:11px;opacity:.7}
</style></head>
<body data-spector-source="$slug" data-family="$family" data-campaign="$campaign_id" data-mode="$mode" data-layout-system="$layout_system" data-object-system="$object_system" data-motion-system="$motion_system">
<div class="badge">$campaign_id / $phase_c1 / $family / C1</div>
<div class="info"><h1>$title</h1><p>$sub</p></div>
<script src="../../../../../../../vendor/three/three.min.js"></script>
<script>
$setup
$scene
</script>
</body></html>"""
    )
    return tmpl.substitute(
        slug=spec.slug,
        family=family,
        campaign_id=story.campaign_id,
        phase_c1=story.phase_c1,
        title=story.c1_title,
        sub=story.c1_sub,
        bg0=theme["bg0"],
        bg1=theme["bg1"],
        ink=theme["ink"],
        edge=theme["edge"],
        font=css,
        setup=shared_three_setup(theme),
        scene=scene_code,
        palette_id=palette_sig,
        layout_id=layout_sig,
        system_signature=systems.get("signature", ""),
        mode=mode,
        layout_system=systems.get("layout_system", ""),
        object_system=systems.get("object_system", ""),
        motion_system=systems.get("motion_system", ""),
    )


def render_c2(
    spec: CaptureSpec,
    story: StorySpec,
    theme: Dict[str, str | float],
    family: str,
    systems: Dict[str, str],
    palette_sig: str,
    layout_sig: str,
) -> str:
    mode = family_mode(family)
    token_a, token_b, token_c = family_tokens(family)
    panel = f'<div class="rail"><span>{token_a}</span><span>{token_b}</span><span>{token_c}</span></div>'
    frame_radius = {"fluid": "28px", "organic": "12px", "spectral": "44px", "brutal": "4px", "grid": "0px", "industrial": "2px", "cinematic": "30px", "editorial": "8px", "luxe": "34px"}.get(family, "24px")

    scene_code = Template(
        """
const root = new THREE.Group();
scene.add(root);
if ("$family" === "fluid") {
  const geo = new THREE.SphereGeometry(1.2, 120, 120);
  const mat = new THREE.MeshPhysicalMaterial({ color: "$accent", metalness: 0.1, roughness: 0.05, transmission: 0.92, thickness: 0.9 });
  root.add(new THREE.Mesh(geo, mat));
} else if ("$family" === "organic") {
  const geo = new THREE.IcosahedronGeometry(1.4, 28);
  const mat = new THREE.MeshStandardMaterial({ color: "$accent", metalness: 0.18, roughness: 0.34, flatShading: true });
  const m = new THREE.Mesh(geo, mat);
  root.add(m);
} else if ("$family" === "spectral") {
  for (let i=0;i<7;i++){
    const c = new THREE.Mesh(new THREE.TorusKnotGeometry(0.7 + i*0.12, 0.03, 140, 18), new THREE.MeshPhysicalMaterial({color:i%2?"$accent":"$accent_alt",metalness:0.74,roughness:0.22,clearcoat:0.7}));
    c.rotation.set(i*0.2, i*0.18, i*0.1);
    c.position.z = -i*0.22;
    root.add(c);
  }
} else if ("$family" === "brutal") {
  for (let i=0;i<14;i++){
    const b = new THREE.Mesh(new THREE.BoxGeometry(2.4,0.16,0.5),new THREE.MeshStandardMaterial({color:i%2?"$accent":"$accent_alt",metalness:0.28,roughness:0.58}));
    b.position.set(0,-1.2+i*0.22,-i*0.35);
    b.rotation.y=i*0.16;
    root.add(b);
  }
} else if ("$family" === "grid") {
  for (let x=-4;x<=4;x++){
    for (let y=-3;y<=3;y++){
      const b = new THREE.Mesh(new THREE.BoxGeometry(0.26,0.26,0.26),new THREE.MeshStandardMaterial({color:(x+y)%2?"$accent":"$edge",metalness:0.18,roughness:0.64}));
      b.position.set(x*0.46,y*0.46,-Math.abs(x*y)*0.04);
      root.add(b);
    }
  }
} else if ("$family" === "industrial") {
  for (let i=0;i<18;i++){
    const b = new THREE.Mesh(new THREE.CylinderGeometry(0.04,0.04,2.8,22),new THREE.MeshStandardMaterial({color:i%2?"$accent":"$edge",metalness:0.58,roughness:0.3}));
    b.position.set((i%6-2.5)*0.6,-1.0+Math.floor(i/6)*1.0,-i*0.18);
    b.rotation.z = Math.PI*0.5;
    b.rotation.y = i*0.12;
    root.add(b);
  }
} else if ("$family" === "editorial") {
  for (let i=0;i<9;i++){
    const p = new THREE.Mesh(new THREE.PlaneGeometry(3.8,0.32),new THREE.MeshStandardMaterial({color:i%2?"$accent":"$accent_alt",side:THREE.DoubleSide,transparent:true,opacity:0.58}));
    p.position.set(0,-1.2+i*0.3,-i*0.44);
    p.rotation.y = i*0.08;
    root.add(p);
  }
} else if ("$family" === "luxe") {
  const core = new THREE.Mesh(new THREE.OctahedronGeometry(1.0,0),new THREE.MeshPhysicalMaterial({color:"$accent",metalness:0.62,roughness:0.08,transmission:0.5,thickness:0.7,clearcoat:1.0}));
  root.add(core);
  for (let i=0;i<6;i++){
    const r = new THREE.Mesh(new THREE.TorusGeometry(1.5+i*0.22,0.03,14,170),new THREE.MeshPhysicalMaterial({color:i%2?"$accent_alt":"$edge",metalness:0.86,roughness:0.2}));
    r.rotation.set(Math.PI/2 + i*0.1,i*0.2,i*0.1);
    r.position.z = -i*0.3;
    root.add(r);
  }
} else {
  for (let i=0;i<9;i++){
    const c = new THREE.CatmullRomCurve3([
      new THREE.Vector3(-2.3,-0.8+i*0.2,0.2),
      new THREE.Vector3(-0.8,0.6-i*0.1,0.8),
      new THREE.Vector3(0.9,-0.2+i*0.05,-0.7),
      new THREE.Vector3(2.2,0.7-i*0.08,0.1)
    ]);
    const t = new THREE.Mesh(new THREE.TubeGeometry(c,170,0.04+i*0.01,12,false),new THREE.MeshPhysicalMaterial({color:i%2?"$accent":"$accent_alt",metalness:0.7,roughness:0.2,clearcoat:0.6}));
    root.add(t);
  }
}
let t=0;
function animate(){
 t+=0.011;
 root.rotation.y = Math.sin(t*0.7)*0.26;
 root.rotation.x = Math.sin(t*0.3)*0.12;
 renderer.render(scene,camera);
 requestAnimationFrame(animate);
}
animate();
"""
    ).substitute(family=family, accent=theme["accent"], accent_alt=theme["accent_alt"], edge=theme["edge"])

    tmpl = Template(
        """<!doctype html>
<html><head><meta charset="utf-8" /><meta name="viewport" content="width=device-width,initial-scale=1" />
<meta name="palette-id" content="$palette_id" />
<meta name="layout-id" content="$layout_id" />
<meta name="system-signature" content="$system_signature" />
<title>C2_$slug</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&display=swap');
:root{--bg0:$bg0;--bg1:$bg1;--ink:$ink;--soft:$ink_soft;--accent:$accent;--edge:$edge;}
html,body{margin:0;width:100%;height:100%;overflow:hidden;background:radial-gradient(120% 80% at 80% 10%,color-mix(in srgb,var(--accent) 20%,transparent),transparent 56%),linear-gradient(150deg,var(--bg1),var(--bg0));font-family:'Space Grotesk',sans-serif}
canvas{display:block}
.frame{position:fixed;inset:8vh 5vw;border:1px solid color-mix(in srgb,var(--edge) 70%,transparent);border-radius:$frame_radius;pointer-events:none}
.copy{position:fixed;left:7vw;top:13vh;z-index:3;color:var(--ink);max-width:min(40ch,74vw)}
.copy h2{margin:0 0 10px;font-size:clamp(26px,4vw,54px);line-height:.95}
.copy p{margin:0 0 6px;color:var(--soft)}
.rail{position:fixed;right:7vw;top:14vh;display:grid;gap:8px;z-index:3;color:var(--ink);font-size:11px;letter-spacing:.14em}
.badge{position:fixed;left:7vw;top:4vh;color:var(--ink);font-size:11px;letter-spacing:.12em;opacity:.75;z-index:3}
</style></head>
<body data-spector-source="$slug" data-family="$family" data-campaign="$campaign_id" data-mode="$mode" data-layout-system="$layout_system" data-object-system="$object_system" data-motion-system="$motion_system">
<div class="badge">$campaign_id / $phase_c2 / $family / C2</div>
<div class="copy"><h2>$title</h2><p>$hook</p><p>$promise</p></div>
$panel
<div class="frame"></div>
<script src="../../../../../../../vendor/three/three.min.js"></script>
<script>
$setup
$scene
</script>
</body></html>"""
    )
    return tmpl.substitute(
        slug=spec.slug,
        family=family,
        campaign_id=story.campaign_id,
        phase_c2=story.phase_c2,
        title=story.c2_title,
        hook=story.hook,
        promise=story.promise,
        panel=panel,
        bg0=theme["bg0"],
        bg1=theme["bg1"],
        ink=theme["ink"],
        ink_soft=theme["ink_soft"],
        accent=theme["accent"],
        edge=theme["edge"],
        frame_radius=frame_radius,
        setup=shared_three_setup(theme),
        scene=scene_code,
        palette_id=palette_sig,
        layout_id=layout_sig,
        system_signature=systems.get("signature", ""),
        mode=mode,
        layout_system=systems.get("layout_system", ""),
        object_system=systems.get("object_system", ""),
        motion_system=systems.get("motion_system", ""),
    )


def render_c3(
    spec: CaptureSpec,
    story: StorySpec,
    theme: Dict[str, str | float],
    family: str,
    systems: Dict[str, str],
    palette_sig: str,
    layout_sig: str,
) -> str:
    mode = family_mode(family)
    modules = {
        "fluid": "<section class='hero'><h1>$c3_title</h1><p>$c3_sub</p><p>$hook</p></section><section class='softgrid'><article></article><article></article><article></article></section><section class='softline'><div></div><div></div></section>",
        "organic": "<section class='hero'><h1>$c3_title</h1><p>$resolve</p></section><section class='organic-grid'><article></article><article></article></section><section class='pillars'><div></div><div></div><div></div></section>",
        "spectral": "<section class='hero'><h1>$c3_title</h1><p>$hook</p></section><section class='timeline'><div></div><div></div><div></div></section><section class='spectral-ribbon'><article></article><article></article><article></article></section>",
        "brutal": "<section class='hero'><h1>$c3_title</h1><p>$tension</p></section><section class='hardgrid'><article></article><article></article><article></article><article></article></section><section class='hardsplit'><article></article><article></article></section>",
        "grid": "<section class='hero'><h1>$c3_title</h1><p>$tension</p></section><section class='matrix'><article></article><article></article><article></article><article></article><article></article><article></article></section><section class='softline'><div></div><div></div></section>",
        "industrial": "<section class='hero'><h1>$c3_title</h1><p>$resolve</p></section><section class='rail'><article></article><article></article><article></article></section><section class='duo'><article></article><article></article></section>",
        "cinematic": "<section class='hero'><h1>$c3_title</h1><p>$resolve</p></section><section class='timeline'><div></div><div></div><div></div></section><section class='duo'><article></article><article></article></section>",
        "editorial": "<section class='hero'><h1>$c3_title</h1><p>$c3_sub</p></section><section class='editorial-stack'><article></article><article></article><article></article></section><section class='hardsplit'><article></article><article></article></section>",
        "luxe": "<section class='hero'><h1>$c3_title</h1><p>$resolve</p></section><section class='duo'><article></article><article></article></section><section class='quote-band'><div></div><div></div></section>",
    }
    section_html = Template(modules.get(family, modules["cinematic"])).substitute(
        c3_title=story.c3_title,
        c3_sub=story.c3_sub,
        hook=story.hook,
        tension=story.tension,
        resolve=story.resolve,
    )

    scene_code = Template(
        """
const canvas = document.getElementById('bg');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(2, window.devicePixelRatio || 1));
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 0.92 + $intensity * 0.2;
const scene = new THREE.Scene();
scene.fog = new THREE.Fog(0x06080c, 6, 24);
const camera = new THREE.PerspectiveCamera(48, window.innerWidth / window.innerHeight, 0.1, 120);
camera.position.set(0.0, 0.5, 7.5);
scene.add(new THREE.AmbientLight(0x8f99a8, 0.52));
const key = new THREE.PointLight(0xffffff, 1.8, 24); key.position.set(3.0,4.0,6.2); scene.add(key);
const group = new THREE.Group(); scene.add(group);
if ("$mode" === "fluid") {
  for (let i=0;i<10;i++){
    const m = new THREE.Mesh(new THREE.TorusGeometry(0.7+i*0.14,0.03,14,150), new THREE.MeshStandardMaterial({color:i%2?"$accent":"$accent_alt",metalness:0.4,roughness:0.35,transparent:true,opacity:0.55}));
    m.rotation.set(i*0.2,i*0.16,i*0.08); m.position.y=-0.8+i*0.2; group.add(m);
  }
} else if ("$mode" === "brutal") {
  for (let i=0;i<20;i++){
    const m = new THREE.Mesh(new THREE.BoxGeometry(3.2,0.12,0.8), new THREE.MeshStandardMaterial({color:i%2?"$accent":"$edge",metalness:0.2,roughness:0.62}));
    m.position.set((i%2?0.5:-0.5), -1.2+i*0.18, -i*0.45); m.rotation.y=i*0.14; group.add(m);
  }
} else {
  for (let i=0;i<8;i++){
    const p = new THREE.Mesh(new THREE.PlaneGeometry(4.6,0.44,30,6), new THREE.MeshStandardMaterial({color:i%2?"$accent":"$accent_alt",side:THREE.DoubleSide,metalness:0.3,roughness:0.38,transparent:true,opacity:0.5}));
    p.position.set(0,-1+i*0.34,-i*0.6); p.rotation.set(-0.4+i*0.05,i*0.1,i*0.05); group.add(p);
  }
}
let scrollY=0; window.addEventListener('scroll',()=>{scrollY=window.scrollY||0;});
let t=0;
function animate(){
  t+=0.009;
  const sn=Math.min(1.3,scrollY/Math.max(1,document.body.scrollHeight-window.innerHeight));
  group.rotation.y = Math.sin(t*0.5)*0.24;
  group.position.y = Math.sin(t*0.8)*0.1 - sn*0.85;
  renderer.render(scene,camera);
  requestAnimationFrame(animate);
}
animate();
window.addEventListener('resize',()=>{camera.aspect=window.innerWidth/window.innerHeight;camera.updateProjectionMatrix();renderer.setSize(window.innerWidth,window.innerHeight);});
"""
    ).substitute(
        intensity=f"{float(theme['intensity']):.3f}", mode=mode, accent=theme["accent"], accent_alt=theme["accent_alt"], edge=theme["edge"]
    )

    hero_font = "'Instrument Serif',serif" if mode != "brutal" else FAMILY_TYPEFACE.get(family, "'Space Grotesk',sans-serif")
    tmpl = Template(
        """<!doctype html><html><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<meta name="palette-id" content="$palette_id" />
<meta name="layout-id" content="$layout_id" />
<meta name="system-signature" content="$system_signature" />
<title>C3_$slug</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;600;700&family=Instrument+Serif&display=swap');
:root{--bg0:$bg0;--bg1:$bg1;--ink:$ink;--soft:$ink_soft;--edge:$edge;--accent:$accent}
html,body{margin:0;background:linear-gradient(180deg,var(--bg1),var(--bg0));color:var(--ink)}
#bg{position:fixed;inset:0;z-index:0}
main{position:relative;z-index:1;font-family:'IBM Plex Sans',sans-serif}
section{min-height:84vh;padding:12vh 8vw;display:grid;gap:1.1rem;align-content:center}
.hero h1{margin:0;font-family:$hero_font;font-size:clamp(44px,8vw,100px);line-height:.92;max-width:9ch}
.hero p{margin:0;max-width:58ch;color:var(--soft)}
.softgrid,.hardgrid,.duo,.hardsplit,.organic-grid,.spectral-ribbon,.editorial-stack,.quote-band,.rail,.matrix{display:grid;gap:1rem}
.softgrid{grid-template-columns:repeat(3,minmax(0,1fr))}
.hardgrid{grid-template-columns:repeat(4,minmax(0,1fr))}
.matrix{grid-template-columns:repeat(3,minmax(0,1fr))}
.organic-grid{grid-template-columns:1fr 1fr}
.duo,.hardsplit{grid-template-columns:1.3fr .7fr}
.rail{grid-template-columns:repeat(3,minmax(0,1fr))}
.editorial-stack{grid-template-columns:1fr}
.quote-band{grid-template-columns:repeat(2,minmax(0,1fr))}
.softgrid article,.hardgrid article,.duo article,.hardsplit article,.organic-grid article,.spectral-ribbon article,.editorial-stack article,.rail article,.matrix article{min-height:200px;border-radius:20px;border:1px solid color-mix(in srgb,var(--edge) 70%,transparent);background:color-mix(in srgb,var(--bg1) 62%,transparent)}
.matrix article{border-radius:0}
.timeline{display:grid;gap:18px}
.timeline div{height:10px;border-radius:999px;background:linear-gradient(90deg,var(--accent),transparent 72%)}
.softline,.pillars{display:grid;gap:16px}
.softline div{height:24px;border-radius:999px;background:linear-gradient(90deg,var(--accent),transparent 72%)}
.pillars div{min-height:140px;border-radius:999px;border:1px solid color-mix(in srgb,var(--edge) 70%,transparent)}
.quote-band div{height:28px;border-radius:999px;background:linear-gradient(90deg,var(--accent),transparent 72%)}
.meta{position:fixed;top:2.5vh;left:3vw;z-index:4;color:var(--soft);font-size:11px;letter-spacing:.12em}
@media(max-width:920px){.softgrid,.hardgrid,.duo,.hardsplit,.organic-grid,.rail,.matrix,.quote-band{grid-template-columns:1fr}}
</style></head>
<body data-spector-source="$slug" data-family="$family" data-campaign="$campaign_id" data-mode="$mode" data-layout-system="$layout_system" data-object-system="$object_system" data-motion-system="$motion_system">
<div class="meta">$campaign_id / $phase_c3 / $family / C3 / $objective</div>
<canvas id="bg"></canvas>
<main>
$sections
<section><p>$cta</p></section>
</main>
<script src="../../../../../../../vendor/three/three.min.js"></script>
<script>
$scene
</script>
</body></html>"""
    )
    return tmpl.substitute(
        slug=spec.slug,
        family=family,
        campaign_id=story.campaign_id,
        phase_c3=story.phase_c3,
        objective=story.objective,
        cta=story.cta,
        bg0=theme["bg0"],
        bg1=theme["bg1"],
        ink=theme["ink"],
        ink_soft=theme["ink_soft"],
        edge=theme["edge"],
        accent=theme["accent"],
        sections=section_html,
        scene=scene_code,
        palette_id=palette_sig,
        layout_id=layout_sig,
        system_signature=systems.get("signature", ""),
        hero_font=hero_font,
        mode=mode,
        layout_system=systems.get("layout_system", ""),
        object_system=systems.get("object_system", ""),
        motion_system=systems.get("motion_system", ""),
    )


def render_c4(
    spec: CaptureSpec,
    story: StorySpec,
    theme: Dict[str, str | float],
    family: str,
    systems: Dict[str, str],
    palette_sig: str,
    layout_sig: str,
) -> str:
    mode = family_mode(family)
    family_layouts = {
        "fluid": ("left:2vw;top:4vh;flex-direction:column;border-radius:16px", "<section class='panel hero'></section><section class='panel wave'></section><section class='panel grid'></section>"),
        "organic": ("left:2vw;top:4vh;flex-direction:column;border-radius:999px", "<section class='panel hero'></section><section class='panel organic'></section><section class='panel wave'></section>"),
        "spectral": ("right:2vw;top:4vh;flex-direction:column;border-radius:28px", "<section class='panel hero'></section><section class='panel prism'></section><section class='panel timeline'></section>"),
        "brutal": ("left:50%;transform:translateX(-50%);top:2vh", "<section class='panel hero'></section><section class='panel blocks'></section><section class='panel split'></section>"),
        "grid": ("left:50%;transform:translateX(-50%);top:2vh;border-radius:0", "<section class='panel hero'></section><section class='panel matrix'></section><section class='panel split'></section>"),
        "industrial": ("left:2vw;bottom:3vh", "<section class='panel hero'></section><section class='panel rail'></section><section class='panel split'></section>"),
        "cinematic": ("right:2vw;top:4vh;flex-direction:column;border-radius:16px", "<section class='panel hero'></section><section class='panel timeline'></section><section class='panel quote'></section>"),
        "editorial": ("right:2vw;top:4vh;flex-direction:column;border-radius:6px", "<section class='panel hero'></section><section class='panel editorial'></section><section class='panel quote'></section>"),
        "luxe": ("right:2vw;top:4vh;flex-direction:column;border-radius:999px", "<section class='panel hero'></section><section class='panel luxe'></section><section class='panel quote'></section>"),
    }
    nav_pos, modules = family_layouts.get(family, family_layouts["cinematic"])

    scene_code = Template(
        """
const canvas = document.getElementById('bg');
const renderer = new THREE.WebGLRenderer({ canvas, antialias:true, alpha:true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(2, window.devicePixelRatio || 1));
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 0.92 + $intensity * 0.2;
const scene = new THREE.Scene();
scene.fog = new THREE.Fog(0x05070b, 8, 26);
const camera = new THREE.PerspectiveCamera(47, window.innerWidth / window.innerHeight, 0.1, 130);
camera.position.set(0.0, 0.4, 8.0);
scene.add(new THREE.AmbientLight(0x8d99a9, 0.52));
const key = new THREE.PointLight(0xffffff, 1.9, 26); key.position.set(3.4,4.0,6.0); scene.add(key);
const root = new THREE.Group(); scene.add(root);
if ("$mode" === "fluid") {
  for (let i=0;i<14;i++){
    const m = new THREE.Mesh(new THREE.TorusGeometry(0.8+i*0.11,0.02+i*0.003,14,140), new THREE.MeshStandardMaterial({color:i%2?"$accent":"$accent_alt",metalness:0.36,roughness:0.42,transparent:true,opacity:0.5}));
    m.rotation.set(i*0.2,i*0.14,i*0.08); m.position.z=-i*0.48; root.add(m);
  }
} else if ("$mode" === "brutal") {
  for (let i=0;i<28;i++){
    const b = new THREE.Mesh(new THREE.BoxGeometry(4.0,0.14,0.24), new THREE.MeshStandardMaterial({color:i%2?"$accent":"$edge",metalness:0.2,roughness:0.64}));
    b.position.set((i%2?0.7:-0.7),-1.4+i*0.16,-i*0.35); b.rotation.y=i*0.12; root.add(b);
  }
} else {
  for (let i=0;i<10;i++){
    const p = new THREE.Mesh(new THREE.PlaneGeometry(5.2,0.5,30,6), new THREE.MeshStandardMaterial({color:i%2?"$accent":"$accent_alt",side:THREE.DoubleSide,metalness:0.3,roughness:0.36,transparent:true,opacity:0.54}));
    p.position.set(0,-1.2+i*0.3,-i*0.62); p.rotation.set(-0.34+i*0.04,i*0.1,i*0.05); root.add(p);
  }
}
let t=0;
function animate(){
  t+=0.009;
  root.rotation.y = Math.sin(t*0.45)*0.22;
  root.position.y = Math.sin(t*0.7)*0.08;
  renderer.render(scene,camera);
  requestAnimationFrame(animate);
}
animate();
window.addEventListener('resize',()=>{camera.aspect=window.innerWidth/window.innerHeight;camera.updateProjectionMatrix();renderer.setSize(window.innerWidth,window.innerHeight);});
"""
    ).substitute(intensity=f"{float(theme['intensity']):.3f}", mode=mode, accent=theme["accent"], accent_alt=theme["accent_alt"], edge=theme["edge"])

    tmpl = Template(
        """<!doctype html><html><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<meta name="palette-id" content="$palette_id" />
<meta name="layout-id" content="$layout_id" />
<meta name="system-signature" content="$system_signature" />
<title>C4_$slug</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700&family=Prata&display=swap');
:root{--bg0:$bg0;--bg1:$bg1;--ink:$ink;--soft:$ink_soft;--edge:$edge;--accent:$accent}
html,body{margin:0;background:linear-gradient(170deg,var(--bg1),var(--bg0));color:var(--ink);font-family:'Manrope',sans-serif}
#bg{position:fixed;inset:0;z-index:0}
.app{position:relative;z-index:1;min-height:100vh}
.nav{position:fixed;$nav_pos;display:flex;gap:1rem;padding:.7rem 1rem;border:1px solid color-mix(in srgb,var(--edge) 70%,transparent);background:color-mix(in srgb,var(--bg0) 74%,transparent);backdrop-filter:blur(8px);z-index:5}
.nav a{color:var(--soft);text-decoration:none;font-size:12px;letter-spacing:.08em}
main{padding:10vh 6vw;display:grid;gap:2rem}
.intro h1{margin:0;font-family:'Prata',serif;font-size:clamp(32px,5vw,70px);line-height:.94}
.intro p{margin:.35rem 0 0;color:var(--soft);max-width:64ch}
.panel{min-height:min(74vh,740px);border:1px solid color-mix(in srgb,var(--edge) 72%,transparent);border-radius:24px;background:color-mix(in srgb,var(--bg1) 58%,transparent)}
.panel.hero{display:grid;place-items:end start;padding:2rem}
.panel.hero::before{content:'$campaign_id / $phase_c4 / $family';letter-spacing:.11em;font-size:11px;color:var(--soft)}
.panel.wave,.panel.timeline,.panel.rail,.panel.luxe{display:grid;align-content:center;gap:16px;padding:2rem}
.panel.wave::before,.panel.wave::after,.panel.timeline::before,.panel.timeline::after,.panel.rail::before,.panel.rail::after,.panel.luxe::before,.panel.luxe::after{content:'';height:12px;border-radius:999px;background:linear-gradient(90deg,var(--accent),transparent 72%)}
.panel.grid,.panel.blocks,.panel.matrix,.panel.prism,.panel.editorial{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1rem;padding:1rem}
.panel.blocks{grid-template-columns:repeat(4,minmax(0,1fr))}
.panel.matrix article,.panel.prism article,.panel.editorial article{border:1px solid color-mix(in srgb,var(--edge) 70%,transparent);min-height:130px}
.panel.split,.panel.organic{display:grid;grid-template-columns:1.2fr .8fr;gap:1rem;padding:1rem}
.panel.quote{display:grid;place-items:center;padding:2rem}
.panel.quote::before{content:'$quote';font-family:'Prata',serif;font-size:clamp(24px,3vw,40px);max-width:24ch;text-align:center;color:var(--soft)}
.panel.grid::before,.panel.grid::after,.panel.blocks::before,.panel.blocks::after,.panel.matrix::before,.panel.matrix::after,.panel.prism::before,.panel.prism::after,.panel.editorial::before,.panel.editorial::after{content:'';border:1px solid color-mix(in srgb,var(--edge) 70%,transparent);border-radius:16px}
.panel.grid > *,.panel.blocks > *,.panel.matrix > *,.panel.prism > *,.panel.editorial > *{border:1px solid color-mix(in srgb,var(--edge) 70%,transparent);border-radius:16px}
@media(max-width:920px){.nav{left:50%!important;right:auto!important;top:2vh!important;transform:translateX(-50%);flex-direction:row!important;border-radius:999px}.panel.grid,.panel.blocks,.panel.split,.panel.matrix,.panel.prism,.panel.editorial,.panel.organic{grid-template-columns:1fr}}
</style></head>
<body data-spector-source="$slug" data-family="$family" data-campaign="$campaign_id" data-mode="$mode" data-layout-system="$layout_system" data-object-system="$object_system" data-motion-system="$motion_system">
<canvas id="bg"></canvas>
<div class="app">
<nav class="nav"><a href="#top">$nav_a</a><a href="#story">$nav_b</a><a href="#offer">$nav_c</a></nav>
<main id="top">
<header class="intro"><h1>$title</h1><p>$objective</p><p>$cta</p></header>
$modules
<section id="offer"><p>$quote</p></section>
</main>
</div>
<script src="../../../../../../../vendor/three/three.min.js"></script>
<script>
$scene
</script>
</body></html>"""
    )
    return tmpl.substitute(
        slug=spec.slug,
        family=family,
        campaign_id=story.campaign_id,
        phase_c4=story.phase_c4,
        nav_pos=nav_pos,
        nav_a=story.nav_a,
        nav_b=story.nav_b,
        nav_c=story.nav_c,
        title=story.c4_title,
        objective=story.objective,
        cta=story.cta,
        quote=story.c4_quote,
        modules=modules,
        bg0=theme["bg0"],
        bg1=theme["bg1"],
        ink=theme["ink"],
        ink_soft=theme["ink_soft"],
        edge=theme["edge"],
        accent=theme["accent"],
        scene=scene_code,
        palette_id=palette_sig,
        layout_id=layout_sig,
        system_signature=systems.get("signature", ""),
        mode=mode,
        layout_system=systems.get("layout_system", ""),
        object_system=systems.get("object_system", ""),
        motion_system=systems.get("motion_system", ""),
    )


def render_unit_html(
    unit: str,
    spec: CaptureSpec,
    story: StorySpec,
    theme: Dict[str, str | float],
    family: str,
    systems: Dict[str, str],
    palette_sig: str,
    layout_sig: str,
) -> str:
    if unit == "C1":
        return render_c1(spec, story, theme, family, systems, palette_sig, layout_sig)
    if unit == "C2":
        return render_c2(spec, story, theme, family, systems, palette_sig, layout_sig)
    if unit == "C3":
        return render_c3(spec, story, theme, family, systems, palette_sig, layout_sig)
    return render_c4(spec, story, theme, family, systems, palette_sig, layout_sig)


def write_units(
    spec: CaptureSpec,
    out_root: Path,
    version: str,
    campaigns: int,
    story_rotation: int,
    campaign_start: int = 0,
    family_shift: int = 0,
) -> List[Path]:
    mapping = {
        "C1": "C1_KV",
        "C2": "C2_FV",
        "C3": "C3_LP",
        "C4": "C4_HP",
    }

    units: List[Path] = []

    for local_idx in range(max(1, campaigns)):
        campaign_idx = campaign_start + local_idx
        story = derive_story(spec.slug, spec.url, spec.profile, campaign_idx=campaign_idx, story_rotation=story_rotation)
        family = select_family(spec, campaign_idx, family_shift=family_shift)
        theme = build_theme(spec, campaign_idx)
        systems = synthesize_systems(spec, story, family, campaign_idx)
        unit_signatures: Dict[str, Dict[str, str]] = {}
        campaign_unit_dirs: List[Path] = []

        for unit, prefix in mapping.items():
            unit_name = f"{prefix}_spector-{spec.slug}_{story.campaign_id}_{version}"
            unit_dir = out_root / unit_name / "demo"
            pal_sig = palette_id(theme, story.campaign_id, unit)
            lay_sig = layout_id(systems, story.campaign_id, unit)
            html = render_unit_html(unit, spec, story, theme, family, systems, pal_sig, lay_sig)
            write_file(unit_dir / "index.html", html)
            make_preview(unit_dir / "preview.png", theme, family, unit)
            unit_signatures[unit] = {
                "palette_id": pal_sig,
                "layout_id": lay_sig,
            }
            campaign_unit_dirs.append(unit_dir)
            units.append(unit_dir)

        story_payload = {
            "campaign_id": story.campaign_id,
            "campaign_name": story.campaign_name,
            "story_id": story.story_id,
            "vertical": story.vertical,
            "family": family,
            "objective": story.objective,
            "audience": story.audience,
            "promise": story.promise,
            "motif": story.motif,
            "scene": story.scene,
            "hook": story.hook,
            "tension": story.tension,
            "resolve": story.resolve,
            "cta": story.cta,
            "phase_c1": story.phase_c1,
            "phase_c2": story.phase_c2,
            "phase_c3": story.phase_c3,
            "phase_c4": story.phase_c4,
            "systems": systems,
            "unit_signatures": unit_signatures,
        }
        for unit_dir in campaign_unit_dirs:
            write_file(unit_dir / "story.json", json.dumps(story_payload, ensure_ascii=True, indent=2))

    return units


def profile_row(spec: CaptureSpec) -> str:
    m = spec.metrics
    im = spec.image_metrics
    p = spec.profile
    return (
        f"profile={p.arch}/{p.motion}/{p.composition}/{p.tone} family={p.style_family} "
        f"intensity={p.intensity:.3f} story={spec.story.story_id} | "
        f"draw={m.draw_calls} prog={m.unique_programs} offscreen={m.offscreen_ratio:.2f} multi={m.multipass_score:.2f} | "
        f"brightness={im.brightness:.2f} sat={im.saturation:.2f} edge={im.edge_density:.2f} center=({im.center_x:.2f},{im.center_y:.2f})"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", type=str, help="capture directory with shots/hero.png")
    parser.add_argument("--demo-image", type=str, help="use image for dry run")
    parser.add_argument("--date", type=str, default=date.today().isoformat(), help="output date YYYY-MM-DD")
    parser.add_argument("--slug", type=str, help="override slug")
    parser.add_argument("--version", type=str, default="v02", help="unit version suffix")
    parser.add_argument("--campaigns", type=int, default=1, help="number of linked campaigns (C1-C4 each)")
    parser.add_argument("--campaign-start", type=int, default=0, help="campaign index start offset (0 => cp01)")
    parser.add_argument("--story-rotation", type=int, default=0, help="story dictionary rotation seed")
    parser.add_argument("--family-shift", type=int, default=0, help="family rotation offset for duplicate reruns")
    parser.add_argument("--print-profile", action="store_true", help="print derived profile")
    args = parser.parse_args()

    if not args.capture and not args.demo_image:
        raise SystemExit("--capture or --demo-image is required")

    capture_dir = Path(args.capture) if args.capture else Path(".")
    demo_image = Path(args.demo_image) if args.demo_image else None

    try:
        out_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    except ValueError as exc:
        raise SystemExit(f"invalid --date: {exc}")

    spec = load_capture_spec(capture_dir, demo_image, args.slug)

    out_root = REPO_ROOT / "04_OUTPUT" / "production" / out_date.strftime("%Y-%m") / args.date / "inbox"
    ensure_dir(out_root)

    units = write_units(
        spec,
        out_root,
        version=args.version,
        campaigns=max(1, args.campaigns),
        story_rotation=args.story_rotation,
        campaign_start=max(0, args.campaign_start),
        family_shift=max(0, args.family_shift),
    )

    print("Generated units:")
    for u in units:
        print(f"- {u}")
    if args.print_profile:
        print(profile_row(spec))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
