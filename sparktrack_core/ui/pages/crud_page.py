from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Any

from PySide6.QtCore import Qt, QDate, QDateTime
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDateTimeEdit,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy import select

from sparktrack_core.database.session import Database
from sparktrack_core.models.registry import entity_title
from sparktrack_core.repositories.base import Repository
from sparktrack_core.ui.widgets.relationship_picker import RelationshipPickerDialog
from sparktrack_core.utils.dates import display_date, display_datetime


STATUS_OPTIONS = ["Active", "Paused", "Completed", "Archived"]
PRIORITY_OPTIONS = ["Low", "Medium", "High", "Critical"]
ARTIFACT_TYPES = [
    "Reflection",
    "Idea",
    "Principle",
    "Quote",
    "Lesson",
    "Research Note",
    "Observation",
    "Story Fragment",
    "Character Sketch",
    "Concept",
]
RESOURCE_TYPES = ["Book", "Course", "Video", "Article", "Paper"]
PROGRESS_OPTIONS = ["Not Started", "In Progress", "Completed", "Reference"]


@dataclass(frozen=True)
class CrudConfig:
    title: str
    model: type
    editable_fields: list[str]


class CrudPage(QWidget):
    def __init__(
        self,
        database: Database,
        config: CrudConfig,
        *,
        entity_type: str | None = None,
    ) -> None:
        super().__init__()
        self.database = database
        self.config = config
        self.entity_type = entity_type
        self.current_id: int | None = None
        self.inputs: dict[str, QWidget] = {}

        title = QLabel(config.title)
        title.setObjectName("PageTitle")

        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.itemSelectionChanged.connect(self._load_selection)
        self.table.itemDoubleClicked.connect(self._focus_editor)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_table_menu)

        form = QWidget()
        self.form_layout = QFormLayout(form)
        self.form_layout.setContentsMargins(12, 12, 12, 12)
        self._build_form()

        new_button = QPushButton("New")
        save_button = QPushButton("Save")
        delete_button = QPushButton("Delete")
        refresh_button = QPushButton("Refresh")
        links_button = QPushButton("Relationships")
        links_button.clicked.connect(self._open_relationships)
        if self.entity_type is None:
            links_button.setEnabled(False)

        new_button.clicked.connect(self._new_record)
        save_button.clicked.connect(self._save_record)
        delete_button.clicked.connect(self._delete_record)
        refresh_button.clicked.connect(self.refresh)

        buttons = QHBoxLayout()
        buttons.addWidget(new_button)
        buttons.addWidget(save_button)
        buttons.addWidget(delete_button)
        buttons.addWidget(links_button)
        buttons.addStretch(1)
        buttons.addWidget(refresh_button)

        editor = QWidget()
        editor_layout = QVBoxLayout(editor)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.addWidget(form)
        editor_layout.addLayout(buttons)
        editor_layout.addStretch(1)

        splitter = QSplitter()
        splitter.addWidget(self.table)
        splitter.addWidget(editor)
        splitter.setSizes([780, 360])

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)
        layout.addWidget(title)
        layout.addWidget(splitter, 1)

        self.refresh()

    def select_record(self, record_id: int) -> None:
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and int(item.text()) == record_id:
                self.table.selectRow(row)
                self._load_selection()
                return

    def _focus_editor(self) -> None:
        title_field = self.config.editable_fields[0]
        self.inputs[title_field].setFocus()

    def _show_table_menu(self, position) -> None:
        if self.table.itemAt(position) is None:
            return
        menu = QMenu(self)
        edit_action = menu.addAction("Edit")
        delete_action = menu.addAction("Delete")
        links_action = menu.addAction("Manage Relationships") if self.entity_type else None
        action = menu.exec(self.table.mapToGlobal(position))
        if action == edit_action:
            self._focus_editor()
        elif action == delete_action:
            self._delete_record()
        elif links_action and action == links_action:
            self._open_relationships()

    def _open_relationships(self) -> None:
        if self.current_id is None or self.entity_type is None:
            return
        with self.database.session_scope() as session:
            item = session.get(self.config.model, self.current_id)
            if item is None:
                return
            title = entity_title(self.entity_type, item)
        dialog = RelationshipPickerDialog(
            self.database,
            source_type=self.entity_type,
            source_id=self.current_id,
            source_title=title,
        )
        dialog.exec()

    def refresh(self) -> None:
        with self.database.session_scope() as session:
            rows = list(session.scalars(select(self.config.model).order_by(self.config.model.id.desc())))
            values = [self._row_values(row) for row in rows]

        columns = ["id", *self.config.editable_fields]
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        self.table.setRowCount(len(values))

        for row_index, row in enumerate(values):
            for column_index, column in enumerate(columns):
                item = QTableWidgetItem(str(row.get(column, "")))
                self.table.setItem(row_index, column_index, item)

        self.table.resizeColumnsToContents()

    def _build_form(self) -> None:
        for field_name in self.config.editable_fields:
            widget = self._input_for(field_name)
            self.inputs[field_name] = widget
            self.form_layout.addRow(self._label(field_name), widget)

    def _input_for(self, field_name: str) -> QWidget:
        if field_name in {"description", "content", "notes"}:
            widget = QTextEdit()
            widget.setMinimumHeight(90)
            return widget
        if field_name in {"path_id", "field_id", "quest_id", "source_id", "target_id", "duration_minutes"}:
            widget = QSpinBox()
            widget.setRange(0, 2_000_000_000)
            if field_name == "duration_minutes":
                widget.setValue(25)
            return widget
        if field_name in {"active"}:
            return QCheckBox()
        if field_name in {"target_date", "start_date", "end_date"}:
            widget = QDateEdit()
            widget.setCalendarPopup(True)
            widget.setSpecialValueText("")
            widget.setMinimumDate(QDate(1900, 1, 1))
            widget.setDate(QDate.currentDate())
            return widget
        if field_name in {"start_time", "end_time"}:
            widget = QDateTimeEdit()
            widget.setCalendarPopup(True)
            widget.setDateTime(QDateTime.currentDateTime())
            return widget
        if field_name == "status":
            return self._combo(STATUS_OPTIONS)
        if field_name == "priority":
            return self._combo(PRIORITY_OPTIONS)
        if field_name == "type" and self.config.title == "Artifacts":
            return self._combo(ARTIFACT_TYPES)
        if field_name == "type" and self.config.title == "Resources":
            return self._combo(RESOURCE_TYPES)
        if field_name == "progress":
            return self._combo(PROGRESS_OPTIONS)

        return QLineEdit()

    def _combo(self, options: list[str]) -> QComboBox:
        widget = QComboBox()
        widget.setEditable(True)
        widget.addItems(options)
        return widget

    def _load_selection(self) -> None:
        selected = self.table.selectedItems()
        if not selected:
            return
        row = selected[0].row()
        self.current_id = int(self.table.item(row, 0).text())

        with self.database.session_scope() as session:
            item = session.get(self.config.model, self.current_id)
            if item is None:
                return
            values = self._row_values(item)

        for field_name, widget in self.inputs.items():
            self._set_widget_value(widget, values.get(field_name))

    def _new_record(self) -> None:
        self.current_id = None
        self.table.clearSelection()
        for field_name, widget in self.inputs.items():
            self._clear_widget(field_name, widget)

    def _save_record(self) -> None:
        values = {field: self._widget_value(widget) for field, widget in self.inputs.items()}
        try:
            with self.database.session_scope() as session:
                repository = Repository(session, self.config.model)
                if self.current_id is None:
                    item = repository.create(values)
                    self.current_id = item.id
                else:
                    repository.update(self.current_id, values)
        except Exception as exc:
            QMessageBox.critical(self, "Save failed", str(exc))
            return
        self.refresh()

    def _delete_record(self) -> None:
        if self.current_id is None:
            return
        confirmed = QMessageBox.question(
            self,
            "Delete record",
            "Delete the selected record?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirmed != QMessageBox.Yes:
            return
        try:
            with self.database.session_scope() as session:
                Repository(session, self.config.model).delete(self.current_id)
        except Exception as exc:
            QMessageBox.critical(self, "Delete failed", str(exc))
            return
        self.current_id = None
        self.refresh()

    def _row_values(self, item: object) -> dict[str, Any]:
        fields = ["id", *self.config.editable_fields]
        return {field: self._display_value(getattr(item, field, "")) for field in fields}

    def _display_value(self, value: Any) -> Any:
        if isinstance(value, datetime):
            return display_datetime(value)
        if isinstance(value, date):
            return display_date(value)
        return value

    def _set_widget_value(self, widget: QWidget, value: Any) -> None:
        if isinstance(widget, QTextEdit):
            widget.setPlainText(str(value or ""))
        elif isinstance(widget, QSpinBox):
            widget.setValue(int(value or 0))
        elif isinstance(widget, QCheckBox):
            widget.setChecked(str(value).lower() in {"true", "1", "yes"})
        elif isinstance(widget, QDateEdit):
            parsed = QDate.fromString(str(value), "yyyy-MM-dd")
            widget.setDate(parsed if parsed.isValid() else QDate.currentDate())
        elif isinstance(widget, QDateTimeEdit):
            parsed = QDateTime.fromString(str(value), "yyyy-MM-dd HH:mm")
            widget.setDateTime(parsed if parsed.isValid() else QDateTime.currentDateTime())
        elif isinstance(widget, QComboBox):
            widget.setCurrentText(str(value or ""))
        elif isinstance(widget, QLineEdit):
            widget.setText(str(value or ""))

    def _clear_widget(self, field_name: str, widget: QWidget) -> None:
        if isinstance(widget, QTextEdit):
            widget.clear()
        elif isinstance(widget, QSpinBox):
            widget.setValue(25 if field_name == "duration_minutes" else 0)
        elif isinstance(widget, QCheckBox):
            widget.setChecked(field_name == "active")
        elif isinstance(widget, QDateEdit):
            widget.setDate(QDate.currentDate())
        elif isinstance(widget, QDateTimeEdit):
            widget.setDateTime(QDateTime.currentDateTime())
        elif isinstance(widget, QComboBox):
            widget.setCurrentIndex(0)
        elif isinstance(widget, QLineEdit):
            widget.clear()

    def _widget_value(self, widget: QWidget) -> Any:
        if isinstance(widget, QTextEdit):
            return widget.toPlainText().strip()
        if isinstance(widget, QSpinBox):
            return widget.value()
        if isinstance(widget, QCheckBox):
            return widget.isChecked()
        if isinstance(widget, QDateEdit) and not isinstance(widget, QDateTimeEdit):
            qdate = widget.date()
            return date(qdate.year(), qdate.month(), qdate.day())
        if isinstance(widget, QDateTimeEdit):
            qdatetime = widget.dateTime()
            qdate = qdatetime.date()
            qtime = qdatetime.time()
            return datetime.combine(
                date(qdate.year(), qdate.month(), qdate.day()),
                time(qtime.hour(), qtime.minute(), qtime.second()),
            )
        if isinstance(widget, QComboBox):
            return widget.currentText().strip()
        if isinstance(widget, QLineEdit):
            return widget.text().strip()
        return None

    def _label(self, field_name: str) -> str:
        return field_name.replace("_", " ").title()
