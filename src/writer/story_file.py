from __future__ import annotations

import os
import shutil
from dataclasses import asdict

import yaml

from writer.models.story_document import StoryDocument
from writer.models.story_front_matter import StoryFrontMatter


def _render_markdown(doc: StoryDocument) -> str:
    """Render a StoryDocument as a YAML-front-matter Markdown string."""
    fm = asdict(doc.front_matter)
    yaml_str = yaml.dump(fm, allow_unicode=True, sort_keys=False)
    return f"---\n{yaml_str}---\n{doc.body}\n"


def _parse_markdown(content: str) -> StoryDocument:
    """Parse a YAML-front-matter Markdown string into a StoryDocument."""
    if not content.startswith("---"):
        raise ValueError("No YAML front matter found")
    end = content.index("---", 3)
    yaml_block = content[3:end].strip()
    body = content[end + 3:].strip()
    data = yaml.safe_load(yaml_block)
    front_matter = StoryFrontMatter(**data)
    return StoryDocument(front_matter=front_matter, body=body)


def _story_filename(slug: str, date: str) -> str:
    return f"{date}-{slug}.md"


class StoryFile:
    """Handles reading and writing story Markdown files across directories."""

    def __init__(
        self,
        stories_dir: str,
        pending_dir: str,
        posts_dir: str,
    ) -> None:
        self.stories_dir = stories_dir
        self.pending_dir = pending_dir
        self.posts_dir = posts_dir

    def save_master(self, doc: StoryDocument) -> str:
        """Save *doc* to the master stories directory; return the file path."""
        year = doc.front_matter.date[:4]
        year_dir = os.path.join(self.stories_dir, year)
        os.makedirs(year_dir, exist_ok=True)
        filename = _story_filename(doc.front_matter.slug, doc.front_matter.date)
        path = os.path.join(year_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(_render_markdown(doc))
        return path

    def load_master(self, slug: str, date: str) -> StoryDocument:
        """Load and return the master StoryDocument identified by *slug* and *date*."""
        year = date[:4]
        path = os.path.join(self.stories_dir, year, _story_filename(slug, date))
        with open(path, encoding="utf-8") as f:
            content = f.read()
        return _parse_markdown(content)

    def verify(self, path: str) -> bool:
        """Return True if the file at *path* exists and is a valid story document."""
        if not os.path.isfile(path):
            return False
        try:
            with open(path, encoding="utf-8") as f:
                content = f.read()
            _parse_markdown(content)
            return True
        except Exception:
            return False

    def copy_to_pending(self, doc: StoryDocument) -> None:
        """Copy *doc* into the pending review directory."""
        year = doc.front_matter.date[:4]
        dest_dir = os.path.join(self.pending_dir, year)
        os.makedirs(dest_dir, exist_ok=True)
        filename = _story_filename(doc.front_matter.slug, doc.front_matter.date)
        dest = os.path.join(dest_dir, filename)
        with open(dest, "w", encoding="utf-8") as f:
            f.write(_render_markdown(doc))

    def sync_to_posts(self, doc: StoryDocument) -> None:
        """Sync the approved *doc* into the public posts directory."""
        os.makedirs(self.posts_dir, exist_ok=True)
        filename = _story_filename(doc.front_matter.slug, doc.front_matter.date)
        dest = os.path.join(self.posts_dir, filename)
        with open(dest, "w", encoding="utf-8") as f:
            f.write(_render_markdown(doc))
