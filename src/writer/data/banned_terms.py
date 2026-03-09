from __future__ import annotations

import json


class BannedTerms:
    """Loads the list of terms that must not appear in generated stories."""

    def __init__(self, path: str) -> None:
        self.path = path

    def load(self) -> list[str]:
        """Load and return all banned terms from disk."""
        with open(self.path, encoding="utf-8") as f:
            return json.load(f)
