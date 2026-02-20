# SKILL: S3 UnitProduce

## 目的
上位3軸のうち1つを使い、制作ユニット（3Dティザー / interactiveFV / explain）を作る。
prototype（SVG素体）と production 用Prompt Pack を分離して出力する。

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
- production用Prompt Pack:
  - 04_OUTPUT/production/YYYY-MM/YYYY-MM-DD/inbox/
  - *_prompt-pack.md（形状/質感/構図/色/禁止事項）

## 注意
- 長文テキストを画像に焼かない
- 破綻（文字化け/ロゴっぽい文字/不自然な手など）があれば自己差し戻し候補にする
- productionの本番画像はS6で生成（S3は作らない）
