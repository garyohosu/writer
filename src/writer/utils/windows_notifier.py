from __future__ import annotations


class WindowsNotifier:
    """Sends Windows toast notifications via PowerShell."""

    def notify(self, title: str, message: str) -> None:
        """Display a Windows notification with *title* and *message*."""
        raise NotImplementedError

    def build_cmd(self, title: str, message: str) -> str:
        """Return the PowerShell command string for the notification."""
        raise NotImplementedError
