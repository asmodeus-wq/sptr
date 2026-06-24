from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QDialog, QLabel, QLineEdit, QListWidget, QListWidgetItem, QVBoxLayout

from sparktrack_core.services.command_registry import CommandItem, CommandRegistry
from sparktrack_core.services.search_service import SearchResult, SearchService
from sparktrack_core.services.workspace_service import WorkspaceService


class CommandPaletteDialog(QDialog):
    command_selected = Signal(str, str)
    search_result_selected = Signal(str, int)

    def __init__(self, database, app_state) -> None:
        super().__init__()
        self.database = database
        self.app_state = app_state
        self.registry = CommandRegistry()
        self._items: list[CommandItem | SearchResult] = []

        self.setWindowTitle("Command")
        self.setModal(True)
        self.resize(720, 460)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search or type a command…")
        self.search_input.textChanged.connect(self._refresh)

        self.results = QListWidget()
        self.results.setObjectName("CommandResults")
        self.results.itemActivated.connect(self._activate_current)

        hint = QLabel("Primary navigation — ↑↓ · Enter · Esc · try 'Builder' or 'capture'")
        hint.setObjectName("MetricLabel")

        layout = QVBoxLayout(self)
        layout.addWidget(self.search_input)
        layout.addWidget(self.results, 1)
        layout.addWidget(hint)

        self._load_workspace_commands()
        self.search_input.setFocus()
        self._refresh("")

    def _load_workspace_commands(self) -> None:
        with self.database.session_scope() as session:
            workspaces = WorkspaceService(session).list_workspaces()
        commands = [
            CommandItem(
                f"ws_{ws.id}",
                f"Enter {ws.name}",
                f"workspace {ws.name.lower()}",
                "Workspace",
                "switch_workspace",
                payload=ws.id,
            )
            for ws in workspaces
        ]
        self.registry.set_workspace_commands(commands)

    def _refresh(self, query: str = "") -> None:
        if not hasattr(self, "results"):
            return
        self.results.clear()
        self._items = []

        for command in self.registry.filter(query):
            self._items.append(command)
            prefix = "◇ " if command.category == "Workspace" else ""
            if command.ai_ready:
                prefix = "✦ "
            item = QListWidgetItem(f"{prefix}{command.category}: {command.label}")
            self.results.addItem(item)

        if query.strip():
            with self.database.session_scope() as session:
                scope = WorkspaceService(session).get_workspace(self.app_state.workspace_id)
                search_results = SearchService(session).search(query, scope=scope, limit=12)
            for result in search_results:
                self._items.append(result)
                item = QListWidgetItem(f"Find: {result.title} — {result.subtitle}")
                self.results.addItem(item)

        if self.results.count():
            self.results.setCurrentRow(0)

    def _activate_current(self, _: QListWidgetItem | None = None) -> None:
        row = self.results.currentRow()
        if row < 0 or row >= len(self._items):
            return
        selected = self._items[row]
        if isinstance(selected, CommandItem):
            self.command_selected.emit(selected.handler_key, selected.payload)
        else:
            self.search_result_selected.emit(selected.entity_type, selected.entity_id)
        self.accept()

    def keyPressEvent(self, event) -> None:
        if event.key() in {Qt.Key_Down, Qt.Key_Up}:
            current = self.results.currentRow()
            if event.key() == Qt.Key_Down:
                self.results.setCurrentRow(min(current + 1, self.results.count() - 1))
            else:
                self.results.setCurrentRow(max(current - 1, 0))
            return
        if event.key() in {Qt.Key_Return, Qt.Key_Enter}:
            self._activate_current()
            return
        super().keyPressEvent(event)