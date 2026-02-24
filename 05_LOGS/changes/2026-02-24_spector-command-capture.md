# Change Log: 2026-02-24 / Spector command capture

## What
- command数ベースのキャプチャに変更（`CAPTURE_COMMANDS`）
- canvas待機をフレーム内で継続
- Spector未ロード時にframe内で再注入

## Why
- 1フレーム待ちがタイムアウトするケースが多いため

## Impact
- scripts/spector_capture/capture_urls.mjs / README.md を更新
