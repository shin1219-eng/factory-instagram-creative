# SKILL: S6 RenderPolish

## 目的
C1〜C4 の production プレビューを生成し、production Gate を通す。

## いつ起動するか
- demo/index.html が生成されたとき
- S4 QAで「FAILED（render error）」になったとき

## いつ起動しないか
- demo/index.html が未生成のとき

## 入力
- C1〜C4: 04_OUTPUT/production/YYYY-MM/YYYY-MM-DD/<unit_id>/demo/index.html

## 出力（固定）
- C1〜C4: 04_OUTPUT/production/YYYY-MM/YYYY-MM-DD/<unit_id>/demo/preview.png
- 05_LOGS/runs に Gate判定結果（合格/不合格理由を1行）

## 実行コマンド
- `node scripts/renderpolish_preview.mjs <demo/index.html>`

## 注意
- Chrome パス: /Applications/Google Chrome.app/Contents/MacOS/Google Chrome
- Chrome が無い場合は FAILED（render error）としてログに残す
- 外部有料APIは使わない（費用発生なし）

## 成功条件
- preview.png が production レーンに生成され、サイズ > 0 で Gate PASS
