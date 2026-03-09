from __future__ import annotations

import json

from writer.agents.codex_cli import CodexCLI
from writer.models.story_output import StoryOutput
from writer.models.review_output import ReviewOutput
from writer.models.story_metadata import StoryMetadata


class ReviewAgent:
    """Reviews generated stories for quality and policy compliance."""

    def __init__(self, codex: CodexCLI) -> None:
        self.codex = codex

    def review(
        self,
        story: StoryOutput,
        banned_terms: list[str],
        recent_30: list[StoryMetadata],
        jaccard_result: dict,
    ) -> ReviewOutput:
        """Review *story* and return a ReviewOutput."""
        # If Jaccard check already flagged as duplicate, fail immediately
        if jaccard_result.get("is_duplicate"):
            return ReviewOutput(
                passed=False,
                scores={"originality": 0, "readability": 0, "consistency": 0, "hook": 0, "ending": 0, "overall": 0},
                issues=["過去作品との類似度が閾値を超えています（Jaccard重複検出）"],
                adsense_risk=False,
                rewrite_instruction="過去作品と異なるテーマ・設定・タイトルで再生成してください。",
            )

        banned_str = "、".join(banned_terms) if banned_terms else "なし"
        recent_str = "\n".join(
            f"  - {m.title}：{m.summary}" for m in recent_30[:10]
        )
        jaccard_str = (
            f"タイトル類似度: {jaccard_result.get('max_title_similarity', 0):.2f}, "
            f"要約類似度: {jaccard_result.get('max_summary_similarity', 0):.2f}"
        )

        prompt = f"""あなたは短編小説品質審査員です。
以下の作品をレビューし、JSONのみで返してください。

【作品】
タイトル: {story.title}
要約: {story.summary}
本文（冒頭500字）:
{story.body[:500]}

【審査条件】
禁止語: {banned_str}
直近作品類似度（ローカル検査済み）: {jaccard_str}

【直近作品（差別化確認用）】
{recent_str}

【評価観点と合格基準】
- 独自性 (originality): 80点以上
- 読みやすさ (readability): 75点以上
- 一貫性 (consistency): 85点以上
- 冒頭の引き (hook)
- 結末の余韻 (ending)
- 総合 (overall): 80点以上
- AdSenseリスク: 差別・暴力・性的表現を含む場合 true

出力スキーマ（JSONのみ）:
{{
  "passed": true,
  "scores": {{
    "originality": 85,
    "readability": 80,
    "consistency": 90,
    "hook": 78,
    "ending": 82,
    "overall": 83
  }},
  "issues": [],
  "adsense_risk": false,
  "rewrite_instruction": null
}}

Output must be valid JSON only. No explanation."""

        raw = self.codex.run(prompt)
        data = json.loads(raw)
        return ReviewOutput(**data)
