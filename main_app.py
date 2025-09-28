import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QGridLayout, QLabel, QFormLayout
from PyQt6.QtGui import QPalette, QColor, QFont

class InfoPanel(QWidget):
    """A custom, styled panel for displaying astrological data."""
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            InfoPanel {
                background-color: #200334;
                border: 1px solid #3DF6FF;
                border-radius: 5px;
            }
            QLabel {
                color: #94EBFF; /* CHANGED to Neon Blue */
                font-family: "Titillium Web";
                font-size: 10pt;
                background-color: transparent;
            }
        """)
        
        layout = QFormLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        layout.addRow("Name:", QLabel("Jane Doe"))
        layout.addRow("Birth Date:", QLabel("15 May 1989"))
        layout.addRow("Birth Time:", QLabel("08:30 AM"))
        layout.addRow("Location:", QLabel("London, UK"))
        layout.addRow("Coords:", QLabel("51.50° N, 0.12° W"))

class MainWindow(QMainWindow):
    """The main window of the application."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Time Crisis Astrology")
        self.setGeometry(100, 100, 1200, 800)

        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#200334"))
        self.setPalette(palette)
        
        main_widget = QWidget()
        grid_layout = QGridLayout(main_widget)
        
        # --- ADDED: Top margin to push everything down ---
        grid_layout.setContentsMargins(10, 20, 10, 10) # Left, Top, Right, Bottom

        birth_info_panel = InfoPanel()
        transit_info_panel = QWidget()
        chart_area = QWidget()

        grid_layout.addWidget(birth_info_panel, 0, 0)
        grid_layout.addWidget(transit_info_panel, 0, 1)
        grid_layout.addWidget(chart_area, 1, 0, 1, 2)
        
        grid_layout.setColumnStretch(0, 1)
        grid_layout.setColumnStretch(1, 1)
        
        grid_layout.setRowStretch(0, 1)
        grid_layout.setRowStretch(1, 4)
        
        self.setCentralWidget(main_widget)

# --- Main execution block ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
