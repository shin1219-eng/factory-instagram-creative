# Unit Brief: 3D Teaser（9:16 静止画）

## 目的
一枚で「技術力・表現力」が伝わるティザーを作る。

## 入力
- 採用軸：TrendScanの上位3軸から1つ
- トーン：ハイエンド寄り
- 色：主1色＋無彩色
- 文字：原則なし（後載せ前提）

## 出力（固定）
- prototype：SVG素体（9:16）
- production：Image Prompt Pack（C1_KV_<axis>_image-pack.md）
  - 1軸につき4案（4プロンプト）
  - 各案に「主役/質感/背景/光/構図/禁止事項」を明記
- メタデータ：同名の .md（目的/軸/参照URL/意図/Rubric/判定）
- 保存先：
  - prototype：04_OUTPUT/prototype/YYYY-MM/YYYY-MM-DD/inbox/
  - production：04_OUTPUT/production/YYYY-MM/YYYY-MM-DD/inbox/

## NG
- ロゴっぽい文字の生成
- 読めない日本語の焼き込み
- 既存ブランドの固有要素踏襲
