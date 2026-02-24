# Change Log: 2026-02-24 / C1-C4 Production v4 (strict diversity)

## What
- C1/C2/C3/C4 を新規レイアウトと新規配色で再構築（v04）
- Run Log run_003 を追加（Palette/Layout 記録）
- latest 集約と review.html を更新

## Why
- 4ユニットの骨格/色の使い回しを防止し、毎回違う出力を担保するため
- palette-id/layout-id の重複禁止ルールに合わせるため

## Impact
- 04_OUTPUT/production/2026-02/2026-02-23/approved/ に v04 を追加
- 04_OUTPUT/approved/latest/ を v04 に更新

Gate判定結果: PASS（C1/C2/C3/C4 すべて demo/index.html と demo/preview.png を確認）
補足: Chrome headless が落ちるため preview.png はPILで生成
