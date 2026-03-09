"""Tests for writer.story_file.StoryFile."""
from __future__ import annotations

import pytest

from writer.story_file import StoryFile
from writer.models.story_document import StoryDocument


@pytest.fixture
def story_file(tmp_path) -> StoryFile:
    stories_dir = tmp_path / "stories"
    pending_dir = tmp_path / "pending"
    posts_dir = tmp_path / "posts"
    for d in [stories_dir, pending_dir, posts_dir]:
        d.mkdir()
    return StoryFile(
        stories_dir=str(stories_dir),
        pending_dir=str(pending_dir),
        posts_dir=str(posts_dir),
    )


class TestStoryFileInit:
    """Tests for StoryFile.__init__."""

    def test_stores_directories(self, tmp_path) -> None:
        sf = StoryFile(
            stories_dir="/stories",
            pending_dir="/pending",
            posts_dir="/posts",
        )
        assert sf.stories_dir == "/stories"
        assert sf.pending_dir == "/pending"
        assert sf.posts_dir == "/posts"


class TestStoryFileSaveMaster:
    """Tests for StoryFile.save_master()."""

    def test_save_master_returns_string_path_inline(
        self, story_file, sample_story_document
    ) -> None:
        result = story_file.save_master(sample_story_document)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_save_master_returns_string_path(
        self, story_file, sample_story_document
    ) -> None:
        try:
            result = story_file.save_master(sample_story_document)
            assert isinstance(result, str)
            assert len(result) > 0
        except NotImplementedError:
            pytest.xfail("StoryFile.save_master not yet implemented")

    def test_save_master_creates_file_on_disk(
        self, story_file, sample_story_document
    ) -> None:
        import os
        try:
            path = story_file.save_master(sample_story_document)
            assert os.path.exists(path)
        except NotImplementedError:
            pytest.xfail("StoryFile.save_master not yet implemented")

    def test_save_master_does_not_duplicate_date_prefix_in_filename(
        self, story_file, sample_story_document
    ) -> None:
        import os

        sample_story_document.front_matter.slug = "2026-03-09-midnight-cat"
        path = story_file.save_master(sample_story_document)
        assert os.path.basename(path) == "2026-03-09-midnight-cat.md"


class TestStoryFileLoadMaster:
    """Tests for StoryFile.load_master()."""

    def test_load_master_missing_file_raises(self, story_file) -> None:
        with pytest.raises((FileNotFoundError, OSError)):
            story_file.load_master("test-slug", "2026-03-09")

    def test_load_master_returns_story_document(
        self, story_file, sample_story_document
    ) -> None:
        try:
            story_file.save_master(sample_story_document)
            result = story_file.load_master(
                sample_story_document.front_matter.slug,
                sample_story_document.front_matter.date,
            )
            assert isinstance(result, StoryDocument)
            assert result.front_matter.slug == sample_story_document.front_matter.slug
        except NotImplementedError:
            pytest.xfail("StoryFile.load_master not yet implemented")


class TestStoryFileVerify:
    """Tests for StoryFile.verify()."""

    def test_verify_nonexistent_returns_false(self, story_file) -> None:
        assert story_file.verify("/nonexistent/path.md") is False

    def test_verify_returns_false_for_nonexistent_file(self, story_file) -> None:
        try:
            result = story_file.verify("/nonexistent/path.md")
            assert result is False
        except NotImplementedError:
            pytest.xfail("StoryFile.verify not yet implemented")

    def test_verify_returns_true_for_valid_file(
        self, story_file, sample_story_document
    ) -> None:
        try:
            path = story_file.save_master(sample_story_document)
            result = story_file.verify(path)
            assert result is True
        except NotImplementedError:
            pytest.xfail("StoryFile.verify not yet implemented")


class TestStoryFileCopyToPending:
    """Tests for StoryFile.copy_to_pending()."""

    def test_copy_to_pending_creates_file(
        self, story_file, sample_story_document
    ) -> None:
        story_file.copy_to_pending(sample_story_document)
        import os
        year = sample_story_document.front_matter.date[:4]
        pending_dir = os.path.join(story_file.pending_dir, year)
        assert len(os.listdir(pending_dir)) > 0

    def test_copy_to_pending_creates_file_in_pending_dir(
        self, story_file, sample_story_document, tmp_path
    ) -> None:
        import os
        try:
            story_file.copy_to_pending(sample_story_document)
            pending_files = os.listdir(story_file.pending_dir)
            assert len(pending_files) > 0
        except NotImplementedError:
            pytest.xfail("StoryFile.copy_to_pending not yet implemented")


class TestStoryFileSyncToPosts:
    """Tests for StoryFile.sync_to_posts()."""

    def test_sync_to_posts_creates_file(
        self, story_file, sample_story_document
    ) -> None:
        story_file.sync_to_posts(sample_story_document)
        import os
        assert len(os.listdir(story_file.posts_dir)) > 0

    def test_sync_to_posts_creates_file_in_posts_dir(
        self, story_file, sample_story_document, tmp_path
    ) -> None:
        import os
        try:
            story_file.sync_to_posts(sample_story_document)
            posts_files = os.listdir(story_file.posts_dir)
            assert len(posts_files) > 0
        except NotImplementedError:
            pytest.xfail("StoryFile.sync_to_posts not yet implemented")
