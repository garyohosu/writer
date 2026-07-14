from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path


class CodexCLI:
    """Thin wrapper around the Codex CLI executable."""

    def __init__(self, executable: str) -> None:
        self.executable = executable

    @staticmethod
    def _clean_output(text: str) -> str:
        s = (text or "").strip()
        if s.startswith("```"):
            lines = s.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            s = "\n".join(lines).strip()
        return s

    def run(self, prompt: str) -> str:
        """Execute Codex in non-interactive mode and return last assistant message."""
        with tempfile.TemporaryDirectory(prefix="writer-codex-") as td:
            out_path = Path(td) / "last_message.txt"
            try:
                result = subprocess.run(
                    [self.executable, "exec", "--output-last-message", str(out_path), prompt],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    check=True,
                )
            except subprocess.CalledProcessError as error:
                stderr = (error.stderr or "").strip()
                stdout = (error.stdout or "").strip()
                detail = stderr or stdout or "no process output captured"
                raise RuntimeError(
                    f"Codex CLI failed with exit code {error.returncode}: {detail}"
                ) from error
            if out_path.exists():
                return self._clean_output(out_path.read_text(encoding="utf-8"))
            return self._clean_output(result.stdout)
