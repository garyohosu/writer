from dataclasses import dataclass, field


@dataclass
class StoryFrontMatter:
    """YAML front matter for a story Markdown file."""

    title: str
    date: str
    slug: str
    tags: list[str]
    genre: str
    theme: str
    character_count: int
    reading_time_min: int
    status: str
    summary: str
    ai_generated: bool
    review_score: int
