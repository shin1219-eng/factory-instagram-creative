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
npm install
npx playwright install --with-deps
node capture_urls.mjs
```

## UnitProduceへ直結（Spector → C1〜C4）
```bash
python3 unitproduce_from_capture.py --capture /abs/path/to/05_LOGS/captures/YYYY-MM-DD/<slug>
```

現在の `unitproduce_from_capture.py` は骨組みを使い回さないため、構造ファミリーを切り替えます:
- `fluid` / `organic` / `spectral`
- `brutal` / `grid` / `industrial`
- `cinematic` / `editorial` / `luxe`

## 2段構成（推奨）
### A) 収集・整理パイプライン（captures -> creative_input）
```bash
python3 build_creative_input.py \
  --captures-date 2026-02-24 \
  --campaigns 3 \
  --story-rotation 1 \
  --target-date 2026-02-24 \
  --axes-config /Users/shintahayama/Documents/New\ project/01_RULES/style/ResearchAxes.json
```

出力:
- `05_LOGS/research/YYYY-MM-DD/<batch_id>/creative_input.json`
- `05_LOGS/research/YYYY-MM-DD/<batch_id>/SUMMARY.md`

3軸評価:
- `technical`（描画・動き・質感）
- `brand_story`（物語・トーン適合・色戦略）
- `market`（Instagram適合・トレンド適合・差別化）

### B) クリエイティブ生成パイプライン（creative_input -> 12units）
```bash
python3 generate_from_creative_input.py \
  --creative-input /abs/path/to/05_LOGS/research/YYYY-MM-DD/<batch_id>/creative_input.json \
  --date 2026-02-24 \
  --version v05 \
  --max-regen 2
```

出力:
- `04_OUTPUT/production/YYYY-MM/YYYY-MM-DD/inbox/*_v05/demo/index.html`
- `04_OUTPUT/production/YYYY-MM/YYYY-MM-DD/inbox/INDEX_<run_tag>_12set.html`
- `05_LOGS/research/YYYY-MM-DD/<batch_id>/generation_result_v05.json`
- `05_LOGS/research/YYYY-MM-DD/<batch_id>/AD_REVIEW_v05.md`

補足:
- `generate_from_creative_input.py` は `creative_input.json` 内の `axis_minimum_scores` を満たさない campaign を自動スキップします。
- campaign signature が重複した場合は `story_rotation` / `family_shift` を自動で回して再生成します（`--max-regen` 回）。

### 3キャンペーン連結（12ユニット: C1-C4 x 3）
```bash
python3 unitproduce_from_capture.py \
  --capture /abs/path/to/05_LOGS/captures/YYYY-MM-DD/<slug> \
  --campaigns 3 \
  --version v04 \
  --story-rotation 1
```

### デモ（キャプチャ無し）
```bash
python3 unitproduce_from_capture.py --demo-image /abs/path/to/hero.png --slug demo
```

### オプション
- `HEADLESS=1` : ヘッドレス
- `VIEWPORT=1080x1920` : 画面サイズ
- `WAIT_MS=7000` : 初期待機
- `WAIT_CANVAS_MS=15000` : canvas待ち
- `CAPTURE_TIMEOUT_MS=15000` : Spector capture 待ち
- `CAPTURE_COMMANDS=400` : command数でキャプチャ（0なら1フレーム）
- `QUICK_CAPTURE=1` : 速度優先（軽量）
- `FULL_CAPTURE=1` : 詳細優先（重い）
- `USE_START_STOP=1` : startCapture/stopCapture で強制取得
- `START_STOP_MS=4000` : start→stop の待機時間
- `MAX_URLS=5` : 先頭N件だけ
- `OUTPUT_ROOT=/abs/path` : 出力先
- `SPECTOR_BUNDLE_URL=...` : Spector.js の取得元
- `CHANNEL=chrome` : ローカルChromeで起動（GPU強め）
- `BYPASS_CSP=1` : CSPを無視して注入（デフォルトON）
- `DISABLE_WEB_SECURITY=1` : Webセキュリティ無効化（最終手段）
- `ANGLE_BACKEND=metal` : GPUバックエンド（推奨: metal）
- `FORCE_WEBGPU_OFF=1` : WebGPUを無効化（WebGL fallbackを狙う）
- `--campaigns 3` : 同一キャンペーンのC1-C4を3本生成（合計12ユニット）
- `--story-rotation 1` : 固定辞書の参照位置を回して出力を変える
- `--family-shift 1` : family選択をずらして再生成時の被りを減らす
- `--max-regen 2` : 重複時の自動再生成回数（generate_from_creative_input.py）
- `--regen-story-step 11` : 再生成時のstory_rotation増分
- `--regen-family-step 1` : 再生成時のfamily_shift増分

## 失敗時の見方
- `meta.json` の `ctx_probe`: `getContext` 呼び出しの実績
- `meta.json` の `frame_results`: frameごとの失敗理由
- 典型パターン:
  - `no-webgl-context`: そのページでWebGLが作れていない（WebGPUのみ/2Dのみ）
  - `spector-not-loaded`: CSPや注入失敗
  - `capture-timeout`: WebGLはあるがSpectorイベント未発火

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
