"""
FlightFinder - Main Application
An AI-powered flight search agent.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from src.apis.amadeus import AmadeusAPI, resolve_airport, get_airport_info
from src.agents.ranking import FlightRankingAgent, FlightPreferences, display_flight_results
from src.agents.query_parser import QueryParserAgent, SimpleQueryParser


class FlightFinder:
    """Main FlightFinder application."""
    
    def __init__(self, sandbox: bool = True, use_llm_parser: bool = True):
        """
        Initialize FlightFinder.
        
        Args:
            sandbox: Use Amadeus test environment (True) or production (False)
            use_llm_parser: Use Claude for query parsing (True) or simple parser (False)
        """
        self.amadeus = AmadeusAPI(sandbox=sandbox)
        self.ranker = FlightRankingAgent()
        self.use_llm_parser = use_llm_parser
        
        if use_llm_parser:
            self.query_parser = QueryParserAgent()
        else:
            self.query_parser = SimpleQueryParser()
    
    def search_natural_language(self, query: str) -> dict:
        """
        Search flights using natural language query.
        
        Args:
            query: Natural language like "Find flights from Lagos to London next month"
            
        Returns:
            Dict with results and recommendation
        """
        print(f"\n🤖 Understanding query: '{query}'")
        
        # Parse the query
        if self.use_llm_parser:
            parsed = self.query_parser.parse_query(query)
        else:
            return {"error": "Natural language requires LLM parser. Use search_direct() instead."}
        
        if not parsed.is_valid:
            return {"error": parsed.error_message}
        
        print(f"✓ Parsed: {parsed.origin_name} → {parsed.destination_name} on {parsed.departure_date}")
        
        # Search flights
        if parsed.flexible_dates:
            flights = self.amadeus.search_flexible_dates(
                origin=parsed.origin,
                destination=parsed.destination,
                target_date=parsed.departure_date,
                flexibility_days=parsed.flexibility_days,
                adults=parsed.adults
            )
        else:
            result = self.amadeus.search_flights(
                origin=parsed.origin,
                destination=parsed.destination,
                departure_date=parsed.departure_date,
                return_date=parsed.return_date,
                adults=parsed.adults,
                travel_class=parsed.travel_class,
                nonstop_only=parsed.nonstop_only
            )
            
            if result.get("error"):
                return {"error": result.get("message", "Search failed")}
            
            flights = result.get("offers", [])
        
        if not flights:
            return {"error": "No flights found for your search criteria."}
        
        # Update ranker preferences if specified
        if parsed.preferred_time != "any":
            self.ranker.preferences.preferred_departure_time = parsed.preferred_time
        
        if parsed.max_price:
            self.ranker.preferences.max_price = parsed.max_price
        
        # Rank flights
        ranked_flights = self.ranker.rank_flights(flights)
        
        # Generate recommendation
        top_flight = ranked_flights[0]
        explanation = self.ranker.explain_recommendation(top_flight, ranked_flights)
        
        return {
            "success": True,
            "query": {
                "origin": parsed.origin_name,
                "destination": parsed.destination_name,
                "departure_date": parsed.departure_date,
                "return_date": parsed.return_date,
                "flexible_dates": parsed.flexible_dates
            },
            "total_results": len(ranked_flights),
            "flights": ranked_flights,
            "top_recommendation": top_flight,
            "explanation": explanation
        }
    
    def search_direct(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: str = None,
        adults: int = 1,
        flexible_dates: bool = False,
        nonstop_only: bool = False
    ) -> dict:
        """
        Search flights with explicit parameters.
        
        Args:
            origin: Origin city or airport code (e.g., "Lagos" or "LOS")
            destination: Destination city or airport code
            departure_date: Date in YYYY-MM-DD format
            return_date: Optional return date
            adults: Number of passengers
            flexible_dates: Search ±3 days for better prices
            nonstop_only: Only return direct flights
            
        Returns:
            Dict with results and recommendation
        """
        # Resolve airport codes
        origin_code = resolve_airport(origin)
        dest_code = resolve_airport(destination)
        
        if not origin_code:
            return {"error": f"Could not find airport for: {origin}"}
        if not dest_code:
            return {"error": f"Could not find airport for: {destination}"}
        
        origin_info = get_airport_info(origin_code)
        dest_info = get_airport_info(dest_code)
        
        print(f"\n🔍 Searching: {origin_info['city']} ({origin_code}) → {dest_info['city']} ({dest_code})")
        print(f"   Date: {departure_date}" + (f" (±3 days)" if flexible_dates else ""))
        
        # Search flights
        if flexible_dates:
            flights = self.amadeus.search_flexible_dates(
                origin=origin_code,
                destination=dest_code,
                target_date=departure_date,
                adults=adults
            )
        else:
            result = self.amadeus.search_flights(
                origin=origin_code,
                destination=dest_code,
                departure_date=departure_date,
                return_date=return_date,
                adults=adults,
                nonstop_only=nonstop_only
            )
            
            if result.get("error"):
                return {"error": result.get("message", "Search failed")}
            
            flights = result.get("offers", [])
        
        if not flights:
            return {"error": "No flights found. Try different dates or routes."}
        
        # Rank flights
        ranked_flights = self.ranker.rank_flights(flights)
        
        # Generate recommendation
        top_flight = ranked_flights[0]
        explanation = self.ranker.explain_recommendation(top_flight, ranked_flights)
        
        return {
            "success": True,
            "query": {
                "origin": f"{origin_info['city']} ({origin_code})",
                "destination": f"{dest_info['city']} ({dest_code})",
                "departure_date": departure_date,
                "return_date": return_date
            },
            "total_results": len(ranked_flights),
            "flights": ranked_flights,
            "top_recommendation": top_flight,
            "explanation": explanation
        }
    
    def display_results(self, results: dict):
        """Display search results in a formatted way."""
        if "error" in results:
            print(f"\n❌ Error: {results['error']}")
            return
        
        flights = results.get("flights", [])
        display_flight_results(flights, self.ranker)
        
        print("\n" + "="*60)
        print("💡 RECOMMENDATION")
        print("="*60)
        print(results.get("explanation", "No explanation available."))


def main():
    """Run FlightFinder from command line."""
    import argparse
    
    parser = argparse.ArgumentParser(description="FlightFinder - AI-powered flight search")
    parser.add_argument("--origin", "-o", help="Origin city or airport code")
    parser.add_argument("--destination", "-d", help="Destination city or airport code")
    parser.add_argument("--date", help="Departure date (YYYY-MM-DD)")
    parser.add_argument("--return", dest="return_date", help="Return date (YYYY-MM-DD)")
    parser.add_argument("--flexible", "-f", action="store_true", help="Search flexible dates")
    parser.add_argument("--direct", action="store_true", help="Only direct flights")
    parser.add_argument("--query", "-q", help="Natural language query")
    parser.add_argument("--sandbox", action="store_true", default=True, help="Use sandbox/test mode")
    
    args = parser.parse_args()
    
    # Initialize
    finder = FlightFinder(sandbox=args.sandbox)
    
    if args.query:
        # Natural language search
        results = finder.search_natural_language(args.query)
    elif args.origin and args.destination and args.date:
        # Direct search
        results = finder.search_direct(
            origin=args.origin,
            destination=args.destination,
            departure_date=args.date,
            return_date=args.return_date,
            flexible_dates=args.flexible,
            nonstop_only=args.direct
        )
    else:
        # Interactive mode
        print("\n✈️  FlightFinder - AI-Powered Flight Search")
        print("="*45)
        print("\nExamples:")
        print('  python -m src.main --query "flights from Lagos to London next month"')
        print('  python -m src.main -o Lagos -d London --date 2026-02-15 --flexible')
        print()
        return
    
    # Display results
    finder.display_results(results)


if __name__ == "__main__":
    main()
