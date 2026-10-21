# ============================================================
# AI TRAVEL BOOKING SYSTEM
# LangGraph Multi-Agent Backend
# In-memory checkpointing for Streamlit Cloud
# ============================================================

import asyncio
import operator
from typing import Annotated, TypedDict

from dotenv import load_dotenv

from langchain_core.messages import (
    AIMessage,
    AnyMessage,
    HumanMessage,
    SystemMessage,
)
from langchain_groq import ChatGroq

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from mcp_client import (
    aviation_mcp_call,
    extract_destination,
    forecast_mcp_search,
    tavily_mcp_search,
    weather_mcp_search,
)


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv(override=True)


# ============================================================
# LLM
# ============================================================

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0,
)


# ============================================================
# STATE
# ============================================================

class TravelState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]

    user_query: str

    flight_results: str

    hotel_results: str

    weather_results: str

    itinerary: str

    llm_calls: int


# ============================================================
# FLIGHT AGENT
# ============================================================

FLIGHT_AGENT_PROMPT = """
You are an expert travel flight planner.

User Query:
{query}

Airport Information:
{airport_data}

Airline Information:
{airline_data}

Provide:

1. Likely departure airport
2. Likely arrival airport
3. Airlines serving the route
4. Typical flight duration
5. Estimated airfare range
6. Peak-season pricing warning
7. Booking advice

Rules:

- Do NOT invent specific flight numbers.
- Do NOT claim a flight is currently available unless tool
  information confirms it.
- Clearly label estimated prices as estimates.
- If departure location is unknown, say that it is unknown.
- Keep the response concise.
"""


def flight_agent(state: TravelState):

    print("INSIDE FLIGHT AGENT")

    query = state["user_query"]

    try:

        airports = asyncio.run(
            aviation_mcp_call("list_airports")
        )

        airlines = asyncio.run(
            aviation_mcp_call("list_airlines")
        )

        prompt = FLIGHT_AGENT_PROMPT.format(
            query=query,
            airport_data=str(airports)[:3000],
            airline_data=str(airlines)[:3000],
        )

        response = llm.invoke(
            [
                SystemMessage(
                    content="You are an expert travel flight planner."
                ),
                HumanMessage(
                    content=prompt
                ),
            ]
        )

        flight_data = response.content

    except Exception as e:

        flight_data = (
            f"Flight information unavailable: {str(e)}"
        )

    return {
        "flight_results": flight_data,

        "messages": [
            AIMessage(
                content="Flight recommendations generated"
            )
        ],

        "llm_calls": state.get("llm_calls", 0) + 1,
    }


# ============================================================
# HOTEL AGENT
# ============================================================

def hotel_agent(state: TravelState):

    query = (
        f"Best hotels for {state['user_query']}"
    )

    try:

        hotel_results = asyncio.run(
            tavily_mcp_search(query)
        )

    except Exception as e:

        hotel_results = (
            f"Hotel information unavailable: {str(e)}"
        )

    return {
        "hotel_results": hotel_results,

        "messages": [
            AIMessage(
                content="Hotel information fetched"
            )
        ],

        "llm_calls": state.get("llm_calls", 0) + 1,
    }


# ============================================================
# WEATHER AGENT
# ============================================================

def weather_agent(state: TravelState):

    try:

        city = extract_destination(
            state["user_query"]
        )

        weather_data = asyncio.run(
            weather_mcp_search(city)
        )

        forecast_data = asyncio.run(
            forecast_mcp_search(city)
        )

        weather_results = f"""
### Current Weather

{weather_data}

### Forecast

{forecast_data}
"""

    except Exception as e:

        weather_results = (
            f"Weather information unavailable: {str(e)}"
        )

    return {
        "weather_results": weather_results,

        "messages": [
            AIMessage(
                content="Weather information fetched"
            )
        ],
    }


# ============================================================
# ITINERARY AGENT
# ============================================================

def itinerary_agent(state: TravelState):

    prompt = f"""
Create a detailed travel itinerary.

USER REQUEST:
{state['user_query']}

FLIGHT INFORMATION:
{state['flight_results']}

HOTEL INFORMATION:
{state['hotel_results']}

WEATHER INFORMATION:
{state['weather_results']}

Requirements:

- Create a practical day-by-day itinerary.
- Consider the weather.
- Include sightseeing.
- Include food recommendations.
- Include transportation guidance.
- Include approximate timing.
- Use flight information only as guidance.
- Do NOT invent specific flight numbers.
- Do NOT present estimated prices as confirmed prices.
- Clearly distinguish recommendations from confirmed information.
- Mention assumptions when important information is missing.
- Make the final response easy to read using Markdown.
"""

    try:

        response = llm.invoke(
            [
                SystemMessage(
                    content="You are an expert travel planner."
                ),
                HumanMessage(
                    content=prompt
                ),
            ]
        )

        itinerary = response.content

    except Exception as e:

        itinerary = (
            f"Unable to generate itinerary: {str(e)}"
        )

    return {
        "itinerary": itinerary,

        "messages": [
            AIMessage(
                content=itinerary
            )
        ],

        "llm_calls": state.get("llm_calls", 0) + 1,
    }


# ============================================================
# LANGGRAPH
# ============================================================

graph = StateGraph(TravelState)


graph.add_node(
    "flight_agent",
    flight_agent,
)

graph.add_node(
    "hotel_agent",
    hotel_agent,
)

graph.add_node(
    "weather_agent",
    weather_agent,
)

graph.add_node(
    "itinerary_agent",
    itinerary_agent,
)


# ============================================================
# WORKFLOW
# ============================================================

graph.add_edge(
    START,
    "flight_agent",
)

graph.add_edge(
    "flight_agent",
    "hotel_agent",
)

graph.add_edge(
    "hotel_agent",
    "weather_agent",
)

graph.add_edge(
    "weather_agent",
    "itinerary_agent",
)

graph.add_edge(
    "itinerary_agent",
    END,
)


# ============================================================
# IN-MEMORY CHECKPOINT
# ============================================================

# No PostgreSQL.
# No psycopg.
# No DATABASE_URL.

checkpointer = MemorySaver()


app = graph.compile(
    checkpointer=checkpointer,
)