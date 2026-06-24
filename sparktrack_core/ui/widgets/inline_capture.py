from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QComboBox, QFrame, QHBoxLayout, QLineEdit, QPushButton

from sparktrack_core.database.session import Database
from sparktrack_core.models.registry import CAPTURE_TYPES
from sparktrack_core.services.app_state import AppStateService
from sparktrack_core.services.capture_service import CaptureService


class InlineCaptureBar(QFrame):
    captured = Signal()

    def __init__(self, database: Database, app_state: AppStateService) -> None:
        super().__init__()
        self.database = database
        self.app_state = app_state
        self.setObjectName("InlineCapture")

        self.type_combo = QComboBox()
        for key, (_, label) in CAPTURE_TYPES.items():
            self.type_combo.addItem(label if key != "artifact" else "Artifact", key)

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Quick capture — title and Enter")

        capture_button = QPushButton("Capture")
        capture_button.clicked.connect(self._capture)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(6)
        layout.addWidget(self.type_combo)
        layout.addWidget(self.title_input, 1)
        layout.addWidget(capture_button)

        self.title_input.returnPressed.connect(self._capture)

    def set_quest_context(self, quest_id: int | None) -> None:
        if quest_id:
            self.app_state.set_context(quest_id=quest_id)

    def _capture(self) -> None:
        title = self.title_input.text().strip()
        if not title:
            return
        capture_type = self.type_combo.currentData()
        try:
            with self.database.session_scope() as session:
                CaptureService(session).capture(capture_type, title, "", self.app_state.context)
        except Exception:
            return
        self.title_input.clear()
        self.captured.emit()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key_Return:
            self._capture()
            return
        super().keyPressEvent(event)