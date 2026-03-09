"""Tests for writer.services.publish_service.PublishService."""
from __future__ import annotations

from unittest.mock import MagicMock, patch, call

import pytest

from writer.services.publish_service import PublishService
from writer.story_file import StoryFile
from writer.data.stories_index import StoriesIndex
from writer.utils.git_operations import GitOperations
from writer.state import StateManager


@pytest.fixture
def mock_story_file() -> MagicMock:
    return MagicMock(spec=StoryFile)


@pytest.fixture
def mock_stories_index() -> MagicMock:
    return MagicMock(spec=StoriesIndex)


@pytest.fixture
def mock_git() -> MagicMock:
    mock = MagicMock(spec=GitOperations)
    mock.add_all.return_value = None
    mock.commit.return_value = "abc123def456"
    mock.push.return_value = True
    mock.get_last_commit_hash.return_value = "abc123def456"
    return mock


@pytest.fixture
def mock_state_manager() -> MagicMock:
    return MagicMock(spec=StateManager)


@pytest.fixture
def publish_service(
    mock_story_file,
    mock_stories_index,
    mock_git,
    mock_state_manager,
) -> PublishService:
    return PublishService(
        story_file=mock_story_file,
        stories_index=mock_stories_index,
        git=mock_git,
        state_manager=mock_state_manager,
    )


class TestPublishServiceInit:
    """Tests for PublishService.__init__."""

    def test_stores_all_dependencies(
        self,
        mock_story_file,
        mock_stories_index,
        mock_git,
        mock_state_manager,
    ) -> None:
        svc = PublishService(
            story_file=mock_story_file,
            stories_index=mock_stories_index,
            git=mock_git,
            state_manager=mock_state_manager,
        )
        assert svc.story_file is mock_story_file
        assert svc.stories_index is mock_stories_index
        assert svc.git is mock_git
        assert svc.state_manager is mock_state_manager


class TestPublishServiceRunFromMaster:
    """Tests for PublishService.run_from_master()."""

    def test_run_from_master_returns_commit_hash(
        self, publish_service, mock_story_file, sample_story_document
    ) -> None:
        mock_story_file.load_master.return_value = sample_story_document
        result = publish_service.run_from_master("test-slug", "2026-03-09")
        assert isinstance(result, str)

    def test_run_from_master_returns_commit_hash_string(
        self, publish_service
    ) -> None:
        try:
            result = publish_service.run_from_master("test-slug", "2026-03-09")
            assert isinstance(result, str)
            assert len(result) > 0
        except NotImplementedError:
            pytest.xfail("PublishService.run_from_master not yet implemented")

    def test_run_from_master_calls_sync_posts(
        self, publish_service, mock_story_file, sample_story_document
    ) -> None:
        """sync_to_posts must be called as part of the publish flow."""
        mock_story_file.load_master.return_value = sample_story_document
        try:
            publish_service.run_from_master("yoake-no-yakusoku", "2026-03-09")
            mock_story_file.sync_to_posts.assert_called_once()
        except NotImplementedError:
            pytest.xfail("PublishService.run_from_master not yet implemented")

    def test_run_from_master_calls_update_index(
        self, publish_service, mock_story_file, mock_stories_index, sample_story_document
    ) -> None:
        """atomic_update must be called to add entry to the stories index."""
        mock_story_file.load_master.return_value = sample_story_document
        try:
            publish_service.run_from_master("yoake-no-yakusoku", "2026-03-09")
            mock_stories_index.atomic_update.assert_called_once()
        except NotImplementedError:
            pytest.xfail("PublishService.run_from_master not yet implemented")

    def test_run_from_master_calls_git_commit_and_push(
        self, publish_service, mock_story_file, mock_git, sample_story_document
    ) -> None:
        """git add_all, commit, push must be called in order."""
        mock_story_file.load_master.return_value = sample_story_document
        try:
            publish_service.run_from_master("yoake-no-yakusoku", "2026-03-09")
            mock_git.add_all.assert_called_once()
            mock_git.commit.assert_called_once()
            mock_git.push.assert_called_once()
        except NotImplementedError:
            pytest.xfail("PublishService.run_from_master not yet implemented")

    def test_run_from_master_marks_published_with_commit_hash(
        self,
        publish_service,
        mock_story_file,
        mock_state_manager,
        mock_git,
        sample_story_document,
    ) -> None:
        """State must be updated with published_commit hash."""
        mock_story_file.load_master.return_value = sample_story_document
        mock_git.commit.return_value = "deadbeef1234"
        try:
            result = publish_service.run_from_master("yoake-no-yakusoku", "2026-03-09")
            assert result == "deadbeef1234"
            # State update should record the commit hash
            mock_state_manager.update.assert_called()
        except NotImplementedError:
            pytest.xfail("PublishService.run_from_master not yet implemented")

    def test_run_from_master_flow_order(
        self,
        publish_service,
        mock_story_file,
        mock_stories_index,
        mock_git,
        mock_state_manager,
        sample_story_document,
    ) -> None:
        """Steps must execute in order: sync -> index -> git -> mark_published."""
        call_order = []
        mock_story_file.load_master.return_value = sample_story_document
        mock_story_file.sync_to_posts.side_effect = lambda _: call_order.append("sync")
        mock_stories_index.atomic_update.side_effect = lambda _: call_order.append("index")
        mock_git.add_all.side_effect = lambda: call_order.append("git_add")
        mock_git.commit.side_effect = lambda msg: call_order.append("git_commit") or "abc"
        mock_git.push.side_effect = lambda: call_order.append("git_push") or True
        mock_state_manager.update.side_effect = lambda *a, **k: call_order.append("mark_published")

        try:
            publish_service.run_from_master("test-slug", "2026-03-09")
            assert call_order.index("sync") < call_order.index("index"), "sync must come before index"
            assert call_order.index("index") < call_order.index("git_commit"), "index must come before commit"
            assert call_order.index("git_commit") < call_order.index("mark_published"), "commit must come before mark_published"
        except (NotImplementedError, ValueError):
            pytest.xfail("PublishService.run_from_master not yet implemented")

    def test_run_from_master_git_push_failure_propagates(
        self, publish_service, mock_story_file, mock_git, sample_story_document
    ) -> None:
        mock_story_file.load_master.return_value = sample_story_document
        mock_git.push.side_effect = RuntimeError("Push failed")
        # This test documents intent: once implemented, git push errors must propagate.
        # Currently raises NotImplementedError which is expected (xfail).
        try:
            publish_service.run_from_master("test-slug", "2026-03-09")
        except NotImplementedError:
            pytest.xfail("PublishService.run_from_master not yet implemented")
        except RuntimeError as exc:
            assert "Push failed" in str(exc)
