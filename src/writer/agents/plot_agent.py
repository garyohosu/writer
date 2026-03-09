from __future__ import annotations

import json
from dataclasses import asdict

from writer.agents.codex_cli import CodexCLI
from writer.models.plot_output import PlotOutput


class PlotAgent:
    """Generates story plots via the Codex CLI."""

    def __init__(self, codex: CodexCLI) -> None:
        self.codex = codex

    def generate(
        self,
        stories_index: list,
        used_themes: list[str],
        banned_terms: list[str],
    ) -> PlotOutput:
        """Generate a new story plot and return a PlotOutput."""
        recent_titles = [getattr(s, "title", str(s)) for s in stories_index[:30]]
        banned_str = "、".join(banned_terms) if banned_terms else "なし"
        used_str = "、".join(used_themes[:20]) if used_themes else "なし"
        recent_str = "、".join(recent_titles[:10]) if recent_titles else "なし"

        prompt = f"""あなたは日本語短編小説のプロット作家です。
以下の制約を守り、新しいプロットをJSON形式のみで出力してください。

禁止語: {banned_str}
直近使用テーマ（避けること）: {used_str}
直近作品タイトル（参考）: {recent_str}

以下のJSONスキーマのみを出力してください（説明文なし）:
{{
  "title_candidates": ["候補A", "候補B", "候補C"],
  "plot": "200〜400字のプロット本文",
  "characters": [{{"name": "主人公名", "role": "主人公", "attribute": "属性"}}],
  "theme": "テーマ一文",
  "setting": "舞台説明",
  "ending_type": "結末傾向",
  "reading_impression": "想定読後感"
}}

Output must be valid JSON only. No explanation."""

        raw = self.codex.run(prompt)
        data = json.loads(raw)
        return PlotOutput(**data)
