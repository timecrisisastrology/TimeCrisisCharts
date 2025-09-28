import sys
from PyQt6.QtWidgets import QWidget, QLabel, QFormLayout, QVBoxLayout, QFrame, QPushButton
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

class InfoPanel(QWidget):
    """A custom, styled panel for displaying astrological data."""
    def __init__(self, title, data):
        super().__init__()
        # The InfoPanel itself is transparent; the QFrame inside provides the styled background and border.
        self.setStyleSheet("""
            QLabel#panel-title {
                color: #FF01F9;
                font-family: "TT Supermolot Neue Condensed";
                font-size: 14pt;
                font-weight: bold;
                padding-bottom: 5px;
            }
            QFrame#container {
                background-color: #200334;
                border: 1px solid #3DF6FF;
                border-radius: 5px;
            }
            QLabel {
                color: #94EBFF;
                font-family: "Titillium Web";
                font-size: 10pt;
                background-color: transparent;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        title_label = QLabel(title)
        title_label.setObjectName("panel-title")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        container = QFrame()
        container.setObjectName("container")
        form_layout = QFormLayout(container)
        form_layout.setContentsMargins(15, 15, 15, 15)

        for label, value in data.items():
            form_layout.addRow(f"{label}:", QLabel(value))

        main_layout.addWidget(container)

class StyledButton(QPushButton):
    """A custom, styled button for the toolbar."""
    def __init__(self, text):
        super().__init__(text)
        self.setStyleSheet("""
            QPushButton {
                background-color: #200334;
                color: #3DF6FF;
                border: 1px solid #3DF6FF;
                border-radius: 5px;
                padding: 10px;
                font-family: "TT Supermolot Neue Condensed";
                font-size: 12pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3DF6FF;
                color: #200334;
            }
            QPushButton:pressed {
                background-color: #94EBFF;
                color: #200334;
            }
        """)