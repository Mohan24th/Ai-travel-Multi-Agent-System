# ============================================================
# AI TRAVEL PLANNING SYSTEM
# LangGraph Multi-Agent Backend
# ============================================================

import asyncio
import json
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
    timeout=30,
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

    flight_status: str
    hotel_status: str
    weather_status: str
    itinerary_status: str

    llm_calls: Annotated[int, operator.add]


# ============================================================
# MCP HELPERS
# ============================================================

MCP_TIMEOUT_SECONDS = 20


def run_mcp_with_timeout(coro, timeout: int = MCP_TIMEOUT_SECONDS):
    """Run an asynchronous MCP operation with a timeout."""
    return asyncio.run(asyncio.wait_for(coro, timeout=timeout))


def result_is_available(value) -> bool:
    """Check whether a tool returned usable data."""
    if value is None:
        return False

    rendered = str(value).strip()

    if not rendered:
        return False

    return not rendered.lower().startswith(
        ("error:", "failed:", "unavailable:")
    )


def format_hotel_results(raw_results) -> str:
    """
    Convert common Tavily MCP response formats into concise,
    readable research results while preserving source URLs.
    """
    if raw_results is None:
        return ""

    # MCP adapters commonly return a list of content blocks.
    if isinstance(raw_results, list):
        formatted_items = []

        for item in raw_results:
            if isinstance(item, dict):
                text_content = item.get("text", "")

                if not text_content:
                    formatted_items.append(
                        json.dumps(item, ensure_ascii=False)
                    )
                    continue

                # Some MCP text blocks contain JSON strings.
                try:
                    parsed = json.loads(text_content)
                except (json.JSONDecodeError, TypeError):
                    formatted_items.append(str(text_content))
                    continue

                if isinstance(parsed, dict):
                    results = parsed.get("results")

                    if isinstance(results, list):
                        for result in results[:8]:
                            if not isinstance(result, dict):
                                continue

                            title = result.get("title") or "Search result"
                            url = result.get("url") or ""
                            details = (
                                result.get("content")
                                or result.get("snippet")
                                or ""
                            )

                            formatted_items.append(
                                f"### {title}\n"
                                f"URL: {url}\n"
                                f"{str(details)[:700]}"
                            )

                    else:
                        formatted_items.append(
                            json.dumps(
                                parsed,
                                ensure_ascii=False,
                            )[:5000]
                        )

                elif isinstance(parsed, list):
                    for result in parsed[:8]:
                        if isinstance(result, dict):
                            title = result.get("title", "Search result")
                            url = result.get("url", "")
                            details = result.get("content", "")

                            formatted_items.append(
                                f"### {title}\n"
                                f"URL: {url}\n"
                                f"{str(details)[:700]}"
                            )
                        else:
                            formatted_items.append(str(result)[:1000])

                else:
                    formatted_items.append(str(parsed)[:5000])

            else:
                formatted_items.append(str(item)[:5000])

        return "\n\n".join(
            item for item in formatted_items if item.strip()
        )[:12000]

    if isinstance(raw_results, dict):
        results = raw_results.get("results")

        if isinstance(results, list):
            formatted_items = []

            for result in results[:8]:
                if not isinstance(result, dict):
                    continue

                formatted_items.append(
                    f"### {result.get('title', 'Search result')}\n"
                    f"URL: {result.get('url', '')}\n"
                    f"{str(result.get('content', ''))[:700]}"
                )

            return "\n\n".join(formatted_items)[:12000]

        return json.dumps(
            raw_results,
            ensure_ascii=False,
            indent=2,
        )[:12000]

    return str(raw_results)[:12000]


# ============================================================
# FLIGHT AGENT
# ============================================================

FLIGHT_AGENT_PROMPT = """
You are an expert travel flight planner.

User request:
{query}

Airport reference data:
{airport_data}

Airline reference data:
{airline_data}

Provide:
1. Likely departure airport, if the departure city is known.
2. Likely arrival airport.
3. Potential airlines serving the route.
4. Typical flight duration.
5. Estimated airfare range.
6. Peak-season pricing warning.
7. Practical booking advice.

Rules:
- Do not invent specific flight numbers.
- Do not claim that a flight is currently available unless the
  supplied tool data confirms it.
- Do not present estimated fares as live prices.
- If the departure city is unknown, explicitly say so.
- Airport and airline reference data does not confirm a live schedule.
- Keep the response concise and clearly label estimates.
"""


def flight_agent(state: TravelState):
    print("INSIDE FLIGHT AGENT")

    query = state.get("user_query", "")
    errors = []
    llm_call_count = 0

    try:
        airports = run_mcp_with_timeout(
            aviation_mcp_call("list_airports")
        )
    except Exception as exc:
        airports = "Airport data unavailable."
        errors.append(f"Airport lookup: {type(exc).__name__}: {exc}")

    try:
        airlines = run_mcp_with_timeout(
            aviation_mcp_call("list_airlines")
        )
    except Exception as exc:
        airlines = "Airline data unavailable."
        errors.append(f"Airline lookup: {type(exc).__name__}: {exc}")

    prompt = FLIGHT_AGENT_PROMPT.format(
        query=query[:5000],
        airport_data=str(airports)[:3000],
        airline_data=str(airlines)[:3000],
    )

    try:
        llm_call_count = 1

        response = llm.invoke(
            [
                SystemMessage(
                    content="You are an expert travel flight planner."
                ),
                HumanMessage(content=prompt),
            ]
        )

        flight_data = str(response.content).strip()

        if not flight_data:
            raise ValueError("The flight summary model returned empty output.")

    except Exception as exc:
        errors.append(
            f"Flight summary generation: {type(exc).__name__}: {exc}"
        )

        flight_data = (
            "# Flight Research\n\n"
            "Flight recommendations could not be generated. "
            "The available airport and airline reference data is shown below.\n\n"
            f"**Airport data:**\n{str(airports)[:3000]}\n\n"
            f"**Airline data:**\n{str(airlines)[:3000]}\n\n"
            "These reference results do not confirm live flights, "
            "schedules, seat availability, or fares."
        )

    if not errors:
        status = "success"
    elif (
        result_is_available(airports)
        or result_is_available(airlines)
    ):
        status = "partial"
    else:
        status = "failed"

    if errors:
        print("FLIGHT AGENT WARNINGS:", " | ".join(errors))

        flight_data += (
            "\n\n**Verification note:** Some flight research steps "
            "failed or timed out. Verify schedules and fares with "
            "an airline or booking provider."
        )

    return {
        "flight_results": flight_data,
        "flight_status": status,
        "messages": [
            AIMessage(content=f"Flight agent status: {status}")
        ],
        "llm_calls": llm_call_count,
    }


# ============================================================
# HOTEL AGENT
# ============================================================

def hotel_agent(state: TravelState):
    user_query = state.get("user_query", "")

    try:
        destination = extract_destination(user_query)

        # Send a concise query instead of the entire planning brief.
        query = (
            f"Best hotels in {destination}. "
            "Find hotel names, neighborhoods, approximate nightly prices, "
            "and official hotel or reliable booking website links."
        )

        print(f"HOTEL SEARCH QUERY: {query}")

        raw_results = run_mcp_with_timeout(
            tavily_mcp_search(query)
        )

        hotel_results = format_hotel_results(raw_results)

        if result_is_available(hotel_results):
            status = "success"
        else:
            hotel_results = (
                "No usable hotel results were returned. "
                "Verify accommodation options manually."
            )
            status = "partial"

    except Exception as exc:
        error_message = f"{type(exc).__name__}: {exc}"
        print(f"HOTEL AGENT ERROR: {error_message}")

        hotel_results = (
            "Hotel research is currently unavailable because "
            "the search failed or timed out. Verify hotel options "
            "and prices directly."
        )
        status = "failed"

    return {
        "hotel_results": hotel_results,
        "hotel_status": status,
        "messages": [
            AIMessage(content=f"Hotel agent status: {status}")
        ],
    }


# ============================================================
# WEATHER AGENT
# ============================================================

def weather_agent(state: TravelState):
    errors = []
    city = "the requested destination"

    try:
        city = extract_destination(state.get("user_query", ""))
    except Exception as exc:
        errors.append(
            f"Destination extraction: {type(exc).__name__}: {exc}"
        )

    try:
        weather_data = run_mcp_with_timeout(
            weather_mcp_search(city)
        )
    except Exception as exc:
        weather_data = "Current weather data unavailable."
        errors.append(
            f"Current weather: {type(exc).__name__}: {exc}"
        )

    try:
        forecast_data = run_mcp_with_timeout(
            forecast_mcp_search(city)
        )
    except Exception as exc:
        forecast_data = "Forecast data unavailable."
        errors.append(
            f"Forecast: {type(exc).__name__}: {exc}"
        )

    weather_results = f"""
### Current Weather

{weather_data}

### Available Forecast

{forecast_data}

### Forecast Limitation

The forecast above may cover only the next few days. Do not assume
it covers the user's trip dates unless the dates are explicitly
included in the forecast results. Recheck the forecast close to departure.
""".strip()

    if not errors:
        status = "success"
    elif (
        result_is_available(weather_data)
        or result_is_available(forecast_data)
    ):
        status = "partial"
    else:
        status = "failed"

    if errors:
        print("WEATHER AGENT WARNINGS:", " | ".join(errors))

        weather_results += (
            "\n\n**Note:** Some weather data could not be retrieved. "
            "Check the latest forecast before travelling."
        )

    return {
        "weather_results": weather_results,
        "weather_status": status,
        "messages": [
            AIMessage(content=f"Weather agent status: {status}")
        ],
    }


# ============================================================
# ITINERARY AGENT
# ============================================================

def itinerary_agent(state: TravelState):
    prompt = f"""
Create a complete, practical travel itinerary using the research below.
Some research may be missing or incomplete.

## USER REQUEST

{state.get("user_query", "")}

## FLIGHT INFORMATION
Status: {state.get("flight_status", "unknown")}

{str(state.get("flight_results") or "No flight research available.")[:6000]}

## HOTEL INFORMATION
Status: {state.get("hotel_status", "unknown")}

{str(state.get("hotel_results") or "No hotel research available.")[:8000]}

## WEATHER INFORMATION
Status: {state.get("weather_status", "unknown")}

{str(state.get("weather_results") or "No weather research available.")[:4000]}

## REQUIRED OUTPUT FORMAT

Return a polished Markdown travel plan using these sections:

# Trip Overview
Summarize the destination, trip duration, and travel style.

## At a Glance
Use a compact Markdown table for destination, dates, departure city,
traveler count, and budget. Mark missing information as not specified.

## Day-by-Day Itinerary
Create one subsection per trip day, staying within the requested dates.
Include approximate times, activities, food suggestions, local transport,
and breaks. Avoid unrealistic travel between distant locations.

## Where to Stay
Use the supplied hotel research. Include hotel names and source URLs
when available. Do not claim confirmed availability or prices.

## Estimated Budget
Break down flights, accommodation, food, local transport, activities,
and contingency. Label all unsupported amounts as estimates or
"Needs verification". State whether amounts are per person or for
the whole group when known.

## Weather-Aware Advice
Use the supplied weather data carefully. Do not imply that a short-range
forecast covers the actual trip dates if it does not. If the trip dates
are outside the forecast range, explain that and give general seasonal
preparation advice.

## Practical Travel Tips
Provide a concise, useful checklist.

## What Needs Verification
List unverified prices, schedules, availability, and assumptions.

## Rules

- Return Markdown directly, not JSON.
- Do not wrap the answer in a Markdown code fence.
- Do not invent flight numbers, live availability, confirmed prices,
  or bookings.
- Distinguish researched facts from estimates and suggestions.
- If a research agent failed or returned incomplete data, say so.
- Keep the plan practical and within the user's selected dates.
- Do not add travel days outside the selected dates.
- If the user's written duration conflicts with the selected date range,
  explain the discrepancy rather than silently changing the dates.
- Use clear headings and concise language.
"""

    try:
        from travel_agent.utils.itinerary_formatter import (
            generate_itinerary_markdown,
        )

        itinerary = generate_itinerary_markdown(
            llm=llm,
            prompt=prompt,
            research_sources={
                "hotel_search": state.get("hotel_results", ""),
            },
        )

        status = "success"
        llm_call_count = 1

    except Exception as exc:
        error_message = f"{type(exc).__name__}: {exc}"
        print(f"ITINERARY AGENT ERROR: {error_message}")

        # Show the actual error in the result, not only in the terminal.
        itinerary = (
            "# Travel Plan — Generation Failed\n\n"
            "The itinerary could not be generated.\n\n"
            f"**Error:** `{error_message}`\n\n"
            "## Flight Research\n\n"
            f"{state.get('flight_results') or 'Unavailable'}\n\n"
            "## Hotel Research\n\n"
            f"{state.get('hotel_results') or 'Unavailable'}\n\n"
            "## Weather Research\n\n"
            f"{state.get('weather_results') or 'Unavailable'}"
        )

        status = "failed"
        llm_call_count = 1

    research_statuses = [
        state.get(key, "unknown")
        for key in (
            "flight_status",
            "hotel_status",
            "weather_status",
        )
    ]

    if status == "success":
        if any(
            research_status in ("partial", "failed", "unknown")
            for research_status in research_statuses
        ):
            status = "partial_research"

    return {
        "itinerary": itinerary,
        "itinerary_status": status,
        "messages": [
            AIMessage(content=f"Itinerary agent status: {status}")
        ],
        "llm_calls": llm_call_count,
    }


# ============================================================
# LANGGRAPH
# ============================================================

graph = StateGraph(TravelState)

graph.add_node("flight_agent", flight_agent)
graph.add_node("hotel_agent", hotel_agent)
graph.add_node("weather_agent", weather_agent)
graph.add_node("itinerary_agent", itinerary_agent)


# ============================================================
# WORKFLOW
# ============================================================

# Independent research agents run concurrently.
graph.add_edge(START, "flight_agent")
graph.add_edge(START, "hotel_agent")
graph.add_edge(START, "weather_agent")

# Wait for all research agents before generating the itinerary.
graph.add_edge(
    ["flight_agent", "hotel_agent", "weather_agent"],
    "itinerary_agent",
)

graph.add_edge("itinerary_agent", END)


# ============================================================
# IN-MEMORY CHECKPOINT
# ============================================================

checkpointer = MemorySaver()

app = graph.compile(
    checkpointer=checkpointer,
)