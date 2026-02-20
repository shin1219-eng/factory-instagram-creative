# SKILL: S4 QA

## 目的
Rubricで採点し、approved / revise を判定し、差分修正指示を出す。
Production Gate を通過できない成果物は自動で差し戻す。

## いつ起動するか
- inboxに新規成果物が入ったとき
- reviseから再提出が来たとき

## いつ起動しないか
- まだ出力が prototype の段階で、S6未完のとき

## 入力
- 対象成果物（画像/動画）
- 同名メタデータ .md
- 01_RULES/Rubric.md

## 出力
- Gate判定結果（合格/不合格理由を1行）を 05_LOGS に必ず記録
- Rubric 12項目の点数
- 合計点
- 判定：approved or revise
- reviseの場合：差分修正指示（不足表現で書く）
- ループ回数の更新（最大2）

## Production Gate
- C1: 生成画像（png/jpg/webp）が存在し、サイズ >=120KB の場合のみ PASS
- C1: 画像が無い場合は BLOCKED（生成待ち）
- C1: 画像サイズ不足/形式不正は FAILED（render error）
- C2: demo/preview.png が存在し、サイズ > 0 の場合のみ PASS
- C2: preview.png が無い／サイズ0の場合は FAILED（render error）
- production成果物は PNG/JPG/WebP のみ合格
- SVG単体はスコア上限60（approved不可）

## Gateログ表記
- 不合格（品質NG）: 画質/質感/主役/構図の品質不足
- BLOCKED（生成待ち）: 画像が未生成
- FAILED（render error）: 生成失敗/サイズ不足/形式不正の理由を明記

## 成功条件
- 判定が一貫している
- 差分指示が具体で、次の制作に落ちる
