# SKILL: S6 RenderPolish

## 目的
C2（LP/Interactive/3D）専用の自動プレビューを生成し、production Gate を通す。
demo/index.html から Google Chrome headless で preview.png を出力する。

## いつ起動するか
- C2 の demo/index.html が生成されているとき
- S4 QAで「FAILED（render error）」になったとき

## いつ起動しないか
- C2 以外のユニット
- demo/index.html が未生成のとき

## 入力
- 04_OUTPUT/production/YYYY-MM/YYYY-MM-DD/demo/index.html

## 出力（固定）
- preview: 04_OUTPUT/production/YYYY-MM/YYYY-MM-DD/preview/preview.png
- 05_LOGS/runs に Gate判定結果（合格/不合格理由を1行）

## 手順
1) Google Chrome headless で demo/index.html を開く
2) 1080×1920 で preview.png を生成

## 実行コマンド
- `node scripts/renderpolish_c2_preview.mjs 04_OUTPUT/production/YYYY-MM/YYYY-MM-DD/demo/index.html`

## 注意
- Chrome パス: /Applications/Google Chrome.app/Contents/MacOS/Google Chrome
- Chrome が無い場合は FAILED（render error）としてログに残す
- 外部有料APIは使わない（費用発生なし）

## 成功条件
- preview.png が production レーンに生成され、サイズ > 0 で Gate PASS
