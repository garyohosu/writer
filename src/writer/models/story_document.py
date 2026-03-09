from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from writer.models.plot_output import PlotOutput
    from writer.models.story_output import StoryOutput
    from writer.models.review_output import ReviewOutput
    from writer.models.story_metadata import StoryMetadata

from writer.models.story_front_matter import StoryFrontMatter


@dataclass
class StoryDocument:
    """Complete story document combining front matter and body."""

    front_matter: StoryFrontMatter
    body: str

    @classmethod
    def from_outputs(
        cls,
        plot: "PlotOutput",
        story: "StoryOutput",
        review: "ReviewOutput",
        slug: str,
        date: str,
    ) -> "StoryDocument":
        """Construct a StoryDocument from pipeline outputs."""
        from writer.models.plot_output import PlotOutput
        from writer.models.story_output import StoryOutput
        from writer.models.review_output import ReviewOutput
        overall_score = review.scores.get("overall", sum(review.scores.values()) // max(1, len(review.scores)))
        front_matter = StoryFrontMatter(
            title=story.title,
            date=date,
            slug=slug,
            tags=story.tags,
            genre=plot.ending_type,
            theme=plot.theme,
            character_count=story.character_count,
            reading_time_min=story.reading_time_min,
            status="published",
            summary=story.summary,
            ai_generated=True,
            review_score=overall_score,
        )
        return cls(front_matter=front_matter, body=story.body)

    def to_index_entry(self) -> "StoryMetadata":
        """Convert this document to a StoryMetadata index entry."""
        from writer.models.story_metadata import StoryMetadata
        fm = self.front_matter
        return StoryMetadata(
            date=fm.date,
            slug=fm.slug,
            title=fm.title,
            summary=fm.summary,
            tags=fm.tags,
            character_count=fm.character_count,
            reading_time_min=fm.reading_time_min,
            review_score=fm.review_score,
        )
