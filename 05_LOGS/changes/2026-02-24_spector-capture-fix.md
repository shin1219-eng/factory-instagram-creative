# Change Log: 2026-02-24 / Spector capture reliability fix

## What
- Spector.js を npm 依存に変更して自動注入を安定化
- addInitScript + frame走査で canvas / Spector の検出強化
- screenshotタイムアウトのエラーを非致命化

## Why
- 既存の capture がほぼ失敗していたため（Spector未ロード / no-canvas）

## Impact
- scripts/spector_capture/capture_urls.mjs / package.json / README.md を更新
