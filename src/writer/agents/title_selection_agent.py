from __future__ import annotations

import json

from writer.agents.codex_cli import CodexCLI
from writer.models.plot_output import PlotOutput
from writer.models.title_selection_output import TitleSelectionOutput
from writer.models.story_metadata import StoryMetadata


class TitleSelectionAgent:
    """Selects the best title from PlotOutput candidates via the Codex CLI."""

    def __init__(self, codex: CodexCLI) -> None:
        self.codex = codex

    def select(
        self,
        plot: PlotOutput,
        recent_titles: list[StoryMetadata],
    ) -> TitleSelectionOutput:
        """Choose the best title and return a TitleSelectionOutput."""
        candidates_str = "\n".join(
            f"  - {t}" for t in plot.title_candidates
        )
        recent_first_words = [m.title[:5] for m in recent_titles[:30]]
        recent_str = "、".join(recent_first_words) if recent_first_words else "なし"

        prompt = f"""タイトル選定エージェントです。
以下の候補から最適な1件を選び、JSONのみで返してください。

プロット: {plot.plot}
テーマ: {plot.theme}
想定読後感: {plot.reading_impression}

タイトル候補:
{candidates_str}

直近作品タイトル冒頭語（重複避ける）: {recent_str}

以下スキーマのみ出力:
{{
  "selected_title": "選定タイトル",
  "reason": "理由（1〜2文）",
  "scores": {{"候補A": 82, "候補B": 75, "候補C": 68}}
}}

Output must be valid JSON only. No explanation."""

        raw = self.codex.run(prompt)
        data = json.loads(raw)
        return TitleSelectionOutput(**data)
