# Unit Brief: C1 3D Teaser（Three.js / 9:16）

## 目的
一枚で「技術力・表現力」が伝わるティザーを作る。

## 入力
- 採用軸：TrendScanの上位3軸から1つ
- トーン：ハイエンド寄り
- 色：主1色＋無彩色
- 文字：原則なし（後載せ前提）

## 出力（固定）
- prototype：SVG素体（9:16）
- production（コード）：
  - demo/index.html（Three.jsで3Dヒーロー）
  - demo/preview.png（Gate用プレビュー）
- メタデータ：同名の .md（目的/軸/参照URL/意図/Rubric/判定）
- 保存先：
  - prototype：04_OUTPUT/prototype/YYYY-MM/YYYY-MM-DD/inbox/
  - production：04_OUTPUT/production/YYYY-MM/YYYY-MM-DD/inbox/

## 必須実装要素（欠けたらFAILED）
- 厚み（ボリュームのある形状）
- 質感（素材感の差が出る）
- 接地影（コンタクトシャドウ）
- 背景ノイズ
- 微パララックス（カメラ/光の微動）
- 単純回転のみは禁止

## NG
- ロゴっぽい文字の生成
- 読めない日本語の焼き込み
- 既存ブランドの固有要素踏襲
