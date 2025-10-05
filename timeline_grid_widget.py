from datetime import datetime, timedelta
from PyQt6.QtWidgets import QFrame, QToolTip
from PyQt6.QtGui import (QFont, QFontMetrics, QColor, QPainter, QPen, QBrush,
                         QPainterPath)
from PyQt6.QtCore import Qt, QPointF, QRectF
from astro_engine import (
    calculate_secondary_progressions,
    calculate_aspects, find_cross_aspects,
    PLANETS, get_planet_position,
    get_ruled_houses_for_planet, get_zodiac_sign,
    format_longitude
)

# --- Glyph Map for Astrological Symbols ---
# This maps the names used in the engine to the correct Unicode characters
# in the "EnigmaAstrology2.ttf" font.
GLYPH_MAP = {
    # Planets
    'Sun': '\uE50A', 'Moon': '\uE50B', 'Mercury': '\uE50C', 'Venus': '\uE50D',
    'Mars': '\uE50E', 'Jupiter': '\uE50F', 'Saturn': '\uE510', 'Uranus': '\uE511',
    'Neptune': '\uE512', 'Pluto': '\uE513', 'Chiron': '\uE515', 'Lilith': '\uE51A',
    'N. Node': '\uE518',
    # Aspects
    'Conjunction': '\uE520', 'Sextile': '\uE523', 'Square': '\uE524',
    'Trine': '\uE525', 'Opposition': '\uE526',
    # Special Characters for Progressions
    '(P)': '\uE530',  # Using a custom character for 'Progressed'
}

class TimelineGridWidget(QFrame):
    """A dedicated widget for drawing the timeline grid and aspect events."""
    def __init__(self, astro_font=None):
        super().__init__()
        self.setObjectName("timeline-grid")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setMinimumHeight(600)
        self.setMouseTracking(True)

        # State & Data
        self.start_date = None
        self.months_to_display = 0
        self.birth_date = None
        self.natal_planets = {}
        self.natal_houses = []
        self.aspect_events = []
        self.timeline_aspects_cache = {}

        # Theming & Fonts
        self.astro_font = astro_font or QFont("Arial", 14) # Fallback font
        self.colors = {
            'grid': QColor("#3DF6FF"),
            'text': QColor("#94EBFF"),
            'lunar': QColor("#00BFFF"),
            'solar': QColor("#FF9933"),
            'transit': QColor("#3DF6FF"),
            'star': QColor("#FFFF00"),
            'box_bg': QColor(255, 1, 249, 20),
        }
        self.fonts = {
            'year': QFont("TT Supermolot Neue Condensed", 14, QFont.Weight.Bold),
            'month': QFont("Titillium Web", 12),
            'grid': QFont("Titillium Web", 9),
            'star': QFont("Titillium Web", 16, QFont.Weight.Bold),
            'glyph': self.astro_font,
        }

    def set_chart_data(self, birth_date, natal_planets, natal_houses):
        self.birth_date = birth_date
        self.natal_planets = natal_planets
        self.natal_houses = natal_houses

    def set_view(self, start_date, months):
        self.start_date = start_date
        self.months_to_display = months
        self._calculate_and_process_timeline()
        self.update()

    def _calculate_and_process_timeline(self):
        if not self.start_date or not self.birth_date:
            return
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

            prog_aspects = calculate_aspects(progressed_planets, 1.0)
            major_transits = {p: transit_planets[p] for p in ['Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto']}
            transit_aspects = find_cross_aspects(major_transits, self.natal_planets, 2.0)

            lunar_prog_aspects = [a for a in prog_aspects if a['p1'] == 'Moon' and a['p2'] != 'Moon']
            other_prog_aspects = [a for a in prog_aspects if 'Moon' not in (a['p1'], a['p2'])]

            self.timeline_aspects_cache[date_key] = {
                'lunar_prog': lunar_prog_aspects,
                'other_prog': other_prog_aspects,
                'transits': transit_aspects,
                'transit_pos': transit_planets,
                'progressed_pos': progressed_planets
            }

    def _process_aspect_events(self):
        self.aspect_events = []
        if not self.timeline_aspects_cache: return
        num_days = self.months_to_display * 30

        raw_events = []
        for tier in ['lunar_prog', 'other_prog', 'transits']:
            active_aspects = {}
            for i in range(num_days + 2):
                current_date = self.start_date + timedelta(days=i - 1)
                date_key = current_date.strftime('%Y-%m-%d')
                day_data = self.timeline_aspects_cache.get(date_key, {})
                todays_aspects = {a['name']: a for a in day_data.get(tier, [])}

                for name, data in todays_aspects.items():
                    if name not in active_aspects:
                        active_aspects[name] = {'start': current_date, 'orb_readings': [], 'data': data}
                    if tier == 'transits':
                        p1_pos = day_data['transit_pos'][data['p1']][0]
                        active_aspects[name]['orb_readings'].append((current_date, data['orb'], p1_pos))
                    else:
                        active_aspects[name]['orb_readings'].append((current_date, data['orb']))

                ended_names = set(active_aspects.keys()) - set(todays_aspects.keys())
                for name in ended_names:
                    event = active_aspects.pop(name)
                    if not event['orb_readings']: continue
                    exact_reading = min(event['orb_readings'], key=lambda x: x[1])
                    final_event = {
                        'name': name, 'start': event['start'], 'end': current_date, 'tier': tier,
                        'exact_date': exact_reading[0], 'orb_readings': event['orb_readings'],
                        'aspect': event['data']['aspect'], 'p1': event['data'].get('p1'), 'p2': event['data'].get('p2')
                    }
                    if tier == 'transits' and len(exact_reading) > 2:
                        final_event['p1_pos_at_exact_pass'] = exact_reading[2]
                    raw_events.append(final_event)

        prog_events = [e for e in raw_events if e['tier'] != 'transits']
        transit_events = [e for e in raw_events if e['tier'] == 'transits']

        merged_transits = {}
        for event in transit_events:
            name = event['name']
            if name not in merged_transits:
                merged_transits[name] = event
                merged_transits[name]['exact_dates'] = [event['exact_date']]
            else:
                existing = merged_transits[name]
                existing['start'] = min(existing['start'], event['start'])
                existing['end'] = max(existing['end'], event['end'])
                existing['exact_dates'].append(event['exact_date'])
                existing['orb_readings'].extend(event['orb_readings'])

        final_transit_events = []
        for name, event in merged_transits.items():
            if not event['orb_readings']: continue
            most_exact_reading = min(event['orb_readings'], key=lambda x: x[1])
            event['exact_date'] = most_exact_reading[0]
            if len(most_exact_reading) > 2:
                event['p1_pos_at_exact'] = most_exact_reading[2]
            event['exact_dates'].sort()
            final_transit_events.append(event)

        self.aspect_events = prog_events + final_transit_events

    def _get_glyph_label(self, p1, aspect, p2, is_transit=False):
        """Constructs the glyph string for an event."""
        p1_glyph = GLYPH_MAP.get(p1, '?')
        aspect_glyph = GLYPH_MAP.get(aspect, '?')
        p2_glyph = GLYPH_MAP.get(p2, '?')
        p_glyph = GLYPH_MAP.get('(P)', 'P')

        if is_transit:
            # Transit: T. Planet Aspect N. Planet
            return f"{p1_glyph} {aspect_glyph} {p2_glyph}"
        else:
            # Progression: P. Planet (P) Aspect P. Planet (P)
            return f"{p1_glyph}{p_glyph} {aspect_glyph} {p2_glyph}{p_glyph}"

    def _perform_layout(self, events, metrics, y_start, lane_height, is_grid=False):
        """
        A more advanced layout algorithm to prevent overlaps.
        Assigns a 'lane' and a final 'y_pos' to each event.
        """
        if not events:
            return []

        sorted_events = sorted(events, key=lambda e: e['start'])
        lanes = []  # Stores the end time of the last event in each lane

        for event in sorted_events:
            event_start_x = self._date_to_x(event['start'])
            event_end_x = self._date_to_x(event['end'])

            if is_grid:
                # For grid boxes, the "width" is fixed and centered on the exact date
                grid_width = 170
                event_start_x = self._date_to_x(event['exact_date']) - (grid_width / 2)
                event_end_x = event_start_x + grid_width
            else:
                # For progression lines, we also need to account for the label width
                label = self._get_glyph_label(event['p1'], event['aspect'], event['p2'])
                label_width = metrics.horizontalAdvance(label) + 15 # Add padding
                event_start_x -= label_width

            placed = False
            for i, lane_end_x in enumerate(lanes):
                if event_start_x >= lane_end_x:
                    lanes[i] = event_end_x
                    event['lane'] = i
                    placed = True
                    break

            if not placed:
                event['lane'] = len(lanes)
                lanes.append(event_end_x)

        # Assign y_pos based on the calculated lane
        for event in sorted_events:
            event['y_pos'] = y_start + event['lane'] * lane_height

        return sorted_events

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        self.padding = 20
        self.content_width = self.width() - 2 * self.padding

        self._draw_month_header(painter)

        # Define vertical layout parameters
        lunar_y_start = 110
        transit_y_start = 250
        other_prog_y_start = self.height() - 250

        # Perform layout and draw each tier
        self._layout_and_draw_progression_tier(painter, 'lunar_prog', self.colors['lunar'], lunar_y_start)
        self._layout_and_draw_transit_tier(painter, transit_y_start)
        self._layout_and_draw_progression_tier(painter, 'other_prog', self.colors['solar'], other_prog_y_start)

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

    def _layout_and_draw_progression_tier(self, painter, tier_name, color, y_start):
        events = [e for e in self.aspect_events if e['tier'] == tier_name]

        # Use QFontMetrics with the glyph font to measure labels accurately
        metrics = QFontMetrics(self.fonts['glyph'])
        lane_height = metrics.height() + 15  # Dynamic lane height based on font size + padding

        laid_out_events = self._perform_layout(events, metrics, y_start, lane_height)

        for event in laid_out_events:
            y_pos = event['y_pos']
            start_x = self._date_to_x(event['start'])
            end_x = self._date_to_x(event['end'])

            # Draw the main aspect line
            pen = QPen(color, 1.5, Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.drawLine(QPointF(start_x, y_pos), QPointF(end_x, y_pos))

            # Draw start and end ticks
            painter.drawLine(QPointF(start_x, y_pos - 3), QPointF(start_x, y_pos + 3))
            painter.drawLine(QPointF(end_x, y_pos - 3), QPointF(end_x, y_pos + 3))

            # Draw the "firework" for the exact aspect
            exact_x = self._date_to_x(event['exact_date'])
            self._draw_glow_text(painter, QPointF(exact_x - 4, y_pos + 5), "*", self.fonts['star'], self.colors['star'])

            # Draw the new glyph-based label
            label = self._get_glyph_label(event['p1'], event['aspect'], event['p2'])
            label_width = metrics.horizontalAdvance(label)
            label_x = start_x - label_width - 10 # Position left of the line start
            label_y = y_pos + (metrics.ascent() / 2) - 3 # Vertically center on the line

            painter.setFont(self.fonts['glyph'])
            painter.setPen(self.colors['text'])
            painter.drawText(QPointF(label_x, label_y), label)

    def _layout_and_draw_transit_tier(self, painter, y_start):
        events = [e for e in self.aspect_events if e['tier'] == 'transits']

        metrics = QFontMetrics(self.fonts['grid']) # Not used for layout here, but for drawing
        grid_height = 85
        lane_height = grid_height + 20 # Spacing between boxes

        laid_out_events = self._perform_layout(events, metrics, y_start, lane_height, is_grid=True)

        for event in laid_out_events:
            grid_width = 170
            x_pos = self._date_to_x(event['exact_date']) - (grid_width / 2)
            y_pos = event['y_pos']

            # Clamp grid position to be within view
            if x_pos < self.padding: x_pos = self.padding
            if x_pos + grid_width > self.width() - self.padding:
                x_pos = self.width() - self.padding - grid_width

            self._draw_single_transit_grid(painter, QRectF(x_pos, y_pos, grid_width, grid_height), event)

    def _draw_single_transit_grid(self, painter, rect, event_data):
        painter.setPen(self.colors['grid'])
        painter.setBrush(self.colors['box_bg'])
        painter.drawRoundedRect(rect, 5, 5)

        p1 = event_data.get('p1') # Transiting planet
        p2 = event_data.get('p2') # Natal planet
        if not p1 or not p2 or p2 not in self.natal_planets: return

        # Draw connecting arrow and date labels
        grid_center_x = rect.center().x()
        arrow_start_y = rect.top()
        arrow_end_y = arrow_start_y - 10
        painter.setPen(QPen(self.colors['transit'], 1))
        painter.drawLine(QPointF(grid_center_x, arrow_start_y), QPointF(grid_center_x, arrow_end_y))
        painter.drawLine(QPointF(grid_center_x, arrow_end_y), QPointF(grid_center_x - 3, arrow_end_y + 5))
        painter.drawLine(QPointF(grid_center_x, arrow_end_y), QPointF(grid_center_x + 3, arrow_end_y + 5))

        date_labels = sorted(list(set([d.strftime('%b %d') for d in event_data['exact_dates']])))
        date_str = ", ".join(date_labels)
        painter.setFont(self.fonts['grid'])
        painter.setPen(self.colors['text'])
        painter.drawText(QPointF(grid_center_x + 5, arrow_end_y - 2), date_str)


        # --- Draw Grid Content ---
        painter.setFont(self.fonts['glyph'])
        painter.setPen(self.colors['text'])

        # Line 1: Glyph-based aspect name
        glyph_label = self._get_glyph_label(p1, event_data['aspect'], p2, is_transit=True)
        painter.drawText(rect.adjusted(8, 5, -5, -5), Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft, glyph_label)

        # Subsequent lines use regular font
        painter.setFont(self.fonts['grid'])

        # Line 2: Natal Planet Position
        natal_pos_str = format_longitude(self.natal_planets[p2][0])
        natal_house = self._get_natal_house_for_planet(p2)
        painter.drawText(rect.adjusted(8, 25, -5, -5), Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft, f"Natal: {natal_pos_str} (H{natal_house})")

        # Line 3: Transiting Planet Info
        transiting_pos_at_exact = event_data.get('p1_pos_at_exact')
        if transiting_pos_at_exact is not None:
            transiting_pos_str = format_longitude(transiting_pos_at_exact)
            transiting_house = self._get_house_for_position(transiting_pos_at_exact)
            painter.drawText(rect.adjusted(8, 42, -5, -5), Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft, f"In House: {transiting_house}")

        # Line 4: Ruled Houses
        ruled_p1 = get_ruled_houses_for_planet(p1, self.natal_houses)
        ruled_p2 = get_ruled_houses_for_planet(p2, self.natal_houses)
        ruled_p1_str = f"{p1}: " + (",".join(ruled_p1) if ruled_p1 else "None")
        ruled_p2_str = f"{p2}: " + (",".join(ruled_p2) if ruled_p2 else "None")
        painter.drawText(rect.adjusted(8, 59, -5, -5), Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft, f"Rules: {ruled_p1_str} | {ruled_p2_str}")

    # --- Helpers & Utilities ---

    def _get_house_for_position(self, position):
        if not self.natal_houses or position is None: return "N/A"
        for i in range(11):
            if self.natal_houses[i] <= position < self.natal_houses[i+1]:
                return str(i + 1)
        if self.natal_houses[11] <= position < 360 or 0 <= position < self.natal_houses[0]:
            return "12"
        return "N/A"

    def _get_natal_house_for_planet(self, planet_name):
        if not self.natal_houses or planet_name not in self.natal_planets: return "N/A"
        planet_pos = self.natal_planets[planet_name][0]
        return self._get_house_for_position(planet_pos)

    def _date_to_x(self, date):
        if not self.start_date or self.months_to_display == 0:
            return self.padding
        total_days = self.months_to_display * 30
        days_from_start = (date - self.start_date).total_seconds() / (24 * 3600)
        proportion = days_from_start / total_days
        return self.padding + proportion * self.content_width

    def _draw_glow_rect(self, painter, rect, color):
        painter.setPen(QPen(color, 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect, 5, 5)

    def _draw_glow_text(self, painter, point, text, font, color):
        painter.setFont(font)
        painter.setPen(QPen(color))
        painter.drawText(point, text)

    def mouseMoveEvent(self, event):
        # Tooltip logic would need to be updated to work with the new layout.
        # Disabling for now.
        QToolTip.hideText()
        super().mouseMoveEvent(event)