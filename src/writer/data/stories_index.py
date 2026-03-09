from __future__ import annotations

import json
import os
from dataclasses import asdict

from writer.models.story_metadata import StoryMetadata


class StoriesIndex:
    """Manages the persistent JSON index of all published stories."""

    def __init__(self, path: str) -> None:
        self.path = path

    def load(self) -> list[StoryMetadata]:
        """Load and return all story metadata entries from the index."""
        with open(self.path, encoding="utf-8") as f:
            data = json.load(f)
        return [StoryMetadata(**entry) for entry in data]

    def get_recent(self, n: int) -> list[StoryMetadata]:
        """Return the *n* most-recently dated story metadata entries."""
        entries = self.load()
        sorted_entries = sorted(entries, key=lambda m: m.date, reverse=True)
        return sorted_entries[:n]

    def atomic_update(self, entry: StoryMetadata) -> None:
        """Atomically add or replace *entry* in the index file (by slug)."""
        try:
            entries = self.load()
        except (FileNotFoundError, json.JSONDecodeError):
            entries = []
        entries = [e for e in entries if e.slug != entry.slug]
        entries.insert(0, entry)
        entries.sort(key=lambda m: m.date, reverse=True)
        tmp_path = self.path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump([asdict(e) for e in entries], f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, self.path)
