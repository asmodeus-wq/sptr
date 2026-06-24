from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QFrame, QHBoxLayout, QLabel

from sqlalchemy import select

from sparktrack_core.database.session import Database
from sparktrack_core.models import Field, Path, Quest, Season
from sparktrack_core.services.app_state import AppStateService
from sparktrack_core.services.context_resolver import ContextResolver


class ContextBar(QFrame):
    context_updated = Signal()

    def __init__(self, database: Database, app_state: AppStateService) -> None:
        super().__init__()
        self.database = database
        self.app_state = app_state
        self.setObjectName("ContextBar")

        self.path_combo = self._combo()
        self.field_combo = self._combo()
        self.quest_combo = self._combo()
        self.season_combo = self._combo()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(8)
        layout.addWidget(self._chip_label("Path"))
        layout.addWidget(self.path_combo, 1)
        layout.addWidget(self._chip_label("Field"))
        layout.addWidget(self.field_combo, 1)
        layout.addWidget(self._chip_label("Quest"))
        layout.addWidget(self.quest_combo, 1)
        layout.addWidget(self._chip_label("Season"))
        layout.addWidget(self.season_combo, 1)

        self.path_combo.currentIndexChanged.connect(self._on_path_changed)
        self.field_combo.currentIndexChanged.connect(self._on_field_changed)
        self.quest_combo.currentIndexChanged.connect(self._on_quest_changed)
        self.season_combo.currentIndexChanged.connect(self._on_season_changed)

        self.app_state.context_changed.connect(self.refresh)
        self.refresh()

    def refresh(self) -> None:
        with self.database.session_scope() as session:
            paths = list(session.scalars(select(Path).order_by(Path.name)))
            fields = list(session.scalars(select(Field).order_by(Field.name)))
            quests = list(session.scalars(select(Quest).order_by(Quest.title)))
            seasons = list(session.scalars(select(Season).order_by(Season.name)))

        self._populate(self.path_combo, paths, "name", self.app_state.context.path_id)
        self._populate(self.field_combo, fields, "name", self.app_state.context.field_id, filter_path=True)
        self._populate(self.quest_combo, quests, "title", self.app_state.context.quest_id, filter_field=True)
        self._populate(self.season_combo, seasons, "name", self.app_state.context.season_id)

    def labels(self) -> dict[str, str]:
        with self.database.session_scope() as session:
            return ContextResolver(session).labels(self.app_state.context)

    def _combo(self) -> QComboBox:
        combo = QComboBox()
        combo.setMinimumWidth(140)
        return combo

    def _chip_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("ContextChip")
        return label

    def _populate(
        self,
        combo: QComboBox,
        rows: list,
        label_field: str,
        selected_id: int | None,
        *,
        filter_path: bool = False,
        filter_field: bool = False,
    ) -> None:
        combo.blockSignals(True)
        combo.clear()
        combo.addItem("—", None)

        path_id = self.app_state.context.path_id
        field_id = self.app_state.context.field_id

        for row in rows:
            if filter_path and path_id and getattr(row, "path_id", None) != path_id:
                continue
            if filter_field and field_id and getattr(row, "field_id", None) != field_id:
                continue
            combo.addItem(getattr(row, label_field), row.id)

        if selected_id is not None:
            index = combo.findData(selected_id)
            if index >= 0:
                combo.setCurrentIndex(index)
        combo.blockSignals(False)

    def _on_path_changed(self) -> None:
        path_id = self.path_combo.currentData()
        self.app_state.set_context(path_id=path_id, field_id=None, quest_id=None, clear_missing=True)
        self.refresh()
        self.context_updated.emit()

    def _on_field_changed(self) -> None:
        field_id = self.field_combo.currentData()
        self.app_state.set_context(field_id=field_id, quest_id=None, clear_missing=False)
        self.refresh()
        self.context_updated.emit()

    def _on_quest_changed(self) -> None:
        quest_id = self.quest_combo.currentData()
        self.app_state.set_context(quest_id=quest_id)
        self.context_updated.emit()

    def _on_season_changed(self) -> None:
        season_id = self.season_combo.currentData()
        self.app_state.set_context(season_id=season_id)
        self.context_updated.emit()