import swisseph as swe
from datetime import datetime, timedelta
import csv, io


# =========================================================
# CONSTANT DEFINITIONS
# =========================================================

RASI_NAMES = {1:'Aries',2:'Taurus',3:'Gemini',4:'Cancer',5:'Leo',6:'Virgo',7:'Libra',8:'Scorpio',9:'Sagittarius',10:'Capricorn',11:'Aquarius',12:'Pisces'}

NAKSHATRA_NAMES = {1:'Ashwini',2:'Bharani',3:'Krittika',4:'Rohini',5:'Mrigashira',6:'Ardra',7:'Punarvasu',8:'Pushya',9:'Ashlesha',10:'Magha',11:'Purva Phalguni',12:'Uttara Phalguni',13:'Hasta',14:'Chitra',15:'Swati',16:'Vishakha',17:'Anuradha',18:'Jyeshtha',19:'Mula',20:'Purva Ashadha',21:'Uttara Ashadha',22:'Shravana',23:'Dhanishta',24:'Shatabhisha',25:'Purva Bhadrapada',26:'Uttara Bhadrapada',27:'Revati'}

FIELDS = ["deg","rasi","nak","pada","house","retro"]


# =========================================================
# BODY REGISTRY
# =========================================================

BODY_DEFS = {"Ascendant":lambda jd,lat,lon,flags,cusps,asc:(asc,""),"Sun":swe.SUN,"Moon":swe.MOON,"Mars":swe.MARS,"Mercury":swe.MERCURY,"Jupiter":swe.JUPITER,"Venus":swe.VENUS,"Saturn":swe.SATURN,"Rahu":swe.TRUE_NODE,"Ketu":swe.TRUE_NODE,"Mandi":"mandi"}

BODY_ORDER = list(BODY_DEFS.keys())


# =========================================================
# BASIC HELPER FUNCTIONS
# =========================================================

def deg_to_rasi(deg):
    return int(deg // 30) + 1, deg % 30


def nakshatra_pada(lon):
    nak = int(lon / 13.3333333333) + 1
    pada = int((lon % 13.3333333333) / 3.3333333333) + 1
    return nak, pada


def get_house_number(lon, cusps):

    for i in range(12):

        start = cusps[i]
        end = cusps[(i + 1) % 12]

        if start < end and start <= lon < end:
            return i + 1

        if start > end and (lon >= start or lon < end):
            return i + 1

    return None


# =========================================================
# MANDI CALCULATION
# =========================================================

def calculate_mandi(jd_ut, lat, lon):

    rsmi = swe.rise_trans(jd_ut, swe.SUN, swe.CALC_RISE, (lon, lat, 0))
    sunset = swe.rise_trans(jd_ut, swe.SUN, swe.CALC_SET, (lon, lat, 0))

    sunrise_jd = rsmi[1][0]
    sunset_jd = sunset[1][0]

    day_length = sunset_jd - sunrise_jd

    weekday = int((jd_ut + 1.5) % 7)
    sat_portions = [6,5,4,3,2,1,0]

    mandi_jd = sunrise_jd + day_length * sat_portions[weekday] / 8

    cusps_m, ascmc_m = swe.houses_ex(mandi_jd, lat, lon, b'S')

    return ascmc_m[0]


# =========================================================
# MAIN ENTRY FUNCTION
# =========================================================

def generate_csv_from_params(params: dict) -> bytes:


    # =========================================================
    # INPUT PARAMETERS
    # =========================================================

    name = params["name"]
    dob = params["dob"]
    tob = params["tob"]

    utc_offset = float(params["utcoffset"])
    longitude = float(params["long"])
    latitude = float(params["lat"])

    # >>> ADDED
    step = float(params.get("step",0))
    adjcount = int(params.get("adjcount",0))

    print(params)

    # >>> ADDED
    birth_local_base = datetime.strptime(dob + " " + tob, "%Y%m%d %H%M%S")


    output = io.StringIO()
    writer = csv.writer(output)

    header_written = False  # >>> ADDED


    # >>> ADDED  (loop to generate multiple charts)
    for adj in range(adjcount + 1):

        print("Chart iteration:", adj)

        adjustment_seconds = step * adj
        birth_local = birth_local_base + timedelta(seconds=adjustment_seconds)

        tob_used = birth_local.strftime("%H%M%S")


        # =========================================================
        # CONVERT LOCAL TIME → UTC
        # =========================================================

        birth_utc = birth_local - timedelta(hours = utc_offset)

        year = birth_utc.year
        month = birth_utc.month
        day = birth_utc.day

        hour = birth_utc.hour + birth_utc.minute/60 + birth_utc.second/3600


        # =========================================================
        # JULIAN DAY + SIDEREAL SETTINGS
        # =========================================================

        jd_ut = swe.julday(year, month, day, hour)

        swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)

        flags = swe.FLG_SWIEPH | swe.FLG_SPEED | swe.FLG_SIDEREAL


        # =========================================================
        # HOUSE CALCULATION
        # =========================================================

        cusps, ascmc = swe.houses_ex(jd_ut, latitude, longitude, b'S', flags)

        ascendant = ascmc[0]


        # =========================================================
        # SPECIAL POINT CALCULATIONS
        # =========================================================

        mandi_lon = calculate_mandi(jd_ut, latitude, longitude)


        body_data = {}


        def build_body_data(body, lon, retro=""):

            rasi, _ = deg_to_rasi(lon)
            nak, pada = nakshatra_pada(lon)
            house = get_house_number(lon, cusps)

            body_data[body] = {
                "deg": f"{lon:.5f}",
                "rasi": RASI_NAMES[rasi],
                "nak": NAKSHATRA_NAMES[nak],
                "pada": pada,
                "house": house,
                "retro": retro
            }


        for body, source in BODY_DEFS.items():

            if isinstance(source, int):

                result, _ = swe.calc_ut(jd_ut, source, flags)

                lon = result[0]
                speed = result[3]

                retro = "Y" if speed < 0 else "N"

                if body == "Ketu":
                    lon = (lon + 180) % 360

            elif callable(source):

                lon, retro = source(jd_ut, latitude, longitude, flags, cusps, ascendant)

            elif source == "mandi":

                lon = mandi_lon
                retro = ""

            build_body_data(body, lon, retro)


        headers_row = []
        values_row = []


        # >>> CHANGED (column name)
        headers_row += ["ChartID","PersonID","ChartType","DOB","TOB_used","AdjustmentSeconds","Latitude","Longitude","Timezone","JulianDay"]

        chart_id = f"CH{adj:02d}"  # >>> CHANGED

        dob_used = birth_local.strftime("%Y%m%d")

        # >>> CHANGED (write seconds instead of minutes)
        values_row += [chart_id, name, "D1", dob_used, tob_used, adjustment_seconds, latitude, longitude, utc_offset, f"{jd_ut:.5f}"]


        for i, c in enumerate(cusps, start = 1):

            headers_row.append(f"House{i}")
            values_row.append(f"{c:.5f}")


        for field in FIELDS:

            for body in BODY_ORDER:

                headers_row.append(f"{body}_{field}")
                values_row.append(body_data[body][field])


        # >>> CHANGED (write header only once)
        if not header_written:
            writer.writerow(headers_row)
            header_written = True

        writer.writerow(values_row)


    return output.getvalue().encode("utf-8")