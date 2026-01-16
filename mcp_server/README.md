# 🌍 Travel Assistant MCP Server

A Model Context Protocol (MCP) server providing travel-related tools for AI assistants.

## Features

| Tool                  | Description                               |
| --------------------- | ----------------------------------------- |
| `get_weather`         | Get current weather at any airport        |
| `convert_currency`    | Convert amounts between currencies        |
| `get_exchange_rate`   | Get current exchange rates                |
| `get_time_difference` | Get timezone differences between airports |
| `convert_flight_time` | Calculate arrival time in local timezone  |

## Installation

```bash
# Install dependencies
pip install mcp fastmcp requests

# Set environment variable for weather
export OPENWEATHER_API_KEY=your_key_here
```

## Usage

### With Claude Desktop

1. Find your Claude Desktop config file:

   - **Mac**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

2. Add this configuration:

```json
{
  "mcpServers": {
    "travel-assistant": {
      "command": "python",
      "args": ["-m", "mcp_server.travel_mcp"],
      "cwd": "/path/to/your/flightfinder",
      "env": {
        "OPENWEATHER_API_KEY": "your_key_here"
      }
    }
  }
}
```

3. Restart Claude Desktop

4. You'll see the travel tools available in Claude!

### With Cursor

Add to your `.cursor/mcp.json`:

```json
{
  "servers": {
    "travel-assistant": {
      "command": "python",
      "args": ["-m", "mcp_server.travel_mcp"],
      "cwd": "/path/to/flightfinder"
    }
  }
}
```

### Standalone Testing

```bash
# Run the MCP server directly
cd flightfinder
python -m mcp_server.travel_mcp

# Or test with MCP Inspector
npx @modelcontextprotocol/inspector python -m mcp_server.travel_mcp
```

## Tool Examples

### Get Weather

```
User: What's the weather like in Dubai?

Tool call: get_weather(airport_code="DXB")

Response: ☀️ Clear Sky - 32°C, Humidity 45%, Wind 3.2 m/s
```

### Convert Currency

```
User: How much is £500 in Nigerian Naira?

Tool call: convert_currency(amount=500, from_currency="GBP", to_currency="NGN")

Response: £500.00 GBP = ₦980,379.75 NGN (Rate: 1 GBP = 1960.76 NGN)
```

### Time Zone Calculation

```
User: What's the time difference between Lagos and Dubai?

Tool call: get_time_difference(origin="LOS", destination="DXB")

Response:
- Lagos: WAT (UTC+1)
- Dubai: GST (UTC+4)
- Difference: 3 hours ahead
```

### Convert Flight Time

```
User: If I leave Lagos at 10:00 on a 7-hour flight to London, what time do I arrive?

Tool call: convert_flight_time(departure_time="10:00", origin="LOS", destination="LHR", flight_duration_hours=7)

Response:
- Departure: 10:00 (Lagos, WAT)
- Arrival: 16:00 (London, GMT)
- Flight: 7h 0m, Timezone change: -1 hour
```

## Supported Data

### Currencies (16)

USD, EUR, GBP, NGN, AED, QAR, TRY, GEL, RSD, JPY, SGD, CNY, MAD, CAD, INR, ZAR

### Airports with Weather (35+)

Nigeria, UK, Turkey, UAE, Qatar, Georgia, Serbia, Japan, Singapore, France, Netherlands, Germany, Spain, Italy, USA, Caribbean, Morocco, South Africa

### Travel Tips Resource

Access via `travel://tips/{country_code}` for GB, AE, GE, TR, NG, RS

## Architecture

```
┌─────────────────┐     ┌─────────────────┐
│  Claude/Cursor  │────▶│  MCP Protocol   │
└─────────────────┘     └────────┬────────┘
                                 │
                        ┌────────▼────────┐
                        │ Travel MCP      │
                        │ Server          │
                        └────────┬────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
┌───────▼───────┐    ┌───────────▼───────────┐    ┌──────▼──────┐
│    Weather    │    │ Currency Converter    │    │  Timezone   │
│  (OpenWeather)│    │   (Fallback rates)    │    │ Calculator  │
└───────────────┘    └───────────────────────┘    └─────────────┘
```

## Portfolio Value

This MCP server demonstrates:

- ✅ **MCP Protocol expertise** - Hot skill in AI/LLM space
- ✅ **API integration** - OpenWeather API
- ✅ **Tool design** - Clean, well-documented functions
- ✅ **Error handling** - Graceful fallbacks
- ✅ **Travel domain** - Practical, useful tools

## Author

**Ojonugwa Egwuda** - [LinkedIn](https://www.linkedin.com/in/egwudaojonugwa/)

Built for the FlightFinder project.

## License

MIT
