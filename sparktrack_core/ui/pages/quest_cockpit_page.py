from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from sparktrack_core.database.session import Database
from sparktrack_core.services.app_state import AppStateService
from sparktrack_core.services.feed_narrator import narrate_event
from sparktrack_core.services.quest_cockpit_service import QuestCockpitService
from sparktrack_core.ui.widgets.activity_timeline import ActivityTimeline
from sparktrack_core.ui.widgets.inline_capture import InlineCaptureBar
from sparktrack_core.ui.widgets.progress_widgets import QuestHealthRow


class QuestCockpitPage(QWidget):
    back_requested = Signal()
    quest_updated = Signal()
    capture_burst = Signal()

    def __init__(self, database: Database, app_state: AppStateService) -> None:
        super().__init__()
        self.database = database
        self.app_state = app_state
        self.quest_id: int | None = None

        back = QPushButton("← Back")
        back.clicked.connect(self.back_requested.emit)

        self.title = QLabel("Mission Control")
        self.title.setObjectName("PageTitle")
        self.meta = QLabel()
        self.meta.setObjectName("MetricLabel")
        self.momentum_bar = QLabel()
        self.momentum_bar.setObjectName("MomentumBar")

        self.description = QTextEdit()
        self.description.setReadOnly(True)
        self.description.setMaximumHeight(72)
        self.description.setObjectName("MissionDescription")

        burst_btn = QPushButton("Start Burst")
        burst_btn.clicked.connect(self.capture_burst.emit)
        progress_btn = QPushButton("Mark Progress")
        progress_btn.clicked.connect(self._mark_progress)

        actions = QHBoxLayout()
        actions.addWidget(burst_btn)
        actions.addWidget(progress_btn)
        actions.addStretch(1)

        self.health_widget = QWidget()
        self.health_layout = QVBoxLayout(self.health_widget)
        self.health_layout.setContentsMargins(0, 0, 0, 0)
        self.timeline = ActivityTimeline()
        self.artifacts_panel = QLabel()
        self.artifacts_panel.setWordWrap(True)
        self.artifacts_panel.setObjectName("CardPreview")
        self.principles_panel = QLabel()
        self.principles_panel.setWordWrap(True)
        self.principles_panel.setObjectName("CardPreview")

        self.inline_capture = InlineCaptureBar(database, app_state)
        self.inline_capture.captured.connect(self._reload)

        grid = QGridLayout()
        grid.setSpacing(8)
        grid.addWidget(self._panel("Timeline", self.timeline), 0, 0, 2, 1)
        grid.addWidget(self._panel("Artifacts", self.artifacts_panel), 0, 1)
        grid.addWidget(self._panel("Principles", self.principles_panel), 1, 1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 6)
        layout.setSpacing(6)
        layout.addWidget(back)
        layout.addWidget(self.title)
        layout.addWidget(self.meta)
        layout.addWidget(self.momentum_bar)
        layout.addWidget(self.health_widget)
        layout.addWidget(self.description)
        layout.addLayout(actions)
        layout.addWidget(self.inline_capture)
        layout.addLayout(grid, 1)

    def load_quest(self, quest_id: int) -> None:
        self.quest_id = quest_id
        self.app_state.set_context(quest_id=quest_id)
        self.app_state.push_recent_quest(quest_id)
        self.inline_capture.set_quest_context(quest_id)
        self._reload()

    def _reload(self) -> None:
        if self.quest_id is None:
            return
        with self.database.session_scope() as session:
            snapshot = QuestCockpitService(session).snapshot(self.quest_id)
        if snapshot is None:
            return

        quest = snapshot["quest"]
        field = snapshot["field"]
        path = snapshot["path"]
        self.title.setText(quest.title)
        self.meta.setText(
            f"{path.name if path else ''}  ·  {field.name if field else ''}  ·  "
            f"{quest.status}  ·  {quest.priority}"
        )
        self.momentum_bar.setText(str(snapshot["momentum_bar"]))
        self.description.setPlainText(quest.description or "No mission description yet.")
        while self.health_layout.count():
            item = self.health_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.health_layout.addWidget(QuestHealthRow({
            "title": quest.title,
            "bar": snapshot["momentum_bar"],
            "health": snapshot["momentum_label"],
            "health_color": "#5EA1FF" if snapshot["momentum_score"] >= 3 else "#6B7280",
        }))

        narrated = [narrate_event(event) for event in snapshot["history"]]
        self.timeline.set_events(narrated)

        artifacts = snapshot["artifacts"]
        self.artifacts_panel.setText(
            "\n".join(f"· {a.type}: {a.title}" for a in artifacts) or "No linked artifacts"
        )
        principles = snapshot["principles"]
        self.principles_panel.setText(
            "\n".join(f"· {p.statement}" for p in principles) or "No linked principles"
        )

    def _mark_progress(self) -> None:
        if self.quest_id is None:
            return
        from sparktrack_core.models import Quest

        with self.database.session_scope() as session:
            quest = session.get(Quest, self.quest_id)
            if quest and quest.status == "Active":
                quest.priority = "High"
                session.flush()
        self.quest_updated.emit()
        self._reload()

    def _panel(self, title: str, widget: QWidget) -> QFrame:
        panel = QFrame()
        panel.setObjectName("ListPanel")
        label = QLabel(title)
        label.setObjectName("MetricLabel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.addWidget(label)
        layout.addWidget(widget)
        return panel