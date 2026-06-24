from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QLabel,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from sparktrack_core.database.session import Database
from sparktrack_core.services.app_state import AppStateService


class SettingsPage(QWidget):
    def __init__(self, database: Database, app_state: AppStateService) -> None:
        super().__init__()
        self.app_state = app_state

        title = QLabel("Settings")
        title.setObjectName("PageTitle")

        self.developer_mode = QCheckBox("Developer Mode")
        self.developer_mode.setChecked(app_state.developer_mode)
        self.developer_mode.toggled.connect(app_state.set_developer_mode)

        developer_group = QGroupBox("Developer")
        developer_layout = QVBoxLayout(developer_group)
        developer_layout.addWidget(self.developer_mode)
        developer_layout.addWidget(
            QLabel("Enables Developer menu: fake life generator, time machine, screenshot mode, performance tests.")
        )

        summary = QPlainTextEdit()
        summary.setReadOnly(True)
        summary.setPlainText(
            "\n".join(
                [
                    "SparkTrack Core V1.5",
                    "",
                    f"Local database: {database.database_path}",
                    "",
                    "Keyboard shortcuts:",
                    "- Ctrl+Space: Quick Capture",
                    "- Ctrl+K: Command Palette",
                    "",
                    "Future extension points:",
                    "- Ollama Integration",
                    "- Local LLM Analysis",
                    "- Semantic Search",
                    "- Backup / Encryption / Sync",
                ]
            )
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)
        layout.addWidget(title)
        layout.addWidget(developer_group)
        layout.addWidget(summary, 1)