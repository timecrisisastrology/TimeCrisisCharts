import sys
import math
from PyQt6.QtWidgets import QWidget, QLabel, QFormLayout, QVBoxLayout, QFrame, QPushButton, QLineEdit
from PyQt6.QtGui import QFont, QPainter, QPen, QColor, QBrush, QFontMetrics, QPainterPath, QTransform
from PyQt6.QtCore import Qt, QPointF, QRectF

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
    def __init__(self, astro_font_name):
        super().__init__()
        self.setMinimumSize(400, 400) # Ensure the widget has a decent size
        self.setStyleSheet("background-color: transparent; border: none;")
        self.astro_font_name = astro_font_name # Store the font name

        # Chart data - will be populated by set_chart_data
        self.house_cusps = []
        self.display_houses = [] # Houses to draw (can be natal or return)
        self.planets = {} # Inner wheel planets
        self.outer_planets = None # Outer wheel planets
        self.aspects = []
        self._setup_glyph_data()

    def set_chart_data(self, natal_planets, natal_houses, aspects, outer_planets=None, display_houses=None):
        self.planets = natal_planets
        self.house_cusps = natal_houses
        self.aspects = aspects
        self.outer_planets = outer_planets
        self.display_houses = display_houses if display_houses is not None else natal_houses
        self.update()

    def _setup_glyph_data(self):
        """Initializes all glyph and color data for rendering, ensuring correct color scheme."""
        # --- Zodiac Sign Glyphs (using Unicode) ---
        self.zodiac_glyphs = {
            'Aries': '♈', 'Taurus': '♉', 'Gemini': '♊', 'Cancer': '♋',
            'Leo': '♌', 'Virgo': '♍', 'Libra': '♎', 'Scorpio': '♏',
            'Sagittarius': '♐', 'Capricorn': '♑', 'Aquarius': '♒', 'Pisces': '♓'
        }
        self.zodiac_names = list(self.zodiac_glyphs.keys())

        # --- Planet Glyphs (using Unicode) ---
        self.planet_glyphs = {
            'Sun': '☉', 'Moon': '☽', 'Mercury': '☿', 'Venus': '♀', 'Mars': '♂',
            'Jupiter': '♃', 'Saturn': '♄', 'Uranus': '♅', 'Neptune': '♆', 'Pluto': '♇'
        }

        # --- Neon Color Definitions ---
        neon_pink = QColor("#FF01F9")   # Fire
        neon_blue = QColor("#3DF6FF")   # Water
        neon_yellow = QColor("#FFFF00") # Air
        neon_green = QColor("#39FF14")  # Earth

        # CRITICAL: This mapping implements the user's requested color scheme.
        self.planet_colors = {
            'Sun': neon_pink, 'Mars': neon_pink, 'Jupiter': neon_pink,     # Fire
            'Moon': neon_blue, 'Neptune': neon_blue, 'Pluto': neon_blue,   # Water
            'Mercury': neon_yellow, 'Uranus': neon_yellow,                 # Air
            'Venus': neon_green, 'Saturn': neon_green,                     # Earth
        }

    def _draw_zodiac_glyphs(self, painter, center, radius, color, angle_offset):
        # Use the astro_font_name passed during initialization.
        font = QFont(self.astro_font_name, 35)
        # CRITICAL: Prevent the OS from substituting the glyphs with emoji or other fonts.
        font.setStyleStrategy(QFont.StyleStrategy.NoFontMerging)
        base_radius = radius * 0.925

        for i, name in enumerate(self.zodiac_names):
            glyph = self.zodiac_glyphs[name]
            angle_deg = (i * 30) + 15 + angle_offset
            angle_rad = math.radians(angle_deg)

            x = center.x() + base_radius * math.cos(angle_rad)
            y = center.y() + base_radius * math.sin(angle_rad)

            font_metrics = QFontMetrics(font)
            text_width = font_metrics.horizontalAdvance(glyph)
            text_height = font_metrics.height()

            painter.save()
            # Move to the glyph's position on the circle
            painter.translate(x, y)
            # Since the canvas is flipped, we flip the text back to be upright
            painter.scale(1, -1)
            # Center the glyph on its calculated position
            draw_point = QPointF(-text_width / 2, text_height / 4)
            self._draw_glow_text(painter, draw_point, glyph, font, color)
            painter.restore()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Apply a single transformation to flip the Y-axis.
        # This makes all subsequent drawing operations use a standard mathematical
        # coordinate system where Y increases upwards.
        painter.translate(0, self.height())
        painter.scale(1, -1)

        neon_pink = QColor("#FF01F9")
        neon_blue = QColor("#3DF6FF")
        # The center now needs to be calculated in the new, flipped coordinate system.
        center = QPointF(self.width() / 2, self.height() / 2)
        radius = min(self.width(), self.height()) / 2 * 0.9

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
        # Use the astro_font_name passed during initialization.
        planet_font = QFont(self.astro_font_name, 24)
        # CRITICAL: Prevent the OS from substituting the glyphs with emoji or other fonts.
        planet_font.setStyleStrategy(QFont.StyleStrategy.NoFontMerging)
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
            # Since the whole canvas is flipped, we need to flip the text back
            painter.save()
            painter.translate(point)
            painter.scale(1, -1)
            self._draw_glow_text(painter, QPointF(-text_width / 2, text_height/4), glyph, planet_font, planet_color)
            painter.restore()

    def _draw_cusp_labels(self, painter, center, radius, color, angle_offset):
        """Helper method to draw the degree labels for each house cusp, rotated along the wheel."""
        if not self.display_houses: return
        label_font = QFont("Titillium Web", 12); label_font.setBold(True)
        def format_degree(deg):
            deg %= 360
            deg_in_sign = deg % 30
            minutes = (deg_in_sign - int(deg_in_sign)) * 60
            # Return only the degree and minute, without the zodiac symbol
            return f"{int(deg_in_sign)}° {int(minutes)}'"

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
            # Text needs to be readable, so we must flip it back upright in the new coordinate system
            painter.scale(1, -1)
            painter.rotate(-(rotation_angle + 180 if 90 < angle_with_offset % 360 < 270 else rotation_angle))

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

            # Since the whole canvas is flipped, we need to flip the text back
            # to make it readable.
            painter.save()
            painter.translate(point)
            painter.scale(1, -1)
            self._draw_glow_text(painter, QPointF(-text_width / 2, text_height / 4), text, house_font, color)
            painter.restore()

    def _draw_glow_path(self, painter, path, color, width):
        """
        Draws a QPainterPath with a multi-layered neon glow effect,
        replicating the user's specified CSS filter.
        The 'color' parameter is expected to be QColor("#3DF6FF").
        """
        # The base color is #3DF6FF, which is rgba(61, 246, 255).

        # CSS: drop-shadow(0 0 20px rgba(61, 246, 255, 0.4));
        glow_color_1 = QColor(61, 246, 255, int(255 * 0.4))
        pen1 = QPen(glow_color_1, width * 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen1)
        painter.drawPath(path)

        # CSS: drop-shadow(0 0 12px rgba(61, 246, 255, 0.7));
        glow_color_2 = QColor(61, 246, 255, int(255 * 0.7))
        pen2 = QPen(glow_color_2, width * 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen2)
        painter.drawPath(path)

        # CSS: drop-shadow(0 0 6px var(--neon-blue));
        pen3 = QPen(color, width * 1.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen3)
        painter.drawPath(path)

        # CSS: drop-shadow(0 0 2px var(--neon-blue));
        pen4 = QPen(color, width * 0.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen4)
        painter.drawPath(path)

        # Core line (stroke: var(--neon-blue); stroke-width: 4;)
        pen_core = QPen(color, width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen_core)
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