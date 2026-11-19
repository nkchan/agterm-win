"""Vertical tab sidebar widget."""
from __future__ import annotations
from typing import Callable

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Pango

from .tab_model import Tab, TabModel


class TabSidebar(Gtk.Box):
    """Vertical list of tab buttons with notification indicators."""

    def __init__(
        self,
        model: TabModel,
        on_select: Callable[[str], None],
        on_add: Callable[[], None],
        on_remove: Callable[[str], None],
    ) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.set_margin_top(4)
        self.set_margin_bottom(4)
        self.set_margin_start(4)
        self.set_margin_end(4)
        self.add_css_class("sidebar")

        self._model = model
        self._on_select = on_select
        self._on_add = on_add
        self._on_remove = on_remove

        self._list_box = Gtk.ListBox()
        self._list_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self._list_box.connect("row-activated", self._row_activated)
        self.append(self._list_box)

        # "+" button at the bottom
        add_btn = Gtk.Button(label="+")
        add_btn.connect("clicked", lambda _: self._on_add())
        add_btn.set_margin_top(4)
        self.append(add_btn)

        model.add_observer(self.refresh)
        self.refresh()

    # ------------------------------------------------------------------

    def refresh(self) -> None:
        # Remove all rows
        while (row := self._list_box.get_row_at_index(0)) is not None:
            self._list_box.remove(row)

        for tab in self._model.tabs:
            row = self._make_row(tab)
            self._list_box.append(row)
            if tab.id == self._model.active_id:
                self._list_box.select_row(row)

    def _make_row(self, tab: Tab) -> Gtk.ListBoxRow:
        row = Gtk.ListBoxRow()
        row._tab_id = tab.id  # type: ignore[attr-defined]

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        hbox.set_margin_top(4)
        hbox.set_margin_bottom(4)
        hbox.set_margin_start(6)
        hbox.set_margin_end(6)

        # Notification dot
        dot = Gtk.Label(label="●")
        dot.add_css_class("notify-dot")
        dot.set_visible(tab.notify)
        hbox.append(dot)

        # Label
        lbl = Gtk.Label(label=tab.label)
        lbl.set_ellipsize(Pango.EllipsizeMode.END)
        lbl.set_xalign(0)
        lbl.set_hexpand(True)
        if tab.status == "running":
            lbl.add_css_class("running")
        hbox.append(lbl)

        # Close button
        close_btn = Gtk.Button(label="×")
        close_btn.add_css_class("flat")
        close_btn.connect("clicked", lambda _, tid=tab.id: self._on_remove(tid))
        hbox.append(close_btn)

        row.set_child(hbox)
        return row

    def _row_activated(self, listbox, row) -> None:
        self._on_select(row._tab_id)  # type: ignore[attr-defined]
