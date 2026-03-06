import swisseph as swe
from datetime import datetime, timedelta
import csv
import io

# -----------------------------
# HELPERS
# -----------------------------
def deg_to_rasi(deg):
    rasi_num = int(deg // 30) + 1
    deg_in_rasi = deg % 30
    return rasi_num, deg_in_rasi

def deg_to_dms(deg):
    d = int(deg)
    m = int((deg - d) * 60)
    s = (deg - d - m/60) * 3600
    return d, m, s

def nakshatra_pada(lon):
    nak = int(lon / 13.3333333333) + 1
    pada = int((lon % 13.3333333333) / 3.3333333333) + 1
    return nak, pada

# >>> CHANGE: Added helper to create rows for any celestial body
# This avoids repeating the same logic for Ascendant, planets, etc.
def add_body_row(rows, name, lon, cusps, retro=""):
    
    rasi, _ = deg_to_rasi(lon)
    nak, pada = nakshatra_pada(lon)

    house = get_house_number(lon, cusps)
    
    rows.append([
        name,
        f"{lon:.5f}",
        RASI_NAMES[rasi],
        NAKSHATRA_NAMES[nak],
        pada,
        retro,
        house
    ])

# >>> NEW HELPER: determine house number
def get_house_number(lon, cusps):

    for i in range(12):

        start = cusps[i]
        end = cusps[(i + 1) % 12]

        if start < end:
            if start <= lon < end:
                return i + 1
        else:
            if lon >= start or lon < end:
                return i + 1

    return None
# -----------------------------
# RASI & NAKSHATRA NAMES
# -----------------------------
RASI_NAMES = {
    1: 'Aries', 2: 'Taurus', 3: 'Gemini', 4: 'Cancer',
    5: 'Leo', 6: 'Virgo', 7: 'Libra', 8: 'Scorpio',
    9: 'Sagittarius', 10: 'Capricorn', 11: 'Aquarius', 12: 'Pisces'
}

NAKSHATRA_NAMES = {
    1: 'Ashwini', 2: 'Bharani', 3: 'Krittika', 4: 'Rohini',
    5: 'Mrigashira', 6: 'Ardra', 7: 'Punarvasu', 8: 'Pushya',
    9: 'Ashlesha', 10: 'Magha', 11: 'Purva Phalguni', 12: 'Uttara Phalguni',
    13: 'Hasta', 14: 'Chitra', 15: 'Swati', 16: 'Vishakha',
    17: 'Anuradha', 18: 'Jyeshtha', 19: 'Mula', 20: 'Purva Ashadha',
    21: 'Uttara Ashadha', 22: 'Shravana', 23: 'Dhanishta', 24: 'Shatabhisha',
    25: 'Purva Bhadrapada', 26: 'Uttara Bhadrapada', 27: 'Revati'
}

# -----------------------------
# MAIN FUNCTION
# -----------------------------
def generate_csv_from_params(params: dict) -> bytes:
    """
    params dict must contain:
      - name
      - dob (YYYYMMDD)
      - tob (HHMMSS)  <-- no colon, e.g. 024500
      - utc_offset (float)
      - longitude (float)
      - latitude (float)
    """
    name = params["name"]
    dob = params["dob"]         # YYYYMMDD
    tob = params["tob"]         # HHMMSS
    utc_offset = float(params["utc_offset"])
    longitude = float(params["longitude"])
    latitude = float(params["latitude"])

    # Parse datetime
    birth_local = datetime.strptime(dob + " " + tob, "%Y%m%d %H%M%S")
    birth_utc = birth_local - timedelta(hours=utc_offset)
    year, month, day = birth_utc.year, birth_utc.month, birth_utc.day
    hour = birth_utc.hour + birth_utc.minute/60 + birth_utc.second/3600

    # Julian Day
    jd_ut = swe.julday(year, month, day, hour)

    # Set Lahiri sidereal mode
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)


    flags = swe.FLG_SWIEPH | swe.FLG_SPEED | swe.FLG_SIDEREAL

    # Houses
    cusps, ascmc = swe.houses_ex(jd_ut, latitude, longitude, b'S', flags)
    ascendant = ascmc[0]

    #asc_nak, asc_pada = nakshatra_pada(ascendant)

    # Planets
   # planets = {
   #     'Sun': swe.SUN, 'Moon': swe.MOON, 'Mercury': swe.MERCURY,
   #     'Venus': swe.VENUS, 'Mars': swe.MARS, 'Jupiter': swe.JUPITER,
   #     'Saturn': swe.SATURN, 'Rahu': swe.TRUE_NODE, 'Ketu': swe.TRUE_NODE
   # }

    planets = {
    'Sun': swe.SUN,
    'Moon': swe.MOON,
    'Mars': swe.MARS,
    'Mercury': swe.MERCURY,
    'Jupiter': swe.JUPITER,
    'Venus': swe.VENUS,
    'Saturn': swe.SATURN,
    'Rahu': swe.TRUE_NODE,
    'Ketu': swe.TRUE_NODE
    }

    planet_positions = {}
    for pname, code in planets.items():
        planet_code = swe.TRUE_NODE if pname in ['Rahu','Ketu'] else code
        result, _ = swe.calc_ut(jd_ut, planet_code, flags)
        lon = result[0]
        speed = result[3]
        retro = "Y" if speed < 0 else "N"
        if pname == 'Ketu':
            lon = (lon + 180) % 360
        planet_positions[pname] = (lon, retro)

    # Prepare CSV
    headers = ["Planet", "Degree", "Rasi", "Nakshatra", "Pada", "Retro", "House"]
    
     # >>> CHANGE: Create list to store rows
    rows = []

    # >>> CHANGE: Add Ascendant row
    add_body_row(rows, "Ascendant", ascendant, cusps, "")

    # >>> CHANGE: Add planets as rows
    for pname, (lon, retro) in planet_positions.items():
        add_body_row(rows, pname, lon, cusps, retro)

    # -----------------------------
    # WRITE CSV
    # -----------------------------

    output = io.StringIO()
    writer = csv.writer(output)

    # >>> CHANGE: First row contains metadata
    writer.writerow([
        "Native_Name",
        name,
        "Birth_UTC",
        birth_utc.strftime("%Y-%m-%d %H:%M:%S"),
        "Julian_Day",
        f"{jd_ut:.5f}"
    ])

    # >>> CHANGE: Second row is table header
    writer.writerow(headers)

    # >>> CHANGE: Remaining rows are Ascendant + planets
    for r in rows:
        writer.writerow(r)

    # >>> HOUSE LABELS 1–6
    writer.writerow([
        "House1","House2","House3","House4","House5","House6"
    ])
    
    # >>> HOUSE VALUES 1–6
    writer.writerow([f"{c:.5f}" for c in cusps[:6]])
    
    # >>> HOUSE LABELS 7–12
    writer.writerow([
        "House7","House8","House9","House10","House11","House12"
    ])
    
    # >>> HOUSE VALUES 7–12
    writer.writerow([f"{c:.5f}" for c in cusps[6:12]])
    



    return output.getvalue().encode("utf-8")
