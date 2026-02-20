# SKILL: S6 RenderPolish

## 目的
C2（LP/Interactive/3D）専用の自動プレビューを生成し、production Gate を通す。
C2_InteractiveFV_*_prompt-pack.md から demo/index.html を生成し、Playwrightで preview.png を出力する。

## いつ起動するか
- C2 の production用 Prompt Pack が作成されたとき
- S4 QAで「BLOCKED（production未生成）」になったとき

## いつ起動しないか
- C2 以外のユニット
- Prompt Pack が未作成のとき

## 入力
- 04_OUTPUT/production/YYYY-MM/YYYY-MM-DD/inbox/C2_InteractiveFV_*_prompt-pack.md

## 出力（固定）
- demo: 04_OUTPUT/production/YYYY-MM/YYYY-MM-DD/demo/index.html
- preview: 04_OUTPUT/production/YYYY-MM/YYYY-MM-DD/preview/preview.png
- 05_LOGS/runs に Gate判定結果（合格/不合格理由を1行）

## 手順
1) Prompt Pack から demo/index.html を生成
2) Playwright で demo/index.html を headless で開き、preview.png を生成

## 実行コマンド
- `npm install`
- `npm run render:preview <prompt-pack>`

## 注意
- Playwright が使えない場合は BLOCKED（production未生成）としてログに残す
- 外部有料APIは使わない（費用発生なし）

## 成功条件
- preview.png が production レーンに生成され、Gate PASS
