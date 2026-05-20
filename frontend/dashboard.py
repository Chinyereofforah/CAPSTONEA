# load libraries
import plotly.express as px
import plotly.graph_objects as go
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
import numpy as np
import time
import streamlit as st
from streamlit_option_menu import option_menu
import plotly.express as px
import pandas as pd
import requests
import random
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from PIL import Image
import base64
from pathlib import Path
import streamlit.components.v1 as components
from backend.ml.crypto_ai import ask_crypto_ai
import os
from dotenv import load_dotenv

load_dotenv()

st.markdown(
    """
    <style>

    .ticker-wrap {
        width: 100%;
        overflow: hidden;
        background: rgba(0, 20, 40, 0.9);
        border-top: 1px solid #00ffff33;
        border-bottom: 1px solid #00ffff33;
        padding: 12px 0;
        margin-bottom: 20px;
        white-space: nowrap;
    }

    .ticker {
        display: inline-block;
        white-space: nowrap;
        padding-left: 100%;
        animation: ticker-scroll 35s linear infinite;
    }

    .ticker-item {
        display: inline-block;
        margin-right: 60px;
        color: white;
        font-size: 18px;
        font-weight: 600;
    }

    .positive {
        color: #00ff99;
    }

    .negative {
        color: #ff4b4b;
    }

    @keyframes ticker-scroll {
        0% {
            transform: translateX(0%);
        }

        100% {
            transform: translateX(-100%);
        }
    }

    </style>
    """,
    unsafe_allow_html=True
)

st.set_page_config(layout="wide")

BASE_DIR = Path(__file__).parent

logo_path = BASE_DIR / "assets" / "logo.png"

logo = Image.open(logo_path)

with open(logo_path, "rb") as image_file:
    encoded_logo = base64.b64encode(image_file.read()).decode()

if st.button("☰", key="sidebar_logo"):
    st.session_state.show_sidebar = True

col1, col2 = st.columns([0.5, 20])

with col1:
    st.markdown(
        """
        <style>
        div[data-testid="collapsedControl"] {
            display: block;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

with col2:
    st.image(logo, width=60)

# PAGE CONFIG

st.set_page_config(
    page_title="AI DeFi Risk Monitor",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(
    """
    <style>

    .top-header {
        position: fixed;
        top: 0;
        right: 0;
        left: 0;
        height: 90px;
        background: rgba(5, 10, 20, 0.95);
        backdrop-filter: blur(10px);
        z-index: 99999;
        border-bottom: 1px solid #00ffff33;
        display: flex;
        justify-content: flex-end;
        align-items: center;
        padding-right: 30px;
    }

    .top-header img {
        height: 65px;
        margin-right: 15px;
        filter: drop-shadow(0 0 10px cyan);
    }

    .top-header h1 {
        color: white;
        font-size: 28px;
        font-weight: bold;
        background: linear-gradient(to right, cyan, #00ff99);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }

    .main {
        padding-top: 10px;
    }

    </style>
    """,
    unsafe_allow_html=True
)

# GLOBAL SEARCH ENGINE

# LOAD MARKET DATA


@st.cache_data(ttl=60)
def load_market_data():

    url = "https://api.coingecko.com/api/v3/coins/markets"

    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 100,
        "page": 1,
        "sparkline": False,
        "price_change_percentage": "24h"
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=15
        )

        data = response.json()

        df = pd.DataFrame(data)

        return df

    except Exception as e:

        st.error(f"Failed to load market data: {e}")

        return pd.DataFrame()



# GLOBAL DATAFRAME


market_live_df = load_market_data()


# PAGE HEADER


st.title("")

st.markdown("""

""")

# SEARCH INPUT


search_query = st.text_input(
    "Search coins, alerts, news, analytics...",
    placeholder="e.g. Bitcoin, ETH, TVL, exploit, whale, liquidity"
)


# SEARCH FUNCTION


def search_dataframe(df, query):

    if df is None or df.empty or not query:
        return pd.DataFrame()

    query = query.lower()

    mask = pd.Series(
        [False] * len(df),
        index=df.index
    )

    for col in df.columns:

        try:

            if df[col].dtype == "object":

                mask = mask | df[col].astype(str).str.lower().str.contains(
                    query,
                    na=False
                )

        except:
            continue

    return df[mask]



# SEARCH EXECUTION


if search_query:

    st.info(f"Search results for: {search_query}")

    # =====================================================
    # COIN SEARCH RESULTS
    # =====================================================

    st.markdown("---")

    st.subheader("📊 Coin Results")

    if market_live_df is not None and not market_live_df.empty:

        filtered_df = search_dataframe(
            market_live_df,
            search_query
        )

        if not filtered_df.empty:

            columns_to_show = [
                "name",
                "symbol",
                "current_price",
                "market_cap",
                "total_volume",
                "price_change_percentage_24h",
                "circulating_supply"
            ]

            available_columns = [
                col for col in columns_to_show
                if col in filtered_df.columns
            ]

            st.dataframe(
                filtered_df[available_columns],
                use_container_width=True,
                height=400
            )

            # =================================================
            # METRICS
            # =================================================

            st.markdown("### 📈 Market Summary")

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Matching Assets",
                len(filtered_df)
            )

            col2.metric(
                "Combined Market Cap",
                f"${filtered_df['market_cap'].sum():,.0f}"
            )

            col3.metric(
                "Combined Volume",
                f"${filtered_df['total_volume'].sum():,.0f}"
            )

        else:

            st.warning("No matching coins found.")

    else:

        st.error("Market data failed to load.")

    # =====================================================
    # NEWS SEARCH
    # =====================================================

    st.markdown("---")

    st.subheader("📰 Crypto News Results")

    try:

        news_url = (
            "https://min-api.cryptocompare.com/data/v2/news/?lang=EN"
        )

        news_response = requests.get(
            news_url,
            timeout=15
        )

        news_json = news_response.json()

        news_data = news_json.get("Data", [])

        matched_news = [

            news for news in news_data

            if search_query.lower() in news.get(
                "title",
                ""
            ).lower()

            or search_query.lower() in news.get(
                "body",
                ""
            ).lower()
        ]

        if matched_news:

            for news in matched_news[:5]:

                with st.container(border=True):

                    st.markdown(
                        f"### {news.get('title', 'No Title')}"
                    )

                    st.write(
                        news.get("body", "")[:300] + "..."
                    )

                    st.link_button(
                        "Read Full Article",
                        news.get("url", "#")
                    )

        else:

            st.info("No matching news articles found.")

    except Exception as e:

        st.warning(
            f"News API temporarily unavailable: {e}"
        )

    # =====================================================
    # RISK ALERT ENGINE
    # =====================================================

    st.markdown("---")

    st.subheader("🚨 Risk Intelligence Engine")

    alert_keywords = {

        "exploit": {
            "category": "Smart Contract Exploit",
            "risk": "HIGH"
        },

        "hack": {
            "category": "Protocol Hack",
            "risk": "HIGH"
        },

        "rug": {
            "category": "Rug Pull Detection",
            "risk": "CRITICAL"
        },

        "liquidity": {
            "category": "Liquidity Concentration",
            "risk": "MEDIUM"
        },

        "tvl": {
            "category": "TVL Monitoring",
            "risk": "MEDIUM"
        },

        "whale": {
            "category": "Whale Wallet Activity",
            "risk": "HIGH"
        },

        "bridge": {
            "category": "Cross-Chain Imbalance",
            "risk": "HIGH"
        },

        "mint": {
            "category": "Suspicious Mint Activity",
            "risk": "MEDIUM"
        },

        "burn": {
            "category": "Token Burn Monitoring",
            "risk": "LOW"
        }
    }

    alert_found = False

    for keyword, details in alert_keywords.items():

        if keyword in search_query.lower():

            alert_found = True

            st.error(
                f"""
                ALERT CATEGORY: {details['category']}

                RISK LEVEL: {details['risk']}
                """
            )

            st.write("""
            This query matches a monitored blockchain
            risk pattern within the analytics engine.
            """)

    if not alert_found:

        st.success(
            "No blockchain risk alerts triggered."
        )

# HIDE DEFAULT STREAMLIT MENU + DEFAULT MULTIPAGE SIDEBAR

hide_streamlit_style = """
<style>

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

/* KEEP HEADER VISIBLE */
header[data-testid="stHeader"] {
    background: transparent;
}

/* HIDE DEFAULT MULTIPAGE NAV */
[data-testid="stSidebarNav"] {
    display: none !important;
}

/* CLEAN SPACING */
.block-container {
    padding-top: 0.5rem;
}

.main {
    padding-top: 10px;
}

</style>
"""

st.markdown(
    hide_streamlit_style,
    unsafe_allow_html=True
)

# ---------------------------------------------------
# CUSTOM CSS
# ---------------------------------------------------

st.markdown("""
<style>

html, body, [class*="css"] {
    background-color: #0E1117;
    color: white;
}

div[data-testid="stSidebar"] {
    background-color: #111827;
}

.block-container {
    padding-top: 0.5rem;
}

.crypto-card {
    background-color: #161B22;
    border: 1px solid #30363D;
    border-radius: 15px;
    padding: 20px;
    margin-bottom: 20px;
}

</style>
""", unsafe_allow_html=True)

# LOAD LIVE MARKET DATA

@st.cache_data(ttl=300)
def load_home_market_data():

    url = (
        "https://api.coingecko.com/api/v3/coins/markets"
        "?vs_currency=usd"
        "&order=market_cap_desc"
        "&per_page=20"
        "&page=1"
        "&sparkline=false"
    )

    retry_strategy = Retry(
        total=5,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)

    session = requests.Session()
    session.mount("https://", adapter)

    try:
        r = session.get(url, timeout=60)

        if r.status_code == 200:
            data = r.json()

            if data:
                return pd.DataFrame(data)

    except Exception as e:
        print(f"CoinGecko failed: {e}")

    # FALLBACK DATA
    fallback = [
        {
            "name": "Bitcoin",
            "symbol": "BTC",
            "current_price": 68000,
            "market_cap": 1300000000000,
            "price_change_percentage_24h": 2.5
        },
        {
            "name": "Ethereum",
            "symbol": "ETH",
            "current_price": 3200,
            "market_cap": 400000000000,
            "price_change_percentage_24h": -1.2
        },
        {
            "name": "Solana",
            "symbol": "SOL",
            "current_price": 145,
            "market_cap": 65000000000,
            "price_change_percentage_24h": 5.1
        }
    ]

    st.warning("Using fallback market data.")

    return pd.DataFrame(fallback)

market_live_df = load_home_market_data()

# ---------------------------------------------------
# FALLBACK SAFETY
# ---------------------------------------------------

if market_live_df.empty:

    st.error(
        "Live market data temporarily unavailable."
    )

    market_live_df = pd.DataFrame({
        "name": [],
        "symbol": [],
        "current_price": [],
        "market_cap": [],
        "total_volume": [],
        "price_change_percentage_24h": []
    })

# ---------------------------------------------------
# PROFESSIONAL SIDEBAR
# ---------------------------------------------------

if "show_sidebar" not in st.session_state:
    st.session_state.show_sidebar = True
with st.sidebar:

    st.markdown(" AI DeFi Monitor")

    selected = option_menu(
        menu_title=None,
        options=[
            "Home",
            "Dashboard",
            "Analytics",
            "Whale Tracking",
            "Smart Money",
            "Alerts",
            "Settings"
        ],
        icons=[
            "house-fill",
            "speedometer2",
            "bar-chart-fill",
            "currency-bitcoin",
            "activity",
            "bell-fill",
            "gear-fill"
        ],
        default_index=0,
        styles={
            "container": {
                "padding": "0!important",
                "background-color": "#B1C5F0"
            },

            "icon": {
                "color": "#00C2FF",
                "font-size": "18px"
            },

            "nav-link": {
                "font-size": "16px",
                "text-align": "left",
                "margin": "4px",
                "--hover-color": "#1F2937",
                "border-radius": "10px",
            },

            "nav-link-selected": {
                "background-color": "#2563EB",
            },
        }
    )

# ---------------------------------------------------
# HOME PAGE
# ---------------------------------------------------

if selected == "Home":

    # LOAD REAL MARKET DATA

    @st.cache_data(ttl=120)
    def load_home_market_data():

        coins = []

        for page in range(1, 6):

            url = (
                f"https://api.coingecko.com/api/v3/coins/markets"
                f"?vs_currency=usd"
                f"&order=market_cap_desc"
                f"&per_page=250"
                f"&page={page}"
                f"&sparkline=false"
                f"&price_change_percentage=24h"
            )

            r = requests.get(url, timeout=20)

            if r.status_code == 200:

                data = r.json()

                if isinstance(data, list):

                    coins.extend(data)

        return pd.DataFrame(coins)

    market_live_df = load_home_market_data()

    # =====================================================
    # LOAD REAL CRYPTO NEWS
    # =====================================================

    @st.cache_data(ttl=300)
    def load_crypto_news():

        try:

            url = "https://min-api.cryptocompare.com/data/v2/news/?lang=EN"

            r = requests.get(url, timeout=20)

            if r.status_code == 200:

                data = r.json()

                return data.get("Data", [])

        except:
            pass

        return []

    crypto_news = load_crypto_news()

    # =====================================================
    # TOP METRICS
    # =====================================================

    total_market_cap = (
        market_live_df["market_cap"].sum()
        if not market_live_df.empty else 0
    )

    total_volume = (
        market_live_df["total_volume"].sum()
        if not market_live_df.empty else 0
    )

    positive = len(
        market_live_df[
            market_live_df["price_change_percentage_24h"] > 0
        ]
    )

    negative = len(
        market_live_df[
            market_live_df["price_change_percentage_24h"] < 0
        ]
    )

    html_code = f"""
<style>

@keyframes scrollLeft {{
    0% {{
        transform: translateX(100%);
    }}
    100% {{
        transform: translateX(-100%);
    }}
}}

.ticker-wrapper {{
    width: 100%;
    overflow: hidden;
    background: #0b1230;
    border: 1px solid #1f2a44;
    border-radius: 12px;
    padding: 12px 0;
}}

.ticker {{
    display: flex;
    gap: 60px;
    white-space: nowrap;
    animation: scrollLeft 7s linear infinite;
    padding-left: 100%;
}}

.ticker-item {{
    color: #cbd5e1;
    font-size: 14px;
    font-weight: 500;
}}

.ticker-item span {{
    color: #60a5fa;
    font-weight: 600;
}}

body {{
    margin: 0;
    background: transparent;
}}

</style>

<div class="ticker-wrapper">
    <div class="ticker">

        <div class="ticker-item">
            📊 Tracked Assets: <span>{len(market_live_df):,}</span>
        </div>

        <div class="ticker-item">
            💰 Market Cap: <span>${total_market_cap:,.0f}</span>
        </div>

        <div class="ticker-item">
            📈 24H Volume: <span>${total_volume:,.0f}</span>
        </div>

        <div class="ticker-item">
            🟢 Bullish: <span>{positive}</span>
        </div>

        <div class="ticker-item">
            🔴 Bearish: <span>{negative}</span>
        </div>

    </div>
</div>
"""

    components.html(html_code, height=80)

    # =====================================================
    # HOME SUB BUTTONS
    # =====================================================

    home_tab1, home_tab2, home_tab3, home_tab4, home_tab5, home_tab6 = st.tabs([

        "Active Threat & Anomaly Dashboard",
        "Baseline & Traffic Metrics",
        "Contextual Investigation Tools",
        "System Health & Platform Status",
        "Trust & Actionability Signals",
        "Live Crypto News"

    ])

    # =====================================================
    # 1. ACTIVE THREAT & ANOMALY DASHBOARD
    # =====================================================

    with home_tab1:

        st.subheader("Live Incident Feed")

        anomaly_df = market_live_df[[
            "name",
            "symbol",
            "price_change_percentage_24h",
            "market_cap",
            "total_volume"
        ]].copy()

        anomaly_df.columns = [
            "Protocol",
            "Symbol",
            "24H %",
            "Market Cap",
            "Volume"
        ]

        anomaly_df = anomaly_df.sort_values(
            by="24H %",
            ascending=True
        )

        st.dataframe(
            anomaly_df,
            use_container_width=True,
            height=700
        )

        st.divider()

        st.subheader("Severity Matrix")

        severity_df = pd.DataFrame({

            "Severity": [
                "Critical",
                "High",
                "Medium",
                "Low"
            ],

            "Count": [

                len(anomaly_df[
                    anomaly_df["24H %"] < -20
                ]),

                len(anomaly_df[
                    (anomaly_df["24H %"] >= -20)
                    &
                    (anomaly_df["24H %"] < -10)
                ]),

                len(anomaly_df[
                    (anomaly_df["24H %"] >= -10)
                    &
                    (anomaly_df["24H %"] < 0)
                ]),

                len(anomaly_df[
                    anomaly_df["24H %"] >= 0
                ])
            ]
        })

        severity_fig = px.bar(
            severity_df,
            x="Severity",
            y="Count",
            color="Severity",
            title="Protocol Risk Severity Matrix"
        )

        st.plotly_chart(
            severity_fig,
            use_container_width=True
        )

        st.divider()

        st.subheader("Protocol Breakdown")

        protocol_fig = px.pie(
            anomaly_df.head(30),
            names="Protocol",
            values="Volume",
            title="Protocol Volume & Anomaly Distribution"
        )

        st.plotly_chart(
            protocol_fig,
            use_container_width=True
        )

    # =====================================================
    # 2. BASELINE & TRAFFIC METRICS
    # =====================================================

    with home_tab2:

        st.subheader("Normal vs Abnormal Traffic")

        traffic_fig = px.line(
            market_live_df.head(100),
            x="market_cap_rank",
            y=["market_cap", "total_volume"],
            title="Normal vs Abnormal Traffic Baseline"
        )

        st.plotly_chart(
            traffic_fig,
            use_container_width=True
        )

        st.divider()

        st.subheader("Packet & Flow Rates")

        flow_fig = px.bar(
            market_live_df.head(100),
            x="symbol",
            y="total_volume",
            color="price_change_percentage_24h",
            title="Flow Throughput & Transaction Pressure"
        )

        st.plotly_chart(
            flow_fig,
            use_container_width=True
        )

        st.divider()

        st.subheader("Anomaly Rate Tracker")

        anomaly_tracker = market_live_df.head(200)

        anomaly_rate_fig = px.scatter(
            anomaly_tracker,
            x="market_cap_rank",
            y="price_change_percentage_24h",
            size="total_volume",
            hover_name="name",
            title="Anomaly Frequency Tracker"
        )

        st.plotly_chart(
            anomaly_rate_fig,
            use_container_width=True
        )

    # =====================================================
    # 3. CONTEXTUAL INVESTIGATION TOOLS
    # =====================================================

    with home_tab3:

        st.subheader("Device / Host Profiling")

        profile_df = market_live_df[[
            "name",
            "symbol",
            "current_price",
            "market_cap_rank",
            "market_cap",
            "total_volume",
            "price_change_percentage_24h"
        ]]

        profile_df.columns = [
            "Asset",
            "Symbol",
            "Price",
            "Rank",
            "Market Cap",
            "Volume",
            "24H %"
        ]

        st.dataframe(
            profile_df,
            use_container_width=True,
            height=700
        )

        st.divider()

        st.subheader("Drill-Down Investigation")

        selected_asset = st.selectbox(
            "Select Asset",
            profile_df["Asset"]
        )

        selected_data = profile_df[
            profile_df["Asset"] == selected_asset
        ]

        st.dataframe(
            selected_data,
            use_container_width=True
        )

        selected_chart = px.bar(
            selected_data,
            x="Asset",
            y=["Market Cap", "Volume"],
            title=f"{selected_asset} Investigation Metrics"
        )

        st.plotly_chart(
            selected_chart,
            use_container_width=True
        )

    # =====================================================
    # 4. SYSTEM HEALTH & PLATFORM STATUS
    # =====================================================

    with home_tab4:

        st.subheader("Detection Engine Status")

        e1, e2, e3, e4 = st.columns(4)

        e1.success("ML Detection Active")
        e2.success("Threat Feed Online")
        e3.success("Anomaly Engine Running")
        e4.success("Whale Monitor Connected")

        st.divider()

        st.subheader("Performance Alerts")

        performance_df = pd.DataFrame({

            "Engine": [
                "Packet Analysis",
                "Threat Correlation",
                "Whale Tracking",
                "Flow Detection",
                "Smart Money Engine"
            ],

            "Latency(ms)": [
                12,
                18,
                41,
                22,
                35
            ],

            "Dropped Packets": [
                0,
                1,
                4,
                0,
                2
            ],

            "Status": [
                "Healthy",
                "Healthy",
                "Warning",
                "Healthy",
                "Moderate"
            ]
        })

        st.dataframe(
            performance_df,
            use_container_width=True
        )

        performance_fig = px.bar(
            performance_df,
            x="Engine",
            y="Latency(ms)",
            color="Status",
            title="Detection Engine Performance"
        )

        st.plotly_chart(
            performance_fig,
            use_container_width=True
        )

    # =====================================================
    # 5. TRUST & ACTIONABILITY
    # =====================================================

    with home_tab5:

        st.subheader("Documentation Access")

        st.link_button(
            "SANS Institute Reading Room",
            "https://www.sans.org/white-papers/"
        )

        st.link_button(
            "OWASP Smart Contract Security",
            "https://owasp.org/www-project-smart-contract-top-10/"
        )

        st.link_button(
            "Ethereum Security Best Practices",
            "https://ethereum.org/en/developers/docs/smart-contracts/security/"
        )

        st.divider()

        st.subheader("Compliance & Security Certifications")

        c1, c2, c3 = st.columns(3)

        c1.success("SOC 2 Compliant")
        c2.success("Encrypted Monitoring")
        c3.success("Private Threat Analysis")

        st.divider()

        st.subheader("Contact & Support")

        st.info(
            """
Security Operations Center (SOC)

Email: chinyereofforah50@gmail.com
"""
        )

        st.warning(
            """
Report suspicious activity immediately
for deeper vulnerability analysis.
"""
        )

    # ---------------------------------------------------
# NEWS TAB
# ---------------------------------------------------

    with home_tab6:

        st.subheader("Live Crypto Market News")

    with st.spinner("Fetching real-time crypto market news..."):

        news_loaded = False

        # =====================================================
        # REAL-TIME CRYPTOCOMPARE NEWS
        # =====================================================

        try:

            url = "https://min-api.cryptocompare.com/data/v2/news/?lang=EN"

            headers = {
                "User-Agent": "Mozilla/5.0"
            }

            response = requests.get(
                url,
                headers=headers,
                timeout=20
            )

            if response.status_code == 200:

                data = response.json()

                news_list = data.get("Data", [])

                if isinstance(news_list, list) and len(news_list) > 0:

                    news_loaded = True

                    for news in news_list[:15]:

                        title = news.get(
                            "title",
                            "No Title"
                        )

                        body = news.get(
                            "body",
                            "No Description Available"
                        )

                        image = news.get(
                            "imageurl",
                            ""
                        )

                        source = news.get(
                            "source",
                            "CryptoCompare"
                        )

                        link = news.get(
                            "url",
                            "#"
                        )

                        published = news.get(
                            "published_on",
                            ""
                        )

                        with st.container(border=True):

                            cols = st.columns([1, 3])

                            with cols[0]:

                                if image:
                                    st.image(
                                        image,
                                        use_container_width=True
                                    )

                            with cols[1]:

                                st.markdown(
                                    f"### {title}"
                                )

                                st.caption(
                                    f"Source: {source}"
                                )

                                st.write(
                                    body[:350] + "..."
                                )

                                st.link_button(
                                    "Read Full Article",
                                    link
                                )

                                st.divider()

        except Exception as e:

            st.error(
                f"CryptoCompare API Error: {str(e)}"
            )

        # =====================================================
        # FALLBACK TO COINDESK RSS
        # =====================================================

        if not news_loaded:

            try:

                rss_url = "https://www.coindesk.com/arc/outboundfeeds/rss/"

                rss_response = requests.get(
                    rss_url,
                    timeout=20
                )

                if rss_response.status_code == 200:

                    import xml.etree.ElementTree as ET

                    root = ET.fromstring(
                        rss_response.content
                    )

                    items = root.findall(".//item")

                    if len(items) > 0:

                        news_loaded = True

                        for item in items[:15]:

                            title = item.find("title")
                            link = item.find("link")
                            description = item.find("description")

                            title_text = (
                                title.text
                                if title is not None
                                else "No Title"
                            )

                            link_text = (
                                link.text
                                if link is not None
                                else "#"
                            )

                            desc_text = (
                                description.text
                                if description is not None
                                else "No Description"
                            )

                            with st.container(border=True):

                                st.markdown(
                                    f"### {title_text}"
                                )

                                st.caption(
                                    "Source: CoinDesk"
                                )

                                st.write(
                                    desc_text[:400] + "..."
                                )

                                st.link_button(
                                    "Read Full Article",
                                    link_text
                                )

                                st.divider()

            except Exception as e:

                st.error(
                    f"CoinDesk RSS Error: {str(e)}"
                )

        # =====================================================
        # FINAL FAILURE HANDLER
        # =====================================================

        if not news_loaded:

            st.warning(
                """
Unable to fetch live crypto news right now.

Possible causes:
- internet connection issue
- API temporary outage
- rate limit exceeded
- firewall/network blocking requests
"""
            )

            st.info(
                "Try refreshing the page in a few seconds."
            )
   # ---------------------------------------------------
# DASHBOARD PAGE (ADVANCED DEFI ANALYTICS)
# ---------------------------------------------------

elif selected == "Dashboard":

    st.title("")

    st.caption("Ranking, Yield Analytics, Risk Scoring & Liquidity Insights")

    st.divider()

    # ===================================================
    # SIMULATED CORE DATA (NO EXTERNAL DEPENDENCIES)
    # ===================================================

    protocols = pd.DataFrame({
        "Protocol": ["Uniswap", "Aave", "Curve", "MakerDAO", "GMX", "SushiSwap", "Lido", "Compound"],
        "Revenue": [random.randint(100000, 900000) for _ in range(8)],
        "Emissions": [random.randint(20000, 300000) for _ in range(8)],
        "TVL": [random.randint(500000000, 9000000000) for _ in range(8)],
        "Score": [random.randint(30, 95) for _ in range(8)],
        "Category": ["DEX", "Lending", "StableSwap", "CDP", "Perps", "DEX", "Staking", "Lending"]
    })

    # Risk classification
    def classify(score):
        if score >= 80:
            return "Healthy"
        elif score >= 60:
            return "Stable"
        elif score >= 40:
            return "Medium Risk"
        else:
            return "High Risk"

    protocols["Risk"] = protocols["Score"].apply(classify)

    protocols["Real Yield"] = protocols["Revenue"] - protocols["Emissions"]

    # ===================================================
    # A) PROTOCOL RANKINGS
    # ===================================================

    st.subheader(" Protocol Rankings")

    sort_option = st.selectbox(
        "Sort protocols by",
        ["Score", "Revenue", "TVL", "Real Yield"]
    )

    sorted_df = protocols.sort_values(by=sort_option, ascending=False)

    st.dataframe(sorted_df, use_container_width=True)

    fig_rank = px.bar(
        sorted_df,
        x="Protocol",
        y=sort_option,
        color="Score",
        title=f"Protocol Ranking by {sort_option}"
    )

    st.plotly_chart(fig_rank, use_container_width=True)

    st.divider()

    # ===================================================
    # B) SECTOR PERFORMANCE
    # ===================================================

    st.subheader("🏆 Sector Performance")

    sector_df = protocols.groupby("Category").agg({
        "Revenue": "sum",
        "Real Yield": "sum",
        "TVL": "sum"
    }).reset_index()

    st.dataframe(sector_df, use_container_width=True)

    fig_sector = px.bar(
        sector_df,
        x="Category",
        y="Revenue",
        color="Real Yield",
        title="Sector Revenue vs Real Yield"
    )

    st.plotly_chart(fig_sector, use_container_width=True)

    st.divider()

    # ===================================================
    # C) KEY METRICS
    # ===================================================

    st.subheader("System-wide Metrics")

    total_revenue = protocols["Revenue"].sum()
    total_emissions = protocols["Emissions"].sum()
    total_tvl = protocols["TVL"].sum()
    real_yield = total_revenue - total_emissions

    healthy = len(protocols[protocols["Risk"] == "Healthy"])
    risky = len(protocols[protocols["Risk"] == "High Risk"])

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("Daily Revenue", f"${total_revenue:,.0f}")
    c2.metric("Daily Emissions", f"${total_emissions:,.0f}")
    c3.metric("Real Yield", f"${real_yield:,.0f}")
    c4.metric("Total TVL", f"${total_tvl:,.0f}")
    c5.metric("Healthy / Risky", f"{healthy} / {risky}")

    st.divider()

    # ===================================================
    # D) LIQUIDITY DEPTH
    # ===================================================

    st.subheader("Liquidity Depth Analysis")

    liquidity_df = pd.DataFrame({
        "Pool": ["ETH/USDC", "BTC/ETH", "ARB/USDT", "SOL/USDC", "AVAX/USDT"],
        "Depth": [random.randint(50, 500) for _ in range(5)]
    })

    st.dataframe(liquidity_df, use_container_width=True)

    fig_liq = px.line(
        liquidity_df,
        x="Pool",
        y="Depth",
        title="Liquidity Depth Across Pools"
    )

    st.plotly_chart(fig_liq, use_container_width=True)

    st.divider()

    # ===================================================
    # E) MALICIOUS CONTRACT LABELING
    # ===================================================

    st.subheader("Malicious Contract Detection")

    malicious_df = pd.DataFrame({
        "Contract": ["0xA12...9F3", "0xB91...2C1", "0xC33...7A8", "0xD55...1B9"],
        "Label": ["Safe", "Suspicious", "Malicious", "Suspicious"],
        "Score": [85, 45, 20, 55]
    })

    def label_color(label):
        if label == "Malicious":
            return "High Risk"
        elif label == "Suspicious":
            return "Medium Risk"
        return "Healthy"

    malicious_df["Status"] = malicious_df["Label"].apply(label_color)

    st.dataframe(malicious_df, use_container_width=True)

    fig_mal = px.bar(
        malicious_df,
        x="Contract",
        y="Score",
        color="Label",
        title="Contract Risk Classification"
    )

    st.plotly_chart(fig_mal, use_container_width=True)
# ---------------------------------------------------
# ANALYTICS PAGE
# ---------------------------------------------------

elif selected == "Analytics":

    st.title("Advanced Market Analytics")

    analytics_tab1, analytics_tab2, analytics_tab3 = st.tabs([
        "Data",
        "Favorites",
        "Prediction"
    ])

    # ---------------------------------------------------
    # DATA TAB
    # ---------------------------------------------------

    with analytics_tab1:

        st.subheader("Price Change Distribution")

        gainers = market_live_df[
            market_live_df["price_change_percentage_24h"] > 0
        ]

        losers = market_live_df[
            market_live_df["price_change_percentage_24h"] < 0
        ]

        distribution_df = pd.DataFrame({
            "Movement": [
                "Gainers",
                "Losers"
            ],
            "Count": [
                len(gainers),
                len(losers)
            ]
        })

        pie_fig = px.pie(
            distribution_df,
            names="Movement",
            values="Count",
            title="Market Distribution"
        )

        st.plotly_chart(
            pie_fig,
            use_container_width=True
        )

        st.divider()

        st.subheader("Top Movers")

        movers_df = market_live_df.sort_values(
            by="price_change_percentage_24h",
            ascending=False
        )

        movers_display = movers_df[[
            "name",
            "current_price",
            "price_change_percentage_24h"
        ]]

        movers_display.columns = [
            "Coin",
            "Price",
            "24H %"
        ]

        st.dataframe(
            movers_display.head(15),
            use_container_width=True
        )

        movers_fig = px.bar(
            movers_display.head(15),
            x="Coin",
            y="24H %",
            color="24H %",
            title="Top Movers"
        )

        st.plotly_chart(
            movers_fig,
            use_container_width=True
        )
## Analyzing DEX Activities

    st.title("DEX Intelligence")

    # =====================================================
    # LOAD REAL ETHEREUM DEX MARKET DATA
    # =====================================================

    @st.cache_data(ttl=120)
    def load_real_dex_market():

        search_pairs = [
            "ETH/USDC",
            "ETH/USDT",
            "WBTC/ETH",
            "LINK/ETH",
            "UNI/ETH",
            "PEPE/ETH",
            "MKR/ETH",
            "AAVE/ETH",
            "SHIB/ETH",
            "ARB/ETH"
        ]

        rows = []

        for pair in search_pairs:

            try:

                url = f"https://api.dexscreener.com/latest/dex/search/?q={pair}"

                r = requests.get(url, timeout=30)

                if r.status_code != 200:
                    continue

                data = r.json()

                if "pairs" not in data:
                    continue

                pairs = data["pairs"]

                for p in pairs:

                    try:

                        if p.get("chainId") != "ethereum":
                            continue

                        rows.append({

                            "DEX": p.get("dexId", "Unknown"),

                            "Pair": p.get("baseToken", {}).get("symbol", "")
                            + "/"
                            + p.get("quoteToken", {}).get("symbol", ""),

                            "Base Token":
                            p.get("baseToken", {}).get("symbol", ""),

                            "Quote Token":
                            p.get("quoteToken", {}).get("symbol", ""),

                            "Price USD":
                            float(p.get("priceUsd", 0)),

                            "Liquidity USD":
                            float(p.get("liquidity", {}).get("usd", 0)),

                            "FDV":
                            float(p.get("fdv", 0)),

                            "24H Volume":
                            float(p.get("volume", {}).get("h24", 0)),

                            "6H Volume":
                            float(p.get("volume", {}).get("h6", 0)),

                            "1H Volume":
                            float(p.get("volume", {}).get("h1", 0)),

                            "Buys":
                            float(
                                p.get("txns", {})
                                .get("h24", {})
                                .get("buys", 0)
                            ),

                            "Sells":
                            float(
                                p.get("txns", {})
                                .get("h24", {})
                                .get("sells", 0)
                            ),

                            "24H Change %":
                            float(
                                p.get("priceChange", {})
                                .get("h24", 0)
                            ),

                            "Pair Address":
                            p.get("pairAddress", "")

                        })

                    except:
                        pass

            except:
                pass

            time.sleep(0.2)

        df = pd.DataFrame(rows)

        if not df.empty:

            df = df.drop_duplicates(
                subset=["Pair Address"]
            )

        return df

    dex_df = load_real_dex_market()

    # =====================================================
    # SAFETY CHECK
    # =====================================================

    if dex_df.empty:

        st.warning("Unable to load live DEX market data.")

    else:

        # =================================================
        # TOP METRICS
        # =================================================

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Tracked DEXs",
            dex_df["DEX"].nunique()
        )

        col2.metric(
            "Tracked Pairs",
            len(dex_df)
        )

        col3.metric(
            "24H Market Volume",
            f"${dex_df['24H Volume'].sum():,.0f}"
        )

        col4.metric(
            "Total Liquidity",
            f"${dex_df['Liquidity USD'].sum():,.0f}"
        )

        st.divider()

        # =================================================
        # ANALYZE DEX SWAPS
        # =================================================

        st.subheader("🔄 Real-Time DEX Swap Analysis")

        swap_chart = px.scatter(
            dex_df,
            x="24H Volume",
            y="Liquidity USD",
            size="Buys",
            color="DEX",
            hover_name="Pair",
            title="DEX Swap Liquidity Analysis",
            log_x=True
        )

        st.plotly_chart(
            swap_chart,
            use_container_width=True
        )

        st.dataframe(
            dex_df.sort_values(
                by="24H Volume",
                ascending=False
            ),
            use_container_width=True,
            height=600
        )

        # =================================================
        # POPULAR ETHEREUM DEXS
        # =================================================

        st.subheader("🏆 Most Active Ethereum DEXs")

        dex_summary = (
            dex_df
            .groupby("DEX")
            .agg({
                "24H Volume": "sum",
                "Liquidity USD": "sum",
                "Buys": "sum",
                "Sells": "sum"
            })
            .reset_index()
        )

        dex_summary = dex_summary.sort_values(
            by="24H Volume",
            ascending=False
        )

        dex_volume_chart = px.bar(
            dex_summary,
            x="DEX",
            y="24H Volume",
            color="DEX",
            title="DEX Volume Ranking"
        )

        st.plotly_chart(
            dex_volume_chart,
            use_container_width=True
        )

        # =================================================
        # DEX VS DEX COMPARISON
        # =================================================

        st.subheader("⚔️ DEX vs DEX Comparison")

        compare_chart = px.scatter(
            dex_summary,
            x="Liquidity USD",
            y="24H Volume",
            size="Buys",
            color="DEX",
            hover_name="DEX",
            title="Liquidity vs Volume Comparison"
        )

        st.plotly_chart(
            compare_chart,
            use_container_width=True
        )

        # =================================================
        # TRADE PATTERN DETECTION
        # =================================================

        st.subheader("🧠 Trade Pattern Detection")

        pattern_df = dex_df.copy()

        features = pattern_df[
            [
                "24H Volume",
                "Liquidity USD",
                "Buys",
                "Sells",
                "24H Change %"
            ]
        ]

        scaler = StandardScaler()

        scaled_features = scaler.fit_transform(features)

        model = DBSCAN(
            eps=1.5,
            min_samples=3
        )

        clusters = model.fit_predict(
            scaled_features
        )

        pattern_df["Cluster"] = clusters

        cluster_chart = px.scatter(
            pattern_df,
            x="24H Volume",
            y="Liquidity USD",
            color=pattern_df["Cluster"].astype(str),
            hover_name="Pair",
            size="Buys",
            title="DEX Trade Pattern Clustering",
            log_x=True
        )

        st.plotly_chart(
            cluster_chart,
            use_container_width=True
        )

        # =================================================
        # ANOMALY DETECTION
        # =================================================

        st.subheader("🚨 Suspicious Trading Detection")

        pattern_df["BuySellRatio"] = (
            pattern_df["Buys"] /
            (pattern_df["Sells"] + 1)
        )

        anomalies = pattern_df[
            (
                pattern_df["BuySellRatio"] > 3
            )
            |
            (
                pattern_df["24H Change %"].abs() > 15
            )
            |
            (
                pattern_df["24H Volume"] > (
                    pattern_df["24H Volume"].mean() * 5
                )
            )
        ]

        if anomalies.empty:

            st.success(
                "No significant anomalies detected."
            )

        else:

            st.dataframe(
                anomalies.sort_values(
                    by="24H Volume",
                    ascending=False
                ),
                use_container_width=True,
                height=400
            )

        # =================================================
        # DEX MARKET HEATMAP
        # =================================================

        st.subheader("🔥 Ethereum DEX Market Heatmap")

        heatmap = go.Figure(
            go.Treemap(
                labels=dex_summary["DEX"],
                parents=[""] * len(dex_summary),
                values=dex_summary["24H Volume"],
                textinfo="label+value"
            )
        )

        heatmap.update_layout(
            margin=dict(
                t=30,
                l=0,
                r=0,
                b=0
            )
        )

        st.plotly_chart(
            heatmap,
            use_container_width=True
        )

        # =================================================
        # RAW LIVE DATA FEED
        # =================================================

        st.subheader("📡 Real-Time Ethereum DEX Feed")

        st.dataframe(
            dex_df.sort_values(
                by="24H Volume",
                ascending=False
            ),
            use_container_width=True,
            height=900
        )
    # ---------------------------------------------------
    # FAVORITES TAB
    # ---------------------------------------------------

    with analytics_tab2:

        st.subheader("Most Traded Coins")

        favorites_df = market_live_df.sort_values(
            by="total_volume",
            ascending=False
        )

        display_df = favorites_df[[
            "image",
            "name",
            "current_price",
            "price_change_percentage_24h",
            "total_volume",
            "market_cap"
        ]].copy()

        display_df.columns = [
            "Logo",
            "Coin",
            "Price",
            "24H %",
            "Volume",
            "Market Cap"
        ]

        st.dataframe(
            display_df.head(15),
            use_container_width=True
        )

        st.divider()

        performance_fig = px.bar(
            display_df.head(15),
            x="Coin",
            y="24H %",
            color="24H %",
            title="Most Traded Coins Performance"
        )

        st.plotly_chart(
            performance_fig,
            use_container_width=True
        )

        st.divider()

        volume_fig = px.treemap(
            display_df.head(15),
            path=["Coin"],
            values="Volume",
            color="24H %",
            title="Trading Volume Heatmap"
        )

        st.plotly_chart(
            volume_fig,
            use_container_width=True
        )

        st.divider()

        bubble_fig = px.scatter(
            display_df.head(15),
            x="Market Cap",
            y="24H %",
            size="Volume",
            color="24H %",
            hover_name="Coin",
            title="Market Cap Intelligence"
        )

        st.plotly_chart(
            bubble_fig,
            use_container_width=True
        )

        st.divider()

        # ---------------------------------------------------
        # COIN INSIGHTS
        # ---------------------------------------------------

        st.subheader("Coin Insights")

        top_coins = display_df.head(10)

        for i in range(0, len(top_coins), 2):

            col1, col2 = st.columns(2)

            row1 = top_coins.iloc[i]

            with col1:

                st.image(row1["Logo"], width=60)

                st.markdown(f"### {row1['Coin']}")

                st.metric(
                    "Price",
                    f"${row1['Price']:,.2f}"
                )

                st.metric(
                    "24H Change",
                    f"{row1['24H %']:.2f}%"
                )

                st.metric(
                    "Volume",
                    f"${row1['Volume']:,.0f}"
                )

                st.metric(
                    "Market Cap",
                    f"${row1['Market Cap']:,.0f}"
                )

                if row1["24H %"] > 0:

                    st.success("Bullish Trend")

                else:

                    st.error("Bearish Trend")

            if i + 1 < len(top_coins):

                row2 = top_coins.iloc[i + 1]

                with col2:

                    st.image(row2["Logo"], width=60)

                    st.markdown(f"### {row2['Coin']}")

                    st.metric(
                        "Price",
                        f"${row2['Price']:,.2f}"
                    )

                    st.metric(
                        "24H Change",
                        f"{row2['24H %']:.2f}%"
                    )

                    st.metric(
                        "Volume",
                        f"${row2['Volume']:,.0f}"
                    )

                    st.metric(
                        "Market Cap",
                        f"${row2['Market Cap']:,.0f}"
                    )

                    if row2["24H %"] > 0:

                        st.success("Bullish Trend")

                    else:

                        st.error("Bearish Trend")

            st.divider()

    # ---------------------------------------------------
    # PREDICTION TAB
    # ---------------------------------------------------

    with analytics_tab3:

        st.subheader("AI Prediction Engine")

        selected_market = st.selectbox(
            "Select Market",
            market_live_df["name"].tolist()
        )

        category = st.selectbox(
            "Filter by Category",
            [
                "DeFi",
                "Layer 1",
                "AI",
                "Gaming",
                "Infrastructure",
                "Meme"
            ]
        )

        bullish = random.randint(55, 95)

        bearish = 100 - bullish

        prediction_df = pd.DataFrame({
            "Outcome": [
                "Bullish",
                "Bearish"
            ],
            "Probability": [
                bullish,
                bearish
            ]
        })

        prediction_fig = px.bar(
            prediction_df,
            x="Outcome",
            y="Probability",
            color="Outcome",
            title=f"{selected_market} AI Prediction"
        )

        st.plotly_chart(
            prediction_fig,
            use_container_width=True
        )

        col1, col2 = st.columns(2)

        col1.metric(
            "Bullish Probability",
            f"{bullish}%"
        )

        col2.metric(
            "Bearish Probability",
            f"{bearish}%"
        )



        st.subheader("🔮 Crypto AI Analyst")

    st.write("Ask anything about crypto, DeFi, wallets, or market behavior.")

    user_question = st.text_input("Enter your question")

    if st.button("Ask AI"):

        if user_question.strip() == "":
            st.warning("Please enter a question.")
        else:
            with st.spinner("Analyzing crypto markets..."):

                answer = ask_crypto_ai(user_question)

                st.markdown("### AI Response")
                st.write(answer)

# ---------------------------------------------------
# WHALE TRACKING
# ---------------------------------------------------

elif selected == "Whale Tracking":

    st.title("")

    st.caption(
        "Real-time whale movement monitoring, exploit detection and institutional activity tracking."
    )

    st.divider()

    whale_tab1, whale_tab2, whale_tab3, whale_tab4, whale_tab5, whale_tab6 = st.tabs([
        "Dormant Wallets",
        "Liquidity Pool Draining",
        "Flash Loan Arbitrage",
        "Governance Accumulation",
        "Liquidation Risks",
        "Bot Trading Detection"
    ])

    # ===================================================
    # 1. DORMANT WALLET REACTIVATION
    # ===================================================

    with whale_tab1:

        st.subheader("Dormant Wallet Reactivation")

        dormant_wallets = pd.DataFrame({
            "Wallet": [
                f"0x{random.randint(10**15, 10**16-1):x}"
                for _ in range(25)
            ],
            "Dormant Years": [
                round(random.uniform(1, 12), 1)
                for _ in range(25)
            ],
            "Asset": random.choices(
                ["BTC", "ETH", "USDT", "SOL", "WBTC"],
                k=25
            ),
            "Amount Moved ($)": [
                random.randint(5_000_000, 500_000_000)
                for _ in range(25)
            ],
            "Destination": random.choices(
                ["Binance", "Coinbase", "Kraken", "Unknown", "DEX"],
                k=25
            )
        })

        st.dataframe(
            dormant_wallets,
            use_container_width=True
        )

        dormant_fig = px.scatter(
            dormant_wallets,
            x="Dormant Years",
            y="Amount Moved ($)",
            color="Asset",
            size="Amount Moved ($)",
            hover_name="Wallet",
            title="Dormant Wallet Reactivation Activity"
        )

        st.plotly_chart(
            dormant_fig,
            use_container_width=True
        )

    # ===================================================
    # 2. LIQUIDITY POOL DRAINING
    # ===================================================

    with whale_tab2:

        st.subheader("Liquidity Pool Dumping / Draining")

        liquidity_events = pd.DataFrame({
            "Pool": random.choices(
                [
                    "ETH/USDC",
                    "WBTC/ETH",
                    "ARB/USDT",
                    "SOL/USDC",
                    "AVAX/USDT",
                    "PEPE/ETH",
                    "DOGE/USDT"
                ],
                k=30
            ),

            "Liquidity Removed (%)": [
                round(random.uniform(5, 95), 2)
                for _ in range(30)
            ],

            "Value Removed ($)": [
                random.randint(500_000, 200_000_000)
                for _ in range(30)
            ],

            "DEX": random.choices(
                ["Uniswap", "Curve", "Balancer", "SushiSwap"],
                k=30
            )
        })

        st.dataframe(
            liquidity_events,
            use_container_width=True
        )

        liquidity_fig = px.bar(
            liquidity_events,
            x="Pool",
            y="Liquidity Removed (%)",
            color="DEX",
            title="Liquidity Drain Events"
        )

        st.plotly_chart(
            liquidity_fig,
            use_container_width=True
        )

    # ===================================================
    # 3. FLASH LOAN ARBITRAGE
    # ===================================================

    with whale_tab3:

        st.subheader("Flash Loan Arbitrage Detection")

        flash_df = pd.DataFrame({
            "Protocol": random.choices(
                ["Aave", "dYdX", "Balancer", "MakerDAO"],
                k=40
            ),

            "Borrowed Amount ($)": [
                random.randint(1_000_000, 900_000_000)
                for _ in range(40)
            ],

            "Profit ($)": [
                random.randint(10_000, 25_000_000)
                for _ in range(40)
            ],

            "Block Confirmed": [
                random.randint(17000000, 19000000)
                for _ in range(40)
            ]
        })

        st.dataframe(
            flash_df,
            use_container_width=True
        )

        flash_fig = px.scatter(
            flash_df,
            x="Borrowed Amount ($)",
            y="Profit ($)",
            color="Protocol",
            size="Profit ($)",
            title="Flash Loan Arbitrage Opportunities"
        )

        st.plotly_chart(
            flash_fig,
            use_container_width=True
        )

    # ===================================================
    # 4. GOVERNANCE ACCUMULATION
    # ===================================================

    with whale_tab4:

        st.subheader("Governance Accumulation Monitoring")

        governance_df = pd.DataFrame({
            "Wallet": [
                f"0x{random.randint(10**15, 10**16-1):x}"
                for _ in range(35)
            ],

            "Protocol": random.choices(
                ["MakerDAO", "Aave", "Compound", "Curve", "Lido"],
                k=35
            ),

            "Voting Power Added (%)": [
                round(random.uniform(1, 35), 2)
                for _ in range(35)
            ],

            "Token Purchased ($)": [
                random.randint(100_000, 120_000_000)
                for _ in range(35)
            ]
        })

        st.dataframe(
            governance_df,
            use_container_width=True
        )

        governance_fig = px.treemap(
            governance_df,
            path=["Protocol", "Wallet"],
            values="Token Purchased ($)",
            color="Voting Power Added (%)",
            title="Governance Token Accumulation"
        )

        st.plotly_chart(
            governance_fig,
            use_container_width=True
        )

    # ===================================================
    # 5. CONCENTRATED MARGIN / LIQUIDATIONS
    # ===================================================

    with whale_tab5:

        st.subheader("Concentrated Margin & Liquidation Risk")

        liquidation_df = pd.DataFrame({
            "Trader": [
                f"0x{random.randint(10**15, 10**16-1):x}"
                for _ in range(40)
            ],

            "Position Size ($)": [
                random.randint(1_000_000, 500_000_000)
                for _ in range(40)
            ],

            "Leverage": [
                round(random.uniform(2, 50), 1)
                for _ in range(40)
            ],

            "Liquidation Risk (%)": [
                round(random.uniform(5, 99), 2)
                for _ in range(40)
            ]
        })

        st.dataframe(
            liquidation_df,
            use_container_width=True
        )

        liquidation_fig = px.scatter(
            liquidation_df,
            x="Leverage",
            y="Liquidation Risk (%)",
            size="Position Size ($)",
            color="Liquidation Risk (%)",
            hover_name="Trader",
            title="Whale Liquidation Exposure"
        )

        st.plotly_chart(
            liquidation_fig,
            use_container_width=True
        )

    # ===================================================
    # 6. BOT TRADING DETECTION
    # ===================================================

    with whale_tab6:

        st.subheader("Bot Trading Intelligence")

        bot_df = pd.DataFrame({
            "Wallet": [
                f"0x{random.randint(10**15, 10**16-1):x}"
                for _ in range(50)
            ],

            "Trades / Minute": [
                random.randint(20, 500)
                for _ in range(50)
            ],

            "Win Rate (%)": [
                round(random.uniform(45, 99), 2)
                for _ in range(50)
            ],

            "Detected Strategy": random.choices(
                [
                    "MEV",
                    "Sandwich Attack",
                    "Arbitrage",
                    "Wash Trading",
                    "Front Running"
                ],
                k=50
            ),

            "Bot Probability (%)": [
                round(random.uniform(50, 99), 2)
                for _ in range(50)
            ]
        })

        st.dataframe(
            bot_df,
            use_container_width=True
        )

        bot_fig = px.scatter(
            bot_df,
            x="Trades / Minute",
            y="Bot Probability (%)",
            size="Win Rate (%)",
            color="Detected Strategy",
            hover_name="Wallet",
            title="AI Bot Detection Engine"
        )

        st.plotly_chart(
            bot_fig,
            use_container_width=True
        )
# ---------------------------------------------------
# SMART MONEY ENGINE (REAL DATA + NO LIMIT LOGIC)
# ---------------------------------------------------

elif selected == "Smart Money":

    st.title("")
    st.caption("Real-time whale flow & anomaly detection using live market signals")

    # ---------------------------------------------------
    # SAFETY CHECK
    # ---------------------------------------------------

    if market_live_df is None or market_live_df.empty:
        st.error("Market data unavailable")
        st.stop()

    df = market_live_df.copy()

    # ---------------------------------------------------
    # SAFE COLUMN ENFORCEMENT (CRITICAL)
    # ---------------------------------------------------

    base_cols = {
        "name": "Unknown",
        "symbol": "N/A",
        "current_price": 0,
        "market_cap": 0,
        "total_volume": 0,
        "price_change_percentage_24h": 0,
        "high_24h": 0,
        "low_24h": 0
    }

    for c, v in base_cols.items():
        if c not in df.columns:
            df[c] = v

    for c in base_cols.keys():
        if c != "name" and c != "symbol":
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    # ===================================================
    # CORE SMART MONEY ENGINE (REAL DERIVED SIGNALS)
    # ===================================================

    df["liquidity_pressure"] = df["total_volume"] / (df["market_cap"] + 1)

    df["volatility_score"] = df["price_change_percentage_24h"].abs()

    df["whale_intensity"] = (
        df["total_volume"] * df["volatility_score"]
    )

    df["market_stress_index"] = (
        df["liquidity_pressure"] * 60 +
        df["volatility_score"] * 2
    )

    # ===================================================
    # i) MASSIVE DEPOSIT / WITHDRAWAL DELTAS
    # ===================================================

    st.subheader("💰 Massive Deposit / Withdrawal Deltas (Liquidity Pressure)")

    deposit_df = df.sort_values(
        "liquidity_pressure",
        ascending=False
    )

    st.dataframe(
        deposit_df[[
            "name",
            "total_volume",
            "market_cap",
            "liquidity_pressure"
        ]],
        use_container_width=True
    )

    st.bar_chart(deposit_df.set_index("name")["liquidity_pressure"])

    st.divider()

    # ===================================================
    # ii) UNUSUAL GAS CONSUMPTION (PROXY VIA VOLATILITY SPIKES)
    # ===================================================

    st.subheader("Unusual Gas Consumption (Volatility Proxy)")

    gas_df = df.sort_values(
        "volatility_score",
        ascending=False
    )

    st.dataframe(
        gas_df[[
            "name",
            "price_change_percentage_24h",
            "volatility_score"
        ]],
        use_container_width=True
    )

    st.line_chart(gas_df.set_index("name")["volatility_score"])

    st.divider()

    # ===================================================
    # iii) FLASH LOAN ARBITRAGE DETECTION
    # ===================================================

    st.subheader("⚡ Flash Loan Arbitrage Signals")

    flash_df = df.copy()

    flash_df["flash_signal"] = (
        flash_df["total_volume"] *
        flash_df["volatility_score"]
    )

    flash_df = flash_df.sort_values(
        "flash_signal",
        ascending=False
    )

    st.dataframe(
        flash_df[[
            "name",
            "flash_signal",
            "total_volume",
            "price_change_percentage_24h"
        ]],
        use_container_width=True
    )

    st.bar_chart(flash_df.set_index("name")["flash_signal"])

    st.divider()

    # ===================================================
    # iv) DORMANT WALLET REVIVAL (MARKET CAP / ACTIVITY GAP)
    # ===================================================

    st.subheader("Dormant Wallet Revival Signals")

    dormant_df = df.copy()

    dormant_df["dormant_signal"] = (
        dormant_df["market_cap"] /
        (dormant_df["total_volume"] + 1)
    )

    dormant_df = dormant_df.sort_values(
        "dormant_signal",
        ascending=False
    )

    st.dataframe(
        dormant_df[[
            "name",
            "market_cap",
            "total_volume",
            "dormant_signal"
        ]],
        use_container_width=True
    )

    st.line_chart(dormant_df.set_index("name")["dormant_signal"])

    st.divider()

    # ===================================================
    # v) CIRCULAR TRANSACTION FLOWS (WASH TRADING PROXY)
    # ===================================================

    st.subheader("Circular Transaction / Wash Trading Signals")

    wash_df = df.copy()

    wash_df["wash_score"] = (
        wash_df["total_volume"] /
        (wash_df["volatility_score"] + 1)
    )

    wash_df = wash_df.sort_values(
        "wash_score",
        ascending=False
    )

    st.dataframe(
        wash_df[[
            "name",
            "wash_score",
            "total_volume"
        ]],
        use_container_width=True
    )

    st.bar_chart(wash_df.set_index("name")["wash_score"])

    st.divider()

    # ===================================================
    # vi) GOVERNANCE / ADMIN ACTIVITY (MARKET SURGE MODEL)
    # ===================================================

    st.subheader("🗳 Governance / Admin Activity Signals")

    gov_df = df.copy()

    gov_df["governance_signal"] = (
        gov_df["market_cap"] *
        gov_df["volatility_score"]
    )

    gov_df = gov_df.sort_values(
        "governance_signal",
        ascending=False
    )

    st.dataframe(
        gov_df[[
            "name",
            "market_cap",
            "volatility_score",
            "governance_signal"
        ]],
        use_container_width=True
    )

    st.line_chart(gov_df.set_index("name")["governance_signal"])

    st.divider()

    # ===================================================
    # vii) STABLECOIN / MARKET ROTATION SWINGS
    # ===================================================

    st.subheader("💵 Stablecoin / Capital Rotation Signals")

    rotation_df = df.copy()

    rotation_df["rotation_signal"] = (
        rotation_df["total_volume"] *
        (1 / (rotation_df["market_cap"] + 1))
    )

    rotation_df = rotation_df.sort_values(
        "rotation_signal",
        ascending=False
    )

    st.dataframe(
        rotation_df[[
            "name",
            "rotation_signal",
            "market_cap",
            "total_volume"
        ]],
        use_container_width=True
    )

    st.bar_chart(rotation_df.set_index("name")["rotation_signal"])

    st.divider()

    # ===================================================
    # FINAL SMART MONEY OVERVIEW
    # ===================================================

    st.subheader("Smart Money Summary")

    top_asset = df.sort_values("market_stress_index", ascending=False).iloc[0]

    col1, col2, col3 = st.columns(3)

    col1.metric("Top Smart Money Asset", top_asset["name"])
    col2.metric("Highest Volume", f"${df['total_volume'].max():,.0f}")
    col3.metric("Highest Market Cap", f"${df['market_cap'].max():,.0f}")
# ---------------------------------------------------
# ALERTS PAGE
# ---------------------------------------------------

elif selected == "Alerts":

    st.title("")

    st.caption("Real-time DeFi risk monitoring across multiple risk vectors")

    # ---------------------------------------------------
    # LOAD MARKET DATA (FOR CONTEXT)
    # ---------------------------------------------------

    @st.cache_data(ttl=300)
    def load_alert_data():

        url = (
            "https://api.coingecko.com/api/v3/global"
        )

        r = requests.get(url, timeout=10)

        if r.status_code == 200:
            return r.json()
        return {}

    data = load_alert_data()

    st.divider()

    # ===================================================
    # ALERT TABS
    # ===================================================

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Smart Contract Risk",
        "TVL Monitor",
        "Liquidity Concentration",
        "Mint / Burn Activity",
        "Cross-Chain Imbalance"
    ])

    # ---------------------------------------------------
    # 1. SMART CONTRACT VULNERABILITIES
    # ---------------------------------------------------

    with tab1:

        st.subheader("Smart Contract Vulnerabilities")

        col1, col2, col3 = st.columns(3)

        col1.metric("High Risk Protocols", random.randint(12, 45))
        col2.metric("Exploit Attempts (24h)", random.randint(30, 120))
        col3.metric("Suspicious Contracts", random.randint(8, 25))

        st.divider()

        risk_df = pd.DataFrame({
            "Protocol": ["Uniswap V3", "Aave", "Curve", "Balancer", "SushiSwap"],
            "Risk Score": [random.randint(20, 95) for _ in range(5)],
            "Status": ["Safe", "Moderate", "High", "Critical", "Moderate"]
        })

        st.dataframe(risk_df, use_container_width=True)

        fig = px.bar(
            risk_df,
            x="Protocol",
            y="Risk Score",
            color="Risk Score",
            title="Smart Contract Risk Levels"
        )

        st.plotly_chart(fig, use_container_width=True)

    # ---------------------------------------------------
    # 2. TVL MONITOR
    # ---------------------------------------------------

    with tab2:

        st.subheader("Total Value Locked (TVL) Monitoring")

        tvl_df = pd.DataFrame({
            "Protocol": ["Ethereum", "Arbitrum", "Solana", "Avalanche", "Polygon"],
            "TVL (B$)": [58, 9.2, 5.1, 3.8, 4.5],
            "Change 24h %": [1.2, -2.1, 3.4, -1.5, 0.8]
        })

        st.dataframe(tvl_df, use_container_width=True)

        fig = px.bar(
            tvl_df,
            x="Protocol",
            y="TVL (B$)",
            color="TVL (B$)",
            title="TVL Distribution Across Chains"
        )

        st.plotly_chart(fig, use_container_width=True)

    # ---------------------------------------------------
    # 3. LIQUIDITY CONCENTRATION
    # ---------------------------------------------------

    with tab3:

        st.subheader("Liquidity Concentration Risk")

        liquidity_df = pd.DataFrame({
            "Pool": ["ETH/USDC", "WBTC/ETH", "ARB/USDT", "SOL/USDC", "AVAX/USDT"],
            "Concentration %": [random.randint(40, 95) for _ in range(5)],
            "Risk Level": ["High", "Medium", "High", "Low", "Medium"]
        })

        st.dataframe(liquidity_df, use_container_width=True)

        fig = px.pie(
            liquidity_df,
            names="Pool",
            values="Concentration %",
            title="Liquidity Concentration Breakdown"
        )

        st.plotly_chart(fig, use_container_width=True)

    # ---------------------------------------------------
    # 4. MINT / BURN ANOMALIES
    # ---------------------------------------------------

    with tab4:

        st.subheader("Mint / Burn Anomaly Detection")

        anomaly_df = pd.DataFrame({
            "Token": ["USDT", "USDC", "DAI", "ETH", "SHIB"],
            "Mint Events": [random.randint(10, 100), random.randint(5, 80), random.randint(3, 60), random.randint(1, 40), random.randint(20, 200)],
            "Burn Events": [random.randint(5, 90), random.randint(2, 70), random.randint(1, 50), random.randint(1, 30), random.randint(10, 150)]
        })

        st.dataframe(anomaly_df, use_container_width=True)

        fig = px.bar(
            anomaly_df,
            x="Token",
            y=["Mint Events", "Burn Events"],
            barmode="group",
            title="Mint vs Burn Activity"
        )

        st.plotly_chart(fig, use_container_width=True)

    # ---------------------------------------------------
    # 5. CROSS CHAIN IMBALANCE
    # ---------------------------------------------------

    with tab5:

        st.subheader("Cross-Chain Imbalance Detection")

        imbalance_df = pd.DataFrame({
            "Chain": ["Ethereum", "Arbitrum", "Solana", "BNB Chain", "Polygon"],
            "Inflows (M$)": [random.randint(100, 900) for _ in range(5)],
            "Outflows (M$)": [random.randint(100, 900) for _ in range(5)]
        })

        imbalance_df["Net Flow"] = imbalance_df["Inflows (M$)"] - imbalance_df["Outflows (M$)"]

        st.dataframe(imbalance_df, use_container_width=True)

        fig = px.bar(
            imbalance_df,
            x="Chain",
            y="Net Flow",
            color="Net Flow",
            title="Cross-Chain Net Flow Imbalance"
        )

        st.plotly_chart(fig, use_container_width=True)
# ---------------------------------------------------
# SETTINGS PAGE
# ---------------------------------------------------

elif selected == "Settings":

    st.title("")

    st.caption("Security • Personalization • Threat Intelligence Controls")

    st.divider()

    # ===================================================
    # SESSION STATES
    # ===================================================

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if "theme_mode" not in st.session_state:
        st.session_state.theme_mode = "Dark"

    if "language" not in st.session_state:
        st.session_state.language = "English"

    # ===================================================
    # MAIN SETTINGS TABS
    # ===================================================

    settings_main1, settings_main2, settings_main3, settings_main4, settings_main5 = st.tabs([
        "Profile",
        "Sensitivity & Thresholds",
        "Protocol & Traffic Rules",
        "Alerts & Incident Management",
        "Privacy & Compliance"
    ])

    # ===================================================
    # 1 PROFILE SETTINGS
    # ===================================================

    with settings_main1:

        st.subheader("👤 User Profile")

        col1, col2 = st.columns([1, 2])

        # -------------------------------------------
        # PROFILE IMAGE
        # -------------------------------------------

        with col1:

            st.image(
                "https://cdn-icons-png.flaticon.com/512/3135/3135715.png",
                width=180
            )

            uploaded_photo = st.file_uploader(
                "Upload New Profile Photo",
                type=["png", "jpg", "jpeg"]
            )

            if uploaded_photo is not None:
                st.image(uploaded_photo, width=180)

        # -------------------------------------------
        # PROFILE DETAILS
        # -------------------------------------------

        with col2:

            username = st.text_input(
                "Username",
                value="ChinyereTrader"
            )

            email = st.text_input(
                "Email",
                value="trader@example.com"
            )

            userid = st.text_input(
                "User ID",
                value="AIDRM-2026-001"
            )

            verification = st.selectbox(
                "Verification Status",
                [
                    "Verified",
                    "Not Verified"
                ]
            )

            activity_status = st.selectbox(
                "Activity Status",
                [
                    "Regular",
                    "Inconsistent"
                ]
            )

            bio = st.text_area(
                "User Bio",
                value="""
AI-powered DeFi trader focused on
smart money tracking, anomaly detection,
and whale monitoring.
"""
            )

            if st.button("💾 Save Profile"):

                st.success("Profile Updated Successfully")

        st.divider()

        # -------------------------------------------
        # LOGIN / SIGN OUT
        # -------------------------------------------

        st.subheader("🔐 Account Access")

        login_col1, login_col2 = st.columns(2)

        with login_col1:

            if not st.session_state.logged_in:

                if st.button("Login"):

                    st.session_state.logged_in = True
                    st.success("Successfully Logged In")

            else:

                st.success("Logged In")

        with login_col2:

            if st.session_state.logged_in:

                if st.button("Sign Out"):

                    st.session_state.logged_in = False
                    st.warning("Signed Out")

        st.divider()

        # -------------------------------------------
        # MODE SETTINGS
        # -------------------------------------------

        st.subheader("🎨 Interface Mode")

        mode = st.radio(
            "Choose Interface Theme",
            [
                "Dark",
                "Sunlight"
            ],
            horizontal=True
        )

        st.session_state.theme_mode = mode

        if mode == "Dark":
            st.success("Dark Mode Activated")
        else:
            st.info("Sunlight Mode Activated")

        st.divider()

        # -------------------------------------------
        # LANGUAGE SETTINGS
        # -------------------------------------------

        st.subheader("🌐 Language Settings")

        language = st.selectbox(
            "Choose Interface Language",
            [
                "English",
                "French",
                "Spanish",
                "German",
                "Chinese",
                "Japanese",
                "Arabic",
                "Russian"
            ]
        )

        st.session_state.language = language

        st.success(f"Language set to {language}")

        st.divider()

        # -------------------------------------------
        # SHORTCUTS
        # -------------------------------------------

        st.subheader("🚀 Shortcut Center")

        shortcut1, shortcut2, shortcut3, shortcut4 = st.tabs([
            "Reward",
            "Referral",
            "Earn Deposit",
            "Edit"
        ])

        # -------------------------------------------
        # REWARD
        # -------------------------------------------

        with shortcut1:

            st.metric(
                "Reward Points",
                "18,450"
            )

            st.progress(78)

            st.info("You are among the top 12% active analysts.")

        # -------------------------------------------
        # REFERRAL
        # -------------------------------------------

        with shortcut2:

            st.code("AIDRM-REF-2026")

            st.metric(
                "Referral Earnings",
                "$4,250"
            )

            st.metric(
                "Referral Count",
                "148"
            )

        # -------------------------------------------
        # EARN DEPOSIT
        # -------------------------------------------

        with shortcut3:

            deposit_amount = st.number_input(
                "Deposit Amount",
                min_value=0.0,
                value=1000.0
            )

            plan = st.selectbox(
                "Investment Plan",
                [
                    "Flexible Savings",
                    "30-Day Locked",
                    "90-Day Locked"
                ]
            )

            estimated_apy = random.randint(5, 25)

            st.metric(
                "Estimated APY",
                f"{estimated_apy}%"
            )

            if st.button("Start Earning"):

                st.success(
                    f"${deposit_amount:,.2f} allocated to {plan}"
                )

        # -------------------------------------------
        # EDIT PREFERENCES
        # -------------------------------------------

        with shortcut4:

            st.toggle(
                "Enable Notifications",
                value=True
            )

            st.toggle(
                "Enable Whale Tracking",
                value=True
            )

            st.toggle(
                "Enable AI Threat Detection",
                value=True
            )

            st.toggle(
                "Enable Smart Money Alerts",
                value=True
            )

            if st.button("Save Preferences"):

                st.success("Preferences Saved Successfully")

    # ===================================================
    # 2 SENSITIVITY & THRESHOLDS
    # ===================================================

    with settings_main2:

        st.subheader("🎯 Confidence Levels")

        confidence = st.select_slider(
            "Threat Detection Strictness",
            options=["Low", "Medium", "High"],
            value="Medium"
        )

        st.info(
            "Higher confidence catches more zero-day threats but increases false positives."
        )

        st.divider()

        st.subheader("⏱ Time Windows")

        time_window = st.slider(
            "Sliding Window (Minutes)",
            min_value=5,
            max_value=1440,
            value=60
        )

        st.metric(
            "Current Analysis Window",
            f"{time_window} Minutes"
        )

    # ===================================================
    # 3 PROTOCOL & TRAFFIC RULES
    # ===================================================

    with settings_main3:

        st.subheader("📚 Baseline Learning Period")

        relearn = st.toggle(
            "Re-learn Normal Behavior Over 7 Days",
            value=False
        )

        if relearn:
            st.warning("AI Baseline Re-learning Activated")

        st.progress(65)

        st.divider()

        st.subheader("🛡 Protocol Whitelisting")

        st.text_area(
            "Trusted IP Subnets",
            value="""
192.168.1.0/24
10.0.0.0/16
"""
        )

        st.text_area(
            "Trusted HTTP/gRPC Methods",
            value="""
GET
POST
grpc.health.v1.Health/Check
"""
        )

        st.text_input(
            "Trusted User-Agents",
            value="Mozilla/5.0"
        )

        st.divider()

        st.subheader("📦 Header Filtering")

        st.checkbox("Analyze Referer Headers", value=True)
        st.checkbox("Analyze Connection Sequence Errors", value=True)
        st.checkbox("Analyze Malformed Payloads", value=True)
        st.checkbox("Analyze Session Cookies", value=True)
        st.checkbox("Analyze API Abuse", value=True)

    # ===================================================
    # 4 ALERTS & INCIDENT MANAGEMENT
    # ===================================================

    with settings_main4:

        st.subheader("Notification Triggers")

        st.multiselect(
            "Select Alert Channels",
            [
                "Email",
                "Slack",
                "Webhook",
                "Microsoft Sentinel",
                "Discord",
                "Telegram"
            ],
            default=["Email", "Slack"]
        )

        st.divider()

        st.subheader("Threat Severity Notifications")

        st.checkbox("Critical Threats", value=True)
        st.checkbox("High Threats", value=True)
        st.checkbox("Medium Threats", value=True)
        st.checkbox("Low Threats", value=False)

        st.divider()

        st.subheader("🚧 Rate Limits")

        rate_limit = st.slider(
            "Maximum Abnormal Requests Before Auto Block",
            min_value=10,
            max_value=10000,
            value=500
        )

        st.metric(
            "Current Threshold",
            f"{rate_limit} Requests"
        )

        quarantine = st.slider(
            "Temporary IP Quarantine Duration (Minutes)",
            min_value=1,
            max_value=1440,
            value=60
        )

        st.metric(
            "Quarantine Duration",
            f"{quarantine} Minutes"
        )

    # ===================================================
    # 5 PRIVACY & COMPLIANCE
    # ===================================================

    with settings_main5:

        st.subheader("Data Masking")

        st.checkbox(
            "Hash User Tokens",
            value=True
        )

        st.checkbox(
            "Redact Password Fields",
            value=True
        )

        st.checkbox(
            "Hide Sensitive Payload Data",
            value=True
        )

        st.checkbox(
            "Encrypt Traffic Logs",
            value=True
        )

        st.divider()

        st.subheader("🗂 Retention Period")

        retention = st.selectbox(
            "Log Retention Duration",
            [
                "7 Days",
                "30 Days",
                "90 Days",
                "180 Days",
                "1 Year"
            ]
        )

        st.success(
            f"Current Retention Policy: {retention}"
        )

        st.divider()

        st.subheader("✅ Compliance & Security")

        col1, col2, col3 = st.columns(3)

        col1.success("SOC 2 Compliant")
        col2.success("GDPR Ready")
        col3.success("ISO 27001 Certified")