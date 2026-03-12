from __future__ import annotations

from pathlib import Path

from writer.agents.codex_cli import CodexCLI
from writer.agents.plot_agent import PlotAgent
from writer.agents.review_agent import ReviewAgent
from writer.agents.story_agent import StoryAgent
from writer.agents.title_selection_agent import TitleSelectionAgent
from writer.config import Config
from writer.data.banned_terms import BannedTerms
from writer.data.stories_index import StoriesIndex
from writer.data.used_themes import UsedThemes
from writer.failure_handler import FailureHandler
from writer.log_manager import LogManager
from writer.run_daily_pipeline import RunDailyPipeline, _today_jst
from writer.services.publish_service import PublishService
from writer.state import StateManager
from writer.story_file import StoryFile
from writer.utils.git_operations import GitOperations
from writer.utils.jaccard_checker import JaccardChecker
from writer.utils.windows_notifier import WindowsNotifier


def _load_config(config_path: Path) -> Config:
    if config_path.exists():
        return Config.load(str(config_path))
    return Config(
        publication_mode="manual_review",
        max_review_attempts=3,
        similarity_threshold=0.55,
    )


def _ensure_json_array(path: Path) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("[]", encoding="utf-8")


def _ensure_state_file(state_path: Path, state_example_path: Path, run_date: str) -> None:
    if state_path.exists():
        return
    state_path.parent.mkdir(parents=True, exist_ok=True)
    if state_example_path.exists():
        state_path.write_text(state_example_path.read_text(encoding="utf-8"), encoding="utf-8")
        return

    # fallback default
    state_path.write_text(
        '{\n'
        f'  "run_date": "{run_date}",\n'
        '  "job_id": "",\n'
        '  "stage": "plot",\n'
        '  "result": "pending",\n'
        '  "slug": null,\n'
        '  "attempts": {},\n'
        '  "artifacts": {},\n'
        '  "published_commit": null\n'
        '}\n',
        encoding="utf-8",
    )


def build_runtime(
    project_root: str | Path | None = None,
) -> tuple[RunDailyPipeline, PublishService]:
    root = Path(project_root or Path.cwd()).resolve()
    run_date = _today_jst()

    config = _load_config(root / "config.json")
    notifier = WindowsNotifier()

    state_path = root / "data" / "state.json"
    state_example_path = root / "data" / "state.example.json"
    _ensure_state_file(state_path, state_example_path, run_date)

    state_manager = StateManager(str(state_path))
    log_manager = LogManager(str(root / "logs"), run_date)
    failure_handler = FailureHandler(state_manager, log_manager, notifier)

    stories_index_path = root / "data" / "stories_index.json"
    used_themes_path = root / "data" / "used_themes.json"
    _ensure_json_array(stories_index_path)
    _ensure_json_array(used_themes_path)

    stories_index = StoriesIndex(str(stories_index_path))
    used_themes = UsedThemes(str(used_themes_path))
    banned_terms = BannedTerms(str(root / "data" / "banned_terms.json"))
    story_file = StoryFile(
        stories_dir=str(root / "stories"),
        pending_dir=str(root / "pending"),
        posts_dir=str(root / "site" / "_posts"),
    )
    codex = CodexCLI(executable="codex")
    plot_agent = PlotAgent(codex)
    title_agent = TitleSelectionAgent(codex)
    story_agent = StoryAgent(codex)
    review_agent = ReviewAgent(codex)
    jaccard_checker = JaccardChecker(config.similarity_threshold)
    git = GitOperations(str(root))
    publish_service = PublishService(
        story_file=story_file,
        stories_index=stories_index,
        git=git,
        state_manager=state_manager,
        used_themes=used_themes,
    )

    pipeline = RunDailyPipeline(
        config=config,
        state_manager=state_manager,
        log_manager=log_manager,
        failure_handler=failure_handler,
        plot_agent=plot_agent,
        title_agent=title_agent,
        story_agent=story_agent,
        review_agent=review_agent,
        stories_index=stories_index,
        used_themes=used_themes,
        banned_terms=banned_terms,
        story_file=story_file,
        jaccard_checker=jaccard_checker,
        publish_service=publish_service,
        notifier=notifier,
    )
    return pipeline, publish_service
