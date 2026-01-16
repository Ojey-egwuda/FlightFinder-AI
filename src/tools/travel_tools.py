"""
FlightFinder Additional Tools
Weather, Currency and Timezone
"""

import requests
import os
from datetime import datetime
from typing import Optional, Dict, List
from dataclasses import dataclass


# WEATHER TOOL - OpenWeatherMap API (Free: 1000 calls/day)
# Get API key: https://openweathermap.org/api


@dataclass
class WeatherForecast:
    """Weather forecast data."""
    city: str
    country: str
    date: str
    temp_celsius: float
    temp_fahrenheit: float
    feels_like_celsius: float
    description: str
    icon: str
    humidity: int
    wind_speed: float
    rain_chance: float


class WeatherTool:
    """Get weather forecasts for destinations."""
    
    # City to coordinates mapping for airports
    AIRPORT_COORDS = {
        # Nigeria
        "LOS": (6.5244, 3.3792),    # Lagos
        "ABV": (9.0579, 7.4951),    # Abuja
        "PHC": (4.8470, 7.0218),    # Port Harcourt
        
        # UK
        "LHR": (51.4700, -0.4543),  # London Heathrow
        "LGW": (51.1537, -0.1821),  # London Gatwick
        "MAN": (53.3537, -2.2750),  # Manchester
        "EDI": (55.9500, -3.3725),  # Edinburgh
        "STN": (51.8850, 0.2350),   # Stansted
        "BHX": (52.4539, -1.7480),  # Birmingham
        "GLA": (55.8719, -4.4331),  # Glasgow
        
        # Balkans & Eastern Europe
        "TBS": (41.6692, 44.9547),  # Tbilisi
        "BUS": (41.6103, 41.5997),  # Batumi
        "BEG": (44.8184, 20.3091),  # Belgrade
        "SKP": (41.9617, 21.6214),  # Skopje
        "TGD": (42.3594, 19.2519),  # Podgorica
        "TIV": (42.4047, 18.7233),  # Tivat
        "TIA": (41.4147, 19.7206),  # Tirana
        "SJJ": (43.8246, 18.3315),  # Sarajevo
        
        # Turkey
        "IST": (41.2753, 28.7519),  # Istanbul
        "SAW": (40.8986, 29.3092),  # Sabiha Gokcen
        "AYT": (36.8987, 30.8005),  # Antalya
        "ADB": (38.2924, 27.1570),  # Izmir
        
        # Middle East
        "DXB": (25.2532, 55.3657),  # Dubai
        "AUH": (24.4330, 54.6511),  # Abu Dhabi
        "DOH": (25.2731, 51.6081),  # Doha
        "SHJ": (25.3286, 55.5172),  # Sharjah
        
        # Asia
        "SIN": (1.3644, 103.9915),  # Singapore
        "HND": (35.5494, 139.7798), # Tokyo Haneda
        "NRT": (35.7720, 140.3929), # Tokyo Narita
        "KIX": (34.4273, 135.2440), # Osaka
        "PEK": (40.0799, 116.6031), # Beijing
        "PVG": (31.1443, 121.8083), # Shanghai
        "HKG": (22.3080, 113.9185), # Hong Kong
        "CAN": (23.3924, 113.2988), # Guangzhou
        
        # Europe
        "CDG": (49.0097, 2.5479),   # Paris CDG
        "ORY": (48.7262, 2.3652),   # Paris Orly
        "AMS": (52.3105, 4.7683),   # Amsterdam
        "FCO": (41.8003, 12.2389),  # Rome
        "MXP": (45.6306, 8.7281),   # Milan
        "MAD": (40.4983, -3.5676),  # Madrid
        "BCN": (41.2971, 2.0785),   # Barcelona
        "FRA": (50.0379, 8.5622),   # Frankfurt
        "MUC": (48.3538, 11.7861),  # Munich
        "BER": (52.3667, 13.5033),  # Berlin
        
        # Africa
        "CMN": (33.3675, -7.5898),  # Casablanca
        "RAK": (31.6069, -8.0363),  # Marrakech
        "CAI": (30.1219, 31.4056),  # Cairo
        "JNB": (-26.1392, 28.2460), # Johannesburg
        "CPT": (-33.9715, 18.6021), # Cape Town
        "ADD": (8.9779, 38.7993),   # Addis Ababa
        
        # Americas
        "JFK": (40.6413, -73.7781), # New York JFK
        "EWR": (40.6895, -74.1745), # Newark
        "LAX": (33.9416, -118.4085),# Los Angeles
        "MIA": (25.7959, -80.2870), # Miami
        "ATL": (33.6407, -84.4277), # Atlanta
        "YYZ": (43.6777, -79.6248), # Toronto
        "YVR": (49.1967, -123.1815),# Vancouver
        
        # Caribbean
        "PUJ": (18.5675, -68.3634), # Punta Cana
        "SDQ": (18.4297, -69.6689), # Santo Domingo
        "SXM": (18.0410, -63.1089), # Sint Maarten
        "ANU": (17.1367, -61.7927), # Antigua
        "PLS": (21.7736, -72.2659), # Providenciales
    }
    
    WEATHER_ICONS = {
        "01d": "☀️", "01n": "🌙",  # Clear
        "02d": "⛅", "02n": "☁️",  # Few clouds
        "03d": "☁️", "03n": "☁️",  # Scattered clouds
        "04d": "☁️", "04n": "☁️",  # Broken clouds
        "09d": "🌧️", "09n": "🌧️",  # Shower rain
        "10d": "🌦️", "10n": "🌧️",  # Rain
        "11d": "⛈️", "11n": "⛈️",  # Thunderstorm
        "13d": "❄️", "13n": "❄️",  # Snow
        "50d": "🌫️", "50n": "🌫️",  # Mist
    }
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENWEATHER_API_KEY")
        self.base_url = "https://api.openweathermap.org/data/2.5"
    
    def get_weather(self, airport_code: str) -> Optional[WeatherForecast]:
        """Get current weather for an airport location."""
        if not self.api_key:
            return None
        
        coords = self.AIRPORT_COORDS.get(airport_code.upper())
        if not coords:
            return None
        
        lat, lon = coords
        
        try:
            response = requests.get(
                f"{self.base_url}/weather",
                params={
                    "lat": lat,
                    "lon": lon,
                    "appid": self.api_key,
                    "units": "metric"
                },
                timeout=10
            )
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            
            return WeatherForecast(
                city=data.get("name", "Unknown"),
                country=data.get("sys", {}).get("country", ""),
                date=datetime.now().strftime("%Y-%m-%d"),
                temp_celsius=data["main"]["temp"],
                temp_fahrenheit=data["main"]["temp"] * 9/5 + 32,
                feels_like_celsius=data["main"]["feels_like"],
                description=data["weather"][0]["description"].title(),
                icon=self.WEATHER_ICONS.get(data["weather"][0]["icon"], "🌡️"),
                humidity=data["main"]["humidity"],
                wind_speed=data["wind"]["speed"],
                rain_chance=data.get("rain", {}).get("1h", 0)
            )
            
        except Exception as e:
            print(f"Weather API error: {e}")
            return None
    
    def get_forecast(self, airport_code: str, days: int = 5) -> List[WeatherForecast]:
        """Get weather forecast for next N days."""
        if not self.api_key:
            return []
        
        coords = self.AIRPORT_COORDS.get(airport_code.upper())
        if not coords:
            return []
        
        lat, lon = coords
        
        try:
            response = requests.get(
                f"{self.base_url}/forecast",
                params={
                    "lat": lat,
                    "lon": lon,
                    "appid": self.api_key,
                    "units": "metric",
                    "cnt": days * 8  # 8 data points per day (3-hour intervals)
                },
                timeout=10
            )
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            forecasts = []
            seen_dates = set()
            
            for item in data.get("list", []):
                date = item["dt_txt"].split(" ")[0]
                if date in seen_dates:
                    continue
                seen_dates.add(date)
                
                forecasts.append(WeatherForecast(
                    city=data["city"]["name"],
                    country=data["city"]["country"],
                    date=date,
                    temp_celsius=item["main"]["temp"],
                    temp_fahrenheit=item["main"]["temp"] * 9/5 + 32,
                    feels_like_celsius=item["main"]["feels_like"],
                    description=item["weather"][0]["description"].title(),
                    icon=self.WEATHER_ICONS.get(item["weather"][0]["icon"], "🌡️"),
                    humidity=item["main"]["humidity"],
                    wind_speed=item["wind"]["speed"],
                    rain_chance=item.get("pop", 0) * 100
                ))
            
            return forecasts[:days]
            
        except Exception as e:
            print(f"Weather API error: {e}")
            return []



# CURRENCY CONVERTER - ExchangeRate-API (Free: 1500 calls/month)
# Get API key: https://www.exchangerate-api.com/

class CurrencyConverter:
    """Convert prices between currencies."""
    
    # Common currency symbols
    SYMBOLS = {
        "USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥",
        "NGN": "₦", "AED": "د.إ", "QAR": "ر.ق", "SGD": "S$",
        "TRY": "₺", "MAD": "د.م.", "CNY": "¥", "CAD": "C$",
        "INR": "₹", "ZAR": "R", "EGP": "E£", "GEL": "₾",
        "RSD": "дин", "MKD": "ден", "ALL": "L", "BAM": "KM",
        "DOP": "RD$", "XCD": "EC$", "ANG": "ƒ",
    }
    
    # Fallback rates (updated periodically)
    FALLBACK_RATES = {
        "USD": 1.0,
        "EUR": 0.92,
        "GBP": 0.79,
        "NGN": 1550.0,
        "AED": 3.67,
        "QAR": 3.64,
        "JPY": 149.5,
        "SGD": 1.34,
        "TRY": 30.5,
        "CNY": 7.24,
        "CAD": 1.36,
        "INR": 83.1,
        "ZAR": 18.9,
        "MAD": 10.1,
    }
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("EXCHANGERATE_API_KEY")
        self.base_url = "https://v6.exchangerate-api.com/v6"
        self._rates_cache = {}
        self._cache_time = None
    
    def get_rate(self, from_currency: str, to_currency: str) -> float:
        """Get exchange rate between two currencies."""
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()
        
        if from_currency == to_currency:
            return 1.0
        
        # Try API first
        if self.api_key:
            try:
                response = requests.get(
                    f"{self.base_url}/{self.api_key}/pair/{from_currency}/{to_currency}",
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("result") == "success":
                        return data["conversion_rate"]
            except:
                pass
        
        # Fallback to stored rates
        if from_currency in self.FALLBACK_RATES and to_currency in self.FALLBACK_RATES:
            from_usd = self.FALLBACK_RATES[from_currency]
            to_usd = self.FALLBACK_RATES[to_currency]
            return to_usd / from_usd
        
        return 1.0
    
    def convert(self, amount: float, from_currency: str, to_currency: str) -> Dict:
        """Convert amount between currencies."""
        rate = self.get_rate(from_currency, to_currency)
        converted = amount * rate
        
        from_symbol = self.SYMBOLS.get(from_currency.upper(), from_currency)
        to_symbol = self.SYMBOLS.get(to_currency.upper(), to_currency)
        
        return {
            "original": f"{from_symbol}{amount:,.2f}",
            "converted": f"{to_symbol}{converted:,.2f}",
            "rate": rate,
            "from_currency": from_currency.upper(),
            "to_currency": to_currency.upper()
        }
    
    def get_symbol(self, currency: str) -> str:
        """Get currency symbol."""
        return self.SYMBOLS.get(currency.upper(), currency)

# TIME ZONE CALCULATOR

class TimeZoneCalculator:
    """Calculate time differences between airports."""
    
    # Airport to UTC offset mapping
    TIMEZONES = {
        # Nigeria (WAT = UTC+1)
        "LOS": 1, "ABV": 1, "PHC": 1,
        
        # UK (GMT/BST = UTC+0/+1)
        "LHR": 0, "LGW": 0, "STN": 0, "MAN": 0, "EDI": 0, "BHX": 0, "GLA": 0,
        
        # Europe
        "CDG": 1, "ORY": 1,  # France (CET)
        "AMS": 1, "RTM": 1,   # Netherlands
        "FCO": 1, "MXP": 1,   # Italy
        "MAD": 1, "BCN": 1,   # Spain
        "FRA": 1, "MUC": 1,   # Germany
        
        # Balkans
        "TBS": 4,  # Georgia (GET)
        "BEG": 1,  # Serbia (CET)
        "SKP": 1,  # North Macedonia
        "TGD": 1,  # Montenegro
        "TIA": 1,  # Albania
        "SJJ": 1,  # Bosnia
        
        # Turkey
        "IST": 3, "SAW": 3, "AYT": 3,
        
        # Middle East
        "DXB": 4, "AUH": 4,  # UAE
        "DOH": 3,  # Qatar
        
        # Asia
        "SIN": 8,  # Singapore
        "HND": 9, "NRT": 9, "KIX": 9,  # Japan
        "PEK": 8, "PVG": 8, "HKG": 8,  # China
        
        # Africa
        "CMN": 1, "RAK": 1,  # Morocco
        "CAI": 2,  # Egypt
        "JNB": 2, "CPT": 2,  # South Africa
        "ADD": 3,  # Ethiopia
        
        # Americas
        "JFK": -5, "EWR": -5,  # New York
        "LAX": -8,  # Los Angeles
        "MIA": -5,  # Miami
        "ATL": -5,  # Atlanta
        "YYZ": -5,  # Toronto
        "YVR": -8,  # Vancouver
        
        # Caribbean
        "PUJ": -4, "SDQ": -4,  # Dominican Republic
        "SXM": -4,  # Sint Maarten
        "ANU": -4,  # Antigua
        "PLS": -5,  # Turks & Caicos
    }
    
    def get_time_difference(self, origin: str, destination: str) -> Dict:
        """Get time difference between airports."""
        origin = origin.upper()
        destination = destination.upper()
        
        origin_offset = self.TIMEZONES.get(origin)
        dest_offset = self.TIMEZONES.get(destination)
        
        if origin_offset is None or dest_offset is None:
            return {"error": "Airport timezone not found"}
        
        diff = dest_offset - origin_offset
        
        if diff == 0:
            diff_text = "Same timezone"
        elif diff > 0:
            diff_text = f"+{diff} hours ahead"
        else:
            diff_text = f"{diff} hours behind"
        
        return {
            "origin": origin,
            "origin_utc_offset": origin_offset,
            "destination": destination,
            "destination_utc_offset": dest_offset,
            "difference_hours": diff,
            "difference_text": diff_text
        }
    
    def convert_time(self, time_str: str, origin: str, destination: str) -> str:
        """Convert a time from origin to destination timezone."""
        result = self.get_time_difference(origin, destination)
        
        if "error" in result:
            return time_str
        
        try:
            # Parse time (HH:MM format)
            hour, minute = map(int, time_str.split(":"))
            
            # Add difference
            new_hour = hour + result["difference_hours"]
            
            # Handle day wrap
            day_change = ""
            if new_hour >= 24:
                new_hour -= 24
                day_change = " (+1 day)"
            elif new_hour < 0:
                new_hour += 24
                day_change = " (-1 day)"
            
            return f"{new_hour:02d}:{minute:02d}{day_change}"
            
        except:
            return time_str



# EXPORT ALL TOOLS

__all__ = [
    "WeatherTool",
    "WeatherForecast", 
    "CurrencyConverter",
    "TimeZoneCalculator",
]