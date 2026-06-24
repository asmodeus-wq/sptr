from __future__ import annotations

from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget


class HeatmapWidget(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("HeatmapPanel")
        self._grid = QGridLayout(self)
        self._grid.setContentsMargins(8, 6, 8, 6)
        self._grid.setSpacing(3)

    def set_data(self, days: list[dict[str, object]]) -> None:
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for index, day in enumerate(days):
            cell = QFrame()
            intensity = float(day.get("intensity", 0))
            alpha = int(40 + intensity * 215)
            cell.setFixedSize(22, 22)
            cell.setStyleSheet(
                f"background: rgba(94, 161, 255, {alpha}); border-radius: 3px;"
            )
            cell.setToolTip(f"{day.get('label', '')}: {day.get('count', 0)} bursts")
            self._grid.addWidget(cell, 0, index)


class QuestHealthRow(QFrame):
    def __init__(self, item: dict[str, object]) -> None:
        super().__init__()
        self.setObjectName("HealthRow")

        title = QLabel(str(item.get("title", ""))[:32])
        title.setObjectName("CardHeadline")

        bar = QLabel(str(item.get("bar", "")))
        bar.setObjectName("MomentumBar")

        health = QLabel(str(item.get("health", "")))
        health.setStyleSheet(f"color: {item.get('health_color', '#AEB7C8')};")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.addWidget(title, 1)
        layout.addWidget(bar)
        layout.addWidget(health)


class ConsistencyBadge(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("MetricPanel")
        self._label = QLabel("—")
        self._label.setObjectName("MetricValue")
        self._caption = QLabel("Consistency")
        self._caption.setObjectName("MetricLabel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.addWidget(self._label)
        layout.addWidget(self._caption)

    def set_data(self, data: dict[str, object]) -> None:
        self._label.setText(f"{data.get('consistency_pct', 0)}%")
        self._caption.setText(str(data.get("streak_label", "Consistency")))