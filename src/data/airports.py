"""
Centralized airport reference data.

Single source of truth for airport metadata used across:
  - src/apis/amadeus.py     (IATA codes, name/city/country)
  - src/tools/travel_tools.py  (coordinates for weather, UTC offsets for timezones)
  - mcp_server/travel_mcp.py   (coordinates + timezone name + UTC offset)
"""

# Keys per entry:
#   name        – full airport name
#   city        – display city name
#   country     – country name
#   lat / lon   – WGS-84 coordinates (None if unknown)
#   timezone    – IANA-style abbreviation (e.g. "WAT", "CET")
#   utc_offset  – UTC offset in whole hours (standard time)

AIRPORT_DATA = {
    # ============ NIGERIA ============
    "LOS": {"name": "Murtala Muhammed International", "city": "Lagos",         "country": "Nigeria",              "lat":  6.5244, "lon":   3.3792, "timezone": "WAT",  "utc_offset":  1},
    "ABV": {"name": "Nnamdi Azikiwe International",   "city": "Abuja",         "country": "Nigeria",              "lat":  9.0579, "lon":   7.4951, "timezone": "WAT",  "utc_offset":  1},
    "PHC": {"name": "Port Harcourt International",    "city": "Port Harcourt", "country": "Nigeria",              "lat":  4.8470, "lon":   7.0218, "timezone": "WAT",  "utc_offset":  1},

    # ============ UNITED KINGDOM ============
    "LHR": {"name": "Heathrow",          "city": "London",          "country": "UK", "lat": 51.4700, "lon":  -0.4543, "timezone": "GMT", "utc_offset": 0},
    "LGW": {"name": "Gatwick",           "city": "London Gatwick",  "country": "UK", "lat": 51.1537, "lon":  -0.1821, "timezone": "GMT", "utc_offset": 0},
    "STN": {"name": "Stansted",          "city": "London Stansted", "country": "UK", "lat": 51.8850, "lon":   0.2350, "timezone": "GMT", "utc_offset": 0},
    "LTN": {"name": "Luton",             "city": "London Luton",    "country": "UK", "lat": 51.8747, "lon":  -0.3683, "timezone": "GMT", "utc_offset": 0},
    "MAN": {"name": "Manchester",        "city": "Manchester",      "country": "UK", "lat": 53.3537, "lon":  -2.2750, "timezone": "GMT", "utc_offset": 0},
    "EDI": {"name": "Edinburgh",         "city": "Edinburgh",       "country": "UK", "lat": 55.9500, "lon":  -3.3725, "timezone": "GMT", "utc_offset": 0},
    "BHX": {"name": "Birmingham",        "city": "Birmingham",      "country": "UK", "lat": 52.4539, "lon":  -1.7480, "timezone": "GMT", "utc_offset": 0},
    "GLA": {"name": "Glasgow",           "city": "Glasgow",         "country": "UK", "lat": 55.8719, "lon":  -4.4331, "timezone": "GMT", "utc_offset": 0},

    # ============ BALKANS & EASTERN EUROPE ============
    "TBS": {"name": "Shota Rustaveli Tbilisi International", "city": "Tbilisi",   "country": "Georgia",             "lat": 41.6692, "lon": 44.9547, "timezone": "GET", "utc_offset": 4},
    "BUS": {"name": "Batumi International",                  "city": "Batumi",    "country": "Georgia",             "lat": 41.6103, "lon": 41.5997, "timezone": "GET", "utc_offset": 4},
    "BEG": {"name": "Nikola Tesla",                          "city": "Belgrade",  "country": "Serbia",              "lat": 44.8184, "lon": 20.3091, "timezone": "CET", "utc_offset": 1},
    "SKP": {"name": "Skopje International",                  "city": "Skopje",    "country": "North Macedonia",     "lat": 41.9617, "lon": 21.6214, "timezone": "CET", "utc_offset": 1},
    "OHD": {"name": "St. Paul the Apostle",                  "city": "Ohrid",     "country": "North Macedonia",     "lat": 41.1800, "lon": 20.7423, "timezone": "CET", "utc_offset": 1},
    "TGD": {"name": "Podgorica",                             "city": "Podgorica", "country": "Montenegro",          "lat": 42.3594, "lon": 19.2519, "timezone": "CET", "utc_offset": 1},
    "TIV": {"name": "Tivat",                                 "city": "Tivat",     "country": "Montenegro",          "lat": 42.4047, "lon": 18.7233, "timezone": "CET", "utc_offset": 1},
    "TIA": {"name": "Tirana International",                  "city": "Tirana",    "country": "Albania",             "lat": 41.4147, "lon": 19.7206, "timezone": "CET", "utc_offset": 1},
    "SJJ": {"name": "Sarajevo International",                "city": "Sarajevo",  "country": "Bosnia & Herzegovina","lat": 43.8246, "lon": 18.3315, "timezone": "CET", "utc_offset": 1},

    # ============ CARIBBEAN ============
    "ANU": {"name": "V.C. Bird International",       "city": "St. John's",    "country": "Antigua & Barbuda",   "lat": 17.1367, "lon":  -61.7927, "timezone": "AST", "utc_offset": -4},
    "PUJ": {"name": "Punta Cana International",      "city": "Punta Cana",    "country": "Dominican Republic",  "lat": 18.5675, "lon":  -68.3634, "timezone": "AST", "utc_offset": -4},
    "SDQ": {"name": "Las Americas International",    "city": "Santo Domingo", "country": "Dominican Republic",  "lat": 18.4297, "lon":  -69.6689, "timezone": "AST", "utc_offset": -4},
    "AXA": {"name": "Clayton J. Lloyd International","city": "The Valley",    "country": "Anguilla",            "lat": 18.2048, "lon":  -63.0500, "timezone": "AST", "utc_offset": -4},
    "SXM": {"name": "Princess Juliana International","city": "Philipsburg",   "country": "Sint Maarten",        "lat": 18.0410, "lon":  -63.1089, "timezone": "AST", "utc_offset": -4},
    "PLS": {"name": "Providenciales International",  "city": "Providenciales","country": "Turks & Caicos",      "lat": 21.7736, "lon":  -72.2659, "timezone": "EST", "utc_offset": -5},

    # ============ TURKEY ============
    "IST": {"name": "Istanbul Airport",  "city": "Istanbul",       "country": "Turkey", "lat": 41.2753, "lon": 28.7519, "timezone": "TRT", "utc_offset": 3},
    "SAW": {"name": "Sabiha Gokcen",     "city": "Istanbul Sabiha","country": "Turkey", "lat": 40.8986, "lon": 29.3092, "timezone": "TRT", "utc_offset": 3},
    "AYT": {"name": "Antalya",           "city": "Antalya",        "country": "Turkey", "lat": 36.8987, "lon": 30.8005, "timezone": "TRT", "utc_offset": 3},
    "ADB": {"name": "Adnan Menderes",    "city": "Izmir",          "country": "Turkey", "lat": 38.2924, "lon": 27.1570, "timezone": "TRT", "utc_offset": 3},

    # ============ MIDDLE EAST ============
    "DOH": {"name": "Hamad International", "city": "Doha",      "country": "Qatar", "lat": 25.2731, "lon": 51.6081, "timezone": "AST", "utc_offset": 3},
    "DXB": {"name": "Dubai International","city": "Dubai",      "country": "UAE",   "lat": 25.2532, "lon": 55.3657, "timezone": "GST", "utc_offset": 4},
    "AUH": {"name": "Zayed International","city": "Abu Dhabi",  "country": "UAE",   "lat": 24.4330, "lon": 54.6511, "timezone": "GST", "utc_offset": 4},
    "SHJ": {"name": "Sharjah International","city": "Sharjah",  "country": "UAE",   "lat": 25.3286, "lon": 55.5172, "timezone": "GST", "utc_offset": 4},

    # ============ ASIA ============
    "PEK": {"name": "Beijing Capital",    "city": "Beijing",      "country": "China",     "lat": 40.0799, "lon": 116.6031, "timezone": "CST", "utc_offset": 8},
    "PKX": {"name": "Beijing Daxing",     "city": "Beijing Daxing","country": "China",    "lat": 39.5093, "lon": 116.4112, "timezone": "CST", "utc_offset": 8},
    "PVG": {"name": "Pudong International","city": "Shanghai",    "country": "China",     "lat": 31.1443, "lon": 121.8083, "timezone": "CST", "utc_offset": 8},
    "CAN": {"name": "Baiyun International","city": "Guangzhou",   "country": "China",     "lat": 23.3924, "lon": 113.2988, "timezone": "CST", "utc_offset": 8},
    "HKG": {"name": "Hong Kong International","city": "Hong Kong","country": "Hong Kong", "lat": 22.3080, "lon": 113.9185, "timezone": "HKT", "utc_offset": 8},
    "NRT": {"name": "Narita International","city": "Tokyo Narita","country": "Japan",     "lat": 35.7720, "lon": 140.3929, "timezone": "JST", "utc_offset": 9},
    "HND": {"name": "Haneda",             "city": "Tokyo Haneda", "country": "Japan",     "lat": 35.5494, "lon": 139.7798, "timezone": "JST", "utc_offset": 9},
    "KIX": {"name": "Kansai International","city": "Osaka",       "country": "Japan",     "lat": 34.4273, "lon": 135.2440, "timezone": "JST", "utc_offset": 9},
    "SIN": {"name": "Changi",             "city": "Singapore",    "country": "Singapore", "lat":  1.3644, "lon": 103.9915, "timezone": "SGT", "utc_offset": 8},

    # ============ EUROPE — Netherlands ============
    "AMS": {"name": "Schiphol",            "city": "Amsterdam", "country": "Netherlands", "lat": 52.3105, "lon":  4.7683, "timezone": "CET", "utc_offset": 1},
    "RTM": {"name": "Rotterdam The Hague", "city": "Rotterdam", "country": "Netherlands", "lat": 51.9569, "lon":  4.4371, "timezone": "CET", "utc_offset": 1},

    # ============ EUROPE — Italy ============
    "FCO": {"name": "Leonardo da Vinci–Fiumicino", "city": "Rome",   "country": "Italy", "lat": 41.8003, "lon": 12.2389, "timezone": "CET", "utc_offset": 1},
    "MXP": {"name": "Malpensa",                    "city": "Milan",  "country": "Italy", "lat": 45.6306, "lon":  8.7281, "timezone": "CET", "utc_offset": 1},
    "VCE": {"name": "Marco Polo",                  "city": "Venice", "country": "Italy", "lat": 45.5053, "lon": 12.3521, "timezone": "CET", "utc_offset": 1},
    "NAP": {"name": "Naples International",        "city": "Naples", "country": "Italy", "lat": 40.8861, "lon": 14.2908, "timezone": "CET", "utc_offset": 1},

    # ============ EUROPE — France ============
    "CDG": {"name": "Charles de Gaulle",      "city": "Paris CDG",  "country": "France", "lat": 49.0097, "lon": 2.5479, "timezone": "CET", "utc_offset": 1},
    "ORY": {"name": "Orly",                   "city": "Paris Orly", "country": "France", "lat": 48.7262, "lon": 2.3652, "timezone": "CET", "utc_offset": 1},
    "NCE": {"name": "Nice Côte d'Azur",       "city": "Nice",       "country": "France", "lat": 43.6584, "lon": 7.2159, "timezone": "CET", "utc_offset": 1},
    "LYS": {"name": "Lyon–Saint-Exupéry",     "city": "Lyon",       "country": "France", "lat": 45.7256, "lon": 5.0811, "timezone": "CET", "utc_offset": 1},

    # ============ EUROPE — Spain ============
    "MAD": {"name": "Adolfo Suárez Madrid–Barajas",        "city": "Madrid",    "country": "Spain", "lat": 40.4983, "lon": -3.5676, "timezone": "CET", "utc_offset": 1},
    "BCN": {"name": "Josep Tarradellas Barcelona–El Prat", "city": "Barcelona", "country": "Spain", "lat": 41.2971, "lon":  2.0785, "timezone": "CET", "utc_offset": 1},
    "AGP": {"name": "Málaga–Costa del Sol",                "city": "Malaga",    "country": "Spain", "lat": 36.6749, "lon": -4.4991, "timezone": "CET", "utc_offset": 1},
    "PMI": {"name": "Palma de Mallorca",                   "city": "Palma",     "country": "Spain", "lat": 39.5517, "lon":  2.7388, "timezone": "CET", "utc_offset": 1},

    # ============ EUROPE — Germany ============
    "FRA": {"name": "Frankfurt",        "city": "Frankfurt", "country": "Germany", "lat": 50.0379, "lon":  8.5622, "timezone": "CET", "utc_offset": 1},
    "MUC": {"name": "Munich",           "city": "Munich",    "country": "Germany", "lat": 48.3538, "lon": 11.7861, "timezone": "CET", "utc_offset": 1},
    "BER": {"name": "Berlin Brandenburg","city": "Berlin",   "country": "Germany", "lat": 52.3667, "lon": 13.5033, "timezone": "CET", "utc_offset": 1},

    # ============ AFRICA — Morocco ============
    "CMN": {"name": "Mohammed V International", "city": "Casablanca", "country": "Morocco", "lat": 33.3675, "lon": -7.5898, "timezone": "WET", "utc_offset": 1},
    "RAK": {"name": "Marrakech Menara",          "city": "Marrakech",  "country": "Morocco", "lat": 31.6069, "lon": -8.0363, "timezone": "WET", "utc_offset": 1},
    "TNG": {"name": "Ibn Battouta",              "city": "Tangier",    "country": "Morocco", "lat": 35.7267, "lon": -5.9168, "timezone": "WET", "utc_offset": 1},
    "FEZ": {"name": "Fès–Saïs",                 "city": "Fez",        "country": "Morocco", "lat": 33.9272, "lon": -4.9779, "timezone": "WET", "utc_offset": 1},

    # ============ AFRICA — Other ============
    "ADD": {"name": "Bole International",        "city": "Addis Ababa",   "country": "Ethiopia",     "lat":  8.9779, "lon": 38.7993, "timezone": "EAT",  "utc_offset": 3},
    "JNB": {"name": "O.R. Tambo International",  "city": "Johannesburg",  "country": "South Africa", "lat": -26.1392,"lon": 28.2460, "timezone": "SAST", "utc_offset": 2},
    "CPT": {"name": "Cape Town International",   "city": "Cape Town",     "country": "South Africa", "lat": -33.9715,"lon": 18.6021, "timezone": "SAST", "utc_offset": 2},
    "CAI": {"name": "Cairo International",       "city": "Cairo",         "country": "Egypt",        "lat": 30.1219, "lon": 31.4056, "timezone": "EET",  "utc_offset": 2},

    # ============ AMERICAS — USA ============
    "JFK": {"name": "John F. Kennedy",        "city": "New York JFK",  "country": "USA",    "lat": 40.6413, "lon":  -73.7781, "timezone": "EST", "utc_offset": -5},
    "EWR": {"name": "Newark Liberty",         "city": "Newark",        "country": "USA",    "lat": 40.6895, "lon":  -74.1745, "timezone": "EST", "utc_offset": -5},
    "LAX": {"name": "Los Angeles International","city": "Los Angeles",  "country": "USA",    "lat": 33.9416, "lon": -118.4085, "timezone": "PST", "utc_offset": -8},
    "ATL": {"name": "Hartsfield-Jackson",      "city": "Atlanta",       "country": "USA",    "lat": 33.6407, "lon":  -84.4277, "timezone": "EST", "utc_offset": -5},
    "MIA": {"name": "Miami International",     "city": "Miami",         "country": "USA",    "lat": 25.7959, "lon":  -80.2870, "timezone": "EST", "utc_offset": -5},

    # ============ AMERICAS — Canada ============
    "YYZ": {"name": "Toronto Pearson",        "city": "Toronto",   "country": "Canada", "lat": 43.6777, "lon":  -79.6248, "timezone": "EST", "utc_offset": -5},
    "YVR": {"name": "Vancouver International","city": "Vancouver", "country": "Canada", "lat": 49.1967, "lon": -123.1815, "timezone": "PST", "utc_offset": -8},
}


# ---------------------------------------------------------------------------
# Derived views — built once at import time so callers pay no runtime cost
# ---------------------------------------------------------------------------

# {code: {"name": ..., "city": ..., "country": ...}}  — used by amadeus.py
AIRPORTS = {
    code: {"name": d["name"], "city": d["city"], "country": d["country"]}
    for code, d in AIRPORT_DATA.items()
}

# {code: (lat, lon)}  — used by WeatherTool
AIRPORT_COORDS = {
    code: (d["lat"], d["lon"])
    for code, d in AIRPORT_DATA.items()
    if d["lat"] is not None
}

# {code: utc_offset}  — used by TimeZoneCalculator
AIRPORT_TIMEZONES = {
    code: d["utc_offset"]
    for code, d in AIRPORT_DATA.items()
    if d["utc_offset"] is not None
}

# {code: (tz_name, utc_offset)}  — used by mcp_server
AIRPORT_TIMEZONES_NAMED = {
    code: (d["timezone"], d["utc_offset"])
    for code, d in AIRPORT_DATA.items()
    if d["timezone"] is not None
}

# {code: (lat, lon, city)}  — used by mcp_server weather tool
AIRPORT_COORDS_NAMED = {
    code: (d["lat"], d["lon"], d["city"])
    for code, d in AIRPORT_DATA.items()
    if d["lat"] is not None
}
