from __future__ import annotations

from writer.data.stories_index import StoriesIndex
from writer.data.used_themes import UsedThemes
from writer.state import StateManager
from writer.story_file import StoryFile
from writer.utils.git_operations import GitOperations


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
        used_themes: UsedThemes | None = None,
    ) -> None:
        self.story_file = story_file
        self.stories_index = stories_index
        self.git = git
        self.state_manager = state_manager
        self.used_themes = used_themes

    def run_from_master(self, slug: str, date: str) -> str:
        """Publish the story identified by *slug* and *date*.

        Steps:
        1. sync_posts  – copy master to the public posts directory
        2. update_index – add the story entry to the stories index
        3. git_commit_push – stage, commit and push changes
        4. mark_published – persist the commit hash in state

        Returns the git commit hash of the publish commit.
        """
        self.state_manager.update("publish", "in_progress", run_date=date, slug=slug)
        try:
            doc = self.story_file.load_master(slug, date)

            # 1. sync_posts
            self.story_file.sync_to_posts(doc)

            # 2. update_index
            index_entry = doc.to_index_entry()
            self.stories_index.atomic_update(index_entry)
            if self.used_themes is not None:
                self.used_themes.add_published(doc.front_matter.theme, date)

            # 3. git_commit_push
            self.git.add_all()
            commit_hash = self.git.commit(f"publish: {date} {slug}")
            self.git.push()

            # 4. mark_published
            self.state_manager.update(
                "publish",
                "published",
                run_date=date,
                slug=doc.front_matter.slug,
                published_commit=commit_hash,
            )

            return commit_hash
        except Exception:
            self.state_manager.update("publish", "failed", run_date=date, slug=slug)
            raise
