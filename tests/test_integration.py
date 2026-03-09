"""Integration tests: multiple components working together with real I/O."""
from __future__ import annotations

import json
import os
import uuid
from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from writer.config import Config
from writer.state import StateManager, StateRecord
from writer.story_file import StoryFile
from writer.data.stories_index import StoriesIndex
from writer.data.used_themes import UsedThemes
from writer.models.plot_output import PlotOutput
from writer.models.story_output import StoryOutput
from writer.models.review_output import ReviewOutput
from writer.models.story_document import StoryDocument
from writer.models.story_front_matter import StoryFrontMatter
from writer.models.story_metadata import StoryMetadata
from writer.utils.jaccard_checker import JaccardChecker
from writer.agents.codex_cli import CodexCLI
from writer.agents.plot_agent import PlotAgent
from writer.agents.title_selection_agent import TitleSelectionAgent
from writer.agents.story_agent import StoryAgent
from writer.agents.review_agent import ReviewAgent
from writer.services.publish_service import PublishService
from writer.utils.git_operations import GitOperations
from writer.run_daily_pipeline import RunDailyPipeline
from writer.log_manager import LogManager
from writer.failure_handler import FailureHandler
from writer.data.banned_terms import BannedTerms
from writer.utils.windows_notifier import WindowsNotifier


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _make_story_document(
    slug: str = "test-slug",
    date_str: str = "2026-03-09",
) -> StoryDocument:
    fm = StoryFrontMatter(
        title="テスト短編",
        date=date_str,
        slug=slug,
        tags=["テスト"],
        genre="SF",
        theme="記憶と喪失",
        character_count=2500,
        reading_time_min=6,
        status="published",
        summary="テスト用のあらすじです。",
        ai_generated=True,
        review_score=85,
    )
    return StoryDocument(front_matter=fm, body="本文テキストがここに入ります。" * 50)


def _make_story_file(tmp_path) -> StoryFile:
    stories_dir = tmp_path / "stories"
    pending_dir = tmp_path / "pending"
    posts_dir = tmp_path / "site" / "_posts"
    for d in [stories_dir, pending_dir, posts_dir]:
        d.mkdir(parents=True)
    return StoryFile(
        stories_dir=str(stories_dir),
        pending_dir=str(pending_dir),
        posts_dir=str(posts_dir),
    )


# ---------------------------------------------------------------------------
# 1. StoryFile × StoriesIndex × StateManager 統合
#    - ファイル保存 → インデックス更新 → 状態更新が一貫して動作する
# ---------------------------------------------------------------------------

class TestStoryFileStoriesIndexStateIntegration:
    """StoryFile・StoriesIndex・StateManager の結合試験。"""

    def test_save_and_index_update_then_state_reflects_publish(
        self, tmp_path
    ) -> None:
        story_file = _make_story_file(tmp_path)
        index_path = tmp_path / "stories_index.json"
        index_path.write_text("[]")
        state_path = tmp_path / "state.json"

        stories_index = StoriesIndex(str(index_path))
        state_manager = StateManager(str(state_path))

        doc = _make_story_document()

        # (1) 正本保存
        saved_path = story_file.save_master(doc)
        assert os.path.isfile(saved_path)

        # (2) インデックス更新
        entry = doc.to_index_entry()
        stories_index.atomic_update(entry)

        # (3) State に published を記録
        state_record = StateRecord(
            run_date="2026-03-09",
            job_id=str(uuid.uuid4()),
            stage="publish",
            result="published",
            slug=doc.front_matter.slug,
            attempts={},
            artifacts={"story": saved_path},
            published_commit="abc1234",
        )
        state_manager.save(state_record)

        # 検証: インデックスに作品が存在する
        loaded_entries = stories_index.load()
        assert any(e.slug == "test-slug" for e in loaded_entries)

        # 検証: state が published を記録している
        loaded_state = state_manager.load()
        assert loaded_state.result == "published"
        assert loaded_state.slug == "test-slug"

    def test_is_today_done_returns_true_after_published_state(
        self, tmp_path
    ) -> None:
        state_path = tmp_path / "state.json"
        state_manager = StateManager(str(state_path))
        run_date = date.today().isoformat()

        record = StateRecord(
            run_date=run_date,
            job_id="test-job",
            stage="publish",
            result="published",
            slug="my-slug",
            attempts={},
            artifacts={},
            published_commit="dead1234",
        )
        state_manager.save(record)

        assert state_manager.is_today_done(run_date) is True

    def test_is_today_done_returns_false_for_different_date(
        self, tmp_path
    ) -> None:
        state_path = tmp_path / "state.json"
        state_manager = StateManager(str(state_path))

        record = StateRecord(
            run_date="2026-03-08",
            job_id="old-job",
            stage="publish",
            result="published",
            slug="old-slug",
            attempts={},
            artifacts={},
            published_commit="abc",
        )
        state_manager.save(record)

        assert state_manager.is_today_done("2026-03-09") is False


# ---------------------------------------------------------------------------
# 2. StoryDocument round-trip
#    - from_outputs で生成 → save_master → load_master → データ一致
# ---------------------------------------------------------------------------

class TestStoryDocumentRoundTrip:
    """StoryDocument の生成・保存・読み込みの結合試験。"""

    def test_from_outputs_save_load_roundtrip(self, tmp_path) -> None:
        story_file = _make_story_file(tmp_path)

        plot = PlotOutput(
            title_candidates=["タイトルA", "タイトルB", "タイトルC"],
            plot="主人公は孤独な研究者で…",
            characters=[{"name": "田中", "role": "protagonist"}],
            theme="孤独と繋がり",
            setting="近未来の東京",
            ending_type="余韻系",
            reading_impression="静かな余韻",
        )
        story = StoryOutput(
            title="眠れない夜に",
            body="夜が深くなるにつれて…" * 100,
            character_count=2800,
            reading_time_min=7,
            summary="孤独な研究者がAIと対話する物語。",
            tags=["SF", "日常"],
        )
        review = ReviewOutput(
            passed=True,
            scores={"originality": 88, "readability": 82, "consistency": 90, "hook": 80, "ending": 85, "overall": 85},
            issues=[],
            adsense_risk=False,
            rewrite_instruction=None,
        )

        doc = StoryDocument.from_outputs(
            plot=plot, story=story, review=review,
            slug="nemurenai-yoru", date="2026-03-09",
        )

        # 保存
        path = story_file.save_master(doc)
        assert os.path.isfile(path)

        # 読み込み
        loaded = story_file.load_master("nemurenai-yoru", "2026-03-09")
        assert isinstance(loaded, StoryDocument)
        assert loaded.front_matter.slug == "nemurenai-yoru"
        assert loaded.front_matter.title == "眠れない夜に"
        assert loaded.front_matter.theme == "孤独と繋がり"
        assert loaded.front_matter.review_score == 85
        assert "夜が深くなるにつれて" in loaded.body

    def test_to_index_entry_after_from_outputs(self, tmp_path) -> None:
        plot = PlotOutput(
            title_candidates=["A", "B", "C"],
            plot="プロット",
            characters=[],
            theme="テーマ",
            setting="舞台",
            ending_type="open",
            reading_impression="余韻",
        )
        story = StoryOutput(
            title="冬の朝",
            body="冬の朝に…" * 100,
            character_count=2200,
            reading_time_min=5,
            summary="冬の朝の静けさを描いた作品。",
            tags=["日常"],
        )
        review = ReviewOutput(
            passed=True,
            scores={"overall": 82},
            issues=[],
            adsense_risk=False,
            rewrite_instruction=None,
        )

        doc = StoryDocument.from_outputs(
            plot=plot, story=story, review=review,
            slug="fuyu-no-asa", date="2026-03-09",
        )
        entry = doc.to_index_entry()

        assert isinstance(entry, StoryMetadata)
        assert entry.slug == "fuyu-no-asa"
        assert entry.title == "冬の朝"
        assert entry.summary == "冬の朝の静けさを描いた作品。"
        assert entry.review_score == 82


# ---------------------------------------------------------------------------
# 3. PublishService 統合（実ファイル I/O + mock Git/State）
#    - sync_to_posts → atomic_update → git → state の順序と副作用を確認
# ---------------------------------------------------------------------------

class TestPublishServiceIntegration:
    """PublishService の結合試験（Git・State はモック）。"""

    @pytest.fixture
    def setup(self, tmp_path):
        story_file = _make_story_file(tmp_path)
        index_path = tmp_path / "stories_index.json"
        index_path.write_text("[]")
        stories_index = StoriesIndex(str(index_path))

        mock_git = MagicMock(spec=GitOperations)
        mock_git.add_all.return_value = None
        mock_git.commit.return_value = "deadbeef"
        mock_git.push.return_value = True

        state_path = tmp_path / "state.json"
        state_manager = StateManager(str(state_path))
        init_record = StateRecord(
            run_date="2026-03-09",
            job_id="init",
            stage="publish",
            result="in_progress",
            slug="nemurenai-yoru",
            attempts={},
            artifacts={},
            published_commit=None,
        )
        state_manager.save(init_record)

        doc = _make_story_document(slug="nemurenai-yoru", date_str="2026-03-09")
        story_file.save_master(doc)

        svc = PublishService(
            story_file=story_file,
            stories_index=stories_index,
            git=mock_git,
            state_manager=state_manager,
        )
        return svc, story_file, stories_index, state_manager, mock_git

    def test_run_from_master_creates_posts_file(self, setup, tmp_path) -> None:
        svc, story_file, stories_index, state_manager, mock_git = setup
        svc.run_from_master("nemurenai-yoru", "2026-03-09")

        posts_files = os.listdir(story_file.posts_dir)
        assert len(posts_files) == 1
        assert "nemurenai-yoru" in posts_files[0]

    def test_run_from_master_updates_index(self, setup) -> None:
        svc, story_file, stories_index, state_manager, mock_git = setup
        svc.run_from_master("nemurenai-yoru", "2026-03-09")

        entries = stories_index.load()
        assert any(e.slug == "nemurenai-yoru" for e in entries)

    def test_run_from_master_calls_git_in_order(self, setup) -> None:
        svc, story_file, stories_index, state_manager, mock_git = setup
        call_order = []
        mock_git.add_all.side_effect = lambda: call_order.append("add")
        mock_git.commit.side_effect = lambda msg: call_order.append("commit") or "abc"
        mock_git.push.side_effect = lambda: call_order.append("push") or True

        svc.run_from_master("nemurenai-yoru", "2026-03-09")

        assert call_order == ["add", "commit", "push"]

    def test_run_from_master_marks_state_published(self, setup) -> None:
        svc, story_file, stories_index, state_manager, mock_git = setup
        svc.run_from_master("nemurenai-yoru", "2026-03-09")

        state = state_manager.load()
        assert state.result == "published"
        assert state.published_commit == "deadbeef"

    def test_run_from_master_git_push_failure_does_not_mark_published(
        self, setup
    ) -> None:
        svc, story_file, stories_index, state_manager, mock_git = setup
        mock_git.push.side_effect = RuntimeError("Push failed")

        with pytest.raises(RuntimeError, match="Push failed"):
            svc.run_from_master("nemurenai-yoru", "2026-03-09")

        # state.json は push 前に published を更新してはいけない
        state = state_manager.load()
        assert state.result != "published"


# ---------------------------------------------------------------------------
# 4. JaccardChecker → ReviewAgent 入力連携
#    - Jaccard の結果が ReviewAgent に正しく渡り、is_duplicate 時に失敗する
# ---------------------------------------------------------------------------

class TestJaccardReviewIntegration:
    """JaccardChecker と ReviewAgent の結合試験。"""

    def _make_recent_stories(self, n: int = 5) -> list[StoryMetadata]:
        return [
            StoryMetadata(
                date=f"2026-02-{i + 1:02d}",
                slug=f"story-{i}",
                title=f"過去作品タイトル {i}",
                summary=f"過去作品のあらすじ {i} です。",
                tags=["テスト"],
                character_count=2000,
                reading_time_min=5,
                review_score=80,
            )
            for i in range(n)
        ]

    def test_jaccard_duplicate_causes_review_failure(self) -> None:
        checker = JaccardChecker(threshold=0.55)
        recent = self._make_recent_stories()

        # 既存タイトルと全く同じ候補
        jaccard_result = checker.compare(
            candidate_title="過去作品タイトル 0",
            candidate_summary="過去作品のあらすじ 0 です。",
            recent_30=recent,
        )

        assert jaccard_result["is_duplicate"] is True

        # ReviewAgent にこの結果を渡すと即失敗を返す
        mock_codex = MagicMock(spec=CodexCLI)
        agent = ReviewAgent(codex=mock_codex)
        story = StoryOutput(
            title="過去作品タイトル 0",
            body="本文" * 100,
            character_count=2000,
            reading_time_min=5,
            summary="過去作品のあらすじ 0 です。",
            tags=[],
        )

        review = agent.review(
            story=story,
            banned_terms=[],
            recent_30=recent,
            jaccard_result=jaccard_result,
        )
        assert review.passed is False
        # Codex は呼ばれない（Jaccard で即失敗）
        mock_codex.run.assert_not_called()

    def test_jaccard_no_duplicate_proceeds_to_llm_review(self) -> None:
        checker = JaccardChecker(threshold=0.55)
        recent = self._make_recent_stories()

        # 全く別のタイトル・要約
        jaccard_result = checker.compare(
            candidate_title="全く新しい宇宙の物語",
            candidate_summary="宇宙人と地球人が友情を築く物語。",
            recent_30=recent,
        )
        assert jaccard_result["is_duplicate"] is False

        # ReviewAgent は Codex を呼んでレビューを実行する
        mock_codex = MagicMock(spec=CodexCLI)
        mock_codex.run.return_value = json.dumps({
            "passed": True,
            "scores": {"originality": 85, "readability": 80, "consistency": 88, "hook": 78, "ending": 82, "overall": 83},
            "issues": [],
            "adsense_risk": False,
            "rewrite_instruction": None,
        })
        agent = ReviewAgent(codex=mock_codex)
        story = StoryOutput(
            title="全く新しい宇宙の物語",
            body="宇宙の果てで…" * 100,
            character_count=2500,
            reading_time_min=6,
            summary="宇宙人と地球人が友情を築く物語。",
            tags=["SF"],
        )

        review = agent.review(
            story=story,
            banned_terms=[],
            recent_30=recent,
            jaccard_result=jaccard_result,
        )
        assert review.passed is True
        mock_codex.run.assert_called_once()

    def test_jaccard_threshold_boundary(self) -> None:
        checker = JaccardChecker(threshold=0.55)
        recent = [
            StoryMetadata(
                date="2026-03-01",
                slug="base",
                title="猫が窓辺に座る話",
                summary="猫が窓辺に座って外を眺める短編。",
                tags=[],
                character_count=2000,
                reading_time_min=5,
                review_score=80,
            )
        ]

        # 全く同じ → 類似度 1.0（閾値超え）
        result_same = checker.compare("猫が窓辺に座る話", "猫が窓辺に座って外を眺める短編。", recent)
        assert result_same["is_duplicate"] is True

        # 全く違う → 類似度低（閾値以下）
        result_diff = checker.compare("宇宙で見た流れ星", "銀河の果てで星を見つめた夜の記憶。", recent)
        assert result_diff["is_duplicate"] is False


# ---------------------------------------------------------------------------
# 5. UsedThemes × StoriesIndex 公開後テーマ追跡
#    - 公開後にテーマを追加し、90日フィルタと連携することを確認
# ---------------------------------------------------------------------------

class TestUsedThemesStoriesIndexIntegration:
    """UsedThemes と StoriesIndex の公開後連携試験。"""

    def test_publish_updates_both_index_and_used_themes(self, tmp_path) -> None:
        index_path = tmp_path / "stories_index.json"
        index_path.write_text("[]")
        themes_path = tmp_path / "used_themes.json"
        themes_path.write_text("[]")

        stories_index = StoriesIndex(str(index_path))
        used_themes = UsedThemes(str(themes_path))

        doc = _make_story_document()
        entry = doc.to_index_entry()

        # 公開: インデックス更新 + テーマ追記
        stories_index.atomic_update(entry)
        used_themes.add_published(doc.front_matter.theme, doc.front_matter.date)

        # インデックス確認
        entries = stories_index.load()
        assert len(entries) == 1
        assert entries[0].slug == "test-slug"

        # テーマ確認（90日以内なので返ってくる）
        recent_themes = used_themes.get_recent_90days()
        assert "記憶と喪失" in recent_themes

    def test_used_themes_prevents_reuse_within_90_days(self, tmp_path) -> None:
        themes_path = tmp_path / "used_themes.json"
        themes_path.write_text("[]")
        used_themes = UsedThemes(str(themes_path))

        today = date.today().isoformat()
        used_themes.add_published("孤独と繋がり", today)
        used_themes.add_published("記憶と喪失", today)

        recent = used_themes.get_recent_90days()
        assert "孤独と繋がり" in recent
        assert "記憶と喪失" in recent
        # PlotAgent はこのリストを参照してテーマの重複を避ける

    def test_stories_index_get_recent_feeds_jaccard(self, tmp_path) -> None:
        index_path = tmp_path / "stories_index.json"
        index_path.write_text("[]")
        stories_index = StoriesIndex(str(index_path))
        checker = JaccardChecker(threshold=0.55)

        # 過去作品を5本登録
        for i in range(5):
            entry = StoryMetadata(
                date=f"2026-02-{i + 1:02d}",
                slug=f"past-story-{i}",
                title=f"過去作 {i}",
                summary=f"あらすじ {i}",
                tags=[],
                character_count=2000,
                reading_time_min=5,
                review_score=80,
            )
            stories_index.atomic_update(entry)

        recent_30 = stories_index.get_recent(30)
        assert len(recent_30) == 5

        # JaccardChecker に直接渡して機能することを確認
        result = checker.compare("完全新作タイトル", "新しいあらすじです。", recent_30)
        assert isinstance(result["is_duplicate"], bool)
        assert isinstance(result["max_title_similarity"], float)


# ---------------------------------------------------------------------------
# 6. Pipeline 状態遷移（state.json への書き込み確認）
#    - run() 中に state.json が正しく更新されることを確認
# ---------------------------------------------------------------------------

class TestPipelineStateTransitionIntegration:
    """Pipeline の state.json 更新を実ファイルで確認する結合試験。"""

    def _make_pipeline(self, tmp_path, publication_mode: str = "automatic"):
        state_path = tmp_path / "state.json"
        config = Config(
            publication_mode=publication_mode,
            max_review_attempts=3,
            similarity_threshold=0.55,
        )
        state_manager = StateManager(str(state_path))
        # 初期 state を作成
        init_record = StateRecord(
            run_date="2026-03-08",  # 前日分（今日とは異なる日付）
            job_id="prev-job",
            stage="publish",
            result="published",
            slug="yesterday-story",
            attempts={},
            artifacts={},
            published_commit="abc123",
        )
        state_manager.save(init_record)

        mock_plot_agent = MagicMock(spec=PlotAgent)
        mock_plot_agent.generate.return_value = PlotOutput(
            title_candidates=["A", "B", "C"],
            plot="プロット",
            characters=[],
            theme="テーマ",
            setting="舞台",
            ending_type="open",
            reading_impression="余韻",
        )

        mock_title_agent = MagicMock(spec=TitleSelectionAgent)
        from writer.models.title_selection_output import TitleSelectionOutput
        mock_title_agent.select.return_value = TitleSelectionOutput(
            selected_title="選ばれたタイトル",
            reason="理由",
            scores={"A": 90, "B": 80, "C": 70},
        )

        mock_story_agent = MagicMock(spec=StoryAgent)
        mock_story_agent.generate.return_value = StoryOutput(
            title="選ばれたタイトル",
            body="本文" * 200,
            character_count=2500,
            reading_time_min=6,
            summary="テスト用のあらすじです。",
            tags=["テスト"],
        )

        mock_review_agent = MagicMock(spec=ReviewAgent)
        mock_review_agent.review.return_value = ReviewOutput(
            passed=True,
            scores={"originality": 85, "readability": 80, "consistency": 88, "hook": 78, "ending": 82, "overall": 83},
            issues=[],
            adsense_risk=False,
            rewrite_instruction=None,
        )

        index_path = tmp_path / "stories_index.json"
        index_path.write_text("[]")
        themes_path = tmp_path / "used_themes.json"
        themes_path.write_text("[]")
        banned_path = tmp_path / "banned_terms.json"
        banned_path.write_text('["禁止語"]')

        story_file_obj = _make_story_file(tmp_path)

        mock_git = MagicMock(spec=GitOperations)
        mock_git.add_all.return_value = None
        mock_git.commit.return_value = "newcommit123"
        mock_git.push.return_value = True

        publish_service = PublishService(
            story_file=story_file_obj,
            stories_index=StoriesIndex(str(index_path)),
            git=mock_git,
            state_manager=state_manager,
        )

        mock_banned_terms = MagicMock(spec=BannedTerms)
        mock_banned_terms.load.return_value = ["禁止語"]

        mock_stories_index = MagicMock(spec=StoriesIndex)
        mock_stories_index.get_recent.return_value = []

        mock_used_themes = MagicMock(spec=UsedThemes)
        mock_used_themes.get_recent_90days.return_value = []

        pipeline = RunDailyPipeline(
            config=config,
            state_manager=state_manager,
            log_manager=MagicMock(spec=LogManager),
            failure_handler=MagicMock(spec=FailureHandler),
            plot_agent=mock_plot_agent,
            title_agent=mock_title_agent,
            story_agent=mock_story_agent,
            review_agent=mock_review_agent,
            stories_index=mock_stories_index,
            used_themes=mock_used_themes,
            banned_terms=mock_banned_terms,
            story_file=story_file_obj,
            jaccard_checker=JaccardChecker(threshold=0.55),
            publish_service=publish_service,
            notifier=MagicMock(spec=WindowsNotifier),
        )
        return pipeline, state_manager

    def test_run_completes_and_state_is_published(self, tmp_path) -> None:
        pipeline, state_manager = self._make_pipeline(tmp_path)
        # story_agent が返す StoryOutput の date と合わせて 2026-03-09 で固定
        pipeline._current_date = "2026-03-09"

        pipeline.run()

        state = state_manager.load()
        assert state.result == "published"
        assert state.published_commit == "newcommit123"

    def test_run_skips_if_today_already_published(self, tmp_path) -> None:
        pipeline, state_manager = self._make_pipeline(tmp_path)
        today = date.today().isoformat()
        pipeline._current_date = today

        # 当日分をすでに published に設定
        record = StateRecord(
            run_date=today,
            job_id="done-job",
            stage="publish",
            result="published",
            slug="done-slug",
            attempts={},
            artifacts={},
            published_commit="done123",
        )
        state_manager.save(record)

        pipeline.run()

        # plot_agent は呼ばれない（スキップされた）
        pipeline.plot_agent.generate.assert_not_called()

    def test_resume_from_story_skips_plot(self, tmp_path) -> None:
        pipeline, state_manager = self._make_pipeline(tmp_path)

        with (
            patch.object(pipeline, "_execute_plot_stage") as mock_plot,
            patch.object(pipeline, "_execute_story_stage") as mock_story,
            patch.object(pipeline, "_execute_review_stage") as mock_review,
            patch.object(pipeline, "_execute_publish_stage") as mock_publish,
        ):
            pipeline.resume_from_stage("story")
            mock_plot.assert_not_called()
            mock_story.assert_called_once()
            mock_review.assert_called_once()
            mock_publish.assert_called_once()


# ---------------------------------------------------------------------------
# 7. フルパイプライン統合試験（Codex CLI のみ mock、ファイル I/O は実物）
#    - 実際のファイルシステムで全 4 ステージを実行し副作用を検証
# ---------------------------------------------------------------------------

class TestFullPipelineIntegration:
    """Codex CLI をモックにして全 4 ステージを実際のファイルで実行する総合試験。"""

    PLOT_JSON = json.dumps({
        "title_candidates": ["月光の詩", "静かな夜明け", "消えた記憶"],
        "plot": "主人公の詩人が記憶を失い、自分の書いた詩から過去を取り戻す物語。",
        "characters": [{"name": "村上詩織", "role": "protagonist", "attribute": "詩人"}],
        "theme": "記憶と詩",
        "setting": "東京・下北沢",
        "ending_type": "余韻系",
        "reading_impression": "静かな感動",
    })

    TITLE_JSON = json.dumps({
        "selected_title": "月光の詩",
        "reason": "最も感情的な共鳴を持つタイトル。",
        "scores": {"月光の詩": 90, "静かな夜明け": 78, "消えた記憶": 72},
    })

    STORY_JSON = json.dumps({
        "title": "月光の詩",
        "body": "村上詩織が古いノートを開いたのは、深夜のことだった。" * 60,
        "character_count": 2640,
        "reading_time_min": 6,
        "summary": "記憶を失った詩人が自作の詩から過去を取り戻す物語。",
        "tags": ["詩", "記憶", "日常"],
    })

    REVIEW_JSON = json.dumps({
        "passed": True,
        "scores": {
            "originality": 88,
            "readability": 82,
            "consistency": 90,
            "hook": 80,
            "ending": 85,
            "overall": 85,
        },
        "issues": [],
        "adsense_risk": False,
        "rewrite_instruction": None,
    })

    def _build_full_pipeline(self, tmp_path):
        """Codex CLI だけモックにし、それ以外は実オブジェクトで構築。"""
        # 設定
        config = Config(
            publication_mode="automatic",
            max_review_attempts=3,
            similarity_threshold=0.55,
        )

        # ファイルパス
        state_path = tmp_path / "state.json"
        index_path = tmp_path / "stories_index.json"
        themes_path = tmp_path / "used_themes.json"
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()

        # 初期データ
        index_path.write_text("[]")
        themes_path.write_text("[]")

        # state.json を初期化（前日分が完了した状態から開始）
        import uuid as _uuid
        state_path.write_text(json.dumps({
            "run_date": "2026-03-08",
            "job_id": str(_uuid.uuid4()),
            "stage": "publish",
            "result": "published",
            "slug": "prev-story",
            "attempts": {},
            "artifacts": {},
            "published_commit": "prev123",
        }))

        # 実際のオブジェクト
        state_manager = StateManager(str(state_path))
        stories_index = StoriesIndex(str(index_path))
        used_themes = UsedThemes(str(themes_path))
        story_file = _make_story_file(tmp_path)
        jaccard_checker = JaccardChecker(threshold=0.55)

        # Codex CLI をモック（JSON を順番に返す）
        codex_responses = [
            self.PLOT_JSON,    # PlotAgent.generate()
            self.TITLE_JSON,   # TitleSelectionAgent.select()
            self.STORY_JSON,   # StoryAgent.generate()
            self.REVIEW_JSON,  # ReviewAgent.review()
        ]
        mock_codex = MagicMock(spec=CodexCLI)
        mock_codex.run.side_effect = codex_responses

        plot_agent = PlotAgent(codex=mock_codex)
        title_agent = TitleSelectionAgent(codex=mock_codex)
        story_agent = StoryAgent(codex=mock_codex)
        review_agent = ReviewAgent(codex=mock_codex)

        # BannedTerms は空リストで
        mock_banned_terms = MagicMock(spec=BannedTerms)
        mock_banned_terms.load.return_value = []

        # Git は push まで mock（GitHub への接続は不要）
        mock_git = MagicMock(spec=GitOperations)
        mock_git.add_all.return_value = None
        mock_git.commit.return_value = "full_commit_abc123"
        mock_git.push.return_value = True

        publish_service = PublishService(
            story_file=story_file,
            stories_index=stories_index,
            git=mock_git,
            state_manager=state_manager,
        )

        pipeline = RunDailyPipeline(
            config=config,
            state_manager=state_manager,
            log_manager=MagicMock(spec=LogManager),
            failure_handler=MagicMock(spec=FailureHandler),
            plot_agent=plot_agent,
            title_agent=title_agent,
            story_agent=story_agent,
            review_agent=review_agent,
            stories_index=stories_index,
            used_themes=used_themes,
            banned_terms=mock_banned_terms,
            story_file=story_file,
            jaccard_checker=jaccard_checker,
            publish_service=publish_service,
            notifier=MagicMock(spec=WindowsNotifier),
        )
        return pipeline, state_manager, stories_index, story_file

    def test_full_pipeline_executes_all_stages(self, tmp_path) -> None:
        pipeline, state_manager, stories_index, story_file = self._build_full_pipeline(tmp_path)
        # Codex が返す STORY_JSON の date フィールドと合わせる
        pipeline._current_date = "2026-03-09"

        # state.json がない状態（初回実行）でパイプラインを実行
        pipeline.run()

        # state.json が published になっている
        state = state_manager.load()
        assert state.result == "published"
        assert state.published_commit == "full_commit_abc123"

    def test_full_pipeline_creates_posts_file(self, tmp_path) -> None:
        pipeline, state_manager, stories_index, story_file = self._build_full_pipeline(tmp_path)
        pipeline._current_date = "2026-03-09"
        pipeline.run()

        # site/_posts/ に Markdown が生成されている
        posts_files = os.listdir(story_file.posts_dir)
        assert len(posts_files) == 1

    def test_full_pipeline_updates_stories_index(self, tmp_path) -> None:
        pipeline, state_manager, stories_index, story_file = self._build_full_pipeline(tmp_path)
        pipeline._current_date = "2026-03-09"
        pipeline.run()

        # stories_index.json に作品が追加されている
        entries = stories_index.load()
        assert len(entries) == 1
        assert entries[0].title == "月光の詩"

    def test_full_pipeline_codex_called_four_times(self, tmp_path) -> None:
        """plot・title・story・review の各フェーズで Codex CLI が計4回呼ばれる。"""
        pipeline, state_manager, stories_index, story_file = self._build_full_pipeline(tmp_path)
        pipeline._current_date = "2026-03-09"
        pipeline.run()

        # PlotAgent.generate → TitleAgent.select → StoryAgent.generate → ReviewAgent.review
        assert pipeline.plot_agent.codex.run.call_count == 4

    def test_full_pipeline_review_passes_on_first_attempt(self, tmp_path) -> None:
        """レビュー合格時は再生成が発生しない。"""
        pipeline, state_manager, stories_index, story_file = self._build_full_pipeline(tmp_path)
        pipeline._current_date = "2026-03-09"
        pipeline.run()

        # Codex は plot(1) + title(1) + story(1) + review(1) = 計4回
        assert pipeline.story_agent.codex.run.call_count == 4
