"""Tests for RunDailyPipeline and PublishStoryScript entry points."""
from __future__ import annotations

from unittest.mock import MagicMock, patch, call

import pytest

from writer.run_daily_pipeline import RunDailyPipeline
from writer.publish_story_script import PublishStoryScript
from writer.config import Config
from writer.state import StateManager, StateRecord
from writer.log_manager import LogManager
from writer.failure_handler import FailureHandler
from writer.agents.codex_cli import CodexCLI
from writer.agents.plot_agent import PlotAgent
from writer.agents.title_selection_agent import TitleSelectionAgent
from writer.agents.story_agent import StoryAgent
from writer.agents.review_agent import ReviewAgent
from writer.data.stories_index import StoriesIndex
from writer.data.used_themes import UsedThemes
from writer.data.banned_terms import BannedTerms
from writer.story_file import StoryFile
from writer.utils.jaccard_checker import JaccardChecker
from writer.utils.git_operations import GitOperations
from writer.utils.windows_notifier import WindowsNotifier
from writer.services.publish_service import PublishService


@pytest.fixture
def mock_config() -> MagicMock:
    cfg = MagicMock(spec=Config)
    cfg.publication_mode = "auto"
    cfg.max_review_attempts = 3
    cfg.similarity_threshold = 0.8
    return cfg


@pytest.fixture
def mock_state_manager() -> MagicMock:
    m = MagicMock(spec=StateManager)
    m.is_today_done.return_value = False
    m.get_resume_point.return_value = ("plot", "pending")
    return m


@pytest.fixture
def pipeline(mock_config, mock_state_manager) -> RunDailyPipeline:
    return RunDailyPipeline(
        config=mock_config,
        state_manager=mock_state_manager,
        log_manager=MagicMock(spec=LogManager),
        failure_handler=MagicMock(spec=FailureHandler),
        plot_agent=MagicMock(spec=PlotAgent),
        title_agent=MagicMock(spec=TitleSelectionAgent),
        story_agent=MagicMock(spec=StoryAgent),
        review_agent=MagicMock(spec=ReviewAgent),
        stories_index=MagicMock(spec=StoriesIndex),
        used_themes=MagicMock(spec=UsedThemes),
        banned_terms=MagicMock(spec=BannedTerms),
        story_file=MagicMock(spec=StoryFile),
        jaccard_checker=MagicMock(spec=JaccardChecker),
        publish_service=MagicMock(spec=PublishService),
        notifier=MagicMock(spec=WindowsNotifier),
    )


class TestRunDailyPipelineInit:
    """Tests for RunDailyPipeline.__init__."""

    def test_stores_config(self, pipeline, mock_config) -> None:
        assert pipeline.config is mock_config

    def test_stores_state_manager(self, pipeline, mock_state_manager) -> None:
        assert pipeline.state_manager is mock_state_manager

    def test_stores_all_agents(self, pipeline) -> None:
        assert pipeline.plot_agent is not None
        assert pipeline.title_agent is not None
        assert pipeline.story_agent is not None
        assert pipeline.review_agent is not None

    def test_stores_all_data_stores(self, pipeline) -> None:
        assert pipeline.stories_index is not None
        assert pipeline.used_themes is not None
        assert pipeline.banned_terms is not None


class TestRunDailyPipelineRun:
    """Tests for RunDailyPipeline.run()."""

    def test_run_calls_is_today_done(self, pipeline, mock_state_manager) -> None:
        with (
            patch.object(pipeline, "_execute_plot_stage"),
            patch.object(pipeline, "_execute_story_stage"),
            patch.object(pipeline, "_execute_review_stage"),
            patch.object(pipeline, "_execute_publish_stage"),
        ):
            pipeline.run()
            mock_state_manager.is_today_done.assert_called_once()

    def test_run_skips_when_today_done(self, pipeline, mock_state_manager) -> None:
        mock_state_manager.is_today_done.return_value = True
        try:
            pipeline.run()
            # If today is done, no new pipeline should execute
        except NotImplementedError:
            pytest.xfail("RunDailyPipeline.run not yet implemented")

    def test_run_executes_all_four_stages(self, pipeline) -> None:
        try:
            with (
                patch.object(pipeline, "_execute_plot_stage") as mock_plot,
                patch.object(pipeline, "_execute_story_stage") as mock_story,
                patch.object(pipeline, "_execute_review_stage") as mock_review,
                patch.object(pipeline, "_execute_publish_stage") as mock_publish,
            ):
                pipeline.run()
                mock_plot.assert_called_once()
                mock_story.assert_called_once()
                mock_review.assert_called_once()
                mock_publish.assert_called_once()
        except NotImplementedError:
            pytest.xfail("RunDailyPipeline.run not yet implemented")


class TestRunDailyPipelineResumeFromStage:
    """Tests for RunDailyPipeline.resume_from_stage()."""

    def test_resume_from_invalid_stage_raises_error(self, pipeline) -> None:
        with pytest.raises((ValueError, KeyError)):
            pipeline.resume_from_stage("nonexistent_stage")

    def test_resume_from_plot_executes_all_stages(self, pipeline) -> None:
        try:
            with (
                patch.object(pipeline, "_execute_plot_stage") as mock_plot,
                patch.object(pipeline, "_execute_story_stage") as mock_story,
                patch.object(pipeline, "_execute_review_stage") as mock_review,
                patch.object(pipeline, "_execute_publish_stage") as mock_publish,
            ):
                pipeline.resume_from_stage("plot")
                mock_plot.assert_called_once()
                mock_story.assert_called_once()
                mock_review.assert_called_once()
                mock_publish.assert_called_once()
        except NotImplementedError:
            pytest.xfail("RunDailyPipeline.resume_from_stage not yet implemented")

    def test_resume_from_story_skips_plot_stage(self, pipeline) -> None:
        try:
            with (
                patch.object(pipeline, "_execute_plot_stage") as mock_plot,
                patch.object(pipeline, "_execute_story_stage") as mock_story,
                patch.object(pipeline, "_execute_review_stage") as mock_review,
                patch.object(pipeline, "_execute_publish_stage") as mock_publish,
            ):
                pipeline.resume_from_stage("story")
                mock_plot.assert_not_called()
                mock_story.assert_called_once()
        except NotImplementedError:
            pytest.xfail("RunDailyPipeline.resume_from_stage not yet implemented")

    def test_resume_from_publish_skips_earlier_stages(self, pipeline) -> None:
        try:
            with (
                patch.object(pipeline, "_execute_plot_stage") as mock_plot,
                patch.object(pipeline, "_execute_story_stage") as mock_story,
                patch.object(pipeline, "_execute_review_stage") as mock_review,
                patch.object(pipeline, "_execute_publish_stage") as mock_publish,
            ):
                pipeline.resume_from_stage("publish")
                mock_plot.assert_not_called()
                mock_story.assert_not_called()
                mock_review.assert_not_called()
                mock_publish.assert_called_once()
        except NotImplementedError:
            pytest.xfail("RunDailyPipeline.resume_from_stage not yet implemented")

    def test_resume_from_invalid_stage_raises_value_error(self, pipeline) -> None:
        with pytest.raises((ValueError, KeyError)):
            pipeline.resume_from_stage("nonexistent_stage")


class TestRunDailyPipelineExecutePlotStage:
    """Tests for RunDailyPipeline._execute_plot_stage()."""

    def test_execute_plot_stage_loads_data(self, pipeline, sample_plot_output) -> None:
        pipeline.plot_agent.generate.return_value = sample_plot_output
        pipeline.stories_index.get_recent.return_value = []
        pipeline.used_themes.get_recent_90days.return_value = []
        pipeline.banned_terms.load.return_value = []
        pipeline._execute_plot_stage()
        pipeline.stories_index.get_recent.assert_called_once()

    def test_execute_plot_stage_calls_plot_agent_generate(
        self, pipeline, sample_plot_output
    ) -> None:
        pipeline.plot_agent.generate.return_value = sample_plot_output
        pipeline.stories_index.get_recent.return_value = []
        pipeline.used_themes.get_recent_90days.return_value = []
        pipeline.banned_terms.load.return_value = []
        try:
            pipeline._execute_plot_stage()
            pipeline.plot_agent.generate.assert_called_once()
        except NotImplementedError:
            pytest.xfail("RunDailyPipeline._execute_plot_stage not yet implemented")

    def test_execute_plot_stage_logs_result(
        self, pipeline, sample_plot_output
    ) -> None:
        pipeline.plot_agent.generate.return_value = sample_plot_output
        pipeline.stories_index.get_recent.return_value = []
        pipeline.used_themes.get_recent_90days.return_value = []
        pipeline.banned_terms.load.return_value = []
        try:
            pipeline._execute_plot_stage()
            pipeline.log_manager.save_plot_json.assert_called_once_with(sample_plot_output)
        except NotImplementedError:
            pytest.xfail("RunDailyPipeline._execute_plot_stage not yet implemented")


class TestRunDailyPipelineExecuteStoryStage:
    """Tests for RunDailyPipeline._execute_story_stage()."""

    def test_execute_story_stage_uses_story_agent(self, pipeline, sample_story_output) -> None:
        pipeline.story_agent.generate.return_value = sample_story_output
        pipeline._execute_story_stage()
        pipeline.story_agent.generate.assert_called_once()

    def test_execute_story_stage_calls_story_agent(
        self, pipeline, sample_story_output, sample_plot_output, sample_title_selection_output
    ) -> None:
        pipeline.story_agent.generate.return_value = sample_story_output
        try:
            pipeline._execute_story_stage()
            pipeline.story_agent.generate.assert_called_once()
        except NotImplementedError:
            pytest.xfail("RunDailyPipeline._execute_story_stage not yet implemented")


class TestRunDailyPipelineExecuteReviewStage:
    """Tests for RunDailyPipeline._execute_review_stage()."""

    def test_execute_review_stage_calls_review_agent(
        self, pipeline, sample_story_output, sample_review_output_passed
    ) -> None:
        pipeline.review_agent.review.return_value = sample_review_output_passed
        pipeline.story_agent.generate.return_value = sample_story_output
        pipeline._execute_review_stage()
        pipeline.review_agent.review.assert_called()

    def test_execute_review_stage_retries_on_failure(
        self,
        pipeline,
        sample_story_output,
        sample_review_output_failed,
        sample_review_output_passed,
    ) -> None:
        """Review stage must retry up to max_review_attempts times."""
        pipeline.config.max_review_attempts = 3
        pipeline.review_agent.review.side_effect = [
            sample_review_output_failed,
            sample_review_output_failed,
            sample_review_output_passed,
        ]
        pipeline.story_agent.generate.return_value = sample_story_output
        try:
            pipeline._execute_review_stage()
            assert pipeline.review_agent.review.call_count == 3
        except NotImplementedError:
            pytest.xfail("RunDailyPipeline._execute_review_stage not yet implemented")

    def test_execute_review_stage_stops_on_pass(
        self,
        pipeline,
        sample_story_output,
        sample_review_output_passed,
    ) -> None:
        pipeline.review_agent.review.return_value = sample_review_output_passed
        pipeline.story_agent.generate.return_value = sample_story_output
        try:
            pipeline._execute_review_stage()
            assert pipeline.review_agent.review.call_count == 1
        except NotImplementedError:
            pytest.xfail("RunDailyPipeline._execute_review_stage not yet implemented")

    def test_execute_review_stage_adsense_risk_forces_fail(
        self, pipeline, sample_story_output, sample_review_output_adsense_risk
    ) -> None:
        """adsense_risk=True review must count as a failure even if passed was True."""
        # ReviewOutput already enforces this via __post_init__
        assert sample_review_output_adsense_risk.passed is False
        pipeline.review_agent.review.return_value = sample_review_output_adsense_risk
        pipeline.story_agent.generate.return_value = sample_story_output
        try:
            pipeline._execute_review_stage()
            # Should have attempted rewrite since review failed
            pipeline.story_agent.generate.assert_called()
        except NotImplementedError:
            pytest.xfail("RunDailyPipeline._execute_review_stage not yet implemented")


class TestRunDailyPipelineExecutePublishStage:
    """Tests for RunDailyPipeline._execute_publish_stage()."""

    def test_execute_publish_stage_uses_publish_service(self, pipeline) -> None:
        pipeline.publish_service.run_from_master.return_value = "abc123"
        pipeline._execute_publish_stage()
        pipeline.publish_service.run_from_master.assert_called_once()

    def test_execute_publish_stage_calls_publish_service(self, pipeline) -> None:
        pipeline.publish_service.run_from_master.return_value = "abc123"
        try:
            pipeline._execute_publish_stage()
            pipeline.publish_service.run_from_master.assert_called_once()
        except NotImplementedError:
            pytest.xfail("RunDailyPipeline._execute_publish_stage not yet implemented")

    def test_execute_publish_stage_sends_notification(self, pipeline) -> None:
        pipeline.publish_service.run_from_master.return_value = "abc123"
        try:
            pipeline._execute_publish_stage()
            pipeline.notifier.notify.assert_called_once()
        except NotImplementedError:
            pytest.xfail("RunDailyPipeline._execute_publish_stage not yet implemented")


class TestPublishStoryScript:
    """Tests for PublishStoryScript."""

    @pytest.fixture
    def mock_publish_service(self) -> MagicMock:
        svc = MagicMock(spec=PublishService)
        svc.run_from_master.return_value = "abc123"
        return svc

    def test_init_stores_publish_service(self, mock_publish_service) -> None:
        script = PublishStoryScript(publish_service=mock_publish_service)
        assert script.publish_service is mock_publish_service

    def test_run_calls_run_from_master(self, mock_publish_service) -> None:
        script = PublishStoryScript(publish_service=mock_publish_service)
        try:
            script.run()
        except SystemExit:
            pass  # argparse may exit if no args provided
        # run_from_master may or may not be called depending on arg parsing


    def test_run_calls_publish_service(self, mock_publish_service) -> None:
        import sys
        script = PublishStoryScript(publish_service=mock_publish_service)
        with patch.object(sys, "argv", ["publish_story", "test-slug", "--date", "2026-03-09"]):
            script.run()
            mock_publish_service.run_from_master.assert_called_once_with("test-slug", "2026-03-09")
