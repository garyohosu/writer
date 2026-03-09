from __future__ import annotations

import shutil
import subprocess


class WindowsNotifier:
    """Sends Windows toast notifications via PowerShell."""

    def notify(self, title: str, message: str) -> None:
        """Display a Windows notification with *title* and *message*."""
        if shutil.which("powershell.exe") is None:
            # WSL/Linux-only環境では通知をスキップ（本処理は継続）
            return
        subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", self.build_cmd(title, message)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )

    def build_cmd(self, title: str, message: str) -> str:
        """Return the PowerShell command string for the notification."""
        escaped_title = title.replace("'", "''")
        escaped_message = message.replace("'", "''")
        return (
            "$module = Get-Module -ListAvailable -Name BurntToast; "
            "if ($module) { "
            "Import-Module BurntToast; "
            f"New-BurntToastNotification -Text '{escaped_title}', '{escaped_message}' | Out-Null"
            "} else { "
            f"Write-Output '{escaped_title}: {escaped_message}'"
            " }"
        )
