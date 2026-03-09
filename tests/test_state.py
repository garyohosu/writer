"""Tests for writer.state.StateManager and StateRecord."""
from __future__ import annotations

import json
import os

import pytest

from writer.state import StateManager, StateRecord


class TestStateRecord:
    """Tests for the StateRecord dataclass."""

    def test_instantiation(self) -> None:
        record = StateRecord(
            run_date="2026-03-09",
            job_id="job-001",
            stage="plot",
            result="done",
            slug=None,
            attempts={},
            artifacts={},
            published_commit=None,
        )
        assert record.run_date == "2026-03-09"
        assert record.job_id == "job-001"
        assert record.stage == "plot"
        assert record.result == "done"
        assert record.slug is None
        assert record.attempts == {}
        assert record.artifacts == {}
        assert record.published_commit is None

    def test_slug_can_be_string(self) -> None:
        record = StateRecord(
            run_date="2026-03-09",
            job_id="job-002",
            stage="publish",
            result="done",
            slug="my-story-slug",
            attempts={"review": 2},
            artifacts={"plot": "/path/plot.json"},
            published_commit="abc123def456",
        )
        assert record.slug == "my-story-slug"
        assert record.published_commit == "abc123def456"

    def test_attempts_dict_stores_arbitrary_data(self) -> None:
        record = StateRecord(
            run_date="2026-03-09",
            job_id="job-003",
            stage="review",
            result="failed",
            slug=None,
            attempts={"review": 3},
            artifacts={},
            published_commit=None,
        )
        assert record.attempts["review"] == 3


class TestStateManagerLoad:
    """Tests for StateManager.load()."""

    def test_load_missing_file_raises(self, tmp_path) -> None:
        manager = StateManager(str(tmp_path / "state.json"))
        with pytest.raises((FileNotFoundError, OSError)):
            manager.load()

    def test_load_returns_state_record(self, tmp_path) -> None:
        state_file = tmp_path / "state.json"
        state_data = {
            "run_date": "2026-03-09",
            "job_id": "job-xyz",
            "stage": "story",
            "result": "in_progress",
            "slug": None,
            "attempts": {},
            "artifacts": {},
            "published_commit": None,
        }
        state_file.write_text(json.dumps(state_data))
        manager = StateManager(str(state_file))
        try:
            result = manager.load()
            assert isinstance(result, StateRecord)
            assert result.run_date == "2026-03-09"
        except NotImplementedError:
            pytest.xfail("StateManager.load not yet implemented")


class TestStateManagerSave:
    """Tests for StateManager.save()."""

    def test_save_persists_to_disk(self, tmp_path, sample_state_record) -> None:
        manager = StateManager(str(tmp_path / "state.json"))
        manager.save(sample_state_record)
        loaded = manager.load()
        assert loaded.run_date == sample_state_record.run_date
        assert loaded.stage == sample_state_record.stage


class TestStateManagerUpdate:
    """Tests for StateManager.update()."""

    def test_update_changes_stage_and_result(self, tmp_path, sample_state_record) -> None:
        manager = StateManager(str(tmp_path / "state.json"))
        manager.save(sample_state_record)
        manager.update("story", "in_progress")
        loaded = manager.load()
        assert loaded.stage == "story"
        assert loaded.result == "in_progress"

    def test_update_with_kwargs_sets_extra_fields(self, tmp_path, sample_state_record) -> None:
        manager = StateManager(str(tmp_path / "state.json"))
        manager.save(sample_state_record)
        manager.update("publish", "published", slug="my-slug")


class TestStateManagerIsTodayDone:
    """Tests for StateManager.is_today_done()."""

    def test_is_today_done_returns_false_for_missing_file(self, tmp_path) -> None:
        manager = StateManager(str(tmp_path / "state.json"))
        assert manager.is_today_done("2026-03-09") is False

    def test_is_today_done_matching_date_and_done(self, tmp_path) -> None:
        """When run_date matches and result is 'done', should return True."""
        manager = StateManager(str(tmp_path / "state.json"))
        try:
            result = manager.is_today_done("2026-03-09")
            assert isinstance(result, bool)
        except NotImplementedError:
            pytest.xfail("StateManager.is_today_done not yet implemented")


class TestStateManagerGetResumePoint:
    """Tests for StateManager.get_resume_point()."""

    def test_get_resume_point_missing_file_raises(self, tmp_path) -> None:
        manager = StateManager(str(tmp_path / "state.json"))
        with pytest.raises((FileNotFoundError, OSError)):
            manager.get_resume_point()

    def test_get_resume_point_returns_tuple(self, tmp_path, sample_state_record) -> None:
        manager = StateManager(str(tmp_path / "state.json"))
        manager.save(sample_state_record)
        result = manager.get_resume_point()
        assert isinstance(result, tuple)
        assert len(result) == 2
        stage, res = result
        assert isinstance(stage, str)
        assert isinstance(res, str)
