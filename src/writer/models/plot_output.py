from dataclasses import dataclass, field


@dataclass
class PlotOutput:
    """Output from PlotAgent.generate()."""

    title_candidates: list[str]
    plot: str
    characters: list[dict]
    theme: str
    setting: str
    ending_type: str
    reading_impression: str
