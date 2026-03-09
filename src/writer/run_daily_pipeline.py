from __future__ import annotations

import datetime
import uuid

from writer.config import Config
from writer.state import StateManager
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
from writer.models.story_document import StoryDocument

_STAGES = ["plot", "story", "review", "publish"]


def _generate_slug(run_date: str) -> str:
    """Generate a unique ASCII slug for a story based on *run_date*."""
    short_id = uuid.uuid4().hex[:8]
    return f"{run_date}-{short_id}"


class RunDailyPipeline:
    """Main entry point that orchestrates the four-stage daily pipeline.

    Stages: plot -> story -> review -> publish
    """

    def __init__(
        self,
        config: Config,
        state_manager: StateManager,
        log_manager: LogManager,
        failure_handler: FailureHandler,
        plot_agent: PlotAgent,
        title_agent: TitleSelectionAgent,
        story_agent: StoryAgent,
        review_agent: ReviewAgent,
        stories_index: StoriesIndex,
        used_themes: UsedThemes,
        banned_terms: BannedTerms,
        story_file: StoryFile,
        jaccard_checker: JaccardChecker,
        publish_service: PublishService,
        notifier: WindowsNotifier,
    ) -> None:
        self.config = config
        self.state_manager = state_manager
        self.log_manager = log_manager
        self.failure_handler = failure_handler
        self.plot_agent = plot_agent
        self.title_agent = title_agent
        self.story_agent = story_agent
        self.review_agent = review_agent
        self.stories_index = stories_index
        self.used_themes = used_themes
        self.banned_terms = banned_terms
        self.story_file = story_file
        self.jaccard_checker = jaccard_checker
        self.publish_service = publish_service
        self.notifier = notifier

        # Internal pipeline state (populated as stages execute)
        self._current_plot = None
        self._current_title_output = None
        self._current_story = None
        self._current_review = None
        self._current_slug: str | None = None
        self._current_date: str = datetime.date.today().isoformat()

    def run(self) -> None:
        """Execute the full pipeline from the beginning."""
        if self.state_manager.is_today_done(self._current_date):
            return
        self._execute_plot_stage()
        self._execute_story_stage()
        self._execute_review_stage()
        self._execute_publish_stage()

    def resume_from_stage(self, stage: str) -> None:
        """Resume the pipeline starting from *stage*."""
        if stage not in _STAGES:
            raise ValueError(f"Unknown stage: {stage!r}. Must be one of {_STAGES}.")
        idx = _STAGES.index(stage)
        for s in _STAGES[idx:]:
            if s == "plot":
                self._execute_plot_stage()
            elif s == "story":
                self._execute_story_stage()
            elif s == "review":
                self._execute_review_stage()
            elif s == "publish":
                self._execute_publish_stage()

    def _execute_plot_stage(self) -> None:
        """Run the plot generation stage."""
        recent = self.stories_index.get_recent(30)
        used = self.used_themes.get_recent_90days()
        banned = self.banned_terms.load()

        plot = self.plot_agent.generate(
            stories_index=recent,
            used_themes=used,
            banned_terms=banned,
        )
        title_output = self.title_agent.select(plot=plot, recent_titles=recent)

        self.log_manager.save_plot_json(plot)
        self.log_manager.save_selected_title_json(title_output)

        self._current_plot = plot
        self._current_title_output = title_output

    def _execute_story_stage(self) -> None:
        """Run the story generation stage."""
        selected_title = (
            self._current_title_output.selected_title
            if self._current_title_output is not None
            else ""
        )
        story = self.story_agent.generate(
            plot=self._current_plot,
            selected_title=selected_title,
            rewrite_instruction=None,
        )
        self.log_manager.save_generation_txt(story)
        self._current_story = story

    def _execute_review_stage(self) -> None:
        """Run the story review stage (may loop up to max_review_attempts)."""
        max_attempts = self.config.max_review_attempts
        recent_30 = self.stories_index.get_recent(30)
        banned = self.banned_terms.load()
        story = self._current_story
        rewrite_instruction = None

        for attempt in range(max_attempts):
            # Regenerate if this is a retry
            if attempt > 0 or story is None:
                story = self.story_agent.generate(
                    plot=self._current_plot,
                    selected_title=(
                        self._current_title_output.selected_title
                        if self._current_title_output else ""
                    ),
                    rewrite_instruction=rewrite_instruction,
                )
                self._current_story = story

            # Jaccard pre-check
            title = getattr(story, "title", "") if story else ""
            summary = getattr(story, "summary", "") if story else ""
            jaccard_result = self.jaccard_checker.compare(title, summary, recent_30)

            review = self.review_agent.review(
                story=story,
                banned_terms=banned,
                recent_30=recent_30,
                jaccard_result=jaccard_result,
            )
            self.log_manager.save_review_json(review, attempt + 1)

            if review.passed:
                # SPEC §12.1 step 11: レビュー合格後に正本を stories/ に保存
                self._current_review = review
                if self._current_plot is not None and story is not None:
                    slug = _generate_slug(self._current_date)
                    selected_title = (
                        self._current_title_output.selected_title
                        if self._current_title_output else story.title
                    )
                    doc = StoryDocument.from_outputs(
                        plot=self._current_plot,
                        story=story,
                        review=review,
                        slug=slug,
                        date=self._current_date,
                    )
                    self.story_file.save_master(doc)
                    self._current_slug = slug
                return

            rewrite_instruction = review.rewrite_instruction

        # All attempts exhausted
        self.failure_handler.handle("review", RuntimeError("Max review attempts reached"))
        self.notifier.notify(
            "DailyStory",
            f"本日分の生成が{max_attempts}回失敗しました",
        )

    def _execute_publish_stage(self) -> None:
        """Run the publish stage."""
        slug = self._current_slug or _generate_slug(self._current_date)
        commit_hash = self.publish_service.run_from_master(
            slug=slug,
            date=self._current_date,
        )
        self.notifier.notify(
            "DailyStory",
            f"本日分を公開しました（{self._current_date}）",
        )
