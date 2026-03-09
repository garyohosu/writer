from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from writer.models.plot_output import PlotOutput
    from writer.models.story_output import StoryOutput
    from writer.models.review_output import ReviewOutput
    from writer.models.title_selection_output import TitleSelectionOutput


class LogManager:
    """Saves structured log artifacts for each pipeline run."""

    def __init__(self, base_dir: str, run_date: str) -> None:
        self.base_dir = base_dir
        self.run_date = run_date

    def save_run_log(self, msg: str) -> None:
        """Append *msg* to the run log file."""
        raise NotImplementedError

    def save_plot_json(self, plot: "PlotOutput") -> None:
        """Serialize and save the PlotOutput as JSON."""
        raise NotImplementedError

    def save_selected_title_json(self, title: "TitleSelectionOutput") -> None:
        """Serialize and save the TitleSelectionOutput as JSON."""
        raise NotImplementedError

    def save_generation_txt(self, story: "StoryOutput") -> None:
        """Save the story body text to a plain-text file."""
        raise NotImplementedError

    def save_review_json(self, review: "ReviewOutput", attempt: int) -> None:
        """Serialize and save the ReviewOutput for *attempt* as JSON."""
        raise NotImplementedError

    def save_error(self, stage: str, error: Exception) -> None:
        """Save error details for *stage* to disk."""
        raise NotImplementedError
