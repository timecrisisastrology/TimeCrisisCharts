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

class ChartWidget(QFrame):
    """A custom widget for drawing the astrological chart."""
    def __init__(self, astro_font_name):
        super().__init__()
        self.setMinimumSize(400, 400) # Ensure the widget has a decent size
        self.setStyleSheet("background-color: transparent; border: none;")
        self.astro_font_name = astro_font_name # Store the font name

        # Chart data - will be populated by set_chart_data
        self.house_cusps = []
        self.display_houses = [] # Houses to draw (can be natal or return)
        self.natal_planets = {} # Inner wheel planets
        self.transit_planets = None # Outer wheel planets
        self.aspects = []
        self._setup_glyph_data()

    def set_chart_data(self, natal_planets, natal_houses, aspects, outer_planets=None, display_houses=None):
        """
        Sets the data for the chart. The 'outer_planets' parameter is used for the
        second wheel, which could be transits, progressions, etc.
        """
        self.natal_planets = natal_planets
        self.house_cusps = natal_houses
        self.aspects = aspects
        self.transit_planets = outer_planets
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

    def _calculate_dynamic_layout(self, wheels, width, height):
        """
        Calculates the layout of the chart wheels based on the user's test script.
        This uses a relative 0-1 coordinate system which is then scaled by the
        widget's dimensions.
        """
        # --- CONFIGURATION ---
        # These values are relative to the chart radius
        AREA_START_RADIUS = 0.15 # Outer edge of the fixed house number circle
        AREA_END_RADIUS = 0.9    # Inner edge of the fixed zodiac circle
        WHEEL_THICKNESS = 0.33   # The relative thickness for each planet wheel
        GUTTER_THICKNESS = 0.02  # The gap between wheels

        # The base radius is the main scaling factor for all elements
        base_radius = min(width, height) / 2

        layout = {}
        wheels_to_draw = [w for w in wheels if w['planets']]

        num_wheels = len(wheels_to_draw)

        # --- SCALED RADII ---
        # Convert relative radii to absolute pixel values
        layout['zodiac_signs'] = {
            'inner': AREA_END_RADIUS * base_radius,
            'outer': 1.0 * base_radius
        }
        layout['house_numbers_ring'] = {
            'inner': (AREA_START_RADIUS - 0.02) * base_radius, # A bit of space
            'outer': AREA_START_RADIUS * base_radius
        }
        layout['house_numbers_text'] = {'radius': 0.13 * base_radius}
        layout['aspect_grid'] = {'radius': layout['house_numbers_ring']['inner']}

        if num_wheels == 0:
            return layout

        # --- DYNAMIC WHEEL CALCULATION ---
        TOTAL_AVAILABLE_SPACE = (AREA_END_RADIUS - AREA_START_RADIUS) * base_radius

        # Calculate the total required space for all wheels and gutters
        total_wheel_space = (num_wheels * WHEEL_THICKNESS * base_radius)
        total_gutter_space = (max(0, num_wheels - 1) * GUTTER_THICKNESS * base_radius)
        total_required_space = total_wheel_space + total_gutter_space

        # If the required space is more than available, scale down the wheel thickness
        if total_required_space > TOTAL_AVAILABLE_SPACE:
            scale_factor = TOTAL_AVAILABLE_SPACE / total_required_space
            scaled_wheel_thickness = WHEEL_THICKNESS * base_radius * scale_factor
            scaled_gutter_thickness = GUTTER_THICKNESS * base_radius * scale_factor
        else:
            scaled_wheel_thickness = WHEEL_THICKNESS * base_radius
            scaled_gutter_thickness = GUTTER_THICKNESS * base_radius

        # Distribute the wheels from the outside in
        current_outer_radius = AREA_END_RADIUS * base_radius

        # Iterate through the wheels in reverse to place them from outside to inside
        for wheel in reversed(wheels_to_draw):
            ring_outer = current_outer_radius
            ring_inner = ring_outer - scaled_wheel_thickness
            layout[wheel['name']] = {'inner': ring_inner, 'outer': ring_outer}
            # Move to the next position, leaving a gutter
            current_outer_radius = ring_inner - scaled_gutter_thickness

        return layout

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.natal_planets:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Invert the Y-axis for a standard Cartesian coordinate system (0,0 at bottom-left)
        painter.translate(0, self.height())
        painter.scale(1, -1)

        center = QPointF(self.width() / 2, self.height() / 2)
        angle_offset = 180 - self.display_houses[0]

        # --- 1. Define Wheels and Calculate Layout ---
        wheels_to_draw = [{'name': 'natal', 'planets': self.natal_planets}]
        if self.transit_planets:
            wheels_to_draw.append({'name': 'transits', 'planets': self.transit_planets})

        layout = self._calculate_dynamic_layout(wheels_to_draw, self.width(), self.height())

        # --- 2. Draw Chart Scaffolding (Structural Lines) ---
        self._draw_chart_scaffolding(painter, center, layout, angle_offset)

        # --- 3. Draw Zodiac Glyphs ---
        self._draw_zodiac_glyphs(painter, center, layout['zodiac_signs'], QColor("#3DF6FF"), angle_offset)

        # --- 4. Draw House Numbers ---
        self._draw_house_numbers(painter, center, layout, QColor("#3DF6FF"), angle_offset)

        # --- 4a. Draw House Cusp Labels ---
        self._draw_house_cusp_labels(painter, center, layout, QColor("#3DF6FF"), angle_offset)

        # --- 5. Draw Planets for Each Wheel ---
        for wheel in wheels_to_draw:
            if wheel['name'] in layout:
                self._draw_wheel_planets(painter, center, wheel, layout[wheel['name']], angle_offset)

        # --- 6. Draw Aspect Lines ---
        self._draw_aspects(painter, center, layout['aspect_grid']['radius'], angle_offset)

    def _format_degree_text(self, degree):
        """Formats a decimal degree into a string with degree, sign, and minute."""
        zodiac_signs = ['Ari', 'Tau', 'Gem', 'Can', 'Leo', 'Vir', 'Lib', 'Sco', 'Sag', 'Cap', 'Aqu', 'Pis']
        sign_index = int(degree / 30)
        sign_name = zodiac_signs[sign_index]
        deg_in_sign = int(degree % 30)
        minutes = int((degree % 1) * 60)
        return f"{deg_in_sign}° {sign_name} {minutes:02d}'"

    def _draw_chart_scaffolding(self, painter, center, layout, angle_offset):
        """Draws the primary circles and lines for the chart structure."""
        line_color = QColor("#A372FF")

        # Draw outer zodiac circle, inner zodiac circle, and house number circle
        path = QPainterPath(); path.addEllipse(center, layout['zodiac_signs']['outer'], layout['zodiac_signs']['outer']); self._draw_glow_path(painter, path, line_color, 2)
        path = QPainterPath(); path.addEllipse(center, layout['zodiac_signs']['inner'], layout['zodiac_signs']['inner']); self._draw_glow_path(painter, path, line_color, 1)
        path = QPainterPath(); path.addEllipse(center, layout['house_numbers_ring']['outer'], layout['house_numbers_ring']['outer']); self._draw_glow_path(painter, path, line_color, 1)

        # Draw the circles for each dynamic wheel that has been calculated
        for wheel_name in ['natal', 'transits', 'progressions']: # Add other wheel types if needed
            if wheel_name in layout:
                wheel_outer_radius = layout[wheel_name]['outer']
                path = QPainterPath(); path.addEllipse(center, wheel_outer_radius, wheel_outer_radius); self._draw_glow_path(painter, path, line_color, 1)

        # Draw house cusp lines
        for i, cusp_degree in enumerate(self.display_houses[:12]):
            angle_rad = math.radians(cusp_degree + angle_offset)
            is_axis = i in [0, 3, 6, 9] # ASC, IC, DSC, MC

            x_start = center.x() + layout['house_numbers_ring']['outer'] * math.cos(angle_rad)
            y_start = center.y() + layout['house_numbers_ring']['outer'] * math.sin(angle_rad)
            x_end = center.x() + layout['zodiac_signs']['inner'] * math.cos(angle_rad)
            y_end = center.y() + layout['zodiac_signs']['inner'] * math.sin(angle_rad)

            cusp_path = QPainterPath(); cusp_path.moveTo(x_start, y_start); cusp_path.lineTo(x_end, y_end)
            self._draw_glow_path(painter, cusp_path, line_color, 3 if is_axis else 1)

    def _draw_wheel_planets(self, painter, center, wheel_data, ring, angle_offset):
        """Draws planets for a single wheel using the definitive layout algorithm."""
        glyph_font = QFont(self.astro_font_name, 24)
        glyph_font.setStyleStrategy(QFont.StyleStrategy.NoFontMerging)
        text_font = QFont("Titillium Web", 11)
        font_color = QColor("#E0D2FF")

        # --- 1. Clustering Logic ---
        CLUSTER_THRESHOLD = 8 # Degrees
        planets_list = []
        for name, (degree, speed) in wheel_data['planets'].items():
            if name in self.planet_glyphs:
                planets_list.append({
                    'name': name,
                    'deg': degree,
                    'glyph': self.planet_glyphs[name],
                    'label': self._format_degree_text(degree)
                })

        planets_list.sort(key=lambda p: p['deg'])
        clusters = []
        if planets_list:
            current_cluster = [planets_list[0]]
            for i in range(1, len(planets_list)):
                diff = abs(planets_list[i]['deg'] - planets_list[i-1]['deg'])
                if diff > 180: diff = 360 - diff
                if diff <= CLUSTER_THRESHOLD:
                    current_cluster.append(planets_list[i])
                else:
                    clusters.append(current_cluster)
                    current_cluster = [planets_list[i]]
            clusters.append(current_cluster)

        # --- 2. New Layout and Drawing Logic ---
        for cluster in clusters:
            num_in_cluster = len(cluster)
            for i, planet in enumerate(cluster):
                # --- Angular Spreading (side-by-side nudge) ---
                angular_offset_nudge = 0
                if num_in_cluster > 1:
                    SPREAD_ANGLE = 5.0 # Degrees
                    # Calculate the starting offset to center the cluster
                    start_offset = - (num_in_cluster - 1) / 2.0 * SPREAD_ANGLE
                    angular_offset_nudge = start_offset + (i * SPREAD_ANGLE)

                display_deg = planet['deg'] + angular_offset_nudge
                angle_rad = math.radians(display_deg + angle_offset)

                # --- Radial Positioning (glyph out, text in) ---
                # These are based on the user's test script for relative positioning
                glyph_radius = ring['outer'] - ( (ring['outer'] - ring['inner']) * 0.25 )
                text_radius = glyph_radius - ( (ring['outer'] - ring['inner']) * 0.40 )

                # --- Draw the Glyph ---
                fm_glyph = QFontMetrics(glyph_font)
                glyph_width = fm_glyph.horizontalAdvance(planet['glyph'])
                glyph_height = fm_glyph.height()
                glyph_x = center.x() + glyph_radius * math.cos(angle_rad)
                glyph_y = center.y() + glyph_radius * math.sin(angle_rad)

                painter.save()
                painter.translate(glyph_x, glyph_y)
                painter.scale(1, -1) # Flip text right-side up
                self._draw_glow_text(painter, QPointF(-glyph_width / 2, glyph_height / 4), planet['glyph'], glyph_font, font_color)
                painter.restore()

                # --- THE DEFINITIVE ROTATION ALGORITHM ---
                fm_text = QFontMetrics(text_font)
                text_width = fm_text.horizontalAdvance(planet['label'])
                text_height = fm_text.height()
                text_x = center.x() + text_radius * math.cos(angle_rad)
                text_y = center.y() + text_radius * math.sin(angle_rad)

                painter.save()
                painter.translate(text_x, text_y)
                painter.scale(1, -1) # Flip text right-side up

                # The rotation is the angle of the text's position, adjusted to be radial
                rotation = display_deg + angle_offset

                # If it's on the left side of the chart, flip it to be readable
                if 90 < (display_deg + angle_offset) % 360 < 270:
                    rotation += 180

                painter.rotate(-rotation)

                # Anchor the text so it rotates around its center
                draw_point = QPointF(-text_width / 2, text_height / 4)
                self._draw_glow_text(painter, draw_point, planet['label'], text_font, font_color)
                painter.restore()

    def _draw_house_numbers(self, painter, center, layout, color, angle_offset):
        """Draws the house numbers centered within their dedicated ring."""
        if not self.display_houses: return
        house_font = QFont("Titillium Web", 14)
        placement_radius = layout['house_numbers_text']['radius']

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

    def _draw_house_cusp_labels(self, painter, center, layout, color, angle_offset):
        """Draws the house cusp degree labels outside the zodiac, with overlap prevention."""
        if not self.display_houses: return
        text_font = QFont("Titillium Web", 10)
        font_color = QColor("#E0D2FF")
        placement_radius = layout['zodiac_signs']['outer'] + 10 # Just outside the zodiac ring

        # 1. Prepare cusp data
        cusps = []
        for i, degree in enumerate(self.display_houses[:12]):
            cusps.append({
                'label': self._format_degree_text(degree),
                'deg': degree
            })

        # 2. Clustering logic (adapted from planet drawing)
        CLUSTER_THRESHOLD = 12 # Degrees - larger threshold for text labels
        clusters = []
        if cusps:
            current_cluster = [cusps[0]]
            for i in range(1, len(cusps)):
                diff = abs(cusps[i]['deg'] - cusps[i-1]['deg'])
                if diff > 180: diff = 360 - diff # Handle wrap-around
                if diff <= CLUSTER_THRESHOLD:
                    current_cluster.append(cusps[i])
                else:
                    clusters.append(current_cluster)
                    current_cluster = [cusps[i]]
            clusters.append(current_cluster)

        # 3. Drawing with spreading
        for cluster in clusters:
            num_in_cluster = len(cluster)
            for i, cusp in enumerate(cluster):
                # Apply angular spreading if in a cluster
                angular_offset_nudge = 0
                if num_in_cluster > 1:
                    SPREAD_ANGLE = 10.0 # Degrees to nudge each label by
                    start_offset = - (num_in_cluster - 1) / 2.0 * SPREAD_ANGLE
                    angular_offset_nudge = start_offset + (i * SPREAD_ANGLE)

                display_deg = cusp['deg'] + angular_offset_nudge
                angle_rad = math.radians(display_deg + angle_offset)

                fm_text = QFontMetrics(text_font)
                text_width = fm_text.horizontalAdvance(cusp['label'])
                text_height = fm_text.height()

                text_x = center.x() + placement_radius * math.cos(angle_rad)
                text_y = center.y() + placement_radius * math.sin(angle_rad)

                painter.save()
                painter.translate(text_x, text_y)
                painter.scale(1, -1)

                rotation = display_deg + angle_offset
                if 90 < (display_deg + angle_offset) % 360 < 270:
                    rotation += 180

                painter.rotate(-rotation)
                draw_point = QPointF(-text_width / 2, text_height / 4)
                self._draw_glow_text(painter, draw_point, cusp['label'], text_font, font_color)
                painter.restore()

    def _draw_aspects(self, painter, center, radius, angle_offset):
        """Draws the aspect lines in the center of the chart."""
        aspect_colors = {
            'Trine': QColor(61, 246, 255, 150), 'Sextile': QColor(61, 246, 255, 150),
            'Square': QColor(255, 1, 249, 150), 'Opposition': QColor(255, 1, 249, 150),
            'Conjunction': QColor(200, 200, 200, 150)
        }
        for aspect_info in self.aspects:
            p1_name, aspect_name, p2_name = aspect_info['p1'], aspect_info['aspect'], aspect_info['p2']
            if p1_name in self.natal_planets and p2_name in self.natal_planets:
                p1_pos, p2_pos = self.natal_planets[p1_name][0], self.natal_planets[p2_name][0]
                color = aspect_colors.get(aspect_name)
                if color:
                    pen = QPen(color, 1.5, Qt.PenStyle.SolidLine)
                    painter.setPen(pen)
                    p1_rad = math.radians(p1_pos + angle_offset)
                    p1_x = center.x() + radius * math.cos(p1_rad)
                    p1_y = center.y() + radius * math.sin(p1_rad)
                    p2_rad = math.radians(p2_pos + angle_offset)
                    p2_x = center.x() + radius * math.cos(p2_rad)
                    p2_y = center.y() + radius * math.sin(p2_rad)
                    painter.drawLine(QPointF(p1_x, p1_y), QPointF(p2_x, p2_y))

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