#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bootstrap: factory-instagram-creative (Instagram Factory v1)

- Creates directory structure
- Writes all markdown templates (Rules / Briefs / Skills spec)
- Adds .gitkeep for empty dirs
"""

from __future__ import annotations

from pathlib import Path
import os
import sys
from datetime import datetime


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")


def touch_gitkeep(dir_path: Path) -> None:
    dir_path.mkdir(parents=True, exist_ok=True)
    (dir_path / ".gitkeep").write_text("", encoding="utf-8")


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    now = datetime.now().strftime("%Y-%m-%d")

    # -----------------------
    # Directory skeleton
    # -----------------------
    dirs_to_create = [
        "00_README",
        "01_RULES",
        "01_RULES/style",
        "02_BRIEFS",
        "02_BRIEFS/production-templates",
        "03_SKILLS_SPEC",
        "04_OUTPUT",
        "04_OUTPUT/approved",
        "04_OUTPUT/approved/latest",
        "04_OUTPUT/prototype",
        "04_OUTPUT/production",
        f"04_OUTPUT/prototype/{datetime.now().strftime('%Y-%m')}/{now}/inbox",
        f"04_OUTPUT/prototype/{datetime.now().strftime('%Y-%m')}/{now}/approved",
        f"04_OUTPUT/prototype/{datetime.now().strftime('%Y-%m')}/{now}/revise",
        f"04_OUTPUT/production/{datetime.now().strftime('%Y-%m')}/{now}/inbox",
        f"04_OUTPUT/production/{datetime.now().strftime('%Y-%m')}/{now}/approved",
        f"04_OUTPUT/production/{datetime.now().strftime('%Y-%m')}/{now}/revise",
        f"04_OUTPUT/production/{datetime.now().strftime('%Y-%m')}/{now}/demo",
        f"04_OUTPUT/production/{datetime.now().strftime('%Y-%m')}/{now}/preview",
        "05_LOGS",
        "05_LOGS/axis-cards",
        "05_LOGS/runs",
        "05_LOGS/changes",
        ".agents",
        ".agents/skills",
        ".agents/skills/S1_TrendScan",
        ".agents/skills/S2_AxisSelect",
        ".agents/skills/S3_UnitProduce",
        ".agents/skills/S4_QA",
        ".agents/skills/S5_ShipAndStore",
        ".agents/skills/S6_RenderPolish",
        ".agents/skills/_shared",
        "scripts",
    ]
    for d in dirs_to_create:
        touch_gitkeep(repo_root / d)

    # -----------------------
    # File contents
    # -----------------------
    files: dict[str, str] = {}

    files["AGENTS.md"] = f"""
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

## 見る場所（固定）
- 01_RULES/TrendSources.md の Tier1/2/3 のみを使用
- 検索結果URL（`?search=` など）は禁止

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
  - C1 production：Image Prompt Pack を生成し、画像（png/jpg/webp）が最終成果物
  - latest：04_OUTPUT/approved/latest/ に採用物を集約（C1画像を優先して1〜2枚）
- 実行ログ：05_LOGS/runs/
"""

    files["00_README/Purpose.md"] = """
# Instagram Factory v1 目的

## 目的
RePrompt公式（国内向け）のInstagram投稿を、以下の一連フローで量産する。

- デザイン界隈の市場調査
- 3D / KV / インタラクティブFV / LP断片などの制作
- 品質確認（Rubric採点）
- 格納（inbox/approved/revise）

## ポイント
- 表現軸は固定しない（毎回 TrendScan で抽出）
- 固定するのは「出力仕様」「採点」「格納ルール」「不変条件」

## 想定成果物（制作ユニット）
- 3Dティザー（静止画 9:16）
- インタラクティブFV（短尺動画 or スクショ3枚）
- 解説スライド（文字少なめ）
- Study case（架空ブランド：KV + LP断片 + Before/After）
"""

    files["00_README/HowToRun.md"] = """
# How to Run (運用手順)

## 1) TrendScan を回す
- 入力：02_BRIEFS/TrendScan-Brief.md
- 出力：05_LOGS/runs/YYYY-MM-DD/run_001.md
  - 参照候補30件 → 品質ゲート
  - 合格参照10件未満なら FAIL
  - トレンド要約（5行）
  - 表現軸カード（5〜12）
  - 上位3軸（採用）
  - 制作ユニット提案（本数）

## 2) 制作する（UnitProduce）
- 入力：02_BRIEFS/Unit-Brief-*.md + 上位3軸
- 出力：
  - prototype（SVG素体）：04_OUTPUT/prototype/YYYY-MM/YYYY-MM-DD/inbox/
  - production用Prompt Pack：04_OUTPUT/production/YYYY-MM/YYYY-MM-DD/inbox/
  - C1 production：Image Prompt Pack を生成（4案）

## 3) QA（採点）→ 出荷/差し戻し
- Rubric合計80点以上 → approved
- 未満 → revise（差分修正）
- 最大2ループで打ち切り（沼防止）

## 4) ShipAndStore（格納）
- approved / revise に移動
- 実行ログを更新
- 04_OUTPUT/approved/latest/ に採用物を集約（C1画像を優先して1〜2枚）
"""

    files["01_RULES/Design-DNA.md"] = """
# Design DNA（不変の美意識）

## 目的
表現軸が毎回変わっても「RePromptっぽさ」を崩さないためのガードレール。

## 方針（固定）
- 余白：広め（詰め込み禁止）
- 主役：必ず1つ（視線が迷う構図はNG）
- 色：主1色＋無彩色が基本（多色は例外）
- 質感：立体 or 素材感のどちらかを必ず強調
- タイポ：極細〜中太、基本は少なめ（長文を焼かない）
- トーン：ハイエンド寄り、安っぽさ・過剰装飾は避ける

## 不足表現（何が欠けているか）
- 「主役が欠けている」→ 何を見せたいのか分からない
- 「余白が欠けている」→ うるさく見える
- 「質感が欠けている」→ 平坦で止まらない
"""

    files["01_RULES/Copy-Voice.md"] = """
# Copy Voice（文体ルール）

## 目的
説明スライドやキャプションが「AIっぽくなる」のを防ぐ。

## 方針（固定）
- 1文は短く。1文に未知語は最大1つ。
- 断定しすぎない。ただし曖昧表現の連発は禁止。
- 言い切りは「見た目/体験」の話に限定し、事実（数値/根拠）はURL付き。

## 禁止
- 誇張の過多（世界一、絶対、誰でも等）
- ふわっとした褒め言葉だけ（すごい、最高等）

## OK例
- 「視線を1点に集める」→ 主役の位置と余白を説明
- 「質感を立てる」→ 光/陰/反射の設計を説明
"""

    files["01_RULES/Guardrails.md"] = """
# Guardrails（不変条件：固定）

## 固定するもの
- 出力仕様（9:16中心、制作ユニット単位）
- 格納ルール（命名/フォルダ/メタデータ）
- Rubric（採点：80点以上で出荷）
- リトライ最大2回（沼防止）

## 固定しないもの
- 表現軸（毎回 TrendScan で抽出→上位3採用）

## 制作ガード（確定条件）
- 主役は必ず1つ
- 情報密度を上げない（余白を確保）
- 長文テキストは画像に焼かない（文字は後載せ前提）
- 破綻（手/顔/ロゴっぽい文字化け/読めない日本語）があれば差し戻し
- 既存ブランドの丸パクリは禁止（固有要素NG）
"""

    files["01_RULES/Rubric.md"] = """
# Rubric（採点表：12項目×10点）

## 出荷条件
- 合計80点以上：approved
- 80点未満：revise（差分修正指示）
- 最大2ループで打ち切り

## Production Gate（必須）
- production成果物は PNG / JPG / WebP のみ合格
- SVG単体はスコア上限60（=approved不可）
- C1は画像生成レーン：生成画像（png/jpg/webp）が存在し、**サイズ>=120KB** なら PASS
- 画像が無い場合は BLOCKED（生成待ち）
- 生成失敗は FAILED（理由をログ）
- Gate判定結果は 05_LOGS に必ず1行で記録（合格/不合格理由）

## Gateログ表記
- 不合格（品質NG）: 画質/質感/主役/構図の品質不足
- BLOCKED（生成待ち）: 画像が未生成
- FAILED（render error）: 生成失敗の理由を明記

## 採点項目
1. 3秒で止まる（スクロールストップ）
2. 何の投稿か即理解（文脈の明確さ）
3. 主役の強さ（縮小耐性）
4. 余白と密度（整理）
5. 質感（光/影/素材）
6. 今っぽい（海外トップ基準）
7. RePromptらしさ（統一感）
8. 投稿化できる（9:16・安全領域）
9. 破綻がない（違和感）
10. 権利的に安全（固有要素なし）
11. 格納が正しい（命名・メタデータ）
12. 転用耐性（KV/LP/広告への展開）

## C1（3DTeaser/KV）評価の明確化
- 必須重点: 「主役の強さ」「質感」「奥行き」
- QAログに短い根拠を残す（各1行）
  - 主役: 縮小しても主役が即判別できるか
  - 質感: 光/影/素材の分離が明確か
  - 奥行き: 前後関係が視覚的に成立するか

## 修正指示の書き方（不足表現）
- 「主役が欠けている」→ 主役を1つに絞る
- 「余白が欠けている」→ 情報を削って間を作る
- 「質感が欠けている」→ 光・反射・陰影を設計する
"""

    files["01_RULES/TrendSources.md"] = """
# TrendSources（参照元リスト：固定）

## 共通ルール
- 参照は **Tier1/2/3 のみ** から取得する
- **検索結果URL（`?search=` などの検索パラメータ付きURL）は禁止**
- 直接の事例ページ／公式の受賞・特集ページのみ可
- 同一ドメイン偏重を避ける（最大4件まで）

## Tier1（最優先・公式/キュレーション）
1. Awwwards / Websites（SOTD含む）
   - https://www.awwwards.com/websites/
2. Awwwards / Collections
   - https://www.awwwards.com/collections/
3. The FWA / Awards
   - https://thefwa.com/awards/
4. CSS Design Awards / Winners
   - https://www.cssdesignawards.com/winners/
5. SiteInspire（キュレーション）
   - https://www.siteinspire.com/

## Tier2（準公式/準キュレーション）
1. Behance / Galleries
   - https://www.behance.net/galleries/
2. Behance / Featured
   - https://www.behance.net/featured
3. Dribbble / Popular
   - https://dribbble.com/shots/popular
4. It’s Nice That（キュレーション）
   - https://www.itsnicethat.com/
5. Brand New（UnderConsideration）
   - https://www.underconsideration.com/brandnew/

## Tier3（公式アカウント・参考）
- https://www.instagram.com/akqa/
- https://www.instagram.com/obys/
- https://www.instagram.com/sixnfive/
- https://www.instagram.com/gmunk/
- https://www.instagram.com/tendril/

## 禁止例
- `https://www.behance.net/search/projects?search=3d`（検索URL）
- `https://dribbble.com/search/3d`（検索URL）
"""

    files["02_BRIEFS/TrendScan-Brief.md"] = """
# TrendScan Brief（入力テンプレ）

## 目的
デザイン界隈の市場調査を行い、表現軸カードを生成して「今回採用する上位3軸」を決める。

## 見る場所（固定）
- 01_RULES/TrendSources.md の Tier1/2/3 のみ
- 検索結果URL（`?search=` など）は禁止

## 確定条件
- 参照候補は30件集める
- Reference Quality Gate を通過した合格参照のみ使用
- 合格参照が10件未満ならそのRunはFAIL（生成に進まない）
- 表現軸カードは5〜12個出す（合格参照からのみ）
- 上位3軸をスコアリングで選ぶ

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
"""

    files["02_BRIEFS/Unit-Brief-3DTeaser.md"] = """
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
"""

    files["02_BRIEFS/Unit-Brief-InteractiveFV.md"] = """
# Unit Brief: Interactive FV（短尺動画 or スクショ3枚）

## 目的
インタラクティブなFVの気持ちよさが一目で伝わる投稿素材を作る。

## 入力
- 採用軸：TrendScanの上位3軸から1つ
- 参照：Awwwards由来の表現を優先
- 文字：最小（基本はなし）

## 出力（固定）
- 動画（短尺） or スクショ3枚
- 9:16で投稿化できる形に整える
- メタデータ .md を同梱
- 保存先：04_OUTPUT/prototype/YYYY-MM/YYYY-MM-DD/inbox/
"""

    files["02_BRIEFS/Unit-Brief-ExplainSlide.md"] = """
# Unit Brief: Explain Slide（文字少なめ）

## 目的
「何が凄いか」を3秒で理解させる補助スライドを作る。

## ルール
- 文字は最小限（1〜2行）
- 専門用語は「意味→用語名」の順で1行補足
- 誇張の連発は禁止
"""

    # -------- Skills (Agent-visible spec) --------
    files[".agents/skills/_shared/CONVENTIONS.md"] = """
# Skills Conventions（共通規約）

## 入出力の固定
- 入力：02_BRIEFS/ のテンプレを使う
- 出力：05_LOGS/ と 04_OUTPUT/ の規約に従う

## 重要
- 表現軸は固定しない（毎回 TrendScan で生成）
- 固定するのは Guardrails / Rubric / 格納ルール
"""

    files[".agents/skills/S1_TrendScan/SKILL.md"] = """
# SKILL: S1 TrendScan (v2)

## 目的
参照の品質を担保し、「カス参照」を排除した上で表現軸カードを生成する。

## いつ起動するか
- 新しい制作日（YYYY-MM-DD）で投稿ネタを作るとき
- 参照の質が落ちているとき

## いつ起動しないか
- 既に当日のrunログがあり、上位3軸が確定しているとき

## 入力
- 02_BRIEFS/TrendScan-Brief.md
- 01_RULES/TrendSources.md

## Reference Quality Gate（必須）
1) 参照候補を30件集める
2) 以下の基準でゲート判定し、合格のみ採用
   - Tier1/2/3 以外は不合格
   - 検索結果URL（`?search=` 等）は不合格
   - 直接の事例ページ／公式の受賞・特集ページのみ
   - 低品質（解像度不足/古い/意図不明）は不合格
3) 合格参照が10件未満なら **FAIL**
   - そのrunは生成に進まない
   - FAIL理由をログに必ず記載

## 出力（固定）
- 05_LOGS/runs/YYYY-MM-DD/run_001.md
  - 参照候補30件
  - Gate判定（合格/不合格＋理由）
  - 合格参照一覧（10件以上）
  - トレンド要約（5行）
  - 表現軸カード（5〜12）
  - 上位3軸（採用）
  - 制作ユニット提案（本数）

## Axisカード要件（合格参照からのみ）
- 参照URL
- なぜトレンド扱いか（短文）
- 使う要素（構図/質感/タイポ）
- NG

## 失敗条件
- 合格参照が10件未満
- 軸カードが抽象的すぎて制作に落ちない

## 成功条件
- そのまま S2/S3 の入力として使える具体性がある
"""

    files[".agents/skills/S2_AxisSelect/SKILL.md"] = """
# SKILL: S2 AxisSelect

## 目的
S1の軸カードをスコアリングし、今回採用する上位3軸を確定する。

## いつ起動するか
- S1で軸カードが出揃った直後

## いつ起動しないか
- 既に上位3軸が確定しているとき（同一run内）

## 入力
- S1の run_001.md 内の軸カード一覧

## スコアリング（各10点）
- 止まる：IGで止まるか
- 作れる：量産が現実的か
- RePrompt適合：Design DNAに合うか

## 出力
- 上位3軸（合計点と短い理由つき）
- 05_LOGS/runs の該当runログに追記（上位3軸欄を確定）

## 失敗条件
- 3軸が似すぎてバリエーションが出ない
- 量産難易度が高すぎる軸を採用してしまう
"""

    files[".agents/skills/S3_UnitProduce/SKILL.md"] = """
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
  - C1: C1_KV_<axis>_image-pack.md（4案、主役/質感/背景/光/構図/禁止事項）
  - C2/C3: *_prompt-pack.md（形状/質感/構図/色/禁止事項）

## 注意
- 長文テキストを画像に焼かない
- 破綻（文字化け/ロゴっぽい文字/不自然な手など）があれば自己差し戻し候補にする
- C1は TrendScan v2 の上位軸のみを使う（品質ゲート未達なら生成しない）
- productionの本番画像は外部生成（C1は image-pack → 画像）
"""

    files[".agents/skills/S4_QA/SKILL.md"] = """
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
"""

    files[".agents/skills/S5_ShipAndStore/SKILL.md"] = """
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
  - C1の勝ち画像を優先して1〜2枚集約
- 05_LOGS/runs の該当runログに結果を追記

## 失敗条件
- 命名規則に違反
- メタデータ欠落
"""

    files[".agents/skills/S6_RenderPolish/SKILL.md"] = """
# SKILL: S6 RenderPolish

## 目的
C2 の production プレビューを生成し、production Gate を通す。

## いつ起動するか
- C2 の demo/index.html が生成されたとき
- S4 QAで「FAILED（render error）」になったとき

## いつ起動しないか
- demo/index.html が未生成のとき
- C1 のみを扱うとき（C1は Image Prompt Pack → 外部生成）

## 入力
- C2: 04_OUTPUT/production/YYYY-MM/YYYY-MM-DD/demo/index.html

## 出力（固定）
- C2: 04_OUTPUT/production/YYYY-MM/YYYY-MM-DD/demo/preview.png
- 05_LOGS/runs に Gate判定結果（合格/不合格理由を1行）

## 実行コマンド
- C2: `node scripts/renderpolish_c2_preview.mjs <demo/index.html>`

## 注意
- Chrome パス: /Applications/Google Chrome.app/Contents/MacOS/Google Chrome
- Chrome が無い場合は FAILED（render error）としてログに残す
- 外部有料APIは使わない（費用発生なし）

## 成功条件
- preview.png が production レーンに生成され、サイズ > 0 で Gate PASS
"""

    # -----------------------
    # Seed output example
    # -----------------------
    files[f"05_LOGS/runs/{now}_run_001.md"] = f"""
# Run Log: {now} / run_001

## A. 参照候補30件（URL）
- (placeholder)

## B. Gate判定（合格/不合格 + 理由）
- (placeholder)

## C. 合格参照一覧（10件以上）
- (placeholder)

## D. トレンド要約（5行）
- (placeholder)

## E. 表現軸カード（5〜12）
- (placeholder)

## F. 上位3軸（今回採用）
- (placeholder)

## G. 制作ユニット提案（本数）
- 3DTeaser: 3
- InteractiveFV: 1
- ExplainSlide: 1

## H. Gate判定結果
- (placeholder) 合格 / 不合格（品質NG） / BLOCKED（production未生成） / FAILED（render error）
"""

    # -----------------------
    # Write all files
    # -----------------------
    for rel_path, content in files.items():
        write_file(repo_root / rel_path, content)

    print("✅ Bootstrap completed.")
    print(f"Repo root: {repo_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
