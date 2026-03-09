# SPEC.md
## 1日1冊短編小説サイト 仕様書
**Project Name:** DailyShortStorySite  
**Version:** 1.0.0  
**Date:** 2026-03-09  
**Primary Runtime:** Win11 + WSL2  
**Scheduler:** OpenClaw Cron  
**Main Generation Engine:** Codex CLI 定額利用（GPT-5.4）  
**Publishing Target:** GitHub Pages  
**Monetization Requirement:** Google AdSense 必須

---

## 1. 目的

本システムは、Codex CLI の定額利用環境を活用し、毎日1本の短編小説を自動生成・品質確認・公開する静的Webサイトを構築することを目的とする。

サイトは以下を満たすことを必須条件とする。

- 毎日1本の新規短編小説を自動生成する
- GitHub Pages に自動公開する
- Google AdSense を掲載できる構成にする
- OpenClaw の cron により毎日定時実行する
- Win11 + WSL2 環境で運用可能である
- 作品品質を担保するため、生成・編集・検査・公開を段階分離する
- 過去作品との類似や品質低下を抑制する


googleアドセンスを各ページに入れておくこと
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-6743751614716161"
     crossorigin="anonymous"></script>

各ページはCDNを使ったモダン技術ブログ的外観のサイトとすること

---

## 2. スコープ

### 2.1 対象範囲
- 短編小説の自動生成
- 生成作品の自動レビュー
- 作品メタデータ生成
- Markdown ファイル生成
- GitHub Pages 向け静的サイト更新
- 広告表示用レイアウト埋め込み
- OpenClaw cron による日次運用
- ログ保存
- 再生成・差し戻し制御

### 2.2 対象外
- ユーザー会員登録
- コメント機能
- 決済機能
- リアルタイムAPI提供
- 読者ごとのレコメンド
- 完全無人の無制限自己改善機構

---

## 3. 前提条件

### 3.1 使用技術
- Windows 11
- WSL2 (Ubuntu 想定)
- Git
- Python 3.8 以上
- Codex CLI
- OpenClaw
- GitHub Pages
- Markdown ベースのコンテンツ管理
- Jekyll（GitHub Pages 標準、MVP では固定）+ Chirpy テーマ
- Google AdSense
- ads.txt 配置
- Python venv（WSL2 内仮想環境管理）

### 3.2 AI利用前提
- 主要な本文生成は Codex CLI + GPT-5.4 を利用する
- 定額利用前提のため、API課金ベースではなく CLI 実行ベースで設計する
- 品質評価も原則 Codex CLI を使う
- 必要に応じてローカル補助チェックを追加可能だが必須ではない

### 3.3 公開前提
- GitHub Pages 側は既存ブログまたは専用リポジトリで運用する
- AdSense 審査通過済みサイト、または審査通過を前提とする
- 広告コード、プライバシーポリシー、問い合わせ導線を配置する

---

## 4. システム概要

本システムは以下の4段階で動作する。

1. **企画生成**
   - 当日のテーマ、舞台、主人公属性、結末傾向を決定する
2. **本文生成**
   - Codex CLI により短編小説本文を生成する
3. **品質検査**
   - 読みやすさ、一貫性、類似度、禁止事項を点検する
4. **公開**
   - Markdown と一覧情報を更新し GitHub に push して Pages へ反映する

---

## 5. コンセプト方針

### 5.1 サイトの方向性
- 毎日読める短編小説サイト
- 1話完結形式
- 読了時間 3〜8分程度
- シリーズ感は持たせるが、各話は単独で読める
- 世界観を統一し、雑多な生成物置き場にしない

### 5.2 推奨ジャンル
以下のような一貫したテーマを選べる設計とする。

- 日常の中の小さな不思議
- 猫が関わる短編
- 仕事帰りに読める少し切なく温かい話
- 軽いSF短編
- 現代日常 + 微ファンタジー

### 5.3 文体方針
- 過剰に説明的にしない
- AI特有の冗長さを避ける
- 冒頭3行で引き込む
- 特定の実在作家模倣は禁止
- 既存作品の二次創作は禁止

---

## 6. 非機能要件

### 6.1 可用性
- 1日1回の定時実行に成功すること
- 一時的失敗時は再試行可能であること
- 実行失敗時に前日公開済みサイトを壊さないこと

### 6.2 保守性
- コンテンツは 1作品1Markdown で管理する
- 状態管理は JSON で行う
- ログは日付単位で保存する
- プロンプトは外部ファイル化する

### 6.3 拡張性
- 後から英訳版を追加できる
- 後から画像生成を追加できる
- 後からランキングや検索を追加できる

### 6.4 セキュリティ
- GitHub Token は環境変数管理とする
- AdSense コードを壊さないテンプレート制御を行う
- 秘密情報を作品本文に混入させない
- OpenClaw 上の実行権限を限定する

---

## 7. ディレクトリ構成

```text
project-root/
  SPEC.md
  README.md
  config.json
  prompts/
    plot_prompt.md
    story_prompt.md
    title_selection_prompt.md
    review_prompt.md
  data/
    state.json
    stories_index.json
    used_themes.json
    banned_terms.json
  stories/
    2026/
      2026-03-09-midnight-cat.md
  logs/
    2026-03-09/
      run.log
      review.json
      generation.txt
  scripts/
    run_daily.py
    generate_plot.py
    select_title.py
    generate_story.py
    review_story.py
    publish_story.py
    rebuild_indexes.py
  pending/
    2026/
      2026-03-09-midnight-cat.md
  site/
    _posts/
      2026-03-09-midnight-cat.md
    _includes/
    ads.txt
    privacy-policy.md
    contact.md
```

### 7.1 保存先の役割分担
- `stories/` を作品 Markdown の**正本**とする
- `pending/` は `manual_review` モード時の**確認用コピー置き場**とする
- `site/_posts/` は Jekyll 公開用の**派生物**とし、公開時に `stories/` から生成または同期する
- 人手による修正・再レビューは必ず `stories/` 側に対して行い、`pending/` や `site/_posts/` を直接編集しない

---

## 8. コンテンツ要件

### 8.1 作品要件
- 1日1作品
- 目安 2,000〜5,000字
- 読了時間の目安を付与
- 必ずタイトル、要約、タグ、公開日を持つ
- 1作品ごとに一意の slug を持つ
- 本文量は `word_count` ではなく `character_count` で管理する
- `character_count` は YAML front matter を除いた本文文字数とし、表示・制約・集計で同じ値を使う

### 8.2 作品形式
作品は Markdown で保存する。

例:

```md
---
title: "夜勤明けの猫はエレベーターを待っていた"
date: "2026-03-09"
slug: "2026-03-09-midnight-cat"
tags: ["猫", "日常", "不思議"]
genre: "短編"
theme: "疲れた心に小さな異界が触れる"
character_count: 3120
reading_time_min: 6
status: "published"
summary: "夜勤明けの技術者が、会社の片隅で奇妙な猫に出会う短編。"
ai_generated: true
review_score: 86
---
本文...
```

### 8.3 禁止事項
- 実在作家の文体模倣
- 差別的内容
- 過度な暴力・性的描写
- 著作権侵害が疑われる固有表現
- 過去作の過剰な焼き直し
- 読者を欺く虚偽の「人間執筆偽装」

### 8.4 banned_terms.json 管理方針
- **初期リストは手動で作成する**（空スタートは禁止）
- 初期リストに含める最低限の分類:

| 分類 | 例 |
|---|---|
| 差別語 | 各種差別的表現 |
| 過度な暴力・性的語 | 直接的描写語句 |
| 実在作家名 | 著名作家の実名 |
| 特定作品名 | 著作権リスクのある固有タイトル |
| 危険な誘導表現 | 自傷・犯罪誘導に読み取られる語句 |

- 運用中に問題が発覚した語句は随時追記する（追記方式で育てる）
- プロンプトと Review Agent の両方から参照する

---

## 9. 状態管理仕様

### 9.1 state.json
日次実行の状態を単一レコードで保持する。`status` と `pipeline_stage` の二重管理は廃止し、`stage` と `result` の組み合わせで再開判定を行う。

フィールド定義:

| フィールド | 型 | 説明 |
|---|---|---|
| `run_date` | string (ISO 8601, JST) | 実行対象日 |
| `job_id` | string (UUID) | 実行識別子 |
| `stage` | enum | 現在パイプライン段階 |
| `result` | enum | 実行結果 |
| `slug` | string \| null | 生成作品の slug |
| `attempts` | object | 各ステージの試行回数 |
| `artifacts` | object | 中間生成物のパス |
| `published_commit` | string \| null | push 済みコミットハッシュ |

例:

```json
{
  "run_date": "2026-03-09",
  "job_id": "a1b2c3d4-0000-0000-0000-000000000000",
  "stage": "publish",
  "result": "published",
  "slug": "2026-03-09-midnight-cat",
  "attempts": { "story": 1, "review": 2 },
  "artifacts": {
    "plot": "logs/2026-03-09/plot.json",
    "story": "logs/2026-03-09/generation.txt",
    "review": "logs/2026-03-09/review.json"
  },
  "published_commit": "abc1234"
}
```

`publication_mode = manual_review` の承認待ち状態では、`stage: "publish"`、`result: "pending_review"`、`published_commit: null` とする。

### 9.2 stage 定義
- `plot` : 企画生成中
- `story` : 本文生成中
- `review` : 品質検査中
- `publish` : 公開処理中

### 9.3 result 定義
- `in_progress` : 実行中
- `failed` : 異常終了
- `pending_review` : レビュー合格済みで、人手承認待ち
- `published` : 公開済み

### 9.4 再開判定ルール

| stage | result | 次回動作 |
|---|---|---|
| `publish` | `pending_review` | `stories/` と `pending/` を保持し、手動公開されるまで自動再生成しない |
| `publish` | `published` | 当日分スキップ |
| `publish` | `failed` | 成果物があれば公開処理のみ再実施 |
| `review` | `failed` | Story Agent から再生成 |
| それ以外 | `failed` / `in_progress` | 該当ステージから再実行 |

---

## 10. stories_index.json 仕様

全公開作品一覧を保持する。**日付降順（新しい順）で保持する**。一覧ページはこの順序をそのまま表示に使うため、フロント側でのソート処理は不要とする。

例:

```json
[
  {
    "date": "2026-03-09",
    "slug": "2026-03-09-midnight-cat",
    "title": "夜勤明けの猫はエレベーターを待っていた",
    "summary": "夜勤明けの技術者が、会社の片隅で奇妙な猫に出会う短編。",
    "tags": ["猫", "日常", "不思議"],
    "character_count": 3120,
    "reading_time_min": 6,
    "review_score": 86
  }
]
```

---

## 11. AIエージェント役割分担

### 11.1 Plot Agent
役割:
- 今日のプロットを作る
- 過去作と被らないテーマを出す
- 主人公、舞台、転換点、結末を設計する
- タイトル候補3件を提示する（選定は §11.5 の Title Selection Agent が行う）

入力:
- 過去作品インデックス
- 直近使用テーマ（used_themes.json 直近90日分）
- 禁止語リスト（banned_terms.json）
- 本日の生成ルール

出力: **JSON only**（以下スキーマに厳密に従うこと）

```json
{
  "title_candidates": ["候補A", "候補B", "候補C"],
  "plot": "200〜400字のプロット本文",
  "characters": [
    { "name": "主人公名", "role": "主人公", "attribute": "属性説明" }
  ],
  "theme": "テーマ一文",
  "setting": "舞台説明",
  "ending_type": "ハッピー|バッドエンド|余韻系|etc",
  "reading_impression": "想定読後感"
}
```

### 11.2 Story Agent
役割:
- プロットと確定タイトルから本文を書く
- 指定文字数に収める
- 文体ガイドを守る

入力:
- Plot Agent の出力 JSON
- Title Selection Agent が選んだ確定タイトル1件

出力: **JSON only**（以下スキーマに厳密に従うこと）

```json
{
  "title": "確定タイトル",
  "body": "本文（2000〜5000字）",
  "character_count": 3120,
  "reading_time_min": 6,
  "summary": "要約（100〜200字）",
  "tags": ["タグ1", "タグ2"]
}
```

### 11.3 Review Agent
役割:
- 一貫性
- 読みやすさ
- 冗長性
- 類似度
- 禁止事項
- タイトル訴求力
を評価する

出力: **JSON only**（以下スキーマに厳密に従うこと）

```json
{
  "passed": true,
  "scores": {
    "originality": 85,
    "readability": 80,
    "consistency": 90,
    "hook": 78,
    "ending": 82,
    "overall": 83
  },
  "issues": ["問題点1", "問題点2"],
  "adsense_risk": false,
  "rewrite_instruction": null
}
```

- `passed` が `false` の場合、`rewrite_instruction` に再生成指示を必ず記述する
- `adsense_risk` が `true` の場合は自動的に `passed: false` とする

### 11.4 Publish Agent
役割:
- Markdown を保存
- インデックス更新
- Git add / commit / push
- GitHub Pages へ反映

### 11.5 Title Selection Agent
役割:
- Plot Agent が提示したタイトル候補3件を採点し、1件を選ぶ
- Plot Agent・Story Agent の責務を分離し、タイトル選定の品質を独立して調整できるようにする

入力:
- `title_candidates`（3件）
- `plot`（プロット内容）
- `theme`（テーマ）
- `reading_impression`（想定読後感）

出力: **JSON only**（以下スキーマに厳密に従うこと）

```json
{
  "selected_title": "選定タイトル",
  "reason": "選定理由（1〜2文）",
  "scores": {
    "候補A": 82,
    "候補B": 75,
    "候補C": 68
  }
}
```

評価観点:
- プロット内容との一致度
- 冒頭の引き（クリック誘引力）
- 既存タイトルとの重複回避
- タイトル冒頭語の重複回避（過去30作品と比較）

---

## 12. 実行フロー

### 12.1 通常フロー
1. OpenClaw cron が日次実行
2. WSL2 上で run_daily.py を起動
3. state.json を確認し再開判定（§9.4参照）
4. 当日分作品未生成なら処理継続
5. 過去作一覧読込
6. Plot Agent 実行 → JSON バリデーション
7. Title Selection Agent 実行 → 確定タイトル決定 → JSON バリデーション
8. Story Agent 実行（確定タイトルを渡す）→ JSON バリデーション
9. Review Agent 実行 → JSON バリデーション
10. **保存・公開処理**
   1. 作品 Markdown を正本として `stories/YYYY/YYYY-MM-DD-slug.md` に書き込む
   2. 正本ファイルを検証する
   3. `publication_mode = manual_review` の場合:
      - `pending/YYYY/YYYY-MM-DD-slug.md` に確認用コピーを作成する
      - `state.json` を `stage: publish`, `result: pending_review` に更新する
      - `stories_index.json`、`site/_posts/`、`git push` は更新せず終了する
      - ログ保存
   4. `publication_mode = automatic` の場合:
      - `stories/` 正本から `site/_posts/YYYY-MM-DD-slug.md` を生成または同期する
      - `stories_index.json` をアトミック更新（`.tmp` 経由の `replace`）
      - `git add / commit / push`
      - push 成功確認後に `state.json` を `result: published` に更新する
      - ログ保存
   - **注意**: `manual_review` / `automatic` のいずれでも、push 成功前に `state.json` を `published` に更新しない

### 12.2 再生成フロー
レビュー不合格時:

1. 改善理由を review.json に保存
2. Story Agent に改善指示を与えて再生成
3. 最大3回まで再試行
4. 3回失敗時は `result: failed` とし、以下の通知を発出する:
   - ログファイルに詳細を記録する
   - Windows 通知を発出する（OpenClaw 経由または PowerShell 呼び出し）
     ```bash
     powershell.exe -c "New-BurntToastNotification -Text 'DailyStory', '本日分の生成が3回失敗しました'"
     ```
5. 公開は行わない

### 12.3 障害時フロー
- push 失敗時はファイルをローカル保持
- `stories/` 正本は保持し、`manual_review` 中なら `pending/` コピーも保持する
- state.json を `failed` に更新
- 既存公開サイトは維持する
- 次回実行時に未公開成果物を再処理可能とする

---

## 13. 品質評価仕様

### 13.1 評価軸
各作品は以下で採点する。

- 独自性
- 読みやすさ
- 一貫性
- 冒頭の引き
- 結末の余韻
- 禁止事項抵触有無

### 13.2 合格基準
- 独自性: 80点以上
- 読みやすさ: 75点以上
- 一貫性: 85点以上
- 総合: 80点以上
- 禁止事項: 問題なし

### 13.3 類似度抑制
以下を必須とする。

- 直近30作品のタイトル + 要約を比較対象に含める
- 舞台、主人公属性、オチ類型が連続しすぎないよう制約を設ける
- タイトル冒頭語の重複を避ける
- 同一テーマが再出現しないよう used_themes.json を参照する（**保持期間: 直近90日**）

**ローカル事前検査（LLM 判定の前に必ず実施する）**

日本語作品では、タイトル + 要約を連結した文字列に対して**文字 3-gram Jaccard 類似度**を用いる。比較対象は直近30作品の `title + summary` とし、初期閾値は `0.55` とする。将来、必要に応じて形態素解析ベースへ差し替えてよい。

```python
def char_ngrams(text: str, n: int = 3) -> set[str]:
    normalized = "".join(text.lower().split())
    if not normalized:
        return set()
    if len(normalized) < n:
        return {normalized}
    return {normalized[i:i+n] for i in range(len(normalized) - n + 1)}

def jaccard_3gram(a: str, b: str) -> float:
    sa, sb = char_ngrams(a), char_ngrams(b)
    return len(sa & sb) / max(1, len(sa | sb))

candidate = f"{new_title}\n{new_summary}"
recent_30_candidates = [f"{s['title']}\n{s['summary']}" for s in recent_30_stories]

if any(jaccard_3gram(candidate, s) > 0.55 for s in recent_30_candidates):
    raise ValueError("summary_too_similar")
```

LLM による類似度・AdSense 適性評価は、このローカル検査を通過した作品にのみ実施する。

---

## 14. プロンプト設計方針

### 14.1 Plot Prompt
目的:
- 今日の話の骨格を作る

含むべき内容:
- サイトの世界観
- 直近作品との差別化
- 禁止事項
- 文体傾向
- 必須出力項目

### 14.2 Story Prompt
目的:
- 実際の本文生成

含むべき内容:
- 文字数範囲
- プロット
- 文体制約
- 説明過多回避
- 冒頭の引き
- 読後感

### 14.4 Title Selection Prompt
目的:
- Plot Agent が提示した3件のタイトル候補から最適な1件を選ぶ

含むべき内容:
- タイトル候補3件
- プロット・テーマ・想定読後感
- 過去30作品のタイトル冒頭語リスト（重複回避用）
- 評価観点（引き力・プロット整合性・独自性）

**出力制約**:
- 必ず §11.5 で定義した JSON スキーマのみを出力すること
- プロンプト末尾に明示する: `Output must be valid JSON only. No explanation.`

### 14.3 Review Prompt
目的:
- 作品検査

含むべき内容:
- 数値評価
- 改善点列挙
- 合否判定
- 過去作との差別化評価
- AdSense 適性上の危険表現有無の点検

**出力制約**:
- 必ず §11.3 で定義した JSON スキーマのみを出力すること
- JSON 以外のテキスト（説明文・前置き・Markdown 装飾など）を一切含めないこと
- プロンプト末尾に明示する: `Output must be valid JSON only. No explanation.`

---

## 15. 広告・AdSense 要件

### 15.1 必須要件
- AdSense コードをテンプレートへ埋め込む
- ads.txt をサイトルートへ配置する
- プライバシーポリシーを公開する
- お問い合わせページを設置する
- AI生成コンテンツである旨を明記する

### 15.2 ページ配置方針
**MVP では固定枠のみで開始する**（自動広告は使用しない）。

固定枠の配置:

| 枠 | 位置 | 備考 |
|---|---|---|
| 記事上部 | 本文直上 | 1枠 |
| 記事下部 | 本文直下 | 1枠 |
| 一覧下部 | 一覧ページ末尾 | 1枠 |

- サイドバーなし・モバイルファースト構成を優先する
- 一覧ページ上部には広告を置かない
- 自動広告は品質安定後に様子を見て追加を検討する

### 15.3 注意事項
- 広告過多で本文を圧迫しない
- 自動広告と固定枠の併用はレイアウト崩れに注意（MVP 期間中は固定枠のみ）
- GitHub Pages であっても AdSense 利用自体は可能だが、審査・ポリシー順守を要する
- コンテンツの薄さは審査・維持の両面で不利

---

## 16. GitHub Pages 要件

### 16.1 前提
- GitHub Pages で静的公開する
- Jekyll + Chirpy テーマを使用する（MVP では固定）
- **当面は GitHub Pages 標準 URL（`garyohosu.github.io/writer` 相当）で運用する**
- `_config.yml` に `url: "https://garyohosu.github.io"`、`baseurl: "/writer"`、`permalink: /posts/:slug/` を明示する
- サイト内リンク、ナビゲーション、canonical URL、OGP URL は `{{ site.url }}{{ site.baseurl }}{{ page.url }}` を基準に生成する
- 独自ドメインへの移行は後から可能だが、MVP 期間中は不要とする

### 16.2 必要ファイル
- _config.yml
- index.html または一覧テンプレート
- 作品ページテンプレート
- privacy-policy.md
- contact.md
- ads.txt
- sitemap.xml
- robots.txt

### 16.3 SEO 基本要件
- title, description, og tags を作品ごとに生成
- canonical / `og:url` は `{{ site.url }}{{ site.baseurl }}{{ page.url }}` で統一する
- 日付・要約・タグを埋め込む
- sitemap を更新
- 内部リンクを自動更新する
- 月別アーカイブまたはタグ一覧を持つ

---

## 17. OpenClaw cron 要件

### 17.1 役割
- 毎日定時で WSL2 上の生成スクリプトを呼び出す
- 失敗時のログを確保する
- 再実行可能な構成にする

### 17.2 実行例
OpenClaw 側から以下相当のコマンドを叩く想定。

```bash
wsl bash -lc 'cd /path/to/project && python3 scripts/run_daily.py >> logs/cron.log 2>&1'
```

### 17.3 実行タイミング
- 推奨: 毎日 05:00 JST
- 理由:
  - 日付単位管理しやすい
  - 読者が朝に新作を見つけやすい
  - 障害時の手動復旧余地がある

---

## 18. Win11 + WSL2 運用要件

### 18.1 必須
- Git 操作が WSL2 内で完結すること
- Python 実行環境を WSL2 内に固定する
- パス依存を避ける
- OpenClaw から WSL を起動可能であること

### 18.2 タイムゾーン
- 日付管理はすべて JST（Asia/Tokyo）で行う
- 実装では `ZoneInfo("Asia/Tokyo")` を必ず使用する

```python
from datetime import datetime
try:
    from zoneinfo import ZoneInfo          # Python 3.9+
except ImportError:
    from backports.zoneinfo import ZoneInfo  # Python 3.8: pip install backports.zoneinfo

run_date = datetime.now(ZoneInfo("Asia/Tokyo")).date().isoformat()
```

- Python 3.8 環境では `pip install backports.zoneinfo` が必要

- `date` フィールドへの UTC や naive datetime の混入を禁止する

### 18.3 Python 仮想環境
- **venv を使用する**（シンプルで標準的、cron 実行時のパス固定が容易）

```bash
# セットアップ
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

- cron 実行コマンドでは絶対パスで venv の Python を指定する

```bash
wsl bash -lc 'cd /path/to/project && .venv/bin/python scripts/run_daily.py >> logs/cron.log 2>&1'
```

- conda・uv は使わない（MVP 期間中のトラブル要因を増やさない）

### 18.4 推奨
- 専用ユーザーまたは専用ディレクトリで運用
- .env にトークン類を集約
- ローカルテストコマンドを別途用意
- 改行コードは LF に統一

---

## 19. ログ・監査要件

### 19.1 保存対象
- 実行ログ
- 生成プロット
- 生成本文
- レビュー結果
- push 実行結果

### 19.2 保存期間
- 最低90日
- 容量が許せば全保存

### 19.3 目的
- 品質劣化の追跡
- 類似作の分析
- 障害復旧
- プロンプト改善

---

## 20. エラー処理要件

### 20.1 失敗分類
- Codex CLI 実行失敗
- 出力フォーマット不正（JSON バリデーションエラー）
- レビュー不合格（最大3回）
- Git push 失敗
- インデックス更新失敗

### 20.2 原則
- 公開処理前に失敗した場合、既存サイトは変更しない
- 中間生成物は保存する
- state.json に失敗箇所を残す
- 次回再実行時に再開判断可能とする

### 20.3 通知
- **すべての `result: failed` 遷移時に Windows 通知を発出する**（§12.2 参照）
- ログのみでは失敗を見落とすリスクがあるため、通知は必須とする
- メール通知は将来拡張とし、MVP では Windows 通知で対応する

---

## 21. MVP定義

最初に必須とする機能:

1. 日次で1作品生成
2. Markdown 保存
3. 作品一覧更新
4. GitHub Pages 公開
5. AdSense テンプレート埋め込み
6. ads.txt 配置
7. プライバシーポリシー
8. 品質チェック
9. 再生成最大3回
10. ログ保存

---

## 22. 将来拡張

- 英訳版の同時生成
- 作品サムネイル自動生成
- 音声読み上げ版生成
- 月間ベスト短編集の自動PDF化
- 作品人気集計
- 連作シリーズモード
- note や Medium への再利用

---

## 23. 受け入れ条件

以下をすべて満たした場合に受け入れとする。

- OpenClaw cron から日次実行できる
- WSL2 内で Codex CLI を呼び出せる
- 作品が所定文字数で生成される
- レビュー不合格時に差し戻しされる
- `manual_review` ではレビュー合格後に `pending_review` で停止できる
- 合格時のみ公開される
- GitHub Pages に反映される
- AdSense コードがテンプレートに含まれる
- ads.txt / privacy-policy / contact が存在する
- `stories/` を正本、`site/_posts/` を公開用派生物として運用できる
- state.json と stories_index.json が更新される
- ログが残る

---

## 24. 実装優先順位

### Phase 1
- 単発生成
- Markdown保存
- GitHub Pages反映

### Phase 2
- 品質レビュー
- 差し戻し
- 状態管理

### Phase 3
- AdSenseテンプレート最適化
- SEO自動化
- アーカイブ強化

### Phase 4
- 英訳版
- 画像生成
- 音声化

---

## 25. 実装メモ

- 最初から完全無人にしない方が安全
- 初期運用は「自動生成 + 人間最終確認」でもよい
- 品質安定後に完全自動公開へ移行する
- 毎日更新サイトは品質の最低線が最重要
- AIは働き者だが、時々うっとりしながら説明を盛るのでレビュー工程は省略しない

### 25.1 公開モード設定
運用フェーズに応じて公開モードを切り替えられるよう、設定値で明示する。

設定ファイル（`config.json`）に以下を定義する:

```json
{
  "publication_mode": "manual_review"
}
```

| 値 | 動作 |
|---|---|
| `manual_review` | 生成・レビュー後に `stories/` を正本保存し、`pending/` に確認用コピーを置いて `result: pending_review` で停止する |
| `automatic` | レビュー合格後に自動で push・公開 |

- **デフォルト値は `manual_review` に固定する**（設定ファイル未読時のフォールバックも `manual_review`）
- `automatic` への切替は品質が安定した段階で行う
- `manual_review` 時の手動公開は、`pending/` を確認後に `scripts/publish_story.py` を実行し、`stories/` 正本から `site/_posts/` と `stories_index.json` を更新する
- 手動公開スクリプトでも、push 成功確認後に `state.json` を `result: published` に更新する

---

## 26. 結論

本仕様では、**Codex CLI 定額利用の GPT-5.4 を中核に、Win11 + WSL2 上で OpenClaw cron により毎日短編小説を生成・審査・公開し、GitHub Pages + AdSense で運用する日次自動小説サイト**を構築する。

最適な設計思想は以下である。

- 静的サイトで堅実に運用する
- 作品は Markdown で資産化する
- 生成と審査を分離する
- 広告要件を初期段階から組み込む
- 状態管理とログを残して運用事故を防ぐ

以上を本システムの正式仕様とする。
