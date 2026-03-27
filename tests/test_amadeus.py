"""
Unit tests for AmadeusAPI — all HTTP calls are mocked.
Run: pytest tests/test_amadeus.py -v
"""

import pytest
import sys
import os
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.apis.amadeus import AmadeusAPI, resolve_airport, get_airport_info, AIRPORTS


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def api():
    """AmadeusAPI with sandbox mode, fake credentials, and isolated (empty) cache."""
    with patch.dict(os.environ, {"AMADEUS_CLIENT_ID": "test_id", "AMADEUS_CLIENT_SECRET": "test_secret"}), \
         patch("src.apis.amadeus._load_persistent_cache", return_value={}), \
         patch("src.apis.amadeus._save_persistent_cache"):
        return AmadeusAPI(sandbox=True)


def _auth_response():
    mock = MagicMock()
    mock.status_code = 200
    mock.json.return_value = {"access_token": "fake_token", "expires_in": 1799}
    return mock


def _flight_response():
    """Minimal valid Amadeus v2 flight-offers response."""
    mock = MagicMock()
    mock.status_code = 200
    mock.json.return_value = {
        "data": [
            {
                "id": "1",
                "price": {"total": "450.00", "currency": "GBP"},
                "itineraries": [
                    {
                        "duration": "PT6H30M",
                        "segments": [
                            {
                                "departure": {"iataCode": "LOS", "at": "2026-05-01T08:00:00", "terminal": None},
                                "arrival": {"iataCode": "LHR", "at": "2026-05-01T14:30:00", "terminal": "2"},
                                "carrierCode": "BA",
                                "number": "75",
                                "aircraft": {"code": "787"},
                                "duration": "PT6H30M",
                            }
                        ],
                    }
                ],
            }
        ],
        "dictionaries": {
            "carriers": {"BA": "British Airways"},
            "aircraft": {"787": "Boeing 787"},
        },
    }
    return mock


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

class TestAuthentication:
    def test_authenticates_and_caches_token(self, api):
        with patch("requests.post", return_value=_auth_response()) as mock_post:
            api._authenticate()
            api._authenticate()  # second call should use cached token
            assert mock_post.call_count == 1  # only one real HTTP call

    def test_re_authenticates_when_token_expired(self, api):
        with patch("requests.post", return_value=_auth_response()) as mock_post:
            api._authenticate()
            api.token_expiry = datetime.now() - timedelta(seconds=1)  # force expiry
            api._authenticate()
            assert mock_post.call_count == 2

    def test_raises_on_auth_failure(self, api):
        error_mock = MagicMock()
        error_mock.status_code = 401
        error_mock.text = "Unauthorized"
        with patch("requests.post", return_value=error_mock):
            with pytest.raises(Exception, match="Authentication failed"):
                api._authenticate()


# ---------------------------------------------------------------------------
# search_flights
# ---------------------------------------------------------------------------

class TestSearchFlights:
    def test_returns_parsed_offers(self, api):
        with patch("requests.post", return_value=_auth_response()), \
             patch("requests.get", return_value=_flight_response()):
            result = api.search_flights("LOS", "LHR", "2026-05-01")

        assert result["error"] is False
        assert result["total_results"] == 1
        offer = result["offers"][0]
        assert offer["price"]["total"] == 450.0
        assert offer["itineraries"][0]["duration"] == "PT6H30M"
        assert offer["itineraries"][0]["stops"] == 0

    def test_returns_error_dict_on_api_failure(self, api):
        bad_response = MagicMock()
        bad_response.status_code = 500
        bad_response.text = "Internal Server Error"
        with patch("requests.post", return_value=_auth_response()), \
             patch("requests.get", return_value=bad_response), \
             patch("time.sleep"):  # skip retry delay
            result = api.search_flights("LOS", "LHR", "2026-05-01")

        assert result["error"] is True
        assert result["status_code"] == 500

    def test_caches_results(self, api):
        with patch("requests.post", return_value=_auth_response()), \
             patch("requests.get", return_value=_flight_response()) as mock_get:
            api.search_flights("LOS", "LHR", "2026-05-01")
            api.search_flights("LOS", "LHR", "2026-05-01")  # same params → cache hit
            assert mock_get.call_count == 1  # only one real GET

    def test_different_params_bypass_cache(self, api):
        with patch("requests.post", return_value=_auth_response()), \
             patch("requests.get", return_value=_flight_response()) as mock_get:
            api.search_flights("LOS", "LHR", "2026-05-01")
            api.search_flights("LOS", "LHR", "2026-06-01")  # different date
            assert mock_get.call_count == 2

    def test_nonstop_param_passed_to_api(self, api):
        with patch("requests.post", return_value=_auth_response()), \
             patch("requests.get", return_value=_flight_response()) as mock_get:
            api.search_flights("LOS", "LHR", "2026-05-01", nonstop_only=True)
            _, kwargs = mock_get.call_args
            assert kwargs["params"]["nonStop"] == "true"


# ---------------------------------------------------------------------------
# Airport helpers
# ---------------------------------------------------------------------------

class TestResolveAirport:
    def test_direct_iata_code(self):
        assert resolve_airport("LOS") == "LOS"

    def test_lowercase_iata_code(self):
        assert resolve_airport("los") == "LOS"

    def test_city_name(self):
        assert resolve_airport("Lagos") == "LOS"

    def test_partial_city_name(self):
        result = resolve_airport("London")
        assert result in ("LHR", "LGW", "STN", "LTN")  # any London airport

    def test_airport_name_substring(self):
        assert resolve_airport("Heathrow") == "LHR"

    def test_unknown_returns_none(self):
        assert resolve_airport("XXX_UNKNOWN_CITY") is None


class TestGetAirportInfo:
    def test_known_code_returns_dict(self):
        info = get_airport_info("LHR")
        assert info["city"] == "London"
        assert info["country"] == "UK"

    def test_unknown_code_returns_fallback(self):
        info = get_airport_info("ZZZ")
        assert info["city"] == "Unknown"

    def test_lowercase_code_normalised(self):
        assert get_airport_info("lhr") == get_airport_info("LHR")


class TestAirportsData:
    def test_all_entries_have_required_keys(self):
        for code, info in AIRPORTS.items():
            assert "name" in info, f"{code} missing 'name'"
            assert "city" in info, f"{code} missing 'city'"
            assert "country" in info, f"{code} missing 'country'"

    def test_key_matches_iata_format(self):
        for code in AIRPORTS:
            assert code.isupper() and len(code) == 3, f"Invalid IATA code: {code}"
