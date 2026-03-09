from __future__ import annotations

import json
from typing import Optional

from writer.agents.codex_cli import CodexCLI
from writer.models.plot_output import PlotOutput
from writer.models.story_output import StoryOutput


class StoryAgent:
    """Generates story prose via the Codex CLI."""

    def __init__(self, codex: CodexCLI) -> None:
        self.codex = codex

    def generate(
        self,
        plot: PlotOutput,
        selected_title: str,
        rewrite_instruction: Optional[str] = None,
    ) -> StoryOutput:
        """Generate story text and return a StoryOutput.

        When *rewrite_instruction* is provided the agent rewrites an existing
        draft rather than generating from scratch.
        """
        rewrite_section = ""
        if rewrite_instruction:
            rewrite_section = f"\n【改稿指示】\n{rewrite_instruction}\n"

        prompt = f"""あなたは日本語短編小説作家です。
以下のプロット情報をもとに短編小説を書き、JSONのみで返してください。

タイトル: {selected_title}
プロット: {plot.plot}
テーマ: {plot.theme}
舞台: {plot.setting}
結末傾向: {plot.ending_type}
想定読後感: {plot.reading_impression}
{rewrite_section}
制約:
- 本文 2000〜5000字
- 冒頭3行で読者を引き込む
- 過剰な説明を避ける
- AI特有の冗長さを避ける

出力スキーマ（JSONのみ）:
{{
  "title": "確定タイトル",
  "body": "本文（2000〜5000字）",
  "character_count": 3120,
  "reading_time_min": 6,
  "summary": "要約（100〜200字）",
  "tags": ["タグ1", "タグ2"]
}}

Output must be valid JSON only. No explanation."""

        raw = self.codex.run(prompt)
        data = json.loads(raw)
        return StoryOutput(**data)
