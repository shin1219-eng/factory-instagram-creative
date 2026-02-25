# 2026-02-25 Quality Pipeline v09

## 何を変えたか
- `scripts/spector_capture/unitproduce_from_capture.py`
  - familyを9系統に拡張し、`systems`（layout/object/light/motion/material/camera）を導入。
  - C1〜C4のHTMLに `palette-id` / `layout-id` / `system-signature` を埋め込み。
  - `story.json` に `systems` と `unit_signatures` を保存。
  - `--family-shift` オプション追加（重複時の再生成用）。
- `scripts/spector_capture/generate_from_creative_input.py`
  - campaign signature重複検知を追加。
  - 重複時に `story_rotation` / `family_shift` をずらして自動再生成（上限回数あり）。
  - `AD_REVIEW_vXX.md` 自動生成を追加。
  - `--max-regen` / `--regen-story-step` / `--regen-family-step` オプション追加。
- ドキュメント更新:
  - `scripts/spector_capture/README.md`
  - `00_README/HowToRun.md`

## なぜ変えたか
- C1〜C4の骨組みが似通う問題を解消し、同日バッチ内での構造重複を減らすため。
- 「調査→制作」の自動化に、品質ゲート（重複検知＋再生成）と人間レビュー導線（AD_REVIEW）を追加するため。

## 影響範囲
- `spector_capture` パイプラインの生成結果（HTML構造、story.json、manifest）が更新される。
- 既存コマンドは互換維持。新オプション未指定でも従来通り実行可能。
