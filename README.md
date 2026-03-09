# DailyShortStorySite — Writer

毎日1本の短編小説を自動生成・品質確認・GitHub Pages に公開するシステムです。

---

## 目次

1. [概要](#概要)
2. [動作環境](#動作環境)
3. [セットアップ](#セットアップ)
4. [設定ファイル](#設定ファイル)
5. [手動実行](#手動実行)
6. [OpenClaw cron からの実行方法](#openclaw-cron-からの実行方法)
7. [パイプライン構成](#パイプライン構成)
8. [ディレクトリ構成](#ディレクトリ構成)
9. [トラブルシューティング](#トラブルシューティング)

---

## 概要

本システムは以下の4段階パイプラインで毎日1作品を生成・公開します。

| Stage | 内容 |
|---|---|
| plot | Codex CLI でプロット・タイトル候補を生成 |
| story | プロットから本文を生成（2,000〜5,000字） |
| review | 品質・類似度・禁止事項を検査（最大3回再試行） |
| publish | Markdown 保存 → Git commit → GitHub Pages 公開 |

---

## 動作環境

- Windows 11 + WSL2 (Ubuntu 想定)
- Python 3.11 以上
- Codex CLI（定額利用）
- OpenClaw（Windowsスケジューラ）
- Git / GitHub Pages

---

## セットアップ

### 1. WSL2 内でリポジトリをクローン

```bash
cd ~
git clone https://github.com/<your-org>/writer.git
cd writer
```

### 2. Python 仮想環境を作成

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 3. 設定ファイルを作成

```bash
cp config.json.example config.json
# config.json を編集してください（§設定ファイル参照）
```

### 4. 初期データを用意

`data/banned_terms.json` は手動で用意してください（空スタート禁止）。

```json
["差別語例", "暴力描写語例", "著名作家名"]
```

`data/stories_index.json` と `data/used_themes.json` は空配列で初期化できます。

```bash
echo "[]" > data/stories_index.json
echo "[]" > data/used_themes.json
```

---

## 設定ファイル

`config.json` の構造：

```json
{
  "publication_mode": "automatic",
  "max_review_attempts": 3,
  "similarity_threshold": 0.55
}
```

| フィールド | 型 | 説明 |
|---|---|---|
| `publication_mode` | string | `"automatic"` または `"manual_review"` |
| `max_review_attempts` | int | レビュー再試行上限（推奨: 3） |
| `similarity_threshold` | float | Jaccard 類似度閾値（推奨: 0.55） |

`publication_mode = "manual_review"` の場合、`pending/` フォルダに作品が置かれ、人手確認後に手動でパブリッシュします。

---

## 手動実行

```bash
# WSL2 ターミナル内で
source .venv/bin/activate
python -m writer.scripts.run_daily
```

### 手動パブリッシュ

レビュー待ち作品を手動公開する場合：

```bash
python -m writer.scripts.publish_story <slug> --date 2026-03-09
```

---

## OpenClaw cron からの実行方法

OpenClaw は Windows 上で動作するタスクスケジューラです。WSL2 経由で本システムを日次実行させます。

### 基本コマンド

OpenClaw の「コマンド」欄に以下を設定してください。

```
wsl bash -lc 'cd /path/to/writer && source .venv/bin/activate && python -m writer.scripts.run_daily >> logs/cron.log 2>&1'
```

> `/path/to/writer` は実際のプロジェクトパス（例: `/home/yourname/writer`）に置き換えてください。

### 実行タイミング

| 項目 | 推奨値 |
|---|---|
| 実行時刻 | 毎日 **05:00 JST** |
| 理由 | 日付単位管理しやすく、朝に新作を公開できる。障害時に手動復旧の余地がある。 |

### OpenClaw での設定手順

1. OpenClaw を起動し、**「新規タスク」** をクリック
2. **タスク名**: `DailyStoryWriter`
3. **トリガー**:
   - 種別: 毎日
   - 時刻: `05:00`
4. **コマンド** (1行):
   ```
   wsl bash -lc 'cd /home/yourname/writer && source .venv/bin/activate && python -m writer.scripts.run_daily >> logs/cron.log 2>&1'
   ```
5. **作業ディレクトリ**: 空のまま（コマンド内で `cd` するため）
6. **保存** してタスクを有効化

### ログ確認

実行ログは `logs/cron.log` と `logs/YYYY-MM-DD/run.log` に記録されます。

```bash
tail -f logs/cron.log
```

### エラー通知

失敗時は Windows トースト通知が発出されます（PowerShell の BurntToast モジュール使用）。

```powershell
# BurntToast が未インストールの場合
Install-Module -Name BurntToast -Force
```

### 再実行（失敗後）

パイプラインは `data/state.json` で進行状態を管理します。失敗した場合は途中から再開できます。

```bash
# 前回の失敗ステージから再開
wsl bash -lc 'cd /home/yourname/writer && source .venv/bin/activate && python -m writer.scripts.run_daily'
```

次回実行時に `state.json` を参照して自動的に再開ポイントを判定します。

### 注意事項

- **GitHub Token**: 環境変数 `GITHUB_TOKEN` を WSL2 の `.bashrc` に設定してください
  ```bash
  export GITHUB_TOKEN="ghp_xxxxxxxxxxxx"
  ```
- **初回テスト**: OpenClaw 登録前に WSL2 ターミナルで手動実行して動作確認を行ってください
- **ログローテーション**: `logs/` は定期的に確認し、古いログを削除してください

---

## パイプライン構成

```
RunDailyPipeline.run()
├── _execute_plot_stage()       ← PlotAgent + TitleSelectionAgent
├── _execute_story_stage()      ← StoryAgent
├── _execute_review_stage()     ← JaccardChecker + ReviewAgent（最大3回）
└── _execute_publish_stage()    ← PublishService → git push → 通知
```

`publication_mode = "manual_review"` の場合、`_execute_publish_stage()` の代わりに `pending/` への配置で停止します。

---

## ディレクトリ構成

```
writer/
  config.json            設定ファイル
  data/
    state.json           パイプライン実行状態
    stories_index.json   公開作品一覧
    used_themes.json     使用済みテーマ（直近90日）
    banned_terms.json    禁止語リスト
  stories/               作品Markdown正本
    2026/
      2026-03-09-*.md
  pending/               manual_review 用確認コピー
  site/
    _posts/              Jekyll 公開用（GitHub Pages）
  logs/
    cron.log             cron 実行ログ
    2026-03-09/
      run.log
      plot.json
      selected_title.json
      generation.txt
      review.json
  src/writer/            Pythonソースコード
  tests/                 テストコード
```

---

## トラブルシューティング

### WSL2 が起動しない

```powershell
# Windows PowerShell で
wsl --status
wsl --update
```

### Codex CLI が見つからない

```bash
which codex
# パスが通っていない場合は .bashrc に追加
export PATH="$HOME/.local/bin:$PATH"
```

### git push が失敗する

```bash
# SSH キーの確認
ssh -T git@github.com
# または GITHUB_TOKEN の確認
echo $GITHUB_TOKEN
```

### 当日分をスキップしたい

```bash
# state.json の result を "published" に手動更新するか削除
rm data/state.json
```

### レビューが毎回失敗する

`data/banned_terms.json` の内容を確認してください。生成本文に禁止語が含まれていないか確認し、必要に応じてプロンプト（`prompts/` ディレクトリ）を調整してください。
