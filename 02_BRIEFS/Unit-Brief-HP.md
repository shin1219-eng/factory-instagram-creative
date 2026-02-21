# Unit Brief: C4 HP（複数ページ or HP構成 / code）

## 目的
HPとして成立する構成をコードで作る（複数ページ or HP構成）。

## 入力
- 採用軸：TrendScanの上位3軸から1つ
- トーン：ハイエンド寄り
- 文字：最小限（要点のみ）

## 出力（固定）
- production（コード）：
  - demo/index.html（HPのメイン）
  - demo/preview.png（Gate用プレビュー）
  - 必要なら複数ページHTMLを同梱（about / product / contact など）
- メタデータ .md を同梱
- 保存先：04_OUTPUT/production/YYYY-MM/YYYY-MM-DD/inbox/

## NG
- 外部CDN依存
- 文字過多
