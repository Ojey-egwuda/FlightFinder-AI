"""
Query Parser Agent - Extracts flight search parameters from natural language.
Uses OpenAI GPT to understand user queries.
"""

import os
import json
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from src.apis.amadeus import resolve_airport, AIRPORTS


@dataclass
class ParsedFlightQuery:
    """Structured flight search parameters."""
    origin: str
    origin_name: str
    destination: str
    destination_name: str
    departure_date: str
    return_date: Optional[str] = None
    adults: int = 1
    travel_class: str = "ECONOMY"
    flexible_dates: bool = False
    flexibility_days: int = 3
    nonstop_only: bool = False
    max_price: Optional[float] = None
    preferred_time: str = "any"
    is_valid: bool = True
    error_message: Optional[str] = None


class QueryParserAgent:
    """Parses natural language flight queries into structured parameters."""
    
    def __init__(self, model: str = "gpt-4o-mini"):
        self.llm = ChatOpenAI(
            model=model,
            temperature=0,
            api_key=os.getenv("OPENAI_API_KEY")
        )
    
    def parse_query(self, user_query: str) -> ParsedFlightQuery:
        """
        Parse a natural language query into flight search parameters.
        
        Args:
            user_query: Natural language like "Find me flights from Lagos to London next Friday"
            
        Returns:
            ParsedFlightQuery with extracted parameters
        """
        
        # Get current date for reference
        today = datetime.now()
        
        system_prompt = f"""You are a flight search query parser. Extract flight search parameters from the user's query.

Current date: {today.strftime('%Y-%m-%d')} ({today.strftime('%A')})

Return a JSON object with these fields:
- origin: Origin city or airport (string)
- destination: Destination city or airport (string)
- departure_date: Date in YYYY-MM-DD format
- return_date: Return date in YYYY-MM-DD format, or null for one-way
- adults: Number of adult passengers (default 1)
- travel_class: ECONOMY, PREMIUM_ECONOMY, BUSINESS, or FIRST (default ECONOMY)
- flexible_dates: true if user wants to search nearby dates for better prices
- nonstop_only: true if user only wants direct flights
- max_price: Maximum price in GBP if specified, or null
- preferred_time: morning, afternoon, evening, night, or any

Date interpretation rules:
- "next week" = 7 days from today
- "next month" = first day of next month
- "next Friday" = the coming Friday
- "in 2 weeks" = 14 days from today
- If no specific date, assume 2 weeks from today

Examples:
- "Lagos to London next Friday" → origin: "Lagos", destination: "London", departure_date: "[next Friday's date]"
- "cheap flights to Dubai flexible dates" → flexible_dates: true
- "direct flight to Manchester" → nonstop_only: true
- "business class to Paris" → travel_class: "BUSINESS"

Return ONLY valid JSON, no other text."""

        try:
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_query)
            ])
            
            # Parse JSON response
            result = json.loads(response.content)
            
            # Resolve airport codes
            origin_code = resolve_airport(result.get("origin", ""))
            dest_code = resolve_airport(result.get("destination", ""))
            
            if not origin_code:
                return ParsedFlightQuery(
                    origin="", origin_name="", destination="", destination_name="",
                    departure_date="",
                    is_valid=False,
                    error_message=f"Could not find airport for origin: {result.get('origin', 'unknown')}"
                )
            
            if not dest_code:
                return ParsedFlightQuery(
                    origin="", origin_name="", destination="", destination_name="",
                    departure_date="",
                    is_valid=False,
                    error_message=f"Could not find airport for destination: {result.get('destination', 'unknown')}"
                )
            
            origin_info = AIRPORTS.get(origin_code, {})
            dest_info = AIRPORTS.get(dest_code, {})
            
            return ParsedFlightQuery(
                origin=origin_code,
                origin_name=f"{origin_info.get('city', origin_code)} ({origin_code})",
                destination=dest_code,
                destination_name=f"{dest_info.get('city', dest_code)} ({dest_code})",
                departure_date=result.get("departure_date"),
                return_date=result.get("return_date"),
                adults=result.get("adults", 1),
                travel_class=result.get("travel_class", "ECONOMY"),
                flexible_dates=result.get("flexible_dates", False),
                flexibility_days=3,
                nonstop_only=result.get("nonstop_only", False),
                max_price=result.get("max_price"),
                preferred_time=result.get("preferred_time", "any"),
                is_valid=True
            )
            
        except json.JSONDecodeError as e:
            return ParsedFlightQuery(
                origin="", origin_name="", destination="", destination_name="",
                departure_date="",
                is_valid=False,
                error_message=f"Failed to parse response: {str(e)}"
            )
        except Exception as e:
            return ParsedFlightQuery(
                origin="", origin_name="", destination="", destination_name="",
                departure_date="",
                is_valid=False,
                error_message=f"Error: {str(e)}"
            )
    
    def get_clarification_questions(self, parsed: ParsedFlightQuery) -> list:
        """Get questions to ask if query is incomplete."""
        questions = []
        
        if not parsed.origin:
            questions.append("Where will you be flying from?")
        
        if not parsed.destination:
            questions.append("Where do you want to fly to?")
        
        if not parsed.departure_date:
            questions.append("When do you want to travel?")
        
        return questions


class SimpleQueryParser:
    """Simpler regex-based parser for when LLM is not needed."""
    
    @staticmethod
    def parse_simple(origin: str, destination: str, date: str, 
                     return_date: str = None, adults: int = 1) -> ParsedFlightQuery:
        """
        Parse explicit parameters without using LLM.
        
        Args:
            origin: Origin city or airport code
            destination: Destination city or airport code
            date: Departure date (YYYY-MM-DD)
            return_date: Optional return date
            adults: Number of passengers
        """
        origin_code = resolve_airport(origin)
        dest_code = resolve_airport(destination)
        
        if not origin_code:
            return ParsedFlightQuery(
                origin="", origin_name="", destination="", destination_name="",
                departure_date="",
                is_valid=False,
                error_message=f"Unknown origin: {origin}. Try using airport code (e.g., LOS, LHR)"
            )
        
        if not dest_code:
            return ParsedFlightQuery(
                origin="", origin_name="", destination="", destination_name="",
                departure_date="",
                is_valid=False,
                error_message=f"Unknown destination: {destination}. Try using airport code (e.g., LOS, LHR)"
            )
        
        origin_info = AIRPORTS.get(origin_code, {})
        dest_info = AIRPORTS.get(dest_code, {})
        
        return ParsedFlightQuery(
            origin=origin_code,
            origin_name=f"{origin_info.get('city', origin_code)} ({origin_code})",
            destination=dest_code,
            destination_name=f"{dest_info.get('city', dest_code)} ({dest_code})",
            departure_date=date,
            return_date=return_date,
            adults=adults,
            is_valid=True
        )
