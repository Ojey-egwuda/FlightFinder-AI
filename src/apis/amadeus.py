"""
Amadeus Flight Search API Integration
Documentation: https://developers.amadeus.com/
"""

import hashlib
import json
import logging
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import List, Optional

import requests
from dotenv import load_dotenv

from src.data.airports import AIRPORTS, AIRPORT_DATA

load_dotenv()

logger = logging.getLogger(__name__)

# Tuneable constants
_CACHE_TTL_SECONDS = 600   # 10-minute result TTL
_REQUEST_TIMEOUT = 10      # seconds per HTTP call
_MAX_RETRIES = 2           # attempts on transient 5xx / timeout
_RETRY_DELAY = 1.5         # seconds between retries
_CACHE_PATH = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".cache", "flights.json")
)


# ---------------------------------------------------------------------------
# Persistent cache helpers
# ---------------------------------------------------------------------------

def _load_persistent_cache() -> dict:
    """Load cache from disk, dropping already-expired entries."""
    try:
        with open(_CACHE_PATH) as fh:
            raw = json.load(fh)
        now = datetime.now()
        return {
            k: v for k, v in raw.items()
            if datetime.fromisoformat(v["expires_at"]) > now
        }
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return {}


def _save_persistent_cache(cache: dict) -> None:
    """Serialise cache dict to disk (datetime → ISO string)."""
    try:
        os.makedirs(os.path.dirname(_CACHE_PATH), exist_ok=True)
        serialisable = {
            k: {
                "result": v["result"],
                "expires_at": v["expires_at"].isoformat()
                    if isinstance(v["expires_at"], datetime)
                    else v["expires_at"],
            }
            for k, v in cache.items()
        }
        with open(_CACHE_PATH, "w") as fh:
            json.dump(serialisable, fh)
    except OSError as exc:
        logger.warning("Could not write cache to disk: %s", exc)


# ---------------------------------------------------------------------------
# API client
# ---------------------------------------------------------------------------

class AmadeusAPI:
    """Amadeus Flight Search API client."""

    def __init__(self, sandbox: bool = True):
        self.client_id = os.getenv("AMADEUS_CLIENT_ID")
        self.client_secret = os.getenv("AMADEUS_CLIENT_SECRET")
        self.sandbox = sandbox
        self.base_url = (
            "https://test.api.amadeus.com" if sandbox else "https://api.amadeus.com"
        )

        self.access_token = None
        self.token_expiry = None
        self._auth_lock = threading.Lock()    # guards token refresh

        self._cache_lock = threading.Lock()   # guards cache reads/writes
        self._search_cache: dict = _load_persistent_cache()

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def _authenticate(self):
        """Get OAuth2 access token (thread-safe, cached until near expiry)."""
        with self._auth_lock:
            if self.access_token and self.token_expiry and datetime.now() < self.token_expiry:
                return

            response = requests.post(
                f"{self.base_url}/v1/security/oauth2/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=_REQUEST_TIMEOUT,
            )

            if response.status_code != 200:
                raise Exception(
                    f"Authentication failed: {response.status_code} - {response.text}"
                )

            data = response.json()
            self.access_token = data["access_token"]
            # Buffer 60 s before true expiry to avoid last-second failures
            self.token_expiry = datetime.now() + timedelta(seconds=data["expires_in"] - 60)
            logger.info("Authenticated with Amadeus API")

    def _headers(self) -> dict:
        self._authenticate()
        return {"Authorization": f"Bearer {self.access_token}"}

    # ------------------------------------------------------------------
    # Flight search
    # ------------------------------------------------------------------

    def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: str = None,
        adults: int = 1,
        travel_class: str = "ECONOMY",
        max_results: int = 10,
        nonstop_only: bool = False,
    ) -> dict:
        """
        Search for flights.

        Args:
            origin: IATA airport code (e.g. "LOS")
            destination: IATA airport code
            departure_date: YYYY-MM-DD format
            return_date: YYYY-MM-DD format (optional, one-way if omitted)
            adults: Number of adult passengers
            travel_class: ECONOMY | PREMIUM_ECONOMY | BUSINESS | FIRST
            max_results: Maximum offers to return
            nonstop_only: Restrict to non-stop flights

        Returns:
            {"offers": [...], "total_results": int, "error": False}
            or {"error": True, "status_code": int, "message": str}
        """
        origin = origin.upper().strip()
        destination = destination.upper().strip()

        # ---- Input validation ----
        if origin == destination:
            return {
                "error": True, "status_code": 400,
                "message": "Origin and destination cannot be the same airport.",
            }

        try:
            dep = datetime.strptime(departure_date, "%Y-%m-%d")
        except ValueError:
            return {
                "error": True, "status_code": 400,
                "message": f"Invalid date format '{departure_date}'. Use YYYY-MM-DD.",
            }

        if dep.date() < datetime.now().date():
            return {
                "error": True, "status_code": 400,
                "message": "Departure date cannot be in the past.",
            }

        if return_date:
            try:
                ret = datetime.strptime(return_date, "%Y-%m-%d")
            except ValueError:
                return {
                    "error": True, "status_code": 400,
                    "message": f"Invalid return date format '{return_date}'. Use YYYY-MM-DD.",
                }
            if ret.date() < dep.date():
                return {
                    "error": True, "status_code": 400,
                    "message": "Return date cannot be before departure date.",
                }

        # ---- Build params ----
        params = {
            "originLocationCode": origin,
            "destinationLocationCode": destination,
            "departureDate": departure_date,
            "adults": adults,
            "travelClass": travel_class,
            "max": max_results,
            "currencyCode": "GBP",
        }
        if return_date:
            params["returnDate"] = return_date
        if nonstop_only:
            params["nonStop"] = "true"

        # ---- Cache lookup ----
        cache_key = hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()
        with self._cache_lock:
            cached = self._search_cache.get(cache_key)
        if cached:
            expires = cached["expires_at"]
            if isinstance(expires, str):
                expires = datetime.fromisoformat(expires)
            if datetime.now() < expires:
                logger.debug("Cache hit: %s → %s on %s", origin, destination, departure_date)
                return cached["result"]

        logger.info("Searching flights: %s → %s on %s", origin, destination, departure_date)

        # ---- HTTP request with retry + timeout ----
        response = None
        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                response = requests.get(
                    f"{self.base_url}/v2/shopping/flight-offers",
                    headers=self._headers(),
                    params=params,
                    timeout=_REQUEST_TIMEOUT,
                )
                if response.status_code < 500:
                    break  # success or client error — no retry
                if attempt < _MAX_RETRIES:
                    logger.warning(
                        "Amadeus returned %s (attempt %d/%d), retrying in %.1fs…",
                        response.status_code, attempt, _MAX_RETRIES, _RETRY_DELAY,
                    )
                    time.sleep(_RETRY_DELAY)
            except requests.Timeout:
                if attempt < _MAX_RETRIES:
                    logger.warning(
                        "Request timed out (attempt %d/%d), retrying…", attempt, _MAX_RETRIES
                    )
                    time.sleep(_RETRY_DELAY)
                else:
                    return {"error": True, "status_code": 408, "message": "Request timed out."}
            except requests.RequestException as exc:
                return {"error": True, "status_code": 503, "message": str(exc)}

        if response is None or response.status_code != 200:
            return {
                "error": True,
                "status_code": response.status_code if response else 503,
                "message": response.text if response else "No response received.",
            }

        result = self._parse_flight_offers(response.json())
        if not result.get("error"):
            entry = {
                "result": result,
                "expires_at": datetime.now() + timedelta(seconds=_CACHE_TTL_SECONDS),
            }
            with self._cache_lock:
                self._search_cache[cache_key] = entry
                _save_persistent_cache(self._search_cache)

        return result

    def _parse_flight_offers(self, raw_data: dict) -> dict:
        """Parse raw Amadeus response into a cleaner, flat structure."""
        offers = []
        dicts = raw_data.get("dictionaries", {})
        carriers = dicts.get("carriers", {})
        aircraft = dicts.get("aircraft", {})

        for offer in raw_data.get("data", []):
            parsed_offer = {
                "id": offer.get("id"),
                "price": {
                    "total": float(offer.get("price", {}).get("total", 0)),
                    "currency": offer.get("price", {}).get("currency", "GBP"),
                },
                "itineraries": [],
            }

            for itinerary in offer.get("itineraries", []):
                parsed_itinerary = {"duration": itinerary.get("duration"), "segments": []}

                for segment in itinerary.get("segments", []):
                    carrier_code = segment.get("carrierCode", "")
                    parsed_itinerary["segments"].append({
                        "departure": {
                            "airport": segment.get("departure", {}).get("iataCode"),
                            "time": segment.get("departure", {}).get("at"),
                            "terminal": segment.get("departure", {}).get("terminal"),
                        },
                        "arrival": {
                            "airport": segment.get("arrival", {}).get("iataCode"),
                            "time": segment.get("arrival", {}).get("at"),
                            "terminal": segment.get("arrival", {}).get("terminal"),
                        },
                        "carrier": {
                            "code": carrier_code,
                            "name": carriers.get(carrier_code, carrier_code),
                        },
                        "flight_number": f"{carrier_code}{segment.get('number', '')}",
                        "aircraft": aircraft.get(
                            segment.get("aircraft", {}).get("code", ""), "Unknown"
                        ),
                        "duration": segment.get("duration"),
                    })

                parsed_itinerary["stops"] = len(parsed_itinerary["segments"]) - 1
                parsed_offer["itineraries"].append(parsed_itinerary)

            offers.append(parsed_offer)

        return {"offers": offers, "total_results": len(offers), "error": False}

    def search_flexible_dates(
        self,
        origin: str,
        destination: str,
        target_date: str,
        flexibility_days: int = 3,
        adults: int = 1,
        nonstop_only: bool = False,
    ) -> List[dict]:
        """
        Search across multiple dates **concurrently** to find best prices.

        Args:
            origin: IATA airport code
            destination: IATA airport code
            target_date: Centre date in YYYY-MM-DD format
            flexibility_days: Days before/after to include
            adults: Number of passengers
            nonstop_only: Only direct flights

        Returns:
            Offers from all dates, sorted by price (cheapest first)
        """
        target = datetime.strptime(target_date, "%Y-%m-%d")
        dates = [
            (target + timedelta(days=d)).strftime("%Y-%m-%d")
            for d in range(-flexibility_days, flexibility_days + 1)
        ]

        logger.info(
            "Flexible search: %d dates around %s (concurrent)", len(dates), target_date
        )

        def _fetch(date: str):
            return date, self.search_flights(
                origin=origin,
                destination=destination,
                departure_date=date,
                adults=adults,
                nonstop_only=nonstop_only,
                max_results=3,
            )

        all_results = []
        with ThreadPoolExecutor(max_workers=len(dates)) as executor:
            futures = {executor.submit(_fetch, d): d for d in dates}
            for future in as_completed(futures):
                try:
                    date, result = future.result()
                    if not result.get("error") and "offers" in result:
                        for offer in result["offers"]:
                            offer["search_date"] = date
                            all_results.append(offer)
                except Exception as exc:
                    logger.warning("Date search raised an exception: %s", exc)

        all_results.sort(key=lambda x: x["price"]["total"])
        logger.info("Flexible search found %d total options", len(all_results))
        return all_results


# ---------------------------------------------------------------------------
# Airport helpers
# ---------------------------------------------------------------------------

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

    if query_upper in AIRPORTS:
        return query_upper

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
