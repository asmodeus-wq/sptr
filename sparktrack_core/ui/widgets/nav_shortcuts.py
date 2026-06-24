from __future__ import annotations

from PySide6.QtCore import QObject, QTimer
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QWidget


class NavigationShortcuts(QObject):
    """Linear-style G+<key> navigation chords."""

    PAGE_KEYS = {
        "Q": "Quests",
        "F": "Fields",
        "B": "Bursts",
        "A": "Artifacts",
        "S": "Seasons",
        "P": "Focus",
        "V": "Smart Views",
        "D": "Dashboard",
    }

    def __init__(self, window: QWidget, navigate_callback) -> None:
        super().__init__()
        self.window = window
        self.navigate = navigate_callback
        self._pending_g = False
        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.setInterval(1200)
        self._timer.timeout.connect(self._reset)

    def eventFilter(self, obj, event) -> bool:
        if event.type() != QKeyEvent.Type.KeyPress:
            return False
        key = event.key()
        text = event.text().upper()

        if text == "G" and not self._pending_g:
            self._pending_g = True
            self._timer.start()
            return True

        if self._pending_g and text in self.PAGE_KEYS:
            page = self.PAGE_KEYS[text]
            self._reset()
            self.navigate(page)
            return True

        self._reset()
        return False

    def _reset(self) -> None:
        self._pending_g = False
        self._timer.stop()

    def install(self) -> None:
        self.window.installEventFilter(self)