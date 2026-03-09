from __future__ import annotations

from typing import Any

from writer.log_manager import LogManager
from writer.state import StateManager
from writer.utils.windows_notifier import WindowsNotifier


class FailureHandler:
    """Centralises error handling and failure-state recording for the pipeline."""

    def __init__(
        self,
        state_manager: StateManager,
        logger: LogManager,
        notifier: WindowsNotifier,
    ) -> None:
        self.state_manager = state_manager
        self.logger = logger
        self.notifier = notifier

    def handle(self, stage: str, error: Exception) -> None:
        """Handle an exception that occurred in *stage*."""
        self.logger.save_error(stage, error)
        self.mark_failed(stage, error=str(error))
        try:
            self.notifier.notify("DailyStory", f"{stage} stage failed: {error}")
        except Exception as notify_error:
            self.logger.save_error("notify", notify_error)

    def mark_failed(self, stage: str, **kwargs: Any) -> None:
        """Persist a failure record for *stage* with optional extra context."""
        self.state_manager.update(stage, "failed", **kwargs)
