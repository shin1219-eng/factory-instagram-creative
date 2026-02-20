# SKILL: S6 RenderPolish

## 目的
prototype（SVG素体）を production 品質へ昇格させる。
画像生成で本番PNGを作るか、生成待ち用のPrompt Packを用意する。

## いつ起動するか
- prototype が approved になり、本番用のproductionが必要なとき
- QAで「SVGのままではapproved不可」と判定されたとき

## いつ起動しないか
- まだ prototype が確定していないとき
- 先に差分修正（S3/S4）が必要なとき

## 入力
- prototype（SVG素体）
- 01_RULES/Rubric.md
- 01_RULES/Design-DNA.md

## 出力（固定）
- Mode A: 04_OUTPUT/production/YYYY-MM/YYYY-MM-DD/inbox/（PNG/JPG/WebP）
- Mode B: 04_OUTPUT/production/YYYY-MM/YYYY-MM-DD/inbox/ に Prompt Pack（.md）
- 05_LOGS/runs に Gate判定結果（合格/不合格理由を1行）

## Mode A（画像生成で本番PNG）
- 画像生成ツールで production 用の PNG/JPG/WebP を作成
- 1080×1920、テキストなし、質感・主役・奥行き・コントラストを強化
- 外部有料APIを使う場合は「費用発生」と「キー管理」を明記し、デフォルトはOFF

## Mode B（Prompt Pack）
- 生成ツールが使えない場合、Prompt Pack を作成して production待ちとする
- Prompt Pack には以下を含める
  - ベース形状
  - 質感（光/影/素材）
  - カメラ距離/構図
  - 色指定
  - 禁止事項
- 05_LOGS/runs に「production生成待ち」を明記

## 成功条件
- production成果物が Gate を通過し、Rubric 80点以上
