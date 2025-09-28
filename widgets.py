import sys
import math
from PyQt6.QtWidgets import QWidget, QLabel, QFormLayout, QVBoxLayout, QFrame, QPushButton
from PyQt6.QtGui import QFont, QPainter, QPen, QColor, QBrush
from PyQt6.QtCore import Qt, QPointF

class InfoPanel(QWidget):
    """A custom, styled panel for displaying astrological data."""
    def __init__(self, title, data):
        super().__init__()
        # The InfoPanel itself is transparent; the QFrame inside provides the styled background and border.
        self.setStyleSheet("""
            QLabel#panel-title {
                color: #FF01F9;
                font-family: "TT Supermolot Neue Condensed";
                font-size: 14pt;
                font-weight: bold;
                padding-bottom: 5px;
            }
            QFrame#container {
                background-color: #200334;
                border: 1px solid #3DF6FF;
                border-radius: 5px;
            }
            QLabel {
                color: #94EBFF;
                font-family: "Titillium Web";
                font-size: 10pt;
                background-color: transparent;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        title_label = QLabel(title)
        title_label.setObjectName("panel-title")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        container = QFrame()
        container.setObjectName("container")
        form_layout = QFormLayout(container)
        form_layout.setContentsMargins(15, 15, 15, 15)

        for label, value in data.items():
            form_layout.addRow(f"{label}:", QLabel(value))

        main_layout.addWidget(container)

class StyledButton(QPushButton):
    """A custom, styled button for the toolbar."""
    def __init__(self, text):
        super().__init__(text)
        self.setStyleSheet("""
            QPushButton {
                background-color: #200334;
                color: #3DF6FF;
                border: 1px solid #3DF6FF;
                border-radius: 5px;
                padding: 10px;
                font-family: "TT Supermolot Neue Condensed";
                font-size: 12pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3DF6FF;
                color: #200334;
            }
            QPushButton:pressed {
                background-color: #94EBFF;
                color: #200334;
            }
        """)

class ChartDrawingWidget(QFrame):
    """A custom widget for drawing the astrological chart."""
    def __init__(self):
        super().__init__()
        self.setMinimumSize(400, 400) # Ensure the widget has a decent size
        self.setStyleSheet("background-color: transparent; border: none;")

        # Placeholder data - will be replaced by live data later
        self.zodiac_signs = ["♈", "♉", "♊", "♋", "♌", "♍", "♎", "♏", "♐", "♑", "♒", "♓"]
        self.house_cusps = [] # Start with empty cusps

    def set_chart_data(self, houses):
        """Receives the calculated chart data and triggers a repaint."""
        self.house_cusps = houses
        self.update() # This is crucial - it tells Qt to redraw the widget

    def paintEvent(self, event):
        """This method is called whenever the widget needs to be redrawn."""
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Define colors and dimensions
        neon_pink = QColor("#FF01F9")
        neon_blue = QColor("#3DF6FF")
        center = QPointF(self.width() / 2, self.height() / 2)
        radius = min(self.width(), self.height()) / 2 * 0.8  # Use 80% of available space

        # 1. Draw the main zodiac circle
        pen = QPen(neon_pink, 2, Qt.PenStyle.SolidLine)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(center, radius, radius)

        # 2. Draw the zodiac sign glyphs
        glyph_font = QFont("Titillium Web", 14)
        glyph_font.setBold(True)
        painter.setFont(glyph_font)
        painter.setPen(neon_blue)

        for i, sign in enumerate(self.zodiac_signs):
            # Calculate angle for each sign (Aries starts at 0 degrees, left side)
            # We subtract 15 degrees to center the glyph in its 30-degree slice
            angle_deg = (i * 30) - 15
            angle_rad = math.radians(angle_deg)

            # Position glyphs slightly inside the main circle for aesthetics
            glyph_radius = radius * 0.9
            x = center.x() + glyph_radius * math.cos(angle_rad)
            y = center.y() + glyph_radius * math.sin(angle_rad)

            # Adjust position to center the glyph character
            font_metrics = painter.fontMetrics()
            text_width = font_metrics.horizontalAdvance(sign)
            text_height = font_metrics.height()
            x -= text_width / 2
            y += text_height / 4

            painter.drawText(QPointF(x, y), sign)

        # 3. Draw the house cusp lines
        painter.setPen(pen) # Use the same neon pink pen as the circle
        for cusp_deg in self.house_cusps:
            angle_rad = math.radians(cusp_deg)

            # Calculate the point on the outer circle for the line end
            x_end = center.x() + radius * math.cos(angle_rad)
            y_end = center.y() + radius * math.sin(angle_rad)

            painter.drawLine(center, QPointF(x_end, y_end))