# ✈️ FlightFinder AI

An AI-powered flight search application that finds, ranks, and recommends the best flights based on your preferences.

![Python](https://img.shields.io/badge/Python-3.9+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red)
![License](https://img.shields.io/badge/License-MIT-green)

## ✨ Features

- **🎯 Smart Ranking** - AI scores flights on price, duration, stops, timing, and airline quality
- **📅 Flexible Dates** - Search ±3 days around your target date for better prices
- **🌍 70+ Airports** - Europe, Middle East, Asia, Caribbean, Africa & Americas
- **📱 Mobile-Friendly** - Responsive design works on any device
- **🛠️ Travel Tools** - Weather forecasts, currency converter, timezone calculator
- **🤖 MCP Server** - Model Context Protocol server for AI assistants

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/yourusername/flightfinder.git
cd flightfinder

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Mac/Linux
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Keys

```bash
# Copy example env file
cp .env.example .env

# Edit with your credentials
```

**Required:**

- `AMADEUS_CLIENT_ID` - Get free at [developers.amadeus.com](https://developers.amadeus.com/)
- `AMADEUS_CLIENT_SECRET`

**Recommended:**

- `OPENWEATHER_API_KEY` - Get free at [openweathermap.org](https://openweathermap.org/api)

**Optional:**

- `OPENAI_API_KEY` - For natural language search
- `EXCHANGERATE_API_KEY` - For live currency rates

### 3. Run the App

```bash
streamlit run frontend/app.py
```

Open http://localhost:8501 in your browser.

## 📱 Screenshots

The app features:

- Clean, mobile-first design
- Two tabs: Flight Search & Travel Tools
- AI-powered flight recommendations
- Weather, currency, and timezone tools

## 🌍 Supported Destinations

| Region         | Airports                                                         |
| -------------- | ---------------------------------------------------------------- |
| 🇳🇬 Nigeria     | Lagos (LOS), Abuja (ABV), Port Harcourt (PHC)                    |
| 🇬🇧 UK          | Heathrow (LHR), Gatwick (LGW), Manchester (MAN), Edinburgh (EDI) |
| 🏔️ Balkans     | Tbilisi (TBS), Belgrade (BEG), Tirana (TIA), Sarajevo (SJJ)      |
| 🇹🇷 Turkey      | Istanbul (IST), Antalya (AYT), Izmir (ADB)                       |
| 🌴 Caribbean   | Punta Cana (PUJ), Sint Maarten (SXM), Antigua (ANU)              |
| 🇦🇪 Middle East | Dubai (DXB), Doha (DOH), Abu Dhabi (AUH)                         |
| 🇯🇵 Asia        | Tokyo (HND), Singapore (SIN), Hong Kong (HKG)                    |
| 🇪🇺 Europe      | Paris (CDG), Amsterdam (AMS), Rome (FCO), Barcelona (BCN)        |

## 🎯 How Scoring Works

Each flight is scored on 5 dimensions (0-100):

| Factor      | Weight | Description                       |
| ----------- | ------ | --------------------------------- |
| 💰 Price    | 35%    | Lower price = higher score        |
| ⏱️ Duration | 25%    | Shorter flight = higher score     |
| 🔄 Stops    | 20%    | Fewer stops = higher score        |
| 🕐 Timing   | 10%    | Match to preferred departure time |
| ✈️ Airline  | 10%    | Airline service quality           |

## 🛠️ Travel Tools

| Tool        | Description                                       |
| ----------- | ------------------------------------------------- |
| 🌤️ Weather  | Current weather at destination (requires API key) |
| 💱 Currency | Convert between 16 currencies                     |
| 🕐 Timezone | Time differences between airports                 |

## 🤖 MCP Server

The project includes an MCP (Model Context Protocol) server for use with Claude Desktop, Cursor, or other AI assistants.

```bash
# Test the MCP server
python -m mcp_server.travel_mcp

# Or with MCP Inspector
npx @modelcontextprotocol/inspector python -m mcp_server.travel_mcp
```

See [mcp_server/README.md](mcp_server/README.md) for setup instructions.

## 💻 Command Line Usage

```bash
# Direct search
python -m src.main -o Lagos -d London --date 2026-02-15

# Flexible dates (±3 days)
python -m src.main -o Lagos -d London --date 2026-02-15 --flexible

# Direct flights only
python -m src.main -o Lagos -d London --date 2026-02-15 --direct

# Natural language (requires OpenAI API key)
python -m src.main --query "cheap flights to London next month"
```

## 📊 API Costs

| Service            | Free Tier   | Notes          |
| ------------------ | ----------- | -------------- |
| Amadeus Sandbox    | Unlimited   | Test data      |
| Amadeus Production | 2,000/month | Real flights   |
| OpenWeather        | 1,000/day   | Weather data   |
| OpenAI             | Pay per use | ~$0.0001/query |

## 🔧 Troubleshooting

**"Authentication failed"**

- Check API credentials in `.env`
- No extra spaces around values

**"No flights found"**

- Try different dates
- Some routes have limited service
- Sandbox has limited test data

**Import errors**

- Activate virtual environment
- Run `pip install -r requirements.txt`

## 🚀 Deployment

**Streamlit Cloud:**

1. Push to GitHub
2. Connect at [share.streamlit.io](https://share.streamlit.io)
3. Add secrets in dashboard

**Railway/Render:**

1. Connect GitHub repo
2. Set environment variables
3. Deploy

## 👤 Author

**Ojonugwa Egwuda**

- LinkedIn: [egwudaojonugwa](https://www.linkedin.com/in/egwudaojonugwa/)

## 📄 License

MIT License - feel free to use for your portfolio!

---

Built with ❤️ using Streamlit & Claude
