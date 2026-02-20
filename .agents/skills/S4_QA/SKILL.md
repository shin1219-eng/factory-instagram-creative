# SKILL: S4 QA

## 目的
Rubricで採点し、approved / revise を判定し、差分修正指示を出す。

## いつ起動するか
- inboxに新規成果物が入ったとき
- reviseから再提出が来たとき

## 入力
- 対象成果物（画像/動画）
- 同名メタデータ .md
- 01_RULES/Rubric.md

## 出力
- Rubric 10項目の点数
- 合計点
- 判定：approved or revise
- reviseの場合：差分修正指示（不足表現で書く）
- ループ回数の更新（最大2）

## 成功条件
- 判定が一貫している
- 差分指示が具体で、次の制作に落ちる
