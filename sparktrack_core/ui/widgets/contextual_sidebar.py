from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QVBoxLayout, QWidget

from sparktrack_core.database.session import Database
from sparktrack_core.models import Quest
from sparktrack_core.services.app_state import AppStateService
from sparktrack_core.services.context_resolver import ContextResolver
from sparktrack_core.services.workspace_service import WorkspaceService


class ContextualSidebar(QWidget):
    navigate = Signal(str)
    quick_capture = Signal()

    def __init__(self, database: Database, app_state: AppStateService) -> None:
        super().__init__()
        self.database = database
        self.app_state = app_state
        self.setFixedWidth(220)
        self._rebuilding = False

        self.list = QListWidget()
        self.list.currentItemChanged.connect(self._on_item_changed)
        self.list.itemDoubleClicked.connect(self._on_double_click)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.list)

        self.app_state.workspace_changed.connect(self.rebuild)
        self.app_state.context_changed.connect(self.rebuild)
        self.rebuild()

    def rebuild(self) -> None:
        self._rebuilding = True
        self.list.blockSignals(True)
        try:
            current = self._current_key()
            self.list.clear()

            self._add_header("NOW")
            self._add_item("now", "Now")

            self._add_header("WORKSPACES")
            with self.database.session_scope() as session:
                workspaces = WorkspaceService(session).list_workspaces()
                labels = ContextResolver(session).labels(self.app_state.context)

            pinned = set(self.app_state.pinned_workspaces)
            ordered = sorted(workspaces, key=lambda w: (w.id not in pinned, w.name))
            for workspace in ordered:
                prefix = "★ " if workspace.id in pinned else ""
                active = " ▸" if workspace.id == self.app_state.workspace_id else ""
                self._add_item(
                    f"workspace:{workspace.id}",
                    f"{prefix}{workspace.name}{active}",
                )

            self._add_header("CONTEXT")
            self._add_item(f"ctx:quest", f"Quest: {labels['quest']}", enabled_only=True)
            self._add_item(f"ctx:season", f"Season: {labels['season']}", enabled_only=True)

            if self.app_state.recent_quests:
                self._add_header("RECENT")
                with self.database.session_scope() as session:
                    for quest_id in self.app_state.recent_quests[:5]:
                        quest = session.get(Quest, quest_id)
                        if quest:
                            self._add_item(f"quest:{quest_id}", quest.title[:28])

            self._add_header("ACTIONS")
            self._add_item("capture", "＋ Quick Capture")
            self._add_item("command", "⌘ Command Palette")

            self._add_header("SYSTEM")
            self._add_item("settings", "Settings")

            self._select_key(current or f"workspace:{self.app_state.workspace_id}" if self.app_state.workspace_id not in ("all", "") else "now")
        finally:
            self.list.blockSignals(False)
            self._rebuilding = False

    def _add_header(self, title: str) -> None:
        item = QListWidgetItem(f"  {title}")
        item.setFlags(Qt.ItemIsEnabled)
        item.setData(Qt.UserRole, f"header:{title}")
        self.list.addItem(item)

    def _add_item(self, key: str, label: str, *, enabled_only: bool = False) -> None:
        item = QListWidgetItem(f"  {label}")
        if enabled_only:
            item.setFlags(Qt.ItemIsEnabled)
        item.setData(Qt.UserRole, key)
        self.list.addItem(item)

    def _current_key(self) -> str | None:
        item = self.list.currentItem()
        return str(item.data(Qt.UserRole)) if item else None

    def _select_key(self, key: str) -> None:
        for row in range(self.list.count()):
            item = self.list.item(row)
            if item and item.data(Qt.UserRole) == key:
                self.list.setCurrentRow(row)
                return

    def _on_item_changed(self, current: QListWidgetItem | None, _prev) -> None:
        if self._rebuilding or current is None:
            return
        key = str(current.data(Qt.UserRole) or "")
        if key.startswith("header:") or key.startswith("ctx:"):
            return

        if key == "now":
            self.navigate.emit("Now")
        elif key.startswith("workspace:"):
            workspace_id = key.split(":", 1)[1]
            if workspace_id != self.app_state.workspace_id:
                self.app_state.set_workspace(workspace_id)
            self.navigate.emit("Now")
        elif key.startswith("quest:"):
            self.navigate.emit(f"quest:{int(key.split(':')[1])}")
        elif key == "capture":
            self.quick_capture.emit()
        elif key == "command":
            self.navigate.emit("command")
        elif key == "settings":
            self.navigate.emit("Settings")

    def _on_double_click(self, item: QListWidgetItem) -> None:
        key = str(item.data(Qt.UserRole) or "")
        if not key.startswith("workspace:"):
            return
        workspace_id = key.split(":", 1)[1]
        pinned = set(self.app_state.pinned_workspaces)
        if workspace_id in pinned:
            pinned.remove(workspace_id)
        else:
            pinned.add(workspace_id)
        self.app_state.set_pinned_workspaces(sorted(pinned))
        self.rebuild()