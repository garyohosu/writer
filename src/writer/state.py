from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from typing import Any, Optional


@dataclass
class StateRecord:
    """Persistent record of a single pipeline run."""

    run_date: str
    job_id: str
    stage: str
    result: str
    slug: Optional[str]
    attempts: dict[str, Any]
    artifacts: dict[str, Any]
    published_commit: Optional[str]


class StateManager:
    """Reads and writes pipeline run state to a JSON file."""

    def __init__(self, path: str) -> None:
        self.path = path

    def load(self) -> StateRecord:
        """Load and return the current StateRecord from disk."""
        with open(self.path, encoding="utf-8") as f:
            data = json.load(f)
        return StateRecord(**data)

    def save(self, record: StateRecord) -> None:
        """Persist *record* to disk."""
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(asdict(record), f, ensure_ascii=False, indent=2)

    def update(self, stage: str, result: str, **kwargs: Any) -> None:
        """Update the persisted state for *stage* with *result* and extra fields."""
        try:
            record = self.load()
        except (FileNotFoundError, KeyError, TypeError):
            import uuid
            record = StateRecord(
                run_date=kwargs.pop("run_date", ""),
                job_id=str(uuid.uuid4()),
                stage=stage,
                result=result,
                slug=None,
                attempts={},
                artifacts={},
                published_commit=None,
            )
        record.stage = stage
        record.result = result
        for key, value in kwargs.items():
            setattr(record, key, value)
        self.save(record)

    def is_today_done(self, run_date: str) -> bool:
        """Return True when the stored run_date matches *run_date* and result is 'done'."""
        try:
            record = self.load()
        except (FileNotFoundError, KeyError, TypeError):
            return False
        return record.run_date == run_date and record.result == "published"

    def get_resume_point(self) -> tuple[str, str]:
        """Return (stage, result) indicating where to resume the pipeline."""
        record = self.load()
        return (record.stage, record.result)
