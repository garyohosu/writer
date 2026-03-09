from dataclasses import dataclass, field


@dataclass
class TitleSelectionOutput:
    """Output from TitleSelectionAgent.select()."""

    selected_title: str
    reason: str
    scores: dict[str, int]
