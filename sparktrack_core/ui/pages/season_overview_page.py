from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from sparktrack_core.database.session import Database
from sparktrack_core.services.season_overview_service import SeasonOverviewService
from sparktrack_core.utils.dates import display_datetime


class SeasonOverviewPage(QWidget):
    back_requested = Signal()

    def __init__(self, database: Database) -> None:
        super().__init__()
        self.database = database
        self.season_id: int | None = None

        back = QPushButton("← Back")
        back.clicked.connect(self.back_requested.emit)

        self.title = QLabel("Season Overview")
        self.title.setObjectName("PageTitle")
        self.meta = QLabel()
        self.goals = QTextEdit()
        self.goals.setReadOnly(True)
        self.goals.setMaximumHeight(70)

        self.quest_progress = QListWidget()
        self.reflections = QListWidget()
        self.timeline = QListWidget()

        grid = QGridLayout()
        grid.setSpacing(6)
        grid.addWidget(self._panel("Quest Progress", self.quest_progress), 0, 0)
        grid.addWidget(self._panel("Reflections", self.reflections), 0, 1)
        grid.addWidget(self._panel("Season Timeline", self.timeline), 1, 0, 1, 2)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 6)
        layout.addWidget(back)
        layout.addWidget(self.title)
        layout.addWidget(self.meta)
        layout.addWidget(self.goals)
        layout.addLayout(grid, 1)

    def load_season(self, season_id: int) -> None:
        self.season_id = season_id
        self._reload()

    def _reload(self) -> None:
        if self.season_id is None:
            return
        with self.database.session_scope() as session:
            snapshot = SeasonOverviewService(session).snapshot(self.season_id)
        if snapshot is None:
            return

        season = snapshot["season"]
        self.title.setText(season.name)
        self.meta.setText(
            f"{snapshot['bursts_created']} bursts  ·  {snapshot['artifacts_created']} artifacts  ·  "
            f"{len(snapshot['paths'])} paths  ·  {len(snapshot['fields'])} fields"
        )
        self.goals.setPlainText(snapshot["goals"] or "No season goals defined.")

        self.quest_progress.clear()
        for quest in snapshot["quest_progress"]:
            self.quest_progress.addItem(
                f"{quest['title']}  ·  {quest['status']}  ·  {quest['burst_count']} bursts"
            )

        self.reflections.clear()
        for reflection in snapshot["reflections"]:
            self.reflections.addItem(reflection.title)

        self.timeline.clear()
        for event in snapshot["timeline"]:
            stamp = display_datetime(event.get("timestamp"))
            self.timeline.addItem(
                f"{stamp}  [{event['entity_type']}]  {event['title']}  ·  {event['path_name']}"
            )

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