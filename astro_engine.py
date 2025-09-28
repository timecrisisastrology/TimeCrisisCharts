import swisseph as swe
from datetime import datetime, timezone

def get_planet_position(calculation_date, planet_id):
    julian_day_utc = swe.utc_to_jd(calculation_date.year, calculation_date.month, calculation_date.day, calculation_date.hour, calculation_date.minute, calculation_date.second, 1)[1]
    planet_position_data = swe.calc_ut(julian_day_utc, planet_id, swe.FLG_SWIEPH)
    longitude = planet_position_data[0][0]
    return longitude

def calculate_natal_chart(birth_date, latitude, longitude):
    planets_to_calculate = {
        'Sun': swe.SUN, 'Moon': swe.MOON, 'Mercury': swe.MERCURY, 'Venus': swe.VENUS, 'Mars': swe.MARS,
        'Jupiter': swe.JUPITER, 'Saturn': swe.SATURN, 'Uranus': swe.URANUS, 'Neptune': swe.NEPTUNE, 'Pluto': swe.PLUTO
    }
    chart_planets = {}
    for name, planet_id in planets_to_calculate.items():
        chart_planets[name] = get_planet_position(birth_date, planet_id)
    julian_day = swe.utc_to_jd(birth_date.year, birth_date.month, birth_date.day, birth_date.hour, birth_date.minute, birth_date.second, 1)[1]
    houses_raw = swe.houses(julian_day, latitude, longitude, b'P')
    chart_houses = houses_raw[0]
    return chart_planets, chart_houses

def calculate_aspects(planets, orb):
    aspects_found = []
    planet_names = list(planets.keys())
    # You can customize this dictionary to include any aspects you want!
    aspect_definitions = {
        'Conjunction': 0, 'Semi-Sextile': 30, 'Sextile': 60, 'Square': 90,
        'Trine': 120, 'Inconjunct': 150, 'Opposition': 180
    }
    for i in range(len(planet_names)):
        for j in range(i + 1, len(planet_names)):
            p1_name = planet_names[i]
            p2_name = planet_names[j]
            p1_pos = planets[p1_name]
            p2_pos = planets[p2_name]
            angle = abs(p1_pos - p2_pos)
            if angle > 180:
                angle = 360 - angle
            for aspect_name, aspect_angle in aspect_definitions.items():
                if abs(angle - aspect_angle) <= orb:
                    aspect_info = f"{p1_name} {aspect_name} {p2_name}"
                    aspects_found.append(aspect_info)
    return aspects_found

if __name__ == "__main__":
    sample_birth_date = datetime(2025, 9, 28, 5, 7, 0, tzinfo=timezone.utc)
    pawtucket_lat = 41.87
    pawtucket_lon = -71.38
    
    planets, houses = calculate_natal_chart(sample_birth_date, pawtucket_lat, pawtucket_lon)
    natal_aspects = calculate_aspects(planets, 7) # Using a 7-degree orb

    print("--- Time Crisis Natal Chart ---")
    
    print("\n--- Planets ---")
    for name, position in planets.items():
        print(f"{name}: {position:.2f}")

    print("\n--- Houses ---")
    for i, cusp_position in enumerate(houses):
        house_number = i + 1
        print(f"House {house_number}: {cusp_position:.2f}")
    
    print("\n--- Major Aspects (7-degree orb) ---")
    for aspect in natal_aspects:
        print(aspect)
