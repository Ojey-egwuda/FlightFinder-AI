"""
Unit tests for WeatherTool, CurrencyConverter, and TimeZoneCalculator.
All external HTTP calls are mocked.
Run: pytest tests/test_travel_tools.py -v
"""

import pytest
import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tools.travel_tools import WeatherTool, CurrencyConverter, TimeZoneCalculator, WeatherForecast


# ===========================================================================
# WeatherTool
# ===========================================================================

def _weather_api_response(temp=22.5, humidity=60, description="Clear sky", icon="01d"):
    mock = MagicMock()
    mock.status_code = 200
    mock.json.return_value = {
        "name": "Lagos",
        "sys": {"country": "NG"},
        "main": {"temp": temp, "feels_like": temp - 2, "humidity": humidity},
        "weather": [{"description": description, "icon": icon}],
        "wind": {"speed": 3.5},
    }
    return mock


class TestWeatherTool:
    def setup_method(self):
        self.tool = WeatherTool(api_key="fake_key")

    def test_get_weather_returns_forecast(self):
        with patch("requests.get", return_value=_weather_api_response()):
            result = self.tool.get_weather("LOS")
        assert isinstance(result, WeatherForecast)
        assert result.city == "Lagos"
        assert result.temp_celsius == 22.5

    def test_fahrenheit_conversion(self):
        with patch("requests.get", return_value=_weather_api_response(temp=0)):
            result = self.tool.get_weather("LOS")
        assert result.temp_fahrenheit == pytest.approx(32.0)

    def test_unknown_airport_returns_none(self):
        result = self.tool.get_weather("ZZZ")
        assert result is None

    def test_no_api_key_returns_none(self):
        tool = WeatherTool(api_key=None)
        with patch.dict(os.environ, {}, clear=True):
            result = tool.get_weather("LHR")
        assert result is None

    def test_api_error_returns_none(self):
        bad = MagicMock()
        bad.status_code = 500
        with patch("requests.get", return_value=bad):
            result = self.tool.get_weather("LHR")
        assert result is None

    def test_network_exception_returns_none(self):
        with patch("requests.get", side_effect=Exception("Network error")):
            result = self.tool.get_weather("LHR")
        assert result is None

    def test_weather_icon_mapped(self):
        with patch("requests.get", return_value=_weather_api_response(icon="01d")):
            result = self.tool.get_weather("DXB")
        assert result.icon == "☀️"

    def test_unknown_icon_falls_back(self):
        with patch("requests.get", return_value=_weather_api_response(icon="99x")):
            result = self.tool.get_weather("DXB")
        assert result.icon == "🌡️"

    def test_get_forecast_returns_list(self):
        forecast_response = MagicMock()
        forecast_response.status_code = 200
        forecast_response.json.return_value = {
            "city": {"name": "London", "country": "GB"},
            "list": [
                {
                    "dt_txt": "2026-05-01 12:00:00",
                    "main": {"temp": 18.0, "feels_like": 16.0, "humidity": 70},
                    "weather": [{"description": "cloudy", "icon": "04d"}],
                    "wind": {"speed": 5.0},
                    "pop": 0.2,
                },
                {
                    "dt_txt": "2026-05-02 12:00:00",
                    "main": {"temp": 20.0, "feels_like": 18.0, "humidity": 65},
                    "weather": [{"description": "sunny", "icon": "01d"}],
                    "wind": {"speed": 3.0},
                    "pop": 0.0,
                },
            ],
        }
        with patch("requests.get", return_value=forecast_response):
            forecasts = self.tool.get_forecast("LHR", days=2)
        assert len(forecasts) == 2
        assert forecasts[0].city == "London"
        assert forecasts[0].rain_chance == pytest.approx(20.0)


# ===========================================================================
# CurrencyConverter
# ===========================================================================

class TestCurrencyConverter:
    def setup_method(self):
        self.converter = CurrencyConverter(api_key=None)  # fallback rates only

    def test_same_currency_is_1(self):
        assert self.converter.get_rate("GBP", "GBP") == 1.0

    def test_fallback_rate_gbp_to_usd(self):
        rate = self.converter.get_rate("GBP", "USD")
        # GBP is 0.79 per USD → 1 GBP = 1/0.79 USD ≈ 1.266
        assert rate == pytest.approx(1 / 0.79, rel=0.01)

    def test_convert_returns_dict_with_all_keys(self):
        result = self.converter.convert(100.0, "GBP", "USD")
        assert set(result.keys()) == {"original", "converted", "rate", "from_currency", "to_currency"}

    def test_convert_amount_correct(self):
        rate = self.converter.get_rate("USD", "NGN")
        result = self.converter.convert(10.0, "USD", "NGN")
        expected = 10.0 * rate
        # extract numeric value from "₦xx,xxx.xx"
        converted_amount = float(result["converted"].replace("₦", "").replace(",", ""))
        assert converted_amount == pytest.approx(expected, rel=0.01)

    def test_currency_symbol_returned(self):
        symbol = self.converter.get_symbol("GBP")
        assert symbol == "£"

    def test_unknown_currency_returns_code_as_symbol(self):
        symbol = self.converter.get_symbol("XYZ")
        assert symbol == "XYZ"

    def test_live_api_used_when_key_present(self):
        api_response = MagicMock()
        api_response.status_code = 200
        api_response.json.return_value = {"result": "success", "conversion_rate": 1.25}
        converter = CurrencyConverter(api_key="fake_key")
        with patch("requests.get", return_value=api_response):
            rate = converter.get_rate("GBP", "USD")
        assert rate == 1.25

    def test_falls_back_to_stored_rates_when_api_fails(self):
        api_response = MagicMock()
        api_response.status_code = 500
        converter = CurrencyConverter(api_key="fake_key")
        with patch("requests.get", return_value=api_response):
            rate = converter.get_rate("GBP", "USD")
        # Should still return a sensible rate from fallback
        assert rate > 0


# ===========================================================================
# TimeZoneCalculator
# ===========================================================================

class TestTimeZoneCalculator:
    def setup_method(self):
        self.tz = TimeZoneCalculator()

    def test_same_timezone(self):
        result = self.tz.get_time_difference("LHR", "LGW")  # both UTC+0
        assert result["difference_hours"] == 0
        assert "Same" in result["difference_text"]

    def test_destination_ahead(self):
        result = self.tz.get_time_difference("LHR", "DXB")  # UTC+0 vs UTC+4
        assert result["difference_hours"] == 4
        assert "ahead" in result["difference_text"]

    def test_destination_behind(self):
        result = self.tz.get_time_difference("LHR", "JFK")  # UTC+0 vs UTC-5
        assert result["difference_hours"] == -5
        assert "behind" in result["difference_text"]

    def test_unknown_airport_returns_error(self):
        result = self.tz.get_time_difference("ZZZ", "LHR")
        assert "error" in result

    def test_convert_time_basic(self):
        # Lagos (UTC+1) to Dubai (UTC+4): +3 hours
        converted = self.tz.convert_time("10:00", "LOS", "DXB")
        assert converted == "13:00"

    def test_convert_time_crosses_midnight_forward(self):
        converted = self.tz.convert_time("22:00", "LHR", "DXB")  # +4h
        assert "02:00" in converted
        assert "+1 day" in converted

    def test_convert_time_crosses_midnight_backward(self):
        converted = self.tz.convert_time("02:00", "DXB", "JFK")  # -9h
        assert "17:00" in converted
        assert "-1 day" in converted

    def test_convert_time_invalid_format_returns_input(self):
        result = self.tz.convert_time("not-a-time", "LHR", "DXB")
        assert result == "not-a-time"

    def test_los_to_lhr_offset(self):
        # Nigeria WAT=+1, UK GMT=0 → LHR is 1h behind LOS
        result = self.tz.get_time_difference("LOS", "LHR")
        assert result["difference_hours"] == -1
