import sys
import os
import json
from datetime import datetime, timezone, timedelta
import pytz
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

# Set the Qt platform plugin to 'offscreen' to allow the application to run
# in a headless environment for testing and screenshot generation.
# os.environ['QT_QPA_PLATFORM'] = 'offscreen'

from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QGridLayout, QLabel, QVBoxLayout, QHBoxLayout, QLineEdit, QStackedWidget, QFileDialog, QComboBox, QMessageBox
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QPalette, QColor, QFontDatabase
from widgets import InfoPanel, StyledButton, ChartDrawingWidget
from time_map_widget import TimeMapWidget
from astro_engine import (
    calculate_natal_chart, calculate_aspects, calculate_transits,
    calculate_secondary_progressions, calculate_solar_return
)

# --- Global variable to hold the correct font name ---
ASTRO_FONT_NAME = None

def load_fonts():
    """
    Loads all fonts from the 'fonts' directory. For the astrological font,
    it programmatically discovers the family name to ensure reliability,
    as hardcoded names can be brittle.
    """
    global ASTRO_FONT_NAME
    font_dir = "fonts"
    astro_font_path = os.path.join(font_dir, "EnigmaAstrology2.ttf")

    # Load the specific astrological font
    font_id = QFontDatabase.addApplicationFont(astro_font_path)

    if font_id != -1:
        # Programmatically get the family name from the font file itself.
        # This is the most reliable way to ensure the correct font is used.
        family = QFontDatabase.applicationFontFamilies(font_id)[0]
        ASTRO_FONT_NAME = family
        print(f"SUCCESS: Astrological font '{astro_font_path}' loaded. Discovered family name: '{ASTRO_FONT_NAME}'")
    else:
        print(f"CRITICAL ERROR: Failed to load the required astrological font from '{astro_font_path}'.")
        # As a fallback, try to use a generic font, although glyphs will be missing.
        ASTRO_FONT_NAME = "Arial"

    # Optionally, load other fonts if needed, without the complex discovery
    for font_file in os.listdir(font_dir):
        if font_file.lower().endswith(('.otf', '.woff', '.ttf')) and font_file != "EnigmaAstrology2.ttf":
            font_path = os.path.join(font_dir, font_file)
            if QFontDatabase.addApplicationFont(font_path) == -1:
                print(f"WARNING: Failed to load font '{font_path}'.")
            else:
                print(f"INFO: Loaded general font '{font_path}'.")

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
        # Apply global styles for QComboBox to match the application's theme.
        # This ensures that the AM/PM and House System dropdowns are branded.
        self.setStyleSheet("""
            QComboBox {
                color: #94EBFF;
                font-family: "Titillium Web";
                font-size: 10pt;
                background-color: #200334;
                border: 1px solid #3DF6FF;
                border-radius: 5px;
                padding: 5px;
            }
            QComboBox:hover {
                background-color: #3DF6FF;
                color: #200334;
            }
            QComboBox QAbstractItemView {
                background-color: #200334;
                border: 1px solid #3DF6FF;
                selection-background-color: #3DF6FF;
                selection-color: #200334;
                color: #94EBFF;
                outline: 0px;
            }
            QComboBox::drop-down {
                border: none;
            }
        """)

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
        # --- Natal Chart Input Fields ---
        self.name_input = QLineEdit("Jane Doe")
        self.birth_date_input = QLineEdit("1989-05-15")
        self.birth_time_input = QLineEdit("08:30")

        # --- AM/PM Selector ---
        self.ampm_input = QComboBox()
        self.ampm_input.addItems(["AM", "PM"])

        # --- Layout for time input ---
        time_layout = QHBoxLayout()
        time_layout.setContentsMargins(0, 0, 0, 0)
        time_layout.addWidget(self.birth_time_input)
        time_layout.addWidget(self.ampm_input)
        time_widget = QWidget()
        time_widget.setLayout(time_layout)

        self.location_input = QLineEdit("Providence, RI, USA")
        self.house_system_input = QComboBox()

        # --- House System Options ---
        self.house_systems = {
            "Placidus": "P", "Koch": "K", "Regiomontanus": "R",
            "Campanus": "C", "Equal": "E", "Whole Sign": "W"
        }
        self.house_system_input.addItems(self.house_systems.keys())


        natal_data = {
            "Name": self.name_input,
            "Birth Date (YYYY-MM-DD)": self.birth_date_input,
            "Birth Time (HH:MM)": time_widget,
            "Location": self.location_input,
            "House System": self.house_system_input,
        }

        # This will be a new VBox layout to hold the panel and the button
        birth_info_container = QWidget()
        birth_info_layout = QVBoxLayout(birth_info_container)
        birth_info_layout.setContentsMargins(0,0,0,0)

        birth_info_panel = InfoPanel("Natal Chart Data", natal_data)
        self.btn_generate_chart = StyledButton("Generate Chart")

        # --- File Operations Buttons ---
        file_ops_layout = QHBoxLayout()
        self.btn_save_chart = StyledButton("Save Chart")
        self.btn_load_chart = StyledButton("Load Chart")
        file_ops_layout.addWidget(self.btn_save_chart)
        file_ops_layout.addWidget(self.btn_load_chart)

        birth_info_layout.addWidget(birth_info_panel)
        birth_info_layout.addWidget(self.btn_generate_chart)
        birth_info_layout.addLayout(file_ops_layout)

        # --- Dynamic Chart Controls ---
        self.lat_input = QLineEdit(str(self.reloc_lat))
        self.lon_input = QLineEdit(str(self.reloc_lon))
        self.date_label = QLabel(self.current_date.strftime("%d %b %Y, %H:%M:%S %Z"))

        transit_data = {
            "Date": self.date_label,
            "Reloc Lat": self.lat_input,
            "Reloc Lon": self.lon_input,
        }
        self.transit_info_panel = InfoPanel("Dynamic Chart Controls", transit_data)
        self.grid_layout.addWidget(birth_info_container, 0, 0)
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
        # Pass the global font name to the drawing widget, ensuring dependency injection.
        self.chart_area = ChartDrawingWidget(ASTRO_FONT_NAME)
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
        self.btn_generate_chart.clicked.connect(self.handle_generate_chart)
        self.btn_save_chart.clicked.connect(self.handle_save_chart)
        self.btn_load_chart.clicked.connect(self.handle_load_chart)

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

    def handle_generate_chart(self):
        """
        Reads natal data from the input fields, calculates the new chart,
        and updates the application state and display.
        """
        try:
            # 1. Initialize geocoding tools
            geolocator = Nominatim(user_agent="timecrisis-astrology")
            tf = TimezoneFinder()

            # 2. Parse the input values
            name = self.name_input.text()
            date_str = self.birth_date_input.text()
            time_str = self.birth_time_input.text()
            ampm_str = self.ampm_input.currentText()
            location_str = self.location_input.text()

            # 3. Geocode the location to get lat, lon, and timezone
            location = geolocator.geocode(location_str)
            if not location:
                QMessageBox.critical(self, "Error", f"Could not find location: '{location_str}'. Please check the spelling or try a different format (e.g., 'City, State, Country').")
                return

            lat = location.latitude
            lon = location.longitude
            tz_name = tf.timezone_at(lng=lon, lat=lat)
            if not tz_name:
                QMessageBox.critical(self, "Error", f"Could not determine the timezone for the location: {location.address}.")
                return

            local_tz = pytz.timezone(tz_name)

            # 4. Combine date and time, localize to the found timezone, and convert to UTC
            birth_dt_str = f"{date_str} {time_str} {ampm_str}"
            naive_datetime = datetime.strptime(birth_dt_str, '%Y-%m-%d %I:%M %p')
            local_datetime = local_tz.localize(naive_datetime)
            birth_datetime_utc = local_datetime.astimezone(timezone.utc)

            # 5. Recalculate the natal chart and aspects
            selected_house_system_name = self.house_system_input.currentText()
            house_system_code = self.house_systems[selected_house_system_name]
            self.natal_planets, self.natal_houses = calculate_natal_chart(birth_datetime_utc, lat, lon, house_system=bytes(house_system_code, 'utf-8'))
            self.natal_aspects = calculate_aspects(self.natal_planets, 7) # Using a default orb of 7

            # Store the new birth date for use in other calculations
            self.sample_birth_date = birth_datetime_utc

            # 6. Update the chart display
            print(f"Successfully generated new chart for {name} in {location.address}.")
            self.update_chart()

        except ValueError:
            QMessageBox.critical(self, "Error", "Invalid Date or Time Format. Please use YYYY-MM-DD for date and HH:MM for time (e.g., 08:30).")
        except Exception as e:
            QMessageBox.critical(self, "An Unexpected Error Occurred", f"An unexpected error occurred: {e}")

    def handle_save_chart(self):
        """
        Opens a file dialog to save the current natal chart data to a JSON file.
        """
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Chart", "", "JSON Files (*.json);;All Files (*)")
        if file_name:
            chart_data = {
                "name": self.name_input.text(),
                "birth_date": self.birth_date_input.text(),
                "birth_time": self.birth_time_input.text(),
                "ampm": self.ampm_input.currentText(),
                "location": self.location_input.text(),
                "house_system": self.house_system_input.currentText(),
            }
            try:
                with open(file_name, 'w') as f:
                    json.dump(chart_data, f, indent=4)
                print(f"Chart data saved to {file_name}")
            except IOError as e:
                print(f"Error saving file: {e}")

    def handle_load_chart(self):
        """
        Opens a file dialog to load natal chart data from a JSON file,
        populates the fields, and generates the chart.
        """
        file_name, _ = QFileDialog.getOpenFileName(self, "Load Chart", "", "JSON Files (*.json);;All Files (*)")
        if file_name:
            try:
                with open(file_name, 'r') as f:
                    chart_data = json.load(f)

                # Populate the input fields with the loaded data
                self.name_input.setText(chart_data.get("name", ""))
                self.birth_date_input.setText(chart_data.get("birth_date", ""))
                self.birth_time_input.setText(chart_data.get("birth_time", ""))
                self.ampm_input.setCurrentText(chart_data.get("ampm", "AM"))
                self.location_input.setText(chart_data.get("location", ""))
                self.house_system_input.setCurrentText(chart_data.get("house_system", "Placidus"))

                # Automatically generate the chart with the loaded data
                self.handle_generate_chart()
                print(f"Chart data loaded from {file_name}")

            except (IOError, json.JSONDecodeError) as e:
                print(f"Error loading file: {e}")
            except Exception as e:
                print(f"An unexpected error occurred during chart loading: {e}")

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

    def save_screenshot_and_exit(self):
        """Saves a screenshot of the window and closes the application."""
        # Ensure the directory exists
        if not os.path.exists("jules-scratch/verification"):
            os.makedirs("jules-scratch/verification")

        screenshot_path = "jules-scratch/verification/verification.png"
        print(f"Attempting to save screenshot to {screenshot_path}...")
        screenshot = self.grab()
        success = screenshot.save(screenshot_path, "png")

        if success:
            print(f"SUCCESS: Screenshot saved to {screenshot_path}.")
        else:
            print(f"CRITICAL ERROR: Failed to save screenshot to {screenshot_path}.")

        print("Exiting application.")
        QApplication.quit()

# --- Main execution block ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    load_fonts() # Load all custom fonts
    window = MainWindow()
    window.show()

    # The QTimer line was removed by Jules to ensure the application runs interactively.

    sys.exit(app.exec())
