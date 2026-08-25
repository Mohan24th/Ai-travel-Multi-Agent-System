````md
# AI Travel Planning System using LangGraph + MCP

A multi-agent AI travel planning system built with LangGraph, Model Context Protocol (MCP), Groq, Tavily, AviationStack, OpenWeather, and Streamlit.

The application accepts a natural-language travel request and coordinates specialized agents to gather travel information and generate a complete day-by-day itinerary.

## Live Demo

https://ai-travel-multi-agent-system.streamlit.app/

## Overview

Instead of relying on a single LLM call, the system divides the travel-planning workflow into specialized agents:

1. Flight Agent
2. Hotel Agent
3. Weather Agent
4. Itinerary Agent

LangGraph manages the state and execution flow between these agents, while MCP provides a modular interface for external tools and services.

## Features

- Flight information and airline recommendations
- Hotel and accommodation search
- Current weather and forecast information
- Day-by-day itinerary generation
- Budget-aware travel planning
- Transportation and food recommendations
- LangGraph-based agent orchestration
- MCP-based external tool integration
- In-memory conversation checkpointing
- Streamlit web interface
- Markdown itinerary export
- Cloud deployment using Streamlit Community Cloud

## Architecture

```text
                         User Request
                              |
                              v
                       +--------------+
                       |  LangGraph   |
                       |    Graph     |
                       +------+-------+
                              |
                              v
                       +--------------+
                       | Flight Agent |
                       +------+-------+
                              |
                              v
                       +--------------+
                       | Hotel Agent  |
                       +------+-------+
                              |
                              v
                       +--------------+
                       |Weather Agent |
                       +------+-------+
                              |
                              v
                     +------------------+
                     | Itinerary Agent  |
                     +--------+---------+
                              |
                              v
                       Final Travel Plan
````

External tools are accessed through the MCP layer:

```text
                    Agent
                      |
                      v
                 MCP Client
                      |
          +-----------+-----------+
          |           |           |
          v           v           v
       Tavily    AviationStack  OpenWeather
```

## Agent Workflow

### 1. Flight Agent

The Flight Agent handles flight-related travel information.

It uses AviationStack data to provide:

* Likely departure airport
* Likely arrival airport
* Airlines serving the route
* Typical flight duration
* Estimated airfare range
* Peak-season pricing considerations
* Booking recommendations

The agent is instructed not to invent specific flight numbers or represent estimated prices as confirmed prices.

### 2. Hotel Agent

The Hotel Agent uses Tavily to search for accommodation information based on the user's travel request.

It provides:

* Hotel recommendations
* Recommended areas to stay
* Approximate accommodation costs
* Location-based suggestions
* Accommodation advice

### 3. Weather Agent

The Weather Agent extracts the destination from the user's request and retrieves weather information.

It provides:

* Current weather
* Weather forecast
* Destination-specific conditions

The weather information is passed to the itinerary agent so the final plan can account for expected conditions.

### 4. Itinerary Agent

The Itinerary Agent combines the information produced by the previous agents:

```text
User Query
    +
Flight Information
    +
Hotel Information
    +
Weather Information
```

It then generates a complete travel plan containing:

* Day-by-day activities
* Approximate timing
* Food recommendations
* Transportation guidance
* Budget estimates
* Travel tips
* Weather considerations
* Important assumptions

## MCP Integration

The project uses the Model Context Protocol to separate agent logic from external tool execution.

The MCP client is implemented using `MultiServerMCPClient` from `langchain-mcp-adapters`.

Current integrations include:

| Service       | Purpose              | Transport         |
| ------------- | -------------------- | ----------------- |
| Tavily        | Web and hotel search | Streamable HTTP   |
| AviationStack | Aviation information | MCP               |
| OpenWeather   | Weather and forecast | Custom MCP server |

MCP configuration and tool wrappers are maintained in:

```text
mcp_client.py
```

This makes the tool layer modular and allows external services to be changed without significantly modifying the agent workflow.

## LLM

The project currently uses Groq with GPT OSS 120B.

```python
from langchain_groq import ChatGroq

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0
)
```

The LLM is used for:

* Travel information interpretation
* Destination extraction
* Flight recommendations
* Itinerary generation
* Combining information from multiple agents

## Memory

The current version uses LangGraph's `MemorySaver` for in-memory checkpointing.

```python
from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()

app = graph.compile(
    checkpointer=checkpointer
)
```

Each execution uses a `thread_id` to identify the conversation state.

The current deployed version does not require PostgreSQL.

PostgreSQL-based persistent memory was part of an earlier implementation and can be added later as an upgrade.

## Technology Stack

| Component           | Technology                |
| ------------------- | ------------------------- |
| Language            | Python                    |
| Agent Orchestration | LangGraph                 |
| LLM                 | Groq GPT OSS 120B         |
| LLM Framework       | LangChain                 |
| Tool Protocol       | Model Context Protocol    |
| MCP Client          | langchain-mcp-adapters    |
| Web Search          | Tavily                    |
| Flight Data         | AviationStack             |
| Weather Data        | OpenWeather               |
| Memory              | LangGraph MemorySaver     |
| Frontend            | Streamlit                 |
| Deployment          | Streamlit Community Cloud |

## Project Structure

```text
AI-travel-multi-agent-system/
|
├── main.py
|   └── LangGraph state, agents and workflow
|
├── frontend.py
|   └── Streamlit web interface
|
├── mcp_client.py
|   └── MCP client and tool integrations
|
├── custom_weather_mcp_server.py
|   └── Custom OpenWeather MCP server
|
├── aviationstack-mcp/
|   └── AviationStack MCP implementation
|
├── requirements.txt
|
├── .env
|
└── README.md
```

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/Mohan24th/Ai-travel---Multi-Agent-System.git

cd Ai-travel---Multi-Agent-System
```

### 2. Create a virtual environment

```bash
python -m venv ai_env
```

Activate the environment.

macOS / Linux:

```bash
source ai_env/bin/activate
```

Windows:

```bash
ai_env\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

If the AviationStack MCP implementation is included as a local package:

```bash
pip install -e ./aviationstack-mcp
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
AVIATIONSTACK_API_KEY=your_aviationstack_api_key
OPENWEATHER_API_KEY=your_openweather_api_key
```

Do not commit `.env` or API keys to the repository.

## Running the Application

### CLI

```bash
python main.py
```

Example:

```text
Enter travel request: 7 day plan for Goa
```

### Streamlit

```bash
streamlit run frontend.py
```

## Example Prompts

```text
Plan a 7-day Japan trip under ₹2 lakhs.
```

```text
Create a 5-day Goa trip including hotels,
weather and sightseeing.
```

```text
Plan a 10-day Thailand trip with budget
accommodation and sightseeing.
```

```text
Create a weekend trip to Dubai with
hotel recommendations and activities.
```

## Example Output

The generated travel plan can include:

```text
Flight Recommendations

Hotel Recommendations

Current Weather and Forecast

Day-by-Day Itinerary

Budget Breakdown

Food Recommendations

Transportation Guidance

Packing Suggestions

Money-Saving Tips
```

## Reliability

The agents are designed to distinguish between confirmed information, estimates, recommendations, and assumptions.

For example, the Flight Agent is instructed to:

* Avoid inventing specific flight numbers
* Avoid claiming real-time availability without supporting tool data
* Clearly label estimated prices
* State when important information is unavailable

The Itinerary Agent similarly treats flight prices, hotel prices, travel times, and other generated values as estimates unless they are explicitly confirmed by tool data.

## Deployment

The application is deployed using Streamlit Community Cloud.

Live application:

[https://ai-travel-multi-agent-system.streamlit.app/](https://ai-travel-multi-agent-system.streamlit.app/)

The Streamlit entry point is:

```text
frontend.py
```

Configure the following secrets in Streamlit Cloud:

```toml
GROQ_API_KEY = "your_key"
TAVILY_API_KEY = "your_key"
AVIATIONSTACK_API_KEY = "your_key"
OPENWEATHER_API_KEY = "your_key"
```

`DATABASE_URL` is not required by the current deployed version because the application uses `MemorySaver`.

## Future Improvements

Possible future extensions include:

* Parallel execution of independent agents
* Dynamic router agent
* Dedicated budget optimization agent
* Real-time flight availability
* Real-time hotel availability
* Persistent PostgreSQL memory
* User authentication
* Saved travel plans
* Maps and route optimization
* PDF itinerary generation
* Calendar integration
* Booking links
* User-specific travel preferences
* Final itinerary validation agent

A future architecture could evolve toward:

```text
                         User Query
                              |
                              v
                        Router Agent
                              |
             +----------------+----------------+
             |                |                |
             v                v                v
        Flight Agent     Hotel Agent     Weather Agent
             |                |                |
             +----------------+----------------+
                              |
                              v
                       Budget Agent
                              |
                              v
                     Itinerary Agent
                              |
                              v
                    Validation Agent
                              |
                              v
                       Final Plan
```

## Project Status

| Component                  | Status    |
| -------------------------- | --------- |
| LangGraph orchestration    | Completed |
| Flight Agent               | Completed |
| Hotel Agent                | Completed |
| Weather Agent              | Completed |
| Itinerary Agent            | Completed |
| Groq GPT OSS 120B          | Completed |
| MCP integration            | Completed |
| Tavily integration         | Completed |
| AviationStack integration  | Completed |
| OpenWeather integration    | Completed |
| Streamlit frontend         | Completed |
| In-memory checkpointing    | Completed |
| Streamlit Cloud deployment | Completed |
| Persistent memory          | Planned   |
| Real-time booking          | Planned   |
| Authentication             | Planned   |
| Parallel agents            | Planned   |

## Author

**Mohan**

Computer Science / AI-ML Engineering Student

Areas of interest:

* Artificial Intelligence
* Machine Learning
* Generative AI
* Multi-Agent Systems
* LangGraph
* MCP
* Backend Engineering
* LLM Applications

## Live Demo

[https://ai-travel-multi-agent-system.streamlit.app/](https://ai-travel-multi-agent-system.streamlit.app/)

## Repository

[https://github.com/Mohan24th/Ai-travel---Multi-Agent-System](https://github.com/Mohan24th/Ai-travel---Multi-Agent-System)

```
```
