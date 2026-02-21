# SKILL: S3 UnitProduce

## 目的
上位3軸のうち1つを使い、制作ユニット（C1/C2/C3/C4）のコード成果物を作る。
productionは `demo/index.html` と `demo/preview.png` を前提とする。

## いつ起動するか
- 上位3軸が確定した後
- inboxに制作物が足りないとき

## いつ起動しないか
- まだ上位3軸が確定していないとき
- Rubricの差し戻し対応が先に必要なとき

## 入力
- 上位3軸のうち1つ
- 対応する Unit-Brief（02_BRIEFS/Unit-Brief-*.md）
- Guardrails / Design DNA

## 出力（固定）
- prototype（SVG素体）:
  - 04_OUTPUT/prototype/YYYY-MM/YYYY-MM-DD/inbox/
  - 画像（SVG）＋同名メタデータ .md
- production（コード）:
  - 04_OUTPUT/production/YYYY-MM/YYYY-MM-DD/inbox/<unit_id>/demo/index.html
  - 04_OUTPUT/production/YYYY-MM/YYYY-MM-DD/inbox/<unit_id>/demo/preview.png

## 注意
- 長文テキストを画像に焼かない
- 破綻（文字化け/ロゴっぽい文字/不自然な手など）があれば自己差し戻し候補にする
- 外部CDNは使わない（vendor/ を参照）
