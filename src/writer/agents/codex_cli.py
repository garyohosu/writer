from __future__ import annotations

import subprocess
import tempfile
import time
from pathlib import Path


class CodexCLI:
    """Thin wrapper around the Codex CLI executable."""

    def __init__(self, executable: str, max_attempts: int = 3) -> None:
        self.executable = executable
        self.max_attempts = max_attempts

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
            last_result: subprocess.CompletedProcess[str] | None = None
            attempts = max(1, self.max_attempts)

            for attempt in range(1, attempts + 1):
                result = subprocess.run(
                    [self.executable, "exec", "--output-last-message", str(out_path), "-"],
                    input=prompt,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                )
                last_result = result

                if out_path.exists():
                    output = self._clean_output(out_path.read_text(encoding="utf-8"))
                    if output:
                        return output

                if result.returncode == 0:
                    return self._clean_output(result.stdout)

                if attempt < attempts:
                    time.sleep(min(attempt, 5))

            if last_result is None:
                raise RuntimeError("Codex CLI was not executed")

            stderr = (last_result.stderr or "").strip()
            stdout = (last_result.stdout or "").strip()
            detail = self._truncate(stderr or stdout or "no process output captured")
            raise RuntimeError(
                f"Codex CLI failed after {attempts} attempt(s) "
                f"with exit code {last_result.returncode}: {detail}"
            )

    @staticmethod
    def _truncate(text: str, limit: int = 2000) -> str:
        if len(text) <= limit:
            return text
        return f"{text[:limit]}... [truncated {len(text) - limit} chars]"
