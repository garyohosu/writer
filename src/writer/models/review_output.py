from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ReviewOutput:
    """Output from ReviewAgent.review().

    Business rule: adsense_risk=True forces passed=False.
    """

    passed: bool
    scores: dict[str, int]
    issues: list[str]
    adsense_risk: bool
    rewrite_instruction: Optional[str]

    def __post_init__(self) -> None:
        # Enforce business rule: adsense_risk=True forces passed=False
        if self.adsense_risk:
            self.passed = False
