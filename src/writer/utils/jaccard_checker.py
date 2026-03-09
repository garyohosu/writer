from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from writer.models.story_metadata import StoryMetadata


class JaccardChecker:
    """Detects near-duplicate stories via Jaccard similarity on character n-grams."""

    def __init__(self, threshold: float) -> None:
        self.threshold = threshold

    def char_ngrams(self, text: str, n: int) -> set[str]:
        """Return the set of all n-character substrings of *text*."""
        if len(text) < n:
            return set()
        return {text[i : i + n] for i in range(len(text) - n + 1)}

    def jaccard(self, a: set[str], b: set[str]) -> float:
        """Return |A ∩ B| / |A ∪ B|, or 0.0 when both sets are empty."""
        if not a and not b:
            return 0.0
        intersection = len(a & b)
        union = len(a | b)
        return intersection / union

    def compare(
        self,
        candidate_title: str,
        candidate_summary: str,
        recent_30: list["StoryMetadata"],
    ) -> dict:
        """Compare candidate title/summary against recent_30 stories.

        Returns:
            {
                "max_title_similarity": float,
                "max_summary_similarity": float,
                "is_duplicate": bool,
            }
        """
        title_ngrams = self.char_ngrams(candidate_title, 2)
        summary_ngrams = self.char_ngrams(candidate_summary, 2)

        max_title_sim = 0.0
        max_summary_sim = 0.0

        for story in recent_30:
            t_sim = self.jaccard(title_ngrams, self.char_ngrams(story.title, 2))
            s_sim = self.jaccard(summary_ngrams, self.char_ngrams(story.summary, 2))
            if t_sim > max_title_sim:
                max_title_sim = t_sim
            if s_sim > max_summary_sim:
                max_summary_sim = s_sim

        is_duplicate = (
            max_title_sim >= self.threshold or max_summary_sim >= self.threshold
        )

        return {
            "max_title_similarity": max_title_sim,
            "max_summary_similarity": max_summary_sim,
            "is_duplicate": is_duplicate,
        }
