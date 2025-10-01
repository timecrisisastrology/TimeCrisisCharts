import swisseph as swe
from datetime import datetime, timezone, timedelta

# --- Centralized list of planets for consistency ---
PLANETS = {
    'Sun': swe.SUN, 'Moon': swe.MOON, 'Mercury': swe.MERCURY, 'Venus': swe.VENUS, 'Mars': swe.MARS,
    'Jupiter': swe.JUPITER, 'Saturn': swe.SATURN, 'Uranus': swe.URANUS, 'Neptune': swe.NEPTUNE, 'Pluto': swe.PLUTO
}

def get_planet_position(calculation_date, planet_id):
    """Calculates the longitude and speed of a single planet for a given UTC datetime."""
    julian_day_utc = swe.utc_to_jd(calculation_date.year, calculation_date.month, calculation_date.day, calculation_date.hour, calculation_date.minute, calculation_date.second, 1)[1]
    planet_position_data = swe.calc_ut(julian_day_utc, planet_id, swe.FLG_SWIEPH | swe.FLG_SPEED)
    longitude = planet_position_data[0][0]
    speed = planet_position_data[0][3]
    return longitude, speed

def calculate_natal_chart(birth_date, latitude, longitude, house_system=b'P'):
    """Calculates the natal chart (planets and houses) for a given time and location."""
    chart_planets = {}
    for name, planet_id in PLANETS.items():
        chart_planets[name] = get_planet_position(birth_date, planet_id)

    julian_day = swe.utc_to_jd(birth_date.year, birth_date.month, birth_date.day, birth_date.hour, birth_date.minute, birth_date.second, 1)[1]
    houses_raw = swe.houses(julian_day, latitude, longitude, house_system)
    chart_houses = houses_raw[0]
    return chart_planets, chart_houses

def calculate_aspects(planets, orb):
    """Finds aspects between planets within a given orb. Returns list of dicts."""
    aspects_found = []
    planet_names = list(planets.keys())
    aspect_definitions = {'Conjunction': 0, 'Opposition': 180, 'Trine': 120, 'Square': 90, 'Sextile': 60}

    for i in range(len(planet_names)):
        for j in range(i + 1, len(planet_names)):
            p1_name = planet_names[i]
            p2_name = planet_names[j]
            p1_pos, p1_speed = planets[p1_name]
            p2_pos, p2_speed = planets[p2_name]

            angle = abs(p1_pos - p2_pos)
            if angle > 180: angle = 360 - angle

            for aspect_name, aspect_angle in aspect_definitions.items():
                current_orb = abs(angle - aspect_angle)
                if current_orb <= orb:
                    sorted_planets = sorted([p1_name, p2_name])
                    aspect_info = {
                        'p1': sorted_planets[0], 'aspect': aspect_name, 'p2': sorted_planets[1],
                        'name': f"{sorted_planets[0]} {aspect_name} {sorted_planets[1]}",
                        'orb': current_orb
                    }
                    aspects_found.append(aspect_info)
    return aspects_found

def find_cross_aspects(planets1, planets2, orb):
    """Finds aspects between two different sets of planets. Returns list of dicts."""
    aspects_found = []
    aspect_definitions = {'Conjunction': 0, 'Opposition': 180, 'Trine': 120, 'Square': 90, 'Sextile': 60}

    for p1_name, (p1_pos, p1_speed) in planets1.items():
        for p2_name, (p2_pos, p2_speed) in planets2.items():
            angle = abs(p1_pos - p2_pos)
            if angle > 180: angle = 360 - angle

            for aspect_name, aspect_angle in aspect_definitions.items():
                current_orb = abs(angle - aspect_angle)
                if current_orb <= orb:
                    aspect_info = {
                        'p1': p1_name, 'aspect': aspect_name, 'p2': p2_name,
                        'name': f"{p1_name} {aspect_name} {p2_name}",
                        'orb': current_orb
                    }
                    aspects_found.append(aspect_info)
    return aspects_found

# --- NEW PREDICTIVE FUNCTIONS ---

def calculate_transits(calculation_date):
    """Calculates the positions of transiting planets for a given date."""
    transit_planets = {}
    for name, planet_id in PLANETS.items():
        transit_planets[name] = get_planet_position(calculation_date, planet_id)
    return transit_planets

def calculate_secondary_progressions(birth_date, target_date):
    """Calculates secondary progressed planet positions based on the 'day for a year' principle."""
    days_offset = (target_date.date() - birth_date.date()).days
    progression_date = birth_date + timedelta(days=days_offset)

    progressed_planets = {}
    for name, planet_id in PLANETS.items():
        progressed_planets[name] = get_planet_position(progression_date, planet_id)
    return progressed_planets

def calculate_solar_arc_progressions(birth_date, target_date):
    """Calculates Solar Arc progressed planet positions."""
    days_offset = (target_date.date() - birth_date.date()).days
    progression_date = birth_date + timedelta(days=days_offset)

    natal_jd = swe.utc_to_jd(birth_date.year, birth_date.month, birth_date.day, birth_date.hour, birth_date.minute, birth_date.second, 1)[1]
    prog_jd = swe.utc_to_jd(progression_date.year, progression_date.month, progression_date.day, progression_date.hour, progression_date.minute, progression_date.second, 1)[1]

    natal_sun_lon = swe.calc_ut(natal_jd, swe.SUN, swe.FLG_SWIEPH)[0][0]
    prog_sun_lon = swe.calc_ut(prog_jd, swe.SUN, swe.FLG_SWIEPH)[0][0]

    solar_arc = prog_sun_lon - natal_sun_lon
    if solar_arc < 0:
        solar_arc += 360

    natal_planets, _ = calculate_natal_chart(birth_date, 0, 0)
    sa_planets = {}
    for name, (natal_lon, natal_speed) in natal_planets.items():
        sa_lon = (natal_lon + solar_arc) % 360
        # The speed of a solar-arced planet is conventionally the same as the natal speed.
        sa_planets[name] = (sa_lon, natal_speed)
    return sa_planets

def _find_return_jd(natal_lon, body_id, start_jd):
    """Helper function to find the precise Julian Day of a celestial body's return."""
    t_jd = start_jd
    for _ in range(5): # Iterate to refine the position
        pos_at_t = swe.calc_ut(t_jd, body_id, swe.FLG_SWIEPH | swe.FLG_SPEED)[0]
        current_lon = pos_at_t[0]
        speed = pos_at_t[3]

        angle_diff = natal_lon - current_lon
        if angle_diff > 180: angle_diff -= 360
        if angle_diff < -180: angle_diff += 360

        if abs(speed) > 1e-9:
            time_offset = angle_diff / speed
            t_jd += time_offset
        else:
            break
    return t_jd

def calculate_solar_return(birth_date, target_year, latitude, longitude, house_system=b'P'):
    """Calculates the Solar Return chart for a given year and location."""
    natal_jd_ut = swe.utc_to_jd(birth_date.year, birth_date.month, birth_date.day, birth_date.hour, birth_date.minute, birth_date.second, 1)[1]
    natal_sun_lon = swe.calc_ut(natal_jd_ut, swe.SUN, swe.FLG_SWIEPH)[0][0]

    start_jd_ut_for_search = swe.utc_to_jd(target_year, birth_date.month, birth_date.day, 0, 0, 0, 1)[1]
    return_jd = _find_return_jd(natal_sun_lon, swe.SUN, start_jd_ut_for_search)

    return_date_tuple = swe.jdut1_to_utc(return_jd, 1) # Corrected function name
    # The tuple returned by pyswisseph contains a float for the seconds part.
    # We need to separate it into seconds and microseconds for the datetime constructor.
    year, month, day, hour, minute, second_float = return_date_tuple
    second = int(second_float)
    microsecond = int((second_float - second) * 1_000_000)
    return_date = datetime(int(year), int(month), int(day), int(hour), int(minute), second, microsecond, tzinfo=timezone.utc)

    return_planets, return_houses = calculate_natal_chart(return_date, latitude, longitude, house_system=house_system)
    return return_planets, return_houses, return_date

def calculate_lunar_return(birth_date, target_date, latitude, longitude):
    """Calculates the Lunar Return chart for a given date and location."""
    natal_jd_ut = swe.utc_to_jd(birth_date.year, birth_date.month, birth_date.day, birth_date.hour, birth_date.minute, birth_date.second, 1)[1]
    natal_moon_lon = swe.calc_ut(natal_jd_ut, swe.MOON, swe.FLG_SWIEPH)[0][0]

    start_jd_ut_for_search = swe.utc_to_jd(target_date.year, target_date.month, target_date.day, 0, 0, 0, 1)[1]
    return_jd = _find_return_jd(natal_moon_lon, swe.MOON, start_jd_ut_for_search)

    return_date_tuple = swe.jdut1_to_utc(return_jd, 1) # Corrected function name
    # The tuple returned by pyswisseph contains a float for the seconds part.
    # We need to separate it into seconds and microseconds for the datetime constructor.
    year, month, day, hour, minute, second_float = return_date_tuple
    second = int(second_float)
    microsecond = int((second_float - second) * 1_000_000)
    return_date = datetime(int(year), int(month), int(day), int(hour), int(minute), second, microsecond, tzinfo=timezone.utc)

    return_planets, return_houses = calculate_natal_chart(return_date, latitude, longitude)
    return return_planets, return_houses, return_date

# --- UI HELPER FUNCTIONS ---

def get_zodiac_sign(degree):
    """Returns the zodiac sign for a given degree."""
    signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
             "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
    return signs[int(degree / 30)]

def get_zodiac_sign_short(degree):
    """Returns the 3-letter abbreviation for a zodiac sign."""
    return get_zodiac_sign(degree)[:3]

def format_longitude(longitude, show_sign=True):
    """Formats a decimal degree into a string like '15° Tau 33''."""
    sign = get_zodiac_sign_short(longitude)
    deg_in_sign = int(longitude % 30)
    minutes = int((longitude - (int(longitude) // 30 * 30) - deg_in_sign) * 60)
    minutes = int((longitude - int(longitude)) * 60)

    if show_sign:
        return f"{deg_in_sign}° {sign} {minutes}'"
    else:
        # The user wants "degrees°minutes'" format, e.g. "15°33'"
        return f"{deg_in_sign}°{minutes:02d}'"

def get_house_ruler(house_cusp_degree):
    """Returns the ruling planet for a house based on its cusp sign using traditional rulers."""
    sign = get_zodiac_sign(house_cusp_degree)
    rulership = {
        "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon",
        "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus", "Scorpio": "Mars",
        "Sagittarius": "Jupiter", "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter"
    }
    return rulership.get(sign, "Unknown")

def get_ruled_houses_for_planet(planet_name, natal_house_cusps):
    """
    Finds which natal houses are ruled by a specific planet based on traditional rulerships.
    For example, if the 7th house cusp is in Aries, Mars rules the 7th house.
    A planet can rule multiple houses.
    """
    ruled_houses = []
    if not natal_house_cusps:
        return []
    for i, cusp_degree in enumerate(natal_house_cusps):
        # We only check the first 12 houses
        if i >= 12:
            break
        ruler = get_house_ruler(cusp_degree)
        if ruler == planet_name:
            ruled_houses.append(str(i + 1))
    return ruled_houses

def calculate_lunar_phase(sun_pos, moon_pos):
    """Calculates the name and angle of the lunar phase."""
    angle = (moon_pos - sun_pos) % 360

    if 0 <= angle < 45:
        phase_name = "New Moon"
    elif 45 <= angle < 90:
        phase_name = "Crescent"
    elif 90 <= angle < 135:
        phase_name = "First Quarter"
    elif 135 <= angle < 180:
        phase_name = "Gibbous"
    elif 180 <= angle < 225:
        phase_name = "Full Moon"
    elif 225 <= angle < 270:
        phase_name = "Disseminating"
    elif 270 <= angle < 315:
        phase_name = "Third Quarter"
    else: # 315 to 360
        phase_name = "Balsamic"

    return phase_name, angle


if __name__ == "__main__":
    # --- Test Data ---
    sample_birth_date = datetime(1990, 5, 15, 8, 30, 0, tzinfo=timezone.utc) # Jane Doe
    pawtucket_lat = 41.87
    pawtucket_lon = -71.38
    today = datetime.now(timezone.utc)

    # --- Test Natal Chart ---
    print("--- Natal Chart ---")
    planets, houses = calculate_natal_chart(sample_birth_date, pawtucket_lat, pawtucket_lon)
    for name, position in planets.items():
        print(f"{name}: {position[0]:.2f}") # Access longitude from tuple

    # --- Test Secondary Progressions ---
    print("\n--- Secondary Progressions ---")
    progressed_planets = calculate_secondary_progressions(sample_birth_date, today)
    for name, position in progressed_planets.items():
        print(f"Progressed {name}: {position[0]:.2f}") # Access longitude from tuple

    # --- Test Solar Return ---
    print("\n--- Solar Return for 2025 ---")
    sr_planets, sr_houses, sr_date = calculate_solar_return(sample_birth_date, 2025, pawtucket_lat, pawtucket_lon)
    print(f"Solar Return Date: {sr_date.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"SR Sun Position: {sr_planets['Sun'][0]:.2f} (Natal: {planets['Sun'][0]:.2f})")
    print(f"SR Ascendant: {sr_houses[0]:.2f}")

    # --- Test Lunar Return ---
    print("\n--- Next Lunar Return ---")
    lr_planets, lr_houses, lr_date = calculate_lunar_return(sample_birth_date, today, pawtucket_lat, pawtucket_lon)
    print(f"Lunar Return Date: {lr_date.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"LR Moon Position: {lr_planets['Moon'][0]:.2f} (Natal: {planets['Moon'][0]:.2f})")
    print(f"LR Ascendant: {lr_houses[0]:.2f}")