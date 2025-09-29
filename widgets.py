import sys
import math
from PyQt6.QtWidgets import QWidget, QLabel, QFormLayout, QVBoxLayout, QFrame, QPushButton, QLineEdit
from PyQt6.QtGui import QFont, QPainter, QPen, QColor, QBrush, QFontMetrics, QPainterPath, QTransform
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
        self.house_cusps = []
        self.display_houses = [] # Houses to draw (can be natal or return)
        self.planets = {} # Inner wheel planets
        self.outer_planets = None # Outer wheel planets
        self.aspects = []
        self.zodiac_symbols = ["♈", "♉", "♊", "♋", "♌", "♍", "♎", "♏", "♐", "♑", "♒", "♓"]
        self._define_zodiac_paths()

        # --- Planet & Color Definitions ---
        self.planet_glyphs = {
            'Sun': '☉', 'Moon': '☽', 'Mercury': '☿', 'Venus': '♀', 'Mars': '♂',
            'Jupiter': '♃', 'Saturn': '♄', 'Uranus': '♅', 'Neptune': '♆', 'Pluto': '♇'
        }
        self.planet_colors = {
            'Sun': QColor("#FF01F9"), 'Mars': QColor("#FF01F9"), 'Jupiter': QColor("#FF01F9"),
            'Moon': QColor("#3DF6FF"), 'Pluto': QColor("#3DF6FF"), 'Neptune': QColor("#3DF6FF"),
            'Mercury': QColor("#FFFF00"), 'Uranus': QColor("#FFFF00"),
            'Venus': QColor("#39FF14"), 'Saturn': QColor("#39FF14"),
        }

    def set_chart_data(self, natal_planets, natal_houses, aspects, outer_planets=None, display_houses=None):
        self.planets = natal_planets
        self.house_cusps = natal_houses
        self.aspects = aspects
        self.outer_planets = outer_planets
        self.display_houses = display_houses if display_houses is not None else natal_houses
        self.update()

    def _define_zodiac_paths(self):
        self.zodiac_paths = {
            "Aries": QPainterPath(), "Taurus": QPainterPath(), "Gemini": QPainterPath(),
            "Cancer": QPainterPath(), "Leo": QPainterPath(), "Virgo": QPainterPath(),
            "Libra": QPainterPath(), "Scorpio": QPainterPath(), "Sagittarius": QPainterPath(),
            "Capricorn": QPainterPath(), "Aquarius": QPainterPath(), "Pisces": QPainterPath()
        }
        # Paths are defined on a 100x100 canvas for uniform scaling.
        p = self.zodiac_paths["Aries"]; p.moveTo(50, 80); p.lineTo(50, 20); p.moveTo(30, 40); p.arcTo(20,-5, 20, 50, 180, -180); p.moveTo(70, 40); p.arcTo(60,-5, 20, 50, 0, 180)
        p = self.zodiac_paths["Taurus"]; p.addEllipse(30, 40, 40, 40); p.moveTo(25, 40); p.arcTo(15, 15, 30, 30, 160, 100); p.moveTo(75, 40); p.arcTo(55, 15, 30, 30, 20, -100)
        p = self.zodiac_paths["Gemini"]; p.moveTo(30, 20); p.arcTo(20, 10, 20, 20, 180, 180); p.lineTo(30, 80); p.arcTo(20, 70, 20, 20, 180, -180); p.moveTo(70, 20); p.arcTo(60, 10, 20, 20, 0, -180); p.lineTo(70, 80); p.arcTo(60, 70, 20, 20, 0, 180)
        p = self.zodiac_paths["Cancer"]; p.moveTo(35, 60); p.arcTo(25, 25, 30, 30, 180, 270); p.addEllipse(15, 50, 15, 15); p.moveTo(65, 40); p.arcTo(45, 45, 30, 30, 0, -270); p.addEllipse(70, 30, 15, 15)
        p = self.zodiac_paths["Leo"]; p.addEllipse(30, 20, 40, 40); p.moveTo(70, 50); p.lineTo(70, 80); p.arcTo(60, 70, 20, 20, 270, -270)
        p = self.zodiac_paths["Virgo"]; p.moveTo(20, 80); p.lineTo(20, 20); p.moveTo(20, 50); p.lineTo(40, 20); p.lineTo(40, 80); p.moveTo(40, 50); p.lineTo(60, 20); p.lineTo(60, 70); p.arcTo(50, 60, 30, 30, 0, 300); p.lineTo(75, 85)
        p = self.zodiac_paths["Libra"]; p.moveTo(20, 80); p.lineTo(80, 80); p.moveTo(20, 65); p.lineTo(80, 65); p.moveTo(35, 65); p.arcTo(35, 45, 30, 20, 180, -180)
        p = self.zodiac_paths["Scorpio"]; p.moveTo(20, 80); p.lineTo(20, 20); p.moveTo(20, 50); p.lineTo(40, 20); p.lineTo(40, 80); p.moveTo(40, 50); p.lineTo(60, 20); p.lineTo(60, 80); p.moveTo(80, 80); p.lineTo(65, 65); p.lineTo(85, 65)
        p = self.zodiac_paths["Sagittarius"]; p.moveTo(20, 80); p.lineTo(80, 20); p.moveTo(60, 20); p.lineTo(80, 20); p.lineTo(80, 40); p.moveTo(30, 70); p.lineTo(50, 50)
        p = self.zodiac_paths["Capricorn"]; p.moveTo(20, 20); p.lineTo(20, 50); p.lineTo(40, 80); p.lineTo(60, 50); p.moveTo(40, 80); p.arcTo(30, 30, 50, 60, 0, -200); p.arcTo(40, 50, 20, 30, 270, 200)
        p = self.zodiac_paths["Aquarius"]; p.moveTo(20, 30); p.lineTo(35, 45); p.lineTo(50, 30); p.lineTo(65, 45); p.lineTo(80, 30); p.moveTo(20, 60); p.lineTo(35, 75); p.lineTo(50, 60); p.lineTo(65, 75); p.lineTo(80, 60)
        p = self.zodiac_paths["Pisces"]; p.moveTo(20, 20); p.arcTo(-30, 20, 100, 60, 90, 180); p.moveTo(80, 20); p.arcTo(30, 20, 100, 60, 90, -180); p.moveTo(20, 50); p.lineTo(80, 50)
        self.zodiac_names = list(self.zodiac_paths.keys())

    def _draw_zodiac_glyphs(self, painter, center, radius, color, angle_offset):
        glyph_size = radius * 0.15
        base_radius = radius * 0.92 - (glyph_size / 2)

        for i, name in enumerate(self.zodiac_names):
            path = self.zodiac_paths[name]
            angle_deg = (i * 30) + 15 + angle_offset
            angle_rad = math.radians(-angle_deg) # Negative for clockwise SVG-style rotation

            # Calculate center of the glyph
            x = center.x() + base_radius * math.cos(math.radians(angle_deg))
            y = center.y() + base_radius * math.sin(math.radians(angle_deg))

            # Transformation: scale, then translate
            transform = QTransform()
            transform.translate(x - (glyph_size/2), y - (glyph_size/2))
            transform.scale(glyph_size / 100.0, glyph_size / 100.0)

            transformed_path = transform.map(path)
            self._draw_glow_path(painter, transformed_path, color, 1.5)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        neon_pink = QColor("#FF01F9")
        neon_blue = QColor("#3DF6FF")
        center = QPointF(self.width() / 2, self.height() / 2)
        radius = min(self.width(), self.height()) / 2 * 0.9

        # --- Rotation Offset ---
        # The first house cusp (Ascendant) should be at 180 degrees (left side).
        angle_offset = 0
        if self.display_houses:
            angle_offset = 180 - self.display_houses[0]

        radii = {
            "zodiac_outer": radius, "zodiac_inner": radius * 0.85, "outer_wheel": radius * 0.65,
            "inner_wheel": radius * 0.45, "aspect_circle": radius * 0.25, "outer_planets": radius * 0.75,
            "inner_planets_bi": radius * 0.55, "inner_planets_single": radius * 0.60,
            "house_numbers": radius * 0.35, "aspect_lines": radius * 0.25 * 0.85
        }

        # 1. Draw concentric circles
        path = QPainterPath(); path.addEllipse(center, radii["zodiac_outer"], radii["zodiac_outer"]); self._draw_glow_path(painter, path, neon_pink, 2)
        path = QPainterPath(); path.addEllipse(center, radii["zodiac_inner"], radii["zodiac_inner"]); self._draw_glow_path(painter, path, neon_pink, 2)
        path = QPainterPath(); path.addEllipse(center, radii["inner_wheel"], radii["inner_wheel"]); self._draw_glow_path(painter, path, neon_pink, 2)
        path = QPainterPath(); path.addEllipse(center, radii["aspect_circle"], radii["aspect_circle"]); self._draw_glow_path(painter, path, neon_pink, 2)
        if self.outer_planets:
            path = QPainterPath(); path.addEllipse(center, radii["outer_wheel"], radii["outer_wheel"]); self._draw_glow_path(painter, path, neon_pink, 2)

        # 2. Draw zodiac glyphs and dividers
        self._draw_zodiac_glyphs(painter, center, radius, neon_blue, angle_offset)
        for i in range(12):
            angle_rad = math.radians(i * 30 + angle_offset)
            x_start = center.x() + radii["zodiac_inner"] * math.cos(angle_rad)
            y_start = center.y() + radii["zodiac_inner"] * math.sin(angle_rad)
            x_end = center.x() + radii["zodiac_outer"] * math.cos(angle_rad)
            y_end = center.y() + radii["zodiac_outer"] * math.sin(angle_rad)
            divider_path = QPainterPath(); divider_path.moveTo(x_start, y_start); divider_path.lineTo(x_end, y_end)
            self._draw_glow_path(painter, divider_path, neon_blue, 1)

        # 3. Draw house cusp lines and labels
        self._draw_cusp_labels(painter, center, radius, neon_blue, angle_offset)
        for cusp_deg in self.display_houses:
            angle_rad = math.radians(cusp_deg + angle_offset)
            x_start = center.x() + radii["aspect_circle"] * math.cos(angle_rad)
            y_start = center.y() + radii["aspect_circle"] * math.sin(angle_rad)
            x_end = center.x() + radii["zodiac_outer"] * math.cos(angle_rad)
            y_end = center.y() + radii["zodiac_outer"] * math.sin(angle_rad)
            cusp_path = QPainterPath(); cusp_path.moveTo(x_start, y_start); cusp_path.lineTo(x_end, y_end)
            self._draw_glow_path(painter, cusp_path, neon_pink, 1)

        # 4. Draw house numbers
        self._draw_house_numbers(painter, center, radii["house_numbers"], neon_blue, angle_offset)

        # 5. Draw planet glyphs
        if self.outer_planets:
            self._draw_planets(painter, center, radii["inner_planets_bi"], self.planets, angle_offset)
            self._draw_planets(painter, center, radii["outer_planets"], self.outer_planets, angle_offset)
        else:
            self._draw_planets(painter, center, radii["inner_planets_single"], self.planets, angle_offset)

        # 6. Draw aspect lines
        aspect_radius = radii["aspect_lines"]
        aspect_colors = {
            'Trine': QColor(61, 246, 255, 150), 'Sextile': QColor(61, 246, 255, 150),
            'Square': QColor(255, 1, 249, 150), 'Opposition': QColor(255, 1, 249, 150),
            'Conjunction': QColor(200, 200, 200, 150)
        }
        for aspect_info in self.aspects:
            p1_name, aspect_name, p2_name = aspect_info['p1'], aspect_info['aspect'], aspect_info['p2']
            if p1_name in self.planets and p2_name in self.planets:
                p1_pos, p2_pos = self.planets[p1_name][0], self.planets[p2_name][0]
                color = aspect_colors.get(aspect_name)
                if color:
                    pen = QPen(color, 1.5, Qt.PenStyle.SolidLine)
                    painter.setPen(pen)
                    p1_rad = math.radians(p1_pos + angle_offset)
                    p1_x = center.x() + aspect_radius * math.cos(p1_rad)
                    p1_y = center.y() + aspect_radius * math.sin(p1_rad)
                    p2_rad = math.radians(p2_pos + angle_offset)
                    p2_x = center.x() + aspect_radius * math.cos(p2_rad)
                    p2_y = center.y() + aspect_radius * math.sin(p2_rad)
                    painter.drawLine(QPointF(p1_x, p1_y), QPointF(p2_x, p2_y))

    def _draw_planets(self, painter, center, radius, planets, angle_offset):
        """Helper method to draw a wheel of planets."""
        planet_font = QFont("Titillium Web", 20); planet_font.setBold(True)
        for name, position in planets.items():
            angle_rad = math.radians(position[0] + angle_offset)
            x = center.x() + radius * math.cos(angle_rad)
            y = center.y() + radius * math.sin(angle_rad)
            glyph = self.planet_glyphs.get(name, '?')
            font_metrics = QFontMetrics(planet_font)
            text_width = font_metrics.horizontalAdvance(glyph)
            text_height = font_metrics.height()
            point = QPointF(x - text_width / 2, y + text_height / 4)
            planet_color = self.planet_colors.get(name, QColor("white"))
            self._draw_glow_text(painter, point, glyph, planet_font, planet_color)

    def _draw_cusp_labels(self, painter, center, radius, color, angle_offset):
        """Helper method to draw the degree labels for each house cusp, rotated along the wheel."""
        if not self.display_houses: return
        label_font = QFont("Titillium Web", 12); label_font.setBold(True)
        def format_degree(deg):
            deg %= 360
            sign_index = int(deg / 30)
            deg_in_sign = deg % 30
            minutes = (deg_in_sign - int(deg_in_sign)) * 60
            return f"{int(deg_in_sign)}° {self.zodiac_symbols[sign_index]} {int(minutes)}'"

        for i, cusp_deg in enumerate(self.display_houses):
            text = format_degree(cusp_deg)
            if i == 0: text = f"ASC = {text}"

            angle_with_offset = cusp_deg + angle_offset
            rotation_angle = angle_with_offset - 90
            label_radius = radius * 1.07
            angle_rad = math.radians(angle_with_offset)
            x = center.x() + label_radius * math.cos(angle_rad)
            y = center.y() + label_radius * math.sin(angle_rad)

            painter.save()
            painter.translate(x, y)
            painter.rotate(rotation_angle + 180 if 90 < angle_with_offset % 360 < 270 else rotation_angle)

            font_metrics = QFontMetrics(label_font)
            text_width = font_metrics.horizontalAdvance(text)
            draw_point = QPointF(-text_width / 2, font_metrics.height() / 4)
            self._draw_glow_text(painter, draw_point, text, label_font, color)
            painter.restore()

    def _draw_house_numbers(self, painter, center, radius, color, angle_offset):
        """Helper method to draw the house numbers in the center of each house."""
        if not self.display_houses: return
        house_font = QFont("Titillium Web", 12); house_font.setBold(True)
        for i in range(12):
            start_angle = self.display_houses[i]
            end_angle = self.display_houses[(i + 1) % 12]
            if end_angle < start_angle: end_angle += 360

            mid_angle_deg = (start_angle + end_angle) / 2 + angle_offset
            angle_rad = math.radians(mid_angle_deg)

            x = center.x() + radius * math.cos(angle_rad)
            y = center.y() + radius * math.sin(angle_rad)

            text = str(i + 1)
            font_metrics = QFontMetrics(house_font)
            text_width = font_metrics.horizontalAdvance(text)
            text_height = font_metrics.height()
            point = QPointF(x - text_width / 2, y + text_height / 4)

            self._draw_glow_text(painter, point, text, house_font, color)

    def _draw_glow_path(self, painter, path, color, width):
        """Draws a QPainterPath with a multi-layered neon glow effect."""
        # 1. Wide, soft outer glow
        glow_color_1 = QColor(color)
        glow_color_1.setAlpha(40) # More subtle
        pen1 = QPen(glow_color_1, width * 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen1)
        painter.drawPath(path)

        # 2. Medium inner glow
        glow_color_2 = QColor(color)
        glow_color_2.setAlpha(80)
        pen2 = QPen(glow_color_2, width * 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen2)
        painter.drawPath(path)

        # 3. Core line
        core_color = color.lighter(150)
        pen3 = QPen(core_color, width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen3)
        painter.drawPath(path)

    def _draw_glow_text(self, painter, point, text, font, color):
        """A helper function to draw text with a more realistic, multi-layered neon glow."""
        painter.setFont(font)

        # 1. Draw the wide, soft outer glow (simulating bloom)
        glow_color1 = QColor(color)
        glow_color1.setAlpha(50) # Softer glow
        pen1 = QPen(glow_color1, 12, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen1)
        painter.drawText(point, text)

        # 2. Draw a tighter, brighter inner glow
        glow_color2 = QColor(color)
        glow_color2.setAlpha(100) # Brighter than outer glow
        pen2 = QPen(glow_color2, 6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen2)
        painter.drawText(point, text)

        # 3. Draw the core text in a very light shade to make it pop
        core_color = color.lighter(180) # Make it almost white
        pen3 = QPen(core_color, 1, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen3)
        painter.drawText(point, text)