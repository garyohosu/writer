from __future__ import annotations

import subprocess


class GitOperations:
    """Wraps git CLI commands for the story repository."""

    def __init__(self, repo_path: str) -> None:
        self.repo_path = repo_path

    def _run(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=check,
        )

    def add_all(self) -> None:
        """Stage all changes (git add -A)."""
        self._run("add", "-A")

    def commit(self, message: str) -> str:
        """Create a commit with *message* and return the commit hash."""
        staged_diff = self._run("diff", "--cached", "--quiet", check=False)
        if staged_diff.returncode == 0:
            return self.get_last_commit_hash()
        self._run("commit", "-m", message)
        return self.get_last_commit_hash()

    def push(self) -> bool:
        """Rebase on remote tip, then push to the remote."""
        self._run("pull", "--rebase", "--autostash")
        self._run("push")
        return True

    def get_last_commit_hash(self) -> str:
        """Return the hash of the most recent commit (HEAD)."""
        return self._run("rev-parse", "HEAD").stdout.strip()
