"""Send Windows toast notifications from WSL via PowerShell interop."""
from __future__ import annotations
import logging
import os
import subprocess

logger = logging.getLogger(__name__)


def _is_wsl() -> bool:
    return "microsoft" in (open("/proc/version").read().lower()
                           if os.path.exists("/proc/version") else "")


def send_windows_toast(title: str, message: str) -> None:
    if not _is_wsl():
        logger.info("Not running in WSL – skipping toast: [%s] %s", title, message)
        return

    ps_script = (
        "Add-Type -AssemblyName System.Windows.Forms; "
        "$n = New-Object System.Windows.Forms.NotifyIcon; "
        "$n.Icon = [System.Drawing.SystemIcons]::Information; "
        "$n.Visible = $true; "
        f"$n.ShowBalloonTip(5000, '{_esc(title)}', '{_esc(message)}', "
        "[System.Windows.Forms.ToolTipIcon]::Info); "
        "Start-Sleep -Milliseconds 5500; "
        "$n.Dispose()"
    )
    try:
        subprocess.Popen(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps_script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        logger.warning("powershell.exe not found – cannot send toast")
    except Exception as exc:
        logger.warning("Toast failed: %s", exc)


def _esc(s: str) -> str:
    """Escape single quotes for PowerShell string embedding."""
    return s.replace("'", "''")
