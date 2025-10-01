import sys
import math
from PyQt6.QtWidgets import QWidget, QLabel, QFormLayout, QVBoxLayout, QFrame, QPushButton, QLineEdit
from PyQt6.QtGui import QFont, QPainter, QPen, QColor, QBrush, QFontMetrics, QPainterPath, QTransform
from PyQt6.QtCore import Qt, QPointF, QRectF, QRect
from astro_engine import format_longitude, get_zodiac_sign

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
        """
        Initializes all glyph and color data for rendering.
        This application uses the "EnigmaAstrology2" font, which is licensed
        under the GPL. The font is available from: http://radixpro.com/downloads/font/
        """
        # --- Zodiac Sign Glyphs (using correct Unicode characters for EnigmaAstrology2) ---
        self.zodiac_glyphs = {
            'Aries': '\uE000', 'Taurus': '\uE001', 'Gemini': '\uE002', 'Cancer': '\uE003',
            'Leo': '\uE004', 'Virgo': '\uE005', 'Libra': '\uE006', 'Scorpio': '\uE007',
            'Sagittarius': '\uE008', 'Capricorn': '\uE009', 'Aquarius': '\uE010', 'Pisces': '\uE011'
        }
        self.zodiac_names = list(self.zodiac_glyphs.keys())

        # --- Planet Glyphs (using correct Unicode characters for EnigmaAstrology2) ---
        self.planet_glyphs = {
            'Sun': '\uE200', 'Moon': '\uE201', 'Mercury': '\uE202', 'Venus': '\uE203', 'Mars': '\uE205',
            'Jupiter': '\uE206', 'Saturn': '\uE207', 'Uranus': '\uE208', 'Neptune': '\uE209', 'Pluto': '\uE210',
            'ASC': '\uE500', 'MC': '\uE501'
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
            'ASC': neon_blue, 'MC': neon_pink,                             # Angles
        }

        # --- NEW: Elemental colors for Zodiac signs ---
        self.zodiac_colors = {
            'Aries': neon_pink, 'Leo': neon_pink, 'Sagittarius': neon_pink, # Fire
            'Taurus': neon_green, 'Virgo': neon_green, 'Capricorn': neon_green, # Earth
            'Gemini': neon_yellow, 'Libra': neon_yellow, 'Aquarius': neon_yellow, # Air
            'Cancer': neon_blue, 'Scorpio': neon_blue, 'Pisces': neon_blue, # Water
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
            glyph_color = self.zodiac_colors.get(name, color) # Use new color map
            self._draw_glow_text(painter, draw_point, glyph, font, glyph_color)
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
            "zodiac_outer": radius,
            "zodiac_inner": radius * 0.85,
            "outer_wheel": radius * 0.70, # Adjusted for more space
            "inner_wheel": radius * 0.50, # Adjusted for more space
            "aspect_circle": radius * 0.30, # Adjusted
            "outer_planets": radius * 0.78, # Adjusted
            "inner_planets_bi": radius * 0.60, # Adjusted
            "inner_planets_single": radius * 0.60,
            "house_numbers": radius * 0.22, # Moved house numbers inward
            "aspect_lines": radius * 0.30 * 0.95 # Adjusted
        }

        # 1. Draw concentric circles
        path = QPainterPath(); path.addEllipse(center, radii["zodiac_outer"], radii["zodiac_outer"]); self._draw_glow_path(painter, path, neon_pink, 2)
        path = QPainterPath(); path.addEllipse(center, radii["zodiac_inner"], radii["zodiac_inner"]); self._draw_glow_path(painter, path, neon_pink, 2)
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
        """
        Draws planet glyphs and their corresponding degree labels, with lines
        pointing towards the center, similar to the user's example.
        """
        planet_font = QFont(self.astro_font_name, 24)
        planet_font.setStyleStrategy(QFont.StyleStrategy.NoFontMerging)
        label_font = QFont("Titillium Web", 10) # Increased font size for clarity

        sorted_planets = sorted(planets.items(), key=lambda item: item[1][0])
        clusters = []
        if not sorted_planets: return

        current_cluster = [sorted_planets[0]]
        CONJUNCTION_THRESHOLD = 12.0

        for i in range(1, len(sorted_planets)):
            prev_lon = current_cluster[-1][1][0]
            curr_lon = sorted_planets[i][1][0]
            distance = abs(curr_lon - prev_lon)
            distance = min(distance, 360 - distance)
            if distance < CONJUNCTION_THRESHOLD:
                current_cluster.append(sorted_planets[i])
            else:
                clusters.append(current_cluster)
                current_cluster = [sorted_planets[i]]
        clusters.append(current_cluster)

        for cluster in clusters:
            num_planets_in_cluster = len(cluster)
            is_cluster = num_planets_in_cluster > 1

            if is_cluster:
                longitudes = [p[1][0] for p in cluster]
                avg_lon = sum(longitudes) / num_planets_in_cluster
                if max(longitudes) - min(longitudes) > 180: # Handle wrap-around for avg
                    avg_lon = (sum(l + 360 if l < 180 else l for l in longitudes) / num_planets_in_cluster) % 360

            for i, (name, position_data) in enumerate(cluster):
                longitude = position_data[0]

                if is_cluster:
                    angle_step = 6
                    start_angle = avg_lon - (angle_step * (num_planets_in_cluster - 1) / 2)
                    current_angle = start_angle + i * angle_step
                    current_radius = radius * (1 - 0.12 * (i % 2)) # Stagger radius
                else:
                    current_angle = longitude
                    current_radius = radius

                angle_rad = math.radians(current_angle + angle_offset)
                planet_color = self.planet_colors.get(name, QColor("white"))

                # --- Draw Planet Glyph ---
                glyph_x = center.x() + current_radius * math.cos(angle_rad)
                glyph_y = center.y() + current_radius * math.sin(angle_rad)
                glyph = self.planet_glyphs.get(name, '?')
                painter.save()
                painter.translate(glyph_x, glyph_y)
                painter.scale(1, -1)
                font_metrics = QFontMetrics(planet_font)
                self._draw_glow_text(painter, QPointF(-font_metrics.horizontalAdvance(glyph) / 2, font_metrics.height() / 4), glyph, planet_font, planet_color)
                painter.restore()

                # --- Draw Position Label ---
                label_radius = current_radius * 0.85
                label_text = f"{format_longitude(longitude, show_sign=False)}\n{get_zodiac_sign(longitude)[:3]}"

                font_metrics = QFontMetrics(label_font)
                # Use a QRect for bounding to handle multi-line text correctly
                text_rect = font_metrics.boundingRect(QRect(0,0,150,50), Qt.AlignmentFlag.AlignCenter, label_text)

                label_x = center.x() + label_radius * math.cos(angle_rad)
                label_y = center.y() + label_radius * math.sin(angle_rad)

                painter.save()
                painter.translate(label_x, label_y)
                painter.scale(1, -1)

                rotation_angle = current_angle + angle_offset

                # Rotate the canvas to align with the planet's angle
                painter.rotate(-rotation_angle)

                # Adjust for readability based on position
                if 90 < (rotation_angle + 90) % 360 < 270:
                    # Left side of the chart: flip text 180 degrees to be readable
                    painter.rotate(180)
                    # Draw text starting from the point, moving away (which is inward)
                    draw_point = QPointF(5, -text_rect.height() / 2 + font_metrics.ascent())
                else:
                    # Right side of the chart: draw text "backwards" from the point
                    draw_point = QPointF(-text_rect.width() - 5, -text_rect.height() / 2 + font_metrics.ascent())

                self._draw_glow_text(painter, draw_point, label_text, label_font, planet_color)
                painter.restore()

    def _draw_cusp_labels(self, painter, center, radius, color, angle_offset):
        """
        Helper method to draw the degree labels for each house cusp, rotated along the wheel.
        Includes collision avoidance to prevent labels from overlapping.
        """
        if not self.display_houses: return
        label_font = QFont("Titillium Web", 12); label_font.setBold(True)
        font_metrics = QFontMetrics(label_font)
        drawn_label_rects = []

        def format_degree(deg):
            deg %= 360
            deg_in_sign = deg % 30
            minutes = (deg_in_sign - int(deg_in_sign)) * 60
            return f"{int(deg_in_sign)}° {int(minutes)}'"

        for i, cusp_deg in enumerate(self.display_houses):
            text = format_degree(cusp_deg)
            if i == 0: text = f"ASC = {text}"

            angle_with_offset = cusp_deg + angle_offset
            label_radius = radius * 1.07

            # --- Collision Avoidance Loop ---
            while True:
                angle_rad = math.radians(angle_with_offset)
                x = center.x() + label_radius * math.cos(angle_rad)
                y = center.y() + label_radius * math.sin(angle_rad)

                # Get the bounding rectangle of the text *before* rotation
                text_width = font_metrics.horizontalAdvance(text)
                text_height = font_metrics.height()

                # Create a transformed bounding box for collision detection
                transform = QTransform()
                transform.translate(x, y)
                rotation_angle = angle_with_offset - 90
                if 90 < angle_with_offset % 360 < 270:
                    transform.rotate(-(rotation_angle + 180))
                else:
                    transform.rotate(-rotation_angle)

                # Define the rectangle centered around the origin
                untransformed_rect = QRectF(-text_width / 2, -text_height / 2, text_width, text_height)
                current_rect = transform.mapRect(untransformed_rect)

                # Check for intersections with already drawn labels
                is_overlapping = any(current_rect.intersects(r) for r in drawn_label_rects)

                if not is_overlapping:
                    drawn_label_rects.append(current_rect)
                    break

                # If overlapping, push the label further out radially
                label_radius += 5

            # --- Draw the label at the final, non-overlapping position ---
            painter.save()
            painter.translate(x, y)
            painter.scale(1, -1)
            rotation_angle = angle_with_offset - 90
            painter.rotate(-(rotation_angle + 180 if 90 < angle_with_offset % 360 < 270 else rotation_angle))
            draw_point = QPointF(-text_width / 2, font_metrics.height() / 4)
            self._draw_glow_text(painter, draw_point, text, label_font, color)
            painter.restore()

    def _draw_house_numbers(self, painter, center, radius, color, angle_offset):
        """Helper method to draw the house numbers in their new, smaller inner ring."""
        if not self.display_houses: return
        house_font = QFont("Titillium Web", 10) # Smaller font for a smaller ring
        house_font.setBold(True)
        for i in range(12):
            start_angle = self.display_houses[i]
            end_angle = self.display_houses[(i + 1) % 12]
            if end_angle < start_angle: end_angle += 360

            # Place number in the middle of the house
            mid_angle_deg = (start_angle + end_angle) / 2 + angle_offset
            angle_rad = math.radians(mid_angle_deg)

            x = center.x() + radius * math.cos(angle_rad)
            y = center.y() + radius * math.sin(angle_rad)

            text = str(i + 1)
            painter.save()
            painter.translate(x, y)
            painter.scale(1, -1) # Flip text to be upright

            font_metrics = QFontMetrics(house_font)
            text_width = font_metrics.horizontalAdvance(text)
            text_height = font_metrics.height()

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

        # 1. Outer Glow: Soft and wide
        glow_color1 = QColor(color)
        glow_color1.setAlpha(40) # Reduced alpha for subtlety
        pen1 = QPen(glow_color1, 7, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen1)
        painter.drawText(point, text)

        # 2. Inner Glow: Tighter and brighter
        glow_color2 = QColor(color)
        glow_color2.setAlpha(80) # Reduced alpha
        pen2 = QPen(glow_color2, 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen2)
        painter.drawText(point, text)

        # 3. Core Text: Use the actual neon color, not a lightened version
        pen3 = QPen(color, 1, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen3)
        painter.drawText(point, text)