# SKILL: S5 ShipAndStore

## 目的
格納ルールに従って成果物を整理し、ログを更新する。
採用物は 04_OUTPUT/approved/latest/ に集約する。

## いつ起動するか
- S4で判定が出た直後

## 入力
- 判定結果（approved/revise）
- 対象ファイル群（成果物＋メタデータ）

## 出力（固定）
- approved：04_OUTPUT/.../approved に移動
- revise：04_OUTPUT/.../revise に移動
- latest：04_OUTPUT/approved/latest/ に採用物をコピー（またはリンク）
  - 採用物のみを集約し、INDEX.md を作成
- 05_LOGS/runs の該当runログに結果を追記

## 失敗条件
- 命名規則に違反
- メタデータ欠落
