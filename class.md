# クラス図

## 全体クラス図

```mermaid
classDiagram
    %% ─────────────────────────────────────────
    %% エントリポイント・オーケストレーター
    %% ─────────────────────────────────────────

    class RunDailyPipeline {
        -config: Config
        -state: StateManager
        -logger: LogManager
        -failure_handler: FailureHandler
        +run()
        +resume_from_stage(stage: str)
        -execute_plot_stage()
        -execute_story_stage()
        -execute_review_stage()
        -execute_publish_stage()
    }

    class PublishStoryScript {
        -config: Config
        -state: StateManager
        -logger: LogManager
        -failure_handler: FailureHandler
        -publish_service: PublishService
        +run()
    }

    class PublishService {
        -story_file: StoryFile
        -stories_index: StoriesIndex
        -git: GitOperations
        -state: StateManager
        -used_themes: UsedThemes
        +run_from_master(slug: str, date: str) str
        -load_publish_target(slug: str, date: str) StoryDocument
        -sync_posts(doc: StoryDocument)
        -update_index(doc: StoryDocument)
        -git_commit_push(slug: str, date: str) str
        -mark_published(commit_hash: str, theme: str, date: str)
    }
    note for PublishService "automatic / manual_review 共通\nsync_posts -> update_index -> git_commit_push -> mark_published"

    %% ─────────────────────────────────────────
    %% 設定・状態管理
    %% ─────────────────────────────────────────

    class Config {
        +publication_mode: str
        +max_review_attempts: int
        +similarity_threshold: float
        +load(path: str)$ Config
    }

    class StateManager {
        -path: str
        +load() StateRecord
        +save(record: StateRecord)
        +update(stage: str, result: str, **kwargs)
        +is_today_done(run_date: str) bool
        +get_resume_point() tuple~str,str~
    }

    class StateRecord {
        +run_date: str
        +job_id: str
        +stage: str
        +result: str
        +slug: str | null
        +attempts: dict
        +artifacts: dict
        +published_commit: str | null
    }

    %% stage enum: plot | story | review | publish
    %% result enum: in_progress | failed | pending_review | published

    %% ─────────────────────────────────────────
    %% AI エージェント
    %% ─────────────────────────────────────────

    class PlotAgent {
        -prompt_path: str
        -codex: CodexCLI
        +generate(stories_index: list, used_themes: list, banned_terms: list) PlotOutput
        -build_prompt(stories_index: list, used_themes: list, banned_terms: list) str
        -validate(raw: str) PlotOutput
    }

    class TitleSelectionAgent {
        -prompt_path: str
        -codex: CodexCLI
        +select(plot: PlotOutput, recent_titles: list) TitleSelectionOutput
        -build_prompt(plot: PlotOutput, recent_titles: list) str
        -validate(raw: str) TitleSelectionOutput
    }

    class StoryAgent {
        -prompt_path: str
        -codex: CodexCLI
        +generate(plot: PlotOutput, selected_title: str, rewrite_instruction: str | null) StoryOutput
        -build_prompt(plot: PlotOutput, selected_title: str, rewrite_instruction: str | null) str
        -validate(raw: str) StoryOutput
    }

    class ReviewAgent {
        -prompt_path: str
        -codex: CodexCLI
        -jaccard: JaccardChecker
        +review(story: StoryOutput, banned_terms: list, recent_30: list, jaccard_result: dict) ReviewOutput
        -build_prompt(story: StoryOutput, jaccard_result: dict, banned_terms: list, recent_30: list) str
        -validate(raw: str) ReviewOutput
    }

    class CodexCLI {
        -executable: str
        +run(prompt: str) str
    }

    %% ─────────────────────────────────────────
    %% エージェント出力 JSON モデル
    %% ─────────────────────────────────────────

    class PlotOutput {
        +title_candidates: list~str~
        +plot: str
        +characters: list~dict~
        +theme: str
        +setting: str
        +ending_type: str
        +reading_impression: str
    }

    class TitleSelectionOutput {
        +selected_title: str
        +reason: str
        +scores: dict~str,int~
    }

    class StoryOutput {
        +title: str
        +body: str
        +character_count: int
        +reading_time_min: int
        +summary: str
        +tags: list~str~
    }

    class ReviewOutput {
        +passed: bool
        +scores: dict~str,int~
        +issues: list~str~
        +adsense_risk: bool
        +rewrite_instruction: str | null
    }

    class StoryFrontMatter {
        +title: str
        +date: str
        +slug: str
        +tags: list~str~
        +genre: str
        +theme: str
        +character_count: int
        +reading_time_min: int
        +status: str
        +summary: str
        +ai_generated: bool
        +review_score: int
    }

    class StoryDocument {
        +front_matter: StoryFrontMatter
        +body: str
        +from_outputs(plot: PlotOutput, story: StoryOutput, review: ReviewOutput, slug: str, date: str)$ StoryDocument
        +to_index_entry() StoryMetadata
    }

    %% ─────────────────────────────────────────
    %% データストア
    %% ─────────────────────────────────────────

    class StoriesIndex {
        -path: str
        +load() list~StoryMetadata~
        +get_recent(n: int) list~StoryMetadata~
        +atomic_update(entry: StoryMetadata)
    }

    class StoryMetadata {
        +date: str
        +slug: str
        +title: str
        +summary: str
        +tags: list~str~
        +character_count: int
        +reading_time_min: int
        +review_score: int
    }

    class UsedThemes {
        -path: str
        +load() list~dict~
        +get_recent_90days() list~str~
        +add_published(theme: str, date: str)
    }
    note for UsedThemes "未公開作品では更新しない\npublished 後のみ追加"

    class BannedTerms {
        -path: str
        +load() list~str~
    }

    %% ─────────────────────────────────────────
    %% ファイル操作・障害処理
    %% ─────────────────────────────────────────

    class StoryFile {
        -stories_dir: str
        -pending_dir: str
        -posts_dir: str
        +save_master(doc: StoryDocument) str
        +load_master(slug: str, date: str) StoryDocument
        +verify(path: str) bool
        +copy_to_pending(doc: StoryDocument)
        +sync_to_posts(doc: StoryDocument)
        -build_markdown(doc: StoryDocument) str
        -parse_markdown(path: str) StoryDocument
    }

    class LogManager {
        -base_dir: str
        -run_date: str
        +save_run_log(message: str)
        +save_plot_json(plot: PlotOutput)
        +save_selected_title_json(title: TitleSelectionOutput)
        +save_generation_txt(story: StoryOutput)
        +save_review_json(review: ReviewOutput, attempt: int)
        +save_error(stage: str, error: Exception)
    }

    class FailureHandler {
        -state: StateManager
        -logger: LogManager
        -notifier: WindowsNotifier
        +handle(stage: str, error: Exception)
        +mark_failed(stage: str, **kwargs)
    }

    %% ─────────────────────────────────────────
    %% ユーティリティ
    %% ─────────────────────────────────────────

    class JaccardChecker {
        -threshold: float
        +char_ngrams(text: str, n: int) set~str~
        +jaccard(a: str, b: str) float
        +compare(candidate_title: str, candidate_summary: str, recent_30: list~StoryMetadata~) dict
    }

    class GitOperations {
        -repo_path: str
        +add_all()
        +commit(message: str) str
        +push() bool
        +get_last_commit_hash() str
    }

    class WindowsNotifier {
        +notify(title: str, message: str)
        -build_cmd(title: str, message: str) str
    }

    %% ─────────────────────────────────────────
    %% 関連
    %% ─────────────────────────────────────────

    RunDailyPipeline --> Config
    RunDailyPipeline --> StateManager
    RunDailyPipeline --> LogManager
    RunDailyPipeline --> FailureHandler
    RunDailyPipeline --> PlotAgent
    RunDailyPipeline --> TitleSelectionAgent
    RunDailyPipeline --> StoryAgent
    RunDailyPipeline --> ReviewAgent
    RunDailyPipeline --> StoryFile
    RunDailyPipeline --> StoriesIndex
    RunDailyPipeline --> PublishService
    RunDailyPipeline --> UsedThemes
    RunDailyPipeline --> BannedTerms

    PublishStoryScript --> Config
    PublishStoryScript --> StateManager
    PublishStoryScript --> LogManager
    PublishStoryScript --> FailureHandler
    PublishStoryScript --> PublishService

    PublishService --> StoryFile
    PublishService --> StoriesIndex
    PublishService --> GitOperations
    PublishService --> StateManager
    PublishService --> UsedThemes

    FailureHandler --> StateManager
    FailureHandler --> LogManager
    FailureHandler --> WindowsNotifier

    StateManager --> StateRecord
    StoriesIndex --> StoryMetadata
    StoryFile --> StoryDocument
    StoryDocument *-- StoryFrontMatter
    StoryDocument --> StoryMetadata

    PlotAgent --> PlotOutput
    PlotAgent --> CodexCLI
    TitleSelectionAgent --> TitleSelectionOutput
    TitleSelectionAgent --> CodexCLI
    StoryAgent --> StoryOutput
    StoryAgent --> CodexCLI
    ReviewAgent --> ReviewOutput
    ReviewAgent --> CodexCLI
    ReviewAgent --> JaccardChecker
```

---

## パイプライン処理フロー（automatic モード）

```mermaid
classDiagram
    direction LR

    class RunDailyPipeline {
        +run()
    }

    class PlotAgent {
        +generate() PlotOutput
    }

    class TitleSelectionAgent {
        +select() TitleSelectionOutput
    }

    class StoryAgent {
        +generate() StoryOutput
    }

    class ReviewAgent {
        +review() ReviewOutput
    }

    class StoryDocument {
        +from_outputs()
    }

    class StoryFile {
        +save_master()
        +verify()
    }

    class PublishService {
        +run_from_master()
    }

    class StoriesIndex {
        +atomic_update()
    }

    class GitOperations {
        +commit()
        +push()
    }

    class StateManager {
        +update()
    }

    RunDailyPipeline --> PlotAgent : PlotOutput
    PlotAgent --> TitleSelectionAgent : title_candidates / plot
    PlotAgent --> StoryAgent : plot
    TitleSelectionAgent --> StoryAgent : selected_title
    StoryAgent --> ReviewAgent : StoryOutput
    ReviewAgent --> StoryDocument : passed=true
    StoryDocument --> StoryFile : save_master()
    StoryFile --> PublishService : verified master
    PublishService --> StoriesIndex : atomic_update()
    PublishService --> GitOperations : commit() / push()
    PublishService --> StateManager : commit_hash -> published
```

---

## パイプライン処理フロー（manual_review モード）

```mermaid
classDiagram
    direction LR

    class RunDailyPipeline {
        +run()
    }

    class StoryFile {
        +save_master()
        +copy_to_pending()
        +load_master()
    }

    class StateManager {
        +update()
    }

    class PublishStoryScript {
        +run()
    }

    class PublishService {
        +run_from_master()
    }

    class StoriesIndex {
        +atomic_update()
    }

    class GitOperations {
        +commit()
        +push()
    }

    RunDailyPipeline --> StoryFile : save_master()
    StoryFile --> StateManager : stage=publish / pending_review
    StoryFile --> PublishStoryScript : master available
    PublishStoryScript --> StoryFile : load_master()
    PublishStoryScript --> PublishService : run_from_master(slug, date)
    PublishService --> StoriesIndex : atomic_update()
    PublishService --> GitOperations : commit() / push()
    PublishService --> StateManager : commit_hash -> published
```

---

## データモデル詳細

```mermaid
classDiagram
    class StateRecord {
        +run_date: str
        +job_id: str
        +stage: str
        +result: str
        +slug: str | null
        +attempts: dict
        +artifacts: dict
        +published_commit: str | null
    }
    note for StateRecord "stage: plot|story|review|publish\nresult: in_progress|failed|pending_review|published\nslug / published_commit は未確定時に null"

    class StoryFrontMatter {
        +title: str
        +date: str
        +slug: str
        +tags: list~str~
        +genre: str
        +theme: str
        +character_count: int
        +reading_time_min: int
        +status: str
        +summary: str
        +ai_generated: bool
        +review_score: int
    }
    note for StoryFrontMatter "stories/ 正本・pending/・site/_posts/ で共通利用する front matter"

    class StoryDocument {
        +front_matter: StoryFrontMatter
        +body: str
        +to_index_entry() StoryMetadata
    }
    note for StoryDocument "manual publish 時は stories/ 正本 Markdown から復元し\nPublishService に渡す"

    class StoryMetadata {
        +date: str
        +slug: str
        +title: str
        +summary: str
        +tags: list~str~
        +character_count: int
        +reading_time_min: int
        +review_score: int
    }
    note for StoryMetadata "stories_index.json の1エントリ\n日付降順で保持"

    class PlotOutput {
        +title_candidates: list~str~
        +plot: str
        +characters: list~dict~
        +theme: str
        +setting: str
        +ending_type: str
        +reading_impression: str
    }
    note for PlotOutput "Plot Agent -> Title Selection Agent -> Story Agent に渡る"

    class ReviewOutput {
        +passed: bool
        +scores: dict~str,int~
        +issues: list~str~
        +adsense_risk: bool
        +rewrite_instruction: str | null
    }
    note for ReviewOutput "adsense_risk=true -> passed=false 強制\nrewrite_instruction は合格時 null"

    StoryDocument *-- StoryFrontMatter
    StoryDocument --> StoryMetadata
```
