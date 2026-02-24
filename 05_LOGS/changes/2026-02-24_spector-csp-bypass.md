# Change Log: 2026-02-24 / Spector CSP bypass

## What
- CSP回避のため `bypassCSP` を有効化
- post-loadでSpector再注入 + frame毎に注入
- クリック/スクロールでcanvas生成を促進
- `DISABLE_WEB_SECURITY` オプションを追加

## Why
- Spector未ロード / no-canvas が継続したため

## Impact
- scripts/spector_capture/capture_urls.mjs / README.md を更新
