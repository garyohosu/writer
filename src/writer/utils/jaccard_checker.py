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
        normalized = "".join(text.lower().split())
        if not normalized:
            return set()
        if len(normalized) < n:
            return {normalized}
        return {
            normalized[i : i + n] for i in range(len(normalized) - n + 1)
        }

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
                "max_similarity": float,
                "is_duplicate": bool,
            }
        """
        title_ngrams = self.char_ngrams(candidate_title, 3)
        summary_ngrams = self.char_ngrams(candidate_summary, 3)
        combined_ngrams = self.char_ngrams(
            f"{candidate_title}\n{candidate_summary}",
            3,
        )

        max_title_sim = 0.0
        max_summary_sim = 0.0
        max_similarity = 0.0

        for story in recent_30:
            t_sim = self.jaccard(title_ngrams, self.char_ngrams(story.title, 3))
            s_sim = self.jaccard(summary_ngrams, self.char_ngrams(story.summary, 3))
            combined_sim = self.jaccard(
                combined_ngrams,
                self.char_ngrams(f"{story.title}\n{story.summary}", 3),
            )
            if t_sim > max_title_sim:
                max_title_sim = t_sim
            if s_sim > max_summary_sim:
                max_summary_sim = s_sim
            if combined_sim > max_similarity:
                max_similarity = combined_sim

        is_duplicate = max_similarity >= self.threshold

        return {
            "max_title_similarity": max_title_sim,
            "max_summary_similarity": max_summary_sim,
            "max_similarity": max_similarity,
            "is_duplicate": is_duplicate,
        }
