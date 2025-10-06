import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

# Ensure the application can find the main modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from main_app import MainWindow, load_fonts

def run_verification():
    """
    Initializes the application, runs it for a few seconds,
    and then closes it, checking for startup errors.
    """
    # Set platform to offscreen for headless execution
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'

    app = QApplication(sys.argv)

    # Load fonts, a critical step from main_app
    load_fonts()

    # Create the main window
    window = MainWindow()

    # Set a timer to automatically close the application after 3 seconds
    # This is enough time for it to initialize fully and for any startup
    # errors to be printed.
    QTimer.singleShot(3000, lambda: app.quit())

    print("Application starting for verification...")
    window.show()
    app.exec()
    print("Verification complete. Application closed.")

if __name__ == "__main__":
    run_verification()