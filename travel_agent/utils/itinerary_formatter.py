from langchain_core.messages import HumanMessage, SystemMessage
from tenacity import retry, stop_after_attempt, wait_exponential

from travel_agent.utils.source_extractor import extract_urls


# ============================================================
# ITINERARY FORMATTER
# ============================================================

SYSTEM_PROMPT = """
You are a careful, practical travel planner.

Generate a complete travel itinerary in Markdown.

Requirements:
- Return Markdown directly.
- Do not return JSON.
- Do not wrap the response in a code fence.
- Use clear headings, lists, and Markdown tables where appropriate.
- Keep the itinerary within the dates supplied by the user.
- Follow the supplied traveler count, budget, and departure city.
- Do not invent confirmed bookings, live availability, or verified prices.
- Clearly label estimates and unverified information.
- Do not invent missing research or present assumptions as facts.
- Distinguish current weather from a forecast for the actual trip dates.
- If a forecast does not cover the trip dates, say so explicitly.
- If research is missing, continue planning with reasonable suggestions
  and clearly identify what needs verification.
- Make the itinerary realistic, with reasonable travel times and breaks.
"""


@retry(
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=1, min=1, max=3),
    reraise=True,
)
def generate_itinerary_markdown(
    llm,
    prompt: str,
    research_sources: dict | None = None,
) -> str:
    """
    Generate a Markdown itinerary directly from the LLM.

    JSON parsing and Pydantic schema validation are intentionally omitted
    so that itinerary generation does not fail solely because the model
    returns malformed JSON.
    """

    response = llm.invoke(
        [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ]
    )

    content = response.content

    # Handle an empty response explicitly.
    if not isinstance(content, str):
        raise ValueError(
            "The itinerary model did not return a text response."
        )

    content = content.strip()

    if not content:
        raise ValueError(
            "The itinerary model returned an empty response."
        )

    # Remove a surrounding Markdown code fence if the model adds one.
    if content.startswith("```"):
        lines = content.splitlines()

        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        content = "\n".join(lines).strip()

    if not content:
        raise ValueError(
            "The itinerary response was empty after formatting."
        )

    # --------------------------------------------------------
    # Add clickable hotel research sources.
    # --------------------------------------------------------

    research_sources = research_sources or {}

    hotel_search_data = research_sources.get("hotel_search", "")
    hotel_urls = extract_urls(str(hotel_search_data))

    if hotel_urls:
        content += "\n\n## Hotel Research Sources\n\n"

        for index, url in enumerate(hotel_urls[:8], start=1):
            content += f"{index}. [Open hotel research source]({url})\n"

    # --------------------------------------------------------
    # Add a final verification checklist.
    # --------------------------------------------------------

    content += """

## Final Verification Checklist

- Verify hotel prices, location, and availability directly.
- Confirm flight schedules and airfare with an airline or booking provider.
- Check attraction opening hours and ticket requirements.
- Confirm local transport schedules and travel times.
- Recheck the weather forecast close to departure.
- Confirm that the itinerary matches the selected travel dates.
"""

    return content.strip()