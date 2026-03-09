from __future__ import annotations

import json
from dataclasses import dataclass


@dataclass
class Config:
    """Application configuration loaded from a TOML/YAML/JSON config file."""

    publication_mode: str
    max_review_attempts: int
    similarity_threshold: float

    @classmethod
    def load(cls, path: str) -> "Config":
        """Load configuration from *path* and return a Config instance."""
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return cls(
            publication_mode=data["publication_mode"],
            max_review_attempts=data["max_review_attempts"],
            similarity_threshold=data["similarity_threshold"],
        )
