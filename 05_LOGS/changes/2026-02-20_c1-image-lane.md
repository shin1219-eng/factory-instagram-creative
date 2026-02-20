# Change Log: 2026-02-20 / C1 Image Lane

## What
- C1（3DTeaser/KV）production を HTML demo ではなく Image Prompt Pack に移行
- C1 の Production Gate を「画像ファイル + サイズ >=120KB」に変更
- latest 集約で C1 画像を優先（1〜2枚）

## Why
- C1 を実運用の「画像生成レーン」に寄せて KV 品質を上げるため

## Impact
- C1 production は `C1_KV_<axis>_image-pack.md` の4案出力が基準
- 画像未生成は BLOCKED、生成失敗は FAILED でログ記録
