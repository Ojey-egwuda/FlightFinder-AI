"""
FlightFinder - AI-Powered Flight Search
Mobile-friendly version - No sidebar
"""

import streamlit as st
from datetime import datetime, timedelta
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.apis.amadeus import AmadeusAPI, AIRPORTS, get_airport_info
from src.agents.ranking import FlightRankingAgent, FlightPreferences
from src.tools.travel_tools import CurrencyConverter, TimeZoneCalculator, WeatherTool

# Page config - no sidebar
st.set_page_config(
    page_title="FlightFinder AI",
    page_icon="✈️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Hide sidebar completely + Mobile CSS
st.markdown("""
<style>
    [data-testid="stSidebar"] {display: none;}
    #MainMenu, footer, header {visibility: hidden;}
    
    /* Max-width for desktop - prevents stretching on wide screens */
    .block-container {
        max-width: 700px !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        text-align: center;
        color: white;
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 1.8rem;
    }
    
    .main-header p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
    }
    
    .footer {
        text-align: center;
        padding: 1.5rem;
        margin-top: 2rem;
        border-top: 1px solid #dee2e6;
        color: #6c757d;
    }
    
    .footer a {
        color: #667eea;
        text-decoration: none;
        font-weight: 600;
    }
    
    /* Mobile optimizations */
    .stButton > button {
        width: 100%;
        min-height: 50px;
        font-size: 16px !important;
    }
    
    .stSelectbox, .stDateInput, .stNumberInput {
        font-size: 16px !important;
    }
    
    [data-testid="stMetricValue"] {
        font-size: 1.2rem !important;
    }
    
    /* Tablet - slightly wider */
    @media (min-width: 768px) {
        .block-container {
            max-width: 800px !important;
        }
    }
</style>
""", unsafe_allow_html=True)


def get_airport_options():
    """Get airport options sorted alphabetically by city."""
    options = {}
    for code, info in sorted(AIRPORTS.items(), key=lambda x: x[1]["city"]):
        label = f"{info['city']} ({code}) - {info['country']}"
        options[label] = code
    return options


def format_time(dt_string):
    try:
        dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
        return dt.strftime("%H:%M")
    except:
        return dt_string


def format_date(dt_string):
    try:
        dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
        return dt.strftime("%a, %d %b")
    except:
        return dt_string


def display_flight(flight, ranker, is_best=False):
    """Display flight - Mobile friendly."""
    summary = ranker.get_flight_summary(flight)
    scores = flight.get("ranking", {}).get("scores", {})
    itinerary = flight["itineraries"][0]
    first_seg = itinerary["segments"][0]
    last_seg = itinerary["segments"][-1]
    
    origin_info = get_airport_info(first_seg["departure"]["airport"])
    dest_info = get_airport_info(last_seg["arrival"]["airport"])
    
    stops = itinerary['stops']
    stops_text = "Direct ✈️" if stops == 0 else f"{stops} Stop{'s' if stops > 1 else ''}"
    stops_color = "🟢" if stops == 0 else ("🟡" if stops == 1 else "🔴")
    
    if is_best:
        st.success("🏆 **BEST MATCH**")
    
    with st.container():
        st.markdown(f"### ✈️ {summary['airline']}")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Score", f"{summary['score']}/100")
        with col2:
            st.markdown(f"**{stops_color} {stops_text}**")
            st.caption(f"Duration: {summary['duration']}")
        
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**🛫 {first_seg['departure']['airport']}**")
            st.caption(origin_info['city'])
            st.markdown(f"🕐 {format_time(summary['departure'])}")
        with col2:
            st.markdown(f"**🛬 {last_seg['arrival']['airport']}**")
            st.caption(dest_info['city'])
            st.markdown(f"🕐 {format_time(summary['arrival'])}")
        
        st.markdown(f"📅 {format_date(summary['departure'])}")
        st.markdown(f"### 💰 {summary['price']}")
        
        with st.expander("📊 Score Breakdown"):
            col1, col2 = st.columns(2)
            with col1:
                st.metric("💰 Price", f"{scores.get('price', 0):.0f}")
                st.metric("⏱️ Duration", f"{scores.get('duration', 0):.0f}")
            with col2:
                st.metric("🔄 Stops", f"{scores.get('stops', 0):.0f}")
                st.metric("✈️ Airline", f"{scores.get('airline', 0):.0f}")
        
        st.divider()


def render_search_form():
    """Render the flight search form."""
    airport_options = get_airport_options()
    airport_labels = list(airport_options.keys())
    
    # Find defaults
    lagos_idx = next((i for i, l in enumerate(airport_labels) if "Lagos" in l), 0)
    london_idx = next((i for i, l in enumerate(airport_labels) if "Heathrow" in l), 1)
    
    st.markdown("### 📍 Route")
    origin_label = st.selectbox("From", airport_labels, index=lagos_idx, key="origin")
    origin_code = airport_options[origin_label]
    
    dest_label = st.selectbox("To", airport_labels, index=london_idx, key="dest")
    dest_code = airport_options[dest_label]
    
    st.markdown("### 📅 Dates")
    col1, col2 = st.columns(2)
    with col1:
        departure_date = st.date_input(
            "Depart", 
            value=datetime.now() + timedelta(days=14), 
            min_value=datetime.now(),
            key="dep_date"
        )
    with col2:
        return_date = st.date_input(
            "Return (optional)", 
            value=None, 
            min_value=departure_date,
            key="ret_date"
        )
    
    st.markdown("### ⚙️ Options")
    col1, col2 = st.columns(2)
    with col1:
        flexible_dates = st.checkbox("🔄 Flexible ±3 days", key="flex")
    with col2:
        nonstop_only = st.checkbox("⚡ Direct only", key="nonstop")
    
    col1, col2 = st.columns(2)
    with col1:
        adults = st.number_input("👥 Travelers", min_value=1, max_value=9, value=1, key="adults")
    with col2:
        travel_class = st.selectbox("💺 Class", ["ECONOMY", "PREMIUM_ECONOMY", "BUSINESS", "FIRST"], key="class")
    
    preferred_time = st.selectbox(
        "🕐 Preferred Time", 
        ["any", "morning", "afternoon", "evening"], 
        format_func=lambda x: x.title(),
        key="time_pref"
    )
    
    search_clicked = st.button("🔍 Search Flights", type="primary", use_container_width=True)
    
    return {
        "search_clicked": search_clicked,
        "origin_code": origin_code,
        "dest_code": dest_code,
        "departure_date": departure_date,
        "return_date": return_date,
        "flexible_dates": flexible_dates,
        "nonstop_only": nonstop_only,
        "adults": adults,
        "travel_class": travel_class,
        "preferred_time": preferred_time
    }


def render_tools_tab():
    """Render the Travel Tools tab."""
    st.markdown("### 🛠️ Travel Tools")
    
    tool_tab1, tool_tab2, tool_tab3 = st.tabs(["🌤️ Weather", "💱 Currency", "🕐 Timezone"])
    
    # WEATHER
    with tool_tab1:
        st.markdown("**Check destination weather**")
        
        airports = [f"{info['city']} ({code})" 
                   for code, info in sorted(AIRPORTS.items(), key=lambda x: x[1]['city'])]
        
        weather_dest = st.selectbox("Select Destination", airports, key="weather_dest")
        
        if st.button("🔍 Get Weather", type="primary", key="weather_btn", use_container_width=True):
            dest_code = weather_dest.split("(")[1].split(")")[0]
            
            api_key = os.getenv("OPENWEATHER_API_KEY")
            if not api_key:
                st.error("⚠️ Add OPENWEATHER_API_KEY to .env")
            else:
                weather_tool = WeatherTool(api_key)
                weather = weather_tool.get_weather(dest_code)
                
                if weather:
                    st.markdown(f"### {weather.icon} {weather.description}")
                    st.caption(f"📍 {weather.city}, {weather.country}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("🌡️ Temp", f"{weather.temp_celsius:.1f}°C")
                    with col2:
                        st.metric("💧 Humidity", f"{weather.humidity}%")
                else:
                    st.warning("⚠️ Weather not available for this location")
    
    # CURRENCY
    with tool_tab2:
        st.markdown("**Convert currencies**")
        
        currencies = ["GBP", "USD", "EUR", "NGN", "AED", "QAR", "TRY", "GEL", "JPY", "SGD", "CAD", "ZAR"]
        
        amount = st.number_input("Amount", min_value=0.0, value=100.0, step=10.0, key="curr_amt")
        
        col1, col2 = st.columns(2)
        with col1:
            from_curr = st.selectbox("From", currencies, index=0, key="from_c")
        with col2:
            to_curr = st.selectbox("To", currencies, index=3, key="to_c")
        
        if st.button("💱 Convert", type="primary", key="conv_btn", use_container_width=True):
            converter = CurrencyConverter()
            result = converter.convert(amount, from_curr, to_curr)
            st.success(f"**{result['original']}** = **{result['converted']}**")
            st.caption(f"Rate: 1 {from_curr} = {result['rate']:.4f} {to_curr}")
    
    # TIMEZONE
    with tool_tab3:
        st.markdown("**Check time differences**")
        
        airports = [f"{info['city']} ({code})" 
                   for code, info in sorted(AIRPORTS.items(), key=lambda x: x[1]['city'])]
        
        col1, col2 = st.columns(2)
        with col1:
            tz_from = st.selectbox("From", airports, key="tz_from")
        with col2:
            tz_to = st.selectbox("To", airports, index=10, key="tz_to")
        
        if st.button("🕐 Calculate", type="primary", key="tz_btn", use_container_width=True):
            from_code = tz_from.split("(")[1].split(")")[0]
            to_code = tz_to.split("(")[1].split(")")[0]
            tz_calc = TimeZoneCalculator()
            result = tz_calc.get_time_difference(from_code, to_code)
            
            if "error" in result:
                st.warning(f"⚠️ {result['error']}")
            else:
                diff = result['difference_hours']
                if diff > 0:
                    st.success(f"**{to_code}** is **{diff}h ahead** of {from_code}")
                elif diff < 0:
                    st.warning(f"**{to_code}** is **{abs(diff)}h behind** {from_code}")
                else:
                    st.info("**Same timezone**")


def render_footer():
    """Render the footer."""
    st.markdown("""
    <div class="footer">
        <h4>🤖 Contact the Developer</h4>
        <p>Connect with <strong>Ojonugwa Egwuda</strong> on 
            <a href="https://www.linkedin.com/in/egwudaojonugwa/" target="_blank">LinkedIn</a>
        </p>
        <small>© 2025 FlightFinder AI | Built with ❤️ using Streamlit & Claude</small>
    </div>
    """, unsafe_allow_html=True)


def main():
    # Initialize session state
    if "search_results" not in st.session_state:
        st.session_state.search_results = None
    if "search_performed" not in st.session_state:
        st.session_state.search_performed = False
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>✈️ FlightFinder AI</h1>
        <p>Smart flight search with AI-powered recommendations</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Main tabs
    tab_search, tab_tools = st.tabs(["✈️ Search Flights", "🛠️ Tools"])
    
    # TOOLS TAB
    with tab_tools:
        render_tools_tab()
    
    # SEARCH TAB
    with tab_search:
        # Check credentials
        if not os.getenv("AMADEUS_CLIENT_ID") or not os.getenv("AMADEUS_CLIENT_SECRET"):
            st.error("⚠️ Add AMADEUS_CLIENT_ID and AMADEUS_CLIENT_SECRET to .env")
            st.markdown("[Get free API keys →](https://developers.amadeus.com/)")
            render_footer()
            st.stop()
        
        # Show search form or results
        if not st.session_state.search_performed:
            # Search form
            form_data = render_search_form()
            
            if form_data["search_clicked"]:
                with st.spinner("✈️ Searching flights..."):
                    try:
                        amadeus = AmadeusAPI(sandbox=True)
                        prefs = FlightPreferences(
                            preferred_departure_time=form_data["preferred_time"], 
                            prefer_direct=form_data["nonstop_only"]
                        )
                        ranker = FlightRankingAgent(preferences=prefs)
                        
                        if form_data["flexible_dates"]:
                            flights = amadeus.search_flexible_dates(
                                origin=form_data["origin_code"],
                                destination=form_data["dest_code"],
                                target_date=form_data["departure_date"].strftime("%Y-%m-%d"),
                                adults=form_data["adults"],
                                nonstop_only=form_data["nonstop_only"]
                            )
                        else:
                            result = amadeus.search_flights(
                                origin=form_data["origin_code"],
                                destination=form_data["dest_code"],
                                departure_date=form_data["departure_date"].strftime("%Y-%m-%d"),
                                return_date=form_data["return_date"].strftime("%Y-%m-%d") if form_data["return_date"] else None,
                                adults=form_data["adults"],
                                travel_class=form_data["travel_class"],
                                nonstop_only=form_data["nonstop_only"]
                            )
                            if result.get("error"):
                                st.error(f"❌ {result.get('message')}")
                                render_footer()
                                st.stop()
                            flights = result.get("offers", [])
                        
                        if not flights:
                            st.warning("😕 No flights found. Try different dates.")
                            render_footer()
                            st.stop()
                        
                        st.session_state.search_results = {
                            "flights": ranker.rank_flights(flights),
                            "ranker": ranker,
                            "query": {
                                "origin_code": form_data["origin_code"],
                                "dest_code": form_data["dest_code"],
                                "origin_city": AIRPORTS[form_data["origin_code"]]["city"],
                                "dest_city": AIRPORTS[form_data["dest_code"]]["city"],
                                "formatted_date": form_data["departure_date"].strftime("%d %b %Y")
                            }
                        }
                        st.session_state.search_performed = True
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
        
        else:
            # Show results
            results = st.session_state.search_results
            flights = results["flights"]
            ranker = results["ranker"]
            query = results["query"]

            # Back button
            if st.button("← New Search", use_container_width=True):
                st.session_state.search_performed = False
                st.session_state.search_results = None
                st.rerun()

            # Results header
            st.markdown(f"### ✈️ {query['origin_city']} → {query['dest_city']}")
            st.caption(f"📅 {query['formatted_date']} • {len(flights)} flights found")

            # Quick stats (based on full unfiltered set)
            col1, col2 = st.columns(2)
            with col1:
                best_price = min(f["price"]["total"] for f in flights)
                st.metric("💰 From", f"£{best_price:.0f}")
            with col2:
                direct_count = sum(1 for f in flights if f["itineraries"][0]["stops"] == 0)
                st.metric("🎯 Direct", direct_count)

            st.markdown("---")

            # ---- Filter panel ----
            all_airlines = sorted({
                f["itineraries"][0]["segments"][0]["carrier"]["name"]
                for f in flights
            })
            all_prices = [f["price"]["total"] for f in flights]
            price_min, price_max = int(min(all_prices)), int(max(all_prices)) + 1

            with st.expander("🔍 Filter Results", expanded=False):
                selected_airlines = st.multiselect(
                    "Airlines", all_airlines, default=all_airlines, key="filter_airline"
                )
                stops_options = ["Any", "Direct only", "1 stop max", "2 stops max"]
                stops_choice = st.selectbox("Max stops", stops_options, index=0, key="filter_stops")
                price_limit = st.slider(
                    "Max price (£)", min_value=price_min, max_value=price_max,
                    value=price_max, key="filter_price"
                )

            # Map stops choice → max integer
            stops_map = {"Any": 99, "Direct only": 0, "1 stop max": 1, "2 stops max": 2}
            max_stops_int = stops_map[stops_choice]

            filtered = [
                f for f in flights
                if f["itineraries"][0]["segments"][0]["carrier"]["name"] in selected_airlines
                and f["itineraries"][0]["stops"] <= max_stops_int
                and f["price"]["total"] <= price_limit
            ]

            if not filtered:
                st.warning("No flights match your filters. Try relaxing them.")
            else:
                st.caption(f"Showing {min(10, len(filtered))} of {len(filtered)} matching flights")

                # AI Recommendation (on filtered set)
                with st.expander("💡 AI Recommendation", expanded=True):
                    st.markdown(ranker.explain_recommendation(filtered[0], filtered))

                # Flight list
                st.markdown("### 📋 Results")
                for i, flight in enumerate(filtered[:10]):
                    display_flight(flight, ranker, is_best=(i == 0))

                if len(filtered) > 10:
                    st.info(f"Showing top 10 of {len(filtered)} matching flights")
    
    render_footer()


if __name__ == "__main__":
    main()