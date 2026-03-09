"""Tests for writer.data.stories_index.StoriesIndex."""
from __future__ import annotations

import json

import pytest

from writer.data.stories_index import StoriesIndex
from writer.models.story_metadata import StoryMetadata


@pytest.fixture
def index_path(tmp_path) -> str:
    return str(tmp_path / "stories_index.json")


@pytest.fixture
def populated_index_path(tmp_path) -> str:
    path = tmp_path / "stories_index.json"
    entries = [
        {
            "date": f"2026-02-{i + 1:02d}",
            "slug": f"story-{i}",
            "title": f"物語タイトル{i}",
            "summary": f"あらすじ{i}",
            "tags": ["タグ"],
            "character_count": 2000 + i * 100,
            "reading_time_min": 5 + i,
            "review_score": 75 + i,
        }
        for i in range(10)
    ]
    path.write_text(json.dumps(entries))
    return str(path)


class TestStoriesIndexLoad:
    """Tests for StoriesIndex.load()."""

    def test_load_missing_file_raises(self, index_path) -> None:
        index = StoriesIndex(index_path)
        with pytest.raises((FileNotFoundError, OSError)):
            index.load()

    def test_load_returns_list_of_story_metadata(self, populated_index_path) -> None:
        index = StoriesIndex(populated_index_path)
        try:
            result = index.load()
            assert isinstance(result, list)
            assert all(isinstance(m, StoryMetadata) for m in result)
        except NotImplementedError:
            pytest.xfail("StoriesIndex.load not yet implemented")

    def test_load_empty_file_returns_empty_list(self, tmp_path) -> None:
        path = tmp_path / "empty.json"
        path.write_text("[]")
        index = StoriesIndex(str(path))
        try:
            result = index.load()
            assert result == []
        except NotImplementedError:
            pytest.xfail("StoriesIndex.load not yet implemented")


class TestStoriesIndexGetRecent:
    """Tests for StoriesIndex.get_recent()."""

    def test_get_recent_returns_list(self, populated_index_path) -> None:
        index = StoriesIndex(populated_index_path)
        result = index.get_recent(5)
        assert isinstance(result, list)

    def test_get_recent_returns_n_entries(self, populated_index_path) -> None:
        index = StoriesIndex(populated_index_path)
        try:
            result = index.get_recent(5)
            assert len(result) == 5
        except NotImplementedError:
            pytest.xfail("StoriesIndex.get_recent not yet implemented")

    def test_get_recent_returns_most_recent_first(self, populated_index_path) -> None:
        index = StoriesIndex(populated_index_path)
        try:
            result = index.get_recent(3)
            dates = [m.date for m in result]
            assert dates == sorted(dates, reverse=True)
        except NotImplementedError:
            pytest.xfail("StoriesIndex.get_recent not yet implemented")

    def test_get_recent_n_larger_than_total(self, populated_index_path) -> None:
        index = StoriesIndex(populated_index_path)
        try:
            result = index.get_recent(100)
            assert len(result) <= 10  # only 10 entries exist
        except NotImplementedError:
            pytest.xfail("StoriesIndex.get_recent not yet implemented")


class TestStoriesIndexAtomicUpdate:
    """Tests for StoriesIndex.atomic_update()."""

    def test_atomic_update_on_empty_file_creates_entry(
        self, tmp_path, sample_story_metadata
    ) -> None:
        path = tmp_path / "new_index.json"
        path.write_text("[]")
        index = StoriesIndex(str(path))
        index.atomic_update(sample_story_metadata)
        loaded = index.load()
        assert any(m.slug == sample_story_metadata.slug for m in loaded)

    def test_atomic_update_adds_new_entry(self, tmp_path, sample_story_metadata) -> None:
        path = tmp_path / "index.json"
        path.write_text("[]")
        index = StoriesIndex(str(path))
        try:
            index.atomic_update(sample_story_metadata)
            loaded = index.load()
            slugs = [m.slug for m in loaded]
            assert sample_story_metadata.slug in slugs
        except NotImplementedError:
            pytest.xfail("StoriesIndex.atomic_update not yet implemented")

    def test_atomic_update_replaces_existing_entry(
        self, tmp_path, sample_story_metadata
    ) -> None:
        path = tmp_path / "index.json"
        path.write_text(
            json.dumps(
                [
                    {
                        "date": sample_story_metadata.date,
                        "slug": sample_story_metadata.slug,
                        "title": "Old Title",
                        "summary": "Old summary",
                        "tags": [],
                        "character_count": 100,
                        "reading_time_min": 1,
                        "review_score": 50,
                    }
                ]
            )
        )
        index = StoriesIndex(str(path))
        try:
            index.atomic_update(sample_story_metadata)
            loaded = index.load()
            match = next(m for m in loaded if m.slug == sample_story_metadata.slug)
            assert match.title == sample_story_metadata.title
        except NotImplementedError:
            pytest.xfail("StoriesIndex.atomic_update not yet implemented")
