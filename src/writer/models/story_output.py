from dataclasses import dataclass, field


@dataclass
class StoryOutput:
    """Output from StoryAgent.generate()."""

    title: str
    body: str
    character_count: int
    reading_time_min: int
    summary: str
    tags: list[str]
