from __future__ import annotations


class BannedTerms:
    """Loads the list of terms that must not appear in generated stories."""

    def __init__(self, path: str) -> None:
        self.path = path

    def load(self) -> list[str]:
        """Load and return all banned terms from disk."""
        raise NotImplementedError
