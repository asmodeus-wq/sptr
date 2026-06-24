from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from sparktrack_core.database.session import Database
from sparktrack_core.services.app_state import AppStateService
from sparktrack_core.services.now_service import NowService
from sparktrack_core.services.workspace_service import WorkspaceService
from sparktrack_core.ui.widgets.activity_timeline import ActivityTimeline
from sparktrack_core.ui.widgets.inline_capture import InlineCaptureBar
from sparktrack_core.ui.widgets.progress_widgets import ConsistencyBadge, HeatmapWidget, QuestHealthRow


class NowPage(QWidget):
    open_quest = Signal(int)
    open_entity = Signal(str, int)

    def __init__(self, database: Database, app_state: AppStateService) -> None:
        super().__init__()
        self.database = database
        self.app_state = app_state

        self.focus_label = QLabel()
        self.focus_label.setObjectName("NowFocus")

        title = QLabel("Now")
        title.setObjectName("PageTitle")
        subtitle = QLabel("What matters right now")
        subtitle.setObjectName("MetricLabel")

        header = QVBoxLayout()
        header.setSpacing(2)
        header.addWidget(title)
        header.addWidget(subtitle)
        header.addWidget(self.focus_label)

        self.inline_capture = InlineCaptureBar(database, app_state)
        self.inline_capture.captured.connect(self.refresh)

        self.active_quests = QListWidget()
        self.attention_list = QListWidget()
        self.insights_list = QListWidget()
        self.decisions_list = QListWidget()
        self.timeline = ActivityTimeline()
        self.heatmap = HeatmapWidget()
        self.consistency = ConsistencyBadge()
        self.health_container = QWidget()
        self.health_layout = QVBoxLayout(self.health_container)
        self.health_layout.setContentsMargins(0, 0, 0, 0)
        self.health_layout.setSpacing(4)

        self.active_quests.itemDoubleClicked.connect(self._open_quest)
        self.timeline.card_clicked.connect(self.open_entity.emit)

        scroll_content = QWidget()
        grid = QGridLayout(scroll_content)
        grid.setContentsMargins(6, 4, 6, 4)
        grid.setSpacing(8)

        grid.addWidget(self._panel("Active Quests", self.active_quests), 0, 0)
        grid.addWidget(self._panel("Needs Attention", self.attention_list), 0, 1)
        grid.addWidget(self._panel("Activity", self.timeline), 1, 0, 1, 2)
        grid.addWidget(self._panel("Recent Insights", self.insights_list), 2, 0)
        grid.addWidget(self._panel("Upcoming Decisions", self.decisions_list), 2, 1)

        progress_row = QHBoxLayout()
        progress_row.addWidget(self.consistency)
        progress_row.addWidget(self.heatmap, 1)
        progress_panel = QFrame()
        progress_panel.setObjectName("ListPanel")
        progress_layout = QVBoxLayout(progress_panel)
        progress_layout.setContentsMargins(8, 6, 8, 6)
        progress_layout.addWidget(QLabel("Momentum & Consistency"))
        progress_layout.addLayout(progress_row)
        progress_layout.addWidget(self.health_container)
        grid.addWidget(progress_panel, 3, 0, 1, 2)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(scroll_content)
        scroll.setFrameShape(QFrame.NoFrame)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 6)
        layout.setSpacing(6)
        layout.addLayout(header)
        layout.addWidget(self.inline_capture)
        layout.addWidget(scroll, 1)

        self.app_state.context_changed.connect(self.refresh)
        self.app_state.workspace_changed.connect(self.refresh)
        self.refresh()

    def refresh(self) -> None:
        with self.database.session_scope() as session:
            scope = WorkspaceService(session).get_workspace(self.app_state.workspace_id)
            snapshot = NowService(session).snapshot(scope, self.app_state.context)

        focus = snapshot["current_focus"]
        self.focus_label.setText(
            f"  {focus['workspace']}  ·  {focus['quest']}  ·  {focus['season']}"
        )

        self._fill_quests(snapshot["active_quests"])
        self._fill_attention(snapshot["needs_attention"])
        self.timeline.set_events(snapshot["recent_progress"])
        self._fill_insights(snapshot["recent_insights"])
        self._fill_decisions(snapshot["upcoming_decisions"])
        self.heatmap.set_data(snapshot["heatmap"])
        self.consistency.set_data(snapshot["consistency"])
        self._fill_health(snapshot["quest_health"])

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

    def _fill_quests(self, quests: list[dict]) -> None:
        self.active_quests.clear()
        if not quests:
            self.active_quests.addItem("No active quests — capture something to begin")
            return
        for quest in quests[:10]:
            text = (
                f"{quest['title']}\n"
                f"{quest['path_name']} → {quest['field_name']}  ·  "
                f"{quest['progress_label']}  ·  {quest['momentum_bar']}"
            )
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, quest["id"])
            self.active_quests.addItem(item)

    def _fill_attention(self, neglect: dict) -> None:
        self.attention_list.clear()
        count = 0
        for quest in neglect.get("quests", [])[:4]:
            self.attention_list.addItem(
                f"Stalled {quest['days_since']}d — {quest['title']}"
            )
            count += 1
        for field in neglect.get("fields", [])[:2]:
            self.attention_list.addItem(f"Dormant field — {field['title']}")
            count += 1
        if count == 0:
            self.attention_list.addItem("Nothing needs attention right now")

    def _fill_insights(self, insights: list[dict]) -> None:
        self.insights_list.clear()
        if not insights:
            self.insights_list.addItem("No recent insights")
            return
        for insight in insights:
            self.insights_list.addItem(
                f"{insight['headline']}  ·  {insight['time_ago']}"
            )

    def _fill_decisions(self, decisions: list[dict]) -> None:
        self.decisions_list.clear()
        if not decisions:
            self.decisions_list.addItem("No upcoming deadlines")
            return
        for decision in decisions:
            self.decisions_list.addItem(
                f"{decision['title']}  ·  {decision['days_left']}d left"
            )

    def _fill_health(self, health_rows: list[dict]) -> None:
        while self.health_layout.count():
            item = self.health_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for row in health_rows[:6]:
            self.health_layout.addWidget(QuestHealthRow(row))

    def _open_quest(self, item: QListWidgetItem) -> None:
        quest_id = item.data(Qt.UserRole)
        if quest_id:
            self.open_quest.emit(int(quest_id))