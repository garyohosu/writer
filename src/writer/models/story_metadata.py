from dataclasses import dataclass, field


@dataclass
class StoryMetadata:
    """Lightweight story entry stored in the stories index."""

    date: str
    slug: str
    title: str
    summary: str
    tags: list[str]
    character_count: int
    reading_time_min: int
    review_score: int
