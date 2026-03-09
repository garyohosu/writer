from __future__ import annotations

import subprocess


class CodexCLI:
    """Thin wrapper around the Codex CLI executable."""

    def __init__(self, executable: str) -> None:
        self.executable = executable

    def run(self, prompt: str) -> str:
        """Execute the Codex CLI with *prompt* and return the raw text output."""
        result = subprocess.run(
            [self.executable, prompt],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )
        return result.stdout
