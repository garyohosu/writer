from __future__ import annotations

import platform
import shutil
import subprocess


class WindowsNotifier:
    """Sends Windows toast notifications via PowerShell."""

    def notify(self, title: str, message: str) -> None:
        """Display a Windows notification with *title* and *message*."""
        # 通知は補助機能。Windows以外では何もしない。
        if platform.system() != "Windows":
            return

        powershell = shutil.which("powershell.exe") or shutil.which("powershell")
        if powershell is None:
            return

        # 通知失敗で公開処理全体を止めない
        subprocess.run(
            [powershell, "-NoProfile", "-Command", self.build_cmd(title, message)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
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
