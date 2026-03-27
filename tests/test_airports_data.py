"""
Tests for the centralized airport data module.
Run: pytest tests/test_airports_data.py -v
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.airports import (
    AIRPORT_DATA,
    AIRPORTS,
    AIRPORT_COORDS,
    AIRPORT_TIMEZONES,
    AIRPORT_TIMEZONES_NAMED,
    AIRPORT_COORDS_NAMED,
)


class TestAirportData:
    def test_all_entries_have_required_fields(self):
        required = {"name", "city", "country", "lat", "lon", "timezone", "utc_offset"}
        for code, entry in AIRPORT_DATA.items():
            missing = required - set(entry.keys())
            assert not missing, f"{code} missing fields: {missing}"

    def test_coordinates_are_valid_floats(self):
        for code, entry in AIRPORT_DATA.items():
            assert isinstance(entry["lat"], float), f"{code} lat is not float"
            assert isinstance(entry["lon"], float), f"{code} lon is not float"
            assert -90 <= entry["lat"] <= 90, f"{code} lat out of range"
            assert -180 <= entry["lon"] <= 180, f"{code} lon out of range"

    def test_utc_offsets_are_plausible(self):
        for code, entry in AIRPORT_DATA.items():
            assert -12 <= entry["utc_offset"] <= 14, f"{code} utc_offset out of range"

    def test_iata_codes_are_three_uppercase_letters(self):
        for code in AIRPORT_DATA:
            assert len(code) == 3 and code.isupper(), f"Invalid IATA code: {code}"


class TestDerivedViews:
    """Verify the derived dicts are consistent with AIRPORT_DATA."""

    def test_airports_keys_match(self):
        assert set(AIRPORTS.keys()) == set(AIRPORT_DATA.keys())

    def test_airports_has_correct_fields(self):
        for code, info in AIRPORTS.items():
            assert set(info.keys()) == {"name", "city", "country"}
            assert info["name"] == AIRPORT_DATA[code]["name"]

    def test_airport_coords_subset_of_airport_data(self):
        for code in AIRPORT_COORDS:
            assert code in AIRPORT_DATA

    def test_airport_coords_values_match_source(self):
        for code, (lat, lon) in AIRPORT_COORDS.items():
            assert lat == AIRPORT_DATA[code]["lat"]
            assert lon == AIRPORT_DATA[code]["lon"]

    def test_airport_timezones_values_match_source(self):
        for code, offset in AIRPORT_TIMEZONES.items():
            assert offset == AIRPORT_DATA[code]["utc_offset"]

    def test_airport_timezones_named_values_match_source(self):
        for code, (tz_name, offset) in AIRPORT_TIMEZONES_NAMED.items():
            assert tz_name == AIRPORT_DATA[code]["timezone"]
            assert offset == AIRPORT_DATA[code]["utc_offset"]

    def test_airport_coords_named_values_match_source(self):
        for code, (lat, lon, city) in AIRPORT_COORDS_NAMED.items():
            assert lat == AIRPORT_DATA[code]["lat"]
            assert lon == AIRPORT_DATA[code]["lon"]
            assert city == AIRPORT_DATA[code]["city"]

    def test_key_airports_present(self):
        """Spot-check that well-known hubs are in every derived view."""
        hubs = ["LOS", "LHR", "DXB", "JFK", "SIN"]
        for hub in hubs:
            assert hub in AIRPORTS, f"{hub} missing from AIRPORTS"
            assert hub in AIRPORT_COORDS, f"{hub} missing from AIRPORT_COORDS"
            assert hub in AIRPORT_TIMEZONES, f"{hub} missing from AIRPORT_TIMEZONES"
