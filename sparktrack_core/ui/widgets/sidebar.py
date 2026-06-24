from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QListWidget, QListWidgetItem

from sparktrack_core.database.session import Database
from sparktrack_core.models import Artifact, Burst, Field, Path, Principle, Quest, Resource, Season
from sparktrack_core.services.activity_service import ActivityService
from sparktrack_core.services.app_state import AppStateService


SECTIONS: list[tuple[str, list[tuple[str, type | None]]]] = [
    ("Command", [("Focus", None), ("Smart Views", None)]),
    ("Structure", [("Paths", Path), ("Fields", Field), ("Quests", Quest), ("Seasons", Season)]),
    ("Work", [("Bursts", Burst), ("Artifacts", Artifact), ("Resources", Resource), ("Principles", Principle)]),
    ("System", [("Dashboard", None), ("Settings", None)]),
]


class Sidebar(QListWidget):
    navigation_requested = Signal(str)
    favorite_toggled = Signal(str, bool)

    def __init__(self, database: Database, app_state: AppStateService) -> None:
        super().__init__()
        self.database = database
        self.app_state = app_state
        self.setFixedWidth(230)
        self.setSpacing(2)
        self._page_keys: list[str] = []
        self._collapsed: set[str] = set()
        self._counts: dict[str, int] = {}

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.itemDoubleClicked.connect(self._on_double_click)

    def rebuild(self) -> None:
        current_key = self.current_page_key()
        self.clear()
        self._page_keys = []

        with self.database.session_scope() as session:
            self._counts = ActivityService(session).entity_counts()

        for section, items in SECTIONS:
            self._add_header(section)
            if section in self._collapsed:
                continue
            for label, model in items:
                count = self._count_for(label, model)
                display = f"{label} ({count})" if count else label
                if label in self.app_state.pinned:
                    display = f"★ {display}"
                if label in self.app_state.favorites:
                    display = f"♥ {display}"
                self._page_keys.append(label)
                item = QListWidgetItem(display)
                item.setData(Qt.UserRole, label)
                self.addItem(item)

        if current_key:
            self.select_page(current_key)

    def current_page_key(self) -> str | None:
        item = self.currentItem()
        if item is None:
            return None
        return item.data(Qt.UserRole)

    def select_page(self, page_key: str) -> None:
        for row in range(self.count()):
            item = self.item(row)
            if item and item.data(Qt.UserRole) == page_key:
                self.setCurrentRow(row)
                return

    def page_index(self, page_key: str) -> int | None:
        try:
            return self._page_keys.index(page_key)
        except ValueError:
            return None

    def _add_header(self, title: str) -> None:
        item = QListWidgetItem(f"— {title}")
        item.setFlags(Qt.ItemIsEnabled)
        item.setData(Qt.UserRole, f"section:{title}")
        self.addItem(item)

    def _count_for(self, label: str, model: type | None) -> int:
        if model is None:
            return 0
        mapping = {
            Path: "paths",
            Field: "fields",
            Quest: "quests",
            Burst: "bursts",
            Artifact: "artifacts",
            Resource: "resources",
        }
        key = mapping.get(model)
        return self._counts.get(key, 0) if key else 0

    def _show_context_menu(self, position) -> None:
        item = self.itemAt(position)
        if item is None:
            return
        page_key = item.data(Qt.UserRole)
        if not page_key or str(page_key).startswith("section:"):
            return

        from PySide6.QtWidgets import QMenu

        menu = QMenu(self)
        favorite_action = menu.addAction("Toggle Favorite")
        pin_action = menu.addAction("Toggle Pin")
        collapse_action = menu.addAction("Toggle Section Collapse")

        action = menu.exec(self.mapToGlobal(position))
        if action == favorite_action:
            favorites = set(self.app_state.favorites)
            if page_key in favorites:
                favorites.remove(page_key)
            else:
                favorites.add(page_key)
            self.app_state.set_favorites(sorted(favorites))
            self.rebuild()
        elif action == pin_action:
            pinned = set(self.app_state.pinned)
            if page_key in pinned:
                pinned.remove(page_key)
            else:
                pinned.add(page_key)
            self.app_state.set_pinned(sorted(pinned))
            self.rebuild()
        elif action == collapse_action:
            section = self._section_for_item(item)
            if section in self._collapsed:
                self._collapsed.remove(section)
            else:
                self._collapsed.add(section)
            self.rebuild()

    def _section_for_item(self, item: QListWidgetItem) -> str:
        row = self.row(item)
        for index in range(row, -1, -1):
            candidate = self.item(index)
            key = candidate.data(Qt.UserRole)
            if str(key).startswith("section:"):
                return str(key).split(":", 1)[1]
        return "Command"

    def _on_double_click(self, item: QListWidgetItem) -> None:
        page_key = item.data(Qt.UserRole)
        if page_key and not str(page_key).startswith("section:"):
            self.navigation_requested.emit(str(page_key))