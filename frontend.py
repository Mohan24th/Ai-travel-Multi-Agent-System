# ============================================================
# AI TRAVEL BOOKING SYSTEM
# Streamlit Frontend
# ============================================================

import os
from datetime import datetime
import uuid

import streamlit as st
from langchain_core.messages import HumanMessage

from main import app


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="AI Travel Booking System",
    page_icon="✈️",
    layout="wide",
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
<style>

@import url(
    'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap'
);

html, body, .stApp {
    font-family: 'Inter', sans-serif;
    background-color: #080d14;
}


/* ============================================================
   HERO
   ============================================================ */

.hero-wrapper {
    position: relative;
    border-radius: 20px;
    overflow: hidden;
    margin-bottom: 2rem;
    height: 280px;
}

.hero-bg {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
    filter: brightness(0.35);
    position: absolute;
    top: 0;
    left: 0;
}

.hero-content {
    position: relative;
    z-index: 2;
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 2rem;
}

.hero-badge {
    background: rgba(58,123,213,0.25);
    border: 1px solid rgba(58,123,213,0.5);
    color: #7ab8f5 !important;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    padding: 0.3rem 0.9rem;
    border-radius: 20px;
    margin-bottom: 0.9rem;
    display: inline-block;
}

.hero-title {
    font-size: 2.6rem;
    font-weight: 700;
    color: #ffffff;
    margin: 0 0 0.6rem;
    line-height: 1.2;
}

.hero-sub {
    color: #94adc8;
    font-size: 1rem;
    max-width: 560px;
}


/* ============================================================
   INPUT CARD
   ============================================================ */

.input-card {
    background: #0e1623;
    border: 1px solid #1e2e44;
    border-radius: 16px;
    padding: 1.6rem 1.8rem;
    margin-bottom: 1.5rem;
}

.input-label {
    color: #7ab8f5;
    font-size: 0.8rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
}


/* ============================================================
   DESTINATION STRIP
   ============================================================ */

.dest-row {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
    margin: 0.8rem 0 1.2rem;
}

.dest-chip {
    background: #111b2b;
    border: 1px solid #1e3050;
    color: #f7fdf4;
    padding: 0.35rem 0.85rem;
    border-radius: 20px;
    font-size: 0.82rem;
    cursor: pointer;
    transition: all 0.2s;
}

.dest-chip:hover {
    background: #1a2e47;
    border-color: #3a7bd5;
    color: #fff;
}


/* ============================================================
   BUTTONS
   ============================================================ */

div[data-testid="stButton"] > button {

    background: linear-gradient(
        135deg,
        #1a6bbf 0%,
        #0d4a8a 50%,
        #0a3d75 100%
    ) !important;

    color: #ffffff !important;

    border: none !important;

    border-radius: 12px !important;

    padding: 0.85rem 2.5rem !important;

    font-size: 1.05rem !important;

    font-weight: 700 !important;

    letter-spacing: 0.03em !important;

    width: 100% !important;

    box-shadow:
        0 0 24px rgba(26,107,191,0.35),
        0 4px 15px rgba(0,0,0,0.4) !important;

    transition: all 0.3s ease !important;
}

div[data-testid="stButton"] > button:hover {

    box-shadow:
        0 0 40px rgba(26,107,191,0.6),
        0 6px 20px rgba(0,0,0,0.5) !important;

    transform: translateY(-2px) !important;

    background: linear-gradient(
        135deg,
        #2278d4 0%,
        #1057a0 50%,
        #0d4a8a 100%
    ) !important;
}

div[data-testid="stButton"] > button:active {
    transform: translateY(0px) !important;
}


/* ============================================================
   AGENT STATUS
   ============================================================ */

[data-testid="stStatusWidget"] {

    background: #0e1a2e !important;

    border: 1px solid #1e3050 !important;

    border-radius: 12px !important;
}

[data-testid="stStatusWidget"] > div:first-child {

    background: #0e1a2e !important;

    border-radius: 12px 12px 0 0 !important;
}

[data-testid="stStatusWidget"] details,
[data-testid="stStatusWidget"] details > div,
[data-testid="stStatusWidget"] [data-testid="stVerticalBlock"] {

    background: #0a1520 !important;

    color: #ffffff !important;

    padding: 0.25rem 0.5rem !important;
}

[data-testid="stStatusWidget"] * {
    color: #ffffff !important;
}

[data-testid="stStatusWidget"] a {
    color: #4ea8f0 !important;
}

[data-testid="stStatusWidget"] hr {
    border-color: #1e3050 !important;
}


/* ============================================================
   SECTION HEADERS
   ============================================================ */

.sec-head {

    display: flex;

    align-items: center;

    gap: 0.6rem;

    margin: 2rem 0 0.75rem;

    padding-bottom: 0.5rem;

    border-bottom: 1px solid #1e2e44;
}

.sec-head span {

    font-size: 1.15rem;

    font-weight: 600;

    color: #e0edf8;
}


/* ============================================================
   METRICS
   ============================================================ */

.metric-row {

    display: flex;

    gap: 1rem;

    margin: 1.5rem 0;
}

.metric-box {

    flex: 1;

    background: #0e1623;

    border: 1px solid #1e2e44;

    border-radius: 12px;

    padding: 1rem 1.2rem;

    text-align: center;
}

.metric-val {

    font-size: 1.8rem;

    font-weight: 700;

    color: #4ea8f0;
}

.metric-lbl {

    font-size: 0.78rem;

    color: #7aa8cc !important;

    margin-top: 0.2rem;

    text-transform: uppercase;

    letter-spacing: 0.08em;
}


/* ============================================================
   FINAL PLAN
   ============================================================ */

.final-card {

    background: linear-gradient(
        160deg,
        #0c1a2e 0%,
        #0a1520 100%
    );

    border: 1px solid #1e3a5c;

    border-left: 4px solid #3a7bd5;

    border-radius: 14px;

    padding: 1.8rem;

    line-height: 1.8;

    color: #cce0f5;

    font-size: 0.95rem;
}


/* ============================================================
   SAVE BAR
   ============================================================ */

.save-bar {

    background: #0e1623;

    border: 1px solid #1e2e44;

    border-radius: 10px;

    padding: 0.85rem 1.2rem;

    color: #8ab8d8 !important;

    font-size: 0.88rem;

    margin-top: 0.5rem;
}

.save-bar code {

    color: #7ab8f5 !important;

    background: #0a1520 !important;
}


/* ============================================================
   SIDEBAR
   ============================================================ */

section[data-testid="stSidebar"] {

    background: #090e18 !important;

    border-right: 1px solid #141f30 !important;
}

.sidebar-chip {

    background: #0e1a2b;

    border: 1px solid #1a2e44;

    border-radius: 8px;

    padding: 0.45rem 0.75rem;

    margin-bottom: 0.4rem;

    font-size: 0.83rem;

    color: #7aa8cc;
}

.sidebar-title {

    color: #e0edf8;

    font-size: 1rem;

    font-weight: 600;

    margin: 1rem 0 0.5rem;
}


/* ============================================================
   HIDE STREAMLIT BRANDING
   ============================================================ */

#MainMenu,
footer,
header {
    visibility: hidden;
}


/* ============================================================
   TEXTAREA
   ============================================================ */

.stTextArea textarea {

    background: #0a1520 !important;

    border: 1px solid #1e2e44 !important;

    border-radius: 10px !important;

    color: #e8f4ff !important;

    font-size: 0.95rem !important;

    resize: none !important;
}

.stTextArea textarea:focus {

    border-color: #3a7bd5 !important;

    box-shadow:
        0 0 0 2px rgba(58,123,213,0.2) !important;
}

.stTextArea textarea::placeholder {
    color: #4a6a85 !important;
}


/* ============================================================
   TEXT INPUT
   ============================================================ */

input[type="text"],
.stTextInput input {

    background: #0e1a2b !important;

    border: 1px solid #1a2e44 !important;

    border-radius: 8px !important;

    color: #e0edf8 !important;
}

input[type="text"]:focus,
.stTextInput input:focus {

    border-color: #3a7bd5 !important;

    box-shadow:
        0 0 0 2px rgba(58,123,213,0.2) !important;
}

input[type="text"]::placeholder {
    color: #3a5570 !important;
}


/* ============================================================
   LABELS
   ============================================================ */

.stTextInput label,
.stTextArea label,
.stSelectbox label,
.stNumberInput label {

    color: #7ab8f5 !important;

    font-size: 0.82rem !important;

    font-weight: 600 !important;

    letter-spacing: 0.08em !important;
}


/* ============================================================
   MARKDOWN
   ============================================================ */

.stMarkdown p,
.stMarkdown li,
.stMarkdown td,
.stMarkdown th {

    color: #cce0f5 !important;
}

.stMarkdown h1,
.stMarkdown h2,
.stMarkdown h3 {

    color: #e8f4ff !important;
}

.stMarkdown code {

    background: #0e1a2b !important;

    color: #7ab8f5 !important;

    padding: 0.15em 0.4em;

    border-radius: 4px;
}


/* ============================================================
   ALERTS
   ============================================================ */

.stAlert {

    background: #0e1a2b !important;

    border-radius: 10px !important;
}

.stAlert p,
.stAlert div {
    color: #e0edf8 !important;
}


/* ============================================================
   SIDEBAR TEXT
   ============================================================ */

section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stMarkdown {

    color: #a0c4e0 !important;
}

section[data-testid="stSidebar"] hr {
    border-color: #1a2e44 !important;
}


/* ============================================================
   DOWNLOAD BUTTON
   ============================================================ */

div[data-testid="stDownloadButton"] > button {

    background: #1a3a5c !important;

    color: #e8f4ff !important;

    border: 1px solid #2a5080 !important;

    border-radius: 10px !important;
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        "<div class='sidebar-title'>🌍 AI Travel Planner</div>",
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # Generate a session ID once
    if "thread_id" not in st.session_state:

        st.session_state.thread_id = str(
            uuid.uuid4()
        )

    thread_id = st.text_input(
        "👤 User ID",
        value=st.session_state.thread_id,
        help="Your session ID — keeps travel state during the current app session",
    )

    st.session_state.thread_id = thread_id

    st.markdown(
        "<div class='sidebar-title'>Powered by</div>",
        unsafe_allow_html=True,
    )

    technologies = [
        "🔗 LangGraph",
        "🧠 Groq · GPT OSS 120B",
        "💾 In-Memory Memory",
        "🔍 Tavily Search",
        "✈️ AviationStack",
        "🌦️ Weather API",
    ]

    for tech in technologies:

        st.markdown(
            f"<div class='sidebar-chip'>{tech}</div>",
            unsafe_allow_html=True,
        )

    st.markdown(
        "<div class='sidebar-title'>Agent Pipeline</div>",
        unsafe_allow_html=True,
    )

    agents = [
        "① Flight Agent",
        "② Hotel Agent",
        "③ Weather Agent",
        "④ Itinerary Agent",
    ]

    for agent in agents:

        st.markdown(
            f"<div class='sidebar-chip'>{agent}</div>",
            unsafe_allow_html=True,
        )


# ============================================================
# HERO
# ============================================================

st.html(
    """
    <div class="hero-wrapper">
        <img
            class="hero-bg"
            src="https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=1400&q=80"
            alt="airplane above clouds"
        />

        <div class="hero-content">
            <div class="hero-badge">
                ✦ Multi-Agent AI System
            </div>

            <div class="hero-title">
                ✈️ AI Travel Booking System
            </div>

            <div class="hero-sub">
                Four specialized agents work together —
                searching flights, hotels, checking weather,
                and building your complete travel itinerary.
            </div>
        </div>
    </div>
    """
)


# ============================================================
# DESTINATION IMAGE STRIP
# ============================================================

DESTINATIONS = [
    (
        "🇯🇵 Tokyo",
        "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=600&q=80",
    ),
    (
        "🇫🇷 Paris",
        "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=600&q=80",
    ),
    (
        "🇹🇭 Bangkok",
        "https://images.unsplash.com/photo-1508009603885-50cf7c579365?w=600&q=80",
    ),
    (
        "🇮🇹 Rome",
        "https://images.unsplash.com/photo-1552832230-c0197dd311b5?w=600&q=80",
    ),
    (
        "🇦🇪 Dubai",
        "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=600&q=80",
    ),
]

cols = st.columns(5)

for col, (name, img_url) in zip(cols, DESTINATIONS):
    with col:
        st.html(
            f"""
            <div style="
                position:relative;
                height:110px;
                width:100%;
                overflow:hidden;
                border-radius:12px;
                border:1px solid #1e3050;
                background:#0e1623;
            ">
                <img
                    src="{img_url}"
                    alt="{name}"
                    style="
                        width:100%;
                        height:100%;
                        display:block;
                        object-fit:cover;
                        filter:brightness(0.55);
                    "
                />

                <div style="
                    position:absolute;
                    left:0;
                    right:0;
                    bottom:0;
                    padding:18px 6px 8px;
                    text-align:center;
                    color:white;
                    font-size:0.82rem;
                    font-weight:600;
                    background:linear-gradient(
                        transparent,
                        rgba(0,0,0,0.75)
                    );
                ">
                    {name}
                </div>
            </div>
            """
        )

st.markdown("<br>", unsafe_allow_html=True)


# ============================================================
# TRIP INPUT
# ============================================================

st.markdown(
    """
    <div class="input-label">
        🗺️ Describe your trip
    </div>
    """,
    unsafe_allow_html=True,
)


QUICK = [
    "7-day Japan under ₹2L",
    "Paris trip for 5 days",
    "Dubai weekend trip",
    "Bali backpacking 10 days",
]


qcols = st.columns(
    len(QUICK)
)


# Use session state so quick buttons actually
# populate the text area.

if "quick_query" not in st.session_state:

    st.session_state.quick_query = ""


for qc, label in zip(
    qcols,
    QUICK,
):

    with qc:

        if st.button(
            label,
            key=f"q_{label}",
            use_container_width=True,
        ):

            st.session_state.quick_query = label


user_query = st.text_area(
    "",
    value=st.session_state.quick_query,
    placeholder=(
        "e.g. Plan a complete 7-day Japan trip "
        "including flights, hotels and sightseeing "
        "under ₹2 lakhs"
    ),
    height=100,
    label_visibility="collapsed",
)


# ============================================================
# GENERATE BUTTON
# ============================================================

generate = st.button(
    "🚀  Generate My Travel Plan",
    use_container_width=True,
)


# ============================================================
# AGENT METADATA
# ============================================================

AGENT_META = {

    "flight_agent": (
        "✈️",
        "Flight Agent",
    ),

    "hotel_agent": (
        "🏨",
        "Hotel Agent",
    ),

    "weather_agent": (
        "🌦️",
        "Weather Agent",
    ),

    "itinerary_agent": (
        "🗓️",
        "Itinerary Agent",
    ),

}


# ============================================================
# RUN TRAVEL AGENTS
# ============================================================

if generate:

    if not user_query.strip():

        st.warning(
            "Please describe your trip first."
        )

    else:

        # --------------------------------------------
        # LangGraph thread
        # --------------------------------------------

        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }


        # --------------------------------------------
        # Initial state
        # --------------------------------------------

        initial_state = {

            "messages": [
                HumanMessage(
                    content=user_query
                )
            ],

            "user_query": user_query,

            "flight_results": "",

            "hotel_results": "",

            "weather_results": "",

            "itinerary": "",

            "llm_calls": 0,

        }


        # --------------------------------------------
        # Collected results
        # --------------------------------------------

        collected = {

            "flight_results": "",

            "hotel_results": "",

            "weather_results": "",

            "itinerary": "",

            "llm_calls": 0,

        }


        st.markdown("---")


        st.markdown(
            """
            <div class="sec-head">
                <span>🤖 Agent Pipeline — Live</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


        # --------------------------------------------
        # Run LangGraph
        # --------------------------------------------

        try:

            with st.spinner(
                "AI agents are planning your trip..."
            ):

                for chunk in app.stream(

                    initial_state,

                    config=config,

                    stream_mode="updates",

                ):

                    for node_name, state_update in chunk.items():

                        icon, label = AGENT_META.get(
                            node_name,
                            ("🔧", node_name),
                        )


                        with st.status(
                            f"{icon}  {label}",
                            state="complete",
                            expanded=True,
                        ):

                            # ==================================
                            # FLIGHT
                            # ==================================

                            if node_name == "flight_agent":

                                text = state_update.get(
                                    "flight_results",
                                    "",
                                )

                                collected[
                                    "flight_results"
                                ] = text

                                st.markdown(
                                    text
                                    or "_No flight data returned._"
                                )


                            # ==================================
                            # HOTEL
                            # ==================================

                            elif node_name == "hotel_agent":

                                text = state_update.get(
                                    "hotel_results",
                                    "",
                                )

                                collected[
                                    "hotel_results"
                                ] = text

                                st.markdown(
                                    text
                                    or "_No hotel data returned._"
                                )


                            # ==================================
                            # WEATHER
                            # ==================================

                            elif node_name == "weather_agent":

                                text = state_update.get(
                                    "weather_results",
                                    "",
                                )

                                collected[
                                    "weather_results"
                                ] = text

                                st.markdown(
                                    text
                                    or "_No weather data returned._"
                                )


                            # ==================================
                            # ITINERARY
                            # ==================================

                            elif node_name == "itinerary_agent":

                                text = state_update.get(
                                    "itinerary",
                                    "",
                                )

                                collected[
                                    "itinerary"
                                ] = text

                                st.markdown(
                                    text
                                    or "_No itinerary generated._"
                                )


                            # ==================================
                            # LLM CALL COUNT
                            # ==================================

                            collected[
                                "llm_calls"
                            ] = state_update.get(
                                "llm_calls",
                                collected[
                                    "llm_calls"
                                ],
                            )


            # ==================================================
            # METRICS
            # ==================================================

            st.markdown(
                f"""
                <div class="metric-row">

                    <div class="metric-box">

                        <div class="metric-val">
                            4
                        </div>

                        <div class="metric-lbl">
                            Agents Run
                        </div>

                    </div>


                    <div class="metric-box">

                        <div class="metric-val">
                            {collected["llm_calls"]}
                        </div>

                        <div class="metric-lbl">
                            LLM Calls
                        </div>

                    </div>


                    <div class="metric-box">

                        <div class="metric-val">
                            ✅
                        </div>

                        <div class="metric-lbl">
                            Status
                        </div>

                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )


            # ==================================================
            # FINAL TRAVEL PLAN
            # ==================================================

            if collected["itinerary"]:

                st.markdown(
                    """
                    <div class="sec-head">
                        <span>
                            🧠 Final Travel Plan
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


                st.markdown(
                    '<div class="final-card">',
                    unsafe_allow_html=True,
                )


                st.markdown(
                    collected["itinerary"]
                )


                st.markdown(
                    "</div>",
                    unsafe_allow_html=True,
                )


            # ==================================================
            # DOWNLOAD
            # ==================================================

            timestamp = datetime.now().strftime(
                "%Y%m%d_%H%M%S"
            )


            filename = (
                f"travel_plan_{timestamp}.md"
            )


            file_content = f"""
# AI Travel Plan

**Query:** {user_query}

**Generated:** {
    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
}

**User ID:** {thread_id}

---

## ✈️ Flight Information

{collected["flight_results"] or "N/A"}

---

## 🏨 Hotel Information

{collected["hotel_results"] or "N/A"}

---

## 🌦️ Weather Information

{collected["weather_results"] or "N/A"}

---

## 🗓️ Itinerary

{collected["itinerary"] or "N/A"}

---

**LLM Calls:** {collected["llm_calls"]}
"""


            # ==================================================
            # DOWNLOAD + INFO
            # ==================================================

            dl_col, info_col = st.columns(
                [1, 3]
            )


            with dl_col:

                st.download_button(
                    "⬇️ Download Plan",
                    data=file_content,
                    file_name=filename,
                    mime="text/markdown",
                    use_container_width=True,
                )


            with info_col:

                st.markdown(
                    f"""
                    <div class="save-bar">
                        📁 Travel plan generated
                        → <code>{filename}</code>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


        except Exception as e:

            st.error(
                f"Travel planning failed: {str(e)}"
            )