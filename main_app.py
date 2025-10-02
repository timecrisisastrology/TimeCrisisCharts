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

import swisseph as swe
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QGridLayout, QLabel, QVBoxLayout, QHBoxLayout, QLineEdit, QStackedWidget, QFileDialog, QComboBox, QMessageBox, QFrame)
from PyQt6.QtCore import QTimer, Qt
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
        self.grid_layout.setContentsMargins(20, 20, 20, 20) # Increased margins

        # --- Create UI Components ---
        self.birth_info_container = self._create_natal_panel()
        self.dynamic_controls_container = self._create_dynamic_controls_panel()
        self.toolbar_container = self._create_toolbar()
        self.view_stack = self._create_chart_area()

        # --- Configure Layout ---
        self._configure_layout()
        
        self.setCentralWidget(main_widget)
        self._connect_signals()
        self.update_chart() # Initial chart display

    def _create_natal_panel(self):
        """Creates the panel for natal chart data input."""
        self.name_input = QLineEdit("Jane Doe")
        self.birth_date_input = QLineEdit("1989-05-15")
        self.birth_time_input = QLineEdit("08:30")
        self.ampm_input = QComboBox()
        self.ampm_input.addItems(["AM", "PM"])

        time_layout = QHBoxLayout()
        time_layout.setContentsMargins(0, 0, 0, 0)
        time_layout.addWidget(self.birth_time_input)
        time_layout.addWidget(self.ampm_input)
        time_widget = QWidget()
        time_widget.setLayout(time_layout)

        self.location_input = QLineEdit("Providence, RI, USA")
        self.house_system_input = QComboBox()
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

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0,0,0,0)

        birth_info_panel = InfoPanel("Natal Chart Data", natal_data)
        self.btn_generate_chart = StyledButton("Generate Chart")

        file_ops_layout = QHBoxLayout()
        self.btn_save_chart = StyledButton("Save Chart")
        self.btn_load_chart = StyledButton("Load Chart")
        file_ops_layout.addWidget(self.btn_save_chart)
        file_ops_layout.addWidget(self.btn_load_chart)

        layout.addWidget(birth_info_panel)
        layout.addWidget(self.btn_generate_chart)
        layout.addLayout(file_ops_layout)
        return container

    def _create_dynamic_controls_panel(self):
        """Creates the panel for dynamic controls like date, time, and relocation."""
        self.date_label = QLabel(self.current_date.strftime("%d %b %Y, %H:%M:%S %Z"))
        self.transit_location_input = QLineEdit("Pawtucket, RI, USA") # New location input
        self.lat_input = QLineEdit(str(self.reloc_lat))
        self.lon_input = QLineEdit(str(self.reloc_lon))

        transit_data = {
            "Date": self.date_label,
            "Reloc Location": self.transit_location_input, # New field
            "Reloc Lat": self.lat_input,
            "Reloc Lon": self.lon_input,
        }
        # The InfoPanel is now the container
        return InfoPanel("Dynamic Chart Controls", transit_data)

    def _create_toolbar(self):
        """Creates the right-side toolbar with navigation and time controls."""
        container = QWidget()
        main_layout = QVBoxLayout(container)

        # --- Chart Type Selection ---
        chart_type_layout = QVBoxLayout()
        self.btn_natal = StyledButton("Natal")
        self.btn_transit = StyledButton("Transit")
        self.btn_progression = StyledButton("Progression")
        self.btn_solar_return = StyledButton("Solar Return")
        self.btn_time_map = StyledButton("Time Map")
        chart_type_layout.addWidget(self.btn_natal)
        chart_type_layout.addWidget(self.btn_transit)
        chart_type_layout.addWidget(self.btn_progression)
        chart_type_layout.addWidget(self.btn_solar_return)
        chart_type_layout.addSpacing(20)
        chart_type_layout.addWidget(self.btn_time_map)
        main_layout.addLayout(chart_type_layout)
        main_layout.addSpacing(20)

        # --- New Animation Control Box ---
        # This section replaces the old grid of buttons with a modern dropdown and forward/backward controls.
        animation_container = QWidget()
        animation_layout = QVBoxLayout(animation_container)
        animation_layout.setContentsMargins(0,0,0,0)
        animation_layout.setSpacing(10)

        # Title for the animation section
        animation_title = QLabel("Animate Chart")
        animation_title.setObjectName("panel-title") # Re-use style from InfoPanel
        animation_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Create a styled frame to group the controls aesthetically
        control_frame = QFrame()
        control_frame.setObjectName("container") # Re-use style from InfoPanel
        control_frame.setStyleSheet("""
            #container {
                background-color: #200334;
                border: 1px solid #3DF6FF;
                border-radius: 5px;
                padding: 10px;
            }
            #panel-title {
                color: #FF01F9;
                font-family: "TT Supermolot Neue Condensed";
                font-size: 14pt;
                font-weight: bold;
                padding-bottom: 5px;
            }
        """)

        frame_layout = QHBoxLayout(control_frame)
        frame_layout.setContentsMargins(5,5,5,5)
        frame_layout.setSpacing(5)

        # Backward and Forward buttons
        self.btn_anim_backward = StyledButton("<<")
        self.btn_anim_forward = StyledButton(">>")

        # Dropdown for time interval selection
        self.animation_step_input = QComboBox()
        self.animation_intervals = [
            "1 Second", "15 Seconds", "30 Seconds", "1 Minute", "15 Minutes",
            "30 Minutes", "Hour", "Day", "Week", "Month", "Year"
        ]
        self.animation_step_input.addItems(self.animation_intervals)
        self.animation_step_input.setCurrentText("Day") # Default value

        # Add controls to the frame
        frame_layout.addWidget(self.btn_anim_backward)
        frame_layout.addWidget(self.animation_step_input)
        frame_layout.addWidget(self.btn_anim_forward)

        # Add title and frame to the main animation container
        animation_layout.addWidget(animation_title)
        animation_layout.addWidget(control_frame)

        main_layout.addWidget(animation_container)
        main_layout.addStretch() # Pushes everything to the top
        return container

    def _create_chart_area(self):
        """Creates the central chart display area."""
        view_stack = QStackedWidget()
        self.chart_area = ChartDrawingWidget(ASTRO_FONT_NAME)
        self.time_map_area = TimeMapWidget()
        view_stack.addWidget(self.chart_area)
        view_stack.addWidget(self.time_map_area)
        return view_stack

    def _configure_layout(self):
        """Configures the main grid layout."""
        # Add widgets to the grid
        self.grid_layout.addWidget(self.birth_info_container, 0, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.grid_layout.addWidget(self.dynamic_controls_container, 0, 2, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        self.grid_layout.addWidget(self.toolbar_container, 1, 2)
        self.grid_layout.addWidget(self.view_stack, 0, 1, 2, 1) # Chart spans two rows in the middle column

        # Configure stretching
        self.grid_layout.setColumnStretch(0, 1) # Left panel
        self.grid_layout.setColumnStretch(1, 4) # Central chart (takes up the most space)
        self.grid_layout.setColumnStretch(2, 1) # Right panel
        self.grid_layout.setRowStretch(0, 1)
        self.grid_layout.setRowStretch(1, 1)

    def _connect_signals(self):
        """Connects all UI component signals to their respective slots."""
        # Chart type buttons
        self.btn_natal.clicked.connect(lambda: self.set_chart_type('natal'))
        self.btn_transit.clicked.connect(lambda: self.set_chart_type('transit'))
        self.btn_progression.clicked.connect(lambda: self.set_chart_type('progression'))
        self.btn_solar_return.clicked.connect(lambda: self.set_chart_type('solar_return'))
        self.btn_time_map.clicked.connect(self.show_time_map_view)

        # Animation control buttons
        self.btn_anim_backward.clicked.connect(lambda: self.handle_animation_step(-1))
        self.btn_anim_forward.clicked.connect(lambda: self.handle_animation_step(1))

        # Relocation inputs
        self.lat_input.editingFinished.connect(self.handle_manual_relocation)
        self.lon_input.editingFinished.connect(self.handle_manual_relocation)
        self.transit_location_input.editingFinished.connect(self.handle_transit_relocation)

        # Chart generation and file operations
        self.btn_generate_chart.clicked.connect(self.handle_generate_chart)
        self.btn_save_chart.clicked.connect(self.handle_save_chart)
        self.btn_load_chart.clicked.connect(self.handle_load_chart)

    def set_chart_type(self, chart_type):
        """Sets the current chart type and updates the view."""
        self.current_chart_type = chart_type
        self.view_stack.setCurrentWidget(self.chart_area) # Switch to chart view
        self.update_chart()

    def show_time_map_view(self):
        self.time_map_area.set_chart_data("Jane Doe", self.sample_birth_date, self.natal_planets, self.natal_houses)
        self.view_stack.setCurrentWidget(self.time_map_area) # Switch to time map view

    def handle_animation_step(self, direction):
        """
        Handles stepping the chart forward or backward in time based on the
        selected interval in the QComboBox.
        """
        interval_text = self.animation_step_input.currentText()

        # Map the dropdown text to a timedelta object
        # Note: 'Month' and 'Year' are approximated for simplicity. A more precise
        # implementation might use dateutil.relativedelta.
        interval_map = {
            "1 Second": timedelta(seconds=1),
            "15 Seconds": timedelta(seconds=15),
            "30 Seconds": timedelta(seconds=30),
            "1 Minute": timedelta(minutes=1),
            "15 Minutes": timedelta(minutes=15),
            "30 Minutes": timedelta(minutes=30),
            "Hour": timedelta(hours=1),
            "Day": timedelta(days=1),
            "Week": timedelta(weeks=1),
            "Month": timedelta(days=30), # Approximation
            "Year": timedelta(days=365)  # Approximation
        }

        delta = interval_map.get(interval_text, timedelta(days=1))

        # Apply the change
        self.current_date += (delta * direction)

        # Refresh the chart display
        self.update_chart()

    def handle_manual_relocation(self):
        """Handles lat/lon changes and updates the chart."""
        try:
            self.reloc_lat = float(self.lat_input.text())
            self.reloc_lon = float(self.lon_input.text())
            # Clear the location name field since coordinates were entered manually
            self.transit_location_input.setText(f"Coords: {self.reloc_lat:.2f}, {self.reloc_lon:.2f}")
            self.update_chart()
        except ValueError:
            print("Invalid coordinates entered.")

    def handle_transit_relocation(self):
        """Geocodes the new transit location and updates the chart."""
        try:
            location_str = self.transit_location_input.text()
            if not location_str or location_str.startswith("Coords:"):
                return # Do nothing if the field is empty or shows coordinates

            geolocator = Nominatim(user_agent="timecrisis-astrology-reloc")
            location = geolocator.geocode(location_str)

            if location:
                self.reloc_lat = location.latitude
                self.reloc_lon = location.longitude
                self.lat_input.setText(f"{self.reloc_lat:.4f}")
                self.lon_input.setText(f"{self.lon_lon:.4f}")
                print(f"Relocated to {location.address} ({self.reloc_lat}, {self.reloc_lon})")
                self.update_chart()
            else:
                QMessageBox.warning(self, "Relocation Error", f"Could not find location: {location_str}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred during relocation: {e}")

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
        
        # Get the currently selected house system for all chart types
        selected_house_system_name = self.house_system_input.currentText()
        house_system_code = self.house_systems.get(selected_house_system_name, "P").encode('utf-8')

        if self.current_chart_type == 'natal':
            self.chart_area.set_chart_data(self.natal_planets, self.natal_houses, self.natal_aspects)
        
        elif self.current_chart_type == 'transit':
            transit_planets = calculate_transits(self.current_date)
            # Calculate transiting houses for the relocated position to find ASC/MC
            jd_utc = swe.utc_to_jd(self.current_date.year, self.current_date.month, self.current_date.day, self.current_date.hour, self.current_date.minute, self.current_date.second, 1)[1]
            transit_angles = swe.houses(jd_utc, self.reloc_lat, self.reloc_lon, house_system_code)[1]
            transit_planets['ASC'] = (transit_angles[0], 0.0) # Add Ascendant
            transit_planets['MC'] = (transit_angles[1], 0.0)  # Add Midheaven
            # Always display the natal houses
            self.chart_area.set_chart_data(
                self.natal_planets, self.natal_houses, [], outer_planets=transit_planets, display_houses=self.natal_houses
            )

        elif self.current_chart_type == 'progression':
            progressed_planets = calculate_secondary_progressions(self.sample_birth_date, self.current_date)
            # Calculate progressed houses for the relocated position to find ASC/MC
            days_offset = (self.current_date.date() - self.sample_birth_date.date()).days
            progression_date = self.sample_birth_date + timedelta(days=days_offset)
            jd_utc = swe.utc_to_jd(progression_date.year, progression_date.month, progression_date.day, progression_date.hour, progression_date.minute, progression_date.second, 1)[1]
            progressed_angles = swe.houses(jd_utc, self.reloc_lat, self.reloc_lon, house_system_code)[1]
            progressed_planets['ASC'] = (progressed_angles[0], 0.0) # Add Ascendant
            progressed_planets['MC'] = (progressed_angles[1], 0.0)  # Add Midheaven
            # Always display the natal houses
            self.chart_area.set_chart_data(
                self.natal_planets, self.natal_houses, [], outer_planets=progressed_planets, display_houses=self.natal_houses
            )

        elif self.current_chart_type == 'solar_return':
            sr_year = self.current_date.year
            # Pass the selected house system to the calculation
            sr_planets, sr_houses, _ = calculate_solar_return(self.sample_birth_date, sr_year, self.reloc_lat, self.reloc_lon, house_system=house_system_code)
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
