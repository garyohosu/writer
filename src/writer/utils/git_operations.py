from __future__ import annotations


class GitOperations:
    """Wraps git CLI commands for the story repository."""

    def __init__(self, repo_path: str) -> None:
        self.repo_path = repo_path

    def add_all(self) -> None:
        """Stage all changes (git add -A)."""
        raise NotImplementedError

    def commit(self, message: str) -> str:
        """Create a commit with *message* and return the commit hash."""
        raise NotImplementedError

    def push(self) -> bool:
        """Push to the remote; return True on success."""
        raise NotImplementedError

    def get_last_commit_hash(self) -> str:
        """Return the hash of the most recent commit (HEAD)."""
        raise NotImplementedError
