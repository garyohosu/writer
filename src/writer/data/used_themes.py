from __future__ import annotations

import json
import os
from datetime import date, timedelta


class UsedThemes:
    """Tracks themes used in previously published stories.

    Note: add_published should only be called after a story has been
    published (committed/pushed), never for unpublished drafts.
    """

    def __init__(self, path: str) -> None:
        self.path = path

    def load(self) -> list[dict]:
        """Load and return all theme records from disk."""
        with open(self.path, encoding="utf-8") as f:
            return json.load(f)

    def get_recent_90days(self) -> list[str]:
        """Return theme strings used within the past 90 calendar days."""
        cutoff = date.today() - timedelta(days=90)
        entries = self.load()
        return [
            entry["theme"]
            for entry in entries
            if date.fromisoformat(entry["date"]) >= cutoff
        ]

    def add_published(self, theme: str, run_date: str) -> None:
        """Record *theme* as used on *run_date* after a story is published."""
        try:
            entries = self.load()
        except (FileNotFoundError, json.JSONDecodeError):
            entries = []
        record = {"theme": theme, "date": run_date}
        if record in entries:
            return
        entries.append(record)
        tmp_path = self.path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, self.path)
