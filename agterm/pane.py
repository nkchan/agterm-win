"""Terminal pane wrapping Vte.Terminal."""
from __future__ import annotations
import logging
import os
from typing import Callable

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Vte", "2.91")
from gi.repository import GLib, Gtk, Vte

from .osc import extract_notify_message
from .tab_model import Tab

logger = logging.getLogger(__name__)


class TerminalPane(Gtk.Box):
    """A single terminal pane backed by a Vte.Terminal."""

    def __init__(
        self,
        tab: Tab,
        on_notify: Callable[[str, str], None],
    ) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._tab = tab
        self._on_notify = on_notify

        self._terminal = Vte.Terminal()
        self._terminal.set_hexpand(True)
        self._terminal.set_vexpand(True)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_child(self._terminal)
        scrolled.set_hexpand(True)
        scrolled.set_vexpand(True)
        self.append(scrolled)

        self._connect_signals()
        self._spawn_shell()

    # ------------------------------------------------------------------
    # Shell spawn
    # ------------------------------------------------------------------

    def _spawn_shell(self) -> None:
        shell = os.environ.get("SHELL", "/bin/bash")
        self._terminal.spawn_async(
            Vte.PtyFlags.DEFAULT,
            os.path.expanduser("~"),
            [shell],
            None,
            GLib.SpawnFlags.DO_NOT_REAP_CHILD,
            None, None,
            -1,
            None,
            self._on_spawn_done,
        )

    def _on_spawn_done(self, terminal, pid, error):
        if error:
            logger.error("Shell spawn failed: %s", error)

    # ------------------------------------------------------------------
    # Signal connections
    # ------------------------------------------------------------------

    def _connect_signals(self) -> None:
        # Try the modern osc-received signal first (VTE >= 0.60 with OSC support).
        # Fall back to scanning terminal contents on contents-changed.
        try:
            self._terminal.connect("osc-received", self._on_osc_received)
            logger.debug("Using osc-received signal")
        except TypeError:
            logger.debug("osc-received not available, falling back to contents-changed")
            self._terminal.connect("contents-changed", self._on_contents_changed)

    # ------------------------------------------------------------------
    # OSC detection – modern path (VTE osc-received signal)
    # ------------------------------------------------------------------

    def _on_osc_received(self, terminal, code: int, text: str) -> None:
        """Called by VTE when an OSC sequence is received (VTE >= 0.60)."""
        # Reconstruct a minimal OSC string so extract_notify_message can parse it
        synthetic = f"\x1b]{code};{text}\x07"
        message = extract_notify_message(synthetic)
        if message is not None:
            logger.debug("OSC notify (osc-received): %s", message)
            GLib.idle_add(self._on_notify, self._tab.id, message)

    # ------------------------------------------------------------------
    # OSC detection – fallback path (scan terminal text)
    # ------------------------------------------------------------------

    def _on_contents_changed(self, terminal) -> None:
        """Scan the last few lines of terminal output for OSC sequences."""
        try:
            # get_text() returns (text, attrs) – we only need text
            result = terminal.get_text(lambda *a: True)
            if isinstance(result, tuple):
                text = result[0]
            else:
                text = result or ""
        except Exception as exc:
            logger.debug("get_text failed: %s", exc)
            return

        # Only inspect the tail to avoid O(n) scanning on large buffers
        tail = text[-4096:] if len(text) > 4096 else text
        message = extract_notify_message(tail)
        if message is not None:
            logger.debug("OSC notify (contents-changed): %s", message)
            GLib.idle_add(self._on_notify, self._tab.id, message)

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    @property
    def terminal(self) -> Vte.Terminal:
        return self._terminal

    def feed_child(self, data: bytes) -> None:
        self._terminal.feed_child(data)
