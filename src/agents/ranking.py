"""
Flight Ranking Agent - Scores and ranks flight options based on preferences.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
import re


@dataclass
class FlightPreferences:
    """User preferences for flight ranking."""
    max_price: Optional[float] = None
    max_stops: int = 2
    preferred_airlines: List[str] = field(default_factory=list)
    avoid_airlines: List[str] = field(default_factory=list)
    preferred_departure_time: str = "any"  # morning, afternoon, evening, night, any
    max_duration_hours: Optional[float] = None
    prefer_direct: bool = True
    
    # Weighting for composite score (should sum to 1.0)
    weight_price: float = 0.35
    weight_duration: float = 0.25
    weight_stops: float = 0.20
    weight_timing: float = 0.10
    weight_airline: float = 0.10


class FlightRankingAgent:
    """Ranks and scores flight options based on user preferences."""

    # Price scoring range (GBP) — calibrated for Lagos-London typical fares
    PRICE_MIN = 300
    PRICE_MAX = 1500

    # Duration scoring range (hours) — direct LOS-LHR ≈ 6.5h, worst-case with long layover
    DURATION_MIN_HOURS = 6.5
    DURATION_MAX_HOURS = 24.0

    # Time windows for departure preference
    TIME_WINDOWS = {
        "morning": (5, 12),     # 5am - 12pm
        "afternoon": (12, 17),  # 12pm - 5pm
        "evening": (17, 21),    # 5pm - 9pm
        "night": (21, 5),       # 9pm - 5am (overnight)
    }
    
    # Airline quality scores 
    AIRLINE_QUALITY = {
        # Premium carriers
        "EK": 90,   # Emirates
        "QR": 90,   # Qatar Airways
        "SQ": 92,   # Singapore Airlines
        "BA": 82,   # British Airways
        "LH": 85,   # Lufthansa
        "AF": 80,   # Air France
        "KL": 85,   # KLM
        "VS": 80,   # Virgin Atlantic
        "TK": 80,   # Turkish Airlines
        
        # Regional/African carriers
        "ET": 75,   # Ethiopian Airlines
        "KQ": 70,   # Kenya Airways
        "SA": 72,   # South African Airways
        "W3": 65,   # Arik Air
        "P4": 65,   # Air Peace
        
        # Low-cost carriers
        "FR": 55,   # Ryanair
        "U2": 60,   # EasyJet
        "W6": 55,   # Wizz Air
    }
    
    def __init__(self, preferences: FlightPreferences = None):
        self.preferences = preferences or FlightPreferences()
    
    def parse_duration(self, duration_str: str) -> float:
        """
        Parse ISO 8601 duration to hours.
        
        Args:
            duration_str: Duration like "PT10H30M"
            
        Returns:
            Duration in hours (e.g., 10.5)
        """
        if not duration_str:
            return 0
        
        hours = 0
        minutes = 0
        
        h_match = re.search(r'(\d+)H', duration_str)
        m_match = re.search(r'(\d+)M', duration_str)
        
        if h_match:
            hours = int(h_match.group(1))
        if m_match:
            minutes = int(m_match.group(1))
        
        return hours + minutes / 60
    
    def format_duration(self, duration_str: str) -> str:
        """Format duration for display."""
        hours = self.parse_duration(duration_str)
        h = int(hours)
        m = int((hours - h) * 60)
        return f"{h}h {m}m"
    
    def score_price(self, price: float) -> float:
        """Score price (0-100, lower price = higher score)."""
        if price <= self.PRICE_MIN:
            return 100
        elif price >= self.PRICE_MAX:
            return 0
        return 100 - ((price - self.PRICE_MIN) / (self.PRICE_MAX - self.PRICE_MIN) * 100)
    
    def score_duration(self, duration_hours: float) -> float:
        """Score duration (0-100, shorter = higher score)."""
        if duration_hours <= self.DURATION_MIN_HOURS:
            return 100
        elif duration_hours >= self.DURATION_MAX_HOURS:
            return 0
        return 100 - ((duration_hours - self.DURATION_MIN_HOURS) / (self.DURATION_MAX_HOURS - self.DURATION_MIN_HOURS) * 100)
    
    def score_stops(self, num_stops: int) -> float:
        """Score number of stops (0-100)."""
        scores = {
            0: 100,  # Direct
            1: 70,   # One stop
            2: 40,   # Two stops
        }
        return scores.get(num_stops, 20)  # 3+ stops
    
    def score_departure_time(self, departure_time: str) -> float:
        """Score departure time based on user preference."""
        try:
            # Parse ISO datetime
            if 'T' in departure_time:
                dt = datetime.fromisoformat(departure_time.replace('Z', '+00:00'))
            else:
                dt = datetime.strptime(departure_time, "%Y-%m-%d %H:%M")
            hour = dt.hour
        except:
            return 70  # Default if parsing fails
        
        preferred = self.preferences.preferred_departure_time
        
        if preferred == "any":
            return 70  # Neutral score
        
        if preferred in self.TIME_WINDOWS:
            start, end = self.TIME_WINDOWS[preferred]
            
            # Handle overnight window (e.g., night: 21-5)
            if start > end:
                in_window = hour >= start or hour < end
            else:
                in_window = start <= hour < end
            
            return 100 if in_window else 50
        
        return 70
    
    def score_airline(self, carrier_code: str) -> float:
        """Score airline based on quality and preferences."""
        # Base quality score
        base_score = self.AIRLINE_QUALITY.get(carrier_code, 60)
        
        # Adjust for user preferences
        if self.preferences.preferred_airlines:
            if carrier_code in self.preferences.preferred_airlines:
                base_score = min(100, base_score + 20)
        
        if self.preferences.avoid_airlines:
            if carrier_code in self.preferences.avoid_airlines:
                base_score = max(0, base_score - 40)
        
        return base_score
    
    def score_flight(self, flight: dict) -> dict:
        """
        Score a flight on all dimensions.
        
        Args:
            flight: Parsed flight offer from Amadeus API
            
        Returns:
            Dict with individual scores and composite score
        """
        scores = {}
        
        # Price score
        price = flight["price"]["total"]
        scores["price"] = self.score_price(price)
        
        # Get outbound itinerary (first one)
        outbound = flight["itineraries"][0]
        
        # Duration score
        duration_hours = self.parse_duration(outbound["duration"])
        scores["duration"] = self.score_duration(duration_hours)
        
        # Stops score
        stops = outbound["stops"]
        scores["stops"] = self.score_stops(stops)
        
        # Departure time score
        first_segment = outbound["segments"][0]
        dep_time = first_segment["departure"]["time"]
        scores["timing"] = self.score_departure_time(dep_time)
        
        # Airline score (use first segment's carrier)
        carrier_code = first_segment["carrier"]["code"]
        scores["airline"] = self.score_airline(carrier_code)
        
        # Calculate weighted composite score
        prefs = self.preferences
        composite = (
            scores["price"] * prefs.weight_price +
            scores["duration"] * prefs.weight_duration +
            scores["stops"] * prefs.weight_stops +
            scores["timing"] * prefs.weight_timing +
            scores["airline"] * prefs.weight_airline
        )
        
        return {
            "scores": {k: round(v, 1) for k, v in scores.items()},
            "composite_score": round(composite, 1)
        }
    
    def rank_flights(self, flights: List[dict]) -> List[dict]:
        """
        Rank all flights and return sorted list with scores.
        
        Args:
            flights: List of parsed flight offers
            
        Returns:
            Flights sorted by composite score (highest first)
        """
        scored_flights = []
        
        for flight in flights:
            score_data = self.score_flight(flight)
            flight["ranking"] = score_data
            scored_flights.append(flight)
        
        # Sort by composite score (highest first)
        scored_flights.sort(key=lambda x: x["ranking"]["composite_score"], reverse=True)
        
        # Add rank position
        for i, flight in enumerate(scored_flights):
            flight["ranking"]["position"] = i + 1
        
        return scored_flights
    
    def get_flight_summary(self, flight: dict) -> dict:
        """Get a clean summary of a flight for display."""
        outbound = flight["itineraries"][0]
        first_seg = outbound["segments"][0]
        last_seg = outbound["segments"][-1]
        
        return {
            "price": f"£{flight['price']['total']:.0f}",
            "airline": first_seg["carrier"]["name"],
            "airline_code": first_seg["carrier"]["code"],
            "departure": first_seg["departure"]["time"],
            "arrival": last_seg["arrival"]["time"],
            "origin": first_seg["departure"]["airport"],
            "destination": last_seg["arrival"]["airport"],
            "duration": self.format_duration(outbound["duration"]),
            "stops": outbound["stops"],
            "stops_text": "Direct" if outbound["stops"] == 0 else f"{outbound['stops']} stop{'s' if outbound['stops'] > 1 else ''}",
            "score": flight.get("ranking", {}).get("composite_score", 0),
            "rank": flight.get("ranking", {}).get("position", 0)
        }
    
    def explain_recommendation(self, top_flight: dict, all_flights: List[dict]) -> str:
        """
        Generate a natural language explanation of why this flight is recommended.
        
        Args:
            top_flight: The recommended flight
            all_flights: All flight options for comparison
            
        Returns:
            Human-readable explanation
        """
        summary = self.get_flight_summary(top_flight)
        ranking = top_flight["ranking"]
        scores = ranking["scores"]
        
        explanation = f"""
## ✈️ Recommended: {summary['airline']} {summary['price']}

**Route:** {summary['origin']} → {summary['destination']}
**Duration:** {summary['duration']} ({summary['stops_text']})
**Overall Score:** {summary['score']}/100

### Why this flight?
"""
        
        # Explain based on scores
        reasons = []
        
        if scores["price"] >= 70:
            reasons.append("✓ **Great value** - competitively priced")
        elif scores["price"] >= 50:
            reasons.append("• Reasonably priced")
        
        if scores["stops"] == 100:
            reasons.append("✓ **Direct flight** - no layovers")
        elif scores["stops"] >= 70:
            reasons.append("• Only 1 stop")
        
        if scores["duration"] >= 70:
            reasons.append("✓ **Good flight time** - efficient routing")
        
        if scores["timing"] >= 80:
            reasons.append("✓ **Convenient departure time**")
        
        if scores["airline"] >= 80:
            reasons.append("✓ **Quality airline** - good service reputation")
        
        explanation += "\n".join(reasons) if reasons else "• Best overall balance of factors"
        
        # Compare to alternatives
        if len(all_flights) > 1:
            cheapest = min(all_flights, key=lambda x: x["price"]["total"])
            if cheapest["price"]["total"] < top_flight["price"]["total"]:
                cheap_summary = self.get_flight_summary(cheapest)
                price_diff = top_flight["price"]["total"] - cheapest["price"]["total"]
                
                explanation += f"""

### Alternative option
The cheapest flight is **{cheap_summary['airline']}** at **{cheap_summary['price']}** (£{price_diff:.0f} less), """
                
                # Explain the trade-off
                if cheapest["itineraries"][0]["stops"] > top_flight["itineraries"][0]["stops"]:
                    explanation += f"but it has {cheap_summary['stops_text'].lower()} vs direct."
                else:
                    cheap_duration = self.parse_duration(cheapest["itineraries"][0]["duration"])
                    top_duration = self.parse_duration(top_flight["itineraries"][0]["duration"])
                    if cheap_duration > top_duration:
                        extra_time = cheap_duration - top_duration
                        explanation += f"but it takes {extra_time:.1f} hours longer."
                    else:
                        explanation += "but with a lower-rated airline."
        
        return explanation


def display_flight_results(flights: List[dict], ranker: FlightRankingAgent):
    """Display flight results in a formatted way."""
    
    print("\n" + "="*60)
    print("✈️  FLIGHT SEARCH RESULTS")
    print("="*60 + "\n")
    
    for flight in flights[:5]:  # Show top 5
        summary = ranker.get_flight_summary(flight)
        
        rank_emoji = {1: "🥇", 2: "🥈", 3: "🥉"}.get(summary["rank"], "  ")
        
        print(f"{rank_emoji} #{summary['rank']} | {summary['airline']} | {summary['price']} | {summary['duration']} | {summary['stops_text']}")
        print(f"      Score: {summary['score']}/100 | Departs: {summary['departure'][:16]}")
        print("-"*60)
    
    print(f"\nTotal options found: {len(flights)}")
