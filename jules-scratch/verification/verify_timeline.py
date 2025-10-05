import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer, QDate

# Ensure the application can find the root modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from main_app import MainWindow, load_fonts

def run_verification():
    """
    This script automates the process of verifying the Time Map fix.
    It performs the following steps:
    1. Sets the environment for headless execution.
    2. Initializes the application and loads necessary fonts.
    3. Populates the input fields with test data for "Jason".
    4. Generates the chart to update the application's state.
    5. Switches the view to the Time Map.
    6. Sets a specific date and timescale for consistent output.
    7. Waits for the UI to render and then saves a screenshot.
    8. Exits the application.
    """
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    app = QApplication(sys.argv)

    # 1. Load fonts and create the main window
    load_fonts()
    window = MainWindow()

    # 2. Set input data to match the user's scenario
    window.name_input.setText("Jason")
    window.birth_date_input.setText("1992-06-20")
    window.birth_time_input.setText("04:15")
    window.ampm_input.setCurrentText("AM")
    window.location_input.setText("Boston, MA, USA")

    # 3. Generate the chart to ensure data is loaded into the app's state
    window.handle_generate_chart()

    # 4. Switch to the Time Map view
    window.show_time_map_view()

    # 5. Set a consistent view for the timeline
    time_map_widget = window.time_map_area
    time_map_widget.date_edit.setDate(QDate(2025, 10, 5))
    time_map_widget._handle_timescale_changed(6) # Set to 6 months

    # 6. Use QTimer to delay the screenshot, allowing the UI to fully render
    # The screenshot function now resides in the MainWindow class.
    QTimer.singleShot(2000, window.save_screenshot_and_exit)

    # Show the window (necessary for rendering, even in offscreen mode)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    run_verification()