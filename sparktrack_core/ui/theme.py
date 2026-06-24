from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication


def apply_dark_theme(app: QApplication) -> None:
    app.setStyle("Fusion")

    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#111318"))
    palette.setColor(QPalette.WindowText, QColor("#ECEFF4"))
    palette.setColor(QPalette.Base, QColor("#171A21"))
    palette.setColor(QPalette.AlternateBase, QColor("#20242D"))
    palette.setColor(QPalette.ToolTipBase, QColor("#ECEFF4"))
    palette.setColor(QPalette.ToolTipText, QColor("#111318"))
    palette.setColor(QPalette.Text, QColor("#ECEFF4"))
    palette.setColor(QPalette.Button, QColor("#20242D"))
    palette.setColor(QPalette.ButtonText, QColor("#ECEFF4"))
    palette.setColor(QPalette.BrightText, QColor("#FFFFFF"))
    palette.setColor(QPalette.Highlight, QColor("#3D7EFF"))
    palette.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
    app.setPalette(palette)

    app.setStyleSheet(
        """
        QWidget {
            font-family: "Segoe UI";
            font-size: 10pt;
        }
        QMainWindow, QDialog {
            background: #111318;
        }
        QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDateEdit, QDateTimeEdit, QComboBox {
            background: #171A21;
            border: 1px solid #303642;
            border-radius: 4px;
            color: #ECEFF4;
            padding: 5px 7px;
            selection-background-color: #3D7EFF;
        }
        QPushButton {
            background: #242936;
            border: 1px solid #384050;
            border-radius: 4px;
            color: #ECEFF4;
            padding: 6px 10px;
        }
        QPushButton:hover {
            background: #2F3646;
        }
        QPushButton:pressed {
            background: #1F2530;
        }
        QTableWidget {
            background: #151820;
            alternate-background-color: #1C202A;
            border: 1px solid #2D3340;
            gridline-color: #303642;
            selection-background-color: #2E5EA8;
            selection-color: #FFFFFF;
        }
        QHeaderView::section {
            background: #20242D;
            border: 0;
            border-right: 1px solid #303642;
            color: #AEB7C8;
            padding: 6px;
        }
        QListWidget {
            background: #0E1015;
            border: 0;
            outline: 0;
        }
        QListWidget::item {
            padding: 10px 12px;
            color: #AEB7C8;
        }
        QListWidget::item:selected {
            background: #24314A;
            color: #FFFFFF;
            border-left: 3px solid #5EA1FF;
        }
        QStatusBar {
            background: #0E1015;
            color: #AEB7C8;
        }
        QLabel#PageTitle {
            font-size: 18pt;
            font-weight: 600;
            color: #FFFFFF;
        }
        QLabel#MetricValue {
            font-size: 18pt;
            font-weight: 600;
            color: #FFFFFF;
        }
        QLabel#MetricLabel {
            color: #AEB7C8;
        }
        QFrame#MetricPanel, QFrame#ListPanel {
            background: #171A21;
            border: 1px solid #2D3340;
            border-radius: 4px;
        }
        QFrame#ContextBar {
            background: #0E1015;
            border-bottom: 1px solid #2D3340;
        }
        QLabel#ContextChip {
            color: #7F8CA3;
            font-size: 9pt;
            font-weight: 600;
            text-transform: uppercase;
        }
        QFrame#InlineCapture {
            background: #141820;
            border: 1px solid #3D7EFF;
            border-radius: 4px;
        }
        QListWidget::item {
            padding: 6px 8px;
        }
        QScrollArea {
            border: none;
        }
        QLabel#NowFocus {
            color: #5EA1FF;
            font-size: 11pt;
            padding: 4px 0;
        }
        QFrame#ActivityCard {
            background: #1A1F2B;
            border: 1px solid #2D3340;
            border-radius: 6px;
        }
        QFrame#ActivityCard:hover {
            background: #1F2635;
            border-color: #3D7EFF;
        }
        QLabel#CardHeadline {
            color: #FFFFFF;
            font-weight: 600;
        }
        QLabel#CardContext {
            color: #7F8CA3;
            font-size: 9pt;
        }
        QLabel#CardTime {
            color: #5EA1FF;
            font-size: 9pt;
        }
        QLabel#CardPreview {
            color: #AEB7C8;
            font-size: 9pt;
        }
        QLabel#CardIcon {
            font-size: 12pt;
        }
        QLabel#MomentumBar {
            font-family: "Consolas", monospace;
            color: #5EA1FF;
            font-size: 9pt;
        }
        QFrame#HealthRow {
            background: #141820;
            border-radius: 4px;
        }
        QFrame#HeatmapPanel {
            background: transparent;
        }
        QListWidget#CommandResults::item {
            padding: 8px 12px;
        }
        QListWidget#CommandResults::item:selected {
            background: #2A3A5C;
        }
        QTextEdit#MissionDescription {
            background: #141820;
            border: 1px solid #2D3340;
            border-radius: 4px;
            color: #C8D0E0;
        }
        """
    )
