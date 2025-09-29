from datetime import datetime, timedelta
from PyQt6.QtWidgets import QFrame, QToolTip
from PyQt6.QtGui import QFont, QColor, QPainter, QPen, QBrush, QPainterPath
from PyQt6.QtCore import Qt, QPointF, QRectF
from astro_engine import (
    calculate_secondary_progressions,
    calculate_aspects, find_cross_aspects,
    PLANETS, get_planet_position,
    get_house_ruler, get_zodiac_sign
)

class TimelineGridWidget(QFrame):
    """A dedicated widget for drawing the timeline grid and aspect lines based on the new design."""
    def __init__(self):
        super().__init__()
        self.setObjectName("timeline-grid")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setMinimumHeight(600) # Increased height for new layout
        self.setMouseTracking(True)

        # State & Data
        self.start_date = datetime.now()
        self.months_to_display = 3
        self.birth_date = None
        self.natal_planets = {}
        self.natal_houses = []
        self.aspect_events = []
        self.timeline_aspects_cache = {} # Cache for daily calculations

        # Theming
        self.colors = {
            'grid': QColor("#3DF6FF"),
            'text': QColor("#94EBFF"),
            'lunar': QColor("#F9EEFB"),
            'solar': QColor("#75439E"),
            'transit': QColor("#3DF6FF"),
            'star': QColor("#FFFF00"),
            'box_bg': QColor(255, 1, 249, 20), # Semi-transparent pink
        }
        self.fonts = {
            'year': QFont("TT Supermolot Neue Condensed", 14, QFont.Weight.Bold),
            'month': QFont("Titillium Web", 12),
            'grid': QFont("Titillium Web", 9),
            'star': QFont("Titillium Web", 16, QFont.Weight.Bold)
        }

    def set_chart_data(self, birth_date, natal_planets, natal_houses):
        """Receives natal data and triggers the aspect calculation for the timeline."""
        self.birth_date = birth_date
        self.natal_planets = natal_planets
        self.natal_houses = natal_houses
        self._calculate_and_process_timeline()
        self.update()

    def set_timescale(self, months):
        self.months_to_display = months
        self._calculate_and_process_timeline()
        self.update()

    # --- Data Calculation ---

    def _calculate_and_process_timeline(self):
        """High-level method to run the full calculation and processing pipeline."""
        self._calculate_daily_aspects()
        self._process_aspect_events()

    def _calculate_daily_aspects(self):
        if not self.birth_date or not self.natal_planets: return
        self.timeline_aspects_cache = {}
        num_days = self.months_to_display * 30

        for i in range(num_days + 2):
            current_date = self.start_date + timedelta(days=i - 1)
            date_key = current_date.strftime('%Y-%m-%d')

            transit_planets = {name: get_planet_position(current_date, pid) for name, pid in PLANETS.items()}
            progressed_planets = calculate_secondary_progressions(self.birth_date, current_date)

            prog_aspects = calculate_aspects(progressed_planets, 1)
            major_transits = {p: transit_planets[p] for p in ['Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto']}
            transit_aspects = find_cross_aspects(major_transits, self.natal_planets, 1.5)

            self.timeline_aspects_cache[date_key] = {
                'lunar_prog': [a for a in prog_aspects if 'Moon' in a['name']],
                'other_prog': [a for a in prog_aspects if 'Moon' not in a['name']],
                'transits': transit_aspects,
                'transit_pos': transit_planets
            }

    def _process_aspect_events(self):
        """Processes the daily aspect cache into a list of continuous aspect events.
        This version stores the full aspect data to avoid bugs from string splitting."""
        self.aspect_events = []
        if not self.timeline_aspects_cache: return
        num_days = self.months_to_display * 30

        for tier in ['lunar_prog', 'other_prog', 'transits']:
            active_aspects = {}  # { name: {'start': date, 'orb_readings': [], 'data': aspect_dict} }
            for i in range(num_days + 2):
                current_date = self.start_date + timedelta(days=i - 1)
                date_key = current_date.strftime('%Y-%m-%d')
                day_data = self.timeline_aspects_cache.get(date_key, {})
                todays_aspects = {a['name']: a for a in day_data.get(tier, [])}

                # Check for newly started or ongoing aspects
                for name, data in todays_aspects.items():
                    if name not in active_aspects:
                        active_aspects[name] = {
                            'start': current_date,
                            'orb_readings': [],
                            'data': data  # Store the whole aspect dictionary
                        }
                    active_aspects[name]['orb_readings'].append((current_date, data['orb']))

                # Check for newly ended aspects
                ended_names = set(active_aspects.keys()) - set(todays_aspects.keys())
                for name in ended_names:
                    event = active_aspects.pop(name)
                    if not event['orb_readings']: continue

                    exact_date = min(event['orb_readings'], key=lambda x: x[1])[0]

                    final_event = {
                        'name': name,
                        'start': event['start'],
                        'end': current_date,
                        'tier': tier,
                        'exact_date': exact_date,
                    }
                    # Add specific planet names if they exist in the original data
                    if 'p1' in event['data']:
                        final_event['p1'] = event['data']['p1']
                    if 'p2' in event['data']:
                        final_event['p2'] = event['data']['p2']

                    self.aspect_events.append(final_event)

    # --- Drawing ---

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        self.padding = 20
        self.content_width = self.width() - 2 * self.padding

        self._draw_month_header(painter)
        self._draw_tier_content(painter, 'lunar_prog', self.colors['lunar'], 120)
        self._draw_transit_grids(painter, 250)
        self._draw_tier_content(painter, 'other_prog', self.colors['solar'], 450)

    def _draw_month_header(self, painter):
        header_y, box_height = 40, 30

        # --- Draw Year Box ---
        year_box_width = 60
        year_rect = QRectF(self.padding, header_y, year_box_width, box_height)
        self._draw_glow_rect(painter, year_rect, self.colors['grid'])
        painter.setFont(self.fonts['year'])
        painter.setPen(self.colors['text'])
        painter.drawText(year_rect, Qt.AlignmentFlag.AlignCenter, str(self.start_date.year))

        # --- Draw Month Boxes ---
        # The number of boxes depends on the timescale, as per the user's sketch
        num_boxes = 5 # Default for 3 months
        if self.months_to_display == 6:
            num_boxes = 8
        elif self.months_to_display == 12:
            num_boxes = 14

        month_area_width = self.content_width - year_box_width - 10
        box_width = month_area_width / num_boxes
        current_x = self.padding + year_box_width + 10

        last_drawn_month = -1
        current_year = self.start_date.year

        for i in range(self.months_to_display):
            month_start_date = self.start_date + timedelta(days=i * 30)
            month_end_date = self.start_date + timedelta(days=(i + 1) * 30)

            start_x = self._date_to_x(month_start_date)
            end_x = self._date_to_x(month_end_date)

            month_rect = QRectF(start_x, header_y, end_x - start_x, box_height)

            # Draw the box for the month
            self._draw_glow_rect(painter, month_rect, self.colors['grid'])

            # Draw the month label inside the box
            label = month_start_date.strftime("%b").upper()
            if month_start_date.year != current_year:
                label = f"{label} {month_start_date.year}"
                current_year = month_start_date.year

            painter.setFont(self.fonts['month'])
            painter.setPen(self.colors['text'])
            painter.drawText(month_rect, Qt.AlignmentFlag.AlignCenter, label)

    def _draw_tier_content(self, painter, tier_name, color, y_pos):
        events = [e for e in self.aspect_events if e['tier'] == tier_name]
        for event in events:
            start_x = self._date_to_x(event['start'])
            end_x = self._date_to_x(event['end'])
            exact_x = self._date_to_x(event['exact_date'])

            self._draw_glow_line(painter, QPointF(start_x, y_pos), QPointF(end_x, y_pos), color)
            self._draw_glow_text(painter, QPointF(exact_x - 5, y_pos + 6), "*", self.fonts['star'], self.colors['star'])

            # Draw label for the aspect
            painter.setFont(self.fonts['grid'])
            painter.setPen(self.colors['text'])
            painter.drawText(QPointF(start_x, y_pos - 8), event['name'])

    def _draw_transit_grids(self, painter, y_start):
        transit_events = sorted([e for e in self.aspect_events if e['tier'] == 'transits'], key=lambda x: x['exact_date'])

        grid_width, grid_height = 160, 80
        y_offset = 0

        for event in transit_events:
            x_pos = self._date_to_x(event['exact_date']) - (grid_width / 2)
            y_pos = y_start + y_offset

            # Check for overlap and adjust y
            # This is a simple implementation, could be improved
            if x_pos < self.padding: x_pos = self.padding
            if x_pos + grid_width > self.width() - self.padding:
                x_pos = self.width() - self.padding - grid_width

            # Draw connecting line to timeline
            painter.setPen(QPen(self.colors['transit'], 1, Qt.PenStyle.DashLine))
            painter.drawLine(int(x_pos + grid_width / 2), y_pos, int(x_pos + grid_width / 2), y_pos - 20)

            self._draw_single_transit_grid(painter, QRectF(x_pos, y_pos, grid_width, grid_height), event)

            y_offset += grid_height + 20 # Stagger grids vertically
            if y_offset > 150: y_offset = 0 # Reset y-offset to avoid going too far down


    def _draw_single_transit_grid(self, painter, rect, event_data):
        painter.setPen(self.colors['grid'])
        painter.setBrush(self.colors['box_bg'])
        painter.drawRoundedRect(rect, 5, 5)

        # --- Defensive Checks ---
        date_key = event_data['exact_date'].strftime('%Y-%m-%d')
        if date_key not in self.timeline_aspects_cache:
            return # Don't draw if data is missing

        p1 = event_data.get('p1')
        p2 = event_data.get('p2')
        if not p1 or not p2:
            return # Don't draw if planet names are missing

        # --- Content ---
        painter.setFont(self.fonts['grid'])
        painter.setPen(self.colors['text'])

        # Line 1: Aspect Name
        painter.drawText(rect.adjusted(5, 5, -5, -5), Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft, event_data['name'])

        # Line 2: Natal House of Natal Planet
        natal_house = self._get_natal_house_for_planet(p2)
        painter.drawText(rect.adjusted(5, 20, -5, -5), Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft, f"Natal House: {natal_house}")

        # Line 3: Transiting House
        transit_pos = self.timeline_aspects_cache[date_key]['transit_pos'][p1][0]
        transiting_house = self._get_transiting_house(transit_pos)
        painter.drawText(rect.adjusted(5, 35, -5, -5), Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft, f"Transiting House: {transiting_house}")

        # Line 4: Ruled Houses
        ruled_houses = self._get_ruled_houses(p1)
        painter.drawText(rect.adjusted(5, 50, -5, -5), Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft, f"Rules Houses: {ruled_houses}")


    # --- Helpers & Utilities ---

    def _get_natal_house_for_planet(self, planet_name):
        if not self.natal_houses or planet_name not in self.natal_planets: return "N/A"
        planet_pos = self.natal_planets[planet_name][0]
        for i in range(11):
            if self.natal_houses[i] <= planet_pos < self.natal_houses[i+1]:
                return str(i + 1)
        if self.natal_houses[11] <= planet_pos < 360 or 0 <= planet_pos < self.natal_houses[0]:
            return "12"
        return "N/A"

    def _get_transiting_house(self, planet_pos):
        if not self.natal_houses: return "N/A"
        for i in range(11):
            if self.natal_houses[i] <= planet_pos < self.natal_houses[i+1]:
                return str(i + 1)
        if self.natal_houses[11] <= planet_pos < 360 or 0 <= planet_pos < self.natal_houses[0]:
            return "12"
        return "N/A"

    def _get_ruled_houses(self, planet_name):
        ruled_houses = []
        if not self.natal_houses: return "N/A"
        for i, cusp in enumerate(self.natal_houses):
            ruler = get_house_ruler(cusp)
            if ruler == planet_name:
                ruled_houses.append(str(i + 1))
        return ", ".join(ruled_houses) if ruled_houses else "None"

    def _date_to_x(self, date):
        total_days = self.months_to_display * 30
        days_from_start = (date - self.start_date).total_seconds() / (24 * 3600)
        proportion = days_from_start / total_days
        return self.padding + proportion * self.content_width

    def _draw_glow_line(self, painter, p1, p2, color):
        glow_color = QColor(color)
        glow_color.setAlpha(80)
        pen = QPen(glow_color, 5, Qt.PenStyle.SolidLine, cap=Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawLine(p1, p2)
        glow_color.setAlpha(150)
        pen.setColor(glow_color)
        pen.setWidth(3)
        painter.setPen(pen)
        painter.drawLine(p1, p2)
        pen.setColor(color)
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawLine(p1, p2)

    def _draw_glow_rect(self, painter, rect, color):
        """Draws a rectangle with a neon glow effect."""
        # Outer glow
        glow_color = QColor(color)
        glow_color.setAlpha(60)
        pen = QPen(glow_color, 5, Qt.PenStyle.SolidLine, cap=Qt.PenCapStyle.RoundCap, join=Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect, 5, 5)
        # Inner glow
        glow_color.setAlpha(120)
        pen.setColor(glow_color)
        pen.setWidth(3)
        painter.setPen(pen)
        painter.drawRoundedRect(rect, 5, 5)
        # Core line
        pen.setColor(color)
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawRoundedRect(rect, 5, 5)

    def mouseMoveEvent(self, event):
        """Handle hover events to show tooltips for aspect lines."""
        y_pos = event.position().y()
        tier_y_positions = {
            'lunar_prog': 120,
            'other_prog': 450,
        }
        hover_radius = 10

        for tier, y_val in tier_y_positions.items():
            if abs(y_pos - y_val) < hover_radius:
                aspects_in_tier = [e for e in self.aspect_events if e['tier'] == tier]
                for aspect_event in aspects_in_tier:
                    start_x = self._date_to_x(aspect_event['start'])
                    end_x = self._date_to_x(aspect_event['end'])

                    if start_x <= event.position().x() <= end_x:
                        tooltip_text = (
                            f"<b>{aspect_event['name']}</b><br>"
                            f"Exact: {aspect_event['exact_date'].strftime('%d %b %Y')}"
                        )
                        QToolTip.showText(event.globalPosition().toPoint(), tooltip_text, self)
                        return

        QToolTip.hideText() # Hide if not hovering over anything
        super().mouseMoveEvent(event)

    def _draw_glow_text(self, painter, point, text, font, color):
        painter.setFont(font)
        glow_color = QColor(color)
        glow_color.setAlpha(80)
        pen = QPen(glow_color, 5)
        painter.setPen(pen)
        painter.drawText(point, text)
        glow_color.setAlpha(150)
        pen.setWidth(3)
        painter.setPen(pen)
        painter.drawText(point, text)
        pen.setColor(color)
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawText(point, text)