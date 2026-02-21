# Change Log: 2026-02-21 / Axis Implementation 강화

## What
- TrendScan v2 のAxisカードに実装要素（HeroGeometry/Material/Lighting/Camera/Background/Motion/Composition/Do-Not）を必須化
- C2/C3/C4 の必須セクションを定義し、欠けたらFAILED
- C1 の必須実装要素（厚み/質感/接地影/背景ノイズ/微パララックス）を明文化

## Why
- Axisが抽象的で実装に落ちない問題を防ぎ、出力品質を底上げするため

## Impact
- Axisカードは実装要素が揃っていないとNG
- Rotation Run は必須セクション/要素が欠けたらFAILED扱い
