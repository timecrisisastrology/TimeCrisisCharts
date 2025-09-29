import sys
import math
from PyQt6.QtWidgets import QWidget, QLabel, QFormLayout, QVBoxLayout, QFrame, QPushButton, QLineEdit
from PyQt6.QtGui import QFont, QPainter, QPen, QColor, QBrush, QFontMetrics
from PyQt6.QtCore import Qt, QPointF

class InfoPanel(QWidget):
    """A custom, styled panel for displaying astrological data. Can accept QWidgets."""
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
            QLabel, QLineEdit {
                color: #94EBFF;
                font-family: "Titillium Web";
                font-size: 10pt;
                background-color: transparent;
            }
            QLineEdit {
                border: 1px solid #75439E;
                border-radius: 3px;
                padding: 2px;
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
            # If the value is already a widget, add it directly. Otherwise, create a QLabel.
            if isinstance(value, QWidget):
                widget = value
            else:
                widget = QLabel(str(value))
            form_layout.addRow(f"{label}:", widget)

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

        # Chart data - will be populated by set_chart_data
        self.zodiac_signs = ["♈", "♉", "♊", "♋", "♌", "♍", "♎", "♏", "♐", "♑", "♒", "♓"]
        self.house_cusps = []
        self.display_houses = [] # Houses to draw (can be natal or return)
        self.planets = {} # Inner wheel planets
        self.outer_planets = None # Outer wheel planets
        self.aspects = []

        # --- Planet & Color Definitions ---
        self.planet_glyphs = {
            'Sun': '☉', 'Moon': '☽', 'Mercury': '☿', 'Venus': '♀', 'Mars': '♂',
            'Jupiter': '♃', 'Saturn': '♄', 'Uranus': '♅', 'Neptune': '♆', 'Pluto': '♇'
        }
        self.planet_colors = {
            # Fire (Neon Pink)
            'Sun': QColor("#FF01F9"), 'Mars': QColor("#FF01F9"), 'Jupiter': QColor("#FF01F9"),
            # Water (Neon Blue)
            'Moon': QColor("#3DF6FF"), 'Pluto': QColor("#3DF6FF"), 'Neptune': QColor("#3DF6FF"),
            # Air (Neon Yellow)
            'Mercury': QColor("#FFFF00"), 'Uranus': QColor("#FFFF00"),
            # Earth (Neon Green)
            'Venus': QColor("#39FF14"), 'Saturn': QColor("#39FF14"),
        }

    def set_chart_data(self, natal_planets, natal_houses, aspects, outer_planets=None, display_houses=None):
        """Receives calculated chart data for single or bi-wheel charts and triggers a repaint."""
        self.planets = natal_planets
        self.house_cusps = natal_houses # Always store natal houses for reference
        self.aspects = aspects
        self.outer_planets = outer_planets

        # Use specific houses for display if provided (for returns), else default to natal houses.
        self.display_houses = display_houses if display_houses is not None else natal_houses
        self.update()

    def paintEvent(self, event):
        """This method is called whenever the widget needs to be redrawn."""
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Define colors and dimensions
        neon_pink = QColor("#FF01F9")
        neon_blue = QColor("#3DF6FF")
        center = QPointF(self.width() / 2, self.height() / 2)
        radius = min(self.width(), self.height()) / 2 * 0.9 # Use 90% of available space
        inner_radius = radius * 0.25 # Radius of the new central circle

        # 1. Draw the concentric chart rings
        pen = QPen(neon_pink, 3, Qt.PenStyle.SolidLine) # Thicker main ring
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(center, radius, radius) # Outer ring
        painter.drawEllipse(center, radius * 0.85, radius * 0.85) # Inner ring of the zodiac band
        painter.drawEllipse(center, inner_radius, inner_radius) # Inner-most circle for aspects

        # 2. Draw the zodiac sign glyphs with glow
        glyph_font = QFont("Titillium Web", 24) # Increased glyph size
        glyph_font.setBold(True)
        painter.setFont(glyph_font)

        for i, sign in enumerate(self.zodiac_signs):
            angle_deg = (i * 30) - 15
            angle_rad = math.radians(angle_deg)
            glyph_radius = radius * 0.9
            x = center.x() + glyph_radius * math.cos(angle_rad)
            y = center.y() + glyph_radius * math.sin(angle_rad)
            font_metrics = painter.fontMetrics()
            text_width = font_metrics.horizontalAdvance(sign)
            text_height = font_metrics.height()
            point = QPointF(x - text_width / 2, y + text_height / 4)

            # --- Draw with glow ---
            self._draw_glow_text(painter, point, sign, glyph_font, neon_blue)

        # 2a. Draw the zodiac dividers
        painter.setPen(QPen(neon_blue, 1, Qt.PenStyle.SolidLine))
        for i in range(12):
            angle_deg = i * 30
            angle_rad = math.radians(angle_deg)
            x_start = center.x() + radius * 0.85 * math.cos(angle_rad)
            y_start = center.y() + radius * 0.85 * math.sin(angle_rad)
            x_end = center.x() + radius * math.cos(angle_rad)
            y_end = center.y() + radius * math.sin(angle_rad)
            painter.drawLine(QPointF(x_start, y_start), QPointF(x_end, y_end))

        # 3. Draw the house cusp lines (using display_houses)
        self._draw_cusp_labels(painter, center, radius, neon_blue) # Draw cusp labels
        painter.setPen(QPen(neon_pink, 1, Qt.PenStyle.SolidLine))
        for cusp_deg in self.display_houses:
            angle_rad = math.radians(cusp_deg)
            x_start = center.x() + inner_radius * math.cos(angle_rad)
            y_start = center.y() + inner_radius * math.sin(angle_rad)
            x_end = center.x() + radius * math.cos(angle_rad)
            y_end = center.y() + radius * math.sin(angle_rad)
            painter.drawLine(QPointF(x_start, y_start), QPointF(x_end, y_end))

        # --- NEW: Define radii for planet wheels ---
        inner_planet_radius = radius * 0.45
        outer_planet_radius = radius * 0.70

        # --- NEW: Add a separation circle for bi-wheel ---
        if self.outer_planets:
            separation_radius = (inner_planet_radius + outer_planet_radius) / 2
            painter.setPen(QPen(neon_blue, 1, Qt.PenStyle.DotLine))
            painter.drawEllipse(center, separation_radius, separation_radius)

        # 4. Draw the house numbers
        self._draw_house_numbers(painter, center, inner_radius * 1.2, neon_blue)

        # 5. Draw the planet glyphs (refactored)
        self._draw_planets(painter, center, inner_planet_radius, self.planets)
        if self.outer_planets:
            self._draw_planets(painter, center, outer_planet_radius, self.outer_planets)

        # 6. Draw the aspect lines (now contained within the inner circle)
        aspect_radius = inner_radius * 0.85
        aspect_colors = {
            'Trine': QColor(61, 246, 255, 150), # Neon Blue, semi-transparent
            'Sextile': QColor(61, 246, 255, 150),
            'Square': QColor(255, 1, 249, 150), # Neon Pink, semi-transparent
            'Opposition': QColor(255, 1, 249, 150),
            'Conjunction': QColor(200, 200, 200, 150) # Light Gray, semi-transparent
        }

        for aspect_info in self.aspects:
            p1_name = aspect_info['p1']
            aspect_name = aspect_info['aspect']
            p2_name = aspect_info['p2']

            if p1_name in self.planets and p2_name in self.planets:
                # FIX: Access the longitude (first element) from the position tuple
                p1_pos = self.planets[p1_name][0]
                p2_pos = self.planets[p2_name][0]

                color = aspect_colors.get(aspect_name)
                if color:
                    pen = QPen(color, 1.5, Qt.PenStyle.SolidLine)
                    painter.setPen(pen)

                    p1_rad = math.radians(p1_pos)
                    p1_x = center.x() + aspect_radius * math.cos(p1_rad)
                    p1_y = center.y() + aspect_radius * math.sin(p1_rad)

                    p2_rad = math.radians(p2_pos)
                    p2_x = center.x() + aspect_radius * math.cos(p2_rad)
                    p2_y = center.y() + aspect_radius * math.sin(p2_rad)

                    painter.drawLine(QPointF(p1_x, p1_y), QPointF(p2_x, p2_y))

    def _draw_planets(self, painter, center, radius, planets):
        """Helper method to draw a wheel of planets."""
        planet_font = QFont("Titillium Web", 20) # Increased planet size
        planet_font.setBold(True)

        for name, position in planets.items():
            # FIX: Access the longitude (first element) from the position tuple
            angle_rad = math.radians(position[0])
            x = center.x() + radius * math.cos(angle_rad)
            y = center.y() + radius * math.sin(angle_rad)

            glyph = self.planet_glyphs.get(name, '?')
            font_metrics = QFontMetrics(planet_font)
            text_width = font_metrics.horizontalAdvance(glyph)
            text_height = font_metrics.height()
            point = QPointF(x - text_width / 2, y + text_height / 4)

            planet_color = self.planet_colors.get(name, QColor("white"))
            self._draw_glow_text(painter, point, glyph, planet_font, planet_color)

    def _draw_cusp_labels(self, painter, center, radius, color):
        """Helper method to draw the degree labels for each house cusp, rotated along the wheel."""
        if not self.display_houses:
            return

        label_font = QFont("Titillium Web", 12) # Increased cusp label size
        label_font.setBold(True)

        def format_degree(deg):
            deg = deg % 360
            sign_index = int(deg / 30)
            deg_in_sign = deg % 30
            minutes = (deg_in_sign - int(deg_in_sign)) * 60
            return f"{int(deg_in_sign)}° {self.zodiac_signs[sign_index]} {int(minutes)}'"

        for i, cusp_deg in enumerate(self.display_houses):
            text = format_degree(cusp_deg)
            if i == 0:  # Special formatting for Ascendant
                text = f"ASC = {text}"

            rotation_angle = cusp_deg - 90
            label_radius = radius * 1.07
            angle_rad = math.radians(cusp_deg)
            x = center.x() + label_radius * math.cos(angle_rad)
            y = center.y() + label_radius * math.sin(angle_rad)

            painter.save()
            painter.translate(x, y)

            if 90 < cusp_deg < 270:
                painter.rotate(rotation_angle + 180)
            else:
                painter.rotate(rotation_angle)

            font_metrics = QFontMetrics(label_font)
            text_width = font_metrics.horizontalAdvance(text)
            text_height = font_metrics.height()

            draw_point = QPointF(-text_width / 2, text_height / 4)
            self._draw_glow_text(painter, draw_point, text, label_font, color)
            painter.restore()

    def _draw_house_numbers(self, painter, center, radius, color):
        """Helper method to draw the house numbers in the center of each house."""
        if not self.display_houses:
            return

        house_font = QFont("Titillium Web", 12)
        house_font.setBold(True)

        for i in range(12):
            house_num = i + 1
            start_angle = self.display_houses[i]
            end_angle = self.display_houses[(i + 1) % 12]

            # Handle the wrap-around from 360 to 0 degrees for calculation
            if end_angle < start_angle:
                end_angle += 360

            mid_angle_deg = (start_angle + end_angle) / 2
            angle_rad = math.radians(mid_angle_deg)

            x = center.x() + radius * math.cos(angle_rad)
            y = center.y() + radius * math.sin(angle_rad)

            text = str(house_num)
            font_metrics = QFontMetrics(house_font)
            text_width = font_metrics.horizontalAdvance(text)
            text_height = font_metrics.height()
            point = QPointF(x - text_width / 2, y + text_height / 4)

            self._draw_glow_text(painter, point, text, house_font, color)

    def _draw_glow_text(self, painter, point, text, font, color):
        """A helper function to draw text with a very intense neon glow effect."""
        painter.setFont(font)

        # 1. Draw the wide, soft outer glow (simulating bloom)
        glow_color = QColor(color)
        glow_color.setAlpha(80) # Increased alpha for a stronger bloom
        pen = QPen(glow_color, 15, Qt.PenStyle.SolidLine) # Wider pen for more glow
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawText(point, text)

        # 2. Draw the brighter, tighter inner glow
        glow_color.setAlpha(180) # Much brighter inner glow
        pen.setColor(glow_color)
        pen.setWidth(7) # Tighter than the outer glow, but still substantial
        painter.setPen(pen)
        painter.drawText(point, text)

        # 3. Draw the core text in a very light shade to make it pop
        core_color = color.lighter(170)
        pen.setColor(core_color)
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawText(point, text)