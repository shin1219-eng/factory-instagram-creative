# Project Operating Rules (Factory / Instagram)

## 目的
RePrompt公式（国内向け）の Instagram 制作を「調査 → 軸生成 → 制作 → QA → 格納」まで、**承認だけ**で回せるようにする。

## 最重要（固定するもの / 固定しないもの）
- 固定する：出力仕様、格納ルール、Rubric（採点）、Guardrails（不変条件）
- 固定しない：表現軸（毎回 TrendScan で軸カードを生成し、上位3つ採用）

## 実行フロー（必ずこの順番）
1) TrendScan：参考収集 → 軸カード生成（5〜12） → 上位3採用
2) UnitProduce：上位3軸 × 制作ユニットで制作
3) QA：Rubric採点。80点未満は差分修正（最大2ループ）
4) ShipAndStore：格納ルールに従い保存（inbox/approved/revise）

## 見る場所（固定）と確定条件
- Awwwards：インタラクティブ/サイト表現の最前線を見る
- Behance：KV/3D/Caseの完成度が高い事例を見る
- Dribbble：瞬間火力のあるグラフィック単体を見る
- Instagram（海外スタジオ/3D作家）：投稿フォーマットに落ちた形を見る

## 出荷条件
- Rubric合計 80点以上 → approved
- 80点未満 → revise（差分修正指示を出す）
- ループは最大2回（沼防止）

## 重要制約
- テキスト（長文）を画像生成に焼き込むのは原則やらない（破綻しやすい）
- 文字は後工程で載せる前提（ExplainSlideは例外だが最小限）
- 既存ブランドの丸パクリは禁止（固有ロゴ/固有コピー/固有KVの踏襲はNG）
- 参照URLは必ず記録（未確認の推測は「未確認」と明示）

## Repo運用ルール（固定）
- PR作成は今後一切しない（gh auth / WebViewログイン不要）
- 変更はデフォルトブランチへ直接 commit & push する
- 大きい変更の前に backup/YYYY-MM-DD-topic を作る
- 作業後は scripts/validate_instagram_factory_v1.py を実行し、PASSしたらpush
- 変更ログは 05_LOGS/ に必ず残す
- コミットメッセージに「何を変えたか/なぜ/影響範囲」を必ず1行ずつ書く

## ファイル配置
- ルール：01_RULES/
- 入力テンプレ：02_BRIEFS/
- Skill仕様：.agents/skills/*/SKILL.md
- 出力：
  - prototype（SVG素体）：04_OUTPUT/prototype/YYYY-MM/YYYY-MM-DD/(inbox|approved|revise)
  - production（PNG/JPG/WebP）：04_OUTPUT/production/YYYY-MM/YYYY-MM-DD/(inbox|approved|revise)
  - C1 production：demo/index.html + demo/preview.png を最終成果物として扱う
- 実行ログ：05_LOGS/runs/
