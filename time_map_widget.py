import sys
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt
from widgets import StyledButton
from timeline_grid_widget import TimelineGridWidget

class TimeMapWidget(QWidget):
    """A custom widget to display the 'Time Map' timeline view."""
    def __init__(self):
        super().__init__()
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QColor("#200334"))
        self.setPalette(palette)

        self.setStyleSheet("""
            QLabel#time-map-title {
                font-family: "Mistrully";
                font-size: 36pt;
                color: #FF01F9;
                padding-bottom: 10px;
            }
            QFrame#timeline-grid {
                border: 1px solid #3DF6FF;
                border-radius: 5px;
                background-color: transparent;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # 1. Header
        title_label = QLabel("Time Crisis Astrology")
        title_label.setObjectName("time-map-title")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 2. Timescale Buttons
        timescale_layout = QHBoxLayout()
        timescale_layout.addStretch()
        self.btn_3_month = StyledButton("3 Month")
        self.btn_6_month = StyledButton("6 Month")
        self.btn_12_month = StyledButton("12 Month")
        timescale_layout.addWidget(self.btn_3_month)
        timescale_layout.addWidget(self.btn_6_month)
        timescale_layout.addWidget(self.btn_12_month)
        timescale_layout.addStretch()

        # --- Connect Signals ---
        self.btn_3_month.clicked.connect(lambda: self.timeline_grid.set_timescale(3))
        self.btn_6_month.clicked.connect(lambda: self.timeline_grid.set_timescale(6))
        self.btn_12_month.clicked.connect(lambda: self.timeline_grid.set_timescale(12))

        # 3. Timeline Grid Container
        self.timeline_grid = TimelineGridWidget()

        # Add widgets to main layout
        main_layout.addWidget(title_label, 0, Qt.AlignmentFlag.AlignTop)
        main_layout.addLayout(timescale_layout)
        main_layout.addWidget(self.timeline_grid, 1)

    def set_chart_data(self, birth_date, natal_planets, natal_houses):
        """Passes the natal chart data down to the timeline grid widget."""
        self.timeline_grid.set_chart_data(birth_date, natal_planets, natal_houses)