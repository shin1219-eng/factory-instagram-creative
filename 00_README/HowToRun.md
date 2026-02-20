# How to Run (運用手順)

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
- 出力：
  - prototype（SVG素体）：04_OUTPUT/prototype/YYYY-MM/YYYY-MM-DD/inbox/
  - production用Prompt Pack：04_OUTPUT/production/YYYY-MM/YYYY-MM-DD/inbox/
  - C1 production：Image Prompt Pack を生成（4案）

## 3) QA（採点）→ 出荷/差し戻し
- Rubric合計80点以上 → approved
- 未満 → revise（差分修正）
- 最大2ループで打ち切り（沼防止）

## 4) ShipAndStore（格納）
- approved / revise に移動
- 実行ログを更新
- 04_OUTPUT/approved/latest/ に採用物を集約（C1画像を優先して1〜2枚）
