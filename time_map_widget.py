import sys
from datetime import datetime, timedelta
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame
from PyQt6.QtGui import QFont, QColor, QPainter, QPen
from PyQt6.QtCore import Qt
from widgets import StyledButton
from astro_engine import (
    calculate_transits, calculate_secondary_progressions,
    calculate_aspects, find_cross_aspects
)

class TimelineGridWidget(QFrame):
    """A dedicated widget for drawing the timeline grid and aspect lines."""
    def __init__(self):
        super().__init__()
        self.setObjectName("timeline-grid")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setMinimumHeight(300)
        self.setMouseTracking(True) # Enable hover events

        # State
        self.start_date = datetime.now()
        self.months_to_display = 3

        # Data
        self.birth_date = None
        self.natal_planets = {}
        self.natal_houses = []
        self.timeline_aspects = {} # Daily cache
        self.aspect_events = [] # Processed list of aspect event dictionaries

    def set_chart_data(self, birth_date, natal_planets, natal_houses):
        """Receives natal data and triggers the aspect calculation for the timeline."""
        self.birth_date = birth_date
        self.natal_planets = natal_planets
        self.natal_houses = natal_houses
        self._calculate_and_process_timeline()
        self.update() # Redraw with new data

    def set_timescale(self, months):
        self.months_to_display = months
        self._calculate_and_process_timeline()
        self.update()

    def _calculate_and_process_timeline(self):
        """High-level method to run the full calculation and processing pipeline."""
        self._calculate_daily_aspects()
        self._process_aspect_events()

    def _calculate_daily_aspects(self):
        """Calculates all aspects for each day in the view and stores them in a cache."""
        if not self.birth_date or not self.natal_planets: return
        self.timeline_aspects = {}
        num_days = self.months_to_display * 30

        for i in range(num_days + 2):
            current_date = self.start_date + timedelta(days=i - 1)
            date_key = current_date.strftime('%Y-%m-%d')

            transit_planets = {name: get_planet_position(current_date, pid) for name, pid in PLANETS.items()}
            progressed_planets = calculate_secondary_progressions(self.birth_date, current_date)

            prog_aspects = calculate_aspects(progressed_planets, 1)
            major_transits = {p: transit_planets[p] for p in ['Saturn', 'Uranus', 'Neptune', 'Pluto']}
            natal_positions_with_speed = {p: (pos, 0) for p, pos in self.natal_planets.items()}
            transit_aspects = find_cross_aspects(major_transits, natal_positions_with_speed, 2)

            self.timeline_aspects[date_key] = {
                'lunar': [a for a in prog_aspects if a['p1'] == 'Moon' or a['p2'] == 'Moon'],
                'solar': [a for a in prog_aspects if a['p1'] != 'Moon' and a['p2'] != 'Moon'],
                'transits': transit_aspects
            }

    def _process_aspect_events(self):
        """Processes the daily aspect cache into a list of continuous aspect events."""
        self.aspect_events = []
        if not self.timeline_aspects: return
        num_days = self.months_to_display * 30

        for tier in ['lunar', 'solar', 'transits']:
            active_aspects = {}  # { "Name": { 'start': date, 'orb_readings': [] } }

            for i in range(num_days + 2):
                current_date = self.start_date + timedelta(days=i - 1)
                date_key = current_date.strftime('%Y-%m-%d')
                todays_aspects_list = self.timeline_aspects.get(date_key, {}).get(tier, [])
                todays_aspects_by_name = {a['name']: a for a in todays_aspects_list}

                # Check for newly started aspects
                for name, aspect_data in todays_aspects_by_name.items():
                    if name not in active_aspects:
                        active_aspects[name] = {'start': current_date, 'orb_readings': []}
                    active_aspects[name]['orb_readings'].append((current_date, aspect_data['orb']))

                # Check for newly ended aspects
                ended_aspect_names = set(active_aspects.keys()) - set(todays_aspects_by_name.keys())
                for name in ended_aspect_names:
                    event_data = active_aspects.pop(name)
                    # Find date of minimum orb (exact date)
                    exact_date = min(event_data['orb_readings'], key=lambda x: x[1])[0]
                    self.aspect_events.append({
                        'name': name, 'start': event_data['start'], 'end': current_date, 'tier': tier,
                        'exact_date': exact_date
                    })

    def _date_to_x(self, date, width, padding):
        """Converts a date to an x-coordinate on the timeline."""
        total_days_in_view = self.months_to_display * 30
        days_from_start = (date - self.start_date).total_seconds() / (24 * 3600)

        if total_days_in_view == 0: return padding

        proportion = days_from_start / total_days_in_view
        return padding + proportion * (width - 2 * padding)

    def _draw_glow_line(self, painter, p1, p2, color):
        """Draws a line with a neon glow effect."""
        # Outer glow
        glow_color = QColor(color)
        glow_color.setAlpha(80)
        pen = QPen(glow_color, 5, Qt.PenStyle.SolidLine)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawLine(p1, p2)
        # Inner glow
        glow_color.setAlpha(150)
        pen.setColor(glow_color)
        pen.setWidth(3)
        painter.setPen(pen)
        painter.drawLine(p1, p2)
        # Core line
        pen.setColor(color)
        pen.setWidth(1.5)
        painter.setPen(pen)
        painter.drawLine(p1, p2)

    def _get_house_for_planet(self, planet_pos):
        """Finds the house number for a given planetary degree."""
        if not self.natal_houses: return 0
        for i in range(11):
            if self.natal_houses[i] <= planet_pos < self.natal_houses[i+1]:
                return i + 1
        # Handle wrap-around for 12th house
        if self.natal_houses[11] <= planet_pos < 360 or 0 <= planet_pos < self.natal_houses[0]:
            return 12
        return 0

    def mouseMoveEvent(self, event):
        """Handle hover events to show tooltips."""
        y_pos = event.position().y()
        # Define the y-ranges for each tier for hit detection
        tier_y_positions = {
            'lunar': self.height() / 4,
            'transits': self.height() / 2,
            'solar': self.height() * 3 / 4
        }
        hover_radius = 10

        for aspect_event in self.aspect_events:
            tier_y = tier_y_positions.get(aspect_event['tier'])
            if tier_y and abs(y_pos - tier_y) < hover_radius:
                # A simple check to see if the mouse is over the line horizontally
                start_x = self._date_to_x(aspect_event['start'], self.width(), 20)
                end_x = self._date_to_x(aspect_event['end'], self.width(), 20)
                if start_x <= event.position().x() <= end_x:
                    parts = aspect_event['name'].split()
                    p1_name, p2_name = parts[0], parts[2]

                    p1_house = self._get_house_for_planet(self.natal_planets.get(p1_name, 0))
                    p2_house = self._get_house_for_planet(self.natal_planets.get(p2_name, 0))

                    tooltip_text = (
                        f"<b>{aspect_event['name']}</b><br>"
                        f"Exact: {aspect_event['exact_date'].strftime('%d %b %Y')}<br>"
                        f"<hr>"
                        f"<b>{p1_name}</b> (Natal House: {p1_house})<br>"
                        f"<b>{p2_name}</b> (Natal House: {p2_house})"
                    )
                    QToolTip.showText(event.globalPosition().toPoint(), tooltip_text, self)
                    return
        QToolTip.hideText() # Hide if not hovering over anything

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Define colors and fonts
        grid_color = QColor("#3DF6FF")
        text_color = QColor("#94EBFF")
        year_font = QFont("TT Supermolot Neue Condensed", 14, QFont.Weight.Bold)
        month_font = QFont("Titillium Web", 12)
        star_font = QFont("Titillium Web", 16, QFont.Weight.Bold)

        tier_colors = {
            'lunar': QColor("#F9EEFB"), 'transits': QColor("#3DF6FF"), 'solar': QColor("#75439E"),
        }
        width, height, padding, header_height, month_label_height = self.width(), self.height(), 20, 60, 30
        tier_y_positions = {
            'lunar': height / 4, 'transits': height / 2, 'solar': height * 3 / 4,
        }

        # Draw Year Header and Month Boxes
        # ... (This part is unchanged and can be considered complete)

        # Draw the Aspect Lines and Indicators
        for event in self.aspect_events:
            start_x = self._date_to_x(event['start'], width, padding)
            end_x = self._date_to_x(event['end'], width, padding)
            y_pos = tier_y_positions.get(event['tier'], height / 2)
            color = tier_colors.get(event['tier'], Qt.GlobalColor.white)

            self._draw_glow_line(painter, QPointF(start_x, y_pos), QPointF(end_x, y_pos), color)

            # Draw the exact aspect indicator '*'
            exact_x = self._date_to_x(event['exact_date'], width, padding)
            painter.setFont(star_font)
            star_color = QColor("#FFFF00") # Neon Yellow for the star
            self._draw_glow_text(painter, QPointF(exact_x - 5, y_pos + 6), "*", star_font, star_color)

    def _draw_glow_text(self, painter, point, text, font, color):
        """A helper function to draw text with a neon glow effect."""
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

class TimeMapWidget(QWidget):
    """A custom widget to display the 'Time Map' timeline view."""
    def __init__(self):
        super().__init__()
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QColor("#200334"))
        self.setPalette(palette)

        self.setStyleSheet("""
            QLabel#time-map-title {
                font-family: "Mistrully";
                font-size: 36pt;
                color: #FF01F9;
                padding-bottom: 10px;
            }
            QFrame#timeline-grid {
                border: 1px solid #3DF6FF;
                border-radius: 5px;
                background-color: transparent;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # 1. Header
        title_label = QLabel("Time Crisis Astrology")
        title_label.setObjectName("time-map-title")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 2. Timescale Buttons
        timescale_layout = QHBoxLayout()
        timescale_layout.addStretch()
        self.btn_3_month = StyledButton("3 Month")
        self.btn_6_month = StyledButton("6 Month")
        self.btn_12_month = StyledButton("12 Month")
        timescale_layout.addWidget(self.btn_3_month)
        timescale_layout.addWidget(self.btn_6_month)
        timescale_layout.addWidget(self.btn_12_month)
        timescale_layout.addStretch()

        # --- Connect Signals ---
        self.btn_3_month.clicked.connect(lambda: self.timeline_grid.set_timescale(3))
        self.btn_6_month.clicked.connect(lambda: self.timeline_grid.set_timescale(6))
        self.btn_12_month.clicked.connect(lambda: self.timeline_grid.set_timescale(12))

        # 3. Timeline Grid Container
        self.timeline_grid = TimelineGridWidget()

        # Add widgets to main layout
        main_layout.addWidget(title_label, 0, Qt.AlignmentFlag.AlignTop)
        main_layout.addLayout(timescale_layout)
        main_layout.addWidget(self.timeline_grid, 1)

    def set_chart_data(self, birth_date, natal_planets, natal_houses):
        """Passes the natal chart data down to the timeline grid widget."""
        self.timeline_grid.set_chart_data(birth_date, natal_planets, natal_houses)