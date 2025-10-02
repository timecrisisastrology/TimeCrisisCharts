import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

# Ensure the application can find the root modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from main_app import MainWindow, load_fonts

def run_verification():
    # Set up for headless execution
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'

    app = QApplication(sys.argv)

    # CRITICAL: Load custom fonts before creating the main window
    load_fonts()

    window = MainWindow()
    window.show()
    window.resize(1280, 1024) # Set a consistent size for screenshots

    # --- Step 1: Generate a Natal Chart ---
    # Use the correct attribute names as defined in MainWindow
    window.name_input.setText("Jane Doe")
    window.birth_date_input.setText("1989-05-15")
    window.birth_time_input.setText("08:30")
    window.ampm_input.setCurrentText("AM")
    window.location_input.setText("Providence, RI, USA")

    # Trigger the chart calculation by calling the correct handler
    window.handle_generate_chart()

    # --- Step 2: Switch to Transit (Bi-wheel) View ---
    # Programmatically set the chart type to transits, which is more reliable
    window.set_chart_type('predictive', 'transit')

    # --- Step 3: Capture Screenshot ---
    # Use a timer to ensure the UI has fully updated before taking a screenshot
    screenshot_path = os.path.abspath("jules-scratch/verification/advanced_layout_verification.png")
    QTimer.singleShot(2000, lambda: (
        print(f"Saving screenshot to {screenshot_path}"),
        window.grab().save(screenshot_path),
        app.quit()
    ))

    # Start the application event loop
    app.exec()
    print("Verification script finished.")

if __name__ == "__main__":
    run_verification()