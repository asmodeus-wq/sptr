from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QVBoxLayout,
)

from sparktrack_core.database.session import Database
from sparktrack_core.models.registry import CAPTURE_TYPES
from sparktrack_core.services.app_state import AppStateService
from sparktrack_core.services.capture_service import CaptureService
from sparktrack_core.services.context_resolver import ContextResolver


class QuickCaptureDialog(QDialog):
    def __init__(self, database: Database, app_state: AppStateService, capture_type: str = "idea") -> None:
        super().__init__()
        self.database = database
        self.app_state = app_state
        self.setWindowTitle("Quick Capture")
        self.setModal(True)
        self.resize(520, 360)

        self.type_combo = QComboBox()
        for key, (_, label) in CAPTURE_TYPES.items():
            self.type_combo.addItem(label if key != "artifact" else "Artifact", key)
        index = self.type_combo.findData(capture_type)
        if index >= 0:
            self.type_combo.setCurrentIndex(index)

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Capture title")
        self.body_input = QTextEdit()
        self.body_input.setPlaceholderText("Optional details")

        self.context_label = QLabel()
        self.context_label.setWordWrap(True)
        self._refresh_context_label()

        form = QFormLayout()
        form.addRow("Type", self.type_combo)
        form.addRow("Title", self.title_input)
        form.addRow("Details", self.body_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Capture to active context"))
        layout.addWidget(self.context_label)
        layout.addLayout(form)
        layout.addWidget(buttons)

        self.title_input.setFocus()

    def _refresh_context_label(self) -> None:
        with self.database.session_scope() as session:
            labels = ContextResolver(session).labels(self.app_state.context)
        self.context_label.setText(
            f"[ {labels['path']} ]  [ {labels['field']} ]  [ {labels['quest']} ]  [ {labels['season']} ]"
        )

    def accept(self) -> None:
        capture_type = self.type_combo.currentData()
        title = self.title_input.text().strip()
        body = self.body_input.toPlainText().strip()
        if not title:
            self.title_input.setFocus()
            return

        try:
            with self.database.session_scope() as session:
                CaptureService(session).capture(capture_type, title, body, self.app_state.context)
        except Exception as exc:
            self.setWindowTitle(f"Quick Capture — {exc}")
            return
        super().accept()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key_Return and event.modifiers() & Qt.ControlModifier:
            self.accept()
            return
        super().keyPressEvent(event)