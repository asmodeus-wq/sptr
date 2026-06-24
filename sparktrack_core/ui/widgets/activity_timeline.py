from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QLabel, QScrollArea, QVBoxLayout, QWidget


class ActivityCard(QFrame):
    clicked = Signal(str, int)

    def __init__(self, event: dict[str, object]) -> None:
        super().__init__()
        self.setObjectName("ActivityCard")
        self.setCursor(Qt.PointingHandCursor)
        self._entity_type = str(event.get("entity_type", ""))
        self._entity_id = int(event.get("entity_id", 0))

        icon = QLabel(str(event.get("icon", "·")))
        icon.setObjectName("CardIcon")

        headline = QLabel(str(event.get("headline", "")))
        headline.setObjectName("CardHeadline")
        headline.setWordWrap(True)

        context = QLabel(str(event.get("context_line", "")))
        context.setObjectName("CardContext")

        time_ago = QLabel(str(event.get("time_ago", "")))
        time_ago.setObjectName("CardTime")

        preview = str(event.get("preview", ""))[:80]
        preview_label = QLabel(preview) if preview else QLabel("")
        preview_label.setObjectName("CardPreview")
        preview_label.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(3)

        top = QVBoxLayout()
        top.addWidget(icon)
        top.addWidget(headline)
        top.addWidget(context)
        top.addWidget(preview_label)

        bottom = QVBoxLayout()
        bottom.addWidget(time_ago)

        layout.addLayout(top)
        layout.addLayout(bottom)

    def mousePressEvent(self, event) -> None:
        if self._entity_id:
            self.clicked.emit(self._entity_type, self._entity_id)
        super().mousePressEvent(event)


class ActivityTimeline(QScrollArea):
    card_clicked = Signal(str, int)

    def __init__(self) -> None:
        super().__init__()
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self._container = QWidget()
        self._layout = QVBoxLayout(self._container)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(6)
        self._layout.addStretch()
        self.setWidget(self._container)

    def set_events(self, events: list[dict[str, object]]) -> None:
        while self._layout.count() > 1:
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not events:
            empty = QLabel("No recent activity in this workspace")
            empty.setObjectName("MetricLabel")
            self._layout.insertWidget(0, empty)
            return

        for event in events:
            card = ActivityCard(event)
            card.clicked.connect(self.card_clicked.emit)
            self._layout.insertWidget(self._layout.count() - 1, card)