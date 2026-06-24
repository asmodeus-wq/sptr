from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QSizePolicy,
    QStackedWidget,
    QToolBar,
    QWidget,
)

from sparktrack_core.database.session import Database
from sparktrack_core.models import (
    Artifact,
    Burst,
    Field,
    Path,
    Principle,
    Quest,
    Resource,
    Season,
)
from sparktrack_core.services.app_state import AppStateService
from sparktrack_core.services.dev.fake_life_generator import FakeLifeGenerator
from sparktrack_core.services.dev.performance_tester import PerformanceTester
from sparktrack_core.services.dev.screenshot_mode import ScreenshotMode
from sparktrack_core.services.dev.time_machine import TimeMachine
from sparktrack_core.services.search_service import SearchService
from sparktrack_core.services.workspace_service import WorkspaceService
from sparktrack_core.ui.pages.crud_page import CrudConfig, CrudPage
from sparktrack_core.ui.pages.dashboard_page import DashboardPage
from sparktrack_core.ui.pages.field_overview_page import FieldOverviewPage
from sparktrack_core.ui.pages.now_page import NowPage
from sparktrack_core.ui.pages.quest_cockpit_page import QuestCockpitPage
from sparktrack_core.ui.pages.season_overview_page import SeasonOverviewPage
from sparktrack_core.ui.pages.settings_page import SettingsPage
from sparktrack_core.ui.pages.smart_view_page import SmartViewPage
from sparktrack_core.ui.widgets.command_palette import CommandPaletteDialog
from sparktrack_core.ui.widgets.context_bar import ContextBar
from sparktrack_core.ui.widgets.contextual_sidebar import ContextualSidebar
from sparktrack_core.ui.widgets.nav_shortcuts import NavigationShortcuts
from sparktrack_core.ui.widgets.quick_capture_dialog import QuickCaptureDialog


class MainWindow(QMainWindow):
    def __init__(self, database: Database, app_state: AppStateService) -> None:
        super().__init__()
        self.database = database
        self.app_state = app_state
        self.page_widgets: dict[str, QWidget] = {}
        self.page_indices: dict[str, int] = {}
        self._return_page = "Now"

        self.setWindowTitle("SparkTrack V1.7")
        self.resize(1320, 860)
        self.setMinimumSize(980, 640)

        self._ensure_default_workspace()

        self.context_bar = ContextBar(database, app_state)
        self.stack = QStackedWidget()
        self.sidebar = ContextualSidebar(database, app_state)

        shell = QWidget()
        shell_layout = QVBoxLayout(shell)
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setSpacing(0)

        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)
        body_layout.addWidget(self.sidebar)
        body_layout.addWidget(self.stack, 1)

        shell_layout.addWidget(self.context_bar)
        shell_layout.addWidget(body, 1)
        self.setCentralWidget(shell)

        self._build_toolbar()
        self._build_pages()
        self._build_shortcuts()
        self._build_developer_menu()
        self._build_statusbar()
        self._restore_window_state()

        self.sidebar.navigate.connect(self._handle_sidebar_nav)
        self.sidebar.quick_capture.connect(lambda: self._open_quick_capture("idea"))
        self.app_state.workspace_changed.connect(self._on_workspace_changed)

        self._navigate("Now")
        self.sidebar.rebuild()

        self._nav_chords = NavigationShortcuts(self, self._navigate)
        self._nav_chords.PAGE_KEYS = {
            "N": "Now",
            "Q": "Quest Cockpit",
            "S": "Settings",
            "D": "Data Explorer",
        }
        self._nav_chords.install()

    def _ensure_default_workspace(self) -> None:
        if self.app_state.workspace_id not in ("all", ""):
            return
        with self.database.session_scope() as session:
            workspaces = WorkspaceService(session).list_workspaces()
        if workspaces:
            self.app_state.set_workspace(workspaces[0].id)

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Command")
        toolbar.setMovable(False)
        toolbar.setFloatable(False)

        cmd_btn = QPushButton("⌘ Command")
        cmd_btn.clicked.connect(self._open_command_palette)
        cmd_btn.setToolTip("Ctrl+K — primary navigation")

        capture_btn = QPushButton("＋ Capture")
        capture_btn.clicked.connect(lambda: self._open_quick_capture("idea"))

        hint = QLineEdit()
        hint.setReadOnly(True)
        hint.setPlaceholderText("Ctrl+K to navigate · Ctrl+Space to capture")
        hint.setMaximumWidth(400)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        toolbar.addWidget(cmd_btn)
        toolbar.addWidget(capture_btn)
        toolbar.addWidget(spacer)
        toolbar.addWidget(hint)
        self.addToolBar(toolbar)

    def _build_pages(self) -> None:
        self.now_page = NowPage(self.database, self.app_state)
        self.quest_cockpit = QuestCockpitPage(self.database, self.app_state)

        configs: list[tuple[str, QWidget]] = [
            ("Now", self.now_page),
            ("Settings", SettingsPage(self.database, self.app_state)),
            ("Data Explorer", SmartViewPage(self.database, self.app_state)),
            ("Dashboard", DashboardPage(self.database, self.app_state)),
            ("Quest Cockpit", self.quest_cockpit),
            ("Field Overview", FieldOverviewPage(self.database)),
            ("Season Overview", SeasonOverviewPage(self.database)),
            ("Paths", CrudPage(self.database, CrudConfig("Paths", Path, ["name", "description", "icon"]))),
            ("Fields", CrudPage(self.database, CrudConfig("Fields", Field, ["path_id", "name", "description", "status"]), entity_type="field")),
            ("Quests", CrudPage(self.database, CrudConfig("Quests", Quest, ["field_id", "title", "description", "status", "priority", "target_date"]), entity_type="quest")),
            ("Bursts", CrudPage(self.database, CrudConfig("Bursts", Burst, ["quest_id", "title", "duration_minutes", "notes", "start_time", "end_time"]))),
            ("Artifacts", CrudPage(self.database, CrudConfig("Artifacts", Artifact, ["type", "title", "content"]), entity_type="artifact")),
            ("Resources", CrudPage(self.database, CrudConfig("Resources", Resource, ["title", "type", "source", "progress", "notes"]), entity_type="resource")),
            ("Principles", CrudPage(self.database, CrudConfig("Principles", Principle, ["statement", "description", "active"]), entity_type="principle")),
            ("Seasons", CrudPage(self.database, CrudConfig("Seasons", Season, ["name", "description", "start_date", "end_date", "active"]), entity_type="season")),
        ]

        for index, (name, page) in enumerate(configs):
            self.page_widgets[name] = page
            self.page_indices[name] = index
            self.stack.addWidget(page)

        self.now_page.open_quest.connect(self._open_quest_cockpit)
        self.now_page.open_entity.connect(self._open_search_result)
        self.quest_cockpit.back_requested.connect(self._back_from_detail)
        self.quest_cockpit.capture_burst.connect(lambda: self._open_quick_capture("burst"))
        self.quest_cockpit.quest_updated.connect(self._refresh_now)

        smart = self.page_widgets["Data Explorer"]
        if hasattr(smart, "open_entity"):
            smart.open_entity.connect(self._open_entity_detail)
        if hasattr(smart, "open_table"):
            smart.open_table.connect(self._navigate)

        self.context_bar.context_updated.connect(self._refresh_now)

    def _build_shortcuts(self) -> None:
        QShortcut(QKeySequence("Ctrl+Space"), self, activated=lambda: self._open_quick_capture("idea"))
        QShortcut(QKeySequence("Ctrl+K"), self, activated=self._open_command_palette)

    def _build_developer_menu(self) -> None:
        developer_menu = self.menuBar().addMenu("Developer")
        developer_menu.setEnabled(self.app_state.developer_mode)
        for profile in ["Builder", "Warrior", "Philosopher", "Creator", "Polymath"]:
            action = QAction(f"Generate {profile} Life", self)
            action.triggered.connect(lambda _=False, name=profile: self._generate_profile(name))
            developer_menu.addAction(action)
        developer_menu.addSeparator()
        for label, key in [("1 Week", "1_week"), ("1 Month", "1_month"), ("6 Months", "6_months"), ("2 Years", "2_years")]:
            action = QAction(f"Time Machine: {label}", self)
            action.triggered.connect(lambda _=False, k=key: self._generate_history(k))
            developer_menu.addAction(action)
        developer_menu.addSeparator()
        developer_menu.addAction("Screenshot Mode", self._generate_screenshot_mode)
        for count in [100, 1000, 5000, 10000]:
            action = QAction(f"Perf Test: {count}", self)
            action.triggered.connect(lambda _=False, c=count: self._run_performance_test(c))
            developer_menu.addAction(action)
        self.developer_menu = developer_menu
        self.app_state.developer_mode_changed.connect(lambda _: self._sync_developer_menu())
        self._sync_developer_menu()

    def _build_statusbar(self) -> None:
        with self.database.session_scope() as session:
            ws = WorkspaceService(session).get_workspace(self.app_state.workspace_id)
        self.statusBar().showMessage(f"{ws.name} · {self.database.database_path}")

    def _restore_window_state(self) -> None:
        geometry = self.app_state.restore_window_geometry()
        if geometry:
            self.restoreGeometry(geometry)

    def closeEvent(self, event) -> None:
        page_index = self.page_indices.get("Now", 0)
        self.app_state.save_window_state(self.saveGeometry(), self.saveState(), page_index)
        super().closeEvent(event)

    def _handle_sidebar_nav(self, target: str) -> None:
        if target == "command":
            self._open_command_palette()
            return
        if target.startswith("quest:"):
            self._open_quest_cockpit(int(target.split(":")[1]))
            return
        self._navigate(target)

    def _navigate(self, page_key: str) -> None:
        if page_key not in self.page_indices:
            return
        if page_key not in {"Quest Cockpit", "Field Overview", "Season Overview"}:
            self._return_page = page_key
        self.stack.setCurrentIndex(self.page_indices[page_key])
        page = self.page_widgets.get(page_key)
        if page and hasattr(page, "refresh"):
            page.refresh()

    def _on_workspace_changed(self) -> None:
        page = self.page_widgets.get("Now")
        if page and hasattr(page, "refresh"):
            page.refresh()
        smart = self.page_widgets.get("Data Explorer")
        if smart and hasattr(smart, "refresh"):
            smart.refresh()
        with self.database.session_scope() as session:
            ws = WorkspaceService(session).get_workspace(self.app_state.workspace_id)
        self.statusBar().showMessage(f"{ws.name} · {self.database.database_path}")

    def _refresh_now(self) -> None:
        self._on_workspace_changed()
        if self.stack.currentWidget() == self.page_widgets.get("Now"):
            return
        self._navigate("Now")

    def _sync_developer_menu(self) -> None:
        self.developer_menu.setEnabled(self.app_state.developer_mode)
        self.developer_menu.menuAction().setVisible(self.app_state.developer_mode)

    def _open_quest_cockpit(self, quest_id: int) -> None:
        self.quest_cockpit.load_quest(quest_id)
        self.stack.setCurrentIndex(self.page_indices["Quest Cockpit"])

    def _open_field_overview(self, field_id: int) -> None:
        page = self.page_widgets["Field Overview"]
        page.load_field(field_id)
        self.stack.setCurrentIndex(self.page_indices["Field Overview"])

    def _open_season_overview(self, season_id: int) -> None:
        page = self.page_widgets["Season Overview"]
        page.load_season(season_id)
        self.stack.setCurrentIndex(self.page_indices["Season Overview"])

    def _open_entity_detail(self, entity_type: str, entity_id: int) -> None:
        if entity_type == "quest":
            self._open_quest_cockpit(entity_id)
        elif entity_type == "field":
            self._open_field_overview(entity_id)
        elif entity_type == "season":
            self._open_season_overview(entity_id)
        else:
            self._open_search_result(entity_type, entity_id)

    def _back_from_detail(self) -> None:
        self._navigate(self._return_page)

    def _open_quick_capture(self, capture_type: str = "idea") -> None:
        dialog = QuickCaptureDialog(self.database, self.app_state, capture_type=capture_type)
        if dialog.exec():
            self._refresh_now()

    def _open_command_palette(self) -> None:
        dialog = CommandPaletteDialog(self.database, self.app_state)
        dialog.command_selected.connect(self._handle_command)
        dialog.search_result_selected.connect(self._open_search_result)
        dialog.exec()

    def _switch_workspace(self, workspace_id: str) -> None:
        if workspace_id:
            self.app_state.set_workspace(workspace_id)
            self._refresh_now()

    def _handle_command(self, handler_key: str, payload: str = "") -> None:
        mapping = {
            "nav_now": lambda: self._navigate("Now"),
            "quick_capture": lambda: self._open_quick_capture("idea"),
            "capture_burst": lambda: self._open_quick_capture("burst"),
            "capture_artifact": lambda: self._open_quick_capture("artifact"),
            "capture_reflection": lambda: self._open_quick_capture("reflection"),
            "capture_resource": lambda: self._open_quick_capture("resource"),
            "nav_settings": lambda: self._navigate("Settings"),
            "nav_smart_views": lambda: self._navigate("Data Explorer"),
            "nav_dashboard": lambda: self._navigate("Dashboard"),
            "nav_paths": lambda: self._navigate("Paths"),
            "nav_fields": lambda: self._navigate("Fields"),
            "nav_quests": lambda: self._navigate("Quests"),
            "nav_bursts": lambda: self._navigate("Bursts"),
            "nav_artifacts": lambda: self._navigate("Artifacts"),
            "nav_resources": lambda: self._navigate("Resources"),
            "nav_principles": lambda: self._navigate("Principles"),
            "set_context": lambda: self.context_bar.setFocus(),
            "switch_workspace": lambda: self._switch_workspace(payload),
            "ai_placeholder": lambda: QMessageBox.information(self, "Future", "AI extension point reserved."),
        }
        handler = mapping.get(handler_key)
        if handler:
            handler()

    def _open_search_result(self, entity_type: str, entity_id: int) -> None:
        if entity_type == "quest":
            self._open_quest_cockpit(entity_id)
        elif entity_type == "field":
            self._open_field_overview(entity_id)
        elif entity_type == "season":
            self._open_season_overview(entity_id)
        elif entity_type == "burst":
            with self.database.session_scope() as session:
                burst = session.get(Burst, entity_id)
                if burst:
                    self._open_quest_cockpit(burst.quest_id)
        elif entity_type == "artifact":
            self._navigate("Artifacts")
            page = self.page_widgets["Artifacts"]
            if hasattr(page, "select_record"):
                page.select_record(entity_id)
        else:
            page_map = {"path": "Paths", "resource": "Resources", "principle": "Principles"}
            key = page_map.get(entity_type)
            if key:
                self._navigate(key)
                page = self.page_widgets[key]
                if hasattr(page, "select_record"):
                    page.select_record(entity_id)

    def _generate_profile(self, name: str) -> None:
        with self.database.session_scope() as session:
            counts = FakeLifeGenerator(session).generate_profile(name.lower(), scale=2)
        self._refresh_now()
        QMessageBox.information(self, "Generated", str(counts))

    def _generate_history(self, key: str) -> None:
        with self.database.session_scope() as session:
            counts = TimeMachine(session).generate_history(key)
        self._refresh_now()
        QMessageBox.information(self, "Time Machine", str(counts))

    def _generate_screenshot_mode(self) -> None:
        with self.database.session_scope() as session:
            context = ScreenshotMode(session).generate()
        self.app_state.set_context(
            path_id=context.path_id, field_id=context.field_id,
            quest_id=context.quest_id, season_id=context.season_id, clear_missing=True,
        )
        self._refresh_now()
        QMessageBox.information(self, "Screenshot Mode", "Showcase data ready.")

    def _run_performance_test(self, count: int) -> None:
        with self.database.session_scope() as session:
            created = PerformanceTester(session).generate_records(count)
            metrics = PerformanceTester(session).benchmark()
        self._refresh_now()
        QMessageBox.information(self, "Perf", f"~{created} records\n{metrics}")

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._sync_developer_menu()