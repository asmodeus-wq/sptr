import sys

from PySide6.QtWidgets import QApplication

from sparktrack_core.database.session import Database
from sparktrack_core.services.app_state import AppStateService
from sparktrack_core.services.seed_service import SeedService
from sparktrack_core.ui.main_window import MainWindow
from sparktrack_core.ui.theme import apply_dark_theme


def run() -> int:
    database = Database()
    database.initialize()

    with database.session_scope() as session:
        SeedService(session).seed_defaults()

    app = QApplication(sys.argv)
    app.setApplicationName("SparkTrack Core")
    app.setOrganizationName("SparkTrack")
    apply_dark_theme(app)

    app_state = AppStateService()
    window = MainWindow(database, app_state)
    window.show()
    return app.exec()
