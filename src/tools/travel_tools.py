"""
FlightFinder Additional Tools
Weather, Currency and Timezone
"""

import logging
import requests
import os
from datetime import datetime
from typing import Optional, Dict, List
from dataclasses import dataclass

from src.data.airports import AIRPORT_COORDS as _AIRPORT_COORDS, AIRPORT_TIMEZONES as _AIRPORT_TIMEZONES

logger = logging.getLogger(__name__)


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

    AIRPORT_COORDS = _AIRPORT_COORDS
    
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
            logger.error("Weather API error: %s", e)
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
            logger.error("Weather API error: %s", e)
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

    TIMEZONES = _AIRPORT_TIMEZONES
    
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