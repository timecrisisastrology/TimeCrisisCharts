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

    def _draw_zodiac_glyphs(self, painter, center, ring, color, angle_offset):
        """Draws zodiac glyphs within a specified ring."""
        font = QFont(self.astro_font_name, 35)
        font.setStyleStrategy(QFont.StyleStrategy.NoFontMerging)
        # Place glyphs in the center of their designated ring
        placement_radius = (ring['inner'] + ring['outer']) / 2

        for i, name in enumerate(self.zodiac_names):
            glyph = self.zodiac_glyphs[name]
            angle_deg = (i * 30) + 15 + angle_offset
            angle_rad = math.radians(angle_deg)

            x = center.x() + placement_radius * math.cos(angle_rad)
            y = center.y() + placement_radius * math.sin(angle_rad)

            font_metrics = QFontMetrics(font)
            text_width = font_metrics.horizontalAdvance(glyph)
            text_height = font_metrics.height()

            painter.save()
            painter.translate(x, y)
            painter.scale(1, -1)
            draw_point = QPointF(-text_width / 2, text_height / 4)
            glyph_color = self.zodiac_colors.get(name, color)
            self._draw_glow_text(painter, draw_point, glyph, font, glyph_color)
            painter.restore()

    def _calculate_rings(self, base_radius, is_biwheel):
        """
        Defines the precise inner and outer boundaries for all concentric data rings.
        This is the core of the professional layout system. It uses fixed-width lanes
        to guarantee separation and prevent overlaps.
        """
        rings = {}
        # Define fixed widths for each lane. These are pixel values.
        zodiac_width = 40
        cusp_label_width = 30
        planet_glyph_width = 35
        planet_info_width = 30
        separator_width = 8 # Gutter between wheels
        house_number_width = 25

        # Work from the outside in, starting from the base_radius.
        current_outer = base_radius
        rings['zodiac'] = {'outer': current_outer, 'inner': current_outer - zodiac_width}

        # The ring for cusp degree labels sits *outside* the main zodiac ring.
        rings['cusp_labels'] = {'outer': base_radius + cusp_label_width, 'inner': base_radius}

        # Set the boundary for the inner chart elements, starting from inside the zodiac.
        current_outer = rings['zodiac']['inner']

        if is_biwheel:
            # Layout for a two-wheel chart (e.g., Natal + Transits)
            rings['outer_planets_glyphs'] = {'outer': current_outer, 'inner': current_outer - planet_glyph_width}
            current_outer -= planet_glyph_width
            rings['outer_planets_info'] = {'outer': current_outer, 'inner': current_outer - planet_info_width}
            current_outer -= planet_info_width

            rings['separator'] = {'outer': current_outer, 'inner': current_outer - separator_width}
            current_outer -= separator_width

            rings['inner_planets_glyphs'] = {'outer': current_outer, 'inner': current_outer - planet_glyph_width}
            current_outer -= planet_glyph_width
            rings['inner_planets_info'] = {'outer': current_outer, 'inner': current_outer - planet_info_width}
            current_outer -= planet_info_width

            rings['house_numbers'] = {'outer': current_outer, 'inner': current_outer - house_number_width}
            current_outer -= house_number_width
        else:
            # Layout for a single-wheel chart (e.g., Natal only)
            # Give more space for a single wheel.
            single_glyph_width = 50
            single_info_width = 40

            rings['inner_planets_glyphs'] = {'outer': current_outer, 'inner': current_outer - single_glyph_width}
            current_outer -= single_glyph_width
            rings['inner_planets_info'] = {'outer': current_outer, 'inner': current_outer - single_info_width}
            current_outer -= single_info_width

            rings['house_numbers'] = {'outer': current_outer, 'inner': current_outer - house_number_width}
            current_outer -= house_number_width

        # The aspect grid fills the remaining space in the center.
        rings['aspect_grid'] = {'outer': current_outer, 'inner': 0}

        return rings

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.translate(0, self.height())
        painter.scale(1, -1)

        neon_pink = QColor("#FF01F9")
        neon_blue = QColor("#3DF6FF")
        center = QPointF(self.width() / 2, self.height() / 2)
        base_radius = min(self.width(), self.height()) / 2 * 0.9

        angle_offset = 180 - self.display_houses[0] if self.display_houses else 0
        is_biwheel = self.outer_planets is not None

        # --- 1. Architect the Layout using the Ring System ---
        rings = self._calculate_rings(base_radius, is_biwheel)

        # --- 2. Draw Structural Circles ---
        path = QPainterPath(); path.addEllipse(center, rings['zodiac']['outer'], rings['zodiac']['outer']); self._draw_glow_path(painter, path, neon_pink, 2)
        path = QPainterPath(); path.addEllipse(center, rings['zodiac']['inner'], rings['zodiac']['inner']); self._draw_glow_path(painter, path, neon_pink, 2)
        path = QPainterPath(); path.addEllipse(center, rings['aspect_grid']['outer'], rings['aspect_grid']['outer']); self._draw_glow_path(painter, path, neon_pink, 2)
        if is_biwheel:
            path = QPainterPath(); path.addEllipse(center, rings['separator']['outer'], rings['separator']['outer']); self._draw_glow_path(painter, path, neon_pink, 2)

        # --- 3. Draw Zodiac Glyphs and Dividers ---
        self._draw_zodiac_glyphs(painter, center, rings['zodiac'], neon_blue, angle_offset)
        for i in range(12):
            angle_rad = math.radians(i * 30 + angle_offset)
            x_start = center.x() + rings['zodiac']['inner'] * math.cos(angle_rad)
            y_start = center.y() + rings['zodiac']['inner'] * math.sin(angle_rad)
            x_end = center.x() + rings['zodiac']['outer'] * math.cos(angle_rad)
            y_end = center.y() + rings['zodiac']['outer'] * math.sin(angle_rad)
            divider_path = QPainterPath(); divider_path.moveTo(x_start, y_start); divider_path.lineTo(x_end, y_end)
            self._draw_glow_path(painter, divider_path, neon_blue, 1)

        # --- 4. Draw House Cusp Lines and Labels ---
        self._draw_cusp_labels(painter, center, rings['cusp_labels'], neon_blue, angle_offset)
        for cusp_deg in self.display_houses:
            angle_rad = math.radians(cusp_deg + angle_offset)
            x_start = center.x() + rings['aspect_grid']['outer'] * math.cos(angle_rad)
            y_start = center.y() + rings['aspect_grid']['outer'] * math.sin(angle_rad)
            x_end = center.x() + rings['zodiac']['outer'] * math.cos(angle_rad)
            y_end = center.y() + rings['zodiac']['outer'] * math.sin(angle_rad)
            cusp_path = QPainterPath(); cusp_path.moveTo(x_start, y_start); cusp_path.lineTo(x_end, y_end)
            self._draw_glow_path(painter, cusp_path, neon_pink, 1)

        # --- 5. Draw House Numbers ---
        self._draw_house_numbers(painter, center, rings['house_numbers'], neon_blue, angle_offset)

        # --- 6. Draw Planet Glyphs and Info ---
        if is_biwheel:
            # Draw outer (e.g., transiting) planets and their info in their dedicated rings
            self._draw_planets(painter, center, rings['outer_planets_glyphs'], rings['outer_planets_info'], self.outer_planets, angle_offset)
            # Draw inner (e.g., natal) planets and their info in their dedicated rings
            self._draw_planets(painter, center, rings['inner_planets_glyphs'], rings['inner_planets_info'], self.planets, angle_offset)
        else:
            # Draw single-wheel planets and info
            self._draw_planets(painter, center, rings['inner_planets_glyphs'], rings['inner_planets_info'], self.planets, angle_offset)

        # --- 7. Draw Aspect Lines ---
        aspect_radius = rings['aspect_grid']['outer'] * 0.95 # Place aspect lines inside the aspect grid
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

    def _draw_planets(self, painter, center, glyph_ring, info_ring, planets, angle_offset):
        """
        Draws planet glyphs and their labels within dedicated, non-overlapping rings.
        - Glyphs are drawn and staggered within the 'glyph_ring'.
        - Text info is drawn and staggered within the 'info_ring'.
        """
        planet_font = QFont(self.astro_font_name, 20)
        planet_font.setStyleStrategy(QFont.StyleStrategy.NoFontMerging)
        label_font = QFont("Titillium Web", 9)

        if not planets: return

        # --- 1. Graph-based Clustering (same as before) ---
        sorted_planets = sorted(planets.items(), key=lambda item: item[1][0])
        num_planets = len(sorted_planets)
        adj = [[] for _ in range(num_planets)]
        CONJUNCTION_THRESHOLD = 12.0

        for i in range(num_planets):
            for j in range(i + 1, num_planets):
                p1_lon = sorted_planets[i][1][0]
                p2_lon = sorted_planets[j][1][0]
                distance = abs(p1_lon - p2_lon)
                distance = min(distance, 360 - distance)
                if distance < CONJUNCTION_THRESHOLD:
                    adj[i].append(j)
                    adj[j].append(i)

        visited = [False] * num_planets
        clusters = []
        for i in range(num_planets):
            if not visited[i]:
                current_cluster = []
                q = [i]
                visited[i] = True
                while q:
                    u = q.pop(0)
                    current_cluster.append(sorted_planets[u])
                    for v in adj[u]:
                        if not visited[v]:
                            visited[v] = True
                            q.append(v)
                clusters.append(sorted(current_cluster, key=lambda item: item[1][0]))

        # --- 2. Drawing with Strict Ring Boundaries ---
        for cluster in clusters:
            num_in_cluster = len(cluster)
            is_cluster = num_in_cluster > 1

            for i, (name, position_data) in enumerate(cluster):
                longitude = position_data[0]
                angle_rad = math.radians(longitude + angle_offset)
                planet_color = self.planet_colors.get(name, QColor("white"))

                # --- Position and Draw Planet Glyph in its Ring ---
                glyph_ring_thickness = glyph_ring['outer'] - glyph_ring['inner']
                if is_cluster:
                    buffer = glyph_ring_thickness * 0.1
                    usable_thickness = glyph_ring_thickness - (2 * buffer)
                    t = i / (num_in_cluster - 1)
                    glyph_radius = (glyph_ring['outer'] - buffer) - (t * usable_thickness)
                else:
                    glyph_radius = (glyph_ring['inner'] + glyph_ring['outer']) / 2

                glyph = self.planet_glyphs.get(name, '?')
                fm_glyph = QFontMetrics(planet_font)
                glyph_width = fm_glyph.horizontalAdvance(glyph)
                glyph_height = fm_glyph.height()

                glyph_x = center.x() + glyph_radius * math.cos(angle_rad)
                glyph_y = center.y() + glyph_radius * math.sin(angle_rad)

                painter.save()
                painter.translate(glyph_x, glyph_y)
                painter.scale(1, -1)
                self._draw_glow_text(painter, QPointF(-glyph_width / 2, glyph_height / 4), glyph, planet_font, planet_color)
                painter.restore()

                # --- Position and Draw Position Label in its Ring ---
                is_retrograde = position_data[1] < 0
                retro_symbol = " \u211E" if is_retrograde else ""
                label_text = f"{format_longitude(longitude, show_sign=True)}{retro_symbol}"
                fm_label = QFontMetrics(label_font)
                label_width = fm_label.horizontalAdvance(label_text)

                info_ring_thickness = info_ring['outer'] - info_ring['inner']
                if is_cluster:
                    # Stagger info labels in sync with their glyphs
                    buffer = info_ring_thickness * 0.1
                    usable_thickness = info_ring_thickness - (2 * buffer)
                    t = i / (num_in_cluster - 1)
                    label_radius = (info_ring['outer'] - buffer) - (t * usable_thickness)
                else:
                    label_radius = (info_ring['inner'] + info_ring['outer']) / 2

                label_x = center.x() + label_radius * math.cos(angle_rad)
                label_y = center.y() + label_radius * math.sin(angle_rad)

                painter.save()
                painter.translate(label_x, label_y)
                painter.scale(1, -1)

                effective_angle = longitude + angle_offset
                painter.rotate(-effective_angle)

                if 90 < effective_angle % 360 < 270:
                    painter.rotate(180)
                    # For text on the left, anchor from the right
                    final_draw_point = QPointF(-label_width, fm_label.ascent() / 2)
                else:
                    # For text on the right, anchor from the left
                    final_draw_point = QPointF(0, fm_label.ascent() / 2)

                self._draw_glow_text(painter, final_draw_point, label_text, label_font, planet_color)
                painter.restore()

    def _draw_cusp_labels(self, painter, center, ring, color, angle_offset):
        """
        Draws the degree labels for each house cusp, placing them within a dedicated ring.
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
            # Start placement in the middle of the ring
            label_radius = (ring['inner'] + ring['outer']) / 2

            # --- Collision Avoidance Loop ---
            while True:
                angle_rad = math.radians(angle_with_offset)
                x = center.x() + label_radius * math.cos(angle_rad)
                y = center.y() + label_radius * math.sin(angle_rad)

                text_width = font_metrics.horizontalAdvance(text)
                text_height = font_metrics.height()

                transform = QTransform()
                transform.translate(x, y)
                rotation_angle = angle_with_offset - 90
                if 90 < angle_with_offset % 360 < 270:
                    transform.rotate(-(rotation_angle + 180))
                else:
                    transform.rotate(-rotation_angle)
                untransformed_rect = QRectF(-text_width / 2, -text_height / 2, text_width, text_height)
                current_rect = transform.mapRect(untransformed_rect)

                is_overlapping = any(current_rect.intersects(r) for r in drawn_label_rects)

                if not is_overlapping:
                    drawn_label_rects.append(current_rect)
                    break

                # If overlapping, push the label further out, but cap it at the ring's outer boundary
                label_radius += 5
                if label_radius > ring['outer']:
                    # As a fallback, just draw it and accept the overlap if it can't be resolved.
                    # A more advanced strategy could shrink the font size.
                    break


            # --- Draw the label at the final, non-overlapping position ---
            painter.save()
            painter.translate(x, y)
            painter.scale(1, -1)
            rotation_angle = angle_with_offset - 90
            painter.rotate(-(rotation_angle + 180 if 90 < angle_with_offset % 360 < 270 else rotation_angle))
            draw_point = QPointF(-text_width / 2, font_metrics.height() / 4)
            self._draw_glow_text(painter, draw_point, text, label_font, color)
            painter.restore()

    def _draw_house_numbers(self, painter, center, ring, color, angle_offset):
        """Draws the house numbers centered within their dedicated ring."""
        if not self.display_houses: return
        house_font = QFont("Titillium Web", 10)
        house_font.setBold(True)
        # Place numbers in the center of their designated ring
        placement_radius = (ring['inner'] + ring['outer']) / 2

        for i in range(12):
            start_angle = self.display_houses[i]
            end_angle = self.display_houses[(i + 1) % 12]
            if end_angle < start_angle: end_angle += 360

            mid_angle_deg = (start_angle + end_angle) / 2 + angle_offset
            angle_rad = math.radians(mid_angle_deg)

            x = center.x() + placement_radius * math.cos(angle_rad)
            y = center.y() + placement_radius * math.sin(angle_rad)

            text = str(i + 1)
            painter.save()
            painter.translate(x, y)
            painter.scale(1, -1)

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