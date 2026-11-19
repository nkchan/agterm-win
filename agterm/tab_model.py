from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Literal
import uuid


@dataclass
class Tab:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    label: str = "Terminal"
    branch: str = ""
    workdir: str = ""
    port: int = 0
    status: Literal["idle", "running"] = "idle"
    notify: bool = False
    notify_message: str = ""
    split: bool = False


class TabModel:
    def __init__(self) -> None:
        self._tabs: list[Tab] = []
        self._active_id: str | None = None
        self._observers: list[Callable[[], None]] = []

    # --- observer ---

    def add_observer(self, cb: Callable[[], None]) -> None:
        self._observers.append(cb)

    def _notify(self) -> None:
        for cb in self._observers:
            cb()

    # --- CRUD ---

    def add_tab(self, label: str = "Terminal") -> Tab:
        tab = Tab(label=label)
        self._tabs.append(tab)
        if self._active_id is None:
            self._active_id = tab.id
        self._notify()
        return tab

    def remove_tab(self, tab_id: str) -> None:
        self._tabs = [t for t in self._tabs if t.id != tab_id]
        if self._active_id == tab_id:
            self._active_id = self._tabs[-1].id if self._tabs else None
        self._notify()

    def get_tab(self, tab_id: str) -> Tab | None:
        return next((t for t in self._tabs if t.id == tab_id), None)

    @property
    def tabs(self) -> list[Tab]:
        return list(self._tabs)

    # --- active ---

    @property
    def active_id(self) -> str | None:
        return self._active_id

    def set_active(self, tab_id: str) -> None:
        if any(t.id == tab_id for t in self._tabs):
            self._active_id = tab_id
            self._notify()

    # --- update helpers ---

    def set_notify(self, tab_id: str, message: str = "") -> None:
        tab = self.get_tab(tab_id)
        if tab:
            tab.notify = True
            tab.notify_message = message
            self._notify()

    def clear_notify(self, tab_id: str) -> None:
        tab = self.get_tab(tab_id)
        if tab:
            tab.notify = False
            tab.notify_message = ""
            self._notify()

    def set_status(self, tab_id: str, status: Literal["idle", "running"]) -> None:
        tab = self.get_tab(tab_id)
        if tab:
            tab.status = status
            self._notify()
