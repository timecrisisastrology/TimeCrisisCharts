import sys
from datetime import datetime, timezone
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QGridLayout, QLabel, QVBoxLayout
from PyQt6.QtGui import QPalette, QColor
from widgets import InfoPanel, StyledButton, ChartDrawingWidget
from astro_engine import calculate_natal_chart

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

        # --- Create Info Panels ---
        natal_data = {
            "Name": "Jane Doe",
            "Birth Date": "15 May 1989",
            "Birth Time": "08:30 AM",
            "Location": "London, UK",
            "Coords": "51.50° N, 0.12° W"
        }
        birth_info_panel = InfoPanel("Natal Chart Data", natal_data)

        transit_data = {
            "Current Date": "28 Sep 2025",
            "Current Time": "12:22 PM",
            "Location": "Pawtucket, RI",
            "Progression": "Secondary",
            "Mode": "Standard"
        }
        transit_info_panel = InfoPanel("Transit / Progression", transit_data)

        # --- Create Right Toolbar ---
        toolbar_container = QWidget()
        toolbar_layout = QVBoxLayout(toolbar_container)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_layout.setSpacing(10)
        # --- Add Buttons to Toolbar ---
        toolbar_layout.addWidget(StyledButton("Natal"))
        toolbar_layout.addWidget(StyledButton("Transit"))
        toolbar_layout.addWidget(StyledButton("Progression"))
        toolbar_layout.addWidget(StyledButton("Time Map"))
        toolbar_layout.addStretch() # Pushes buttons to the top

        # --- Calculate a Sample Chart ---
        sample_birth_date = datetime(1990, 5, 15, 8, 30, 0, tzinfo=timezone.utc)
        london_lat = 51.5074
        london_lon = -0.1278
        planets, houses = calculate_natal_chart(sample_birth_date, london_lat, london_lon)

        # --- Create Chart Area ---
        chart_area = ChartDrawingWidget()
        chart_area.set_chart_data(houses) # Pass the calculated house data

        # --- Add Widgets to Grid ---
        grid_layout.addWidget(birth_info_panel, 0, 0)
        grid_layout.addWidget(transit_info_panel, 0, 1)
        grid_layout.addWidget(toolbar_container, 0, 2, 2, 1) # Span 2 rows
        grid_layout.addWidget(chart_area, 1, 0, 1, 2) # Span 2 columns
        
        # --- Configure Stretches ---
        grid_layout.setColumnStretch(0, 3) # Birth Info Panel
        grid_layout.setColumnStretch(1, 3) # Transit Info Panel
        grid_layout.setColumnStretch(2, 1) # Toolbar (narrower)
        
        grid_layout.setRowStretch(0, 0) # Let panels define their height
        grid_layout.setRowStretch(1, 1) # Let chart area expand
        
        self.setCentralWidget(main_widget)

# --- Main execution block ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
