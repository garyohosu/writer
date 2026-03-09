# ui.md
## DailyShortStorySite UI 設計書

**Theme:** Jekyll + Chirpy
**方針:** モバイルファースト・モダン技術ブログ的外観・CDN 利用・AdSense 固定枠3箇所

---

## 1. サイト全体構成図（サイトマップ）

```mermaid
graph TD
    TOP["🏠 トップページ\n（作品一覧）"]
    ARTICLE["📖 記事詳細ページ\n/posts/:slug"]
    TAG["🏷️ タグ一覧\n/tags/"]
    ARCHIVE["📅 月別アーカイブ\n/archives/"]
    PRIVACY["🔒 プライバシーポリシー\n/privacy-policy/"]
    CONTACT["✉️ お問い合わせ\n/contact/"]
    ADS["📄 ads.txt\n（サイトルート）"]
    SITEMAP["🗺️ sitemap.xml"]
    ROBOTS["🤖 robots.txt"]

    TOP --> ARTICLE
    TOP --> TAG
    TOP --> ARCHIVE
    TOP --> PRIVACY
    TOP --> CONTACT
    TOP -.-> ADS
    TOP -.-> SITEMAP
    TOP -.-> ROBOTS

    TAG --> ARTICLE
    ARCHIVE --> ARTICLE
```

---

## 2. ナビゲーション遷移図

```mermaid
graph LR
    subgraph NAV["グローバルナビゲーション（全ページ共通）"]
        N1["🏠 ホーム"] --> TOP
        N2["🏷️ タグ"] --> TAG
        N3["📅 アーカイブ"] --> ARCHIVE
        N4["🔒 プライバシー"] --> PRIVACY
        N5["✉️ お問い合わせ"] --> CONTACT
    end

    TOP["一覧ページ"] -->|記事カードクリック| ARTICLE["記事詳細"]
    ARTICLE -->|タグクリック| TAG["タグ一覧"]
    ARTICLE -->|前後ナビ| ARTICLE
    TAG -->|記事クリック| ARTICLE
    ARCHIVE -->|記事クリック| ARTICLE
```

---

## 3. トップページ（作品一覧）ワイヤーフレーム

```mermaid
graph TD
    subgraph PAGE["トップページ（モバイル幅 max 768px 基準）"]
        HD["━━━━━━━━━━━━━━━━━━━━━━━━━━━\n🏠  DailyShortStory  ☰\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\nヘッダー / サイト名 / ハンバーガーメニュー"]

        AD1["┌─────────────────────────┐\n│  📢 AdSense 固定枠①     │\n│      一覧ページ上部      │\n└─────────────────────────┘"]

        HERO["━━━━━━━━━━━━━━━━━━━━━━━━━━━\n✨ 最新作品ピックアップ\n『タイトル』\n要約テキスト…  [続きを読む →]\n━━━━━━━━━━━━━━━━━━━━━━━━━━━"]

        CARD1["┌─────────────────────────┐\n│ 2026-03-09  #猫 #日常   │\n│ 📖 タイトルA            │\n│ 要約テキスト（2行）      │\n│ 読了時間 6分  スコア 86  │\n└─────────────────────────┘"]

        CARD2["┌─────────────────────────┐\n│ 2026-03-08  #SF         │\n│ 📖 タイトルB            │\n│ 要約テキスト（2行）      │\n│ 読了時間 5分  スコア 82  │\n└─────────────────────────┘"]

        DOTS["…（日付降順で続く）"]

        AD2["┌─────────────────────────┐\n│  📢 AdSense 固定枠②     │\n│      一覧ページ下部      │\n└─────────────────────────┘"]

        FT["━━━━━━━━━━━━━━━━━━━━━━━━━━━\nフッター\nプライバシーポリシー | お問い合わせ\nAI生成コンテンツ明記 | © DailyShortStory\n━━━━━━━━━━━━━━━━━━━━━━━━━━━"]
    end

    HD --> AD1 --> HERO --> CARD1 --> CARD2 --> DOTS --> AD2 --> FT
```

---

## 4. 記事詳細ページワイヤーフレーム

```mermaid
graph TD
    subgraph PAGE["記事詳細ページ"]
        HD["━━━━━━━━━━━━━━━━━━━━━━━━━━━\n🏠  DailyShortStory  ☰\n━━━━━━━━━━━━━━━━━━━━━━━━━━━"]

        META["━━━━━━━━━━━━━━━━━━━━━━━━━━━\n📖 タイトル\n2026-03-09  読了 6分  #猫 #日常\n━━━━━━━━━━━━━━━━━━━━━━━━━━━"]

        AD1["┌─────────────────────────┐\n│  📢 AdSense 固定枠①     │\n│      記事上部            │\n└─────────────────────────┘"]

        NOTICE["💡 本作品はAIが生成した短編小説です。"]

        BODY["━━━━━━━━━━━━━━━━━━━━━━━━━━━\n本文（2,000〜5,000字）\n\n　冒頭3行で読者を引き込む。\n\n　……\n\n　（結末・余韻）\n━━━━━━━━━━━━━━━━━━━━━━━━━━━"]

        AD2["┌─────────────────────────┐\n│  📢 AdSense 固定枠②     │\n│      記事下部            │\n└─────────────────────────┘"]

        TAGS["🏷️ タグ: #猫  #日常  #不思議"]

        NAV["← 前の作品　　　　次の作品 →"]

        FT["━━━━━━━━━━━━━━━━━━━━━━━━━━━\nフッター\n━━━━━━━━━━━━━━━━━━━━━━━━━━━"]
    end

    HD --> META --> AD1 --> NOTICE --> BODY --> AD2 --> TAGS --> NAV --> FT
```

---

## 5. タグ一覧ページワイヤーフレーム

```mermaid
graph TD
    subgraph PAGE["タグ一覧ページ"]
        HD["ヘッダー"]

        TAGCLOUD["━━━━━━━━━━━━━━━━━━━━━━━━━━━\n🏷️ タグ一覧\n\n  #猫 (12)  #日常 (20)  #SF (8)\n  #ファンタジー (5)  #不思議 (15)\n  …\n━━━━━━━━━━━━━━━━━━━━━━━━━━━"]

        FILTERED["━━━━━━━━━━━━━━━━━━━━━━━━━━━\n#猫 の作品一覧（12件）\n\n  📖 タイトルA  2026-03-09\n  📖 タイトルB  2026-03-01\n  …\n━━━━━━━━━━━━━━━━━━━━━━━━━━━"]

        FT["フッター"]
    end

    HD --> TAGCLOUD --> FILTERED --> FT
```

---

## 6. AdSense 配置まとめ

```mermaid
graph LR
    subgraph LIST["一覧ページ"]
        LA1["枠① 上部"]
        LA2["枠② 下部"]
    end

    subgraph ARTICLE["記事ページ"]
        AA1["枠① 記事上部"]
        AA2["枠② 記事下部"]
    end

    subgraph RULE["ルール"]
        R1["固定枠のみ\n（自動広告は MVP 期間中使用しない）"]
        R2["本文を広告で分断しない"]
        R3["モバイル幅を優先\n（300×250 or レスポンシブ）"]
    end

    LIST -.->|適用| RULE
    ARTICLE -.->|適用| RULE
```

---

## 7. レスポンシブ対応方針

```mermaid
graph TD
    subgraph BREAKPOINT["ブレークポイント設計"]
        SP["📱 モバイル\n〜 768px\n・1カラム\n・フルwidth\n・ハンバーガーメニュー"]
        TB["💻 タブレット\n769px 〜 1024px\n・1カラム維持\n・余白拡張"]
        PC["🖥️ デスクトップ\n1025px 〜\n・中央寄せ\n・最大幅 800px\n・サイドバーなし"]
    end

    SP --> TB --> PC
```

---

## 8. Chirpy テーマ カスタマイズ方針

```mermaid
graph TD
    BASE["Chirpy テーマ（ベース）"]

    subgraph CUSTOM["カスタマイズ箇所"]
        C1["_config.yml\n・サイト名・説明\n・lang: ja\n・timezone: Asia/Tokyo"]
        C2["_includes/\n・AdSense スニペット追加\n・AI生成明記バナー"]
        C3["assets/css/\n・フォント調整（CDN: Google Fonts）\n・カラー変数上書き"]
        C4["_layouts/\n・post.html に広告枠挿入\n・home.html にヒーロー記事追加"]
    end

    BASE --> C1
    BASE --> C2
    BASE --> C3
    BASE --> C4
```

---

## 9. 各ページ必須要素チェックリスト

```mermaid
graph TD
    subgraph COMMON["全ページ共通"]
        CM1["✅ AdSense スクリプト（head内）"]
        CM2["✅ title / description / og tags"]
        CM3["✅ グローバルナビ"]
        CM4["✅ フッター（プライバシー・お問い合わせリンク）"]
        CM5["✅ AI生成コンテンツ明記"]
    end

    subgraph ARTICLE_REQ["記事ページのみ"]
        AR1["✅ AdSense 枠① 記事上部"]
        AR2["✅ AdSense 枠② 記事下部"]
        AR3["✅ 前後作品ナビゲーション"]
        AR4["✅ タグリンク"]
        AR5["✅ 読了時間・文字数表示"]
    end

    subgraph LIST_REQ["一覧ページのみ"]
        LR1["✅ AdSense 枠② 一覧下部"]
        LR2["✅ 最新作品ヒーロー表示"]
        LR3["✅ 日付降順カード一覧"]
    end
```
