import sys
import os
from datetime import datetime, timezone, timedelta
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QGridLayout, QLabel, QVBoxLayout, QHBoxLayout, QLineEdit, QStackedWidget
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QPalette, QColor, QFontDatabase
from widgets import InfoPanel, StyledButton, ChartDrawingWidget
from time_map_widget import TimeMapWidget
from astro_engine import (
    calculate_natal_chart, calculate_aspects, calculate_transits,
    calculate_secondary_progressions, calculate_solar_return
)

def load_fonts():
    """Loads all .otf, .woff, and .ttf fonts from the 'fonts' directory."""
    font_dir = "fonts"
    if not os.path.exists(font_dir):
        print(f"Font directory '{font_dir}' not found.")
        return
    for font_file in os.listdir(font_dir):
        if font_file.lower().endswith(('.otf', '.woff', '.ttf')):
            font_path = os.path.join(font_dir, font_file)
            font_id = QFontDatabase.addApplicationFont(font_path)
            if font_id == -1:
                print(f"Warning: Failed to load font '{font_path}'. May not be a valid font file.")
            else:
                families = QFontDatabase.applicationFontFamilies(font_id)
                # print(f"Successfully loaded font '{font_path}' with families: {families}")

class MainWindow(QMainWindow):
    """The main window of the application."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Time Crisis Astrology")
        self.setGeometry(100, 100, 1200, 800)

        # --- State Management ---
        self.current_chart_type = 'natal'
        self.current_date = datetime.now(timezone.utc)
        self.reloc_lat = 41.87 # Pawtucket, RI default
        self.reloc_lon = -71.38

        # --- Store Chart Data ---
        self.sample_birth_date = datetime(1990, 5, 15, 8, 30, 0, tzinfo=timezone.utc)
        self.london_lat = 51.5074
        self.london_lon = -0.1278
        self.natal_planets, self.natal_houses = calculate_natal_chart(self.sample_birth_date, self.london_lat, self.london_lon)
        self.natal_aspects = calculate_aspects(self.natal_planets, 7)

        # --- Setup UI ---
        self._setup_ui()

    def _setup_ui(self):
        """Initializes all user interface components."""
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#200334"))
        self.setPalette(palette)
        
        main_widget = QWidget()
        self.grid_layout = QGridLayout(main_widget)
        self.grid_layout.setContentsMargins(10, 20, 10, 10)

        self._create_info_panels()
        self._create_toolbar()
        self._create_chart_area()
        self._configure_layout()
        
        self.setCentralWidget(main_widget)
        self._connect_signals()
        self.update_chart() # Initial chart display

    def _create_info_panels(self):
        natal_data = {
            "Name": "Jane Doe", "Birth Date": "15 May 1989", "Birth Time": "08:30 AM",
            "Location": "London, UK", "Coords": f"{self.london_lat:.2f}° N, {self.london_lon:.2f}° W"
        }
        birth_info_panel = InfoPanel("Natal Chart Data", natal_data)

        # --- NEW: Relocation input fields ---
        self.lat_input = QLineEdit(str(self.reloc_lat))
        self.lon_input = QLineEdit(str(self.reloc_lon))
        self.date_label = QLabel(self.current_date.strftime("%d %b %Y, %H:%M:%S %Z"))

        transit_data = {
            "Date": self.date_label,
            "Reloc Lat": self.lat_input,
            "Reloc Lon": self.lon_input,
        }
        self.transit_info_panel = InfoPanel("Dynamic Chart Controls", transit_data)
        self.grid_layout.addWidget(birth_info_panel, 0, 0)
        self.grid_layout.addWidget(self.transit_info_panel, 0, 1)

    def _create_toolbar(self):
        toolbar_container = QWidget()
        main_toolbar_layout = QVBoxLayout(toolbar_container)

        # --- Chart Type Buttons ---
        chart_type_layout = QVBoxLayout()
        self.btn_natal = StyledButton("Natal")
        self.btn_transit = StyledButton("Transit")
        self.btn_progression = StyledButton("Progression")
        self.btn_solar_return = StyledButton("Solar Return")
        self.btn_time_map = StyledButton("Time Map") # --- NEW BUTTON ---
        chart_type_layout.addWidget(self.btn_natal)
        chart_type_layout.addWidget(self.btn_transit)
        chart_type_layout.addWidget(self.btn_progression)
        chart_type_layout.addWidget(self.btn_solar_return)
        chart_type_layout.addSpacing(20)
        chart_type_layout.addWidget(self.btn_time_map)

        # --- Time Scrolling Buttons ---
        time_scroll_layout = QGridLayout()
        self.time_buttons = {
            '<< DAY': -1, 'DAY >>': 1,
            '<< WEEK': -7, 'WEEK >>': 7,
            '<< MONTH': -30, 'MONTH >>': 30,
            '<< YEAR': -365, 'YEAR >>': 365
        }
        row, col = 0, 0
        for text, days in self.time_buttons.items():
            btn = StyledButton(text)
            btn.setProperty("days", days)
            time_scroll_layout.addWidget(btn, row, col)
            btn.clicked.connect(self.handle_time_scroll)
            col += 1
            if col > 1:
                col = 0
                row += 1

        main_toolbar_layout.addLayout(chart_type_layout)
        main_toolbar_layout.addSpacing(20)
        main_toolbar_layout.addWidget(QLabel("Time Scrolling"))
        main_toolbar_layout.addLayout(time_scroll_layout)
        main_toolbar_layout.addStretch()
        self.grid_layout.addWidget(toolbar_container, 0, 2, 2, 1)

    def _create_chart_area(self):
        # --- NEW: Use QStackedWidget to manage views ---
        self.view_stack = QStackedWidget()
        self.chart_area = ChartDrawingWidget()
        self.time_map_area = TimeMapWidget()
        self.view_stack.addWidget(self.chart_area)
        self.view_stack.addWidget(self.time_map_area)

        self.grid_layout.addWidget(self.view_stack, 1, 0, 1, 2)

    def _configure_layout(self):
        self.grid_layout.setColumnStretch(0, 3)
        self.grid_layout.setColumnStretch(1, 3)
        self.grid_layout.setColumnStretch(2, 1)
        self.grid_layout.setRowStretch(0, 0)
        self.grid_layout.setRowStretch(1, 1)

    def _connect_signals(self):
        self.btn_natal.clicked.connect(lambda: self.set_chart_type('natal'))
        self.btn_transit.clicked.connect(lambda: self.set_chart_type('transit'))
        self.btn_progression.clicked.connect(lambda: self.set_chart_type('progression'))
        self.btn_solar_return.clicked.connect(lambda: self.set_chart_type('solar_return'))
        self.btn_time_map.clicked.connect(self.show_time_map_view)
        self.lat_input.editingFinished.connect(self.handle_relocation)
        self.lon_input.editingFinished.connect(self.handle_relocation)

    def set_chart_type(self, chart_type):
        self.current_chart_type = chart_type
        self.view_stack.setCurrentWidget(self.chart_area) # Switch to chart view
        self.update_chart()

    def show_time_map_view(self):
        self.time_map_area.set_chart_data("Jane Doe", self.sample_birth_date, self.natal_planets, self.natal_houses)
        self.view_stack.setCurrentWidget(self.time_map_area) # Switch to time map view

    def handle_time_scroll(self):
        sender = self.sender()
        days_to_add = sender.property("days")
        self.current_date += timedelta(days=days_to_add)
        self.update_chart()

    def handle_relocation(self):
        try:
            self.reloc_lat = float(self.lat_input.text())
            self.reloc_lon = float(self.lon_input.text())
            self.update_chart()
        except ValueError:
            # Handle invalid input gracefully if needed
            print("Invalid coordinates entered.")

    def update_chart(self):
        """The central method to recalculate and redraw the chart based on current state."""
        self.date_label.setText(self.current_date.strftime("%d %b %Y, %H:%M:%S %Z"))
        
        if self.current_chart_type == 'natal':
            self.chart_area.set_chart_data(self.natal_planets, self.natal_houses, self.natal_aspects)
        
        elif self.current_chart_type == 'transit':
            transit_planets = calculate_transits(self.current_date)
            self.chart_area.set_chart_data(
                self.natal_planets, self.natal_houses, [], outer_planets=transit_planets
            )
        
        elif self.current_chart_type == 'progression':
            progressed_planets = calculate_secondary_progressions(self.sample_birth_date, self.current_date)
            self.chart_area.set_chart_data(
                self.natal_planets, self.natal_houses, [], outer_planets=progressed_planets
            )

        elif self.current_chart_type == 'solar_return':
            sr_year = self.current_date.year
            sr_planets, sr_houses, _ = calculate_solar_return(self.sample_birth_date, sr_year, self.reloc_lat, self.reloc_lon)
            self.chart_area.set_chart_data(
                self.natal_planets, self.natal_houses, [], outer_planets=sr_planets, display_houses=sr_houses
            )

# --- Main execution block ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    load_fonts() # Load all custom fonts
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
