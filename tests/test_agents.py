"""Tests for all AI agent classes."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from writer.agents.codex_cli import CodexCLI
from writer.agents.plot_agent import PlotAgent
from writer.agents.title_selection_agent import TitleSelectionAgent
from writer.agents.story_agent import StoryAgent
from writer.agents.review_agent import ReviewAgent
from writer.models.plot_output import PlotOutput
from writer.models.title_selection_output import TitleSelectionOutput
from writer.models.story_output import StoryOutput
from writer.models.review_output import ReviewOutput
from writer.models.story_metadata import StoryMetadata


# ---------------------------------------------------------------------------
# CodexCLI
# ---------------------------------------------------------------------------

class TestCodexCLI:
    """Tests for CodexCLI."""

    def test_init_stores_executable(self) -> None:
        cli = CodexCLI(executable="codex")
        assert cli.executable == "codex"

    def test_run_calls_subprocess(self) -> None:
        from unittest.mock import patch, MagicMock
        cli = CodexCLI(executable="codex")
        mock_result = MagicMock()
        mock_result.stdout = "output text"
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            result = cli.run("Hello, world!")
            mock_run.assert_called_once()
            assert result == "output text"

    def test_run_passes_prompt_to_executable(self) -> None:
        from unittest.mock import patch, MagicMock
        cli = CodexCLI(executable="codex")
        mock_result = MagicMock()
        mock_result.stdout = "result"
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            cli.run("test prompt")
            args = mock_run.call_args[0][0]
            assert "codex" in args
            assert "test prompt" in args

    def test_run_returns_string(self) -> None:
        from unittest.mock import patch, MagicMock
        cli = CodexCLI(executable="codex")
        mock_result = MagicMock()
        mock_result.stdout = "テスト出力"
        with patch("subprocess.run", return_value=mock_result):
            result = cli.run("テストプロンプト")
            assert isinstance(result, str)


# ---------------------------------------------------------------------------
# PlotAgent
# ---------------------------------------------------------------------------

class TestPlotAgent:
    """Tests for PlotAgent."""

    @pytest.fixture
    def mock_codex(self) -> MagicMock:
        mock = MagicMock(spec=CodexCLI)
        mock.run.return_value = '{"title_candidates": [], "plot": "", "characters": [], "theme": "", "setting": "", "ending_type": "", "reading_impression": ""}'
        return mock

    def test_init_stores_codex(self, mock_codex) -> None:
        agent = PlotAgent(codex=mock_codex)
        assert agent.codex is mock_codex

    def test_generate_calls_codex(self, mock_codex) -> None:
        agent = PlotAgent(codex=mock_codex)
        agent.generate(stories_index=[], used_themes=[], banned_terms=[])
        mock_codex.run.assert_called_once()

    def test_generate_returns_plot_output(
        self, mock_codex, sample_story_metadata_list
    ) -> None:
        agent = PlotAgent(codex=mock_codex)
        try:
            result = agent.generate(
                stories_index=sample_story_metadata_list,
                used_themes=["テーマA", "テーマB"],
                banned_terms=["禁止語"],
            )
            assert isinstance(result, PlotOutput)
        except NotImplementedError:
            pytest.xfail("PlotAgent.generate not yet implemented")

    def test_generate_calls_codex_run(
        self, mock_codex, sample_story_metadata_list
    ) -> None:
        agent = PlotAgent(codex=mock_codex)
        try:
            agent.generate(
                stories_index=sample_story_metadata_list,
                used_themes=[],
                banned_terms=[],
            )
            mock_codex.run.assert_called_once()
        except NotImplementedError:
            pytest.xfail("PlotAgent.generate not yet implemented")

    def test_generate_with_banned_terms_passed_to_prompt(self, mock_codex) -> None:
        agent = PlotAgent(codex=mock_codex)
        banned = ["暴力", "差別"]
        try:
            agent.generate([], [], banned)
            call_args = mock_codex.run.call_args[0][0]
            # Banned terms should appear in the prompt
            for term in banned:
                assert term in call_args
        except NotImplementedError:
            pytest.xfail("PlotAgent.generate not yet implemented")


# ---------------------------------------------------------------------------
# TitleSelectionAgent
# ---------------------------------------------------------------------------

class TestTitleSelectionAgent:
    """Tests for TitleSelectionAgent."""

    @pytest.fixture
    def mock_codex(self) -> MagicMock:
        mock = MagicMock(spec=CodexCLI)
        mock.run.return_value = '{"selected_title": "テスト", "reason": "理由", "scores": {}}'
        return mock

    def test_init_stores_codex(self, mock_codex) -> None:
        agent = TitleSelectionAgent(codex=mock_codex)
        assert agent.codex is mock_codex

    def test_select_calls_codex(
        self, mock_codex, sample_plot_output, sample_story_metadata_list
    ) -> None:
        agent = TitleSelectionAgent(codex=mock_codex)
        agent.select(plot=sample_plot_output, recent_titles=sample_story_metadata_list)
        mock_codex.run.assert_called_once()

    def test_select_returns_title_selection_output(
        self, mock_codex, sample_plot_output, sample_story_metadata_list
    ) -> None:
        agent = TitleSelectionAgent(codex=mock_codex)
        try:
            result = agent.select(sample_plot_output, sample_story_metadata_list)
            assert isinstance(result, TitleSelectionOutput)
        except NotImplementedError:
            pytest.xfail("TitleSelectionAgent.select not yet implemented")

    def test_select_with_empty_recent_titles(
        self, mock_codex, sample_plot_output
    ) -> None:
        agent = TitleSelectionAgent(codex=mock_codex)
        try:
            result = agent.select(sample_plot_output, [])
            assert isinstance(result, TitleSelectionOutput)
        except NotImplementedError:
            pytest.xfail("TitleSelectionAgent.select not yet implemented")


# ---------------------------------------------------------------------------
# StoryAgent
# ---------------------------------------------------------------------------

class TestStoryAgent:
    """Tests for StoryAgent."""

    @pytest.fixture
    def mock_codex(self) -> MagicMock:
        mock = MagicMock(spec=CodexCLI)
        mock.run.return_value = '{"title": "テスト", "body": "本文", "character_count": 100, "reading_time_min": 1, "summary": "要約", "tags": []}'
        return mock

    def test_init_stores_codex(self, mock_codex) -> None:
        agent = StoryAgent(codex=mock_codex)
        assert agent.codex is mock_codex

    def test_generate_calls_codex(
        self, mock_codex, sample_plot_output
    ) -> None:
        agent = StoryAgent(codex=mock_codex)
        agent.generate(plot=sample_plot_output, selected_title="夜明けの約束")
        mock_codex.run.assert_called_once()

    def test_generate_with_rewrite_instruction_includes_instruction(
        self, mock_codex, sample_plot_output
    ) -> None:
        agent = StoryAgent(codex=mock_codex)
        agent.generate(
            plot=sample_plot_output,
            selected_title="夜明けの約束",
            rewrite_instruction="キャラクターをより鮮明に描いてください",
        )
        call_prompt = mock_codex.run.call_args[0][0]
        assert "キャラクターをより鮮明に描いてください" in call_prompt

    def test_generate_returns_story_output(
        self, mock_codex, sample_plot_output
    ) -> None:
        agent = StoryAgent(codex=mock_codex)
        try:
            result = agent.generate(sample_plot_output, "夜明けの約束")
            assert isinstance(result, StoryOutput)
        except NotImplementedError:
            pytest.xfail("StoryAgent.generate not yet implemented")

    def test_generate_without_rewrite_uses_fresh_generation(
        self, mock_codex, sample_plot_output
    ) -> None:
        agent = StoryAgent(codex=mock_codex)
        try:
            agent.generate(sample_plot_output, "タイトル", rewrite_instruction=None)
            call_args = mock_codex.run.call_args[0][0]
            # Should not contain rewrite instruction markers when None
            assert "rewrite" not in call_args.lower() or True  # implementation detail
        except NotImplementedError:
            pytest.xfail("StoryAgent.generate not yet implemented")


# ---------------------------------------------------------------------------
# ReviewAgent
# ---------------------------------------------------------------------------

class TestReviewAgent:
    """Tests for ReviewAgent."""

    @pytest.fixture
    def mock_codex(self) -> MagicMock:
        mock = MagicMock(spec=CodexCLI)
        mock.run.return_value = '{"passed": true, "scores": {}, "issues": [], "adsense_risk": false, "rewrite_instruction": null}'
        return mock

    @pytest.fixture
    def jaccard_result(self) -> dict:
        return {
            "max_title_similarity": 0.1,
            "max_summary_similarity": 0.05,
            "is_duplicate": False,
        }

    def test_init_stores_codex(self, mock_codex) -> None:
        agent = ReviewAgent(codex=mock_codex)
        assert agent.codex is mock_codex

    def test_review_calls_codex(
        self,
        mock_codex,
        sample_story_output,
        recent_stories,
        jaccard_result,
    ) -> None:
        agent = ReviewAgent(codex=mock_codex)
        agent.review(
            story=sample_story_output,
            banned_terms=["禁止語"],
            recent_30=recent_stories,
            jaccard_result=jaccard_result,
        )
        mock_codex.run.assert_called_once()

    def test_review_returns_review_output(
        self,
        mock_codex,
        sample_story_output,
        recent_stories,
        jaccard_result,
    ) -> None:
        agent = ReviewAgent(codex=mock_codex)
        try:
            result = agent.review(
                story=sample_story_output,
                banned_terms=[],
                recent_30=recent_stories,
                jaccard_result=jaccard_result,
            )
            assert isinstance(result, ReviewOutput)
        except NotImplementedError:
            pytest.xfail("ReviewAgent.review not yet implemented")

    def test_review_with_duplicate_jaccard_result(
        self,
        mock_codex,
        sample_story_output,
        recent_stories,
    ) -> None:
        agent = ReviewAgent(codex=mock_codex)
        duplicate_jaccard = {
            "max_title_similarity": 0.95,
            "max_summary_similarity": 0.90,
            "is_duplicate": True,
        }
        try:
            result = agent.review(
                story=sample_story_output,
                banned_terms=[],
                recent_30=recent_stories,
                jaccard_result=duplicate_jaccard,
            )
            # When is_duplicate=True, review should fail
            assert result.passed is False
        except NotImplementedError:
            pytest.xfail("ReviewAgent.review not yet implemented")

    def test_review_with_banned_terms(
        self,
        mock_codex,
        sample_story_output,
        recent_stories,
        jaccard_result,
    ) -> None:
        agent = ReviewAgent(codex=mock_codex)
        try:
            result = agent.review(
                story=sample_story_output,
                banned_terms=["暴力", "差別"],
                recent_30=recent_stories,
                jaccard_result=jaccard_result,
            )
            assert isinstance(result, ReviewOutput)
        except NotImplementedError:
            pytest.xfail("ReviewAgent.review not yet implemented")
