from __future__ import annotations

from typing import Any


class FailureHandler:
    """Centralises error handling and failure-state recording for the pipeline."""

    def handle(self, stage: str, error: Exception) -> None:
        """Handle an exception that occurred in *stage*."""
        raise NotImplementedError

    def mark_failed(self, stage: str, **kwargs: Any) -> None:
        """Persist a failure record for *stage* with optional extra context."""
        raise NotImplementedError
