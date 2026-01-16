"""
Amadeus Flight Search API Integration
Documentation: https://developers.amadeus.com/
"""

import requests
from datetime import datetime, timedelta
from typing import List, Optional
import os
from dotenv import load_dotenv

load_dotenv()


class AmadeusAPI:
    """Amadeus Flight Search API client."""
    
    def __init__(self, sandbox: bool = True):
        self.client_id = os.getenv("AMADEUS_CLIENT_ID")
        self.client_secret = os.getenv("AMADEUS_CLIENT_SECRET")
        self.sandbox = sandbox
        
        if sandbox:
            self.base_url = "https://test.api.amadeus.com"
        else:
            self.base_url = "https://api.amadeus.com"
        
        self.access_token = None
        self.token_expiry = None
    
    def _authenticate(self):
        """Get OAuth2 access token."""
        # Skip if we have a valid token
        if self.access_token and self.token_expiry and datetime.now() < self.token_expiry:
            return
        
        response = requests.post(
            f"{self.base_url}/v1/security/oauth2/token",
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code != 200:
            raise Exception(f"Authentication failed: {response.status_code} - {response.text}")
        
        data = response.json()
        self.access_token = data["access_token"]
        # Set expiry 60 seconds before actual expiry for safety
        self.token_expiry = datetime.now() + timedelta(seconds=data["expires_in"] - 60)
        print(f"Authenticated with Amadeus API")
    
    def _headers(self) -> dict:
        """Get headers with auth token."""
        self._authenticate()
        return {"Authorization": f"Bearer {self.access_token}"}
    
    def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: str = None,
        adults: int = 1,
        travel_class: str = "ECONOMY",
        max_results: int = 10,
        nonstop_only: bool = False
    ) -> dict:
        """
        Search for flights.
        
        Args:
            origin: IATA airport code (e.g., "LOS" for Lagos, "LHR" for London Heathrow)
            destination: IATA airport code
            departure_date: YYYY-MM-DD format
            return_date: YYYY-MM-DD format (optional for one-way)
            adults: Number of adult passengers
            travel_class: ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST
            max_results: Maximum number of offers to return
            nonstop_only: Only return non-stop flights
            
        Returns:
            Dict with parsed flight offers
        """
        params = {
            "originLocationCode": origin.upper(),
            "destinationLocationCode": destination.upper(),
            "departureDate": departure_date,
            "adults": adults,
            "travelClass": travel_class,
            "max": max_results,
            "currencyCode": "GBP"
        }
        
        if return_date:
            params["returnDate"] = return_date
        
        if nonstop_only:
            params["nonStop"] = "true"
        
        print(f"Searching flights: {origin} → {destination} on {departure_date}")
        
        response = requests.get(
            f"{self.base_url}/v2/shopping/flight-offers",
            headers=self._headers(),
            params=params
        )
        
        if response.status_code != 200:
            return {
                "error": True,
                "status_code": response.status_code,
                "message": response.text
            }
        
        return self._parse_flight_offers(response.json())
    
    def _parse_flight_offers(self, raw_data: dict) -> dict:
        """Parse raw Amadeus response into cleaner format."""
        
        offers = []
        dictionaries = raw_data.get("dictionaries", {})
        carriers = dictionaries.get("carriers", {})
        aircraft = dictionaries.get("aircraft", {})
        
        for offer in raw_data.get("data", []):
            parsed_offer = {
                "id": offer.get("id"),
                "price": {
                    "total": float(offer.get("price", {}).get("total", 0)),
                    "currency": offer.get("price", {}).get("currency", "GBP"),
                },
                "itineraries": []
            }
            
            for itinerary in offer.get("itineraries", []):
                parsed_itinerary = {
                    "duration": itinerary.get("duration"),
                    "segments": []
                }
                
                for segment in itinerary.get("segments", []):
                    carrier_code = segment.get("carrierCode", "")
                    parsed_segment = {
                        "departure": {
                            "airport": segment.get("departure", {}).get("iataCode"),
                            "time": segment.get("departure", {}).get("at"),
                            "terminal": segment.get("departure", {}).get("terminal")
                        },
                        "arrival": {
                            "airport": segment.get("arrival", {}).get("iataCode"),
                            "time": segment.get("arrival", {}).get("at"),
                            "terminal": segment.get("arrival", {}).get("terminal")
                        },
                        "carrier": {
                            "code": carrier_code,
                            "name": carriers.get(carrier_code, carrier_code)
                        },
                        "flight_number": f"{carrier_code}{segment.get('number', '')}",
                        "aircraft": aircraft.get(
                            segment.get("aircraft", {}).get("code", ""), 
                            "Unknown"
                        ),
                        "duration": segment.get("duration")
                    }
                    parsed_itinerary["segments"].append(parsed_segment)
                
                # Calculate total stops
                parsed_itinerary["stops"] = len(parsed_itinerary["segments"]) - 1
                parsed_offer["itineraries"].append(parsed_itinerary)
            
            offers.append(parsed_offer)
        
        return {
            "offers": offers,
            "total_results": len(offers),
            "error": False
        }
    
    def search_flexible_dates(
        self,
        origin: str,
        destination: str,
        target_date: str,
        flexibility_days: int = 3,
        adults: int = 1,
        nonstop_only: bool = False
    ) -> List[dict]:
        """
        Search across multiple dates to find best prices.
        
        Args:
            origin: IATA airport code
            destination: IATA airport code
            target_date: Target date in YYYY-MM-DD format
            flexibility_days: Number of days before/after to search
            adults: Number of passengers
            nonstop_only: Only return direct flights
            
        Returns:
            List of flight offers sorted by price
        """
        target = datetime.strptime(target_date, "%Y-%m-%d")
        all_results = []
        
        print(f"Searching {flexibility_days * 2 + 1} dates around {target_date}...")
        
        for delta in range(-flexibility_days, flexibility_days + 1):
            search_date = (target + timedelta(days=delta)).strftime("%Y-%m-%d")
            
            results = self.search_flights(
                origin=origin,
                destination=destination,
                departure_date=search_date,
                adults=adults,
                nonstop_only=nonstop_only,
                max_results=3  # Fewer per date to avoid rate limits
            )
            
            if not results.get("error") and "offers" in results:
                for offer in results["offers"]:
                    offer["search_date"] = search_date
                    all_results.append(offer)
        
        # Sort by price
        all_results.sort(key=lambda x: x["price"]["total"])
        
        print(f"Found {len(all_results)} total options")
        
        return all_results


# Airport codes reference
AIRPORTS = {
    # ============ NIGERIA ============
    "LOS": {"name": "Murtala Muhammed International", "city": "Lagos", "country": "Nigeria"},
    "ABV": {"name": "Nnamdi Azikiwe International", "city": "Abuja", "country": "Nigeria"},
    "PHC": {"name": "Port Harcourt International", "city": "Port Harcourt", "country": "Nigeria"},
    
    # ============ UNITED KINGDOM ============
    "LHR": {"name": "Heathrow", "city": "London", "country": "UK"},
    "LGW": {"name": "Gatwick", "city": "London Gatwick", "country": "UK"},
    "STN": {"name": "Stansted", "city": "London Stansted", "country": "UK"},
    "LTN": {"name": "Luton", "city": "London Luton", "country": "UK"},
    "MAN": {"name": "Manchester", "city": "Manchester", "country": "UK"},
    "EDI": {"name": "Edinburgh", "city": "Edinburgh", "country": "UK"},
    "BHX": {"name": "Birmingham", "city": "Birmingham", "country": "UK"},
    "GLA": {"name": "Glasgow", "city": "Glasgow", "country": "UK"},
    
    # ============ BALKANS & EASTERN EUROPE ============
    # Georgia
    "TBS": {"name": "Shota Rustaveli Tbilisi International", "city": "Tbilisi", "country": "Georgia"},
    "BUS": {"name": "Batumi International", "city": "Batumi", "country": "Georgia"},
    
    # Serbia
    "BEG": {"name": "Nikola Tesla", "city": "Belgrade", "country": "Serbia"},
    
    # North Macedonia
    "SKP": {"name": "Skopje International", "city": "Skopje", "country": "North Macedonia"},
    "OHD": {"name": "St. Paul the Apostle", "city": "Ohrid", "country": "North Macedonia"},
    
    # Montenegro
    "TGD": {"name": "Podgorica", "city": "Podgorica", "country": "Montenegro"},
    "TIV": {"name": "Tivat", "city": "Tivat", "country": "Montenegro"},
    
    # Albania
    "TIA": {"name": "Tirana International", "city": "Tirana", "country": "Albania"},
    
    # Bosnia & Herzegovina
    "SJJ": {"name": "Sarajevo International", "city": "Sarajevo", "country": "Bosnia & Herzegovina"},
    
    # ============ CARIBBEAN ============
    # Antigua and Barbuda
    "ANU": {"name": "V.C. Bird International", "city": "St. John's", "country": "Antigua & Barbuda"},
    
    # Dominican Republic
    "PUJ": {"name": "Punta Cana International", "city": "Punta Cana", "country": "Dominican Republic"},
    "SDQ": {"name": "Las Americas International", "city": "Santo Domingo", "country": "Dominican Republic"},
    
    # Anguilla
    "AXA": {"name": "Clayton J. Lloyd International", "city": "The Valley", "country": "Anguilla"},
    
    # Sint Maarten
    "SXM": {"name": "Princess Juliana International", "city": "Philipsburg", "country": "Sint Maarten"},
    
    # Turks and Caicos
    "PLS": {"name": "Providenciales International", "city": "Providenciales", "country": "Turks & Caicos"},
    
    # ============ MIDDLE EAST ============
    # Turkey
    "IST": {"name": "Istanbul Airport", "city": "Istanbul", "country": "Turkey"},
    "SAW": {"name": "Sabiha Gokcen", "city": "Istanbul Sabiha", "country": "Turkey"},
    "AYT": {"name": "Antalya", "city": "Antalya", "country": "Turkey"},
    "ADB": {"name": "Adnan Menderes", "city": "Izmir", "country": "Turkey"},
    
    # Qatar
    "DOH": {"name": "Hamad International", "city": "Doha", "country": "Qatar"},
    
    # UAE
    "DXB": {"name": "Dubai International", "city": "Dubai", "country": "UAE"},
    "AUH": {"name": "Zayed International", "city": "Abu Dhabi", "country": "UAE"},
    "SHJ": {"name": "Sharjah International", "city": "Sharjah", "country": "UAE"},
    
    # ============ ASIA ============
    # China
    "PEK": {"name": "Beijing Capital", "city": "Beijing", "country": "China"},
    "PKX": {"name": "Beijing Daxing", "city": "Beijing Daxing", "country": "China"},
    "PVG": {"name": "Pudong International", "city": "Shanghai", "country": "China"},
    "CAN": {"name": "Baiyun International", "city": "Guangzhou", "country": "China"},
    "HKG": {"name": "Hong Kong International", "city": "Hong Kong", "country": "Hong Kong"},
    
    # Japan
    "NRT": {"name": "Narita International", "city": "Tokyo Narita", "country": "Japan"},
    "HND": {"name": "Haneda", "city": "Tokyo Haneda", "country": "Japan"},
    "KIX": {"name": "Kansai International", "city": "Osaka", "country": "Japan"},
    
    # Singapore
    "SIN": {"name": "Changi", "city": "Singapore", "country": "Singapore"},
    
    # ============ EUROPE ============
    # Netherlands
    "AMS": {"name": "Schiphol", "city": "Amsterdam", "country": "Netherlands"},
    "RTM": {"name": "Rotterdam The Hague", "city": "Rotterdam", "country": "Netherlands"},
    
    # Italy
    "FCO": {"name": "Leonardo da Vinci–Fiumicino", "city": "Rome", "country": "Italy"},
    "MXP": {"name": "Malpensa", "city": "Milan", "country": "Italy"},
    "VCE": {"name": "Marco Polo", "city": "Venice", "country": "Italy"},
    "NAP": {"name": "Naples International", "city": "Naples", "country": "Italy"},
    
    # France
    "CDG": {"name": "Charles de Gaulle", "city": "Paris CDG", "country": "France"},
    "ORY": {"name": "Orly", "city": "Paris Orly", "country": "France"},
    "NCE": {"name": "Nice Côte d'Azur", "city": "Nice", "country": "France"},
    "LYS": {"name": "Lyon–Saint-Exupéry", "city": "Lyon", "country": "France"},
    
    # Spain
    "MAD": {"name": "Adolfo Suárez Madrid–Barajas", "city": "Madrid", "country": "Spain"},
    "BCN": {"name": "Josep Tarradellas Barcelona–El Prat", "city": "Barcelona", "country": "Spain"},
    "AGP": {"name": "Málaga–Costa del Sol", "city": "Malaga", "country": "Spain"},
    "PMI": {"name": "Palma de Mallorca", "city": "Palma", "country": "Spain"},
    
    # Germany
    "FRA": {"name": "Frankfurt", "city": "Frankfurt", "country": "Germany"},
    "MUC": {"name": "Munich", "city": "Munich", "country": "Germany"},
    "BER": {"name": "Berlin Brandenburg", "city": "Berlin", "country": "Germany"},
    
    # ============ AFRICA ============
    # Morocco
    "CMN": {"name": "Mohammed V International", "city": "Casablanca", "country": "Morocco"},
    "RAK": {"name": "Marrakech Menara", "city": "Marrakech", "country": "Morocco"},
    "TNG": {"name": "Ibn Battouta", "city": "Tangier", "country": "Morocco"},
    "FEZ": {"name": "Fès–Saïs", "city": "Fez", "country": "Morocco"},
    
    # Ethiopia (common connection)
    "ADD": {"name": "Bole International", "city": "Addis Ababa", "country": "Ethiopia"},
    
    # South Africa
    "JNB": {"name": "O.R. Tambo International", "city": "Johannesburg", "country": "South Africa"},
    "CPT": {"name": "Cape Town International", "city": "Cape Town", "country": "South Africa"},
    
    # Egypt
    "CAI": {"name": "Cairo International", "city": "Cairo", "country": "Egypt"},
    
    # ============ AMERICAS ============
    # USA (common hubs)
    "JFK": {"name": "John F. Kennedy", "city": "New York JFK", "country": "USA"},
    "EWR": {"name": "Newark Liberty", "city": "Newark", "country": "USA"},
    "LAX": {"name": "Los Angeles International", "city": "Los Angeles", "country": "USA"},
    "ATL": {"name": "Hartsfield-Jackson", "city": "Atlanta", "country": "USA"},
    "MIA": {"name": "Miami International", "city": "Miami", "country": "USA"},
    
    # Canada
    "YYZ": {"name": "Toronto Pearson", "city": "Toronto", "country": "Canada"},
    "YVR": {"name": "Vancouver International", "city": "Vancouver", "country": "Canada"},
}


def resolve_airport(query: str) -> Optional[str]:
    """
    Resolve city/airport name to IATA code.
    
    Args:
        query: City name or IATA code
        
    Returns:
        IATA code or None if not found
    """
    query_upper = query.upper().strip()
    query_lower = query.lower().strip()
    
    # Direct IATA code match
    if query_upper in AIRPORTS:
        return query_upper
    
    # City name match
    for code, info in AIRPORTS.items():
        if query_lower == info["city"].lower():
            return code
        if query_lower in info["city"].lower():
            return code
        if query_lower in info["name"].lower():
            return code
    
    return None


def get_airport_info(code: str) -> dict:
    """Get airport information by IATA code."""
    return AIRPORTS.get(code.upper(), {"name": code, "city": "Unknown", "country": "Unknown"})