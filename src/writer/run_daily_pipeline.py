from __future__ import annotations

import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

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
from writer.models.story_document import StoryDocument
from writer.services.publish_service import PublishService
from writer.state import StateManager
from writer.story_file import StoryFile
from writer.utils.jaccard_checker import JaccardChecker
from writer.utils.windows_notifier import WindowsNotifier

_STAGES = ["plot", "story", "review", "publish"]
_JST = ZoneInfo("Asia/Tokyo")


def _generate_slug(run_date: str) -> str:
    """Generate a unique ASCII slug for a story based on *run_date*."""
    short_id = uuid.uuid4().hex[:8]
    return f"{run_date}-{short_id}"


def _today_jst() -> str:
    return datetime.now(_JST).date().isoformat()


def _is_manual_review_mode(mode: str) -> bool:
    return mode in {"manual", "manual_review"}


class RunDailyPipeline:
    """Main entry point that orchestrates the four-stage daily pipeline."""

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

        self._current_plot = None
        self._current_title_output = None
        self._current_story = None
        self._current_review = None
        self._current_slug: str | None = None
        self._current_date: str = _today_jst()

    def _run_stage(self, stage: str, action) -> None:
        try:
            action()
        except Exception as error:
            self.failure_handler.handle(stage, error)
            raise

    def _load_today_state(self):
        try:
            record = self.state_manager.load()
        except (FileNotFoundError, KeyError, TypeError):
            return None
        if record.run_date != self._current_date:
            return None
        return record

    def run(self) -> None:
        """Execute the full pipeline from the beginning."""
        state = self._load_today_state()
        if state is not None:
            if state.result == "published":
                return
            if state.stage == "publish" and state.result == "pending_review":
                return
            if state.stage == "publish" and state.slug:
                self._current_slug = state.slug
                self._run_stage("publish", self._execute_publish_stage)
                return

        if self.state_manager.is_today_done(self._current_date):
            return

        self._run_stage("plot", self._execute_plot_stage)
        self._run_stage("story", self._execute_story_stage)
        self._run_stage("review", self._execute_review_stage)
        if _is_manual_review_mode(self.config.publication_mode):
            return
        self._run_stage("publish", self._execute_publish_stage)

    def resume_from_stage(self, stage: str) -> None:
        """Resume the pipeline starting from *stage*."""
        if stage not in _STAGES:
            raise ValueError(f"Unknown stage: {stage!r}. Must be one of {_STAGES}.")
        idx = _STAGES.index(stage)
        for current_stage in _STAGES[idx:]:
            if current_stage == "publish" and _is_manual_review_mode(
                self.config.publication_mode
            ):
                return
            if current_stage == "plot":
                self._run_stage(current_stage, self._execute_plot_stage)
            elif current_stage == "story":
                self._run_stage(current_stage, self._execute_story_stage)
            elif current_stage == "review":
                self._run_stage(current_stage, self._execute_review_stage)
            elif current_stage == "publish":
                self._run_stage(current_stage, self._execute_publish_stage)

    def _execute_plot_stage(self) -> None:
        """Run the plot generation stage."""
        self.state_manager.update("plot", "in_progress", run_date=self._current_date)
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
        self.state_manager.update("story", "in_progress", run_date=self._current_date)
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
        self.state_manager.update("review", "in_progress", run_date=self._current_date)
        max_attempts = self.config.max_review_attempts
        recent_30 = self.stories_index.get_recent(30)
        banned = self.banned_terms.load()
        story = self._current_story
        rewrite_instruction = None

        for attempt in range(max_attempts):
            if attempt > 0 or story is None:
                story = self.story_agent.generate(
                    plot=self._current_plot,
                    selected_title=(
                        self._current_title_output.selected_title
                        if self._current_title_output
                        else ""
                    ),
                    rewrite_instruction=rewrite_instruction,
                )
                self._current_story = story

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
                self._current_review = review
                if self._current_plot is not None and story is not None:
                    doc = StoryDocument.from_outputs(
                        plot=self._current_plot,
                        story=story,
                        review=review,
                        slug=_generate_slug(self._current_date),
                        date=self._current_date,
                    )
                    saved_path = self.story_file.save_master(doc)
                    if not self.story_file.verify(saved_path):
                        raise RuntimeError("Saved story document failed verification")
                    self._current_slug = doc.front_matter.slug
                    self.state_manager.update(
                        "publish",
                        "in_progress",
                        run_date=self._current_date,
                        slug=self._current_slug,
                    )
                    if _is_manual_review_mode(self.config.publication_mode):
                        self.story_file.copy_to_pending(doc)
                        self.state_manager.update(
                            "publish",
                            "pending_review",
                            run_date=self._current_date,
                            slug=self._current_slug,
                        )
                return

            rewrite_instruction = review.rewrite_instruction

        raise RuntimeError(f"Max review attempts reached ({max_attempts})")

    def _execute_publish_stage(self) -> None:
        """Run the publish stage."""
        slug = self._current_slug
        if slug is None:
            state = self._load_today_state()
            slug = state.slug if state is not None else None
        if slug is None:
            raise RuntimeError("No slug available for publish stage")
        self.publish_service.run_from_master(
            slug=slug,
            date=self._current_date,
        )
        self.notifier.notify(
            "DailyStory",
            f"本日分を公開しました（{self._current_date}）",
        )
