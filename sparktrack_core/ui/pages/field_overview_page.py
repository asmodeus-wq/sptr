from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from sparktrack_core.database.session import Database
from sparktrack_core.services.field_overview_service import FieldOverviewService
from sparktrack_core.utils.dates import display_datetime


class FieldOverviewPage(QWidget):
    back_requested = Signal()
    open_quest = Signal(int)

    def __init__(self, database: Database) -> None:
        super().__init__()
        self.database = database
        self.field_id: int | None = None

        back = QPushButton("← Back")
        back.clicked.connect(self.back_requested.emit)

        self.title = QLabel("Field Overview")
        self.title.setObjectName("PageTitle")
        self.meta = QLabel()
        self.momentum = QLabel()

        self.active_quests = QListWidget()
        self.dormant_quests = QListWidget()
        self.activity = QListWidget()
        self.artifacts = QListWidget()

        self.active_quests.itemDoubleClicked.connect(self._open_quest)

        grid = QGridLayout()
        grid.setSpacing(6)
        grid.addWidget(self._panel("Active Quests", self.active_quests), 0, 0)
        grid.addWidget(self._panel("Dormant Quests", self.dormant_quests), 0, 1)
        grid.addWidget(self._panel("Recent Activity", self.activity), 1, 0)
        grid.addWidget(self._panel("Knowledge Produced", self.artifacts), 1, 1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 6)
        layout.addWidget(back)
        layout.addWidget(self.title)
        layout.addWidget(self.meta)
        layout.addWidget(self.momentum)
        layout.addLayout(grid, 1)

    def load_field(self, field_id: int) -> None:
        self.field_id = field_id
        self._reload()

    def _reload(self) -> None:
        if self.field_id is None:
            return
        with self.database.session_scope() as session:
            snapshot = FieldOverviewService(session).snapshot(self.field_id)
        if snapshot is None:
            return

        field = snapshot["field"]
        path = snapshot["path"]
        self.title.setText(field.name)
        self.meta.setText(f"{path.name if path else '—'}  ·  {field.status}")
        self.momentum.setText(
            f"Momentum: {snapshot['momentum_bar']} ({snapshot['momentum_label']})  ·  "
            f"{snapshot['resources_consumed']} resources linked"
        )

        self.active_quests.clear()
        for quest in snapshot["active_quests"]:
            item_text = f"{quest.title}  ·  {quest.priority}"
            self.active_quests.addItem(item_text)
            self.active_quests.item(self.active_quests.count() - 1).setData(
                Qt.UserRole, quest.id
            )

        self.dormant_quests.clear()
        for quest in snapshot["dormant_quests"]:
            self.dormant_quests.addItem(quest.title)

        self.activity.clear()
        for event in snapshot["recent_activity"]:
            stamp = display_datetime(event.get("timestamp"))
            self.activity.addItem(f"{stamp}  [{event['entity_type']}]  {event['title']}")

        self.artifacts.clear()
        for artifact in snapshot["artifacts"]:
            self.artifacts.addItem(f"{artifact.type}: {artifact.title}")

    def _open_quest(self, item) -> None:
        quest_id = item.data(Qt.UserRole)
        if quest_id:
            self.open_quest.emit(int(quest_id))

    def _panel(self, title: str, widget: QListWidget) -> QFrame:
        panel = QFrame()
        panel.setObjectName("ListPanel")
        label = QLabel(title)
        label.setObjectName("MetricLabel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.addWidget(label)
        layout.addWidget(widget)
        return panel