# Change Log: 2026-02-24 / Spector → UnitProduce automation

## What
- Spector capture から C1〜C4 を自動生成するスクリプトを追加
- 実行手順を README に追記

## Why
- URL参照の実描画から直接 UnitProduce に接続し、質感再現性を上げるため

## Impact
- scripts/spector_capture/unitproduce_from_capture.py を追加
- scripts/spector_capture/README.md / 00_README/HowToRun.md を更新

補足: デモ実行は `--demo-image` で行い、本番は capture dir を指定
