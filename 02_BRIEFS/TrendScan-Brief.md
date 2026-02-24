# TrendScan Brief（入力テンプレ）

## 目的
デザイン界隈の市場調査を行い、表現軸カードを生成して「今回採用する上位3軸」を決める。

## 見る場所（固定）
- 01_RULES/TrendSources.md の Tier1/2/3 のみ
- 検索結果URL（`?search=` など）は禁止

## 確定条件
- 参照候補は30件集める
- 同一ドメインは最大2件まで
- 最低10ドメイン以上を含める
- Tier1/2/3 を必ず混在させる（どれか1つでも欠けたらFAIL）
- ただしユーザーが30件を指定した場合は Tier混在条件を例外扱い（Runログに明記）
- Reference Quality Gate を通過した合格参照のみ使用
- 合格参照が10件未満ならそのRunはFAIL（生成に進まない）
- 表現軸カードは5〜12個出す（合格参照からのみ）
- 上位3軸をスコアリングで選ぶ
- C4は多様化枠として上位3以外から1軸を選ぶことを許可（Runログに明記）
- 直近3Runで使った参照URL/軸名は再利用禁止
- Runログに palette_id / layout_id を必ず記録する
- Spector Capture（05_LOGS/captures）で実描画を取得できたものは「確認済み」とし、取得できない場合は「未確認」と明記する

## Axisカード必須項目（実装要素）
各Axisカードに以下を必ず含める。
- 参照URL
- なぜトレンド扱いか（短文）
- 実装要素
  - HeroGeometry
  - Material
  - Lighting
  - Camera
  - Background
  - Motion
  - Composition
  - Do-Not

## スコアリング軸（各10点）
- 止まる：IGで目が止まるか
- 作れる：量産の難易度が現実的か
- RePrompt適合：Design DNAに合うか

## Reference Quality Gate
- 参照元は Tier1/2/3 のみ
- 検索結果URLは禁止
- 直接の事例ページ／公式の受賞・特集ページのみ
- 低品質（解像度不足/古い/意図不明）は不合格

## 出力先（固定）
05_LOGS/runs/YYYY-MM-DD/run_001.md
