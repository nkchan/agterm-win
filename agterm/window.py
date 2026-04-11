"""Main application window."""
from __future__ import annotations
import logging

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

from .notifier import send_windows_toast
from .pane import TerminalPane
from .tab_model import TabModel
from .tab_sidebar import TabSidebar

logger = logging.getLogger(__name__)

CSS = b"""
.sidebar { background-color: #1e1e2e; }
.notify-dot { color: #f38ba8; font-size: 10px; }
.running { font-style: italic; color: #a6e3a1; }
"""


class AgTermWindow(Gtk.ApplicationWindow):
    def __init__(self, app: Gtk.Application) -> None:
        super().__init__(application=app, title="agterm-win")
        self.set_default_size(1200, 700)

        self._load_css()

        self._model = TabModel()
        self._panes: dict[str, TerminalPane] = {}

        # Layout: sidebar | content
        hpaned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        hpaned.set_position(200)

        self._sidebar = TabSidebar(
            self._model,
            on_select=self._on_tab_select,
            on_add=self._on_tab_add,
            on_remove=self._on_tab_remove,
        )
        hpaned.set_start_child(self._sidebar)
        hpaned.set_resize_start_child(False)

        self._stack = Gtk.Stack()
        self._stack.set_transition_type(Gtk.StackTransitionType.NONE)
        hpaned.set_end_child(self._stack)

        self.set_child(hpaned)

        # Open initial tab
        self._on_tab_add()

    # ------------------------------------------------------------------
    # CSS
    # ------------------------------------------------------------------

    def _load_css(self) -> None:
        provider = Gtk.CssProvider()
        provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_display(
            self.get_display(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

    # ------------------------------------------------------------------
    # Tab lifecycle
    # ------------------------------------------------------------------

    def _on_tab_add(self) -> None:
        tab = self._model.add_tab()
        pane = TerminalPane(tab, on_notify=self._on_agent_notify)
        self._panes[tab.id] = pane
        self._stack.add_named(pane, tab.id)
        self._model.set_active(tab.id)
        self._stack.set_visible_child_name(tab.id)

    def _on_tab_select(self, tab_id: str) -> None:
        self._model.set_active(tab_id)
        self._model.clear_notify(tab_id)
        self._stack.set_visible_child_name(tab_id)

    def _on_tab_remove(self, tab_id: str) -> None:
        if len(self._model.tabs) <= 1:
            return  # keep at least one tab
        pane = self._panes.pop(tab_id, None)
        if pane:
            self._stack.remove(pane)
        self._model.remove_tab(tab_id)
        active = self._model.active_id
        if active:
            self._stack.set_visible_child_name(active)

    # ------------------------------------------------------------------
    # Notification handler (called from TerminalPane via GLib.idle_add)
    # ------------------------------------------------------------------

    def _on_agent_notify(self, tab_id: str, message: str) -> None:
        logger.info("Agent notify tab=%s msg=%s", tab_id, message)
        tab = self._model.get_tab(tab_id)
        if tab is None:
            return

        self._model.set_notify(tab_id, message)

        title = f"agterm [{tab.label}]"
        send_windows_toast(title, message)
