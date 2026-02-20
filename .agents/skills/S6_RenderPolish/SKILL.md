# SKILL: S6 RenderPolish

## 目的
C1/C2 の production プレビューを生成し、production Gate を通す。
C1は Prompt Pack → demo/index.html → preview.png を生成する。
C2は demo/index.html → preview.png を生成する。

## いつ起動するか
- C1 の production用 Prompt Pack が作成されたとき
- C2 の demo/index.html が生成されたとき
- S4 QAで「FAILED（render error）」になったとき

## いつ起動しないか
- demo/index.html も Prompt Pack も未生成のとき

## 入力
- C1: 04_OUTPUT/production/YYYY-MM/YYYY-MM-DD/inbox/C1_3DTeaser_*_prompt-pack.md
- C2: 04_OUTPUT/production/YYYY-MM/YYYY-MM-DD/demo/index.html

## 出力（固定）
- C1/C2: 04_OUTPUT/production/YYYY-MM/YYYY-MM-DD/demo/index.html
- C1/C2: 04_OUTPUT/production/YYYY-MM/YYYY-MM-DD/demo/preview.png
- 05_LOGS/runs に Gate判定結果（合格/不合格理由を1行）

## 実行コマンド
- C1: `node scripts/renderpolish_c1_kv.mjs <prompt-pack>`
- C2: `node scripts/renderpolish_c2_preview.mjs <demo/index.html>`

## 注意
- Chrome パス: /Applications/Google Chrome.app/Contents/MacOS/Google Chrome
- Chrome が無い場合は FAILED（render error）としてログに残す
- 外部有料APIは使わない（費用発生なし）

## 成功条件
- preview.png が production レーンに生成され、サイズ > 0 で Gate PASS
