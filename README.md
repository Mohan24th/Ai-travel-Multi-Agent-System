
# AI Travel Planning System using LangGraph + MCP

This project is a Real-World Multi-Agent AI System built using **LangGraph** and the **Model Context Protocol (MCP)**.

The system uses 4 AI agents that work together to plan a complete trip automatically. Tool access is provided through three MCP servers (Tavily, AviationStack, and a custom OpenWeather server) instead of in-process function calls.

## Live Demo

https://ai-travel-multi-agent-system.streamlit.app/

## Features

- ✈️ Flight Search Agent (AviationStack via MCP)
- 🏨 Hotel Search Agent (Tavily via MCP)
- 🌦️ Weather Agent (custom OpenWeather MCP server)
- 🗓️ Itinerary Planning Agent
- 🧠 In-memory state management using LangGraph `MemorySaver`
- 💻 Streamlit Web Interface
- 🔌 Pluggable MCP-based tool layer

---

# Tech Stack

- **Orchestration:** LangGraph
- **LLM:** Groq — `openai/gpt-oss-120b`
- **Memory:** LangGraph `MemorySaver` (in-memory)
- **Tooling (MCP):**
  - Tavily MCP (HTTP transport)
  - AviationStack MCP (local stdio)
  - Custom OpenWeather MCP server (local stdio)
- **MCP client:** `langchain-mcp-adapters` (`MultiServerMCPClient`)
- **Frontend:** Streamlit

---

# Architecture

```text
┌────────────┐
│  User Query │
└─────┬──────┘
      ▼
┌────────────┐
│ LangGraph  │
│   Graph    │
└─────┬──────┘
      │
      ├── flight_agent    ──▶ AviationStack MCP (stdio)
      │
      ├── hotel_agent     ──▶ Tavily MCP        (HTTP)
      │
      ├── weather_agent   ──▶ OpenWeather MCP   (stdio, custom)
      │
      └── itinerary_agent ──▶ Groq GPT OSS 120B
````

The agents execute through the following workflow:

```text
START
  ↓
flight_agent
  ↓
hotel_agent
  ↓
weather_agent
  ↓
itinerary_agent
  ↓
END
```

All MCP wiring lives in `mcp_client.py`. To add or swap a tool, edit the server configuration there — no agent code change is required.

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
            langchain-mcp-adapters mcp python-dotenv \
            tavily-python requests streamlit
```

The AviationStack MCP server (`aviationstack-mcp/`) is a sibling sub-repo — install it inside the same environment:

```bash
pip install -e ./aviationstack-mcp
```

---

# Step 3: Setup `.env` File

Create a `.env` file inside the project folder:

```env
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
AVIATIONSTACK_API_KEY=your_aviationstack_api_key
OPENWEATHER_API_KEY=your_openweather_api_key
```

The MCP client loads these environment variables at startup and raises an error if required keys are missing.

---

# Step 4: Get API Keys

| Service       | URL                                                              |
| ------------- | ---------------------------------------------------------------- |
| Groq          | [https://console.groq.com](https://console.groq.com)             |
| Tavily        | [https://tavily.com](https://tavily.com)                         |
| AviationStack | [https://aviationstack.com](https://aviationstack.com)           |
| OpenWeather   | [https://openweathermap.org/api](https://openweathermap.org/api) |

---

# Step 5: MCP Servers

The system uses three MCP servers, configured in `mcp_client.py`.

### 5.1 Tavily MCP (HTTP)

Remote server, no local installation required.

```python
"tavily": {
    "transport": "streamable_http",
    "url": f"https://mcp.tavily.com/mcp/?tavilyApiKey={TAVILY_API_KEY}"
}
```

### 5.2 AviationStack MCP (local stdio)

Local Python package launched as a subprocess.

```python
"aviationstack": {
    "transport": "stdio",
    "command": "/path/to/your/venv/bin/python",
    "args": ["-m", "aviationstack_mcp", "mcp", "run"],
    "env": {
        "AVIATIONSTACK_API_KEY": AVIATION_STACK_API_KEY
    }
}
```

Make sure `aviationstack-mcp/` is installed in the same Python environment used by the command.

### 5.3 Custom OpenWeather MCP server (local stdio)

A FastMCP server in `custom_weather_mcp_server.py` exposing:

```text
get_current_weather
get_forecast
```

Example configuration:

```python
"weather": {
    "transport": "stdio",
    "command": "/path/to/your/venv/bin/python",
    "args": ["/absolute/path/to/custom_weather_mcp_server.py"],
    "env": {
        "OPENWEATHER_API_KEY": OPENWEATHER_API_KEY
    }
}
```

> **macOS / Linux:** use the virtual environment's `bin/python` path.
> **Windows:** use the environment's `Scripts\python.exe` path.

---

# Step 6: Run the Application

**Terminal (CLI)**

```bash
python main.py
```

**Streamlit Web App**

```bash
streamlit run frontend.py
```

**Example prompt**

```text
Plan a complete 7 days Japan trip including flights, hotels and sightseeing under 2 lakhs.
```

---

# Project Workflow

1. **flight_agent** — pulls airport and airline data from the AviationStack MCP, then asks the LLM to summarize likely routes, durations, and fares.
2. **hotel_agent** — queries the Tavily MCP for hotel recommendations.
3. **weather_agent** — calls the custom OpenWeather MCP for current weather and forecast at the destination.
4. **itinerary_agent** — synthesizes flights + hotels + weather into a day-by-day travel plan.
5. **MemorySaver** — maintains LangGraph state in memory using a `thread_id` during application execution.

---

# Project Structure

```text
.
├── main.py                       # LangGraph graph, state, agents
├── mcp_client.py                 # MultiServerMCPClient + tool wrappers
├── custom_weather_mcp_server.py  # FastMCP server (OpenWeather)
├── aviationstack-mcp/            # Sibling sub-repo (AviationStack MCP)
├── frontend.py                   # Streamlit UI
├── tools/                        # Legacy in-process tools (kept for reference)
├── travel_plans/                 # Saved itineraries (auto-generated)
└── .env                          # API keys
```

---

# Troubleshooting

**`TypeError: expected string or bytes-like object, got 'NoneType'` from `langchain_mcp_adapters.sessions`**

One of the environment variables (`TAVILY_API_KEY`, `AVIATIONSTACK_API_KEY`, `OPENWEATHER_API_KEY`) is missing or empty.

Verify your `.env` file or Streamlit Cloud Secrets.

---

**MCP server fails to start on macOS / Linux**

The most common cause is an incorrect Python path in `mcp_client.py`.

Make sure the `command` points to the Python executable inside your active virtual environment.

For example:

```text
/Users/you/venvs/ai_env/bin/python
```

On Windows:

```text
C:\path\to\venv\Scripts\python.exe
```

---

**Streamlit deployment**

For Streamlit Cloud, configure the required API keys under:

```text
App → Settings → Secrets
```

The current deployed application uses `MemorySaver`, so a PostgreSQL `DATABASE_URL` is not required.

---

# Live Application

[https://ai-travel-multi-agent-system.streamlit.app/](https://ai-travel-multi-agent-system.streamlit.app/)

```
```
