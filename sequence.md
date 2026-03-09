# シーケンス図

## 1. 日次自動実行フロー（automatic モード）

```mermaid
sequenceDiagram
    participant CRON as OpenClaw Cron
    participant MAIN as run_daily.py
    participant STATE as state.json
    participant PLOT as Plot Agent
    participant TITLE as Title Selection Agent
    participant STORY as Story Agent
    participant REVIEW as Review Agent
    participant PUB as Publish Agent
    participant IDX as stories_index.json
    participant GIT as Git / GitHub Pages

    CRON->>MAIN: 05:00 JST 起動
    MAIN->>STATE: 再開判定確認
    STATE-->>MAIN: 未実行 or failed（該当ステージから再開）

    MAIN->>PLOT: plot_prompt.md + stories_index + used_themes + banned_terms
    PLOT-->>MAIN: plot JSON（title_candidates × 3, plot, theme …）
    MAIN->>MAIN: JSON バリデーション

    MAIN->>TITLE: title_candidates × 3 + plot + theme + reading_impression
    TITLE-->>MAIN: selected_title JSON
    MAIN->>MAIN: JSON バリデーション
    MAIN->>MAIN: plot_bundle 保存（plot.json, selected_title.json）

    MAIN->>STORY: plot JSON + selected_title
    STORY-->>MAIN: story JSON（title, body, character_count …）
    MAIN->>MAIN: JSON バリデーション

    MAIN->>REVIEW: story JSON + banned_terms + stories_index（直近30作品）
    Note over MAIN,REVIEW: ローカル 3-gram Jaccard 類似度検査（閾値 0.55）を先行実施
    REVIEW-->>MAIN: review JSON（passed: true, scores …）

    MAIN->>MAIN: stories/YYYY/YYYY-MM-DD-slug.md 正本保存
    MAIN->>MAIN: 正本ファイル検証
    MAIN->>STATE: stage: publish, result: in_progress
    Note over MAIN,STATE: publish は sync_posts -> update_index -> git_commit_push -> mark_published の順で進む
    MAIN->>MAIN: site/_posts/ へ同期
    MAIN->>IDX: stories_index.json アトミック更新（.tmp経由）
    MAIN->>GIT: git add / commit / push
    GIT-->>MAIN: push 成功
    MAIN->>STATE: stage: publish, result: published, published_commit: <hash>
    MAIN->>MAIN: ログ保存（run.log, review.json, generation.txt）
    GIT->>GIT: GitHub Pages ビルド・公開
```

---

## 2. 日次自動実行フロー（manual_review モード）

```mermaid
sequenceDiagram
    participant CRON as OpenClaw Cron
    participant MAIN as run_daily.py
    participant STATE as state.json
    participant PLOT as Plot Agent
    participant TITLE as Title Selection Agent
    participant STORY as Story Agent
    participant REVIEW as Review Agent
    participant PENDING as pending/
    participant OPE as オペレーター
    participant PUB as publish_story.py
    participant IDX as stories_index.json
    participant GIT as Git / GitHub Pages

    CRON->>MAIN: 05:00 JST 起動
    MAIN->>STATE: 再開判定確認
    STATE-->>MAIN: 未実行

    MAIN->>PLOT: plot_prompt.md + 入力データ
    PLOT-->>MAIN: plot JSON
    MAIN->>TITLE: title_candidates + plot
    TITLE-->>MAIN: selected_title JSON
    MAIN->>MAIN: plot_bundle 保存（plot.json, selected_title.json）
    MAIN->>STORY: plot JSON + selected_title
    STORY-->>MAIN: story JSON
    MAIN->>REVIEW: story JSON + banned_terms + 直近30作品
    Note over MAIN,REVIEW: 毎回レビュー前にローカル 3-gram Jaccard 類似度検査を実施し、その結果も渡す
    REVIEW-->>MAIN: review JSON（passed: true）

    MAIN->>MAIN: stories/YYYY/YYYY-MM-DD-slug.md 正本保存
    MAIN->>MAIN: 正本ファイル検証
    MAIN->>STATE: stage: publish, result: in_progress
    MAIN->>PENDING: pending/YYYY/YYYY-MM-DD-slug.md 確認用コピー作成
    MAIN->>STATE: stage: publish, result: pending_review
    MAIN->>MAIN: ログ保存（自動停止 ※push しない）

    Note over OPE: Windows 通知なし（pending_review は正常停止）
    OPE->>PENDING: 確認用コピーを閲覧・確認
    OPE->>PUB: scripts/publish_story.py 手動実行

    PUB->>STATE: stage: publish, result: in_progress
    PUB->>PUB: stories/ 正本から site/_posts/ へ同期
    PUB->>IDX: stories_index.json アトミック更新
    PUB->>GIT: git add / commit / push
    GIT-->>PUB: push 成功
    PUB->>STATE: stage: publish, result: published, published_commit: <hash>
    GIT->>GIT: GitHub Pages ビルド・公開
```

---

## 3. レビュー不合格・再生成フロー

```mermaid
sequenceDiagram
    participant MAIN as run_daily.py
    participant STORY as Story Agent
    participant REVIEW as Review Agent
    participant IDX as stories_index.json
    participant STATE as state.json
    participant LOG as logs/
    participant WIN as Windows 通知

    MAIN->>STORY: plot JSON + selected_title（1回目）
    STORY-->>MAIN: story JSON

    MAIN->>REVIEW: story JSON + banned_terms + 直近30作品
    Note over MAIN,REVIEW: 初回・再生成後ともにローカル 3-gram Jaccard 類似度検査結果を添付する
    REVIEW-->>MAIN: review JSON（passed: false, rewrite_instruction: "..."）

    MAIN->>LOG: review.json に不合格理由を保存（試行 1/3）

    MAIN->>STORY: plot JSON + selected_title + rewrite_instruction（2回目）
    STORY-->>MAIN: story JSON

    MAIN->>REVIEW: story JSON + banned_terms + 直近30作品（再検査）
    REVIEW-->>MAIN: review JSON（passed: false）

    MAIN->>LOG: review.json に不合格理由を保存（試行 2/3）

    MAIN->>STORY: plot JSON + selected_title + rewrite_instruction（3回目）
    STORY-->>MAIN: story JSON

    MAIN->>REVIEW: story JSON + banned_terms + 直近30作品（再検査）
    REVIEW-->>MAIN: review JSON（passed: false）

    MAIN->>LOG: review.json に不合格理由を保存（試行 3/3 上限）
    MAIN->>STATE: stage: review, result: failed
    MAIN->>WIN: powershell.exe New-BurntToastNotification\n"本日分の生成が3回失敗しました"
    Note over MAIN: 公開処理は行わない（既存サイト維持）
```

---

## 4. オペレーターによる差し戻し・再生成フロー

```mermaid
sequenceDiagram
    participant OPE as オペレーター
    participant PENDING as pending/
    participant STORIES as stories/
    participant MAIN as run_daily.py
    participant STORY as Story Agent
    participant REVIEW as Review Agent
    participant PUB as publish_story.py
    participant STATE as state.json
    participant IDX as stories_index.json
    participant GIT as Git / GitHub Pages

    OPE->>PENDING: 確認用コピーを閲覧
    OPE->>OPE: 品質に問題あり → 差し戻し判断

    OPE->>MAIN: run_daily.py --from-stage story（差し戻し再実行）
    Note over MAIN: state.json の stage: story, result: in_progress に更新

    MAIN->>STORY: plot JSON + selected_title + 差し戻し理由
    STORY-->>MAIN: story JSON（再生成）
    MAIN->>REVIEW: story JSON + banned_terms + 直近30作品
    Note over MAIN,REVIEW: 差し戻し後もローカル 3-gram Jaccard 類似度検査結果を添付
    REVIEW-->>MAIN: review JSON（passed: true）

    MAIN->>STORIES: stories/ 正本を上書き保存
    MAIN->>PENDING: pending/ 確認用コピーを更新

    OPE->>PENDING: 再確認
    OPE->>PUB: scripts/publish_story.py 手動実行（承認）
    PUB->>STATE: stage: publish, result: in_progress
    PUB->>PUB: stories/ 正本から site/_posts/ へ同期
    PUB->>IDX: stories_index.json アトミック更新
    PUB->>GIT: git add / commit / push
    GIT-->>PUB: push 成功
    PUB->>STATE: stage: publish, result: published, published_commit: <hash>
    GIT->>GIT: GitHub Pages 公開
```

---

## 5. 障害・復旧フロー

```mermaid
sequenceDiagram
    participant CRON as OpenClaw Cron
    participant MAIN as run_daily.py
    participant STATE as state.json
    participant LOG as logs/
    participant WIN as Windows 通知
    participant OPE as オペレーター
    participant GIT as Git / GitHub Pages

    MAIN->>MAIN: 処理中に障害発生（Codex CLI 失敗 / push 失敗 等）
    MAIN->>STATE: stage: <失敗ステージ>, result: failed
    MAIN->>LOG: エラー詳細を run.log に保存
    MAIN->>WIN: Windows 通知発出（result: failed 遷移時）

    OPE->>WIN: 通知受信
    OPE->>LOG: logs/YYYY-MM-DD/run.log 確認
    OPE->>STATE: state.json の stage / result を確認
    Note over MAIN,STATE: plot stage は Plot Agent -> Title Selection Agent -> plot_bundle 保存を内包する

    alt stage=plot, result=failed or in_progress
        OPE->>MAIN: run_daily.py 再実行（plot stage）
        MAIN->>MAIN: artifacts.plot があり artifacts.selected_title がなければ Title Selection から再開
        MAIN->>MAIN: それ以外は Plot Agent から再実行
    else stage=story, result=failed or in_progress
        OPE->>MAIN: run_daily.py 再実行（story stage）
        MAIN->>MAIN: Story Agent から再実行
    else stage=review, result=failed
        OPE->>MAIN: run_daily.py --from-stage story
        MAIN->>MAIN: Story Agent から再生成
    else stage=publish, result=failed
        OPE->>MAIN: run_daily.py --from-stage publish
        MAIN->>STATE: stage: publish, result: in_progress
        MAIN->>MAIN: site/_posts 同期 → stories_index 更新 → git add / commit / push を冪等再実行
        GIT-->>MAIN: push 成功
        MAIN->>STATE: stage: publish, result: published, published_commit: <hash>
    else stage=publish, result=pending_review
        OPE->>OPE: pending/ を確認後に手動公開を判断
        OPE->>MAIN: scripts/publish_story.py 手動実行
        MAIN->>STATE: stage: publish, result: in_progress
        MAIN->>MAIN: site/_posts 同期 → stories_index 更新 → git add / commit / push
        GIT-->>MAIN: push 成功
        MAIN->>STATE: stage: publish, result: published, published_commit: <hash>
    end

    Note over CRON,STATE: 翌日 05:00 になった場合も同じ再開判定ルール（§9.4）が適用される
    Note over CRON,STATE: stage=publish / result=pending_review は翌日自動再生成しない
```

---

## 6. 読者によるサイト閲覧フロー

```mermaid
sequenceDiagram
    participant READER as 読者
    participant PAGES as GitHub Pages
    participant JEKYLL as Jekyll（静的HTML）
    participant ADS as Google AdSense

    READER->>PAGES: https://garyohosu.github.io/writer/ アクセス
    PAGES->>JEKYLL: index.html（作品一覧）
    JEKYLL-->>READER: 作品一覧ページ（stories_index 反映済み）

    READER->>PAGES: 作品ページ /posts/<slug>/ アクセス
    PAGES->>JEKYLL: 作品 Markdown → HTML レンダリング
    JEKYLL-->>READER: 作品本文（title / summary / tags / reading_time_min 付き）

    READER->>ADS: 広告スクリプト読込（本文上部・下部）
    ADS-->>READER: 広告表示
```
