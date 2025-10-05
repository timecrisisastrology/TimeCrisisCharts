import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer, QDate, QCoreApplication
from main_app import MainWindow, load_fonts

app = None
window = None

def take_screenshot_and_continue(screenshot_name):
    """Takes a screenshot and prepares for the next step."""
    try:
        output_dir = "jules-scratch/verification"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        screenshot_path = os.path.join(output_dir, screenshot_name)
        pixmap = window.grab()
        pixmap.save(screenshot_path)
        print(f"SUCCESS: Screenshot saved to {screenshot_path}")
        return True
    except Exception as e:
        print(f"CRITICAL: An error occurred during screenshot: {e}")
        QCoreApplication.quit()
        sys.exit(1)

def step_4_final_screenshot_and_exit():
    """Final step: take the last screenshot and exit."""
    if take_screenshot_and_continue("time_map_6_month_view.png"):
        print("Verification sequence complete.")
    QCoreApplication.quit()
    sys.exit(0)

def step_3_change_timescale():
    """Third step: Change the timescale to 6 months."""
    print("Step 3: Changing timescale to 6 months...")
    try:
        time_map_widget = window.time_map_area
        time_map_widget.btn_6_month.click()
        QTimer.singleShot(2000, step_4_final_screenshot_and_exit)
    except Exception as e:
        print(f"CRITICAL: Failed to change timescale: {e}")
        QCoreApplication.quit()
        sys.exit(1)

def step_2_change_date_and_screenshot():
    """Second step: Change the date, click Go, and take a screenshot."""
    if not take_screenshot_and_continue("time_map_initial_view.png"):
        return

    print("Step 2: Changing date to 2025-01-15 and clicking Go...")
    try:
        time_map_widget = window.time_map_area
        time_map_widget.date_edit.setDate(QDate(2025, 1, 15))
        time_map_widget.btn_go.click()
        # Allow time for the grid to recalculate
        QTimer.singleShot(2000, step_3_change_timescale)
    except Exception as e:
        print(f"CRITICAL: Failed to change date: {e}")
        QCoreApplication.quit()
        sys.exit(1)

def step_1_setup_and_run_test():
    """First step: Load chart and switch to Time Map tab."""
    global window
    try:
        print("Step 1: Setting up test case...")
        # Load a default chart
        window.name_input.setText("Jules Verne")
        window.birth_date_input.setText("1985-02-08")
        window.birth_time_input.setText("12:00")
        window.ampm_input.setCurrentText("PM")
        window.location_input.setText("Nantes, France")
        window.handle_generate_chart()

        # Switch to the Time Map tab by programmatically clicking the button
        print("Switching to Time Map tab...")
        window.btn_time_map.click()

        QTimer.singleShot(2000, step_2_change_date_and_screenshot)

    except Exception as e:
        print(f"CRITICAL: An error occurred during test setup: {e}")
        QCoreApplication.quit()
        sys.exit(1)


if __name__ == "__main__":
    # Ensure PYTHONPATH is set to resolve modules correctly
    if '.' not in sys.path:
        sys.path.insert(0, '.')

    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    app = QApplication(sys.argv)

    try:
        print("Loading fonts...")
        load_fonts()

        print("Creating MainWindow...")
        window = MainWindow()
        window.show()

        QTimer.singleShot(500, step_1_setup_and_run_test)
        sys.exit(app.exec())

    except Exception as e:
        print(f"CRITICAL: An error occurred during application startup: {e}")
        sys.exit(1)