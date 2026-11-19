#!/usr/bin/env bash
# Claude Code hook – sends OSC 777 notify escape + Windows toast
# Usage: claude_hook.sh "<message>"
set -euo pipefail

MESSAGE="${1:-Claude finished}"
TITLE="Claude Code"

# Send OSC 777 notify sequence to the terminal (agterm-win picks this up)
# Format: ESC ] 777 ; notify ; <title> ; <body> BEL
printf '\033]777;notify;%s;%s\007' "$TITLE" "$MESSAGE"

# Also call PowerShell toast directly as a fallback / redundancy
if command -v powershell.exe &>/dev/null; then
    powershell.exe -NoProfile -NonInteractive -Command \
        "Add-Type -AssemblyName System.Windows.Forms; \
         \$n = New-Object System.Windows.Forms.NotifyIcon; \
         \$n.Icon = [System.Drawing.SystemIcons]::Information; \
         \$n.Visible = \$true; \
         \$n.ShowBalloonTip(5000, '$TITLE', '$MESSAGE', [System.Windows.Forms.ToolTipIcon]::Info); \
         Start-Sleep -Milliseconds 5500; \
         \$n.Dispose()" &
fi
