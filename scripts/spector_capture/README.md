# Spector Capture (URL → GPU Spec)

目的: URL を実描画し、WebGL の draw call / shader / uniform を **Spector.js で直接抽出**する。
録画は補助で、主軸は `spector/capture.json`。

## 事前準備
```bash
cd /Users/shintahayama/Documents/New\ project/scripts/spector_capture
npm init -y
npm i playwright
npx playwright install --with-deps
```

## 実行
```bash
node capture_urls.mjs
```

## UnitProduceへ直結（Spector → C1〜C4）
```bash
python3 unitproduce_from_capture.py --capture /abs/path/to/05_LOGS/captures/YYYY-MM-DD/<slug>
```

### デモ（キャプチャ無し）
```bash
python3 unitproduce_from_capture.py --demo-image /abs/path/to/hero.png --slug demo
```

### オプション
- `HEADLESS=1` : ヘッドレス
- `VIEWPORT=1080x1920` : 画面サイズ
- `WAIT_MS=7000` : 初期待機
- `CAPTURE_TIMEOUT_MS=15000` : Spector capture 待ち
- `MAX_URLS=5` : 先頭N件だけ
- `OUTPUT_ROOT=/abs/path` : 出力先
- `SPECTOR_BUNDLE_URL=...` : Spector.js の取得元

## 出力
`05_LOGS/captures/YYYY-MM-DD/<slug>/`
- `spector/capture.json` : Spector capture（可能な限り）
- `shots/hero.png` : 代表スクショ
- `videos/*.webm` : Playwright録画
- `meta.json` : status / canvas / GPU情報

## 重要
- URLは `urls.txt` に並べる（空行/コメントは無視）。
- 一部サイトは **canvas を複数持つ**ため、最大サイズの canvas を対象にする。
- `capture.json` が生成されない場合は `meta.json` に理由が入る。
- さらに高精度が必要なら、Chrome拡張版 Spector で手動キャプチャ。
