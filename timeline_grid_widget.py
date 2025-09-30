from datetime import datetime, timedelta
from PyQt6.QtWidgets import QFrame, QToolTip
from PyQt6.QtGui import QFont, QColor, QPainter, QPen, QBrush, QPainterPath
from PyQt6.QtCore import Qt, QPointF, QRectF
from astro_engine import (
    calculate_secondary_progressions,
    calculate_aspects, find_cross_aspects,
    PLANETS, get_planet_position,
    get_ruled_houses_for_planet, get_zodiac_sign,
    format_longitude
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

            # Use an orb of 1.0 degree for all progressions, as requested
            prog_aspects = calculate_aspects(progressed_planets, 1.0)
            # Only include aspects from the 5 major outer planets for transits
            major_transits = {p: transit_planets[p] for p in ['Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto']}
            # Use an orb of 2.0 degrees for transits, as requested
            transit_aspects = find_cross_aspects(major_transits, self.natal_planets, 2.0)

            # Filter lunar progressions to only include aspects to other PROGRESSED planets
            lunar_prog_aspects = [
                a for a in prog_aspects if a['p1'] == 'Moon' and a['p2'] != 'Moon'
            ]

            # Filter other progressions to exclude any involving the Moon
            other_prog_aspects = [
                a for a in prog_aspects if 'Moon' not in (a['p1'], a['p2'])
            ]

            self.timeline_aspects_cache[date_key] = {
                'lunar_prog': lunar_prog_aspects,
                'other_prog': other_prog_aspects,
                'transits': transit_aspects,
                'transit_pos': transit_planets,
                'progressed_pos': progressed_planets
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
                        'orb_readings': event['orb_readings'], # Carry over for detailed drawing
                        'aspect': event['data']['aspect'] # Carry over for labeling
                    }
                    # Add specific planet names if they exist in the original data
                    if 'p1' in event['data']:
                        final_event['p1'] = event['data']['p1']
                    if 'p2' in event['data']:
                        final_event['p2'] = event['data']['p2']

                    self.aspect_events.append(final_event)

    # --- Layout & Drawing ---

    def _assign_layout_lanes(self, events, is_grid=False):
        """
        Assigns a vertical 'lane' to each event to prevent overlapping.
        :param events: A list of event dictionaries.
        :param is_grid: If True, uses a simpler check for grid boxes.
        :return: A list of the same events, with an added 'lane' key.
        """
        if not events:
            return []

        # Sort events by start time, crucial for the greedy algorithm
        sorted_events = sorted(events, key=lambda e: e['start'])

        lanes = [] # Each item in this list represents the last event in that lane

        for event in sorted_events:
            placed = False
            # Find the first lane where this event can fit
            for i, lane_end_event in enumerate(lanes):
                # Check for temporal overlap
                if event['start'] < lane_end_event['end']:
                    continue # This lane is occupied, try the next one

                # For grid items, we also need to check for horizontal overlap
                if is_grid:
                    grid_width = 160 # Should be a shared constant
                    event_x = self._date_to_x(event['exact_date'])
                    lane_event_x = self._date_to_x(lane_end_event['exact_date'])
                    if abs(event_x - lane_event_x) < grid_width:
                        continue # Horizontally too close, try next lane

                lanes[i] = event
                event['lane'] = i
                placed = True
                break

            if not placed:
                event['lane'] = len(lanes)
                lanes.append(event)

        return sorted_events

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        self.padding = 20
        self.content_width = self.width() - 2 * self.padding

        self._draw_month_header(painter)

        # Define drawing areas based on the new layout
        lunar_y_start = 110
        other_prog_y_start = self.height() - 150
        transit_y_start = 200

        # Draw the tiers in their new positions
        self._draw_progression_tier(painter, 'lunar_prog', self.colors['lunar'], lunar_y_start)
        self._draw_transit_tier(painter, transit_y_start)
        self._draw_progression_tier(painter, 'other_prog', self.colors['solar'], other_prog_y_start)

    def _draw_month_header(self, painter):
        header_y, box_height = 40, 30
        year_box_width = 60
        year_rect = QRectF(self.padding, header_y, year_box_width, box_height)
        self._draw_glow_rect(painter, year_rect, self.colors['grid'])
        painter.setFont(self.fonts['year'])
        painter.setPen(self.colors['text'])
        painter.drawText(year_rect, Qt.AlignmentFlag.AlignCenter, str(self.start_date.year))

        current_year = self.start_date.year
        for i in range(self.months_to_display):
            month_start_date = self.start_date + timedelta(days=i * 30)
            month_end_date = self.start_date + timedelta(days=(i + 1) * 30)
            start_x = self._date_to_x(month_start_date)
            end_x = self._date_to_x(month_end_date)
            month_rect = QRectF(start_x, header_y, end_x - start_x, box_height)
            self._draw_glow_rect(painter, month_rect, self.colors['grid'])

            label = month_start_date.strftime("%b").upper()
            if month_start_date.year != current_year:
                label = f"{label} {month_start_date.year}"
                current_year = month_start_date.year

            painter.setFont(self.fonts['month'])
            painter.setPen(self.colors['text'])
            painter.drawText(month_rect, Qt.AlignmentFlag.AlignCenter, label)

    def _draw_progression_tier(self, painter, tier_name, color, y_start):
        events = [e for e in self.aspect_events if e['tier'] == tier_name]
        laid_out_events = self._assign_layout_lanes(events)

        lane_height = 25 # Vertical distance between lines

        for event in laid_out_events:
            y_pos = y_start + event['lane'] * lane_height
            start_x = self._date_to_x(event['start'])
            end_x = self._date_to_x(event['end'])
            exact_x = self._date_to_x(event['exact_date'])

            # Draw the main aspect line
            self._draw_glow_line(painter, QPointF(start_x, y_pos), QPointF(end_x, y_pos), color)

            # Draw the "firework" for the exact aspect
            self._draw_glow_text(painter, QPointF(exact_x - 5, y_pos + 6), "*", self.fonts['star'], self.colors['star'])

            # Draw arrow indicators for near-exact orbs
            for date, orb in event['orb_readings']:
                # 12 arcminutes = 0.2 degrees
                if orb < 0.2:
                    arrow_x = self._date_to_x(date)
                    self._draw_arrow_indicator(painter, QPointF(arrow_x, y_pos), color)

            # Draw label: "P. Planet1 Aspect P. Planet2"
            label = f"P. {event['p1']} {event['aspect']} P. {event['p2']}"
            painter.setFont(self.fonts['grid'])
            painter.setPen(self.colors['text'])
            painter.drawText(QPointF(start_x + 5, y_pos - 8), label)

    def _draw_transit_tier(self, painter, y_start):
        transit_events = [e for e in self.aspect_events if e['tier'] == 'transits']
        laid_out_events = self._assign_layout_lanes(transit_events, is_grid=True)

        grid_width, grid_height = 170, 85
        lane_height = grid_height + 15

        for event in laid_out_events:
            x_pos = self._date_to_x(event['exact_date']) - (grid_width / 2)
            y_pos = y_start + event['lane'] * lane_height

            # Clamp grid position to be within view
            if x_pos < self.padding: x_pos = self.padding
            if x_pos + grid_width > self.width() - self.padding:
                x_pos = self.width() - self.padding - grid_width

            # Draw connecting line to month header
            painter.setPen(QPen(self.colors['transit'], 1, Qt.PenStyle.DashLine))
            painter.drawLine(int(x_pos + grid_width / 2), y_pos, int(x_pos + grid_width / 2), 75)

            self._draw_single_transit_grid(painter, QRectF(x_pos, y_pos, grid_width, grid_height), event)

    def _draw_single_transit_grid(self, painter, rect, event_data):
        painter.setPen(self.colors['grid'])
        painter.setBrush(self.colors['box_bg'])
        painter.drawRoundedRect(rect, 5, 5)

        p1 = event_data.get('p1') # Transiting planet
        p2 = event_data.get('p2') # Natal planet
        if not p1 or not p2 or p2 not in self.natal_planets: return

        painter.setFont(self.fonts['grid'])
        painter.setPen(self.colors['text'])

        # Line 1: Aspect Name (e.g., Jupiter Opposition Sun)
        painter.drawText(rect.adjusted(5, 5, -5, -5), Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft, event_data['name'])

        # Line 2: Natal Planet Position
        natal_planet_pos_str = format_longitude(self.natal_planets[p2][0])
        painter.drawText(rect.adjusted(5, 22, -5, -5), Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft, f"Natal {p2}: {natal_planet_pos_str}")

        # Line 3: Natal House of Planet
        natal_house = self._get_natal_house_for_planet(p2)
        painter.drawText(rect.adjusted(5, 39, -5, -5), Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft, f"Natal House: {natal_house}")

        # Line 4: Houses Ruled by Natal Planet
        ruled_houses = get_ruled_houses_for_planet(p2, self.natal_houses)
        ruled_houses_str = ", ".join(ruled_houses) if ruled_houses else "None"
        painter.drawText(rect.adjusted(5, 56, -5, -5), Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft, f"Rules Houses: {ruled_houses_str}")

    # --- Helpers & Utilities ---

    def _get_natal_house_for_planet(self, planet_name):
        if not self.natal_houses or planet_name not in self.natal_planets: return "N/A"
        planet_pos = self.natal_planets[planet_name][0]
        for i in range(11):
            if self.natal_houses[i] <= planet_pos < self.natal_houses[i+1]: return str(i + 1)
        if self.natal_houses[11] <= planet_pos < 360 or 0 <= planet_pos < self.natal_houses[0]: return "12"
        return "N/A"

    def _date_to_x(self, date):
        total_days = self.months_to_display * 30
        if total_days == 0: return self.padding
        days_from_start = (date - self.start_date).total_seconds() / (24 * 3600)
        proportion = days_from_start / total_days
        return self.padding + proportion * self.content_width

    def _draw_arrow_indicator(self, painter, point, color):
        painter.setPen(QPen(color, 1))
        painter.setBrush(QBrush(color))
        arrow = QPainterPath()
        arrow.moveTo(point.x(), point.y() - 5)
        arrow.lineTo(point.x() - 3, point.y() - 9)
        arrow.lineTo(point.x() + 3, point.y() - 9)
        arrow.closeSubpath()
        painter.drawPath(arrow)

    def _draw_glow_line(self, painter, p1, p2, color):
        # Simplified for clarity, focusing on a single, clear line
        pen = QPen(color, 1.5, Qt.PenStyle.SolidLine, cap=Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawLine(p1, p2)

    def _draw_glow_rect(self, painter, rect, color):
        painter.setPen(QPen(color, 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect, 5, 5)

    def _draw_glow_text(self, painter, point, text, font, color):
        painter.setFont(font)
        painter.setPen(QPen(color))
        painter.drawText(point, text)

    def mouseMoveEvent(self, event):
        # This needs to be updated to work with the new dynamic Y positions
        # For now, disabling it to prevent incorrect tooltips.
        QToolTip.hideText()
        super().mouseMoveEvent(event)