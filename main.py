# LangGraph Multi-Agent Travel Booking System
# Streamlit-friendly version with in-memory LangGraph memory

import os
from typing import TypedDict, Annotated
import operator
import asyncio
import uuid

from dotenv import load_dotenv

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from langchain_core.messages import (
    AnyMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
)

from langchain_groq import ChatGroq

from mcp_client import (
    tavily_mcp_search,
    get_airports,
    get_airlines,
    aviation_mcp_call,
    extract_destination,
    forecast_mcp_search,
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
    temperature=0
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
You are a travel flight expert.

User Query:
{query}

Airport Information:
{airport_data}

Airline Information:
{airline_data}

Generate:

1. Likely departure airport
2. Likely arrival airport
3. Airlines serving this route
4. Typical flight duration
5. Estimated airfare range
6. Peak season pricing warning
7. Booking advice

Important:
- Do not invent specific flight numbers.
- Do not claim that a flight is currently available unless the tool data confirms it.
- Clearly label estimates as estimates.
- If the user's departure city is unknown, say that it is unknown.

Return concise travel guidance.
"""


def flight_agent(state: TravelState):

    print("\nINSIDE FLIGHT AGENT\n")

    query = state["user_query"]

    try:

        airports = asyncio.run(
            aviation_mcp_call(
                "list_airports"
            )
        )

        airlines = asyncio.run(
            aviation_mcp_call(
                "list_airlines"
            )
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
Current Weather:
{weather_data}

Forecast:
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

User Query:
{state['user_query']}

Flight Results:
{state['flight_results']}

Hotel Results:
{state['hotel_results']}

Weather Information:
{state['weather_results']}

Requirements:

- Create a practical day-by-day itinerary.
- Consider the weather information.
- Use the flight information only as guidance.
- Do not invent specific flight numbers.
- Do not present estimated prices as confirmed prices.
- Clearly distinguish recommendations from confirmed information.
- Include useful activities, food suggestions, transportation guidance,
  and approximate timing.
- If important information is missing, state the assumption.
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


# Add agents
graph.add_node(
    "flight_agent",
    flight_agent
)

graph.add_node(
    "hotel_agent",
    hotel_agent
)

graph.add_node(
    "weather_agent",
    weather_agent
)

graph.add_node(
    "itinerary_agent",
    itinerary_agent
)


# Workflow
graph.add_edge(
    START,
    "flight_agent"
)

graph.add_edge(
    "flight_agent",
    "hotel_agent"
)

graph.add_edge(
    "hotel_agent",
    "weather_agent"
)

graph.add_edge(
    "weather_agent",
    "itinerary_agent"
)

graph.add_edge(
    "itinerary_agent",
    END
)


# ============================================================
# IN-MEMORY CHECKPOINTER
# ============================================================

# No PostgreSQL required.
#
# This stores LangGraph state in memory while
# the application is running.

checkpointer = MemorySaver()


# Compile graph
app = graph.compile(
    checkpointer=checkpointer
)


# ============================================================
# CLI MODE
# ============================================================

if __name__ == "__main__":

    config = {
        "configurable": {
            "thread_id": str(uuid.uuid4())
        }
    }

    user_input = input(
        "Enter travel request: "
    )

    result = app.invoke(
        {
            "messages": [
                HumanMessage(
                    content=user_input
                )
            ],

            "user_query": user_input,

            "flight_results": "",

            "hotel_results": "",

            "weather_results": "",

            "itinerary": "",

            "llm_calls": 0,
        },

        config=config
    )

    print(
        "\nFINAL RESPONSE:\n"
    )

    print(
        result["itinerary"]
    )