from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from sparktrack_core.database.session import Database
from sparktrack_core.services.app_state import AppStateService
from sparktrack_core.services.smart_view_service import VIEW_MODES, SmartViewService
from sparktrack_core.services.workspace_service import WorkspaceService


ENTITY_OPTIONS = [
    ("quest", "Quests"),
    ("field", "Fields"),
    ("burst", "Bursts"),
    ("artifact", "Artifacts"),
    ("resource", "Resources"),
    ("season", "Seasons"),
    ("principle", "Principles"),
]


class SmartViewPage(QWidget):
    open_entity = Signal(str, int)
    open_table = Signal(str)

    def __init__(self, database: Database, app_state: AppStateService) -> None:
        super().__init__()
        self.database = database
        self.app_state = app_state

        title = QLabel("Smart Views")
        title.setObjectName("PageTitle")

        self.entity_combo = QComboBox()
        for key, label in ENTITY_OPTIONS:
            self.entity_combo.addItem(label, key)

        self.view_combo = QComboBox()
        self.view_combo.addItems(VIEW_MODES)

        refresh = QPushButton("Refresh")
        refresh.clicked.connect(self.refresh)

        open_table = QPushButton("Open Raw Table")
        open_table.clicked.connect(self._open_raw_table)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Entity"))
        controls.addWidget(self.entity_combo)
        controls.addWidget(QLabel("View"))
        controls.addWidget(self.view_combo)
        controls.addWidget(refresh)
        controls.addStretch(1)
        controls.addWidget(open_table)

        self.list = QListWidget()
        self.list.itemDoubleClicked.connect(self._on_open)

        self.entity_combo.currentIndexChanged.connect(self.refresh)
        self.view_combo.currentIndexChanged.connect(self.refresh)
        self.app_state.workspace_changed.connect(self.refresh)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 6)
        layout.addWidget(title)
        layout.addLayout(controls)
        layout.addWidget(self.list, 1)
        self.refresh()

    def refresh(self) -> None:
        entity_type = self.entity_combo.currentData()
        view_mode = self.view_combo.currentText()
        with self.database.session_scope() as session:
            scope = WorkspaceService(session).get_workspace(self.app_state.workspace_id)
            rows = SmartViewService(session).list_items(entity_type, view_mode, scope)

        self.list.clear()
        if not rows:
            self.list.addItem("No items match this view")
            return
        for row in rows:
            subtitle = row.get("subtitle", "")
            extra = ""
            if row.get("link_count") is not None:
                extra = f"  ·  {row['link_count']} links"
            if row.get("days_since") is not None:
                extra = f"  ·  {row['days_since']}d idle"
            text = f"{row['title']}  ·  {subtitle}{extra}"
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, (entity_type, row["id"]))
            self.list.addItem(item)

    def _on_open(self, item: QListWidgetItem) -> None:
        data = item.data(Qt.UserRole)
        if data:
            entity_type, entity_id = data
            self.open_entity.emit(entity_type, int(entity_id))

    def _open_raw_table(self) -> None:
        entity_type = self.entity_combo.currentData()
        page_map = {
            "quest": "Quests",
            "field": "Fields",
            "burst": "Bursts",
            "artifact": "Artifacts",
            "resource": "Resources",
            "season": "Seasons",
            "principle": "Principles",
        }
        page = page_map.get(entity_type)
        if page:
            self.open_table.emit(page)