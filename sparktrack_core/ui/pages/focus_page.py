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
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from sparktrack_core.database.session import Database
from sparktrack_core.services.app_state import AppStateService
from sparktrack_core.services.focus_service import FocusService
from sparktrack_core.services.workspace_service import WorkspaceService
from sparktrack_core.ui.widgets.inline_capture import InlineCaptureBar
from sparktrack_core.utils.dates import display_datetime


class FocusPage(QWidget):
    open_quest = Signal(int)
    capture_to_quest = Signal(int)

    def __init__(self, database: Database, app_state: AppStateService) -> None:
        super().__init__()
        self.database = database
        self.app_state = app_state

        title = QLabel("Focus Mode")
        title.setObjectName("PageTitle")
        subtitle = QLabel("What matters right now")
        subtitle.setObjectName("MetricLabel")

        header = QVBoxLayout()
        header.setSpacing(2)
        header.addWidget(title)
        header.addWidget(subtitle)

        self.active_quests = QListWidget()
        self.today_feed = QListWidget()
        self.momentum_list = QListWidget()
        self.neglect_list = QListWidget()

        self.inline_capture = InlineCaptureBar(database, app_state)
        self.inline_capture.captured.connect(self.refresh)

        scroll_content = QWidget()
        grid = QGridLayout(scroll_content)
        grid.setContentsMargins(8, 4, 8, 4)
        grid.setSpacing(6)
        grid.addWidget(self._panel("Active Quests", self.active_quests), 0, 0)
        grid.addWidget(self._panel("Today", self.today_feed), 0, 1)
        grid.addWidget(self._panel("Momentum", self.momentum_list), 1, 0)
        grid.addWidget(self._panel("Needs Attention", self.neglect_list), 1, 1)

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

        self.active_quests.itemDoubleClicked.connect(self._on_quest_open)
        self.active_quests.itemClicked.connect(self._on_quest_select)

        self.app_state.context_changed.connect(self.refresh)
        self.app_state.workspace_changed.connect(self.refresh)
        self.refresh()

    def refresh(self) -> None:
        with self.database.session_scope() as session:
            scope = WorkspaceService(session).get_workspace(self.app_state.workspace_id)
            snapshot = FocusService(session).snapshot(scope)

        self._fill_quests(snapshot["active_quests"])
        self._fill_today(snapshot["today_feed"])
        self._fill_momentum(snapshot["momentum_quests"], snapshot["momentum_fields"])
        self._fill_neglect(snapshot["neglect"])

    def _panel(self, title: str, widget: QListWidget) -> QFrame:
        panel = QFrame()
        panel.setObjectName("ListPanel")
        widget.setMinimumHeight(200)

        label = QLabel(title)
        label.setObjectName("MetricLabel")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(4)
        layout.addWidget(label)
        layout.addWidget(widget)
        return panel

    def _fill_quests(self, quests: list[dict[str, object]]) -> None:
        self.active_quests.clear()
        if not quests:
            self.active_quests.addItem("No active quests in this workspace")
            return
        for quest in quests[:16]:
            last = quest.get("last_activity")
            last_text = display_datetime(last) if last else "never"
            text = (
                f"{quest['title']}  ·  {quest['path_name']} → {quest['field_name']}\n"
                f"{quest['progress_label']}  ·  last {last_text}  ·  {quest['momentum_bar']}"
            )
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, quest["id"])
            self.active_quests.addItem(item)

    def _fill_today(self, feed: list[dict[str, object]]) -> None:
        self.today_feed.clear()
        if not feed:
            self.today_feed.addItem("Nothing captured today")
            return
        for event in feed:
            stamp = display_datetime(event.get("timestamp"))
            text = (
                f"{stamp}  [{event['entity_type']}]  {event['title']}\n"
                f"{event['path_name']} → {event['field_name']} → {event['quest_title']}  ·  "
                f"{str(event.get('preview', ''))[:80]}"
            )
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, (event["entity_type"], event["entity_id"]))
            self.today_feed.addItem(item)

    def _fill_momentum(
        self,
        quests: list[dict[str, object]],
        fields: list[dict[str, object]],
    ) -> None:
        self.momentum_list.clear()
        for quest in quests[:8]:
            self.momentum_list.addItem(
                f"{quest['title'][:28]:28} {quest['bar']}  {quest['status_label']}"
            )
        self.momentum_list.addItem("— fields —")
        for field in fields[:6]:
            self.momentum_list.addItem(
                f"{field['title'][:28]:28} {field['bar']}  {field['status_label']}"
            )

    def _fill_neglect(self, neglect: dict[str, list]) -> None:
        self.neglect_list.clear()
        for quest in neglect.get("quests", [])[:6]:
            self.neglect_list.addItem(
                f"Quest stalled {quest['days_since']}d — {quest['title']} ({quest['field_name']})"
            )
        for field in neglect.get("fields", [])[:4]:
            self.neglect_list.addItem(
                f"Field dormant {field['days_since']}d — {field['title']}"
            )
        for resource in neglect.get("resources", [])[:3]:
            self.neglect_list.addItem(
                f"Resource untouched {resource['days_since']}d — {resource['title']}"
            )
        for artifact in neglect.get("artifacts", [])[:3]:
            self.neglect_list.addItem(
                f"Artifact unrevisited {artifact['days_since']}d — {artifact['title']}"
            )
        if self.neglect_list.count() == 0:
            self.neglect_list.addItem("Nothing neglected — good momentum")

    def _on_quest_open(self, item: QListWidgetItem) -> None:
        quest_id = item.data(Qt.UserRole)
        if quest_id:
            self.open_quest.emit(int(quest_id))

    def _on_quest_select(self, item: QListWidgetItem) -> None:
        quest_id = item.data(Qt.UserRole)
        if quest_id:
            self.capture_to_quest.emit(int(quest_id))
            self.inline_capture.set_quest_context(int(quest_id))