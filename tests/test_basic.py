"""
Quick test script to verify FlightFinder installation.
Run: python tests/test_basic.py
"""

import os
import sys

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()


def test_imports():
    """Test that all modules import correctly."""
    print("Testing imports...")
    
    from src.apis.amadeus import AmadeusAPI, AIRPORTS, resolve_airport
    from src.agents.ranking import FlightRankingAgent, FlightPreferences
    from src.main import FlightFinder
    
    print("All imports successful")
    return True


def test_airport_resolution():
    """Test airport code resolution."""
    print("\nTesting airport resolution...")
    
    from src.apis.amadeus import resolve_airport
    
    # Test cases
    tests = [
        ("Lagos", "LOS"),
        ("LOS", "LOS"),
        ("London", "LHR"),
        ("Heathrow", "LHR"),
        ("Manchester", "MAN"),
    ]
    
    for query, expected in tests:
        result = resolve_airport(query)
        status = "✓" if result == expected else "✗"
        print(f"  {status} '{query}' -> {result} (expected {expected})")
    
    return True


def test_ranking():
    """Test flight ranking logic."""
    print("\nTesting ranking logic...")
    
    from src.agents.ranking import FlightRankingAgent, FlightPreferences
    
    ranker = FlightRankingAgent()
    
    # Test duration parsing
    assert ranker.parse_duration("PT10H30M") == 10.5
    assert ranker.parse_duration("PT6H") == 6.0
    print("Duration parsing works")
    
    # Test price scoring
    assert ranker.score_price(300) == 100  # Cheapest
    assert ranker.score_price(1500) == 0   # Most expensive
    assert 0 < ranker.score_price(800) < 100  # Middle
    print("Price scoring works")
    
    # Test stops scoring
    assert ranker.score_stops(0) == 100  # Direct
    assert ranker.score_stops(1) == 70   # One stop
    assert ranker.score_stops(2) == 40   # Two stops
    print("Stops scoring works")
    
    print("All ranking tests passed")
    return True


def test_api_credentials():
    """Test that API credentials are configured."""
    print("\nChecking API credentials...")
    
    client_id = os.getenv("AMADEUS_CLIENT_ID")
    client_secret = os.getenv("AMADEUS_CLIENT_SECRET")
    
    if client_id and client_secret:
        print(f"Amadeus credentials found (ID: {client_id[:8]}...)")
    else:
        print("Amadeus credentials not found in .env")
        print("Get free credentials at https://developers.amadeus.com/")
    
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        print(f"OpenAI API key found")
    else:
        print("OpenAI API key not found (needed for natural language parsing)")
    
    return True


def test_api_connection():
    """Test actual API connection (requires credentials)."""
    print("\nTesting Amadeus API connection...")
    
    client_id = os.getenv("AMADEUS_CLIENT_ID")
    client_secret = os.getenv("AMADEUS_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        print("Skipping - no credentials")
        return True
    
    try:
        from src.apis.amadeus import AmadeusAPI
        
        api = AmadeusAPI(sandbox=True)
        api._authenticate()
        
        print("Successfully authenticated with Amadeus API")
        
        # Try a simple search
        from datetime import datetime, timedelta
        future_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        
        result = api.search_flights(
            origin="LOS",
            destination="LHR",
            departure_date=future_date,
            max_results=1
        )
        
        if result.get("error"):
            print(f"Search returned error: {result.get('message', 'Unknown')}")
        else:
            offers = result.get("offers", [])
            print(f"Search successful - found {len(offers)} offers")
        
    except Exception as e:
        print(f"API connection failed: {str(e)}")
        return False
    
    return True


def main():
    """Run all tests."""
    print("="*50)
    print("FlightFinder - Installation Test")
    print("="*50)
    
    tests = [
        test_imports,
        test_airport_resolution,
        test_ranking,
        test_api_credentials,
        test_api_connection,
    ]
    
    all_passed = True
    for test in tests:
        try:
            if not test():
                all_passed = False
        except Exception as e:
            print(f"Test failed with error: {str(e)}")
            all_passed = False
    
    print("\n" + "="*50)
    if all_passed:
        print("All tests passed! FlightFinder is ready to use.")
        print("\nNext steps:")
        print("  1. Run the web app: streamlit run frontend/app.py")
        print("  2. Or use CLI: python -m src.main -o Lagos -d London --date 2026-02-15")
    else:
        print("Some tests failed. Check the errors above.")
    print("="*50)


if __name__ == "__main__":
    main()
