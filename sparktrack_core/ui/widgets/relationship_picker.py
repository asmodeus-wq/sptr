from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from sqlalchemy import select

from sparktrack_core.database.session import Database
from sparktrack_core.models.registry import ENTITY_REGISTRY, RELATIONSHIP_RULES
from sparktrack_core.services.relationship_service import RelationshipService


class RelationshipPickerDialog(QDialog):
    def __init__(
        self,
        database: Database,
        *,
        source_type: str,
        source_id: int,
        source_title: str,
    ) -> None:
        super().__init__()
        self.database = database
        self.source_type = source_type
        self.source_id = source_id
        self.setWindowTitle("Manage Relationships")
        self.resize(560, 420)

        title = QLabel(f"{source_title}")
        title.setObjectName("PageTitle")

        self.target_type_combo = QComboBox()
        allowed_targets = sorted({target for source, target in RELATIONSHIP_RULES if source == source_type})
        for target_type in allowed_targets:
            self.target_type_combo.addItem(ENTITY_REGISTRY[target_type].label, target_type)

        self.target_entity_combo = QComboBox()
        self.target_type_combo.currentIndexChanged.connect(self._load_target_entities)

        add_button = QPushButton("Link")
        add_button.clicked.connect(self._add_link)

        self.links = QListWidget()
        self._refresh_links()

        form = QFormLayout()
        form.addRow("Target Type", self.target_type_combo)
        form.addRow("Target", self.target_entity_combo)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)

        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addWidget(self.links, 1)
        layout.addLayout(form)
        row = QHBoxLayout()
        row.addWidget(add_button)
        row.addStretch(1)
        layout.addLayout(row)
        layout.addWidget(buttons)

        self._load_target_entities()

    def _load_target_entities(self) -> None:
        target_type = self.target_type_combo.currentData()
        self.target_entity_combo.clear()
        if not target_type:
            return

        meta = ENTITY_REGISTRY[target_type]
        with self.database.session_scope() as session:
            rows = list(session.scalars(select(meta.model).order_by(meta.model.id.desc())))
        for row in rows[:200]:
            self.target_entity_combo.addItem(getattr(row, meta.title_field), row.id)

    def _add_link(self) -> None:
        target_type = self.target_type_combo.currentData()
        target_id = self.target_entity_combo.currentData()
        if not target_type or target_id is None:
            return
        try:
            with self.database.session_scope() as session:
                RelationshipService(session).link(
                    self.source_type,
                    self.source_id,
                    target_type,
                    target_id,
                )
        except Exception as exc:
            QMessageBox.warning(self, "Link failed", str(exc))
            return
        self._refresh_links()

    def _refresh_links(self) -> None:
        self.links.clear()
        with self.database.session_scope() as session:
            rows = RelationshipService(session).list_for_entity(self.source_type, self.source_id)
        for row in rows:
            self.links.addItem(f"{row['relationship_type']}: {row['title']}")