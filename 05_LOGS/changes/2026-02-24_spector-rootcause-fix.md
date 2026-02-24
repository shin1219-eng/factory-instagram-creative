# Change Log: 2026-02-24 / Spector root-cause fix

## What
- `capture_urls.mjs` の評価引数バグを修正（Playwright `frame.evaluate` は引数1つ）
- canvas選定を「WebGL contextが実在するcanvas」に変更
- `meta.json` に `ctx_probe` / `frame_results` / `canvas_infos` を追加
- GPU起動フラグを `--use-angle=metal` ベースに変更

## Why
- `capture-no-result` の原因切り分けで以下を確認したため:
  - 引数過多で `frame.evaluate` が例外
  - 一部URLは WebGPU only（Spector対象外）
  - WebGL非生成時に no-canvas と混同されていた

## Impact
- `scripts/spector_capture/capture_urls.mjs` と `README.md` を更新
- 失敗理由が `meta.json` 上で再現可能になり、調査可能性が上がった
