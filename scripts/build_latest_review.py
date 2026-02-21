#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass
from typing import List


@dataclass
class PreviewEntry:
    unit: str
    preview_path: Path
    demo_path: Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def latest_dir() -> Path:
    return repo_root() / "04_OUTPUT" / "approved" / "latest"


def find_previews(root: Path) -> List[PreviewEntry]:
    entries: List[PreviewEntry] = []
    for preview in root.rglob("preview.png"):
        if not preview.is_file():
            continue
        try:
            unit = preview.parents[1].name
            demo = preview.parent / "index.html"
            entries.append(PreviewEntry(unit=unit, preview_path=preview, demo_path=demo))
        except Exception:
            continue
    return entries


def sort_entries(entries: List[PreviewEntry]) -> List[PreviewEntry]:
    order = {"C1": 0, "C2": 1, "C3": 2, "C4": 3}

    def key(e: PreviewEntry):
        prefix = e.unit.split("_", 1)[0]
        return (order.get(prefix, 9), e.unit)

    return sorted(entries, key=key)


def rel_to_repo(path: Path) -> str:
    root = repo_root()
    try:
        return str(path.relative_to(root))
    except Exception:
        return str(path)


def build_index(entries: List[PreviewEntry], out_path: Path) -> None:
    lines = ["# Preview Index", ""]
    for e in entries:
        lines.append(f"- {rel_to_repo(e.preview_path)}")
    out_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def build_review_html(entries: List[PreviewEntry], out_path: Path) -> None:
    cards = []
    for e in entries:
        rel_preview = e.preview_path.relative_to(latest_dir()).as_posix()
        demo_uri = e.demo_path.resolve().as_uri()
        cards.append(
            f"""
            <article class="card">
              <div class="title">{e.unit}</div>
              <a class="thumb" href="{demo_uri}" target="_blank" rel="noreferrer">
                <img loading="lazy" src="{rel_preview}" alt="{e.unit} preview"/>
              </a>
              <div class="link">{demo_uri}</div>
            </article>
            """.strip()
        )

    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>Latest Preview</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #0b0d12;
      --card: #131722;
      --text: #e5e9f2;
      --muted: #9aa4b2;
      --border: #23293a;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--text);
    }}
    header {{
      padding: 28px 32px 12px;
      font-size: 20px;
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 18px;
      padding: 16px 32px 40px;
    }}
    .card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 12px;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }}
    .title {{
      font-size: 14px;
      letter-spacing: 0.04em;
      color: var(--muted);
      text-transform: uppercase;
    }}
    .thumb {{
      display: block;
      border-radius: 10px;
      overflow: hidden;
      border: 1px solid var(--border);
    }}
    img {{
      width: 100%;
      height: auto;
      display: block;
    }}
    .link {{
      font-size: 12px;
      color: var(--muted);
      word-break: break-all;
    }}
  </style>
</head>
<body>
  <header>Approved Latest Preview</header>
  <section class="grid">
    {"".join(cards)}
  </section>
</body>
</html>
""".strip()
    out_path.write_text(html + "\n", encoding="utf-8")


def main() -> int:
    latest = latest_dir()
    latest.mkdir(parents=True, exist_ok=True)
    entries = sort_entries(find_previews(latest))
    build_index(entries, latest / "INDEX.md")
    build_review_html(entries, latest / "review.html")
    print("Preview: 04_OUTPUT/approved/latest/review.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
