"""Parse OSC escape sequences from terminal output."""
from __future__ import annotations
import re

# OSC sequences: ESC ] <code> ; <text> BEL  or  ESC ] <code> ; <text> ST
_OSC_RE = re.compile(
    r"\x1b\]"          # ESC ]
    r"(\d+)"           # OSC code
    r";"               # separator
    r"([^\x07\x1b]*)"  # payload (no BEL / ESC)
    r"(?:\x07|\x1b\\)" # BEL or ST terminator
)


def parse_osc(text: str) -> list[tuple[int, str]]:
    """Return list of (code, payload) tuples found in *text*."""
    return [(int(m.group(1)), m.group(2)) for m in _OSC_RE.finditer(text)]


def extract_notify_message(text: str) -> str | None:
    """
    Return the notification message if any OSC 9 / 99 / 777 sequence is found,
    otherwise None.

    OSC 9  ;  <message>          (iTerm2 / ConEmu style)
    OSC 99 ;  title=T;body=B    (Mintty style)
    OSC 777;  notify;title;body (rxvt-unicode / agterm style)
    """
    for code, payload in parse_osc(text):
        if code == 9:
            return payload
        if code == 99:
            # payload: "title=…;body=…" or just the body
            parts = dict(p.split("=", 1) for p in payload.split(";") if "=" in p)
            return parts.get("body", payload)
        if code == 777:
            # payload: "notify;<title>;<body>"
            segments = payload.split(";", 2)
            if len(segments) >= 3 and segments[0] == "notify":
                return segments[2]
            if len(segments) >= 2 and segments[0] == "notify":
                return segments[1]
    return None
