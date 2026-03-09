"""Shared pytest fixtures for the writer test suite."""
from __future__ import annotations

import pytest

from writer.models.plot_output import PlotOutput
from writer.models.title_selection_output import TitleSelectionOutput
from writer.models.story_output import StoryOutput
from writer.models.review_output import ReviewOutput
from writer.models.story_metadata import StoryMetadata
from writer.models.story_front_matter import StoryFrontMatter
from writer.models.story_document import StoryDocument
from writer.config import Config
from writer.state import StateRecord


# ---------------------------------------------------------------------------
# Model fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_plot_output() -> PlotOutput:
    return PlotOutput(
        title_candidates=["夜明けの約束", "消えない星", "帰還"],
        plot="主人公は記憶を失った探偵として…",
        characters=[
            {"name": "田中一郎", "role": "protagonist"},
            {"name": "鈴木花子", "role": "antagonist"},
        ],
        theme="記憶と喪失",
        setting="近未来の東京",
        ending_type="open",
        reading_impression="切なく温かい",
    )


@pytest.fixture
def sample_title_selection_output() -> TitleSelectionOutput:
    return TitleSelectionOutput(
        selected_title="夜明けの約束",
        reason="最も感情的な共鳴を持つ",
        scores={"夜明けの約束": 95, "消えない星": 80, "帰還": 70},
    )


@pytest.fixture
def sample_story_output() -> StoryOutput:
    return StoryOutput(
        title="夜明けの約束",
        body="夜が明ける前の静寂の中で…" * 100,
        character_count=3000,
        reading_time_min=8,
        summary="記憶を失った探偵が過去と向き合う物語",
        tags=["ミステリー", "SF", "感動"],
    )


@pytest.fixture
def sample_review_output_passed() -> ReviewOutput:
    return ReviewOutput(
        passed=True,
        scores={"quality": 85, "originality": 80, "readability": 90},
        issues=[],
        adsense_risk=False,
        rewrite_instruction=None,
    )


@pytest.fixture
def sample_review_output_failed() -> ReviewOutput:
    return ReviewOutput(
        passed=False,
        scores={"quality": 50, "originality": 45, "readability": 60},
        issues=["文章が単調すぎる", "キャラクターの動機が不明確"],
        adsense_risk=False,
        rewrite_instruction="キャラクターの動機をより明確に描写してください。",
    )


@pytest.fixture
def sample_review_output_adsense_risk() -> ReviewOutput:
    return ReviewOutput(
        passed=True,  # Will be forced to False by __post_init__
        scores={"quality": 88, "originality": 85, "readability": 87},
        issues=["AdSense ポリシー違反の可能性"],
        adsense_risk=True,
        rewrite_instruction="問題のある表現を削除してください。",
    )


@pytest.fixture
def sample_story_metadata() -> StoryMetadata:
    return StoryMetadata(
        date="2026-03-01",
        slug="yoake-no-yakusoku",
        title="夜明けの約束",
        summary="記憶を失った探偵が過去と向き合う物語",
        tags=["ミステリー", "SF"],
        character_count=3000,
        reading_time_min=8,
        review_score=85,
    )


@pytest.fixture
def sample_story_metadata_list() -> list[StoryMetadata]:
    entries = []
    for i in range(5):
        entries.append(
            StoryMetadata(
                date=f"2026-02-{i + 1:02d}",
                slug=f"story-{i}",
                title=f"物語タイトル{i}",
                summary=f"あらすじ {i}",
                tags=["タグA"],
                character_count=2000 + i * 100,
                reading_time_min=5 + i,
                review_score=75 + i,
            )
        )
    return entries


@pytest.fixture
def sample_story_front_matter() -> StoryFrontMatter:
    return StoryFrontMatter(
        title="夜明けの約束",
        date="2026-03-09",
        slug="yoake-no-yakusoku",
        tags=["ミステリー", "SF", "感動"],
        genre="ミステリー",
        theme="記憶と喪失",
        character_count=3000,
        reading_time_min=8,
        status="published",
        summary="記憶を失った探偵が過去と向き合う物語",
        ai_generated=True,
        review_score=85,
    )


@pytest.fixture
def sample_story_document(
    sample_story_front_matter: StoryFrontMatter,
    sample_story_output: StoryOutput,
) -> StoryDocument:
    return StoryDocument(
        front_matter=sample_story_front_matter,
        body=sample_story_output.body,
    )


# ---------------------------------------------------------------------------
# Config / State fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_config() -> Config:
    return Config(
        publication_mode="auto",
        max_review_attempts=3,
        similarity_threshold=0.8,
    )


@pytest.fixture
def sample_state_record() -> StateRecord:
    return StateRecord(
        run_date="2026-03-09",
        job_id="job-abc123",
        stage="plot",
        result="done",
        slug=None,
        attempts={},
        artifacts={},
        published_commit=None,
    )


# ---------------------------------------------------------------------------
# Recent stories fixture (for Jaccard / review tests)
# ---------------------------------------------------------------------------

@pytest.fixture
def recent_stories() -> list[StoryMetadata]:
    return [
        StoryMetadata(
            date=f"2026-0{i + 1}-01",
            slug=f"recent-story-{i}",
            title=f"最近の物語 {i}",
            summary=f"これはサンプルのあらすじです {i}",
            tags=["タグ"],
            character_count=2500,
            reading_time_min=7,
            review_score=80,
        )
        for i in range(10)
    ]
