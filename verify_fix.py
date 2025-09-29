import sys
from PyQt6.QtWidgets import QApplication
from main_app import MainWindow

# This script is to verify that the main window can be created without a runtime error.
# It will not show a window, but it will exit with a non-zero code if an exception occurs.
if __name__ == "__main__":
    app = QApplication(sys.argv)
    try:
        window = MainWindow()
        print("MainWindow created successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)
    sys.exit(0)