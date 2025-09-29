import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from main_app import MainWindow

app = None
window = None

def create_screenshot_and_exit():
    """Function to be called by QTimer to grab the window content and then exit."""
    global window, app
    try:
        # Grab the content of the main window
        pixmap = window.grab()
        # Save it to a file
        pixmap.save("chart_screenshot_final.png")
        print("Screenshot saved to chart_screenshot_final.png")
    except Exception as e:
        print(f"An error occurred during screenshot: {e}")
        if app:
            app.quit()
        sys.exit(1)
    finally:
        # Ensure the application exits
        if app:
            app.quit()
        sys.exit(0)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    try:
        window = MainWindow()
        window.show() # Show the window to make it available for grabbing
        print("MainWindow created successfully. Waiting to take screenshot...")

        # Use a QTimer to allow the UI to render before taking the screenshot
        # The timeout is in milliseconds. 2000ms = 2 seconds.
        QTimer.singleShot(2000, create_screenshot_and_exit)

        sys.exit(app.exec())

    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)