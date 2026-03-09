from __future__ import annotations

from writer.story_file import StoryFile
from writer.data.stories_index import StoriesIndex
from writer.utils.git_operations import GitOperations
from writer.state import StateManager


class PublishService:
    """Orchestrates the publish flow: sync -> index -> git -> mark published.

    Flow: sync_posts -> update_index -> git_commit_push -> mark_published
    """

    def __init__(
        self,
        story_file: StoryFile,
        stories_index: StoriesIndex,
        git: GitOperations,
        state_manager: StateManager,
    ) -> None:
        self.story_file = story_file
        self.stories_index = stories_index
        self.git = git
        self.state_manager = state_manager

    def run_from_master(self, slug: str, date: str) -> str:
        """Publish the story identified by *slug* and *date*.

        Steps:
        1. sync_posts  – copy master to the public posts directory
        2. update_index – add the story entry to the stories index
        3. git_commit_push – stage, commit and push changes
        4. mark_published – persist the commit hash in state

        Returns the git commit hash of the publish commit.
        """
        doc = self.story_file.load_master(slug, date)

        # 1. sync_posts
        self.story_file.sync_to_posts(doc)

        # 2. update_index
        index_entry = doc.to_index_entry()
        self.stories_index.atomic_update(index_entry)

        # 3. git_commit_push
        self.git.add_all()
        commit_hash = self.git.commit(f"publish: {date} {slug}")
        self.git.push()

        # 4. mark_published
        self.state_manager.update("publish", "published", published_commit=commit_hash)

        return commit_hash
