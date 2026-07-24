# AI Travel Planning System using LangGraph + MCP

This project is a Real-World Multi-Agent AI System built using **LangGraph** and the **Model Context Protocol (MCP)**.

The system uses 4 AI agents that work together to plan a complete trip automatically. Tool access is provided through three MCP servers (Tavily, AviationStack, and a custom OpenWeather server) instead of in-process function calls.

## Features

- ✈️ Flight Search Agent (AviationStack via MCP)
- 🏨 Hotel Search Agent (Tavily via MCP)
- 🌦️ Weather Agent (custom OpenWeather MCP server)
- 🗓️ Itinerary Planning Agent
- 🧠 Long-term memory using PostgreSQL (`langgraph-checkpoint-postgres`)
- 💻 Streamlit Web Interface
- 🔌 Pluggable MCP-based tool layer

---

# Tech Stack

- **Orchestration:** LangGraph
- **LLM:** Groq — `llama-3.3-70b-versatile`
- **Memory:** PostgreSQL + `langgraph-checkpoint-postgres`
- **Tooling (MCP):**
  - Tavily MCP (HTTP transport)
  - AviationStack MCP (local stdio)
  - Custom OpenWeather MCP server (local stdio)
- **MCP client:** `langchain-mcp-adapters` (`MultiServerMCPClient`)
- **Frontend:** Streamlit

---

# Architecture

```
┌────────────┐
│  User Query │
└─────┬──────┘
      ▼
┌────────────┐  PostgresSaver  ┌──────────┐
│ LangGraph  │◀───────────────▶│ Postgres │
│   Graph    │   checkpoints   └──────────┘
└─────┬──────┘
      │
      ├── flight_agent   ──▶ AviationStack MCP (stdio)
      ├── hotel_agent    ──▶ Tavily MCP        (HTTP)
      ├── weather_agent  ──▶ OpenWeather MCP   (stdio, custom)
      └── itinerary_agent ──▶ Groq LLM
```

All MCP wiring lives in `mcp_client.py`. To add or swap a tool, edit the server config there — no agent code change required.

---

# Step 1: Create Python Environment

Open the terminal inside the project folder and run:

```bash
python -m venv langgraph_env3
```

Activate it.

**macOS / Linux**

```bash
source langgraph_env3/bin/activate
```

**Windows**

```bash
langgraph_env3\Scripts\activate
```

---

# Step 2: Install Dependencies

```bash
pip install langgraph langchain langchain-openai langchain-groq langchain-community langchain-tavily \
            langchain-mcp-adapters mcp psycopg[binary] psycopg_pool python-dotenv \
            tavily-python requests streamlit

pip install -U "psycopg[binary,pool]" langgraph-checkpoint-postgres
```

The AviationStack MCP server (`aviationstack-mcp/`) is a sibling sub-repo — install it inside the same env:

```bash
pip install -e ./aviationstack-mcp
```

---

# Step 3: Install PostgreSQL

Download and install PostgreSQL: https://www.postgresql.org/download/

While installing PostgreSQL, remember:
- PostgreSQL password
- Port number

You will need them when building the connection string.

---

# Step 4: Create Database

```sql
CREATE DATABASE langgraph_memory_demo;
```

---

# Step 5: Setup `.env` File

Create a `.env` file inside the project folder with all five keys:

```env
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
AVIATIONSTACK_API_KEY=your_aviationstack_api_key
OPENWEATHER_API_KEY=your_openweather_api_key
DATABASE_URL=postgresql://postgres:postgres@localhost:5433/langgraph_memory_demo
```

The MCP client (`mcp_client.py`) loads these at import time and will raise a clear `RuntimeError` if any are missing.

---

# Step 6: Get API Keys

| Service       | URL                              |
| ------------- | -------------------------------- |
| Groq          | https://console.groq.com         |
| Tavily        | https://tavily.com               |
| AviationStack | https://aviationstack.com        |
| OpenWeather   | https://openweathermap.org/api   |

---

# Step 7: MCP Servers

The system uses three MCP servers, configured in `mcp_client.py`.

### 7.1 Tavily MCP (HTTP)
Remote server, no install. Configured via the `TAVILY_API_KEY` in the URL.

```python
"tavily": {
    "transport": "streamable_http",
    "url": f"https://mcp.tavily.com/mcp/?tavilyApiKey={TAVILY_API_KEY}"
}
```

### 7.2 AviationStack MCP (local stdio)
Local Python package launched as a subprocess.

```python
"aviationstack": {
    "transport": "stdio",
    "command": "/Users/amohan/Repos/venvs/ai_env/bin/python",   # adjust to your venv
    "args": ["-m", "aviationstack_mcp", "mcp", "run"],
    "env": {"AVIATIONSTACK_API_KEY": AVIATION_STACK_API_KEY}
}
```

Make sure `aviationstack-mcp/` is installed in the same Python the `command` points at.

### 7.3 Custom OpenWeather MCP server (local stdio)
A small FastMCP server in `custom_weather_mcp_server.py` exposing two tools: `get_current_weather` and `get_forecast`.

```python
"weather": {
    "transport": "stdio",
    "command": "/Users/amohan/Repos/venvs/ai_env/bin/python",   # adjust to your venv
    "args": ["/absolute/path/to/custom_weather_mcp_server.py"],
    "env": {"OPENWEATHER_API_KEY": OPENWEATHER_API_KEY}
}
```

> **macOS / Linux note:** use the venv's `bin/python` path, e.g. `/Users/you/venvs/ai_env/bin/python`. On Windows use `…\Scripts\python.exe`.

---

# Step 8: Run the Application

**Terminal (CLI)**

```bash
python main.py
```

**Streamlit Web App**

```bash
streamlit run frontend.py
```

**Example prompt**

```
Plan a complete 7 days Japan trip including flights, hotels and sightseeing under 2 lakhs.
```

---

# Project Workflow

1. **flight_agent** — pulls airport and airline data from the AviationStack MCP, then asks the LLM to summarize likely routes, durations, and fares.
2. **hotel_agent** — queries the Tavily MCP for hotel recommendations.
3. **weather_agent** — calls the custom OpenWeather MCP for current weather and forecast at the destination.
4. **itinerary_agent** — synthesizes flights + hotels + weather into a day-by-day plan.
5. PostgreSQL stores conversation memory via `PostgresSaver`, so prior turns in the same `thread_id` are available to later runs.

---

# Project Structure

```
.
├── main.py                       # LangGraph graph, state, agents
├── mcp_client.py                 # MultiServerMCPClient + tool wrappers
├── custom_weather_mcp_server.py  # FastMCP server (OpenWeather)
├── aviationstack-mcp/            # Sibling sub-repo (AviationStack MCP)
├── frontend.py                   # Streamlit UI
├── tools/                        # Legacy in-process tools (kept for reference)
├── travel_plans/                 # Saved itineraries (auto-generated)
└── .env                          # API keys + DATABASE_URL
```

---

# Troubleshooting

**`TypeError: expected string or bytes-like object, got 'NoneType'` from `langchain_mcp_adapters.sessions`**
One of the env vars (`TAVILY_API_KEY`, `AVIATIONSTACK_API_KEY`, `OPENWEATHER_API_KEY`) is missing or empty. The new `mcp_client.py` will now raise a clear `RuntimeError` at import time instead.

**MCP server fails to start on macOS / Linux**
The most common cause is a Windows path in `mcp_client.py` (`E:\…\.venv\Scripts\python.exe`). Update the `command` to your local venv's Python.

**Postgres connection error**
Verify `DATABASE_URL` matches the user / password / port / dbname you created in Steps 3 and 4.
