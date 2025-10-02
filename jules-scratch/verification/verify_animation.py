import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from main_app import MainWindow, load_fonts

# This is a dedicated verification script to test the animation controls.
# It will:
# 1. Launch the application.
# 2. Switch to the 'Transit' chart view.
# 3. Click the '>>' button to advance the chart time by one day (the default).
# 4. Take a screenshot to visually confirm the new UI and that the date has updated.
# 5. Exit.

app = None
window = None

def run_verification_steps():
    """Function to perform the UI interactions."""
    global window
    try:
        print("Running verification steps...")
        # 1. Switch to Transit view to enable animation controls
        window.btn_transit.click()
        print("Clicked 'Transit' button.")

        # 2. Click the forward animation button
        window.btn_anim_forward.click()
        print("Clicked '>>' (forward) animation button.")

        # 3. Schedule the screenshot and exit
        QTimer.singleShot(500, save_screenshot_and_exit) # Wait 500ms for UI to update

    except Exception as e:
        print(f"An error occurred during UI interaction: {e}")
        if app:
            app.quit()
        sys.exit(1)


def save_screenshot_and_exit():
    """Saves a screenshot of the window and closes the application."""
    global window, app
    screenshot_path = "jules-scratch/verification/verification.png"
    print(f"Attempting to save screenshot to {screenshot_path}...")
    try:
        # Ensure the directory exists
        if not os.path.exists("jules-scratch/verification"):
            os.makedirs("jules-scratch/verification")

        screenshot = window.grab()
        success = screenshot.save(screenshot_path, "png")

        if success:
            print(f"SUCCESS: Screenshot saved to {screenshot_path}.")
        else:
            print(f"CRITICAL ERROR: Failed to save screenshot to {screenshot_path}.")
            sys.exit(1)

    except Exception as e:
        print(f"An error occurred during screenshot: {e}")
        sys.exit(1)
    finally:
        print("Exiting application.")
        if app:
            app.quit()
        sys.exit(0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    try:
        # It's critical to load fonts before creating the main window,
        # otherwise the astrological glyphs will not render correctly in the screenshot.
        load_fonts()

        window = MainWindow()
        window.show()
        print("MainWindow created successfully. Starting verification...")

        # Use a QTimer to allow the UI to fully render before interacting with it.
        QTimer.singleShot(2000, run_verification_steps)

        sys.exit(app.exec())

    except Exception as e:
        print(f"An error occurred during application startup: {e}")
        sys.exit(1)