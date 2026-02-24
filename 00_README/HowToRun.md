# How to Run (運用手順)

## 0) Render Capture（Spector）
- 目的：URL を実描画し、WebGLの実仕様（draw call / shader / uniform）を取得
- 実行：`node scripts/spector_capture/capture_urls.mjs`
- 出力：`05_LOGS/captures/YYYY-MM-DD/<slug>/`
  - `spector/capture.json` / `shots/hero.png` / `videos/*.webm` / `meta.json`
 - C1〜C4へ直結：`python3 scripts/spector_capture/unitproduce_from_capture.py --capture 05_LOGS/captures/YYYY-MM-DD/<slug>`

## 1) TrendScan を回す
- 入力：02_BRIEFS/TrendScan-Brief.md
- 出力：05_LOGS/runs/YYYY-MM-DD/run_001.md
  - 参照候補30件 → 品質ゲート
  - 合格参照10件未満なら FAIL
  - トレンド要約（5行）
  - 表現軸カード（5〜12）
  - 上位3軸（採用）
  - 制作ユニット提案（本数）

## 2) 制作する（UnitProduce）
- 入力：02_BRIEFS/Unit-Brief-*.md + 上位3軸
- 制作ユニット：
  - C1: 3D（Three.js）
  - C2: Interactive FV
  - C3: LP
  - C4: HP（複数ページ or HP構成）
- 出力：
  - prototype（SVG素体）：04_OUTPUT/prototype/YYYY-MM/YYYY-MM-DD/inbox/
  - production（コード）：04_OUTPUT/production/YYYY-MM/YYYY-MM-DD/inbox/
    - `demo/index.html` と `demo/preview.png`

## 3) QA（採点）→ 出荷/差し戻し
- Rubric合計80点以上 → approved
- 未満 → revise（差分修正）
- 最大2ループで打ち切り（沼防止）

## 4) ShipAndStore（格納）
- approved / revise に移動
- 実行ログを更新
- 04_OUTPUT/approved/latest/ に採用物を集約（INDEX.mdを作成）
- `scripts/build_latest_review.py` で review.html を生成
