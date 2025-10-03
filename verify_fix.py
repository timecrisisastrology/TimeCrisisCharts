import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from main_app import MainWindow, load_fonts

app = None
window = None

def take_screenshot_and_exit():
    """Grabs the window content and exits the application."""
    global window, app
    try:
        # Ensure the output directory exists
        output_dir = "jules-scratch/verification"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        screenshot_path = os.path.join(output_dir, "verification_screenshot.png")

        # Grab the content of the main window
        pixmap = window.grab()
        pixmap.save(screenshot_path)
        print(f"SUCCESS: Screenshot saved to {screenshot_path}")

    except Exception as e:
        print(f"CRITICAL: An error occurred during screenshot: {e}")
        if app:
            app.quit()
        sys.exit(1)
    finally:
        # Ensure the application exits cleanly
        if app:
            app.quit()
        sys.exit(0)

def setup_and_run_test():
    """Sets up the specific chart state for verification."""
    global window
    try:
        print("Setting up test case...")
        # 1. Set the natal chart data to the problematic one from the user's report.
        window.name_input.setText("Jane Doe")
        window.birth_date_input.setText("1989-05-15")
        window.birth_time_input.setText("08:30")
        window.ampm_input.setCurrentText("AM")
        window.location_input.setText("Providence, RI, USA")

        # 2. Programmatically "click" the generate chart button.
        # This calculates and displays the initial natal chart.
        print("Generating natal chart...")
        window.handle_generate_chart()

        # 3. Programmatically switch to the Transit (bi-wheel) view.
        # This will trigger the complex layout logic we are testing.
        print("Switching to transit (bi-wheel) view...")
        window.set_chart_type('predictive', 'transit')

        # 4. Use a QTimer to allow the UI to fully render before taking the screenshot.
        # 3 seconds should be sufficient for all calculations and drawing to complete.
        print("UI updated. Waiting 3 seconds for rendering to complete...")
        QTimer.singleShot(3000, take_screenshot_and_exit)

    except Exception as e:
        print(f"CRITICAL: An error occurred during test setup: {e}")
        if app:
            app.quit()
        sys.exit(1)


if __name__ == "__main__":
    # Set headless mode for automated testing environment
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'

    app = QApplication(sys.argv)

    try:
        # CRITICAL: Load custom fonts before creating the main window
        # to ensure astrological glyphs are rendered correctly in the screenshot.
        print("Loading fonts...")
        load_fonts()

        print("Creating MainWindow...")
        window = MainWindow()
        window.show() # Show the window to make it available for grabbing

        # Use a short delay to ensure the window is initialized before we manipulate it.
        QTimer.singleShot(500, setup_and_run_test)

        sys.exit(app.exec())

    except Exception as e:
        print(f"CRITICAL: An error occurred during application startup: {e}")
        sys.exit(1)