"""
Travel Assistant MCP Server
===========================
A Model Context Protocol server providing travel-related tools:
- Weather forecasts
- Currency converter  
- Time zone calculator

This MCP server can be used with Claude Desktop, Cursor, or any MCP-compatible client.

Setup:
1. pip install mcp fastmcp requests
2. Set OPENWEATHER_API_KEY environment variable
3. Add to your MCP client configuration
4. Use the tools in your AI conversations

Author: Ojonugwa Egwuda - FlightFinder Project
"""

import os
import json
import requests
from datetime import datetime
from typing import Optional
from mcp.server.fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("travel-assistant")


# WEATHER TOOL

AIRPORT_COORDS = {
    # Nigeria
    "LOS": (6.5244, 3.3792, "Lagos"),
    "ABV": (9.0579, 7.4951, "Abuja"),
    "PHC": (4.8470, 7.0218, "Port Harcourt"),
    # UK
    "LHR": (51.4700, -0.4543, "London"),
    "LGW": (51.1537, -0.1821, "London Gatwick"),
    "MAN": (53.3537, -2.2750, "Manchester"),
    "EDI": (55.9500, -3.3725, "Edinburgh"),
    # Balkans
    "TBS": (41.6692, 44.9547, "Tbilisi"),
    "BEG": (44.8184, 20.3091, "Belgrade"),
    "TIA": (41.4147, 19.7206, "Tirana"),
    "SJJ": (43.8246, 18.3315, "Sarajevo"),
    # Turkey
    "IST": (41.2753, 28.7519, "Istanbul"),
    "AYT": (36.8987, 30.8005, "Antalya"),
    # Middle East
    "DXB": (25.2532, 55.3657, "Dubai"),
    "AUH": (24.4330, 54.6511, "Abu Dhabi"),
    "DOH": (25.2731, 51.6081, "Doha"),
    # Asia
    "SIN": (1.3644, 103.9915, "Singapore"),
    "HND": (35.5494, 139.7798, "Tokyo"),
    "NRT": (35.7720, 140.3929, "Tokyo Narita"),
    "HKG": (22.3080, 113.9185, "Hong Kong"),
    # Europe
    "CDG": (49.0097, 2.5479, "Paris"),
    "AMS": (52.3105, 4.7683, "Amsterdam"),
    "FCO": (41.8003, 12.2389, "Rome"),
    "MAD": (40.4983, -3.5676, "Madrid"),
    "BCN": (41.2971, 2.0785, "Barcelona"),
    "FRA": (50.0379, 8.5622, "Frankfurt"),
    # Americas
    "JFK": (40.6413, -73.7781, "New York"),
    "LAX": (33.9416, -118.4085, "Los Angeles"),
    "MIA": (25.7959, -80.2870, "Miami"),
    # Caribbean
    "PUJ": (18.5675, -68.3634, "Punta Cana"),
    "SXM": (18.0410, -63.1089, "Sint Maarten"),
    # Africa
    "CMN": (33.3675, -7.5898, "Casablanca"),
    "JNB": (-26.1392, 28.2460, "Johannesburg"),
}

WEATHER_ICONS = {
    "01d": "☀️", "01n": "🌙",
    "02d": "⛅", "02n": "☁️",
    "03d": "☁️", "03n": "☁️",
    "04d": "☁️", "04n": "☁️",
    "09d": "🌧️", "09n": "🌧️",
    "10d": "🌦️", "10n": "🌧️",
    "11d": "⛈️", "11n": "⛈️",
    "13d": "❄️", "13n": "❄️",
    "50d": "🌫️", "50n": "🌫️",
}


@mcp.tool()
def get_weather(airport_code: str) -> str:
    """
    Get current weather for an airport destination.
    
    Args:
        airport_code: IATA airport code (e.g., "LHR", "DXB", "JFK")
    
    Returns:
        Current weather conditions including temperature, humidity, and description
    """
    code = airport_code.upper().strip()
    
    if code not in AIRPORT_COORDS:
        return json.dumps({
            "error": f"Unknown airport: {code}",
            "supported": list(AIRPORT_COORDS.keys())[:20]
        })
    
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return json.dumps({
            "error": "OPENWEATHER_API_KEY not configured",
            "note": "Set the environment variable to enable weather lookups"
        })
    
    lat, lon, city = AIRPORT_COORDS[code]
    
    try:
        response = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"lat": lat, "lon": lon, "appid": api_key, "units": "metric"},
            timeout=10
        )
        
        if response.status_code != 200:
            return json.dumps({"error": f"Weather API error: {response.status_code}"})
        
        data = response.json()
        icon_code = data["weather"][0].get("icon", "01d")
        
        return json.dumps({
            "airport": code,
            "city": data.get("name", city),
            "country": data.get("sys", {}).get("country", ""),
            "weather": {
                "description": data["weather"][0]["description"].title(),
                "icon": WEATHER_ICONS.get(icon_code, "🌡️"),
                "temperature_c": round(data["main"]["temp"], 1),
                "temperature_f": round(data["main"]["temp"] * 9/5 + 32, 1),
                "feels_like_c": round(data["main"]["feels_like"], 1),
                "humidity": data["main"]["humidity"],
                "wind_speed_ms": data["wind"]["speed"],
            },
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch weather: {str(e)}"})



# CURRENCY CONVERTER TOOL

EXCHANGE_RATES = {
    "USD": 1.0,
    "EUR": 0.92,
    "GBP": 0.79,
    "NGN": 1550.0,
    "AED": 3.67,
    "QAR": 3.64,
    "TRY": 30.5,
    "GEL": 2.7,
    "RSD": 108.0,
    "JPY": 149.5,
    "SGD": 1.34,
    "CNY": 7.24,
    "MAD": 10.1,
    "CAD": 1.36,
    "INR": 83.1,
    "ZAR": 18.9,
}

CURRENCY_SYMBOLS = {
    "USD": "$", "EUR": "€", "GBP": "£", "NGN": "₦",
    "AED": "د.إ", "QAR": "ر.ق", "TRY": "₺", "GEL": "₾",
    "RSD": "дин", "JPY": "¥", "SGD": "S$", "CNY": "¥",
    "MAD": "د.م.", "CAD": "C$", "INR": "₹", "ZAR": "R",
}


@mcp.tool()
def convert_currency(
    amount: float,
    from_currency: str,
    to_currency: str
) -> str:
    """
    Convert an amount between currencies.
    
    Args:
        amount: Amount to convert
        from_currency: Source currency code (e.g., "USD", "GBP", "NGN")
        to_currency: Target currency code
    
    Returns:
        Converted amount with exchange rate information
    """
    from_code = from_currency.upper().strip()
    to_code = to_currency.upper().strip()
    
    if from_code not in EXCHANGE_RATES:
        return json.dumps({"error": f"Unknown currency: {from_code}"})
    if to_code not in EXCHANGE_RATES:
        return json.dumps({"error": f"Unknown currency: {to_code}"})
    
    # Convert through USD as base
    usd_amount = amount / EXCHANGE_RATES[from_code]
    converted = usd_amount * EXCHANGE_RATES[to_code]
    rate = EXCHANGE_RATES[to_code] / EXCHANGE_RATES[from_code]
    
    from_symbol = CURRENCY_SYMBOLS.get(from_code, from_code)
    to_symbol = CURRENCY_SYMBOLS.get(to_code, to_code)
    
    return json.dumps({
        "original": f"{from_symbol}{amount:,.2f} {from_code}",
        "converted": f"{to_symbol}{converted:,.2f} {to_code}",
        "amount": round(converted, 2),
        "exchange_rate": round(rate, 4),
        "rate_display": f"1 {from_code} = {rate:.4f} {to_code}",
        "note": "Rates are indicative. Check live rates before transactions."
    })


@mcp.tool()
def get_exchange_rate(
    from_currency: str,
    to_currency: str
) -> str:
    """
    Get the exchange rate between two currencies.
    
    Args:
        from_currency: Source currency code
        to_currency: Target currency code
    
    Returns:
        Current exchange rate
    """
    from_code = from_currency.upper().strip()
    to_code = to_currency.upper().strip()
    
    if from_code not in EXCHANGE_RATES or to_code not in EXCHANGE_RATES:
        return json.dumps({"error": "Unknown currency code"})
    
    rate = EXCHANGE_RATES[to_code] / EXCHANGE_RATES[from_code]
    
    return json.dumps({
        "from": from_code,
        "to": to_code,
        "rate": round(rate, 4),
        "display": f"1 {from_code} = {rate:.4f} {to_code}",
        "inverse": f"1 {to_code} = {1/rate:.4f} {from_code}"
    })



# TIME ZONE TOOL

AIRPORT_TIMEZONES = {
    # Nigeria
    "LOS": ("WAT", 1), "ABV": ("WAT", 1), "PHC": ("WAT", 1),
    # UK
    "LHR": ("GMT", 0), "LGW": ("GMT", 0), "MAN": ("GMT", 0), "EDI": ("GMT", 0),
    # USA
    "JFK": ("EST", -5), "LAX": ("PST", -8), "MIA": ("EST", -5),
    # Middle East
    "DXB": ("GST", 4), "AUH": ("GST", 4), "DOH": ("AST", 3),
    # Turkey
    "IST": ("TRT", 3), "AYT": ("TRT", 3),
    # Balkans
    "TBS": ("GET", 4), "BEG": ("CET", 1), "TIA": ("CET", 1), "SJJ": ("CET", 1),
    # Asia
    "SIN": ("SGT", 8), "HND": ("JST", 9), "NRT": ("JST", 9), "HKG": ("HKT", 8),
    "PEK": ("CST", 8), "PVG": ("CST", 8),
    # Europe
    "CDG": ("CET", 1), "AMS": ("CET", 1), "FCO": ("CET", 1), 
    "MAD": ("CET", 1), "BCN": ("CET", 1), "FRA": ("CET", 1),
    # Caribbean
    "PUJ": ("AST", -4), "SXM": ("AST", -4),
    # Africa
    "CMN": ("WET", 1), "JNB": ("SAST", 2),
}


@mcp.tool()
def get_time_difference(
    origin: str,
    destination: str
) -> str:
    """
    Get the time difference between two airports.
    
    Args:
        origin: Origin airport code
        destination: Destination airport code
    
    Returns:
        Time difference and timezone information
    """
    origin = origin.upper().strip()
    destination = destination.upper().strip()
    
    origin_tz = AIRPORT_TIMEZONES.get(origin)
    dest_tz = AIRPORT_TIMEZONES.get(destination)
    
    if not origin_tz:
        return json.dumps({"error": f"Unknown airport: {origin}"})
    if not dest_tz:
        return json.dumps({"error": f"Unknown airport: {destination}"})
    
    origin_name, origin_offset = origin_tz
    dest_name, dest_offset = dest_tz
    
    diff = dest_offset - origin_offset
    
    if diff == 0:
        diff_text = "Same time zone"
    elif diff > 0:
        diff_text = f"{diff} hours ahead"
    else:
        diff_text = f"{abs(diff)} hours behind"
    
    return json.dumps({
        "origin": {
            "airport": origin,
            "timezone": origin_name,
            "utc_offset": f"UTC{'+' if origin_offset >= 0 else ''}{origin_offset}"
        },
        "destination": {
            "airport": destination,
            "timezone": dest_name,
            "utc_offset": f"UTC{'+' if dest_offset >= 0 else ''}{dest_offset}"
        },
        "difference": {
            "hours": diff,
            "description": diff_text
        },
        "tip": "Adjust sleep schedule 1 hour per day before travel to reduce jet lag."
    })


@mcp.tool()
def convert_flight_time(
    departure_time: str,
    origin: str,
    destination: str,
    flight_duration_hours: float
) -> str:
    """
    Calculate arrival time in destination timezone.
    
    Args:
        departure_time: Departure time in HH:MM format (24-hour)
        origin: Origin airport code
        destination: Destination airport code  
        flight_duration_hours: Flight duration in hours
    
    Returns:
        Arrival time in destination local time
    """
    origin = origin.upper().strip()
    destination = destination.upper().strip()
    
    origin_tz = AIRPORT_TIMEZONES.get(origin)
    dest_tz = AIRPORT_TIMEZONES.get(destination)
    
    if not origin_tz or not dest_tz:
        return json.dumps({"error": "Unknown airport code"})
    
    try:
        dep_hour, dep_min = map(int, departure_time.split(":"))
    except:
        return json.dumps({"error": "Invalid time format. Use HH:MM"})
    
    # Calculate arrival
    time_diff = dest_tz[1] - origin_tz[1]
    
    arrival_minutes = dep_min + int((flight_duration_hours % 1) * 60)
    arrival_hour = dep_hour + int(flight_duration_hours) + time_diff
    
    # Handle minute overflow
    if arrival_minutes >= 60:
        arrival_hour += 1
        arrival_minutes -= 60
    
    # Handle day changes
    day_change = 0
    while arrival_hour >= 24:
        arrival_hour -= 24
        day_change += 1
    while arrival_hour < 0:
        arrival_hour += 24
        day_change -= 1
    
    day_text = ""
    if day_change == 1:
        day_text = " (+1 day)"
    elif day_change == -1:
        day_text = " (-1 day)"
    elif day_change > 1:
        day_text = f" (+{day_change} days)"
    
    return json.dumps({
        "departure": {
            "time": f"{dep_hour:02d}:{dep_min:02d}",
            "airport": origin,
            "timezone": origin_tz[0]
        },
        "arrival": {
            "time": f"{arrival_hour:02d}:{arrival_minutes:02d}{day_text}",
            "airport": destination,
            "timezone": dest_tz[0]
        },
        "flight_duration": f"{int(flight_duration_hours)}h {int((flight_duration_hours % 1) * 60)}m",
        "time_zone_change": f"{'+' if time_diff >= 0 else ''}{time_diff} hours"
    })



# TRAVEL TIPS RESOURCE


@mcp.resource("travel://tips/{destination}")
def get_travel_tips(destination: str) -> str:
    """Get travel tips for a destination country."""
    
    tips = {
        "GB": {
            "country": "United Kingdom",
            "currency": "GBP (£)",
            "language": "English",
            "tips": [
                "Tipping 10-15% is appreciated in restaurants",
                "The Tube is the fastest way around London",
                "Pubs typically stop serving at 11 PM",
                "Drive on the left side of the road",
                "Weather is unpredictable - bring layers"
            ],
            "emergency": "999"
        },
        "AE": {
            "country": "United Arab Emirates", 
            "currency": "AED (د.إ)",
            "language": "Arabic (English widely spoken)",
            "tips": [
                "Dress modestly in public places",
                "Friday is the holy day - some businesses close",
                "Alcohol only in licensed venues",
                "Metro is excellent in Dubai",
                "Bargaining expected in souks"
            ],
            "emergency": "999"
        },
        "GE": {
            "country": "Georgia",
            "currency": "GEL (₾)",
            "language": "Georgian (English in tourist areas)",
            "tips": [
                "Try local Qvevri wines",
                "Cash preferred outside Tbilisi",
                "Very safe for tourists",
                "Amazing hiking in the Caucasus",
                "Generous hospitality culture"
            ],
            "emergency": "112"
        },
        "TR": {
            "country": "Turkey",
            "currency": "TRY (₺)",
            "language": "Turkish",
            "tips": [
                "Bargaining expected in Grand Bazaar",
                "Remove shoes in mosques",
                "Try Turkish breakfast!",
                "Istanbul Card saves money on transport",
                "Tipping 10% in restaurants"
            ],
            "emergency": "112"
        },
        "NG": {
            "country": "Nigeria",
            "currency": "NGN (₦)",
            "language": "English (official), Yoruba, Igbo, Hausa",
            "tips": [
                "Cash is king - ATMs can be unreliable",
                "Bargaining is expected in markets",
                "Traffic in Lagos is legendary - plan ahead",
                "Try jollof rice and suya",
                "Be security conscious, especially at night"
            ],
            "emergency": "112"
        },
        "RS": {
            "country": "Serbia",
            "currency": "RSD (дин)",
            "language": "Serbian",
            "tips": [
                "Very affordable destination",
                "Rakija is the national drink",
                "Belgrade nightlife is famous",
                "People are warm and hospitable",
                "Tipping 10% is standard"
            ],
            "emergency": "112"
        },
    }
    
    dest_code = destination.upper()[:2]
    if dest_code in tips:
        return json.dumps(tips[dest_code])
    
    return json.dumps({
        "message": f"No specific tips for {destination}",
        "general_tips": [
            "Always have travel insurance",
            "Keep copies of important documents",
            "Register with your embassy for long trips",
            "Learn basic phrases in local language",
            "Respect local customs and dress codes"
        ]
    })

if __name__ == "__main__":
    mcp.run()