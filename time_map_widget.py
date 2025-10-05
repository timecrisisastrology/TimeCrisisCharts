import sys
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame, QDateEdit
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtCore import Qt, QDate
from widgets import StyledButton
from timeline_grid_widget import TimelineGridWidget
from astro_engine import calculate_secondary_progressions, calculate_lunar_phase
from datetime import datetime, timedelta

class TimeMapWidget(QWidget):
    """A custom widget to display the 'Time Map' timeline view."""
    def __init__(self, astro_font=None):
        super().__init__()

        self.astro_font = astro_font # Store the font

        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QColor("#000000")) # Changed background to black
        self.setPalette(palette)

        self.setStyleSheet("""
            QLabel {
                color: #94EBFF;
                font-family: "Titillium Web";
                font-size: 12pt;
            }
            QLabel#time-map-title {
                font-family: "Mistrully";
                font-size: 36pt;
                color: #FF01F9;
                padding-bottom: 10px;
            }
            QLabel.header-info {
                font-size: 14pt;
                font-weight: bold;
                color: #FFFFFF; /* White for better contrast */
            }
            QLabel.header-info-small {
                font-size: 11pt;
                color: #E0E0E0;
            }
            QFrame#timeline-grid {
                border: 1px solid #3DF6FF;
                border-radius: 5px;
                background-color: transparent;
            }
            QDateEdit {
                background-color: #1A1A1A;
                color: #FFFFFF;
                border: 1px solid #3DF6FF;
                border-radius: 4px;
                padding: 4px;
                font-family: "Titillium Web";
                font-size: 11pt;
            }
            QDateEdit::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left-width: 1px;
                border-left-color: #3DF6FF;
                border-left-style: solid;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
            }
        """)

        # --- Chart Data State ---
        self.natal_houses = []
        self.birth_date = None
        self.name = ""
        self.natal_planets = {}
        self.current_start_date = datetime.now()
        self.current_timescale_months = 3

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # 1. Header Layout
        header_layout = QHBoxLayout()
        header_layout.setSpacing(20)

        # -- Left Header --
        left_header_layout = QVBoxLayout()
        left_header_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.name_label = QLabel("Name: [Client Name]")
        self.name_label.setProperty("class", "header-info")
        self.date_range_label = QLabel("Year: [Date Range]")
        self.date_range_label.setProperty("class", "header-info-small")
        left_header_layout.addWidget(self.name_label)
        left_header_layout.addWidget(self.date_range_label)

        # -- Center Header --
        title_label = QLabel("Time Crisis Chart Plot")
        title_label.setObjectName("time-map-title")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # -- Right Header --
        right_header_layout = QVBoxLayout()
        right_header_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        self.lunar_phase_label = QLabel("Lunar Phase: [Phase] 00°")
        self.lunar_phase_label.setProperty("class", "header-info")
        self.moon_house_label = QLabel("House of Moon (P): [House]")
        self.moon_house_label.setProperty("class", "header-info-small")
        self.sun_house_label = QLabel("House of Sun (P): [House]")
        self.sun_house_label.setProperty("class", "header-info-small")
        right_header_layout.addWidget(self.lunar_phase_label)
        right_header_layout.addWidget(self.moon_house_label)
        right_header_layout.addWidget(self.sun_house_label)

        header_layout.addLayout(left_header_layout, 1)
        header_layout.addWidget(title_label, 2)
        header_layout.addLayout(right_header_layout, 1)


        # 2. Controls Layout (Date + Timescale)
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)
        controls_layout.addStretch()

        # -- Date Selector --
        date_label = QLabel("Start Date:")
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setFixedWidth(140)
        self.btn_go = StyledButton("Go")
        self.btn_go.setFixedWidth(50)


        # -- Timescale Buttons --
        self.btn_3_month = StyledButton("3 Month")
        self.btn_6_month = StyledButton("6 Month")
        self.btn_12_month = StyledButton("12 Month")

        controls_layout.addWidget(date_label)
        controls_layout.addWidget(self.date_edit)
        controls_layout.addWidget(self.btn_go)
        controls_layout.addSpacing(40) # Spacer
        controls_layout.addWidget(self.btn_3_month)
        controls_layout.addWidget(self.btn_6_month)
        controls_layout.addWidget(self.btn_12_month)
        controls_layout.addStretch()

        # --- Connect Signals ---
        self.btn_go.clicked.connect(self._handle_go_clicked)
        self.btn_3_month.clicked.connect(lambda: self._handle_timescale_changed(3))
        self.btn_6_month.clicked.connect(lambda: self._handle_timescale_changed(6))
        self.btn_12_month.clicked.connect(lambda: self._handle_timescale_changed(12))


        # 3. Timeline Grid Container
        self.timeline_grid = TimelineGridWidget(astro_font=self.astro_font)

        # Add widgets to main layout
        main_layout.addLayout(header_layout)
        main_layout.addLayout(controls_layout)
        main_layout.addWidget(self.timeline_grid, 1)


    def _handle_go_clicked(self):
        """Handles the 'Go' button click, updating the start date."""
        qdate = self.date_edit.date()
        self.current_start_date = datetime(qdate.year(), qdate.month(), qdate.day())
        self.update_time_map()

    def _handle_timescale_changed(self, months):
        """Handles timescale button clicks."""
        self.current_timescale_months = months
        self.update_time_map()

    def update_time_map(self):
        """Central method to update the entire time map view based on current settings."""
        if not self.birth_date:
            return # Don't update if no chart data is loaded

        # 1. Update Header Info based on the start date
        progressed_planets = calculate_secondary_progressions(self.birth_date, self.current_start_date)
        prog_sun_pos = progressed_planets['Sun'][0]
        prog_moon_pos = progressed_planets['Moon'][0]

        prog_sun_house = self._get_house_for_planet(prog_sun_pos)
        prog_moon_house = self._get_house_for_planet(prog_moon_pos)
        self.sun_house_label.setText(f"House of Sun (P): {prog_sun_house}th")
        self.moon_house_label.setText(f"House of Moon (P): {prog_moon_house}th")

        phase_name, phase_angle = calculate_lunar_phase(prog_sun_pos, prog_moon_pos)
        self.lunar_phase_label.setText(f"Lunar Phase: {phase_name} {int(phase_angle)}°")

        # 2. Update Date Range Label
        end_date = self.current_start_date + timedelta(days=self.current_timescale_months * 30)
        self.date_range_label.setText(f"Date Range: {self.current_start_date.strftime('%b %Y')} - {end_date.strftime('%b %Y')}")

        # 3. Update Timeline Grid
        self.timeline_grid.set_view(
            start_date=self.current_start_date,
            months=self.current_timescale_months
        )

    def _get_house_for_planet(self, planet_pos):
        """Finds the house number for a given planetary degree based on natal houses."""
        if not self.natal_houses: return 0
        for i in range(11):
            if self.natal_houses[i] <= planet_pos < self.natal_houses[i+1]: return i + 1
        if self.natal_houses[11] <= planet_pos < 360 or 0 <= planet_pos < self.natal_houses[0]: return 12
        return 0 # Should not happen with valid data

    def set_chart_data(self, name, birth_date, natal_planets, natal_houses):
        """Receives all chart data, populates header, and passes data down."""
        # Store data
        self.name = name
        self.birth_date = birth_date
        self.natal_planets = natal_planets
        self.natal_houses = natal_houses

        # --- Populate Header ---
        self.name_label.setText(f"Name: {name}")

        # --- Pass data to timeline grid ---
        self.timeline_grid.set_chart_data(birth_date, natal_planets, natal_houses)

        # --- Initialize the view ---
        self.date_edit.setDate(QDate.currentDate())
        self.current_start_date = datetime.now()
        self.current_timescale_months = 3 # Default to 3 months
        self.update_time_map()