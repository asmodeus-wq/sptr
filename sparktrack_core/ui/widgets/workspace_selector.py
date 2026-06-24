from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QFrame, QHBoxLayout, QLabel

from sparktrack_core.database.session import Database
from sparktrack_core.services.app_state import AppStateService
from sparktrack_core.services.workspace_service import WorkspaceService


class WorkspaceSelector(QFrame):
    workspace_changed = Signal(str)

    def __init__(self, database: Database, app_state: AppStateService) -> None:
        super().__init__()
        self.database = database
        self.app_state = app_state

        label = QLabel("Workspace")
        label.setObjectName("ContextChip")

        self.combo = QComboBox()
        self.combo.setMinimumWidth(200)
        self.combo.currentIndexChanged.connect(self._on_changed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(label)
        layout.addWidget(self.combo)

        self.app_state.workspace_changed.connect(self.refresh)
        self.refresh()

    def refresh(self) -> None:
        self.combo.blockSignals(True)
        self.combo.clear()
        with self.database.session_scope() as session:
            workspaces = WorkspaceService(session).list_all_scopes()
        current_index = 0
        for index, workspace in enumerate(workspaces):
            self.combo.addItem(workspace.name, workspace.id)
            if workspace.id == self.app_state.workspace_id:
                current_index = index
        self.combo.setCurrentIndex(current_index)
        self.combo.blockSignals(False)

    def _on_changed(self) -> None:
        workspace_id = self.combo.currentData()
        if workspace_id and workspace_id != self.app_state.workspace_id:
            self.app_state.set_workspace(workspace_id)
            self.workspace_changed.emit(workspace_id)