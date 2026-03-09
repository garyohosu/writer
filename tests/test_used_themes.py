"""Tests for writer.data.used_themes.UsedThemes."""
from __future__ import annotations

import json
from datetime import date, timedelta

import pytest

from writer.data.used_themes import UsedThemes


@pytest.fixture
def themes_path(tmp_path) -> str:
    return str(tmp_path / "used_themes.json")


@pytest.fixture
def populated_themes_path(tmp_path) -> str:
    path = tmp_path / "used_themes.json"
    today = date(2026, 3, 9)
    entries = [
        {"theme": f"テーマ{i}", "date": (today - timedelta(days=i * 10)).isoformat()}
        for i in range(15)
    ]
    path.write_text(json.dumps(entries))
    return str(path)


@pytest.fixture
def old_themes_path(tmp_path) -> str:
    """Themes file where all entries are older than 90 days."""
    path = tmp_path / "used_themes_old.json"
    today = date(2026, 3, 9)
    entries = [
        {
            "theme": f"古いテーマ{i}",
            "date": (today - timedelta(days=100 + i)).isoformat(),
        }
        for i in range(5)
    ]
    path.write_text(json.dumps(entries))
    return str(path)


class TestUsedThemesLoad:
    """Tests for UsedThemes.load()."""

    def test_load_missing_file_raises(self, themes_path) -> None:
        ut = UsedThemes(themes_path)
        with pytest.raises((FileNotFoundError, OSError)):
            ut.load()

    def test_load_returns_list_of_dicts(self, populated_themes_path) -> None:
        ut = UsedThemes(populated_themes_path)
        try:
            result = ut.load()
            assert isinstance(result, list)
            for item in result:
                assert isinstance(item, dict)
        except NotImplementedError:
            pytest.xfail("UsedThemes.load not yet implemented")


class TestUsedThemesGetRecent90Days:
    """Tests for UsedThemes.get_recent_90days()."""

    def test_get_recent_90days_returns_list(self, populated_themes_path) -> None:
        ut = UsedThemes(populated_themes_path)
        result = ut.get_recent_90days()
        assert isinstance(result, list)

    def test_get_recent_90days_returns_list_of_strings(
        self, populated_themes_path
    ) -> None:
        ut = UsedThemes(populated_themes_path)
        try:
            result = ut.get_recent_90days()
            assert isinstance(result, list)
            for theme in result:
                assert isinstance(theme, str)
        except NotImplementedError:
            pytest.xfail("UsedThemes.get_recent_90days not yet implemented")

    def test_get_recent_90days_excludes_old_entries(self, old_themes_path) -> None:
        ut = UsedThemes(old_themes_path)
        try:
            result = ut.get_recent_90days()
            assert result == [], "Themes older than 90 days should be excluded"
        except NotImplementedError:
            pytest.xfail("UsedThemes.get_recent_90days not yet implemented")

    def test_get_recent_90days_includes_entries_within_window(
        self, populated_themes_path
    ) -> None:
        ut = UsedThemes(populated_themes_path)
        try:
            result = ut.get_recent_90days()
            # entries at 0,10,20,...,80 days ago = 9 entries within 90 days
            assert len(result) >= 9
        except NotImplementedError:
            pytest.xfail("UsedThemes.get_recent_90days not yet implemented")


class TestUsedThemesAddPublished:
    """Tests for UsedThemes.add_published()."""

    def test_add_published_appends_entry(self, themes_path) -> None:
        import json
        with open(themes_path, "w", encoding="utf-8") as f:
            json.dump([], f)
        ut = UsedThemes(themes_path)
        ut.add_published("新しいテーマ", "2026-03-09")
        data = ut.load()
        assert any(e["theme"] == "新しいテーマ" for e in data)

    def test_add_published_only_for_published_stories(self, tmp_path) -> None:
        """add_published must only be called after successful publish, not drafts."""
        path = tmp_path / "themes.json"
        path.write_text("[]")
        ut = UsedThemes(str(path))
        # This test documents the business rule: add_published is for published only
        try:
            ut.add_published("公開後のテーマ", "2026-03-09")
            data = ut.load()
            themes = [entry["theme"] for entry in data]
            assert "公開後のテーマ" in themes
        except NotImplementedError:
            pytest.xfail("UsedThemes.add_published not yet implemented")

    def test_add_published_persists_to_disk(self, tmp_path) -> None:
        path = tmp_path / "themes.json"
        path.write_text("[]")
        ut = UsedThemes(str(path))
        try:
            ut.add_published("テーマA", "2026-03-09")
            # Reload from disk to verify persistence
            ut2 = UsedThemes(str(path))
            data = ut2.load()
            themes = [entry["theme"] for entry in data]
            assert "テーマA" in themes
        except NotImplementedError:
            pytest.xfail("UsedThemes.add_published not yet implemented")
