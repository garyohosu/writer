from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
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
        self.run_dir = Path(base_dir) / run_date
        self.run_dir.mkdir(parents=True, exist_ok=True)

    def _write_text(self, filename: str, content: str, append: bool = False) -> None:
        path = self.run_dir / filename
        mode = "a" if append else "w"
        with path.open(mode, encoding="utf-8") as f:
            f.write(content)

    def _write_json(self, filename: str, payload: object) -> None:
        path = self.run_dir / filename
        data = asdict(payload) if is_dataclass(payload) else payload
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def save_run_log(self, msg: str) -> None:
        """Append *msg* to the run log file."""
        timestamp = datetime.now().isoformat(timespec="seconds")
        self._write_text("run.log", f"[{timestamp}] {msg}\n", append=True)

    def save_plot_json(self, plot: "PlotOutput") -> None:
        """Serialize and save the PlotOutput as JSON."""
        self._write_json("plot.json", plot)

    def save_selected_title_json(self, title: "TitleSelectionOutput") -> None:
        """Serialize and save the TitleSelectionOutput as JSON."""
        self._write_json("selected_title.json", title)

    def save_generation_txt(self, story: "StoryOutput") -> None:
        """Save the story body text to a plain-text file."""
        self._write_text("generation.txt", story.body)

    def save_review_json(self, review: "ReviewOutput", attempt: int) -> None:
        """Serialize and save the ReviewOutput for *attempt* as JSON."""
        filename = "review.json" if attempt == 1 else f"review-{attempt}.json"
        self._write_json(filename, review)

    def save_error(self, stage: str, error: Exception) -> None:
        """Save error details for *stage* to disk."""
        self._write_text(f"{stage}-error.log", f"{type(error).__name__}: {error}\n")
