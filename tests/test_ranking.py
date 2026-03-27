"""
Unit tests for FlightRankingAgent.
Run: pytest tests/test_ranking.py -v
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.ranking import FlightRankingAgent, FlightPreferences


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_flight(price=500, duration="PT10H0M", stops=0, dep_time="2026-05-01T08:00:00",
                carrier_code="BA"):
    """Return a minimal flight dict in the shape produced by AmadeusAPI."""
    return {
        "price": {"total": price, "currency": "GBP"},
        "itineraries": [
            {
                "duration": duration,
                "stops": stops,
                "segments": [
                    {
                        "departure": {"airport": "LOS", "time": dep_time, "terminal": None},
                        "arrival": {"airport": "LHR", "time": None, "terminal": None},
                        "carrier": {"code": carrier_code, "name": carrier_code},
                        "flight_number": f"{carrier_code}100",
                        "aircraft": "Boeing 787",
                        "duration": duration,
                    }
                ],
            }
        ],
    }


# ---------------------------------------------------------------------------
# parse_duration
# ---------------------------------------------------------------------------

class TestParseDuration:
    def setup_method(self):
        self.ranker = FlightRankingAgent()

    def test_hours_and_minutes(self):
        assert self.ranker.parse_duration("PT10H30M") == 10.5

    def test_hours_only(self):
        assert self.ranker.parse_duration("PT6H") == 6.0

    def test_minutes_only(self):
        assert self.ranker.parse_duration("PT45M") == pytest.approx(0.75)

    def test_empty_string(self):
        assert self.ranker.parse_duration("") == 0

    def test_none(self):
        assert self.ranker.parse_duration(None) == 0


# ---------------------------------------------------------------------------
# score_price
# ---------------------------------------------------------------------------

class TestScorePrice:
    def setup_method(self):
        self.ranker = FlightRankingAgent()

    def test_at_minimum_is_100(self):
        assert self.ranker.score_price(FlightRankingAgent.PRICE_MIN) == 100

    def test_below_minimum_is_100(self):
        assert self.ranker.score_price(100) == 100

    def test_at_maximum_is_0(self):
        assert self.ranker.score_price(FlightRankingAgent.PRICE_MAX) == 0

    def test_above_maximum_is_0(self):
        assert self.ranker.score_price(2000) == 0

    def test_midpoint(self):
        mid = (FlightRankingAgent.PRICE_MIN + FlightRankingAgent.PRICE_MAX) / 2
        assert self.ranker.score_price(mid) == pytest.approx(50.0)

    def test_in_range(self):
        score = self.ranker.score_price(800)
        assert 0 < score < 100


# ---------------------------------------------------------------------------
# score_duration
# ---------------------------------------------------------------------------

class TestScoreDuration:
    def setup_method(self):
        self.ranker = FlightRankingAgent()

    def test_at_minimum_is_100(self):
        assert self.ranker.score_duration(FlightRankingAgent.DURATION_MIN_HOURS) == 100

    def test_below_minimum_is_100(self):
        assert self.ranker.score_duration(1.0) == 100

    def test_at_maximum_is_0(self):
        assert self.ranker.score_duration(FlightRankingAgent.DURATION_MAX_HOURS) == 0

    def test_above_maximum_is_0(self):
        assert self.ranker.score_duration(30.0) == 0

    def test_in_range(self):
        score = self.ranker.score_duration(12.0)
        assert 0 < score < 100


# ---------------------------------------------------------------------------
# score_stops
# ---------------------------------------------------------------------------

class TestScoreStops:
    def setup_method(self):
        self.ranker = FlightRankingAgent()

    def test_direct_is_100(self):
        assert self.ranker.score_stops(0) == 100

    def test_one_stop(self):
        assert self.ranker.score_stops(1) == 70

    def test_two_stops(self):
        assert self.ranker.score_stops(2) == 40

    def test_three_or_more_stops(self):
        assert self.ranker.score_stops(3) == 20
        assert self.ranker.score_stops(5) == 20


# ---------------------------------------------------------------------------
# score_departure_time
# ---------------------------------------------------------------------------

class TestScoreDepartureTime:
    def setup_method(self):
        self.ranker = FlightRankingAgent(FlightPreferences(preferred_departure_time="morning"))

    def test_morning_preference_in_window(self):
        score = self.ranker.score_departure_time("2026-05-01T08:00:00")
        assert score == 100

    def test_morning_preference_outside_window(self):
        score = self.ranker.score_departure_time("2026-05-01T19:00:00")
        assert score == 50

    def test_any_preference_returns_neutral(self):
        ranker = FlightRankingAgent(FlightPreferences(preferred_departure_time="any"))
        assert ranker.score_departure_time("2026-05-01T03:00:00") == 70

    def test_invalid_time_returns_default(self):
        score = self.ranker.score_departure_time("not-a-date")
        assert score == 70


# ---------------------------------------------------------------------------
# score_flight (composite)
# ---------------------------------------------------------------------------

class TestScoreFlight:
    def setup_method(self):
        self.ranker = FlightRankingAgent()

    def test_returns_all_score_keys(self):
        result = self.ranker.score_flight(make_flight())
        assert set(result["scores"].keys()) == {"price", "duration", "stops", "timing", "airline"}
        assert "composite_score" in result

    def test_composite_score_in_range(self):
        result = self.ranker.score_flight(make_flight())
        assert 0 <= result["composite_score"] <= 100

    def test_direct_flight_scores_higher_than_two_stops(self):
        direct = self.ranker.score_flight(make_flight(stops=0))
        two_stop = self.ranker.score_flight(make_flight(stops=2))
        assert direct["composite_score"] > two_stop["composite_score"]

    def test_cheaper_flight_scores_higher_on_price(self):
        cheap = self.ranker.score_flight(make_flight(price=350))
        expensive = self.ranker.score_flight(make_flight(price=1400))
        assert cheap["scores"]["price"] > expensive["scores"]["price"]

    def test_preferred_airline_boosts_score(self):
        prefs = FlightPreferences(preferred_airlines=["EK"])
        ranker = FlightRankingAgent(prefs)
        preferred = ranker.score_flight(make_flight(carrier_code="EK"))
        other = ranker.score_flight(make_flight(carrier_code="FR"))
        assert preferred["scores"]["airline"] > other["scores"]["airline"]

    def test_avoided_airline_lowers_score(self):
        prefs = FlightPreferences(avoid_airlines=["FR"])
        ranker = FlightRankingAgent(prefs)
        avoided = ranker.score_flight(make_flight(carrier_code="FR"))
        other = ranker.score_flight(make_flight(carrier_code="BA"))
        assert avoided["scores"]["airline"] < other["scores"]["airline"]


# ---------------------------------------------------------------------------
# rank_flights
# ---------------------------------------------------------------------------

class TestRankFlights:
    def setup_method(self):
        self.ranker = FlightRankingAgent()

    def test_returns_sorted_by_score(self):
        flights = [
            make_flight(price=1400, stops=2),  # bad
            make_flight(price=350, stops=0),   # good
            make_flight(price=800, stops=1),   # medium
        ]
        ranked = self.ranker.rank_flights(flights)
        scores = [f["ranking"]["composite_score"] for f in ranked]
        assert scores == sorted(scores, reverse=True)

    def test_positions_are_assigned(self):
        flights = [make_flight(price=p) for p in [300, 700, 1200]]
        ranked = self.ranker.rank_flights(flights)
        positions = [f["ranking"]["position"] for f in ranked]
        assert sorted(positions) == [1, 2, 3]

    def test_empty_list(self):
        assert self.ranker.rank_flights([]) == []

    def test_single_flight(self):
        ranked = self.ranker.rank_flights([make_flight()])
        assert ranked[0]["ranking"]["position"] == 1
