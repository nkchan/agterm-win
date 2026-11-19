#!/usr/bin/env bash
# agterm-win installer
# Run inside WSL: bash install.sh
set -euo pipefail

echo "=== agterm-win installer ==="

# --- System dependencies ---
echo "[1/4] Installing system packages..."
sudo apt-get update -q
sudo apt-get install -y -q \
    python3-gi \
    python3-gi-cairo \
    gir1.2-gtk-4.0 \
    gir1.2-vte-2.91 \
    libvte-2.91-gtk4-0 \
    python3-pip

# --- Python package (editable install) ---
echo "[2/4] Installing agterm-win Python package..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
pip3 install --user -e "$SCRIPT_DIR" --quiet

# --- Config dir + hook ---
echo "[3/4] Installing Claude Code hook..."
CONFIG_DIR="$HOME/.config/agterm-win"
mkdir -p "$CONFIG_DIR"
cp "$SCRIPT_DIR/scripts/claude_hook.sh" "$CONFIG_DIR/claude_hook.sh"
chmod +x "$CONFIG_DIR/claude_hook.sh"

echo ""
echo "  To activate Claude Code hooks, merge the following into"
echo "  ~/.claude/settings.json (or run: cp scripts/claude_settings.json ~/.claude/settings.json)"
echo ""
cat "$SCRIPT_DIR/scripts/claude_settings.json"
echo ""

# --- Desktop entry (WSLg) ---
echo "[4/4] Installing desktop entry..."
DESKTOP_DIR="$HOME/.local/share/applications"
mkdir -p "$DESKTOP_DIR"
cat > "$DESKTOP_DIR/agterm-win.desktop" <<EOF
[Desktop Entry]
Name=agterm-win
Comment=AI Agent Terminal for WSL
Exec=python3 -m agterm
Icon=utilities-terminal
Terminal=false
Type=Application
Categories=System;TerminalEmulator;
EOF

echo ""
echo "=== Installation complete ==="
echo "Launch with:  python3 -m agterm"
echo "           or search 'agterm-win' in your app menu (WSLg)"
