from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
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
from sparktrack_core.services.dashboard_service import DashboardService
from sparktrack_core.utils.dates import display_datetime


class DashboardPage(QWidget):
    quick_action_requested = Signal(str)

    def __init__(self, database: Database, app_state: AppStateService) -> None:
        super().__init__()
        self.database = database
        self.app_state = app_state

        self.title = QLabel("Command Center")
        self.title.setObjectName("PageTitle")

        refresh = QPushButton("Refresh")
        refresh.clicked.connect(self.refresh)

        header = QHBoxLayout()
        header.addWidget(self.title)
        header.addStretch(1)
        header.addWidget(refresh)

        self.context_panel = self._metric_panel("Current Context", "—")
        self.season_panel = self._metric_panel("Current Season", "—")
        self.burst_panel = self._metric_panel("Bursts", "0")
        self.quest_panel = self._metric_panel("Active Quests", "0")

        metrics = QGridLayout()
        metrics.setSpacing(8)
        for index, panel in enumerate(
            [self.context_panel, self.season_panel, self.burst_panel, self.quest_panel]
        ):
            metrics.addWidget(panel, 0, index)

        self.activity_feed = QListWidget()
        self.recent_bursts = QListWidget()
        self.recent_artifacts = QListWidget()
        self.timeline = QListWidget()

        quick_actions = QHBoxLayout()
        for label in ["Capture Idea", "Start Burst", "Add Artifact", "Open Command Palette"]:
            button = QPushButton(label)
            button.clicked.connect(lambda _checked=False, action=label: self.quick_action_requested.emit(action))
            quick_actions.addWidget(button)

        lower = QGridLayout()
        lower.setSpacing(8)
        lower.addWidget(self._list_panel("Recent Activity", self.activity_feed), 0, 0)
        lower.addWidget(self._list_panel("Recent Bursts", self.recent_bursts), 0, 1)
        lower.addWidget(self._list_panel("Recent Artifacts", self.recent_artifacts), 1, 0)
        lower.addWidget(self._list_panel("Activity Timeline", self.timeline), 1, 1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)
        layout.addLayout(header)
        layout.addLayout(metrics)
        layout.addLayout(quick_actions)
        layout.addLayout(lower, 1)

        self.app_state.context_changed.connect(self.refresh)
        self.refresh()

    def refresh(self) -> None:
        with self.database.session_scope() as session:
            snapshot = DashboardService(session).snapshot(self.app_state.context)

        context = snapshot["context"]
        self._set_metric(
            self.context_panel,
            f"{context['path']} → {context['field']} → {context['quest']}",
        )
        self._set_metric(self.season_panel, str(snapshot["current_season"]))
        self._set_metric(self.burst_panel, str(snapshot["total_bursts"]))
        self._set_metric(self.quest_panel, str(snapshot["active_quests"]))

        self._fill_feed(self.activity_feed, snapshot["activity_feed"])
        self._fill_simple(self.recent_bursts, snapshot["recent_bursts"], "title", "minutes")
        self._fill_simple(self.recent_artifacts, snapshot["recent_artifacts"], "title", "type")
        self._fill_feed(self.timeline, snapshot["timeline"])

    def _metric_panel(self, caption: str, value: str) -> QFrame:
        panel = QFrame()
        panel.setObjectName("MetricPanel")
        panel.setMinimumHeight(72)

        value_label = QLabel(value)
        value_label.setObjectName("MetricValue")
        value_label.setWordWrap(True)

        caption_label = QLabel(caption)
        caption_label.setObjectName("MetricLabel")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.addWidget(value_label)
        layout.addWidget(caption_label)
        panel._value_label = value_label  # type: ignore[attr-defined]
        return panel

    def _set_metric(self, panel: QFrame, value: str) -> None:
        panel._value_label.setText(value)  # type: ignore[attr-defined]

    def _list_panel(self, title: str, list_widget: QListWidget) -> QFrame:
        panel = QFrame()
        panel.setObjectName("ListPanel")
        list_widget.setMinimumHeight(160)

        label = QLabel(title)
        label.setObjectName("MetricLabel")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(label)
        layout.addWidget(list_widget)
        return panel

    def _fill_feed(self, widget: QListWidget, rows: list[dict[str, object]]) -> None:
        widget.clear()
        if not rows:
            widget.addItem("No activity yet")
            return
        for row in rows:
            timestamp = row.get("timestamp")
            stamp = display_datetime(timestamp) if timestamp else ""
            text = f"{stamp} · {row.get('title', '')} — {row.get('summary', '')}"
            widget.addItem(QListWidgetItem(text))

    def _fill_simple(self, widget: QListWidget, rows: list[dict[str, object]], a: str, b: str) -> None:
        widget.clear()
        if not rows:
            widget.addItem("Nothing yet")
            return
        for row in rows:
            widget.addItem(QListWidgetItem(f"{row.get(a, '')} ({row.get(b, '')})"))