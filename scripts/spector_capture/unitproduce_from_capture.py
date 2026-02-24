#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Generate C1-C4 units from a Spector capture directory.

Inputs:
- capture dir with shots/hero.png and optional spector/capture.json, meta.json
- or --demo-image to run a dry pipeline test without capture

Outputs:
- 04_OUTPUT/production/YYYY-MM/YYYY-MM-DD/inbox/<unit_id>/demo/index.html
- 04_OUTPUT/production/YYYY-MM/YYYY-MM-DD/inbox/<unit_id>/demo/preview.png
"""

from __future__ import annotations
import argparse
from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path
from typing import List, Tuple
from string import Template

from PIL import Image, ImageDraw

REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class CaptureSpec:
    slug: str
    url: str | None
    palette: List[str]
    bg_dark: str
    bg_mid: str
    complexity: str


def slugify(text: str) -> str:
    return "".join(ch if ch.isalnum() else "-" for ch in text).strip("-")[:80]


def hex_color(rgb: Tuple[int, int, int]) -> str:
    return "#%02x%02x%02x" % rgb


def extract_palette(image_path: Path, n: int = 6) -> List[str]:
    img = Image.open(image_path).convert("RGB").resize((200, 200))
    colors = img.getcolors(200 * 200)
    if not colors:
        return ["#0b0b0b", "#1b1b1b", "#2b2b2b", "#e0e0e0", "#a0a0a0", "#606060"]
    colors.sort(reverse=True)
    palette = []
    for _, rgb in colors:
        hx = hex_color(rgb)
        if hx not in palette:
            palette.append(hx)
        if len(palette) >= n:
            break
    while len(palette) < n:
        palette.append(palette[-1])
    return palette


def classify_complexity(capture_json: Path | None) -> str:
    if not capture_json or not capture_json.exists():
        return "unknown"
    size = capture_json.stat().st_size
    if size > 8_000_000:
        return "high"
    if size > 2_000_000:
        return "mid"
    return "low"


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
    bg_dark = palette[0]
    bg_mid = palette[1]
    complexity = classify_complexity(capture_dir / "spector" / "capture.json")

    return CaptureSpec(slug=slugify(slug), url=url, palette=palette, bg_dark=bg_dark, bg_mid=bg_mid, complexity=complexity)


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def write_file(path: Path, content: str) -> None:
    ensure_dir(path.parent)
    path.write_text(content, encoding="utf-8")


def make_preview(path: Path, palette: List[str], accent: str) -> None:
    w, h = 1080, 1920
    img = Image.new("RGB", (w, h), palette[0])
    draw = ImageDraw.Draw(img, "RGBA")
    draw.rectangle([0, 0, w, h // 2], fill=palette[1])
    draw.ellipse([260, 640, 820, 1200], outline=accent, width=8)
    draw.rectangle([140, 1400, 940, 1520], fill=accent)
    img.save(path)


def template_c1(spec: CaptureSpec, palette_id: str, layout_id: str) -> str:
    p = spec.palette
    tmpl = Template("""<!DOCTYPE html>
<html lang=\"en\">
<head>
<meta charset=\"utf-8\" />
<meta name=\"viewport\" content=\"width=device-width, height=device-height, initial-scale=1\" />
<meta name=\"palette-id\" content=\"$palette_id\" />
<meta name=\"layout-id\" content=\"$layout_id\" />
<title>C1_KV_spector_$slug</title>
<style>
:root {
  --bg-1: $p0;
  --bg-2: $p1;
  --accent: $p2;
}
html, body {
  margin: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
  background: radial-gradient(120% 80% at 70% 20%, $p1 0%, $p0 55%, #050505 100%);
}
#grain {
  position: absolute;
  inset: 0;
  background-image: repeating-linear-gradient(45deg, rgba(255,255,255,0.03) 0 1px, transparent 1px 3px);
  mix-blend-mode: soft-light;
  opacity: 0.5;
}
canvas { display: block; }
</style>
</head>
<body data-spector-source=\"$slug\">
<div id=\"grain\"></div>
<script src=\"../../../../../../../vendor/three/three.min.js\"></script>
<script>
const scene = new THREE.Scene();
scene.fog = new THREE.Fog(0x050505, 6, 14);
const camera = new THREE.PerspectiveCamera(48, window.innerWidth / window.innerHeight, 0.1, 100);
camera.position.set(0.8, 0.2, 5.2);
const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(1);
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.15;
document.body.appendChild(renderer.domElement);

scene.add(new THREE.AmbientLight(0x555555, 0.7));
const key = new THREE.SpotLight(0xffffff, 2.4, 16, Math.PI / 6, 0.4, 1.2);
key.position.set(3.2, 3.1, 4.2);
scene.add(key);
const rim = new THREE.PointLight(0xffcc99, 1.4, 10);
rim.position.set(-3.0, -1.2, 2.4);
scene.add(rim);

const group = new THREE.Group();
const core = new THREE.Mesh(new THREE.IcosahedronGeometry(0.5, 2), new THREE.MeshPhysicalMaterial({
  color: 0xffffff,
  metalness: 0.9,
  roughness: 0.18,
  clearcoat: 0.7,
  clearcoatRoughness: 0.12
}));
core.position.set(0.0, -0.1, 0.1);

const ring = new THREE.Mesh(new THREE.TorusKnotGeometry(0.9, 0.18, 220, 36), new THREE.MeshStandardMaterial({
  color: 0x333333,
  metalness: 0.8,
  roughness: 0.3
}));
ring.rotation.set(0.3, 0.7, 0.2);

const halo = new THREE.Mesh(new THREE.TorusGeometry(1.4, 0.05, 32, 200, Math.PI * 1.6), new THREE.MeshStandardMaterial({
  color: 0xffffff,
  metalness: 0.4,
  roughness: 0.3,
  transparent: true,
  opacity: 0.5
}));
halo.rotation.x = Math.PI / 2.4;
halo.position.set(-0.2, 0.3, 0.1);

for (const obj of [core, ring, halo]) group.add(obj);
scene.add(group);

const target = { x: 0, y: 0 };
window.addEventListener('pointermove', (e) => {
  target.x = (e.clientX / window.innerWidth - 0.5) * 0.3;
  target.y = (e.clientY / window.innerHeight - 0.5) * 0.2;
});
let t = 0;
function animate() {
  t += 0.01;
  ring.rotation.y += 0.004;
  core.rotation.y -= 0.006;
  halo.rotation.z += 0.0014;
  group.position.y = Math.sin(t * 0.7) * 0.05;
  camera.position.x += (target.x - camera.position.x) * 0.06;
  camera.position.y += (target.y - camera.position.y) * 0.06;
  camera.lookAt(0.1, -0.05, 0);
  renderer.render(scene, camera);
  requestAnimationFrame(animate);
}
animate();
window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});
</script>
</body>
</html>""")
    return tmpl.substitute(
        palette_id=palette_id,
        layout_id=layout_id,
        slug=spec.slug,
        p0=p[0],
        p1=p[1],
        p2=p[2],
    )


def template_c2(spec: CaptureSpec, palette_id: str, layout_id: str) -> str:
    p = spec.palette
    tmpl = Template("""<!DOCTYPE html>
<html lang=\"en\">
<head>
<meta charset=\"utf-8\" />
<meta name=\"viewport\" content=\"width=device-width, height=device-height, initial-scale=1\" />
<meta name=\"palette-id\" content=\"$palette_id\" />
<meta name=\"layout-id\" content=\"$layout_id\" />
<title>C2_FV_spector_$slug</title>
<style>
:root {
  --bg-1: $p1;
  --bg-2: $p0;
  --accent: $p3;
}
html, body {
  margin: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
  background: radial-gradient(120% 80% at 72% 14%, $p1 0%, $p0 50%, #040404 100%);
  font-family: "Trebuchet MS", sans-serif;
}
#hud {
  position: absolute;
  left: 6vw;
  top: 10vh;
  display: grid;
  gap: 12px;
}
.hud-bar {
  width: 120px;
  height: 6px;
  background: linear-gradient(90deg, $p3, rgba(0,0,0,0));
  opacity: 0.8;
}
#frame {
  position: absolute;
  inset: 6vh 5vw;
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: 24px;
  pointer-events: none;
}
canvas { display: block; }
</style>
</head>
<body data-spector-source=\"$slug\">
<div id=\"hud\"><div class=\"hud-bar\"></div><div class=\"hud-bar\"></div></div>
<div id=\"frame\"></div>
<script src=\"../../../../../../../vendor/three/three.min.js\"></script>
<script>
const scene = new THREE.Scene();
scene.fog = new THREE.Fog(0x050505, 8, 18);
const camera = new THREE.PerspectiveCamera(52, window.innerWidth / window.innerHeight, 0.1, 100);
camera.position.set(0.2, 0.2, 6.0);
const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(1);
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.1;
document.body.appendChild(renderer.domElement);
scene.add(new THREE.AmbientLight(0x666666, 0.7));
const key = new THREE.DirectionalLight(0xffffff, 2.2);
key.position.set(3, 4, 5);
scene.add(key);
const arcGroup = new THREE.Group();
const ring = new THREE.Mesh(new THREE.TorusGeometry(1.4, 0.05, 20, 220), new THREE.MeshStandardMaterial({ color: 0xffffff, metalness: 0.5, roughness: 0.25 }));
ring.rotation.x = Math.PI / 2.2;
arcGroup.add(ring);
const curve = new THREE.CatmullRomCurve3([
  new THREE.Vector3(-2.2, -0.4, -0.6),
  new THREE.Vector3(-0.6, 0.4, 0.4),
  new THREE.Vector3(1.0, 0.1, 0.6),
  new THREE.Vector3(2.2, 0.6, -0.2)
]);
const tube = new THREE.TubeGeometry(curve, 200, 0.12, 12, false);
const sweep = new THREE.Mesh(tube, new THREE.MeshPhysicalMaterial({ color: 0xffffff, metalness: 0.7, roughness: 0.2, clearcoat: 0.6 }));
arcGroup.add(sweep);
arcGroup.position.set(0.6, 0.2, 0);
scene.add(arcGroup);
const target = { x: 0, y: 0 };
window.addEventListener('pointermove', (e) => {
  target.x = (e.clientX / window.innerWidth - 0.5) * 0.5;
  target.y = (e.clientY / window.innerHeight - 0.5) * 0.4;
});
let t = 0;
function animate() {
  t += 0.01;
  arcGroup.rotation.y = t * 0.2;
  arcGroup.rotation.x = Math.sin(t * 0.6) * 0.12;
  arcGroup.position.y = Math.sin(t * 0.8) * 0.08;
  camera.position.x += (target.x - camera.position.x) * 0.05;
  camera.position.y += (target.y - camera.position.y) * 0.05;
  camera.lookAt(0.4, 0.1, 0);
  renderer.render(scene, camera);
  requestAnimationFrame(animate);
}
animate();
window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});
</script>
</body>
</html>""")
    return tmpl.substitute(
        palette_id=palette_id,
        layout_id=layout_id,
        slug=spec.slug,
        p0=p[0],
        p1=p[1],
        p3=p[3],
    )


def template_c3(spec: CaptureSpec, palette_id: str, layout_id: str) -> str:
    p = spec.palette
    tmpl = Template("""<!DOCTYPE html>
<html lang=\"en\">
<head>
<meta charset=\"utf-8\" />
<meta name=\"viewport\" content=\"width=device-width, height=device-height, initial-scale=1\" />
<meta name=\"palette-id\" content=\"$palette_id\" />
<meta name=\"layout-id\" content=\"$layout_id\" />
<title>C3_LP_spector_$slug</title>
<style>
:root {
  --bg-1: $p0;
  --bg-2: $p1;
  --accent: $p4;
  --ink: rgba(240, 240, 240, 0.9);
}
html, body {
  margin: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(180deg, $p1 0%, $p0 55%, #050505 100%);
  color: var(--ink);
  font-family: "Times New Roman", serif;
}
canvas {
  position: fixed;
  inset: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
}
main { position: relative; z-index: 1; }
section {
  min-height: 100vh;
  padding: 12vh 10vw;
  display: grid;
  gap: 3vh;
  align-content: center;
}
.card {
  border: 1px solid rgba(255,255,255,0.2);
  background: rgba(5, 5, 5, 0.5);
  border-radius: 18px;
  height: 160px;
}
</style>
</head>
<body data-spector-source=\"$slug\">
<canvas id=\"scene\"></canvas>
<main>
  <section>
    <div style=\"font-size:48px; max-width:520px;\">Temporal stacks shaped by the capture.</div>
  </section>
  <section style=\"grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 2vw;\">
    <div class=\"card\"></div>
    <div class=\"card\"></div>
    <div class=\"card\"></div>
  </section>
</main>
<script src=\"../../../../../../../vendor/three/three.min.js\"></script>
<script>
const canvas = document.getElementById('scene');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(1);
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.0;
const scene = new THREE.Scene();
scene.fog = new THREE.Fog(0x050505, 6, 18);
const camera = new THREE.PerspectiveCamera(50, window.innerWidth / window.innerHeight, 0.1, 100);
camera.position.set(0.0, 0.6, 6.2);
scene.add(new THREE.AmbientLight(0x666666, 0.7));
const key = new THREE.PointLight(0xffffff, 2.0, 16);
key.position.set(2.6, 3.2, 4.4);
scene.add(key);
const stacks = new THREE.Group();
const boxGeo = new THREE.BoxGeometry(1.2, 0.2, 0.6);
for (let i = 0; i < 7; i++) {
  const mat = new THREE.MeshStandardMaterial({ color: 0xffffff, metalness: 0.3, roughness: 0.45, transparent: true, opacity: 0.8 });
  const box = new THREE.Mesh(boxGeo, mat);
  box.position.set(-0.6 + (i % 3) * 0.7, -0.6 + i * 0.25, -i * 0.2);
  box.rotation.y = i * 0.2;
  stacks.add(box);
}
scene.add(stacks);
const target = { x: 0, y: 0 };
window.addEventListener('pointermove', (e) => {
  target.x = (e.clientX / window.innerWidth - 0.5) * 0.3;
  target.y = (e.clientY / window.innerHeight - 0.5) * 0.2;
});
let t = 0;
function animate() {
  t += 0.01;
  stacks.rotation.y = Math.sin(t * 0.3) * 0.3;
  stacks.position.y = Math.sin(t * 0.4) * 0.08;
  camera.position.x += (target.x - camera.position.x) * 0.05;
  camera.position.y += (0.6 + target.y - camera.position.y) * 0.04;
  camera.lookAt(0, 0, 0);
  renderer.render(scene, camera);
  requestAnimationFrame(animate);
}
animate();
window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});
</script>
</body>
</html>""")
    return tmpl.substitute(
        palette_id=palette_id,
        layout_id=layout_id,
        slug=spec.slug,
        p0=p[0],
        p1=p[1],
        p4=p[4],
    )


def template_c4(spec: CaptureSpec, palette_id: str, layout_id: str) -> str:
    p = spec.palette
    tmpl = Template("""<!DOCTYPE html>
<html lang=\"en\">
<head>
<meta charset=\"utf-8\" />
<meta name=\"viewport\" content=\"width=device-width, height=device-height, initial-scale=1\" />
<meta name=\"palette-id\" content=\"$palette_id\" />
<meta name=\"layout-id\" content=\"$layout_id\" />
<title>C4_HP_spector_$slug</title>
<style>
:root {
  --bg-1: $p0;
  --bg-2: $p1;
  --accent: $p5;
}
html, body {
  margin: 0;
  width: 100%;
  height: 100%;
  background: radial-gradient(120% 80% at 60% 12%, $p1 0%, $p0 55%, #040404 100%);
  color: rgba(255, 255, 255, 0.85);
  font-family: "Palatino", "Times New Roman", serif;
}
canvas {
  position: fixed;
  inset: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
}
main { position: relative; z-index: 1; }
section {
  min-height: 80vh;
  padding: 12vh 8vw;
  display: grid;
  gap: 2.5vh;
  align-content: center;
}
.band {
  height: 18px;
  border-radius: 999px;
  background: linear-gradient(90deg, rgba(255,255,255,0.6), rgba(0,0,0,0));
}
.grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 2vw;
}
.tile {
  height: 180px;
  border: 1px solid rgba(255,255,255,0.25);
  border-radius: 20px;
  background: rgba(8, 8, 8, 0.6);
}
</style>
</head>
<body data-spector-source=\"$slug\">
<canvas id=\"scene\"></canvas>
<main>
  <section>
    <div style=\"font-size:52px; max-width:520px;\">Captured structure, expanded into panels.</div>
    <div class=\"band\"></div>
    <div class=\"band\"></div>
  </section>
  <section>
    <div class=\"grid\">
      <div class=\"tile\"></div>
      <div class=\"tile\"></div>
      <div class=\"tile\"></div>
    </div>
  </section>
</main>
<script src=\"../../../../../../../vendor/three/three.min.js\"></script>
<script>
const canvas = document.getElementById('scene');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(1);
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.05;
const scene = new THREE.Scene();
scene.fog = new THREE.Fog(0x050505, 7, 18);
const camera = new THREE.PerspectiveCamera(48, window.innerWidth / window.innerHeight, 0.1, 100);
camera.position.set(0.0, 0.6, 7.0);
scene.add(new THREE.AmbientLight(0x666666, 0.8));
const key = new THREE.PointLight(0xffffff, 2.0, 16);
key.position.set(2.8, 3.2, 4.6);
scene.add(key);
const group = new THREE.Group();
const panelGeo = new THREE.PlaneGeometry(4.2, 1.1, 32, 8);
for (let i = 0; i < 5; i++) {
  const mat = new THREE.MeshStandardMaterial({ color: 0xffffff, metalness: 0.2, roughness: 0.6, side: THREE.DoubleSide });
  const panel = new THREE.Mesh(panelGeo, mat);
  panel.position.set(0, -1.0 + i * 0.6, -i * 0.4);
  panel.rotation.x = -0.3 + i * 0.05;
  panel.rotation.y = i * 0.08;
  group.add(panel);
}
scene.add(group);
const target = { x: 0, y: 0 };
window.addEventListener('pointermove', (e) => {
  target.x = (e.clientX / window.innerWidth - 0.5) * 0.4;
  target.y = (e.clientY / window.innerHeight - 0.5) * 0.3;
});
let t = 0;
function animate() {
  t += 0.01;
  group.rotation.y = Math.sin(t * 0.4) * 0.2;
  group.position.y = Math.sin(t * 0.6) * 0.08;
  camera.position.x += (target.x - camera.position.x) * 0.05;
  camera.position.y += (0.6 + target.y - camera.position.y) * 0.04;
  camera.lookAt(0, -0.2, 0);
  renderer.render(scene, camera);
  requestAnimationFrame(animate);
}
animate();
window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});
</script>
</body>
</html>""")
    return tmpl.substitute(
        palette_id=palette_id,
        layout_id=layout_id,
        slug=spec.slug,
        p0=p[0],
        p1=p[1],
        p5=p[5],
    )


def write_units(spec: CaptureSpec, output_date: str, out_root: Path) -> List[Path]:
    palette_ids = {
        "C1": f"spector-{spec.slug}-p1",
        "C2": f"spector-{spec.slug}-p2",
        "C3": f"spector-{spec.slug}-p3",
        "C4": f"spector-{spec.slug}-p4",
    }
    layout_ids = {
        "C1": f"spector-{spec.slug}-l1",
        "C2": f"spector-{spec.slug}-l2",
        "C3": f"spector-{spec.slug}-l3",
        "C4": f"spector-{spec.slug}-l4",
    }

    units = []
    mapping = {
        "C1": (f"C1_KV_spector-{spec.slug}_v01", template_c1),
        "C2": (f"C2_FV_spector-{spec.slug}_v01", template_c2),
        "C3": (f"C3_LP_spector-{spec.slug}_v01", template_c3),
        "C4": (f"C4_HP_spector-{spec.slug}_v01", template_c4),
    }

    for key, (unit_name, tmpl) in mapping.items():
        unit_dir = out_root / unit_name / "demo"
        html = tmpl(spec, palette_ids[key], layout_ids[key])
        write_file(unit_dir / "index.html", html)
        accent = spec.palette[(2 + list(mapping.keys()).index(key)) % len(spec.palette)]
        make_preview(unit_dir / "preview.png", spec.palette, accent)
        units.append(unit_dir)

    return units


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", type=str, help="capture directory with shots/hero.png")
    parser.add_argument("--demo-image", type=str, help="use an image for dry run")
    parser.add_argument("--date", type=str, default=date.today().isoformat(), help="output date YYYY-MM-DD")
    parser.add_argument("--slug", type=str, help="override slug for unit ids")
    args = parser.parse_args()

    if not args.capture and not args.demo_image:
        raise SystemExit("--capture or --demo-image is required")

    capture_dir = Path(args.capture) if args.capture else Path(".")
    demo_image = Path(args.demo_image) if args.demo_image else None

    spec = load_capture_spec(capture_dir, demo_image, args.slug)

    out_root = REPO_ROOT / "04_OUTPUT" / "production" / date.today().strftime("%Y-%m") / args.date / "inbox"
    ensure_dir(out_root)
    units = write_units(spec, args.date, out_root)

    print("Generated units:")
    for u in units:
        print(f"- {u}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
