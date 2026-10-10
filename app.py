"""
app.py
======
Český, Evropský & US Makroekonomický Dashboard ve Streamlit.
Přehledná, vysoce responzivní a modulární aplikace pro komplexní vizualizaci
a srovnání makroekonomických indikátorů České republiky, Evropské unie (Eurozóny)
a Spojených států amerických a světových akciových trhů (PX, Euro Stoxx 50, S&P 500, NASDAQ).
"""

from __future__ import annotations

import io
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Zajištění přítomnosti kořenového adresáře v sys.path pro Streamlit Cloud / Linux
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

PARENT_DIR = ROOT_DIR.parent
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

try:
    import data_loader as dl_module
except (ImportError, ModuleNotFoundError):
    try:
        import macro_dashboard.data_loader as dl_module
    except (ImportError, ModuleNotFoundError):
        import Macro_Dashboard.data_loader as dl_module

DataLoader = getattr(dl_module, "DataLoader")
INDICATORS = getattr(dl_module, "INDICATORS")
CZ_INDICATORS = getattr(dl_module, "CZ_INDICATORS", {k: v for k, v in INDICATORS.items() if v.region == "CZ"})
EU_INDICATORS = getattr(dl_module, "EU_INDICATORS", {k: v for k, v in INDICATORS.items() if v.region == "EU"})
US_INDICATORS = getattr(dl_module, "US_INDICATORS", {k: v for k, v in INDICATORS.items() if v.region == "US"})
MARKET_INDICATORS = getattr(dl_module, "MARKET_INDICATORS", {k: v for k, v in INDICATORS.items() if v.category == "Akciové trhy"})
get_cached_macro_data = getattr(dl_module, "get_cached_macro_data")

try:
    import glossary_data as glossary_module
except (ImportError, ModuleNotFoundError):
    try:
        import macro_dashboard.glossary_data as glossary_module
    except (ImportError, ModuleNotFoundError):
        import Macro_Dashboard.glossary_data as glossary_module

render_glossary_view = getattr(glossary_module, "render_glossary_view", None)
GLOSSARY_ITEMS = getattr(glossary_module, "GLOSSARY_ITEMS", [])

# =============================================================================
# 1. KONFIGURACE STRÁNKY A STYLING
# =============================================================================

st.set_page_config(
    page_title="Makro & Tržní Monitor | ČR, EU & USA Terminal",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="auto",  # Mobilně přívětivé: automatické sbalení na telefonu
)

CUSTOM_CSS = """
<style>
    /* Základní rozvržení a moderní typografie */
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Inter", Helvetica, Arial, sans-serif !important;
    }
    
    .main .block-container {
        padding-top: 1.0rem;
        padding-bottom: 2.5rem;
        max-width: 1440px;
    }

    /* Mobilní optimalizace paddingu a prvků */
    @media (max-width: 768px) {
        .main .block-container {
            padding-top: 0.6rem !important;
            padding-left: 0.6rem !important;
            padding-right: 0.6rem !important;
            padding-bottom: 2.0rem !important;
        }
        div[data-testid="stMetric"] {
            padding: 7px 9px !important;
        }
        div[data-testid="stMetricValue"] {
            font-size: 1.08rem !important;
        }
        .sa-header-container {
            padding: 12px 14px !important;
        }
        .sa-header-title {
            font-size: 1.20rem !important;
        }
    }
    
    /* VZHLED METRICKÝCH SUMMARY BOXŮ (KOMPAKTNÍ PÍSMO, VÝRAZNĚJŠÍ A ČISTÉ PROVEDENÍ) */
    div[data-testid="stMetric"] {
        background-color: #f1f5f9 !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px !important;
        padding: 9px 13px !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
        transition: all 0.2s ease !important;
    }
    div[data-testid="stMetric"]:hover {
        background-color: #e2e8f0 !important;
        border-color: #94a3b8 !important;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08) !important;
    }
    div[data-testid="stMetricLabel"] p {
        font-size: 0.76rem !important;
        font-weight: 700 !important;
        color: #475569 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.04em !important;
        margin-bottom: 2px !important;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.22rem !important;
        font-weight: 800 !important;
        color: #0f172a !important;
        font-variant-numeric: tabular-nums !important;
    }
    div[data-testid="stMetricDelta"] {
        font-size: 0.78rem !important;
        font-weight: 600 !important;
    }
    
    /* Status štítky (Stock Analysis live tags) */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 0.74rem;
        font-weight: 600;
        letter-spacing: 0.03em;
        text-transform: uppercase;
    }
    .status-live {
        background-color: #ecfdf5;
        color: #065f46;
        border: 1px solid #a7f3d0;
    }
    .status-partial {
        background-color: #fffbeb;
        color: #92400e;
        border: 1px solid #fde68a;
    }
    .status-fallback {
        background-color: #fff7ed;
        color: #9a3412;
        border: 1px solid #ffedd5;
    }
    
    /* Záhlaví sekcí */
    .section-header {
        font-size: 1.15rem;
        font-weight: 700;
        color: #0f172a;
        margin-top: 0.8rem;
        margin-bottom: 0.4rem;
        display: flex;
        align-items: center;
        gap: 8px;
        border-left: 3px solid #2563eb;
        padding-left: 10px;
    }

    /* ZÁLOŽKY (TABS): AGREGOVANÉ KATEGORIE S TMAVŠÍM PODBARVENÍM A TMAVOMODRÝM PÍSMEM */
    div[data-baseweb="tab-list"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
        gap: 6px 8px !important;
        background-color: #e2e8f0 !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 10px !important;
        padding: 6px 9px !important;
        margin-bottom: 1.1rem !important;
        overflow-x: auto !important;
        white-space: nowrap !important;
        scrollbar-width: thin !important;
        -webkit-overflow-scrolling: touch !important;
        width: 100% !important;
    }

    div[data-baseweb="tab-highlight"],
    div[data-baseweb="tab-border"] {
        display: none !important;
    }

    button[data-baseweb="tab"] {
        background-color: #f1f5f9 !important;
        color: #1e3a8a !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 7px !important;
        padding: 7px 16px !important;
        font-size: 0.88rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.01em !important;
        transition: all 0.15s ease !important;
        white-space: nowrap !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04) !important;
        cursor: pointer !important;
        height: auto !important;
    }

    button[data-baseweb="tab"] p,
    button[data-baseweb="tab"] span {
        color: #1e3a8a !important;
        font-weight: 700 !important;
    }

    button[data-baseweb="tab"]:hover {
        background-color: #dbeafe !important;
        color: #172554 !important;
        border-color: #93c5fd !important;
    }

    button[data-baseweb="tab"]:hover p,
    button[data-baseweb="tab"]:hover span {
        color: #172554 !important;
    }

    button[data-baseweb="tab"][aria-selected="true"],
    button[data-baseweb="tab"][data-selected="true"] {
        background-color: #1e3a8a !important;
        color: #ffffff !important;
        font-weight: 800 !important;
        border-color: #1e3a8a !important;
        border-radius: 7px !important;
        box-shadow: 0 2px 6px rgba(30, 58, 138, 0.28) !important;
    }

    button[data-baseweb="tab"][aria-selected="true"] p,
    button[data-baseweb="tab"][aria-selected="true"] span,
    button[data-baseweb="tab"][data-selected="true"] p,
    button[data-baseweb="tab"][data-selected="true"] span {
        color: #ffffff !important;
        font-weight: 800 !important;
    }

    /* KARTA AKTUÁLNÍHO FINANČNÍHO ZPRAVODAJSTVÍ A KONTEXTU */
    .macro-news-card {
        background: #f8fafc;
        border: 1px solid #cbd5e1;
        border-left: 4px solid #2563eb;
        border-radius: 8px;
        padding: 13px 17px;
        margin-top: 10px;
        margin-bottom: 18px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
    }
    .macro-news-top {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        justify-content: space-between;
        gap: 8px;
        margin-bottom: 7px;
    }
    .macro-news-tag {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: #eff6ff;
        border: 1px solid #bfdbfe;
        color: #1d4ed8;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }
    .news-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background-color: #2563eb;
        display: inline-block;
    }
    .macro-news-meta {
        font-size: 0.77rem;
        color: #64748b;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .macro-news-headline {
        font-size: 1.00rem;
        font-weight: 750;
        color: #0f172a;
        line-height: 1.35;
        margin-bottom: 9px;
    }
    .macro-news-content {
        display: flex;
        flex-direction: column;
        gap: 6px;
        font-size: 0.84rem;
        line-height: 1.45;
    }
    .news-section-item {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 8px 12px;
    }
    .news-label {
        font-weight: 700;
        color: #1e293b;
        margin-right: 6px;
    }
    .news-text {
        color: #475569;
    }

    /* TOP HEADER & KEY STATS PANELS */
    .sa-header-container {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 14px;
    }
    .sa-header-top {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 12px;
        border-bottom: 1px solid #f1f5f9;
        padding-bottom: 12px;
        margin-bottom: 12px;
    }
    .sa-header-title-box {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .sa-header-title {
        font-size: 1.45rem;
        font-weight: 700;
        color: #0f172a;
        margin: 0;
        letter-spacing: -0.02em;
    }
    .sa-ticker-badge {
        background: #f1f5f9;
        color: #334155;
        font-size: 0.75rem;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 4px;
        border: 1px solid #e2e8f0;
        letter-spacing: 0.05em;
    }
    .sa-header-meta {
        font-size: 0.78rem;
        color: #64748b;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .sa-live-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        background-color: #10b981;
        border-radius: 50%;
    }
    .sa-hero-strip {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 16px 24px;
    }
    .sa-hero-item {
        display: flex;
        flex-direction: column;
    }
    .sa-hero-label {
        font-size: 0.74rem;
        color: #64748b;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }
    .sa-hero-val-row {
        display: flex;
        align-items: baseline;
        gap: 6px;
    }
    .sa-hero-val {
        font-size: 1.15rem;
        font-weight: 700;
        color: #0f172a;
        font-variant-numeric: tabular-nums;
    }
    .sa-hero-change-pos {
        font-size: 0.80rem;
        font-weight: 600;
        color: #16a34a;
    }
    .sa-hero-change-neg {
        font-size: 0.80rem;
        font-weight: 600;
        color: #dc2626;
    }
    .sa-hero-change-neutral {
        font-size: 0.80rem;
        font-weight: 500;
        color: #64748b;
    }

    /* Dvou-sloupcová tabulka klíčových metrik (Key Metrics Widget) */
    .sa-stats-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 14px 18px;
        margin-top: 6px;
        margin-bottom: 12px;
    }
    .sa-stats-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0 32px;
    }
    @media (max-width: 768px) {
        .sa-stats-grid {
            grid-template-columns: 1fr;
        }
    }
    .sa-stat-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 7px 0;
        border-bottom: 1px solid #e2e8f0;
        font-size: 0.86rem;
    }
    .sa-stat-row:last-child {
        border-bottom: none;
    }
    .sa-stat-label {
        color: #475569;
        font-weight: 500;
    }
    .sa-stat-val {
        color: #0f172a;
        font-weight: 700;
        font-variant-numeric: tabular-nums;
        display: flex;
        align-items: center;
        gap: 6px;
    }

    /* Postranní panel (Sidebar) */
    section[data-testid="stSidebar"] {
        background-color: #f8fafc !important;
        border-right: 1px solid #e5e7eb !important;
    }
    section[data-testid="stSidebar"] .block-container {
        padding-top: 1.2rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    .sidebar-brand-card {
        background: #0f172a;
        border-radius: 8px;
        padding: 12px 14px;
        color: #ffffff;
        margin-bottom: 16px;
        border: 1px solid #1e293b;
    }
    .sidebar-brand-title {
        font-size: 1.05rem;
        font-weight: 700;
        color: #ffffff;
        margin: 0;
    }
    .sidebar-brand-sub {
        font-size: 0.72rem;
        color: #94a3b8;
        margin-top: 2px;
    }
    .sidebar-brand-top {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 4px;
    }
    .sidebar-brand-badge {
        background: #2563eb;
        color: #ffffff;
        font-size: 0.65rem;
        font-weight: 700;
        padding: 2px 6px;
        border-radius: 4px;
        letter-spacing: 0.05em;
    }
    .sidebar-brand-version {
        font-size: 0.70rem;
        color: #64748b;
        font-weight: 600;
    }
    .sidebar-section-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-top: 14px;
        margin-bottom: 6px;
    }
    .sidebar-section-title {
        font-size: 0.78rem;
        font-weight: 700;
        color: #475569;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    .sidebar-section-badge {
        font-size: 0.68rem;
        font-weight: 600;
        color: #64748b;
        background: #e2e8f0;
        padding: 1px 6px;
        border-radius: 3px;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# =============================================================================
# 2. POMOCNÉ FUNKCE
# =============================================================================

def safe_metric(row: Any, col: str, default: float = 0.0) -> float:
    """Bezpečně extrahuje číselnou hodnotu z řádku dataframe."""
    try:
        val = row.get(col, default)
        if pd.isna(val) or val is None:
            return default
        return float(val)
    except Exception:
        return default


def format_delta_str(curr: Optional[float], prev: Optional[float], unit: str = "p.b.") -> str:
    """Spočítá a zformátuje deltu mezi současnou a předchozí hodnotou."""
    if curr is None or prev is None or pd.isna(curr) or pd.isna(prev):
        return "–"
    delta = curr - prev
    sign = "+" if delta > 0 else ""
    return f"{sign}{delta:,.2f} {unit}".replace(".", ",")


def render_plotly_chart(fig: go.Figure, key: Optional[str] = None) -> None:
    """Vykreslí Plotly graf s plnou kompatibilitou napříč verzemi a mobilní optimalizací."""
    chart_config = {
        "scrollZoom": False,
        "displayModeBar": False,
        "responsive": True
    }
    try:
        st.plotly_chart(fig, width="stretch", key=key, config=chart_config)
    except (TypeError, ValueError):
        st.plotly_chart(fig, use_container_width=True, key=key, config=chart_config)


def render_dataframe(df_to_render: pd.DataFrame) -> None:
    """Vykreslí tabulku s plnou kompatibilitou napříč verzemi Streamlit."""
    try:
        st.dataframe(df_to_render, width="stretch", hide_index=True)
    except (TypeError, ValueError):
        st.dataframe(df_to_render, use_container_width=True, hide_index=True)


# =============================================================================
# 3. HLAVNÍ ZÁHLAVÍ & PŘEPÍNAČ EKONOMIKY (ČR vs. EU vs. USA)
# =============================================================================

st.markdown(
    """
    <div style="display: flex; align-items: center; gap: 10px; padding: 2px 0 6px 0;">
        <span style="font-size: 1.55rem;">🏛️</span>
        <div>
            <div style="font-size: 1.25rem; font-weight: 850; color: #0F172A; letter-spacing: -0.02em;">MAKROEKONOMICKÝ & TRŽNÍ MONITOR</div>
            <div style="font-size: 0.74rem; font-weight: 600; color: #64748B; text-transform: uppercase;">Institucionální analýza &bull; ČNB &bull; ECB &bull; Fed &bull; Akciové indexy &bull; Výnosové křivky</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

economy_options = ["🇨🇿 Česká republika", "🇪🇺 Evropská unie", "🇺🇸 Spojené státy"]
if hasattr(st, "segmented_control"):
    selected_economy = st.segmented_control(
        "Zvolte ekonomiku:",
        options=economy_options,
        default="🇨🇿 Česká republika",
        key="macro_region_top_switch",
        label_visibility="collapsed"
    )
    if not selected_economy:
        selected_economy = "🇨🇿 Česká republika"
else:
    selected_economy = st.radio(
        "Zvolte ekonomiku:",
        options=economy_options,
        index=0,
        key="macro_region_top_switch",
        horizontal=True,
        label_visibility="collapsed"
    )

is_cz = (selected_economy == "🇨🇿 Česká republika")
is_eu = (selected_economy == "🇪🇺 Evropská unie")
is_us = (selected_economy == "🇺🇸 Spojené státy")


# =============================================================================
# 4. SIDEBAR: OVLÁDACÍ PRVKY A FILTRY
# =============================================================================

if is_cz:
    sidebar_badge = "ČR MACRO"
    sidebar_sub = "ČNB &bull; Eurostat &bull; PRIBOR &bull; Křivka"
    region_label = "ČR"
elif is_eu:
    sidebar_badge = "EU MACRO"
    sidebar_sub = "ECB &bull; Eurostat &bull; EURIBOR &bull; Bunds &bull; €STR"
    region_label = "EU"
else:
    sidebar_badge = "USA MACRO"
    sidebar_sub = "Fed &bull; BLS &bull; BEA &bull; Treasury &bull; DXY"
    region_label = "USA"

st.sidebar.markdown(
    f"""
    <div class="sidebar-brand-card">
        <div class="sidebar-brand-top">
            <span class="sidebar-brand-badge">{sidebar_badge}</span>
            <span class="sidebar-brand-version">TERMINAL</span>
        </div>
        <div class="sidebar-brand-title">Nastavení a filtry ({region_label})</div>
        <div class="sidebar-brand-sub">{sidebar_sub}</div>
    </div>
    """,
    unsafe_allow_html=True
)

if "current_view" not in st.session_state:
    st.session_state["current_view"] = "monitor"

st.sidebar.markdown(
    """
    <div class="sidebar-section-header">
        <span class="sidebar-section-title">🧭 Hlavní navigace</span>
        <span class="sidebar-section-badge">Menu</span>
    </div>
    """,
    unsafe_allow_html=True
)

col_sb_nav1, col_sb_nav2 = st.sidebar.columns(2)
is_in_glossary = (st.session_state.get("current_view") == "glossary")
if col_sb_nav1.button("📊 Monitor", use_container_width=True, type="secondary" if is_in_glossary else "primary", key="sb_nav_btn_monitor"):
    st.session_state["current_view"] = "monitor"
    st.rerun()
if col_sb_nav2.button("📖 Glosář pojmů", use_container_width=True, type="primary" if is_in_glossary else "secondary", help="Otevře srozumitelný výkladový glosář všech makroekonomických pojmů a ukazatelů pro laiky i investory.", key="sb_nav_btn_glossary"):
    st.session_state["current_view"] = "glossary"
    st.rerun()

# 1. Výběr časového horizontu
st.sidebar.markdown(
    """
    <div class="sidebar-section-header">
        <span class="sidebar-section-title">📅 Časový horizont</span>
        <span class="sidebar-section-badge">Období</span>
    </div>
    """,
    unsafe_allow_html=True
)

horizon_options = ["1 rok", "3 roky", "5 let", "Od 2015", "Vlastní"]

if hasattr(st.sidebar, "segmented_control"):
    horizon_option = st.sidebar.segmented_control(
        "Zvolte období:",
        options=horizon_options,
        default="5 let",
        key="sb_horizon_seg",
        help="Rychlé předvolby nebo vlastní nastavení kalendářního rozpětí dat.",
        label_visibility="collapsed"
    )
    if not horizon_option:
        horizon_option = "5 let"
else:
    horizon_option = st.sidebar.radio(
        "Zvolte období:",
        options=horizon_options,
        index=2,
        key="sb_horizon_rad",
        horizontal=True,
        help="Rychlé předvolby nebo vlastní nastavení kalendářního rozpětí dat.",
        label_visibility="collapsed"
    )

all_month_dates = pd.date_range("2015-01-01", datetime.now(), freq="MS")
month_options = [d.strftime("%m/%Y") for d in all_month_dates]

start_filter_date = pd.to_datetime("2021-01-01")
end_filter_date = pd.to_datetime(datetime.now().strftime("%Y-%m-%d"))

if horizon_option in ("Vlastní", "Vlastní rozsah"):
    st.sidebar.markdown(
        """
        <div style="background: #f1f5f9; border: 1px dashed #cbd5e1; border-radius: 8px; padding: 10px; margin-top: 6px; margin-bottom: 10px;">
            <div style="font-size: 0.74rem; font-weight: 700; color: #475569; text-transform: uppercase; margin-bottom: 6px;">📅 Vlastní časové rozpětí:</div>
        """,
        unsafe_allow_html=True
    )
    col_c1, col_c2 = st.sidebar.columns(2)
    default_start_idx = max(0, len(month_options) - 36)
    selected_start_str = col_c1.selectbox("Od (měsíc/rok):", options=month_options, index=default_start_idx, key="sb_custom_from")
    selected_end_str = col_c2.selectbox("Do (měsíc/rok):", options=month_options, index=len(month_options) - 1, key="sb_custom_to")
    
    start_filter_date = pd.to_datetime(selected_start_str, format="%m/%Y")
    end_filter_date = pd.to_datetime(selected_end_str, format="%m/%Y") + pd.offsets.MonthEnd(0)
    
    if start_filter_date > end_filter_date:
        start_filter_date, end_filter_date = end_filter_date, start_filter_date
        st.sidebar.warning("Datum 'Od' bylo po 'Do', rozsah byl automaticky upraven.")
    st.sidebar.markdown("</div>", unsafe_allow_html=True)

# 2. Přepínač frekvence
st.sidebar.markdown(
    """
    <div class="sidebar-section-header">
        <span class="sidebar-section-title">⏱️ Frekvence dat</span>
        <span class="sidebar-section-badge">Agregace</span>
    </div>
    """,
    unsafe_allow_html=True
)

freq_options = ["Měsíční", "Kvartální"]

if hasattr(st.sidebar, "segmented_control"):
    freq_choice = st.sidebar.segmented_control(
        "Agregace časové řady:",
        options=freq_options,
        default="Měsíční",
        format_func=lambda x: "📅 Měsíční (M)" if x == "Měsíční" else "📊 Kvartální (Q)",
        key="sb_freq_seg",
        help="Měsíční data poskytují vyšší detail sazeb a inflace, kvartální data přesně odpovídají periodicitě HDP a dluhu.",
        label_visibility="collapsed"
    )
    if not freq_choice:
        freq_choice = "Měsíční"
else:
    freq_choice = st.sidebar.radio(
        "Agregace časové řady:",
        options=freq_options,
        index=0,
        format_func=lambda x: "📅 Měsíční (M)" if x == "Měsíční" else "📊 Kvartální (Q)",
        key="sb_freq_rad",
        horizontal=True,
        help="Měsíční data poskytují vyšší detail sazeb a inflace, kvartální data přesně odpovídají periodicitě HDP a dluhu.",
        label_visibility="collapsed"
    )

frequency_code = "M" if freq_choice.startswith("Měsíční") else "Q"

# 3. Všechny ukazatele jsou vždy aktivní a zobrazeny
if is_cz:
    selected_indicators = list(CZ_INDICATORS.keys())
elif is_eu:
    selected_indicators = list(EU_INDICATORS.keys())
else:
    selected_indicators = list(US_INDICATORS.keys())

st.sidebar.markdown(
    """
    <div style="background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 8px; padding: 10px 12px; margin-top: 14px; margin-bottom: 6px;">
        <div style="font-size: 0.74rem; font-weight: 750; color: #1e293b; text-transform: uppercase; margin-bottom: 3px;">✅ Všechny ukazatele aktivní</div>
        <div style="font-size: 0.73rem; color: #64748b; line-height: 1.35;">Všechny časové řady jsou trvale zapnuty. Podrobný metodický přehled a zdroje dat naleznete v nové záložce <strong>📖 Seznam ukazatelů & Zdroje</strong>.</div>
    </div>
    """,
    unsafe_allow_html=True
)

# 4. Zdroj dat & Nastavení API
st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    <div class="sidebar-section-header">
        <span class="sidebar-section-title">⚙️ Zdroj dat & Server</span>
        <span class="sidebar-section-badge">API</span>
    </div>
    """,
    unsafe_allow_html=True
)

force_fallback = st.sidebar.checkbox(
    "Vynutit Fallback data (Offline režim)",
    value=False,
    help="Přepne dashboard na interní historický model bez volání externích REST API."
)

fred_key_input = st.sidebar.text_input(
    "Volitelný FRED API Klíč:",
    value="",
    type="password",
    help="Pokud máte klíč k Federal Reserve Bank of St. Louis (FRED), můžete jej zde zadat."
)

if st.sidebar.button("🔄 Obnovit data (Vymazat cache)", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

refresh_meta_slot = st.sidebar.empty()


# =============================================================================
# 5. NAČTENÍ DAT S CACHOVÁNÍM
# =============================================================================

with st.spinner("Načítám data z ČNB, Eurostatu, Yahoo Finance a U.S. Treasury..."):
    df_raw, status_info, df_daily_fx = get_cached_macro_data(
        frequency=frequency_code,
        fred_api_key=fred_key_input,
        force_fallback=force_fallback
    )

if df_raw.empty:
    st.error("Nepodařilo se načíst žádná data. Zkuste aktivovat záložní fallback model v levém panelu.")
    st.stop()

# Zobrazení data aktuálnosti dat přímo pod tlačítkem obnovení
latest_macro_date = df_raw["date"].max()
latest_macro_str = latest_macro_date.strftime("%d. %m. %Y") if (pd.notna(latest_macro_date) and hasattr(latest_macro_date, "strftime")) else "Aktuální"
latest_fx_date = df_daily_fx["date"].max() if not df_daily_fx.empty else latest_macro_date
latest_fx_str = latest_fx_date.strftime("%d. %m. %Y") if (pd.notna(latest_fx_date) and hasattr(latest_fx_date, "strftime")) else latest_macro_str
fetch_time_str = status_info.get("fetch_timestamp", datetime.now().strftime("%d.%m.%Y %H:%M"))

refresh_meta_slot.markdown(
    f"""
    <div style="background: #ffffff; border: 1px solid #cbd5e1; border-radius: 7px; padding: 8px 11px; margin-top: 6px; margin-bottom: 8px; box-shadow: 0 1px 2px rgba(0,0,0,0.03);">
        <div style="font-size: 0.73rem; font-weight: 750; color: #1e3a8a; text-transform: uppercase; margin-bottom: 2px;">
            📅 Data aktuální k: <strong>{latest_macro_str}</strong>
        </div>
        <div style="font-size: 0.70rem; color: #475569; line-height: 1.35;">
            Denní kurzy & trhy: <strong>{latest_fx_str}</strong><br/>
            Poslední stažení: {fetch_time_str}
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# Status v sidebaru
mode = status_info.get("mode", "LIVE")
badge_class = "status-live" if mode == "LIVE" else ("status-partial" if mode == "PARTIAL_LIVE" else "status-fallback")
st.sidebar.markdown(
    f'<div class="status-badge {badge_class}">{status_info.get("status_badge", "Data načtena")}</div>',
    unsafe_allow_html=True
)

with st.sidebar.expander("ℹ️ Stav jednotlivých API endpointů"):
    st.write(f"**Čas aktualizace:** {status_info.get('fetch_timestamp')}")
    st.write(f"**Režim:** `{mode}`")
    st.markdown("---")
    for ep, status_text in status_info.get("endpoints", {}).items():
        st.write(f"- **{ep}**: {status_text}")
    if status_info.get("errors"):
        st.caption("Chybové hlášky: " + "; ".join(status_info.get("errors", [])))


# =============================================================================
# 6. FILTRACE PODLE VYBRANÉHO HORIZONTU
# =============================================================================

max_date = df_raw["date"].max()
min_date = df_raw["date"].min()

if horizon_option == "1 rok":
    start_filter_date = max_date - pd.DateOffset(years=1)
    end_filter_date = max_date
elif horizon_option == "3 roky":
    start_filter_date = max_date - pd.DateOffset(years=3)
    end_filter_date = max_date
elif horizon_option == "5 let":
    start_filter_date = max_date - pd.DateOffset(years=5)
    end_filter_date = max_date
elif horizon_option in ("Od 2015", "Celá historie (od 2015)", "Celá historie", "MAX"):
    start_filter_date = min_date
    end_filter_date = max_date

df = df_raw[(df_raw["date"] >= start_filter_date) & (df_raw["date"] <= end_filter_date)].copy().sort_values("date").reset_index(drop=True)
df_daily_fx_filtered = df_daily_fx[(df_daily_fx["date"] >= start_filter_date) & (df_daily_fx["date"] <= end_filter_date)].copy().sort_values("date").reset_index(drop=True)

if df.empty:
    st.warning("Pro vybraný časový filtr nejsou k dispozici žádné záznamy. Zvolte prosím širší rozsah.")
    st.stop()


# -----------------------------------------------------------------------------
# POKUD JE VYBRÁN GLOSÁŘ POJMŮ (GLOSSARY VIEW)
# -----------------------------------------------------------------------------
if st.session_state.get("current_view") == "glossary":
    col_back_top, _ = st.columns([1.8, 3.2])
    with col_back_top:
        if st.button("⬅️ Zpět na Makroekonomický Monitor", type="primary", use_container_width=True, key="btn_back_to_mon_top"):
            st.session_state["current_view"] = "monitor"
            st.rerun()

    if render_glossary_view:
        render_glossary_view()
    else:
        st.info("Výkladový glosář se načítá...")

    st.markdown("---")
    col_back_bot, _ = st.columns([1.8, 3.2])
    with col_back_bot:
        if st.button("⬅️ Zpět na Makroekonomický Monitor", type="primary", use_container_width=True, key="btn_back_to_mon_bottom"):
            st.session_state["current_view"] = "monitor"
            st.rerun()
    st.stop()


# =============================================================================
# 7. HLAVNÍ PLOCHA DASHBOARDU: ZÁHLAVÍ & TOP SUMMARY
# =============================================================================

last_row = df.iloc[-1]
prev_row = df.iloc[-2] if len(df) > 1 else last_row

date_str = last_row.get("date").strftime("%d. %m. %Y") if hasattr(last_row.get("date"), "strftime") else "Aktuální"

# --- Hodnoty pro ČR ---
repo_curr = safe_metric(last_row, "repo_rate", 3.75)
repo_prev = safe_metric(prev_row, "repo_rate", repo_curr)
repo_delta = repo_curr - repo_prev
disc_curr = safe_metric(last_row, "discount_rate", 2.75)
lomb_curr = safe_metric(last_row, "lombard_rate", 4.75)
prib3m_curr = safe_metric(last_row, "pribor_3m", 3.90)

cpi_cz_curr = safe_metric(last_row, "cpi_yoy", 2.3)
cpi_cz_prev = safe_metric(prev_row, "cpi_yoy", cpi_cz_curr)
cpi_cz_delta = cpi_cz_curr - cpi_cz_prev
core_cpi_cz_curr = safe_metric(last_row, "cpi_core_yoy", 2.4)

gdp_cz_curr = safe_metric(last_row, "gdp_growth_real", 1.2)
gdp_cz_prev = safe_metric(prev_row, "gdp_growth_real", gdp_cz_curr)
gdp_cz_delta = gdp_cz_curr - gdp_cz_prev
nom_cz_val = safe_metric(last_row, "gdp_nominal_czk_bn", 1950.0)

retail_cz_curr = safe_metric(last_row, "retail_sales_yoy", 2.6)
ind_cz_curr = safe_metric(last_row, "industrial_prod_yoy", 1.2)

une_cz_curr = safe_metric(last_row, "unemployment_rate", 2.8)
une_cz_prev = safe_metric(prev_row, "unemployment_rate", une_cz_curr)
une_cz_delta = une_cz_curr - une_cz_prev

eur_cz_curr = safe_metric(last_row, "eur_czk", 25.10)
usd_cz_curr = safe_metric(last_row, "usd_czk", 23.20)
pln_cz_curr = safe_metric(last_row, "pln_czk", 5.85)
gbp_cz_curr = safe_metric(last_row, "gbp_czk", 30.10)

czgb10_curr = safe_metric(last_row, "czgb_10y", 4.10)
czgb2_curr = safe_metric(last_row, "czgb_2y", 3.70)
cz_spread_curr = safe_metric(last_row, "czgb_spread_10y_2y", round(czgb10_curr - czgb2_curr, 2))
irs10_curr = safe_metric(last_row, "irs_10y", 3.95)
debt_cz_pct = safe_metric(last_row, "public_debt_gdp_pct", 44.0)
deficit_cz_curr = safe_metric(last_row, "budget_deficit_czk_bn", -65.0)
px_curr = safe_metric(last_row, "px_index", 1680.0)

# --- Hodnoty pro EU (Eurozóna) ---
ecb_dep_curr = safe_metric(last_row, "ecb_deposit_rate", 3.00)
ecb_dep_prev = safe_metric(prev_row, "ecb_deposit_rate", ecb_dep_curr)
ecb_dep_delta = ecb_dep_curr - ecb_dep_prev
ecb_refi_curr = safe_metric(last_row, "ecb_refi_rate", 3.15)
ecb_lend_curr = safe_metric(last_row, "ecb_lending_rate", 3.40)
euribor3m_curr = safe_metric(last_row, "euribor_3m", 2.95)
estr_curr = safe_metric(last_row, "estr_rate", 2.92)

cpi_eu_curr = safe_metric(last_row, "eu_cpi_yoy", 2.2)
cpi_eu_prev = safe_metric(prev_row, "eu_cpi_yoy", cpi_eu_curr)
cpi_eu_delta = cpi_eu_curr - cpi_eu_prev
core_cpi_eu_curr = safe_metric(last_row, "eu_core_cpi_yoy", 2.7)

gdp_eu_curr = safe_metric(last_row, "eu_gdp_growth_real", 0.9)
gdp_eu_prev = safe_metric(prev_row, "eu_gdp_growth_real", gdp_eu_curr)
gdp_eu_delta = gdp_eu_curr - gdp_eu_prev
nom_eu_val = safe_metric(last_row, "eu_gdp_nominal_eur_bn", 3800.0)

retail_eu_curr = safe_metric(last_row, "eu_retail_sales_yoy", 1.4)
ind_eu_curr = safe_metric(last_row, "eu_industrial_prod_yoy", -0.8)

une_eu_curr = safe_metric(last_row, "eu_unemployment_rate", 5.9)
une_eu_prev = safe_metric(prev_row, "eu_unemployment_rate", une_eu_curr)
une_eu_delta = une_eu_curr - une_eu_prev

eur_usd_curr = safe_metric(last_row, "eur_usd", 1.0850)
eur_pln_curr = safe_metric(last_row, "eur_pln", 4.30)
eur_gbp_curr = safe_metric(last_row, "eur_gbp", 0.85)

bund10_curr = safe_metric(last_row, "bund_10y", 2.35)
bund2_curr = safe_metric(last_row, "bund_2y", 2.20)
bund_spread_curr = safe_metric(last_row, "bund_spread_10y_2y", round(bund10_curr - bund2_curr, 2))
debt_eu_pct = safe_metric(last_row, "eu_public_debt_gdp_pct", 88.6)
debt_eu_nom = safe_metric(last_row, "eu_public_debt_eur_bn", 13200.0)
deficit_eu_curr = safe_metric(last_row, "eu_budget_deficit_eur_bn", -110.0)
stoxx50_curr = safe_metric(last_row, "stoxx50_index", 5150.0)

# --- Hodnoty pro USA ---
fed_upper_curr = safe_metric(last_row, "fed_funds_upper", 4.50)
fed_upper_prev = safe_metric(prev_row, "fed_funds_upper", fed_upper_curr)
fed_upper_delta = fed_upper_curr - fed_upper_prev
fed_lower_curr = safe_metric(last_row, "fed_funds_lower", 4.25)
fed_effr_curr = safe_metric(last_row, "fed_effective_rate", 4.33)
sofr_curr = safe_metric(last_row, "sofr_rate", 4.31)
us3m_curr = safe_metric(last_row, "us_3m", 4.40)

cpi_us_curr = safe_metric(last_row, "us_cpi_yoy", 2.6)
cpi_us_prev = safe_metric(prev_row, "us_cpi_yoy", cpi_us_curr)
cpi_us_delta = cpi_us_curr - cpi_us_prev
core_cpi_us_curr = safe_metric(last_row, "us_core_cpi_yoy", 3.2)

gdp_us_curr = safe_metric(last_row, "us_gdp_growth_real", 2.8)
gdp_us_prev = safe_metric(prev_row, "us_gdp_growth_real", gdp_us_curr)
gdp_us_delta = gdp_us_curr - gdp_us_prev
nom_us_val = safe_metric(last_row, "us_gdp_nominal_usd_bn", 28500.0)

retail_us_curr = safe_metric(last_row, "us_retail_sales_yoy", 3.1)
ind_us_curr = safe_metric(last_row, "us_industrial_prod_yoy", 1.5)

une_us_curr = safe_metric(last_row, "us_unemployment_rate", 4.1)
une_us_prev = safe_metric(prev_row, "us_unemployment_rate", une_us_curr)
une_us_delta = une_us_curr - une_us_prev

dxy_curr = safe_metric(last_row, "dxy_index", 101.50)
dxy_prev = safe_metric(prev_row, "dxy_index", dxy_curr)
dxy_delta = dxy_curr - dxy_prev
usd_jpy_curr = safe_metric(last_row, "usd_jpy", 152.40)
gbp_usd_curr = safe_metric(last_row, "gbp_usd", 1.28)
usd_pln_curr = safe_metric(last_row, "usd_pln", 3.95)

us10_curr = safe_metric(last_row, "us_10y", 4.30)
us2_curr = safe_metric(last_row, "us_2y", 4.10)
us_spread_curr = safe_metric(last_row, "us_spread_10y_2y", round(us10_curr - us2_curr, 2))
debt_us_pct = safe_metric(last_row, "us_public_debt_gdp_pct", 123.5)
debt_us_nom = safe_metric(last_row, "us_public_debt_usd_bn", 35500.0)
deficit_us_curr = safe_metric(last_row, "us_budget_deficit_usd_bn", -450.0)
sp500_curr = safe_metric(last_row, "sp500_index", 6100.0)
nasdaq_curr = safe_metric(last_row, "nasdaq_index", 20100.0)

# Předstihové & Sentiment metriky
cz_pmi_curr = safe_metric(last_row, "cz_pmi_manufacturing", 48.5)
cz_pmi_prev = safe_metric(prev_row, "cz_pmi_manufacturing", cz_pmi_curr)
cz_conf_curr = safe_metric(last_row, "cz_confidence_composite", 96.0)
cz_conf_prev = safe_metric(prev_row, "cz_confidence_composite", cz_conf_curr)

eu_ifo_curr = safe_metric(last_row, "eu_ifo_business_climate", 89.5)
eu_ifo_prev = safe_metric(prev_row, "eu_ifo_business_climate", eu_ifo_curr)
eu_pmi_curr = safe_metric(last_row, "eu_composite_pmi", 51.0)
eu_pmi_prev = safe_metric(prev_row, "eu_composite_pmi", eu_pmi_curr)

us_ism_mfg_curr = safe_metric(last_row, "us_ism_manufacturing", 50.5)
us_ism_mfg_prev = safe_metric(prev_row, "us_ism_manufacturing", us_ism_mfg_curr)
us_ism_srv_curr = safe_metric(last_row, "us_ism_services", 53.6)
us_ism_srv_prev = safe_metric(prev_row, "us_ism_services", us_ism_srv_curr)
us_mich_curr = safe_metric(last_row, "us_michigan_sentiment", 78.5)
us_mich_prev = safe_metric(prev_row, "us_michigan_sentiment", us_mich_curr)

# Trh práce & Mzdy metriky
cz_nom_wage_curr = safe_metric(last_row, "cz_nominal_wage_yoy", 7.2)
cz_nom_wage_prev = safe_metric(prev_row, "cz_nominal_wage_yoy", cz_nom_wage_curr)
cz_real_wage_curr = safe_metric(last_row, "cz_real_wage_yoy", 4.5)
cz_real_wage_prev = safe_metric(prev_row, "cz_real_wage_yoy", cz_real_wage_curr)

eu_wages_curr = safe_metric(last_row, "eu_negotiated_wages_yoy", 4.2)
eu_wages_prev = safe_metric(prev_row, "eu_negotiated_wages_yoy", eu_wages_curr)

us_earn_curr = safe_metric(last_row, "us_hourly_earnings_yoy", 3.9)
us_earn_prev = safe_metric(prev_row, "us_hourly_earnings_yoy", us_earn_curr)

# Bankovní sektor & Měnová zásoba metriky
cz_mort_rate_curr = safe_metric(last_row, "cz_mortgage_rate", 4.85)
cz_mort_rate_prev = safe_metric(prev_row, "cz_mortgage_rate", cz_mort_rate_curr)
cz_mort_vol_curr = safe_metric(last_row, "cz_mortgage_volume_czk_bn", 21.5)
cz_corp_loans_curr = safe_metric(last_row, "cz_corporate_loans_yoy", 6.8)
cz_corp_loans_prev = safe_metric(prev_row, "cz_corporate_loans_yoy", cz_corp_loans_curr)
cz_m2_curr = safe_metric(last_row, "cz_m2_growth_yoy", 6.8)
cz_m2_prev = safe_metric(prev_row, "cz_m2_growth_yoy", cz_m2_curr)

# Vnější rovnováha metriky
cz_ca_curr = safe_metric(last_row, "cz_current_account_gdp_pct", 1.5)
cz_trade_bal_curr = safe_metric(last_row, "cz_trade_balance_czk_bn", 17.5)
cz_trade_bal_prev = safe_metric(prev_row, "cz_trade_balance_czk_bn", cz_trade_bal_curr)

# Kreditní a rizikové spready metriky
czgb_bund_sp_curr = safe_metric(last_row, "czgb_bund_spread_10y", round((czgb10_curr - bund10_curr) * 100, 1))
cz_asw_curr = safe_metric(last_row, "cz_asw_10y_spread", round((czgb10_curr - irs10_curr) * 100, 1))
eu_btp_sp_curr = safe_metric(last_row, "eu_btp_bund_spread", 132.0)
eu_btp_sp_prev = safe_metric(prev_row, "eu_btp_bund_spread", eu_btp_sp_curr)

# Tržní sentiment & riziko (VIX)
vix_curr = safe_metric(last_row, "vix_index", 15.2)
vix_prev = safe_metric(prev_row, "vix_index", vix_curr)

# Poslední denní FX data
last_daily_fx = df_daily_fx_filtered.iloc[-1] if not df_daily_fx_filtered.empty else last_row
prev_daily_fx = df_daily_fx_filtered.iloc[-2] if len(df_daily_fx_filtered) > 1 else last_daily_fx

daily_eur_czk = safe_metric(last_daily_fx, "eur_czk", eur_cz_curr)
daily_usd_czk = safe_metric(last_daily_fx, "usd_czk", usd_cz_curr)
daily_pln_czk = safe_metric(last_daily_fx, "pln_czk", pln_cz_curr)
daily_gbp_czk = safe_metric(last_daily_fx, "gbp_czk", gbp_cz_curr)

daily_eur_usd = safe_metric(last_daily_fx, "eur_usd", eur_usd_curr)
daily_eur_pln = safe_metric(last_daily_fx, "eur_pln", eur_pln_curr)
daily_eur_gbp = safe_metric(last_daily_fx, "eur_gbp", eur_gbp_curr)

daily_dxy = safe_metric(last_daily_fx, "dxy_index", dxy_curr)
daily_gbp_usd = safe_metric(last_daily_fx, "gbp_usd", gbp_usd_curr)
daily_usd_jpy = safe_metric(last_daily_fx, "usd_jpy", usd_jpy_curr)
daily_usd_pln = safe_metric(last_daily_fx, "usd_pln", usd_pln_curr)


# -----------------------------------------------------------------------------
# ZOBRAZENÍ TOP HERO BOXU PODLE ZVOLENÉ ZEMĚ
# -----------------------------------------------------------------------------

if is_cz:
    st.markdown(
        f"""
        <div class="sa-header-container">
            <div class="sa-header-top">
                <div class="sa-header-title-box">
                    <h1 class="sa-header-title">🇨🇿 Česká republika</h1>
                    <span class="sa-ticker-badge">CZ MACRO & MARKET MONITOR</span>
                </div>
                <div class="sa-header-meta">
                    <span class="sa-live-dot"></span>
                    <span><strong>TRHY AKTIVNÍ</strong> &bull; ČNB &bull; BCPP &bull; Eurostat &bull; {date_str}</span>
                </div>
            </div>
            <div class="sa-hero-strip">
                <div class="sa-hero-item">
                    <span class="sa-hero-label">2T Repo ČNB</span>
                    <div class="sa-hero-val-row">
                        <span class="sa-hero-val">{repo_curr:.2f} %</span>
                        <span class="sa-hero-change-neutral">{repo_delta:+.2f} p.b.</span>
                    </div>
                </div>
                <div class="sa-hero-item">
                    <span class="sa-hero-label">PRIBOR 3M</span>
                    <div class="sa-hero-val-row">
                        <span class="sa-hero-val">{prib3m_curr:.2f} %</span>
                        <span class="sa-hero-change-neutral">Mezibankovní</span>
                    </div>
                </div>
                <div class="sa-hero-item">
                    <span class="sa-hero-label">Inflace ČR (CPI)</span>
                    <div class="sa-hero-val-row">
                        <span class="sa-hero-val">{cpi_cz_curr:.1f} %</span>
                        <span class="sa-hero-change-pos">Cíl 2.0 %</span>
                    </div>
                </div>
                <div class="sa-hero-item">
                    <span class="sa-hero-label">Index PX (Praha)</span>
                    <div class="sa-hero-val-row">
                        <span class="sa-hero-val">{px_curr:,.0f} b.</span>
                        <span class="sa-hero-change-pos">BCPP</span>
                    </div>
                </div>
                <div class="sa-hero-item">
                    <span class="sa-hero-label">Reálný růst HDP</span>
                    <div class="sa-hero-val-row">
                        <span class="sa-hero-val">{gdp_cz_curr:+.1f} %</span>
                        <span class="{'sa-hero-change-pos' if gdp_cz_delta >= 0 else 'sa-hero-change-neg'}">{gdp_cz_delta:+.1f} p.b.</span>
                    </div>
                </div>
                <div class="sa-hero-item">
                    <span class="sa-hero-label">Kurz EUR/CZK</span>
                    <div class="sa-hero-val-row">
                        <span class="sa-hero-val">{daily_eur_czk:.2f} Kč</span>
                        <span class="sa-hero-change-neutral">ČNB fix</span>
                    </div>
                </div>
                <div class="sa-hero-item">
                    <span class="sa-hero-label">10Y CZGB Výnos</span>
                    <div class="sa-hero-val-row">
                        <span class="sa-hero-val">{czgb10_curr:.2f} %</span>
                        <span class="sa-hero-change-neutral">Benchmark</span>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

elif is_eu:
    st.markdown(
        f"""
        <div class="sa-header-container">
            <div class="sa-header-top">
                <div class="sa-header-title-box">
                    <h1 class="sa-header-title">🇪🇺 Evropská unie / Eurozóna</h1>
                    <span class="sa-ticker-badge">EU MACRO & MARKET MONITOR</span>
                </div>
                <div class="sa-header-meta">
                    <span class="sa-live-dot"></span>
                    <span><strong>TRHY AKTIVNÍ</strong> &bull; ECB &bull; Eurostat &bull; STOXX &bull; {date_str}</span>
                </div>
            </div>
            <div class="sa-hero-strip">
                <div class="sa-hero-item">
                    <span class="sa-hero-label">Depozitní sazba ECB</span>
                    <div class="sa-hero-val-row">
                        <span class="sa-hero-val">{ecb_dep_curr:.2f} %</span>
                        <span class="sa-hero-change-neutral">{ecb_dep_delta:+.2f} p.b.</span>
                    </div>
                </div>
                <div class="sa-hero-item">
                    <span class="sa-hero-label">EURIBOR 3M</span>
                    <div class="sa-hero-val-row">
                        <span class="sa-hero-val">{euribor3m_curr:.2f} %</span>
                        <span class="sa-hero-change-neutral">Benchmark</span>
                    </div>
                </div>
                <div class="sa-hero-item">
                    <span class="sa-hero-label">Inflace Eurozóny (HICP)</span>
                    <div class="sa-hero-val-row">
                        <span class="sa-hero-val">{cpi_eu_curr:.1f} %</span>
                        <span class="sa-hero-change-pos">Cíl 2.0 %</span>
                    </div>
                </div>
                <div class="sa-hero-item">
                    <span class="sa-hero-label">Euro Stoxx 50</span>
                    <div class="sa-hero-val-row">
                        <span class="sa-hero-val">{stoxx50_curr:,.0f} b.</span>
                        <span class="sa-hero-change-pos">EU Blue-chips</span>
                    </div>
                </div>
                <div class="sa-hero-item">
                    <span class="sa-hero-label">Reálný růst HDP EU</span>
                    <div class="sa-hero-val-row">
                        <span class="sa-hero-val">{gdp_eu_curr:+.1f} %</span>
                        <span class="{'sa-hero-change-pos' if gdp_eu_delta >= 0 else 'sa-hero-change-neg'}">{gdp_eu_delta:+.1f} p.b.</span>
                    </div>
                </div>
                <div class="sa-hero-item">
                    <span class="sa-hero-label">Kurz EUR/USD</span>
                    <div class="sa-hero-val-row">
                        <span class="sa-hero-val">{daily_eur_usd:.4f} $</span>
                        <span class="sa-hero-change-neutral">Denní FX</span>
                    </div>
                </div>
                <div class="sa-hero-item">
                    <span class="sa-hero-label">10Y Německý Bund</span>
                    <div class="sa-hero-val-row">
                        <span class="sa-hero-val">{bund10_curr:.2f} %</span>
                        <span class="sa-hero-change-neutral">Bezrizikový</span>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

else:
    st.markdown(
        f"""
        <div class="sa-header-container">
            <div class="sa-header-top">
                <div class="sa-header-title-box">
                    <h1 class="sa-header-title">🇺🇸 Spojené státy americké</h1>
                    <span class="sa-ticker-badge">US MACRO & MARKET MONITOR</span>
                </div>
                <div class="sa-header-meta">
                    <span class="sa-live-dot"></span>
                    <span><strong>TRHY AKTIVNÍ</strong> &bull; Fed &bull; NYSE &bull; NASDAQ &bull; {date_str}</span>
                </div>
            </div>
            <div class="sa-hero-strip">
                <div class="sa-hero-item">
                    <span class="sa-hero-label">Fed Funds Target</span>
                    <div class="sa-hero-val-row">
                        <span class="sa-hero-val">{fed_upper_curr:.2f} %</span>
                        <span class="sa-hero-change-neutral">{fed_upper_delta:+.2f} p.b.</span>
                    </div>
                </div>
                <div class="sa-hero-item">
                    <span class="sa-hero-label">SOFR</span>
                    <div class="sa-hero-val-row">
                        <span class="sa-hero-val">{sofr_curr:.2f} %</span>
                        <span class="sa-hero-change-neutral">Peněžní trh</span>
                    </div>
                </div>
                <div class="sa-hero-item">
                    <span class="sa-hero-label">Inflace USA (CPI)</span>
                    <div class="sa-hero-val-row">
                        <span class="sa-hero-val">{cpi_us_curr:.1f} %</span>
                        <span class="sa-hero-change-pos">Cíl 2.0 %</span>
                    </div>
                </div>
                <div class="sa-hero-item">
                    <span class="sa-hero-label">S&P 500</span>
                    <div class="sa-hero-val-row">
                        <span class="sa-hero-val">{sp500_curr:,.0f} b.</span>
                        <span class="sa-hero-change-pos">Index USA</span>
                    </div>
                </div>
                <div class="sa-hero-item">
                    <span class="sa-hero-label">Dolarový index DXY</span>
                    <div class="sa-hero-val-row">
                        <span class="sa-hero-val">{daily_dxy:.2f}</span>
                        <span class="sa-hero-change-neutral">Koš měn</span>
                    </div>
                </div>
                <div class="sa-hero-item">
                    <span class="sa-hero-label">10Y US Treasury</span>
                    <div class="sa-hero-val-row">
                        <span class="sa-hero-val">{us10_curr:.2f} %</span>
                        <span class="sa-hero-change-neutral">Benchmark</span>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# -----------------------------------------------------------------------------
# SKRYTÁ DETAILNÍ TABULKA INDIKÁTORŮ (MOŽNOST ZOBRAZIT PŘES EXPANDER)
# -----------------------------------------------------------------------------

with st.expander("📊 Zobrazit detailní přehled indikátorů a metrik", expanded=False):
    if is_cz:
        st.markdown(
            f"""
            <div class="sa-stats-card">
                <div class="sa-stats-grid">
                    <div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">2T Repo sazba ČNB</span>
                            <span class="sa-stat-val">{repo_curr:.2f} % <span class="sa-hero-change-neutral">{repo_delta:+.2f}</span></span>
                        </div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">Diskontní sazba (spodní koridor)</span>
                            <span class="sa-stat-val">{disc_curr:.2f} %</span>
                        </div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">Lombardní sazba (horní koridor)</span>
                            <span class="sa-stat-val">{lomb_curr:.2f} %</span>
                        </div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">PRIBOR 3M (referenční sazba)</span>
                            <span class="sa-stat-val">{prib3m_curr:.2f} %</span>
                        </div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">Meziroční inflace CPI</span>
                            <span class="sa-stat-val">{cpi_cz_curr:.1f} % <span class="sa-hero-change-pos">Cíl 2.0 %</span></span>
                        </div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">Jádrová inflace ČR (Core CPI)</span>
                            <span class="sa-stat-val">{core_cpi_cz_curr:.1f} %</span>
                        </div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">Maloobchodní tržby (Spotřeba YoY)</span>
                            <span class="sa-stat-val">{retail_cz_curr:+.1f} %</span>
                        </div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">Průmyslová produkce (YoY)</span>
                            <span class="sa-stat-val">{ind_cz_curr:+.1f} %</span>
                        </div>
                    </div>
                    <div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">Reálný růst HDP (YoY)</span>
                            <span class="sa-stat-val">{gdp_cz_curr:+.1f} % <span class="sa-hero-change-pos">{gdp_cz_delta:+.1f}</span></span>
                        </div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">Míra nezaměstnanosti (ILO)</span>
                            <span class="sa-stat-val">{une_cz_curr:.1f} % <span class="sa-hero-change-pos">Nejnižší v EU</span></span>
                        </div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">EUR/CZK &bull; USD/CZK (denní)</span>
                            <span class="sa-stat-val">{daily_eur_czk:.2f} &bull; {daily_usd_czk:.2f} Kč</span>
                        </div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">PLN/CZK &bull; GBP/CZK (denní)</span>
                            <span class="sa-stat-val">{daily_pln_czk:.2f} &bull; {daily_gbp_czk:.2f} Kč</span>
                        </div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">Výnos 10Y CZGB (státní dluhopis)</span>
                            <span class="sa-stat-val">{czgb10_curr:.2f} %</span>
                        </div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">Sklon křivky CZGB (10Y − 2Y)</span>
                            <span class="sa-stat-val">{cz_spread_curr * 100:+.0f} bps <span class="{'sa-hero-change-pos' if cz_spread_curr >= 0 else 'sa-hero-change-neg'}">{'Normální' if cz_spread_curr >= 0 else 'Inverze'}</span></span>
                        </div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">Veřejný dluh ČR (% HDP)</span>
                            <span class="sa-stat-val">{debt_cz_pct:.1f} % <span class="sa-hero-change-pos">&lt; 60 % limit</span></span>
                        </div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">Kvartální saldo rozpočtu</span>
                            <span class="sa-stat-val">{deficit_cz_curr:,.1f} mld. Kč</span>
                        </div>
                    </div>
                    <div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">PMI v průmyslu ČR (S&P Global)</span>
                            <span class="sa-stat-val">{cz_pmi_curr:.1f} b. <span class="{'sa-hero-change-pos' if cz_pmi_curr >= 50 else 'sa-hero-change-neg'}">{'Expanze' if cz_pmi_curr >= 50 else 'Útlum'}</span></span>
                        </div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">Důvěra konjunktury (ČSÚ)</span>
                            <span class="sa-stat-val">{cz_conf_curr:.1f} b.</span>
                        </div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">Průměrná hrubá mzda (YoY)</span>
                            <span class="sa-stat-val">{cz_nom_wage_curr:+.1f} %</span>
                        </div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">Průměrná reálná mzda (YoY)</span>
                            <span class="sa-stat-val">{cz_real_wage_curr:+.1f} %</span>
                        </div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">Nové hypotéky (sazba & objem)</span>
                            <span class="sa-stat-val">{cz_mort_rate_curr:.2f} % &bull; {cz_mort_vol_curr:.1f} mld. Kč</span>
                        </div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">Korporátní úvěry & M2 (YoY)</span>
                            <span class="sa-stat-val">{cz_corp_loans_curr:+.1f} % &bull; {cz_m2_curr:+.1f} %</span>
                        </div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">Běžný účet k HDP & Obchod ČSÚ</span>
                            <span class="sa-stat-val">{cz_ca_curr:+.1f} % &bull; {cz_trade_bal_curr:+.1f} mld. Kč</span>
                        </div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">Spread CZGB vs. Bund & ASW 10Y</span>
                            <span class="sa-stat-val">{czgb_bund_sp_curr:+.0f} bps &bull; {cz_asw_curr:+.0f} bps</span>
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    elif is_eu:
        st.markdown(
            f"""
            <div class="sa-stats-card">
                <div class="sa-stats-grid">
                    <div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">Depozitní sazba ECB</span>
                            <span class="sa-stat-val">{ecb_dep_curr:.2f} % <span class="sa-hero-change-neutral">{ecb_dep_delta:+.2f}</span></span>
                        </div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">Refinanční operace (MRO)</span>
                            <span class="sa-stat-val">{ecb_refi_curr:.2f} %</span>
                        </div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">Mezní zápůjční sazba ECB</span>
                            <span class="sa-stat-val">{ecb_lend_curr:.2f} %</span>
                        </div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">EURIBOR 3M &bull; €STR</span>
                            <span class="sa-stat-val">{euribor3m_curr:.2f} % &bull; {estr_curr:.2f} %</span>
                        </div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">Harmonizovaná inflace (HICP)</span>
                            <span class="sa-stat-val">{cpi_eu_curr:.1f} % <span class="sa-hero-change-pos">Cíl 2.0 %</span></span>
                        </div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">Jádrová inflace EU (Core HICP)</span>
                            <span class="sa-stat-val">{core_cpi_eu_curr:.1f} %</span>
                        </div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">Maloobchodní tržby EU (Spotřeba YoY)</span>
                            <span class="sa-stat-val">{retail_eu_curr:+.1f} %</span>
                        </div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">Průmyslová produkce EU (YoY)</span>
                            <span class="sa-stat-val">{ind_eu_curr:+.1f} %</span>
                        </div>
                    </div>
                    <div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">Reálný růst HDP Eurozóny (YoY)</span>
                            <span class="sa-stat-val">{gdp_eu_curr:+.1f} % <span class="sa-hero-change-pos">{gdp_eu_delta:+.1f}</span></span>
                        </div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">Míra nezaměstnanosti v EU</span>
                            <span class="sa-stat-val">{une_eu_curr:.1f} %</span>
                        </div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">EUR/USD &bull; EUR/CZK</span>
                            <span class="sa-stat-val">{daily_eur_usd:.4f} $ &bull; {daily_eur_czk:.2f} Kč</span>
                        </div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">EUR/PLN &bull; EUR/GBP</span>
                            <span class="sa-stat-val">{daily_eur_pln:.4f} zł &bull; {daily_eur_gbp:.4f} £</span>
                        </div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">Výnos 10Y Německý Bund</span>
                            <span class="sa-stat-val">{bund10_curr:.2f} %</span>
                        </div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">Sklon Bund křivky (10Y − 2Y)</span>
                            <span class="sa-stat-val">{bund_spread_curr * 100:+.0f} bps <span class="{'sa-hero-change-pos' if bund_spread_curr >= 0 else 'sa-hero-change-neg'}">{'Normální' if bund_spread_curr >= 0 else 'Inverze'}</span></span>
                        </div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">Veřejný dluh Eurozóny k HDP</span>
                            <span class="sa-stat-val">{debt_eu_pct:.1f} % <span class="sa-hero-change-neutral">{debt_eu_nom:,.0f} mld. €</span></span>
                        </div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">Kvartální deficit vládních institucí</span>
                            <span class="sa-stat-val">{deficit_eu_curr:,.0f} mld. EUR</span>
                        </div>
                    </div>
                    <div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">Composite PMI Eurozóny</span>
                            <span class="sa-stat-val">{eu_pmi_curr:.1f} b. <span class="{'sa-hero-change-pos' if eu_pmi_curr >= 50 else 'sa-hero-change-neg'}">{'Expanze' if eu_pmi_curr >= 50 else 'Útlum'}</span></span>
                        </div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">Německý Ifo index klimatu</span>
                            <span class="sa-stat-val">{eu_ifo_curr:.1f} b.</span>
                        </div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">Sjednané mzdy Eurozóna (ECB YoY)</span>
                            <span class="sa-stat-val">{eu_wages_curr:+.1f} %</span>
                        </div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">Rizikový spread 10Y BTP - Bund</span>
                            <span class="sa-stat-val">{eu_btp_sp_curr:+.0f} bps</span>
                        </div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">Euro Stoxx 50 (Index)</span>
                            <span class="sa-stat-val">{stoxx50_curr:,.0f} b.</span>
                        </div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">Běžný účet Eurozóny (% HDP)</span>
                            <span class="sa-stat-val">+2.8 %</span>
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    else:
        st.markdown(
            f"""
            <div class="sa-stats-card">
                <div class="sa-stats-grid">
                    <div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">Fed Funds Target (horní limit)</span>
                            <span class="sa-stat-val">{fed_upper_curr:.2f} % <span class="sa-hero-change-neutral">{fed_upper_delta:+.2f}</span></span>
                        </div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">Fed Funds Target (dolní limit)</span>
                            <span class="sa-stat-val">{fed_lower_curr:.2f} %</span>
                        </div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">Efektivní sazba EFFR</span>
                            <span class="sa-stat-val">{fed_effr_curr:.2f} %</span>
                        </div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">SOFR &bull; 3M T-Bill</span>
                            <span class="sa-stat-val">{sofr_curr:.2f} % &bull; {us3m_curr:.2f} %</span>
                        </div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">Spotřebitelská inflace (CPI Headline)</span>
                            <span class="sa-stat-val">{cpi_us_curr:.1f} % <span class="sa-hero-change-pos">Cíl 2.0 %</span></span>
                        </div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">Jádrová inflace USA (Core CPI)</span>
                            <span class="sa-stat-val">{core_cpi_us_curr:.1f} %</span>
                        </div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">Maloobchodní tržby USA (Spotřeba YoY)</span>
                            <span class="sa-stat-val">{retail_us_curr:+.1f} %</span>
                        </div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">Průmyslová produkce USA (YoY)</span>
                            <span class="sa-stat-val">{ind_us_curr:+.1f} %</span>
                        </div>
                    </div>
                    <div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">Reálný růst HDP USA (YoY)</span>
                            <span class="sa-stat-val">{gdp_us_curr:+.1f} % <span class="sa-hero-change-pos">{gdp_us_delta:+.1f}</span></span>
                        </div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">Míra nezaměstnanosti (U-3)</span>
                            <span class="sa-stat-val">{une_us_curr:.1f} %</span>
                        </div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">Dolarový index DXY &bull; EUR/USD</span>
                            <span class="sa-stat-val">{daily_dxy:.2f} b. &bull; {daily_eur_usd:.4f} $</span>
                        </div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">GBP/USD &bull; USD/PLN &bull; USD/JPY</span>
                            <span class="sa-stat-val">{daily_gbp_usd:.4f} &bull; {daily_usd_pln:.2f} &bull; {daily_usd_jpy:.1f}</span>
                        </div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">Výnos 10Y US Treasury (Benchmark)</span>
                            <span class="sa-stat-val">{us10_curr:.2f} %</span>
                        </div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">Sklon US křivky (10Y − 2Y)</span>
                            <span class="sa-stat-val">{us_spread_curr * 100:+.0f} bps <span class="{'sa-hero-change-pos' if us_spread_curr >= 0 else 'sa-hero-change-neg'}">{'Normální' if us_spread_curr >= 0 else 'Inverze'}</span></span>
                        </div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">Federální dluh USA k HDP</span>
                            <span class="sa-stat-val">{debt_us_pct:.1f} % <span class="sa-hero-change-neutral">{debt_us_nom:,.0f} mld. $</span></span>
                        </div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">Kvartální federální deficit</span>
                            <span class="sa-stat-val">{deficit_us_curr:,.0f} mld. USD</span>
                        </div>
                    </div>
                    <div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">ISM Manufacturing PMI</span>
                            <span class="sa-stat-val">{us_ism_mfg_curr:.1f} b. <span class="{'sa-hero-change-pos' if us_ism_mfg_curr >= 50 else 'sa-hero-change-neg'}">{'Expanze' if us_ism_mfg_curr >= 50 else 'Útlum'}</span></span>
                        </div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">ISM Services PMI</span>
                            <span class="sa-stat-val">{us_ism_srv_curr:.1f} b.</span>
                        </div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">Spotřebitelský sentiment Michigan</span>
                            <span class="sa-stat-val">{us_mich_curr:.1f} b.</span>
                        </div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">Průměrná hodinová mzda (YoY)</span>
                            <span class="sa-stat-val">{us_earn_curr:+.1f} %</span>
                        </div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">Index volatility VIX (Tržní riziko)</span>
                            <span class="sa-stat-val">{vix_curr:.2f} b.</span>
                        </div>
                        <div class="sa-stat-row">
                            <span class="sa-stat-label">S&P 500 &bull; NASDAQ Composite</span>
                            <span class="sa-stat-val">{sp500_curr:,.0f} &bull; {nasdaq_curr:,.0f} b.</span>
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )


# =============================================================================
# 8. GENERÁTORY GRAFŮ (PLOTLY BUILDERS)
# =============================================================================

# --- A. SAZBY ---
def build_rates_chart(dframe: pd.DataFrame, indicators: List[str]) -> go.Figure:
    """Graf měnové politiky ČNB (úrokový koridor) a PRIBOR sazeb."""
    fig = go.Figure()
    if "lombard_rate" in indicators and "lombard_rate" in dframe.columns:
        fig.add_trace(go.Scatter(
            x=dframe["date"], y=dframe["lombard_rate"], mode="lines",
            name="Lombardní sazba ČNB (horní mez)",
            line=dict(color="rgba(148, 163, 184, 0.7)", width=1.5, dash="dash"),
            hoverinfo="x+y+name"
        ))
    if "discount_rate" in indicators and "discount_rate" in dframe.columns:
        fig.add_trace(go.Scatter(
            x=dframe["date"], y=dframe["discount_rate"], mode="lines",
            name="Diskontní sazba ČNB (dolní mez)",
            line=dict(color="rgba(148, 163, 184, 0.7)", width=1.5, dash="dash"),
            fill="tonexty" if ("lombard_rate" in indicators and "lombard_rate" in dframe.columns) else None,
            fillcolor="rgba(226, 232, 240, 0.35)", hoverinfo="x+y+name"
        ))
    if "repo_rate" in indicators and "repo_rate" in dframe.columns:
        fig.add_trace(go.Scatter(
            x=dframe["date"], y=dframe["repo_rate"], mode="lines",
            name="2T Repo sazba ČNB (klíčová)",
            line=dict(color="#1D4ED8", width=3.5, shape="hv"),
            hovertemplate="<b>2T Repo sazba</b>: %{y:.2f} %<extra></extra>"
        ))
    pribor_colors = {"pribor_1m": ("#06B6D4", "PRIBOR 1M", 1.5), "pribor_3m": ("#0D9488", "PRIBOR 3M (benchmark)", 2.4), "pribor_6m": ("#047857", "PRIBOR 6M", 1.5)}
    for p_col, (p_color, p_name, p_width) in pribor_colors.items():
        if p_col in indicators and p_col in dframe.columns:
            fig.add_trace(go.Scatter(
                x=dframe["date"], y=dframe[p_col], mode="lines", name=p_name,
                line=dict(color=p_color, width=p_width, dash="dot" if p_col != "pribor_3m" else "solid"),
                hovertemplate=f"<b>{p_name}</b>: %{{y:.2f}} %<extra></extra>"
            ))
    fig.update_layout(
        height=430, hovermode="x unified", margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor="rgba(255, 255, 255, 0.85)"),
        xaxis=dict(title="", showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(title="Úrokové sazby (%)", title_font=dict(color="#1D4ED8"), tickfont=dict(color="#1D4ED8"), showgrid=True, gridcolor="#f1f5f9", ticksuffix=" %"),
        plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF"
    )
    return fig


def build_eu_rates_chart(dframe: pd.DataFrame, indicators: List[str]) -> go.Figure:
    """Graf měnové politiky ECB a sazeb EURIBOR / €STR."""
    fig = go.Figure()
    if "ecb_lending_rate" in indicators and "ecb_lending_rate" in dframe.columns:
        fig.add_trace(go.Scatter(
            x=dframe["date"], y=dframe["ecb_lending_rate"], mode="lines",
            name="Mezní zápůjční sazba ECB (strop)",
            line=dict(color="rgba(148, 163, 184, 0.7)", width=1.5, dash="dash"),
            hoverinfo="x+y+name"
        ))
    if "ecb_deposit_rate" in indicators and "ecb_deposit_rate" in dframe.columns:
        fig.add_trace(go.Scatter(
            x=dframe["date"], y=dframe["ecb_deposit_rate"], mode="lines",
            name="Depozitní sazba ECB (hlavní kotva)",
            line=dict(color="#1D4ED8", width=3.5, shape="hv"),
            fill="tonexty" if ("ecb_lending_rate" in indicators and "ecb_lending_rate" in dframe.columns) else None,
            fillcolor="rgba(226, 232, 240, 0.35)", hovertemplate="<b>ECB Depo sazba</b>: %{y:.2f} %<extra></extra>"
        ))
    if "ecb_refi_rate" in indicators and "ecb_refi_rate" in dframe.columns:
        fig.add_trace(go.Scatter(
            x=dframe["date"], y=dframe["ecb_refi_rate"], mode="lines",
            name="Refinanční sazba ECB (MRO)",
            line=dict(color="#4F46E5", width=2.0, dash="dash"),
            hovertemplate="<b>ECB Refi (MRO)</b>: %{y:.2f} %<extra></extra>"
        ))
    if "euribor_3m" in indicators and "euribor_3m" in dframe.columns:
        fig.add_trace(go.Scatter(
            x=dframe["date"], y=dframe["euribor_3m"], mode="lines", name="EURIBOR 3M (benchmark)",
            line=dict(color="#0D9488", width=2.5), hovertemplate="<b>EURIBOR 3M</b>: %{y:.2f} %<extra></extra>"
        ))
    if "estr_rate" in indicators and "estr_rate" in dframe.columns:
        fig.add_trace(go.Scatter(
            x=dframe["date"], y=dframe["estr_rate"], mode="lines", name="€STR (Overnight ECB)",
            line=dict(color="#D97706", width=1.8, dash="dot"), hovertemplate="<b>€STR</b>: %{y:.2f} %<extra></extra>"
        ))
    fig.update_layout(
        height=430, hovermode="x unified", margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor="rgba(255, 255, 255, 0.85)"),
        xaxis=dict(title="", showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(title="Úrokové sazby EUR (%)", title_font=dict(color="#1D4ED8"), tickfont=dict(color="#1D4ED8"), showgrid=True, gridcolor="#f1f5f9", ticksuffix=" %"),
        plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF"
    )
    return fig


def build_us_rates_chart(dframe: pd.DataFrame, indicators: List[str]) -> go.Figure:
    """Graf měnové politiky Fedu a peněžního trhu USA."""
    fig = go.Figure()
    if "fed_funds_upper" in indicators and "fed_funds_upper" in dframe.columns:
        fig.add_trace(go.Scatter(
            x=dframe["date"], y=dframe["fed_funds_upper"], mode="lines",
            name="Fed Funds Target (horní limit)",
            line=dict(color="rgba(148, 163, 184, 0.8)", width=1.5, dash="dash"),
            hoverinfo="x+y+name"
        ))
    if "fed_funds_lower" in indicators and "fed_funds_lower" in dframe.columns:
        fig.add_trace(go.Scatter(
            x=dframe["date"], y=dframe["fed_funds_lower"], mode="lines",
            name="Fed Funds Target (dolní limit)",
            line=dict(color="rgba(148, 163, 184, 0.8)", width=1.5, dash="dash"),
            fill="tonexty" if ("fed_funds_upper" in indicators and "fed_funds_upper" in dframe.columns) else None,
            fillcolor="rgba(226, 232, 240, 0.35)", hoverinfo="x+y+name"
        ))
    if "fed_effective_rate" in indicators and "fed_effective_rate" in dframe.columns:
        fig.add_trace(go.Scatter(
            x=dframe["date"], y=dframe["fed_effective_rate"], mode="lines",
            name="Efektivní Fed Funds (EFFR)",
            line=dict(color="#1D4ED8", width=3.2, shape="hv"),
            hovertemplate="<b>EFFR</b>: %{y:.2f} %<extra></extra>"
        ))
    if "sofr_rate" in indicators and "sofr_rate" in dframe.columns:
        fig.add_trace(go.Scatter(
            x=dframe["date"], y=dframe["sofr_rate"], mode="lines",
            name="SOFR (Secured Overnight Rate)",
            line=dict(color="#0D9488", width=2.2),
            hovertemplate="<b>SOFR</b>: %{y:.2f} %<extra></extra>"
        ))
    if "us_3m" in indicators and "us_3m" in dframe.columns:
        fig.add_trace(go.Scatter(
            x=dframe["date"], y=dframe["us_3m"], mode="lines",
            name="3M US Treasury Bill",
            line=dict(color="#D97706", width=2.0, dash="dot"),
            hovertemplate="<b>3M T-Bill</b>: %{y:.2f} %<extra></extra>"
        ))
    fig.update_layout(
        height=430, hovermode="x unified", margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor="rgba(255, 255, 255, 0.85)"),
        xaxis=dict(title="", showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(title="Úrokové sazby USD (%)", title_font=dict(color="#1D4ED8"), tickfont=dict(color="#1D4ED8"), showgrid=True, gridcolor="#f1f5f9", ticksuffix=" %"),
        plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF"
    )
    return fig


# --- B. INFLACE ---
def build_inflation_chart(dframe: pd.DataFrame) -> go.Figure:
    """Graf inflace ČR (Headline & Core CPI) s 2% cílem ČNB a reálnou sazbou."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_hrect(
        y0=1.0, y1=3.0, fillcolor="rgba(34, 197, 94, 0.12)", line_width=0,
        annotation_text="Toleranční pásmo ČNB (1–3 %)", annotation_position="top left",
        annotation_font=dict(color="#166534", size=11), secondary_y=False
    )
    fig.add_hline(
        y=2.0, line=dict(color="#16A34A", width=1.8, dash="dash"),
        annotation_text="Inflační cíl (2.0 %)", annotation_position="bottom right",
        annotation_font=dict(color="#16A34A", size=11), secondary_y=False
    )
    if "cpi_yoy" in dframe.columns:
        fig.add_trace(go.Scatter(
            x=dframe["date"], y=dframe["cpi_yoy"], mode="lines+markers",
            name="Celková inflace CPI (YoY %)", line=dict(color="#DC2626", width=3.0),
            marker=dict(size=4, color="#DC2626"), hovertemplate="<b>CPI ČR</b>: %{y:.1f} %<extra></extra>"
        ), secondary_y=False)
    if "cpi_core_yoy" in dframe.columns:
        fig.add_trace(go.Scatter(
            x=dframe["date"], y=dframe["cpi_core_yoy"], mode="lines",
            name="Jádrová inflace ČR (Core CPI)", line=dict(color="#D97706", width=2.4),
            hovertemplate="<b>Jádrová inflace ČR</b>: %{y:.1f} %<extra></extra>"
        ), secondary_y=False)
    if "repo_rate" in dframe.columns and "cpi_yoy" in dframe.columns:
        real_rate = dframe["repo_rate"] - dframe["cpi_yoy"]
        fig.add_trace(go.Scatter(
            x=dframe["date"], y=real_rate, mode="lines",
            name="Reálná sazba (Repo − CPI)", line=dict(color="#6366F1", width=2.0, dash="dot"),
            hovertemplate="<b>Reálná sazba</b>: %{y:.1f} %<extra></extra>"
        ), secondary_y=True)
        fig.add_hline(y=0.0, line=dict(color="#94A3B8", width=1.2, dash="dash"), secondary_y=True)
    fig.update_layout(
        height=430, hovermode="x unified", margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor="rgba(255, 255, 255, 0.85)"),
        xaxis=dict(title="", showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(title="Meziroční inflace (%)", title_font=dict(color="#DC2626"), tickfont=dict(color="#DC2626"), showgrid=True, gridcolor="#f1f5f9", ticksuffix=" %"),
        yaxis2=dict(title="Reálná úroková míra (%)", title_font=dict(color="#6366F1"), tickfont=dict(color="#6366F1"), overlaying="y", side="right", showgrid=False, ticksuffix=" %"),
        plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF"
    )
    return fig


def build_eu_inflation_chart(dframe: pd.DataFrame) -> go.Figure:
    """Graf inflace Eurozóny (Headline & Core HICP)."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_hline(
        y=2.0, line=dict(color="#16A34A", width=1.8, dash="dash"),
        annotation_text="Inflační cíl ECB (2.0 %)", annotation_position="bottom right",
        annotation_font=dict(color="#16A34A", size=11), secondary_y=False
    )
    if "eu_cpi_yoy" in dframe.columns:
        fig.add_trace(go.Scatter(
            x=dframe["date"], y=dframe["eu_cpi_yoy"], mode="lines+markers",
            name="Harmonizovaná inflace (HICP YoY %)", line=dict(color="#DC2626", width=3.0),
            marker=dict(size=4, color="#DC2626"), hovertemplate="<b>EU HICP</b>: %{y:.1f} %<extra></extra>"
        ), secondary_y=False)
    if "eu_core_cpi_yoy" in dframe.columns:
        fig.add_trace(go.Scatter(
            x=dframe["date"], y=dframe["eu_core_cpi_yoy"], mode="lines",
            name="Jádrová inflace EU (Core HICP)", line=dict(color="#D97706", width=2.4),
            hovertemplate="<b>EU Core HICP</b>: %{y:.1f} %<extra></extra>"
        ), secondary_y=False)
    if "ecb_deposit_rate" in dframe.columns and "eu_cpi_yoy" in dframe.columns:
        real_eu_rate = dframe["ecb_deposit_rate"] - dframe["eu_cpi_yoy"]
        fig.add_trace(go.Scatter(
            x=dframe["date"], y=real_eu_rate, mode="lines",
            name="Reálná sazba ECB (Depo − HICP)", line=dict(color="#6366F1", width=2.0, dash="dot"),
            hovertemplate="<b>Reálná sazba ECB</b>: %{y:.1f} %<extra></extra>"
        ), secondary_y=True)
        fig.add_hline(y=0.0, line=dict(color="#94A3B8", width=1.2, dash="dash"), secondary_y=True)
    fig.update_layout(
        height=430, hovermode="x unified", margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor="rgba(255, 255, 255, 0.85)"),
        xaxis=dict(title="", showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(title="Inflace Eurozóny (% YoY)", title_font=dict(color="#DC2626"), tickfont=dict(color="#DC2626"), showgrid=True, gridcolor="#f1f5f9", ticksuffix=" %"),
        yaxis2=dict(title="Reálná úroková míra EUR (%)", title_font=dict(color="#6366F1"), tickfont=dict(color="#6366F1"), overlaying="y", side="right", showgrid=False, ticksuffix=" %"),
        plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF"
    )
    return fig


def build_us_inflation_chart(dframe: pd.DataFrame) -> go.Figure:
    """Graf inflace USA (Headline CPI a Core CPI)."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_hline(
        y=2.0, line=dict(color="#16A34A", width=1.8, dash="dash"),
        annotation_text="Inflační cíl Fedu (2.0 %)", annotation_position="bottom right",
        annotation_font=dict(color="#16A34A", size=11), secondary_y=False
    )
    if "us_cpi_yoy" in dframe.columns:
        fig.add_trace(go.Scatter(
            x=dframe["date"], y=dframe["us_cpi_yoy"], mode="lines+markers",
            name="Headline CPI USA (YoY %)", line=dict(color="#DC2626", width=3.0),
            marker=dict(size=4, color="#DC2626"), hovertemplate="<b>Headline CPI</b>: %{y:.1f} %<extra></extra>"
        ), secondary_y=False)
    if "us_core_cpi_yoy" in dframe.columns:
        fig.add_trace(go.Scatter(
            x=dframe["date"], y=dframe["us_core_cpi_yoy"], mode="lines",
            name="Jádrová inflace (Core CPI)", line=dict(color="#D97706", width=2.4),
            hovertemplate="<b>Core CPI</b>: %{y:.1f} %<extra></extra>"
        ), secondary_y=False)
    if "fed_effective_rate" in dframe.columns and "us_cpi_yoy" in dframe.columns:
        real_us_rate = dframe["fed_effective_rate"] - dframe["us_cpi_yoy"]
        fig.add_trace(go.Scatter(
            x=dframe["date"], y=real_us_rate, mode="lines",
            name="Reálná sazba (Fed EFFR − CPI)", line=dict(color="#6366F1", width=2.0, dash="dot"),
            hovertemplate="<b>Reálná sazba USA</b>: %{y:.1f} %<extra></extra>"
        ), secondary_y=True)
        fig.add_hline(y=0.0, line=dict(color="#94A3B8", width=1.2, dash="dash"), secondary_y=True)
    fig.update_layout(
        height=430, hovermode="x unified", margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor="rgba(255, 255, 255, 0.85)"),
        xaxis=dict(title="", showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(title="Inflace USA (% YoY)", title_font=dict(color="#DC2626"), tickfont=dict(color="#DC2626"), showgrid=True, gridcolor="#f1f5f9", ticksuffix=" %"),
        yaxis2=dict(title="Reálná úroková míra USA (%)", title_font=dict(color="#6366F1"), tickfont=dict(color="#6366F1"), overlaying="y", side="right", showgrid=False, ticksuffix=" %"),
        plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF"
    )
    return fig


# --- C. HDP ---
def build_gdp_chart(dframe: pd.DataFrame, indicators: List[str]) -> go.Figure:
    """Kombinovaný graf HDP ČR."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    df_gdp_plot = dframe.drop_duplicates(subset=["quarter"] if "quarter" in dframe.columns else ["date"]).copy()
    if "gdp_nominal_czk_bn" in indicators and "gdp_nominal_czk_bn" in dframe.columns:
        fig.add_trace(go.Bar(
            x=df_gdp_plot["date"], y=df_gdp_plot["gdp_nominal_czk_bn"],
            name="Nominální HDP (mld. CZK)", marker=dict(color="rgba(71, 85, 105, 0.55)", line=dict(color="#334155", width=1)),
            hovertemplate="<b>Nominální HDP ČR</b>: %{y:,.1f} mld. CZK<extra></extra>"
        ), secondary_y=False)
    if "gdp_growth_real" in indicators and "gdp_growth_real" in dframe.columns:
        marker_colors = ["#16A34A" if val >= 0 else "#DC2626" for val in df_gdp_plot["gdp_growth_real"]]
        fig.add_trace(go.Scatter(
            x=df_gdp_plot["date"], y=df_gdp_plot["gdp_growth_real"], mode="lines+markers",
            name="Reálný růst HDP ČR (YoY %)", line=dict(color="#D97706", width=3),
            marker=dict(size=7, color=marker_colors, line=dict(color="#FFFFFF", width=1.5)),
            hovertemplate="<b>Reálný růst ČR</b>: %{y:+.1f} %<extra></extra>"
        ), secondary_y=True)
        fig.add_hline(y=0.0, line=dict(color="#94A3B8", width=1.5, dash="dash"), secondary_y=True)
    fig.update_layout(
        height=430, hovermode="x unified", margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor="rgba(255, 255, 255, 0.85)"),
        xaxis=dict(title="", showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(title="Nominální HDP (mld. CZK)", title_font=dict(color="#334155"), tickfont=dict(color="#334155"), showgrid=True, gridcolor="#f1f5f9", ticksuffix=" mld."),
        yaxis2=dict(title="Reálný růst HDP (YoY %)", title_font=dict(color="#D97706"), tickfont=dict(color="#D97706"), overlaying="y", side="right", showgrid=False, ticksuffix=" %"),
        plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF"
    )
    return fig


def build_eu_gdp_chart(dframe: pd.DataFrame, indicators: List[str]) -> go.Figure:
    """Kombinovaný graf HDP Eurozóny / EU."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    df_gdp_plot = dframe.drop_duplicates(subset=["quarter"] if "quarter" in dframe.columns else ["date"]).copy()
    if "eu_gdp_nominal_eur_bn" in indicators and "eu_gdp_nominal_eur_bn" in dframe.columns:
        fig.add_trace(go.Bar(
            x=df_gdp_plot["date"], y=df_gdp_plot["eu_gdp_nominal_eur_bn"],
            name="Nominální HDP Eurozóny (mld. EUR)", marker=dict(color="rgba(30, 58, 138, 0.50)", line=dict(color="#1e3a8a", width=1)),
            hovertemplate="<b>Nominální HDP EU</b>: %{y:,.0f} mld. EUR<extra></extra>"
        ), secondary_y=False)
    if "eu_gdp_growth_real" in indicators and "eu_gdp_growth_real" in dframe.columns:
        marker_colors = ["#16A34A" if val >= 0 else "#DC2626" for val in df_gdp_plot["eu_gdp_growth_real"]]
        fig.add_trace(go.Scatter(
            x=df_gdp_plot["date"], y=df_gdp_plot["eu_gdp_growth_real"], mode="lines+markers",
            name="Reálný růst HDP Eurozóny (YoY %)", line=dict(color="#2563EB", width=3),
            marker=dict(size=7, color=marker_colors, line=dict(color="#FFFFFF", width=1.5)),
            hovertemplate="<b>Reálný růst EU</b>: %{y:+.1f} %<extra></extra>"
        ), secondary_y=True)
        fig.add_hline(y=0.0, line=dict(color="#94A3B8", width=1.5, dash="dash"), secondary_y=True)
    fig.update_layout(
        height=430, hovermode="x unified", margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor="rgba(255, 255, 255, 0.85)"),
        xaxis=dict(title="", showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(title="Nominální HDP EU (mld. EUR)", title_font=dict(color="#1e3a8a"), tickfont=dict(color="#1e3a8a"), showgrid=True, gridcolor="#f1f5f9", ticksuffix=" mld. €"),
        yaxis2=dict(title="Reálný růst HDP EU (YoY %)", title_font=dict(color="#2563EB"), tickfont=dict(color="#2563EB"), overlaying="y", side="right", showgrid=False, ticksuffix=" %"),
        plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF"
    )
    return fig


def build_us_gdp_chart(dframe: pd.DataFrame, indicators: List[str]) -> go.Figure:
    """Kombinovaný graf HDP USA."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    df_gdp_plot = dframe.drop_duplicates(subset=["quarter"] if "quarter" in dframe.columns else ["date"]).copy()
    if "us_gdp_nominal_usd_bn" in indicators and "us_gdp_nominal_usd_bn" in dframe.columns:
        fig.add_trace(go.Bar(
            x=df_gdp_plot["date"], y=df_gdp_plot["us_gdp_nominal_usd_bn"],
            name="Nominální HDP USA (mld. USD)", marker=dict(color="rgba(30, 41, 59, 0.55)", line=dict(color="#0f172a", width=1)),
            hovertemplate="<b>Nominální HDP USA</b>: %{y:,.0f} mld. USD<extra></extra>"
        ), secondary_y=False)
    if "us_gdp_growth_real" in indicators and "us_gdp_growth_real" in dframe.columns:
        marker_colors = ["#16A34A" if val >= 0 else "#DC2626" for val in df_gdp_plot["us_gdp_growth_real"]]
        fig.add_trace(go.Scatter(
            x=df_gdp_plot["date"], y=df_gdp_plot["us_gdp_growth_real"], mode="lines+markers",
            name="Reálný růst HDP USA (YoY %)", line=dict(color="#2563EB", width=3),
            marker=dict(size=7, color=marker_colors, line=dict(color="#FFFFFF", width=1.5)),
            hovertemplate="<b>Reálný růst USA</b>: %{y:+.1f} %<extra></extra>"
        ), secondary_y=True)
        fig.add_hline(y=0.0, line=dict(color="#94A3B8", width=1.5, dash="dash"), secondary_y=True)
    fig.update_layout(
        height=430, hovermode="x unified", margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor="rgba(255, 255, 255, 0.85)"),
        xaxis=dict(title="", showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(title="Nominální HDP USA (mld. USD)", title_font=dict(color="#0f172a"), tickfont=dict(color="#0f172a"), showgrid=True, gridcolor="#f1f5f9", ticksuffix=" mld. $"),
        yaxis2=dict(title="Reálný růst HDP USA (YoY %)", title_font=dict(color="#2563EB"), tickfont=dict(color="#2563EB"), overlaying="y", side="right", showgrid=False, ticksuffix=" %"),
        plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF"
    )
    return fig


# --- D. PRŮMYSL A SPOTŘEBA ---
def build_activity_chart(dframe: pd.DataFrame, region: str = "CZ") -> go.Figure:
    """Graf spotřeby a průmyslové produkce."""
    fig = go.Figure()
    if region == "CZ":
        retail_col, ind_col = "retail_sales_yoy", "industrial_prod_yoy"
        retail_name, ind_name = "Maloobchodní tržby ČR (Spotřeba YoY)", "Průmyslová produkce ČR (YoY)"
    elif region == "EU":
        retail_col, ind_col = "eu_retail_sales_yoy", "eu_industrial_prod_yoy"
        retail_name, ind_name = "Maloobchodní tržby EU (Spotřeba YoY)", "Průmyslová výroba EU (YoY)"
    else:
        retail_col, ind_col = "us_retail_sales_yoy", "us_industrial_prod_yoy"
        retail_name, ind_name = "Maloobchodní tržby USA (Spotřeba YoY)", "Průmyslová produkce USA (YoY)"

    if retail_col in dframe.columns:
        fig.add_trace(go.Scatter(
            x=dframe["date"], y=dframe[retail_col], mode="lines+markers",
            name=retail_name, line=dict(color="#0284C7", width=2.6),
            marker=dict(size=4, color="#0284C7"), hovertemplate=f"<b>{retail_name}</b>: %{{y:+.1f}} %<extra></extra>"
        ))
    if ind_col in dframe.columns:
        fig.add_trace(go.Scatter(
            x=dframe["date"], y=dframe[ind_col], mode="lines+markers",
            name=ind_name, line=dict(color="#7C3AED", width=2.4),
            marker=dict(size=4, color="#7C3AED"), hovertemplate=f"<b>{ind_name}</b>: %{{y:+.1f}} %<extra></extra>"
        ))
    fig.add_hline(y=0.0, line=dict(color="#94A3B8", width=1.5, dash="dash"))
    fig.update_layout(
        height=430, hovermode="x unified", margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor="rgba(255, 255, 255, 0.85)"),
        xaxis=dict(title="", showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(title="Meziroční růst / pokles (%)", ticksuffix=" %", showgrid=True, gridcolor="#f1f5f9"),
        plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF"
    )
    return fig


# --- E. TRH PRÁCE ---
def build_unemployment_chart(dframe: pd.DataFrame) -> go.Figure:
    """Plošný graf míry nezaměstnanosti v ČR."""
    fig = go.Figure()
    if "unemployment_rate" in dframe.columns:
        fig.add_trace(go.Scatter(
            x=dframe["date"], y=dframe["unemployment_rate"], mode="lines",
            name="Míra nezaměstnanosti v ČR", line=dict(color="#4F46E5", width=2.8),
            fill="tozeroy", fillcolor="rgba(79, 70, 229, 0.08)", hovertemplate="<b>Nezaměstnanost ČR</b>: %{y:.1f} %<extra></extra>"
        ))
        avg_une = dframe["unemployment_rate"].mean()
        fig.add_hline(y=avg_une, line=dict(color="#64748B", width=1.5, dash="dash"), annotation_text=f"Průměr: {avg_une:.2f} %", annotation_position="top right")
        min_val = dframe["unemployment_rate"].min()
        max_val = dframe["unemployment_rate"].max()
        min_row = dframe.loc[dframe["unemployment_rate"] == min_val].iloc[0]
        max_row = dframe.loc[dframe["unemployment_rate"] == max_val].iloc[0]
        fig.add_trace(go.Scatter(
            x=[min_row["date"], max_row["date"]], y=[min_val, max_val], mode="markers+text",
            name="Extrémy", marker=dict(size=8, color=["#16A34A", "#DC2626"]),
            text=[f"Min: {min_val:.1f} %", f"Max: {max_val:.1f} %"], textposition=["bottom center", "top center"],
            showlegend=False, hoverinfo="skip"
        ))
        fig.update_layout(
            height=430, hovermode="x unified", margin=dict(l=20, r=20, t=30, b=20),
            xaxis=dict(title="", showgrid=True, gridcolor="#f1f5f9"),
            yaxis=dict(title="Míra nezaměstnanosti (%)", ticksuffix=" %", showgrid=True, gridcolor="#f1f5f9", range=[0, max(6.0, max_val + 1.0)]),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF"
        )
    return fig


def build_eu_unemployment_chart(dframe: pd.DataFrame) -> go.Figure:
    """Graf míry nezaměstnanosti v EU."""
    fig = go.Figure()
    if "eu_unemployment_rate" in dframe.columns:
        fig.add_trace(go.Scatter(
            x=dframe["date"], y=dframe["eu_unemployment_rate"], mode="lines",
            name="Míra nezaměstnanosti v EU", line=dict(color="#2563EB", width=2.8),
            fill="tozeroy", fillcolor="rgba(37, 99, 235, 0.08)", hovertemplate="<b>Nezaměstnanost EU</b>: %{y:.1f} %<extra></extra>"
        ))
        avg_une = dframe["eu_unemployment_rate"].mean()
        fig.add_hline(y=avg_une, line=dict(color="#64748B", width=1.5, dash="dash"), annotation_text=f"Průměr EU: {avg_une:.2f} %", annotation_position="top right")
        fig.update_layout(
            height=430, hovermode="x unified", margin=dict(l=20, r=20, t=30, b=20),
            xaxis=dict(title="", showgrid=True, gridcolor="#f1f5f9"),
            yaxis=dict(title="Míra nezaměstnanosti EU (%)", ticksuffix=" %", showgrid=True, gridcolor="#f1f5f9"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF"
        )
    return fig


def build_us_unemployment_chart(dframe: pd.DataFrame) -> go.Figure:
    """Graf míry nezaměstnanosti USA."""
    fig = go.Figure()
    if "us_unemployment_rate" in dframe.columns:
        fig.add_trace(go.Scatter(
            x=dframe["date"], y=dframe["us_unemployment_rate"], mode="lines",
            name="Míra nezaměstnanosti USA (U-3)", line=dict(color="#2563EB", width=2.8),
            fill="tozeroy", fillcolor="rgba(37, 99, 235, 0.08)", hovertemplate="<b>Nezaměstnanost USA</b>: %{y:.1f} %<extra></extra>"
        ))
        avg_une = dframe["us_unemployment_rate"].mean()
        fig.add_hline(y=avg_une, line=dict(color="#64748B", width=1.5, dash="dash"), annotation_text=f"Průměr USA: {avg_une:.2f} %", annotation_position="top right")
        fig.update_layout(
            height=430, hovermode="x unified", margin=dict(l=20, r=20, t=30, b=20),
            xaxis=dict(title="", showgrid=True, gridcolor="#f1f5f9"),
            yaxis=dict(title="Míra nezaměstnanosti USA (%)", ticksuffix=" %", showgrid=True, gridcolor="#f1f5f9"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF"
        )
    return fig


# --- F. DYNAMICKÝ VÝBĚR MĚN (FX - OMEZENÍ PŘEPLNĚNÉHO GRAFU) ---
def build_dynamic_fx_chart_cz(dframe_daily: pd.DataFrame, selected_currencies: List[str]) -> go.Figure:
    """Dynamický devizový graf ČNB přizpůsobený zvoleným měnám."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    curr_set = set(selected_currencies) if selected_currencies else {"EUR", "USD", "CZK"}

    # EUR/CZK
    if ("EUR" in curr_set and "CZK" in curr_set) or (len(curr_set) == 1 and "EUR" in curr_set):
        if "eur_czk" in dframe_daily.columns:
            fig.add_trace(go.Scatter(
                x=dframe_daily["date"], y=dframe_daily["eur_czk"], mode="lines",
                name="EUR / CZK", line=dict(color="#2563EB", width=2.4),
                hovertemplate="<b>EUR/CZK</b>: %{y:.4f} Kč<extra></extra>"
            ), secondary_y=False)

    # USD/CZK
    if ("USD" in curr_set and "CZK" in curr_set) or (len(curr_set) == 1 and "USD" in curr_set):
        if "usd_czk" in dframe_daily.columns:
            fig.add_trace(go.Scatter(
                x=dframe_daily["date"], y=dframe_daily["usd_czk"], mode="lines",
                name="USD / CZK", line=dict(color="#059669", width=2.0),
                hovertemplate="<b>USD/CZK</b>: %{y:.4f} Kč<extra></extra>"
            ), secondary_y=False)

    # GBP/CZK
    if ("GBP" in curr_set and "CZK" in curr_set) or (len(curr_set) == 1 and "GBP" in curr_set):
        if "gbp_czk" in dframe_daily.columns:
            fig.add_trace(go.Scatter(
                x=dframe_daily["date"], y=dframe_daily["gbp_czk"], mode="lines",
                name="GBP / CZK", line=dict(color="#D97706", width=2.0),
                hovertemplate="<b>GBP/CZK</b>: %{y:.4f} Kč<extra></extra>"
            ), secondary_y=False)

    # PLN/CZK (pravá osa pro detailní rozlišení kurzu cca 5.5-6.0 Kč)
    if ("PLN" in curr_set and "CZK" in curr_set) or (len(curr_set) == 1 and "PLN" in curr_set):
        if "pln_czk" in dframe_daily.columns:
            fig.add_trace(go.Scatter(
                x=dframe_daily["date"], y=dframe_daily["pln_czk"], mode="lines",
                name="PLN / CZK (pravá osa)", line=dict(color="#DC2626", width=2.0, dash="dot"),
                hovertemplate="<b>PLN/CZK</b>: %{y:.4f} Kč<extra></extra>"
            ), secondary_y=True)

    fig.update_layout(
        height=450, hovermode="x unified", margin=dict(l=20, r=20, t=30, b=20),
        xaxis=dict(title="", showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(title="Kurz EUR, USD, GBP (Kč)", ticksuffix=" Kč", showgrid=True, gridcolor="#f1f5f9"),
        yaxis2=dict(title="Kurz PLN (Kč)", title_font=dict(color="#DC2626"), tickfont=dict(color="#DC2626"), overlaying="y", side="right", showgrid=False, ticksuffix=" Kč"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor="rgba(255, 255, 255, 0.85)"),
        plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF"
    )
    return fig


def build_dynamic_fx_chart_eu(dframe_daily: pd.DataFrame, selected_currencies: List[str]) -> go.Figure:
    """Dynamický devizový graf Eurozóny."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    curr_set = set(selected_currencies) if selected_currencies else {"EUR", "USD", "CZK"}

    if "USD" in curr_set and "eur_usd" in dframe_daily.columns:
        fig.add_trace(go.Scatter(
            x=dframe_daily["date"], y=dframe_daily["eur_usd"], mode="lines",
            name="EUR / USD", line=dict(color="#059669", width=2.4),
            hovertemplate="<b>EUR/USD</b>: %{y:.4f} $<extra></extra>"
        ), secondary_y=False)

    if "GBP" in curr_set and "eur_gbp" in dframe_daily.columns:
        fig.add_trace(go.Scatter(
            x=dframe_daily["date"], y=dframe_daily["eur_gbp"], mode="lines",
            name="EUR / GBP", line=dict(color="#D97706", width=2.0),
            hovertemplate="<b>EUR/GBP</b>: %{y:.4f} £<extra></extra>"
        ), secondary_y=False)

    if "CZK" in curr_set and "eur_czk" in dframe_daily.columns:
        fig.add_trace(go.Scatter(
            x=dframe_daily["date"], y=dframe_daily["eur_czk"], mode="lines",
            name="EUR / CZK (pravá osa)", line=dict(color="#2563EB", width=2.2),
            hovertemplate="<b>EUR/CZK</b>: %{y:.2f} Kč<extra></extra>"
        ), secondary_y=True)

    if "PLN" in curr_set and "eur_pln" in dframe_daily.columns:
        fig.add_trace(go.Scatter(
            x=dframe_daily["date"], y=dframe_daily["eur_pln"], mode="lines",
            name="EUR / PLN (pravá osa)", line=dict(color="#DC2626", width=2.0, dash="dot"),
            hovertemplate="<b>EUR/PLN</b>: %{y:.4f} zł<extra></extra>"
        ), secondary_y=True)

    fig.update_layout(
        height=450, hovermode="x unified", margin=dict(l=20, r=20, t=30, b=20),
        xaxis=dict(title="", showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(title="Kurz EUR/USD & EUR/GBP", showgrid=True, gridcolor="#f1f5f9"),
        yaxis2=dict(title="Kurz EUR/CZK & EUR/PLN", overlaying="y", side="right", showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor="rgba(255, 255, 255, 0.85)"),
        plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF"
    )
    return fig


def build_dynamic_fx_chart_us(dframe_daily: pd.DataFrame, selected_currencies: List[str]) -> go.Figure:
    """Dynamický devizový graf USA s DXY indexem a vybranými měnovými páry."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    curr_set = set(selected_currencies) if selected_currencies else {"USD", "EUR", "GBP"}

    if "USD" in curr_set and "dxy_index" in dframe_daily.columns:
        fig.add_trace(go.Scatter(
            x=dframe_daily["date"], y=dframe_daily["dxy_index"], mode="lines",
            name="U.S. Dollar Index (DXY)", line=dict(color="#1E293B", width=2.6),
            hovertemplate="<b>DXY Index</b>: %{y:.2f} b.<extra></extra>"
        ), secondary_y=False)

    if "EUR" in curr_set and "eur_usd" in dframe_daily.columns:
        fig.add_trace(go.Scatter(
            x=dframe_daily["date"], y=dframe_daily["eur_usd"], mode="lines",
            name="EUR / USD", line=dict(color="#2563EB", width=2.0),
            hovertemplate="<b>EUR/USD</b>: %{y:.4f} $<extra></extra>"
        ), secondary_y=True)

    if "GBP" in curr_set and "gbp_usd" in dframe_daily.columns:
        fig.add_trace(go.Scatter(
            x=dframe_daily["date"], y=dframe_daily["gbp_usd"], mode="lines",
            name="GBP / USD (Cable)", line=dict(color="#D97706", width=2.0),
            hovertemplate="<b>GBP/USD</b>: %{y:.4f} $<extra></extra>"
        ), secondary_y=True)

    if "PLN" in curr_set and "usd_pln" in dframe_daily.columns:
        fig.add_trace(go.Scatter(
            x=dframe_daily["date"], y=dframe_daily["usd_pln"], mode="lines",
            name="USD / PLN", line=dict(color="#DC2626", width=1.8, dash="dot"),
            hovertemplate="<b>USD/PLN</b>: %{y:.4f} zł<extra></extra>"
        ), secondary_y=True)

    fig.update_layout(
        height=450, hovermode="x unified", margin=dict(l=20, r=20, t=30, b=20),
        xaxis=dict(title="", showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(title="Dolarový index DXY (body)", title_font=dict(color="#1E293B"), tickfont=dict(color="#1E293B"), showgrid=True, gridcolor="#f1f5f9"),
        yaxis2=dict(title="Měnové kurzy ($)", title_font=dict(color="#2563EB"), tickfont=dict(color="#2563EB"), overlaying="y", side="right", showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor="rgba(255, 255, 255, 0.85)"),
        plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF"
    )
    return fig


# --- G. AKCIOVÉ INDEXY (TRHY) ---
def build_stock_comparison_chart(dframe: pd.DataFrame, selected_indices: List[str], mode: str = "pct") -> go.Figure:
    """Srovnávací graf normalizované výkonnosti akciových indexů."""
    fig = go.Figure()
    if dframe.empty or not selected_indices:
        return fig

    index_configs = {
        "Index PX (Praha)": ("px_index", "#DC2626", "Index PX (Praha)"),
        "Euro Stoxx 50 (EU)": ("stoxx50_index", "#059669", "Euro Stoxx 50 (EU)"),
        "S&P 500 (USA)": ("sp500_index", "#2563EB", "S&P 500 (USA)"),
        "NASDAQ (USA)": ("nasdaq_index", "#7C3AED", "NASDAQ Composite (USA)")
    }

    first_row = dframe.iloc[0]

    for label in selected_indices:
        cfg = index_configs.get(label)
        if not cfg:
            continue
        col, color, name = cfg
        if col in dframe.columns:
            base_val = first_row.get(col)
            if base_val is not None and not pd.isna(base_val) and base_val > 0:
                if mode == "pct":
                    y_vals = ((dframe[col] / base_val) - 1.0) * 100.0
                    hover = f"<b>{name}</b>: %{{y:+.2f}} % (hodnota: %{{customdata:,.1f}} b.)<extra></extra>"
                else:
                    y_vals = (dframe[col] / base_val) * 100.0
                    hover = f"<b>{name}</b>: %{{y:.1f}} b. (hodnota: %{{customdata:,.1f}} b.)<extra></extra>"

                fig.add_trace(go.Scatter(
                    x=dframe["date"],
                    y=y_vals,
                    mode="lines",
                    name=name,
                    line=dict(color=color, width=2.6),
                    customdata=dframe[col],
                    hovertemplate=hover
                ))

    ref_line = 0.0 if mode == "pct" else 100.0
    fig.add_hline(y=ref_line, line=dict(color="#64748B", width=1.5, dash="dash"),
                  annotation_text="Báze (0 %)" if mode == "pct" else "Báze (100 b.)",
                  annotation_position="bottom left")

    y_title = "Relativní zhodnocení (%)" if mode == "pct" else "Index rebase (báze = 100)"
    suffix = " %" if mode == "pct" else " b."

    fig.update_layout(
        height=460,
        hovermode="x unified",
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis=dict(title="", showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(title=y_title, ticksuffix=suffix, showgrid=True, gridcolor="#f1f5f9"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor="rgba(255, 255, 255, 0.85)"),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF"
    )
    return fig


def build_single_stock_chart(dframe: pd.DataFrame, col: str, title: str, color: str = "#2563EB") -> go.Figure:
    """Detailní cenový graf konkrétního akciového indexu s trendem a extrémy."""
    fig = go.Figure()
    if col in dframe.columns:
        fig.add_trace(go.Scatter(
            x=dframe["date"],
            y=dframe[col],
            mode="lines",
            name=title,
            line=dict(color=color, width=2.8),
            fill="tozeroy",
            fillcolor=f"rgba{tuple(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + (0.06,)}",
            hovertemplate=f"<b>{title}</b>: %{{y:,.1f}} bodů<extra></extra>"
        ))

        if len(dframe) >= 12:
            sma12 = dframe[col].rolling(window=12, min_periods=3).mean()
            fig.add_trace(go.Scatter(
                x=dframe["date"],
                y=sma12,
                mode="lines",
                name="12M klouzavý průměr",
                line=dict(color="#64748B", width=1.5, dash="dot"),
                hovertemplate="<b>12M SMA</b>: %{y:,.1f} bodů<extra></extra>"
            ))

        min_val = dframe[col].min()
        max_val = dframe[col].max()
        min_row = dframe.loc[dframe[col] == min_val].iloc[0]
        max_row = dframe.loc[dframe[col] == max_val].iloc[0]

        fig.add_trace(go.Scatter(
            x=[min_row["date"], max_row["date"]],
            y=[min_val, max_val],
            mode="markers+text",
            name="Extrémy",
            marker=dict(size=8, color=["#16A34A", "#DC2626"]),
            text=[f"Min: {min_val:,.0f}", f"Max: {max_val:,.0f}"],
            textposition=["bottom center", "top center"],
            showlegend=False,
            hoverinfo="skip"
        ))

    fig.update_layout(
        height=430,
        hovermode="x unified",
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis=dict(title="", showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(title="Hodnota indexu (body)", showgrid=True, gridcolor="#f1f5f9"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor="rgba(255, 255, 255, 0.85)"),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF"
    )
    return fig


# --- H. VEŘEJNÝ DLUH & FISKÁL ---
def build_debt_charts(dframe: pd.DataFrame) -> Tuple[go.Figure, go.Figure]:
    """Grafy pro veřejný dluh ČR."""
    df_q_plot = dframe.drop_duplicates(subset=["quarter"] if "quarter" in dframe.columns else ["date"]).copy()
    fig_debt = go.Figure()
    if "public_debt_gdp_pct" in df_q_plot.columns:
        fig_debt.add_hline(y=60.0, line=dict(color="#DC2626", width=2.0, dash="dash"), annotation_text="Maastrichtský limit (60.0 % HDP)", annotation_position="bottom right")
        fig_debt.add_trace(go.Scatter(
            x=df_q_plot["date"], y=df_q_plot["public_debt_gdp_pct"], mode="lines+markers",
            name="Veřejný dluh ČR (% HDP)", line=dict(color="#4F46E5", width=3.0),
            marker=dict(size=6, color="#4F46E5"), hovertemplate="<b>Dluh k HDP</b>: %{y:.1f} %<extra></extra>"
        ))
    fig_debt.update_layout(
        height=380, hovermode="x unified", margin=dict(l=20, r=20, t=30, b=20),
        xaxis=dict(title="", showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(title="Veřejný dluh (% HDP)", ticksuffix=" %", showgrid=True, gridcolor="#f1f5f9", range=[20, 90]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF"
    )

    fig_def = go.Figure()
    if "budget_deficit_czk_bn" in df_q_plot.columns:
        bar_colors = ["#16A34A" if v >= 0 else "#DC2626" for v in df_q_plot["budget_deficit_czk_bn"]]
        fig_def.add_trace(go.Bar(
            x=df_q_plot["date"], y=df_q_plot["budget_deficit_czk_bn"],
            name="Kvartální saldo rozpočtu", marker=dict(color=bar_colors),
            hovertemplate="<b>Saldo SR</b>: %{y:,.1f} mld. Kč<extra></extra>"
        ))
        fig_def.add_hline(y=0.0, line=dict(color="#334155", width=1.0))
    fig_def.update_layout(
        height=380, hovermode="x unified", margin=dict(l=20, r=20, t=30, b=20),
        xaxis=dict(title="", showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(title="Saldo rozpočtu (mld. CZK)", ticksuffix=" mld.", showgrid=True, gridcolor="#f1f5f9"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF"
    )
    return fig_debt, fig_def


def build_eu_debt_charts(dframe: pd.DataFrame) -> Tuple[go.Figure, go.Figure]:
    """Grafy pro veřejný dluh Eurozóny."""
    df_q_plot = dframe.drop_duplicates(subset=["quarter"] if "quarter" in dframe.columns else ["date"]).copy()
    fig_debt = go.Figure()
    if "eu_public_debt_gdp_pct" in df_q_plot.columns:
        fig_debt.add_hline(y=60.0, line=dict(color="#16A34A", width=1.8, dash="dash"), annotation_text="Maastrichtské kritérium (60.0 % HDP)", annotation_position="bottom right")
        fig_debt.add_trace(go.Scatter(
            x=df_q_plot["date"], y=df_q_plot["eu_public_debt_gdp_pct"], mode="lines+markers",
            name="Veřejný dluh Eurozóny (% HDP)", line=dict(color="#2563EB", width=3.0),
            marker=dict(size=6, color="#2563EB"), hovertemplate="<b>Dluh Eurozóny k HDP</b>: %{y:.1f} %<extra></extra>"
        ))
    fig_debt.update_layout(
        height=380, hovermode="x unified", margin=dict(l=20, r=20, t=30, b=20),
        xaxis=dict(title="", showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(title="Veřejný dluh EU (% HDP)", ticksuffix=" %", showgrid=True, gridcolor="#f1f5f9", range=[50, 110]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF"
    )

    fig_def = go.Figure()
    if "eu_budget_deficit_eur_bn" in df_q_plot.columns:
        bar_colors = ["#16A34A" if v >= 0 else "#DC2626" for v in df_q_plot["eu_budget_deficit_eur_bn"]]
        fig_def.add_trace(go.Bar(
            x=df_q_plot["date"], y=df_q_plot["eu_budget_deficit_eur_bn"],
            name="Kvartální saldo rozpočtu Eurozóny", marker=dict(color=bar_colors),
            hovertemplate="<b>Saldo EU</b>: %{y:,.0f} mld. EUR<extra></extra>"
        ))
        fig_def.add_hline(y=0.0, line=dict(color="#334155", width=1.0))
    fig_def.update_layout(
        height=380, hovermode="x unified", margin=dict(l=20, r=20, t=30, b=20),
        xaxis=dict(title="", showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(title="Saldo rozpočtu (mld. EUR)", ticksuffix=" mld. €", showgrid=True, gridcolor="#f1f5f9"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF"
    )
    return fig_debt, fig_def


def build_us_debt_charts(dframe: pd.DataFrame) -> Tuple[go.Figure, go.Figure]:
    """Grafy pro dluh USA."""
    df_q_plot = dframe.drop_duplicates(subset=["quarter"] if "quarter" in dframe.columns else ["date"]).copy()
    fig_debt = go.Figure()
    if "us_public_debt_gdp_pct" in df_q_plot.columns:
        fig_debt.add_hline(y=100.0, line=dict(color="#D97706", width=1.8, dash="dash"), annotation_text="Hranice 100 % HDP", annotation_position="bottom right")
        fig_debt.add_trace(go.Scatter(
            x=df_q_plot["date"], y=df_q_plot["us_public_debt_gdp_pct"], mode="lines+markers",
            name="Federální dluh USA (% HDP)", line=dict(color="#DC2626", width=3.0),
            marker=dict(size=6, color="#DC2626"), hovertemplate="<b>Dluh USA k HDP</b>: %{y:.1f} %<extra></extra>"
        ))
    fig_debt.update_layout(
        height=380, hovermode="x unified", margin=dict(l=20, r=20, t=30, b=20),
        xaxis=dict(title="", showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(title="Dluh USA (% HDP)", ticksuffix=" %", showgrid=True, gridcolor="#f1f5f9", range=[80, 140]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF"
    )

    fig_def = go.Figure()
    if "us_budget_deficit_usd_bn" in df_q_plot.columns:
        bar_colors = ["#16A34A" if v >= 0 else "#DC2626" for v in df_q_plot["us_budget_deficit_usd_bn"]]
        fig_def.add_trace(go.Bar(
            x=df_q_plot["date"], y=df_q_plot["us_budget_deficit_usd_bn"],
            name="Kvartální federální deficit", marker=dict(color=bar_colors),
            hovertemplate="<b>Deficit USA</b>: %{y:,.0f} mld. USD<extra></extra>"
        ))
        fig_def.add_hline(y=0.0, line=dict(color="#334155", width=1.0))
    fig_def.update_layout(
        height=380, hovermode="x unified", margin=dict(l=20, r=20, t=30, b=20),
        xaxis=dict(title="", showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(title="Saldo rozpočtu (mld. USD)", ticksuffix=" mld. $", showgrid=True, gridcolor="#f1f5f9"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF"
    )
    return fig_debt, fig_def


# --- I. VÝNOSOVÉ KŘIVKY ---
def build_yield_curve_snapshot(df_row: pd.Series, compare_row: Optional[pd.Series] = None) -> go.Figure:
    """Výnosová křivka ČR (CZGB & IRS)."""
    tenor_labels = ["1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "15Y"]
    tenor_keys = ["1y", "2y", "3y", "5y", "7y", "10y", "15y"]
    czgb_vals = [df_row.get(f"czgb_{k}") for k in tenor_keys]
    irs_vals = [df_row.get(f"irs_{k}") for k in tenor_keys]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=tenor_labels, y=czgb_vals, mode="lines+markers+text", name="Státní dluhopisy (CZGB)",
        line=dict(color="#1D4ED8", width=3.2), marker=dict(size=8, color="#1D4ED8"),
        text=[f"{v:.2f} %" if (v is not None and not pd.isna(v)) else "" for v in czgb_vals],
        textposition="top center", hovertemplate="<b>CZGB %{x}</b>: %{y:.2f} % p.a.<extra></extra>"
    ))
    fig.add_trace(go.Scatter(
        x=tenor_labels, y=irs_vals, mode="lines+markers", name="Úrokové swapy (CZK IRS)",
        line=dict(color="#0D9488", width=2.5, dash="dash"), marker=dict(size=7, color="#0D9488"),
        hovertemplate="<b>CZK IRS %{x}</b>: %{y:.2f} % p.a.<extra></extra>"
    ))
    if compare_row is not None:
        comp_czgb = [compare_row.get(f"czgb_{k}") for k in tenor_keys]
        fig.add_trace(go.Scatter(
            x=tenor_labels, y=comp_czgb, mode="lines+markers", name="CZGB (Před rokem)",
            line=dict(color="#94A3B8", width=1.8, dash="dot"), marker=dict(size=6, color="#94A3B8"),
            hovertemplate="<b>CZGB (historie) %{x}</b>: %{y:.2f} % p.a.<extra></extra>"
        ))
    fig.update_layout(
        height=400, hovermode="x unified", margin=dict(l=20, r=20, t=30, b=20),
        xaxis=dict(title="Splatnost", showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(title="Výnos do splatnosti (% p.a.)", ticksuffix=" %", showgrid=True, gridcolor="#f1f5f9"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF"
    )
    return fig


def build_eu_yield_curve_snapshot(df_row: pd.Series, compare_row: Optional[pd.Series] = None) -> go.Figure:
    """Německá výnosová křivka Bundů."""
    tenor_labels = ["2Y", "5Y", "10Y", "30Y"]
    tenor_keys = ["2y", "5y", "10y", "30y"]
    bund_vals = [df_row.get(f"bund_{k}") for k in tenor_keys]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=tenor_labels, y=bund_vals, mode="lines+markers+text", name="Německý Bund (Aktuální)",
        line=dict(color="#2563EB", width=3.4), marker=dict(size=8, color="#2563EB"),
        text=[f"{v:.2f} %" if (v is not None and not pd.isna(v)) else "" for v in bund_vals],
        textposition="top center", hovertemplate="<b>Bund %{x}</b>: %{y:.2f} % p.a.<extra></extra>"
    ))
    if compare_row is not None:
        comp_vals = [compare_row.get(f"bund_{k}") for k in tenor_keys]
        fig.add_trace(go.Scatter(
            x=tenor_labels, y=comp_vals, mode="lines+markers", name="Německý Bund (Před rokem)",
            line=dict(color="#94A3B8", width=2.0, dash="dot"), marker=dict(size=6, color="#94A3B8"),
            hovertemplate="<b>Bund (historie) %{x}</b>: %{y:.2f} % p.a.<extra></extra>"
        ))
    fig.update_layout(
        height=400, hovermode="x unified", margin=dict(l=20, r=20, t=30, b=20),
        xaxis=dict(title="Splatnost", showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(title="Výnos do splatnosti (% p.a.)", ticksuffix=" %", showgrid=True, gridcolor="#f1f5f9"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF"
    )
    return fig


def build_us_yield_curve_snapshot(df_row: pd.Series, compare_row: Optional[pd.Series] = None) -> go.Figure:
    """Výnosová křivka USA (U.S. Treasury 1M–30Y)."""
    tenor_labels = ["1M", "3M", "6M", "1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y"]
    tenor_keys = ["1m", "3m", "6m", "1y", "2y", "3y", "5y", "7y", "10y", "20y", "30y"]
    us_vals = [df_row.get(f"us_{k}") for k in tenor_keys]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=tenor_labels, y=us_vals, mode="lines+markers+text", name="U.S. Treasury (Aktuální)",
        line=dict(color="#2563EB", width=3.4), marker=dict(size=8, color="#2563EB"),
        text=[f"{v:.2f} %" if (v is not None and not pd.isna(v)) else "" for v in us_vals],
        textposition="top center", hovertemplate="<b>US Treasury %{x}</b>: %{y:.2f} % p.a.<extra></extra>"
    ))
    if compare_row is not None:
        comp_vals = [compare_row.get(f"us_{k}") for k in tenor_keys]
        fig.add_trace(go.Scatter(
            x=tenor_labels, y=comp_vals, mode="lines+markers", name="U.S. Treasury (Před rokem)",
            line=dict(color="#94A3B8", width=2.0, dash="dot"), marker=dict(size=6, color="#94A3B8"),
            hovertemplate="<b>US Treasury (historie) %{x}</b>: %{y:.2f} % p.a.<extra></extra>"
        ))
    fig.update_layout(
        height=400, hovermode="x unified", margin=dict(l=20, r=20, t=30, b=20),
        xaxis=dict(title="Splatnost", showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(title="Výnos do splatnosti (% p.a.)", ticksuffix=" %", showgrid=True, gridcolor="#f1f5f9"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF"
    )
    return fig


# --- J. MEZINÁRODNÍ SROVNÁNÍ ---
def build_international_spread_chart(dframe: pd.DataFrame, comparison_type: str = "CZ") -> go.Figure:
    """Mezinárodní úroková a výnosová rozpětí."""
    fig = go.Figure()
    if comparison_type == "CZ":
        if "czgb_10y" in dframe.columns and "bund_10y" in dframe.columns:
            diff_bund_bps = (dframe["czgb_10y"] - dframe["bund_10y"]) * 100.0
            fig.add_trace(go.Scatter(
                x=dframe["date"], y=diff_bund_bps, mode="lines",
                name="Spread 10Y (CZGB − Německý Bund)", line=dict(color="#2563EB", width=2.5),
                hovertemplate="<b>Spread CZGB - Bund</b>: %{y:+.0f} bps<extra></extra>"
            ))
        if "czgb_10y" in dframe.columns and "us_10y" in dframe.columns:
            diff_us_bps = (dframe["czgb_10y"] - dframe["us_10y"]) * 100.0
            fig.add_trace(go.Scatter(
                x=dframe["date"], y=diff_us_bps, mode="lines",
                name="Spread 10Y (CZGB − US Treasury)", line=dict(color="#D97706", width=2.2, dash="dash"),
                hovertemplate="<b>Spread CZGB - US 10Y</b>: %{y:+.0f} bps<extra></extra>"
            ))
        title_text = "Mezinárodní sovereign spready ČR (v bps)"
    elif comparison_type == "EU":
        if "bund_10y" in dframe.columns and "us_10y" in dframe.columns:
            diff_bps = (dframe["bund_10y"] - dframe["us_10y"]) * 100.0
            fig.add_trace(go.Scatter(
                x=dframe["date"], y=diff_bps, mode="lines",
                name="Spread 10Y (Německý Bund − US Treasury)", line=dict(color="#2563EB", width=2.5),
                hovertemplate="<b>Spread Bund - US 10Y</b>: %{y:+.0f} bps<extra></extra>"
            ))
        title_text = "Transatlantické rozpětí: Eurozóna vs. Spojené státy (v bps)"
    else:
        if "us_10y" in dframe.columns and "bund_10y" in dframe.columns:
            diff_bps = (dframe["us_10y"] - dframe["bund_10y"]) * 100.0
            fig.add_trace(go.Scatter(
                x=dframe["date"], y=diff_bps, mode="lines",
                name="Spread 10Y (US Treasury − Německý Bund)", line=dict(color="#2563EB", width=2.5),
                hovertemplate="<b>Spread US 10Y - Bund</b>: %{y:+.0f} bps<extra></extra>"
            ))
        title_text = "Mezinárodní spread Spojených států (v bps)"

    fig.add_hline(y=0.0, line=dict(color="#64748B", width=1.5, dash="dash"), annotation_text="Parita výnosů (0 bps)", annotation_position="bottom left")
    fig.update_layout(
        title=dict(text=title_text, font=dict(size=14, color="#1E293B")),
        height=380, hovermode="x unified", margin=dict(l=20, r=20, t=45, b=20),
        xaxis=dict(title="", showgrid=True, gridcolor="#F1F5F9"),
        yaxis=dict(title="Rozpětí (bps)", ticksuffix=" bps", showgrid=True, gridcolor="#F1F5F9"),
        plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF"
    )
    return fig


# --- K. PŘEDSTIHOVÉ UKAZATELE & SENTIMENT ---
def build_leading_indicators_chart(dframe: pd.DataFrame, region: str = "CZ") -> go.Figure:
    """Graf předstihových ukazatelů a ekonomického sentimentu."""
    from plotly.subplots import make_subplots
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    if region == "CZ":
        if "cz_pmi_manufacturing" in dframe.columns:
            fig.add_trace(go.Scatter(
                x=dframe["date"], y=dframe["cz_pmi_manufacturing"], mode="lines+markers",
                name="PMI v průmyslu ČR (S&P Global)", line=dict(color="#2563EB", width=2.8),
                marker=dict(size=4), hovertemplate="<b>PMI ČR</b>: %{y:.1f} bodů<extra></extra>"
            ), secondary_y=False)
        if "cz_confidence_composite" in dframe.columns:
            fig.add_trace(go.Scatter(
                x=dframe["date"], y=dframe["cz_confidence_composite"], mode="lines",
                name="Důvěra podnikatelů a spotřebitelů (ČSÚ)", line=dict(color="#059669", width=2.4, dash="dot"),
                hovertemplate="<b>Důvěra ČSÚ</b>: %{y:.1f} bodů<extra></extra>"
            ), secondary_y=True)
        fig.add_hline(y=50.0, line=dict(color="#DC2626", width=1.5, dash="dash"),
                      annotation_text="PMI 50 = Expanze / Kontrakce", annotation_position="bottom right", secondary_y=False)
        y1_title, y2_title = "PMI Index (50 = zlom)", "Důvěra ČSÚ (body)"
        chart_title = "Předstihové ukazatele ČR: PMI průmyslu (S&P Global) vs. Souhrnná důvěra (ČSÚ)"

    elif region == "EU":
        if "eu_composite_pmi" in dframe.columns:
            fig.add_trace(go.Scatter(
                x=dframe["date"], y=dframe["eu_composite_pmi"], mode="lines+markers",
                name="Composite PMI Eurozóny (HCOB/S&P)", line=dict(color="#2563EB", width=2.8),
                marker=dict(size=4), hovertemplate="<b>Composite PMI EU</b>: %{y:.1f} bodů<extra></extra>"
            ), secondary_y=False)
        if "eu_ifo_business_climate" in dframe.columns:
            fig.add_trace(go.Scatter(
                x=dframe["date"], y=dframe["eu_ifo_business_climate"], mode="lines",
                name="Německý Ifo index klimatu", line=dict(color="#D97706", width=2.4),
                hovertemplate="<b>Německý Ifo</b>: %{y:.1f} bodů<extra></extra>"
            ), secondary_y=True)
        fig.add_hline(y=50.0, line=dict(color="#DC2626", width=1.5, dash="dash"),
                      annotation_text="PMI 50 = Hranice růstu", annotation_position="bottom right", secondary_y=False)
        y1_title, y2_title = "Composite PMI (body)", "Ifo Index Německa (body)"
        chart_title = "Předstihové ukazatele EU: Composite PMI Eurozóny & Německý Ifo index podnikatelského klimatu"

    else: # US
        if "us_ism_manufacturing" in dframe.columns:
            fig.add_trace(go.Scatter(
                x=dframe["date"], y=dframe["us_ism_manufacturing"], mode="lines",
                name="ISM Index ve výrobě (Manufacturing)", line=dict(color="#2563EB", width=2.5),
                hovertemplate="<b>ISM Výroba</b>: %{y:.1f} bodů<extra></extra>"
            ), secondary_y=False)
        if "us_ism_services" in dframe.columns:
            fig.add_trace(go.Scatter(
                x=dframe["date"], y=dframe["us_ism_services"], mode="lines",
                name="ISM Index ve službách (Services)", line=dict(color="#059669", width=2.5),
                hovertemplate="<b>ISM Služby</b>: %{y:.1f} bodů<extra></extra>"
            ), secondary_y=False)
        if "us_michigan_sentiment" in dframe.columns:
            fig.add_trace(go.Scatter(
                x=dframe["date"], y=dframe["us_michigan_sentiment"], mode="lines",
                name="Spotřebitelský sentiment (Univ. of Michigan)", line=dict(color="#D97706", width=2.2, dash="dash"),
                hovertemplate="<b>Univ. of Michigan</b>: %{y:.1f} bodů<extra></extra>"
            ), secondary_y=True)
        fig.add_hline(y=50.0, line=dict(color="#DC2626", width=1.5, dash="dash"),
                      annotation_text="ISM 50 = Hranice expanze", annotation_position="bottom right", secondary_y=False)
        y1_title, y2_title = "ISM PMI (50 = zlom)", "Michigan Sentiment (body)"
        chart_title = "US Předstihové ukazatele: ISM Výroba, ISM Služby & Spotřebitelský sentiment Univ. of Michigan"

    fig.update_layout(
        title=dict(text=chart_title, font=dict(size=14, color="#1E293B")),
        height=420, hovermode="x unified", margin=dict(l=20, r=20, t=45, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(title="", showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(title=y1_title, showgrid=True, gridcolor="#f1f5f9"),
        yaxis2=dict(title=y2_title, showgrid=False),
        plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF"
    )
    return fig


# --- L. TRH PRÁCE & MZDY ---
def build_wages_chart(dframe: pd.DataFrame, region: str = "CZ") -> go.Figure:
    """Graf dynamiky mezd a reálného příjmu v porovnání s inflací."""
    fig = go.Figure()
    if region == "CZ":
        if "cz_nominal_wage_yoy" in dframe.columns:
            fig.add_trace(go.Scatter(
                x=dframe["date"], y=dframe["cz_nominal_wage_yoy"], mode="lines+markers",
                name="Průměrná hrubá mzda nominálně (YoY)", line=dict(color="#2563EB", width=2.8),
                hovertemplate="<b>Nominální mzda</b>: %{y:+.1f} %<extra></extra>"
            ))
        if "cz_real_wage_yoy" in dframe.columns:
            fig.add_trace(go.Scatter(
                x=dframe["date"], y=dframe["cz_real_wage_yoy"], mode="lines",
                name="Průměrná reálná mzda (YoY)", line=dict(color="#059669", width=2.6),
                fill="tozeroy", fillcolor="rgba(5, 150, 105, 0.12)",
                hovertemplate="<b>Reálná mzda</b>: %{y:+.1f} %<extra></extra>"
            ))
        if "cpi_yoy" in dframe.columns:
            fig.add_trace(go.Scatter(
                x=dframe["date"], y=dframe["cpi_yoy"], mode="lines",
                name="Inflace CPI ČR (YoY)", line=dict(color="#DC2626", width=2.0, dash="dash"),
                hovertemplate="<b>Inflace CPI</b>: %{y:.1f} %<extra></extra>"
            ))
        title_text = "Vývoj mezd v ČR: Nominální vs. Reálná mzda (očištěná o inflaci CPI)"

    elif region == "EU":
        if "eu_negotiated_wages_yoy" in dframe.columns:
            fig.add_trace(go.Scatter(
                x=dframe["date"], y=dframe["eu_negotiated_wages_yoy"], mode="lines+markers",
                name="Sjednané mzdy Eurozóny (ECB YoY)", line=dict(color="#2563EB", width=2.8),
                hovertemplate="<b>Sjednané mzdy EU</b>: %{y:+.1f} %<extra></extra>"
            ))
        if "eu_cpi_yoy" in dframe.columns:
            fig.add_trace(go.Scatter(
                x=dframe["date"], y=dframe["eu_cpi_yoy"], mode="lines",
                name="Harmonizovaná inflace EU (HICP)", line=dict(color="#DC2626", width=2.0, dash="dash"),
                hovertemplate="<b>Inflace HICP</b>: %{y:.1f} %<extra></extra>"
            ))
        title_text = "Mzdový růst v Eurozóně: Sjednané mzdy (ECB) vs. Harmonizovaná inflace HICP"

    else: # US
        if "us_hourly_earnings_yoy" in dframe.columns:
            fig.add_trace(go.Scatter(
                x=dframe["date"], y=dframe["us_hourly_earnings_yoy"], mode="lines+markers",
                name="Průměrná hodinová mzda USA (Average Hourly Earnings YoY)", line=dict(color="#2563EB", width=2.8),
                hovertemplate="<b>Hodinová mzda USA</b>: %{y:+.1f} %<extra></extra>"
            ))
        if "us_cpi_yoy" in dframe.columns:
            fig.add_trace(go.Scatter(
                x=dframe["date"], y=dframe["us_cpi_yoy"], mode="lines",
                name="Headline CPI USA (YoY)", line=dict(color="#DC2626", width=2.0, dash="dash"),
                hovertemplate="<b>Inflace USA</b>: %{y:.1f} %<extra></extra>"
            ))
        title_text = "Trh práce USA: Růst hodinových výdělků vs. Inflace CPI"

    fig.add_hline(y=0.0, line=dict(color="#64748B", width=1.0, dash="solid"))
    fig.update_layout(
        title=dict(text=title_text, font=dict(size=14, color="#1E293B")),
        height=400, hovermode="x unified", margin=dict(l=20, r=20, t=45, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(title="", showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(title="Meziroční změna (%)", ticksuffix=" %", showgrid=True, gridcolor="#f1f5f9"),
        plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF"
    )
    return fig


# --- M. BANKOVNÍ SEKTOR, ÚVĚRY & M2 ---
def build_banking_and_loans_chart(dframe: pd.DataFrame) -> go.Figure:
    """Graf bankovního sektoru ČR: Nové hypotéky (objem a sazba), korporátní úvěry a M2."""
    from plotly.subplots import make_subplots
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    if "cz_mortgage_volume_czk_bn" in dframe.columns:
        fig.add_trace(go.Bar(
            x=dframe["date"], y=dframe["cz_mortgage_volume_czk_bn"],
            name="Nové hypotéky – objem (mld. Kč)",
            marker_color="rgba(37, 99, 235, 0.40)",
            hovertemplate="<b>Objem hypoték</b>: %{y:.1f} mld. Kč<extra></extra>"
        ), secondary_y=False)

    if "cz_mortgage_rate" in dframe.columns:
        fig.add_trace(go.Scatter(
            x=dframe["date"], y=dframe["cz_mortgage_rate"], mode="lines+markers",
            name="Průměrná sazba nových hypoték (% p.a.)", line=dict(color="#DC2626", width=2.8),
            marker=dict(size=4), hovertemplate="<b>Hypoteční sazba</b>: %{y:.2f} % p.a.<extra></extra>"
        ), secondary_y=True)

    if "cz_corporate_loans_yoy" in dframe.columns:
        fig.add_trace(go.Scatter(
            x=dframe["date"], y=dframe["cz_corporate_loans_yoy"], mode="lines",
            name="Korporátní úvěry (YoY)", line=dict(color="#059669", width=2.4),
            hovertemplate="<b>Podnikové úvěry</b>: %{y:+.1f} %<extra></extra>"
        ), secondary_y=True)

    if "cz_m2_growth_yoy" in dframe.columns:
        fig.add_trace(go.Scatter(
            x=dframe["date"], y=dframe["cz_m2_growth_yoy"], mode="lines",
            name="Měnový agregát M2 (YoY)", line=dict(color="#7C3AED", width=2.2, dash="dash"),
            hovertemplate="<b>Růst M2</b>: %{y:+.1f} %<extra></extra>"
        ), secondary_y=True)

    fig.update_layout(
        title=dict(text="Bankovní sektor ČR: Hypotéky (objem v mld. Kč & sazba % p.a.), korporátní úvěry a peněžní zásoba M2", font=dict(size=14, color="#1E293B")),
        height=420, hovermode="x unified", margin=dict(l=20, r=20, t=45, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(title="", showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(title="Objem nových hypoték (mld. Kč)", ticksuffix=" mld.", showgrid=True, gridcolor="#f1f5f9"),
        yaxis2=dict(title="Sazby & Růst (%)", ticksuffix=" %", showgrid=False),
        plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF"
    )
    return fig


# --- N. VNĚJŠÍ ROVNOVÁHA & OBCHODNÍ BILANCE ---
def build_external_balance_chart(dframe: pd.DataFrame) -> go.Figure:
    """Graf vnější rovnováhy ČR: Běžný účet k HDP a bilance zahraničního obchodu ČSÚ."""
    from plotly.subplots import make_subplots
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    if "cz_trade_balance_czk_bn" in dframe.columns:
        bar_colors = ["#059669" if val >= 0 else "#DC2626" for val in dframe["cz_trade_balance_czk_bn"]]
        fig.add_trace(go.Bar(
            x=dframe["date"], y=dframe["cz_trade_balance_czk_bn"],
            name="Měsíční saldo zahraničního obchodu ČSÚ (mld. Kč)",
            marker_color=bar_colors,
            hovertemplate="<b>Obchodní bilance</b>: %{y:+.1f} mld. Kč<extra></extra>"
        ), secondary_y=False)

    if "cz_current_account_gdp_pct" in dframe.columns:
        fig.add_trace(go.Scatter(
            x=dframe["date"], y=dframe["cz_current_account_gdp_pct"], mode="lines+markers",
            name="Běžný účet platební bilance (% HDP)", line=dict(color="#2563EB", width=3.0),
            marker=dict(size=5, color="#2563EB"),
            hovertemplate="<b>Běžný účet / HDP</b>: %{y:+.1f} %<extra></extra>"
        ), secondary_y=True)

    fig.add_hline(y=0.0, line=dict(color="#64748B", width=1.2, dash="dash"), secondary_y=False)
    fig.update_layout(
        title=dict(text="Vnější rovnováha ČR: Bilance zahraničního obchodu (ČSÚ) & Běžný účet (% HDP)", font=dict(size=14, color="#1E293B")),
        height=420, hovermode="x unified", margin=dict(l=20, r=20, t=45, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(title="", showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(title="Obchodní bilance (mld. Kč)", ticksuffix=" mld.", showgrid=True, gridcolor="#f1f5f9"),
        yaxis2=dict(title="Běžný účet (% HDP)", ticksuffix=" %", showgrid=False),
        plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF"
    )
    return fig


# --- O. KREDITNÍ & SPREADOVÉ UKAZATELE ---
def build_credit_spreads_chart(dframe: pd.DataFrame, region: str = "CZ") -> go.Figure:
    """Graf kreditních a suverénních spreadů (CZGB vs. Bund, ASW 10Y CZK, BTP vs. Bund)."""
    fig = go.Figure()
    if region == "CZ":
        if "czgb_bund_spread_10y" in dframe.columns:
            fig.add_trace(go.Scatter(
                x=dframe["date"], y=dframe["czgb_bund_spread_10y"], mode="lines",
                name="Kreditní spread 10Y CZGB vs. 10Y Bund", line=dict(color="#2563EB", width=2.8),
                hovertemplate="<b>Spread CZGB - Bund</b>: %{y:+.0f} bps<extra></extra>"
            ))
        if "cz_asw_10y_spread" in dframe.columns:
            fig.add_trace(go.Scatter(
                x=dframe["date"], y=dframe["cz_asw_10y_spread"], mode="lines",
                name="Asset Swap Spread (ASW 10Y CZK)", line=dict(color="#D97706", width=2.2, dash="dash"),
                hovertemplate="<b>ASW 10Y CZK</b>: %{y:+.0f} bps<extra></extra>"
            ))
        title_text = "Dluhopisové a swapové spready ČR: 10Y CZGB vs. Bund & Asset Swap Spread (ASW 10Y CZK)"

    else: # EU
        if "eu_btp_bund_spread" in dframe.columns:
            fig.add_trace(go.Scatter(
                x=dframe["date"], y=dframe["eu_btp_bund_spread"], mode="lines",
                name="Rizikový spread Itálie vs. Německo (10Y BTP - Bund)", line=dict(color="#DC2626", width=2.8),
                hovertemplate="<b>Spread 10Y BTP - Bund</b>: %{y:+.0f} bps<extra></extra>"
            ))
        fig.add_hline(y=200.0, line=dict(color="#D97706", width=1.5, dash="dot"),
                      annotation_text="Zvýšené periferní riziko (200 bps)", annotation_position="top left")
        title_text = "Dluhopisové rizikové spready Eurozóny: Itálie (BTP) vs. Německo (Bund) 10Y"

    fig.add_hline(y=0.0, line=dict(color="#64748B", width=1.0, dash="dash"))
    fig.update_layout(
        title=dict(text=title_text, font=dict(size=14, color="#1E293B")),
        height=390, hovermode="x unified", margin=dict(l=20, r=20, t=45, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(title="", showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(title="Rozpětí (bps)", ticksuffix=" bps", showgrid=True, gridcolor="#f1f5f9"),
        plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF"
    )
    return fig


# --- P. TRŽNÍ SENTIMENT & VOLATILITA (VIX) ---
def build_vix_chart(dframe: pd.DataFrame) -> go.Figure:
    """Graf Cboe Volatility Index VIX s barevnými zónami tržního sentimentu a stresu."""
    fig = go.Figure()
    if "vix_index" in dframe.columns:
        fig.add_trace(go.Scatter(
            x=dframe["date"], y=dframe["vix_index"], mode="lines",
            name="Index volatility VIX (Cboe)", line=dict(color="#0F172A", width=2.8),
            hovertemplate="<b>VIX Index</b>: %{y:.1f} bodů<extra></extra>"
        ))

    # Barevná referenční pásma sentimentu
    fig.add_hrect(y0=0, y1=15, fillcolor="rgba(16, 185, 129, 0.12)", line_width=0,
                  annotation_text="Klid & Býčí sentiment (<15)", annotation_position="top left", annotation_font_size=11)
    fig.add_hrect(y0=15, y1=20, fillcolor="rgba(245, 158, 11, 0.10)", line_width=0,
                  annotation_text="Normální volatilita (15–20)", annotation_position="top left", annotation_font_size=11)
    fig.add_hrect(y0=20, y1=30, fillcolor="rgba(239, 68, 68, 0.12)", line_width=0,
                  annotation_text="Zvýšená nervozita & riziko (20–30)", annotation_position="top left", annotation_font_size=11)
    fig.add_hrect(y0=30, y1=70, fillcolor="rgba(185, 28, 28, 0.20)", line_width=0,
                  annotation_text="Extrémní stres & panika (>30)", annotation_position="top left", annotation_font_size=11)

    fig.update_layout(
        title=dict(text="Index volatility Cboe VIX ('Index strachu') a režimy tržního sentimentu", font=dict(size=14, color="#1E293B")),
        height=410, hovermode="x unified", margin=dict(l=20, r=20, t=45, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(title="", showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(title="VIX Index (body)", showgrid=True, gridcolor="#f1f5f9", range=[8, 65]),
        plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF"
    )
    return fig


# =============================================================================
# 9. PŘÍPRAVA DAT PRO EXPORT
# =============================================================================

cols_to_display = ["date"]
if "quarter" in df.columns and frequency_code == "Q":
    cols_to_display.append("quarter")

for col in selected_indicators:
    if col in df.columns and col not in cols_to_display:
        cols_to_display.append(col)

df_export = df[cols_to_display].copy()
rename_dict = {"date": "Datum", "quarter": "Kvartál"}
for col in selected_indicators:
    info = INDICATORS.get(col)
    if info:
        rename_dict[col] = f"{info.name_cz} [{info.unit}]"

df_export_active = df_export.rename(columns=rename_dict)
df_export_active["Datum"] = df_export_active["Datum"].dt.strftime("%d.%m.%Y")


# =============================================================================
# 9b. AKTUÁLNÍ FINANČNÍ ZPRAVODAJSTVÍ A METODICKÝ KATALOG PRO ČESKOU REPUBLIKU
# =============================================================================

CZ_NEWS = {
    "rates": {
        "tag": "MĚNOVÁ POLITIKA ČNB & SAZBY",
        "date": "Poslední zasedání Bankovní rady ČNB",
        "source": "Česká národní banka (Tisková konference guvernéra A. Michla) / ČTK",
        "title": "Bankovní rada ČNB pozvolna uvolňuje měnovou politiku: 2T repo sazba upravena na 4,00 % / 3,75 %",
        "reason": "Pokles celkové spotřebitelské inflace k 2% cíli vytvořil prostor pro uvolnění měnových podmínek. Bankovní rada však tempo snižování záměrně rozvolnila na standardních 25 bazických bodů.",
        "context": "Guvernér ČNB zdůraznil, že boj s inflací nekončí. Proinflačním rizikem zůstává setrvačnost v cenách služeb a oživení mzdového růstu. Měnová politika zůstane v mírně restriktivním pásmu déle, než trhy původně očekávaly, aby se zabránilo opětovnému vzplanutí inflačních očekávání."
    },
    "yield_curve": {
        "tag": "DLUHOPISOVÝ TRH & VÝNOSY",
        "date": "Poslední aukce státních dluhopisů MF ČR",
        "source": "Ministerstvo financí ČR (Měsíční zpráva o řízení dluhu) / Patria Finance",
        "title": "Napřimování české výnosové křivky: 10letý dluhopis CZGB se drží u 4,10 %, odeznívá inverze",
        "reason": "S poklesem krátkodobých sazeb ČNB klesají výnosy na 2letém tenoru, zatímco dlouhý konec křivky (10Y až 15Y) zůstává ukotven vyšší emisní aktivitou státu k profinancování schodku rozpočtu.",
        "context": "Po téměř dvou letech hluboké inverze se křivka státních dluhopisů CZGB vrací k přirozenému pozitivnímu sklonu (un-inversion). Poptávka domácích i zahraničních institucionálních investorů v aukcích MF ČR zůstává silná s průměrným přeupsáním 1,8×."
    },
    "fx": {
        "tag": "DEVIZOVÝ TRH & KURZ KORUNY",
        "date": "Denní fixace ČNB / Mezibankovní FX trh",
        "source": "Česká národní banka (Denní devizový trh) / Hospodářské noviny Byznys",
        "title": "Česká koruna se stabilizuje v pásmu 25,15–25,30 EUR/CZK, vůči dolaru odráží sílu americké měny",
        "reason": "Koruně poskytuje oporu přetrvávající kladný úrokový diferenciál ČNB vůči ECB (+0,75 až +1,00 p.b.) a ujištění bankovní rady o připravenosti kurz v případě výkyvů stabilizovat.",
        "context": "Vůči americkému dolaru (USD/CZK kolem 23,20–23,60) kurz kolísá v závislosti na globálním makru a geopolitice. Vývozci hlásí stabilní zajištění, zatímco silnější koruna pomáhá tlumit importovanou inflaci u energetických a technologických dovozů."
    },
    "gdp": {
        "tag": "NÁRODNÍ ÚČTY & HOSPODÁŘSKÝ RŮST",
        "date": "Poslední Rychlá informace ČSÚ o HDP",
        "source": "Český statistický úřad (ČSÚ) / Analytici České bankovní asociace (ČBA)",
        "title": "Česká ekonomika zrychluje: Meziroční růst HDP dosáhl 2,6 %, tahounem je spotřeba domácností",
        "reason": "Hlavním motorem oživení po předchozí stagnaci je obnova reálných příjmů domácností a odložená spotřeba. K růstu pozitivně přispěla i hrubá tvorba fixního kapitálu a stavebnictví.",
        "context": "Česká ekonomika se vymanila z recese nejpozději v regionu střední Evropy, avšak aktuální dynamika překonává tempo eurozóny. Zahraniční poptávka zůstává mírně tlumena slabším výkonem německého průmyslu, čistý export nicméně vykazuje kladné saldo."
    },
    "inflation": {
        "tag": "SPOTŘEBITELSKÉ CENY & INFLACE",
        "date": "Poslední Rychlá informace ČSÚ o indexech spotřebitelských cen",
        "source": "Český statistický úřad (ČSÚ) / Měnová sekce ČNB / Patria.cz",
        "title": "Meziroční inflace se drží v tolerančním pásmu ČNB (1,8–2,4 %), jádrová inflace mírně zvýšená vlivem služeb",
        "reason": "Pokles celkové inflace byl podpořen odezněním energetického šoku, stabilizací cen pohonných hmot a mírným meziměsíčním poklesem cen potravin. Naopak jádrová inflace vykazuje vyšší setrvačnost (kolem 2,2 %).",
        "context": "Vývoj potvrzuje úspěšné zkrocení dvouciferné inflace z let 2022–2023. Hlavní pozornost ČNB se nyní přesouvá k cenám ve službách (nájemné, pohostinství, rekreace), kde firmy promítají rostoucí mzdové náklady, což brání agresivnějšímu snižování úrokových sazeb."
    },
    "retail_industry": {
        "tag": "KONJUNKTURA: SPOTŘEBA & PRŮMYSL",
        "date": "Poslední měsíční data ČSÚ (Průmysl a Maloobchod)",
        "source": "Český statistický úřad (ČSÚ) / Svaz průmyslu a dopravy ČR / E15",
        "title": "Maloobchodní tržby rostou o 4,5 % s oživením nákupů, průmysl vykazuje smíšené signály",
        "reason": "Růst reálných mezd vedl ke znatelnému zvýšení útrat za nepotravinářské zboží, elektroniku a online nákupy. V průmyslu táhne výrobu automobilový sektor (+5 % YoY), zatímco energeticky náročná odvětví stagnují.",
        "context": "Data potvrzují dvourychlostní charakter ekonomiky – spotřebitelská poptávka domácností a služby prudce rostou, avšak exportně orientovaný těžký průmysl a strojírenství čelí poklesu nových zakázek z Německa a vysokým nákladům na dekarbonizaci."
    },
    "unemployment": {
        "tag": "TRH PRÁCE & ZAMĚSTNANOST",
        "date": "Poslední statistika MPSV a ČSÚ",
        "source": "Ministerstvo práce a sociálních věcí (MPSV) / Eurostat / Seznam Zprávy",
        "title": "Míra nezaměstnanosti v ČR činí 3,8 %, Česko si drží jednu z nejnižších úrovní v celé Evropské unii",
        "reason": "Vysoká míra zaměstnanosti a flexibilita podniků udržují počet evidovaných uchazečů na nízkých stavech (kolem 275–285 tisíc osob), srovnatelně s počtem hlášených volných pracovních míst.",
        "context": "Strukturální nedostatek techniků, řemeslníků a kvalifikovaných dělníků přetrvává napříč všemi regiony. Tento převis poptávky nutí firmy zvyšovat nominální mzdy o 6–7 % ročně, což představuje hlavní proinflační faktor pečlivě sledovaný ČNB."
    },
    "stocks_px": {
        "tag": "AKCIOVÉ TRHY & BCPP",
        "date": "Aktuální obchodování Burzy cenných papírů Praha",
        "source": "Burza cenných papírů Praha (BCPP / PSE) / Analytici Patria Finance",
        "title": "Index PX překonal hranici 1 700 bodů a útočí na mnohaletá maxima tažen bankovními tituly",
        "reason": "Rekordní ziskovost a štědré dividendy bank (Erste Group, Komerční banka, Moneta) lákají domácí i zahraniční investory. Titul ČEZ poskytuje stabilitu při vysokých realizačních cenách elektřiny.",
        "context": "Pražská burza patří v posledních dvou letech k nejvýkonnějším trhům v Evropě s celkovým dividendovým výnosem přes 7 % p.a. Příznivý sentiment podporuje také zařazení nových emisí (Colt CZ, Gevorkyan) a stabilní makroekonomické prostředí v ČR."
    },
    "debt": {
        "tag": "FISKÁLNÍ POLITIKA & STÁTNÍ ROZPOČET",
        "date": "Poslední pokladní plnění MF ČR & Notifikace vládního dluhu",
        "source": "Ministerstvo financí ČR (Zpráva o plnění státního rozpočtu) / Eurostat",
        "title": "Vládní dluh ČR činí 44,2 % HDP, konsolidační balíček přispívá ke snižování strukturálního deficitu",
        "reason": "Zavedení ozdravného vládního balíčku (úprava sazeb DPH, snížení dotací a výdajových škrtů) stabilizovalo hospodaření státu a drží celkové zadlužení hluboko pod 60% limitem Maastrichtských kritérií.",
        "context": "I přes relativně nízký poměr k HDP v porovnání s průměrem EU (cca 82 % HDP) zůstává výzvou absolutní výše dluhu (přes 3,3 bilionu Kč) a rostoucí náklady na obsluhu státního dluhu, které se pohybují kolem 90–95 miliard Kč ročně."
    },
    "intl_spread": {
        "tag": "SOVEREIGN SPREADY & MEZINÁRODNÍ TRHY",
        "date": "Aktuální dluhopisové spready na evropském trhu",
        "source": "Bloomberg / Reuters / Analýza ČNB",
        "title": "Výnosový spread CZGB vůči německému Bundu se stabilizuje kolem 180–200 bazických bodů",
        "reason": "Rozpětí odráží rozdíl v úrokových sazbách mezi ČNB a ECB a specifickou rizikovou prémii korunového trhu mimo eurozónu.",
        "context": "Přestože ČR má výrazně nižší poměr veřejného dluhu než většina zemí jižního křídla eurozóny, spread vůči Německu zůstává kladný zejména kvůli vyšší inflační zkušenosti z minulých let a samostatné měnové politice."
    },
    "leading": {
        "tag": "PŘEDSTIHOVÉ UKAZATELE & KONJUNKTURA",
        "date": "Poslední zpráva S&P Global PMI & Konjunkturální průzkum ČSÚ",
        "source": "S&P Global / Český statistický úřad (ČSÚ) / Hospodářské noviny",
        "title": "PMI v průmyslu ČR se blíží hranici 50 bodů, sentiment podnikatelů a spotřebitelů roste",
        "reason": "Zpomalení poklesu nových zakázek a postupné oživení poptávky v automotive a elektrotechnice pomáhá českému průmyslu odrazit se ze dna.",
        "context": "Index nákupních manažerů (PMI) vystoupal z dřívějších útlumových hodnot k prahové hodnotě 50 bodů oddělující kontrakci od expanze. Souhrnný indikátor důvěry ČSÚ potvrzuje výrazné zlepšení optimismu spotřebitelů díky klesající inflaci a růstu reálných příjmů."
    },
    "wages": {
        "tag": "TRH PRÁCE & MZDOVÝ VÝVOJ",
        "date": "Poslední čtvrtletní statistika ČSÚ o mzdách",
        "source": "Český statistický úřad (ČSÚ) / Analytici ČNB",
        "title": "Průměrná hrubá mzda v ČR roste o 7,2 %, reálné mzdy po dvou letech propadu zřetelně posilují",
        "reason": "Při odeznění inflace na 2% úroveň se nominální růst mezd (cca 7,2 % YoY) přímo transformuje do růstu reálné kupní síly zaměstnanců (+4,5 až +5,0 % YoY).",
        "context": "Návrat k reálnému růstu mezd obnovuje kupní sílu obyvatelstva a pohání maloobchodní tržby. ČNB však pečlivě monitoruje mzdovou dynamiku ve službách, aby zamezila vzniku nebezpečné mzdově-inflační spirály."
    },
    "banking": {
        "tag": "BANKOVNÍ SEKTOR & ÚVĚROVÝ TRH",
        "date": "Poslední ČBA Hypomonitor & Měnová statistika ČNB",
        "source": "Česká bankovní asociace (ČBA) / Česká národní banka (ARAD)",
        "title": "Hypoteční trh ožívá: Průměrná úroková sazba klesá pod 5 %, objem nových hypoték roste",
        "reason": "Pokles základních úrokových sazeb ČNB a redukce nákladů bank na mezibankovním trhu (IRS swapy) umožnily zlevnění hypotečních úvěrů a uvolnění odložené poptávky po vlastnickém bydlení.",
        "context": "Měsíční objem nově poskytnutých hypoték přesahuje 20 miliard Kč. Současně korporátní úvěry vykazují solidní meziroční růst kolem 6–7 %, což dokládá chuť tuzemských firem financovat investice do modernizace a automatizace."
    },
    "external": {
        "tag": "VNĚJŠÍ ROVNOVÁHA & ZAHRANIČNÍ OBCHOD",
        "date": "Poslední měsíční data zahraničního obchodu ČSÚ & Platební bilance ČNB",
        "source": "Český statistický úřad (ČSÚ) / Česká národní banka (ČNB)",
        "title": "Zahraniční obchod ČR generuje silné přebytky, běžný účet platební bilance se vrací do plusu",
        "reason": "Zlevnění dovážených energetických komodit (ropa, zemní plyn) v kombinaci s vysokou exportní výkonností výrobců motorových vozidel vedly k citelnému zlepšení obchodního salda.",
        "context": "Přebytek běžného účtu kolem 1,5 % HDP vytváří přirozený fundamentální tlak na stabilitu či mírné posilování české koruny a potvrzuje odolnost proexportního modelu české ekonomiky vůči externím šokům."
    }
}


def render_cz_news_card(news_item: Optional[Dict[str, str]]):
    """Vykreslí přehlednou kartu s nejnovější finanční zprávou a makroekonomickým kontextem pod metrikami."""
    if not news_item:
        return
    st.markdown(
        f"""
        <div class="macro-news-card">
            <div class="macro-news-top">
                <div class="macro-news-tag">
                    <span class="news-dot"></span>
                    <span>{news_item.get('tag', 'AKTUÁLNÍ ZPRÁVA')}</span>
                </div>
                <div class="macro-news-meta">
                    <span>📅 {news_item.get('date', '')}</span>
                    <span>•</span>
                    <span>🗞️ {news_item.get('source', '')}</span>
                </div>
            </div>
            <div class="macro-news-headline">{news_item.get('title', '')}</div>
            <div class="macro-news-content">
                <div class="news-section-item">
                    <span class="news-label">🔍 Důvod změny & klíčové faktory:</span>
                    <span class="news-text">{news_item.get('reason', '')}</span>
                </div>
                <div class="news-section-item">
                    <span class="news-label">📊 Makroekonomický kontext:</span>
                    <span class="news-text">{news_item.get('context', '')}</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def get_indicators_catalog_df() -> pd.DataFrame:
    """Sestaví kompletní přehledný katalog všech indikátorů se zdroji a frekvencí."""
    catalog_rows = []

    def resolve_source(code: str, category: str, region: str) -> str:
        if region == "CZ":
            if "pmi" in code:
                return "S&P Global"
            if "confidence" in code:
                return "Český statistický úřad (ČSÚ – Konjunkturální průzkum)"
            if any(k in code for k in ["nominal_wage", "real_wage"]):
                return "Český statistický úřad (ČSÚ – Statistika práce)"
            if "mortgage" in code:
                return "Česká bankovní asociace (ČBA Hypomonitor) & ČNB"
            if "corporate_loans" in code:
                return "Česká národní banka (ARAD – Měnová statistika)"
            if "m2" in code:
                return "Česká národní banka (Statistika peněžního oběhu)"
            if "current_account" in code:
                return "Česká národní banka (Platební bilance) & ČSÚ"
            if "trade_balance" in code:
                return "Český statistický úřad (ČSÚ – Zahraniční obchod)"
            if "czgb_bund" in code:
                return "Ministerstvo financí ČR / Deutsche Bundesbank / Eurostat"
            if "asw" in code:
                return "Mezibankovní trh (CZGB vs. CZK IRS) & ČNB"
            if any(k in code for k in ["repo", "discount", "lombard", "pribor"]):
                return "Česká národní banka (ČNB)"
            if any(k in code for k in ["cpi"]):
                return "Český statistický úřad (ČSÚ) & ČNB"
            if any(k in code for k in ["gdp", "retail", "industrial"]):
                return "Český statistický úřad (ČSÚ)"
            if code == "unemployment_rate":
                return "Ministerstvo práce a sociálních věcí (MPSV) & ČSÚ"
            if any(k in code for k in ["eur_czk", "usd_czk", "pln_czk", "gbp_czk", "chf_czk", "jpy_czk"]):
                return "Česká národní banka (ČNB - Denní devizový trh)"
            if any(k in code for k in ["public_debt", "budget_deficit", "czgb_"]):
                return "Ministerstvo financí ČR (MF ČR)"
            if "irs_" in code:
                return "Mezibankovní trh (CZK Interest Rate Swaps)"
            if "px_" in code:
                return "Burza cenných papírů Praha (BCPP / PSE)"
            return "Česká národní banka / ČSÚ"

        elif region == "EU":
            if "ifo" in code:
                return "Ifo Institut Mnichov (ifo Geschäftsklimaindex)"
            if "composite_pmi" in code:
                return "S&P Global & Hamburg Commercial Bank (HCOB)"
            if "negotiated_wages" in code:
                return "Evropská centrální banka (ECB Negotiated Wages)"
            if "btp_bund" in code:
                return "MTS Italy, Deutsche Bundesbank & Banca d'Italia"
            if any(k in code for k in ["ecb_", "estr"]):
                return "Evropská centrální banka (ECB)"
            if "euribor" in code:
                return "European Money Markets Institute (EMMI) & ECB"
            if any(k in code for k in ["eu_cpi", "eu_core_cpi"]):
                return "Eurostat (HICP Harmonizovaná inflace)"
            if any(k in code for k in ["eu_gdp", "eu_retail", "eu_industrial", "eu_unemployment", "eu_public_debt", "eu_budget_deficit"]):
                return "Eurostat (Evropská komise)"
            if "bund_" in code:
                return "Deutsche Bundesbank & Eurostat"
            if any(k in code for k in ["eur_usd", "eur_pln", "eur_gbp"]):
                return "Evropská centrální banka (ECB Reference Rates)"
            if "stoxx" in code:
                return "STOXX Ltd. (Deutsche Börse Group) & Yahoo Finance"
            return "Eurostat & ECB"

        else: # US
            if "ism_" in code:
                return "Institute for Supply Management (ISM)"
            if "michigan" in code:
                return "University of Michigan (Surveys of Consumers)"
            if "hourly_earnings" in code:
                return "U.S. Bureau of Labor Statistics (BLS)"
            if "vix" in code:
                return "Chicago Board Options Exchange (Cboe VIX) & Yahoo Finance"
            if any(k in code for k in ["fed_funds", "effr", "us_industrial"]):
                return "Federal Reserve Board (Fed)"
            if "sofr" in code:
                return "Federal Reserve Bank of New York (NY Fed)"
            if any(k in code for k in ["us_cpi", "us_core_cpi", "us_unemployment"]):
                return "U.S. Bureau of Labor Statistics (BLS)"
            if "us_gdp" in code:
                return "U.S. Bureau of Economic Analysis (BEA)"
            if "us_retail" in code:
                return "U.S. Census Bureau"
            if any(k in code for k in ["us_1m", "us_3m", "us_6m", "us_1y", "us_2y", "us_3y", "us_5y", "us_7y", "us_10y", "us_20y", "us_30y", "us_spread", "us_public_debt", "us_budget_deficit"]):
                return "U.S. Department of the Treasury"
            if any(k in code for k in ["dxy", "usd_jpy", "gbp_usd", "usd_pln", "usd_chf"]):
                return "Intercontinental Exchange (ICE) & FX trhy"
            if "sp500" in code:
                return "S&P Dow Jones Indices & Yahoo Finance"
            if "nasdaq" in code:
                return "NASDAQ OMX Group & Yahoo Finance"
            return "U.S. Federal Agencies & Financial Markets"

    def resolve_frequency(code: str, category: str) -> str:
        if any(k in code for k in ["eur_czk", "usd_czk", "pln_czk", "gbp_czk", "chf_czk", "jpy_czk", "eur_usd", "eur_pln", "eur_gbp", "dxy", "usd_jpy", "gbp_usd", "usd_pln", "usd_chf"]):
            return "Denní (D) & Měsíční (M)"
        if any(k in code for k in ["pribor", "euribor", "estr", "sofr", "effr", "vix_index"]):
            return "Denní (D) & Měsíční (M)"
        if any(k in code for k in ["czgb_", "bund_", "us_1m", "us_3m", "us_6m", "us_1y", "us_2y", "us_3y", "us_5y", "us_7y", "us_10y", "us_20y", "us_30y", "czgb_bund", "asw", "btp_bund"]):
            return "Denní (D) & Měsíční (M)"
        if any(k in code for k in ["px_index", "stoxx50_index", "sp500_index", "nasdaq_index"]):
            return "Denní (D) & Měsíční (M)"
        if "wage" in code:
            return "Kvartální (Q) & Měsíční (M)"
        if "gdp" in code or "debt" in code or "deficit" in code or "current_account" in code:
            return "Kvartální (Q)"
        return "Měsíční (M)"

    region_names = {
        "CZ": "🇨🇿 Česká republika",
        "EU": "🇪🇺 Evropská unie",
        "US": "🇺🇸 Spojené státy"
    }

    for code, info in INDICATORS.items():
        reg_title = region_names.get(info.region, info.region)
        src = resolve_source(code, info.category, info.region)
        freq = resolve_frequency(code, info.category)
        catalog_rows.append({
            "Země / Region": reg_title,
            "Kategorie": info.category,
            "Název ukazatele": info.name_cz,
            "Kód indikátoru": code,
            "Jednotka": info.unit,
            "Periodicita": freq,
            "Primární zdroj dat": src,
            "Metodický popis": info.description,
            "_region_code": info.region
        })

    return pd.DataFrame(catalog_rows)


# =============================================================================
# 10. ZÁLOŽKY DASHBOARDU (6 KATEGORIÍ VČETNĚ METODICKÉHO KATALOGU)
# =============================================================================

main_tab_markets, main_tab_real, main_tab_stocks, main_tab_public, main_tab_export, main_tab_catalog = st.tabs([
    "💳 Finanční trhy & Měna",
    "🏛️ Reálná ekonomika & Práce",
    "📈 Trhy",
    "🌐 Veřejné finance & Svět",
    "📋 Data a export",
    "📖 Seznam ukazatelů & Zdroje"
])


# =============================================================================
# 1. KATEGORIE: FINANČNÍ TRHY & MĚNA
# =============================================================================
with main_tab_markets:
    sub_tab_rates, sub_tab_curve, sub_tab_fx, sub_tab_banking = st.tabs([
        f"Sazby ({'ČNB' if is_cz else ('ECB' if is_eu else 'Fed')})",
        f"Výnosová křivka & Spready ({'CZ' if is_cz else ('Bund' if is_eu else 'US')})",
        "Měnové kurzy (FX)",
        f"Bankovní sektor & Úvěry ({'ČR' if is_cz else ('Eurozóna' if is_eu else 'USA')})"
    ])

    # 1.1 Úrokové sazby
    with sub_tab_rates:
        if is_cz:
            st.markdown('<div class="section-header">Měnová politika ČNB a mezibankovní sazby PRIBOR</div>', unsafe_allow_html=True)
            col_r1, col_r2, col_r3, col_r4 = st.columns(4)
            col_r1.metric("2T Repo sazba", f"{repo_curr:.2f} %", delta=f"{repo_delta:+.2f} p.b.", help="Hlavní nástroj stahování likvidity")
            col_r2.metric("Diskontní sazba", f"{disc_curr:.2f} %", help="Úročení vkladů bank u ČNB")
            col_r3.metric("Lombardní sazba", f"{lomb_curr:.2f} %", help="Úročení zápůjček likvidity")
            col_r4.metric("PRIBOR 3M", f"{prib3m_curr:.2f} %", help="Referenční tržní sazba")
            render_cz_news_card(CZ_NEWS["rates"])
            fig_rates = build_rates_chart(df, selected_indicators)
            render_plotly_chart(fig_rates, key="chart_cz_rates")
            st.caption("📌 **Zdroj dat:** Česká národní banka (ČNB) – Otevřená data měnové politiky & FinStat")

        elif is_eu:
            st.markdown('<div class="section-header">Měnová politika ECB a sazby EURIBOR / €STR</div>', unsafe_allow_html=True)
            col_er1, col_er2, col_er3, col_er4 = st.columns(4)
            col_er1.metric("Depozitní sazba ECB", f"{ecb_dep_curr:.2f} %", delta=f"{ecb_dep_delta:+.2f} p.b.")
            col_er2.metric("Refinanční sazba MRO", f"{ecb_refi_curr:.2f} %")
            col_er3.metric("Mezní sazba ECB", f"{ecb_lend_curr:.2f} %")
            col_er4.metric("EURIBOR 3M", f"{euribor3m_curr:.2f} %")
            fig_eu_rates = build_eu_rates_chart(df, selected_indicators)
            render_plotly_chart(fig_eu_rates, key="chart_eu_rates")
            st.caption("📌 **Zdroj dat:** Evropská centrální banka (ECB) & European Money Markets Institute (EMMI)")

        else:
            st.markdown('<div class="section-header">Měnová politika Federálního rezervního systému (Fed) & SOFR</div>', unsafe_allow_html=True)
            col_ur1, col_ur2, col_ur3, col_ur4 = st.columns(4)
            col_ur1.metric("Fed Funds Target Upper", f"{fed_upper_curr:.2f} %", delta=f"{fed_upper_delta:+.2f} p.b.")
            col_ur2.metric("Fed Funds Target Lower", f"{fed_lower_curr:.2f} %")
            col_ur3.metric("SOFR Rate", f"{sofr_curr:.2f} %")
            col_ur4.metric("3M T-Bill", f"{us3m_curr:.2f} %")
            fig_us_rates = build_us_rates_chart(df, selected_indicators)
            render_plotly_chart(fig_us_rates, key="chart_us_rates")
            st.caption("📌 **Zdroj dat:** Federal Reserve Board (EFFR / Target) & Federal Reserve Bank of New York (SOFR)")

    # 1.2 Výnosová křivka & Spready
    with sub_tab_curve:
        if is_cz:
            st.markdown('<div class="section-header">Výnosová křivka ČR (Státní dluhopisy CZGB & CZK IRS swapy)</div>', unsafe_allow_html=True)
            col_yc1, col_yc2, col_yc3, col_yc4 = st.columns(4)
            czgb10 = safe_metric(last_row, "czgb_10y", 4.10)
            czgb2 = safe_metric(last_row, "czgb_2y", 3.85)
            czgb_spread = czgb10 - czgb2
            irs10 = safe_metric(last_row, "irs_10y", 3.95)
            col_yc1.metric("10Y CZGB Výnos", f"{czgb10:.2f} %")
            col_yc2.metric("2Y CZGB Výnos", f"{czgb2:.2f} %")
            col_yc3.metric("Sklon (10Y − 2Y)", f"{czgb_spread:+.2f} p.b.", delta="Normální sklon" if czgb_spread >= 0 else "Inverze")
            col_yc4.metric("10Y CZK IRS Swap", f"{irs10:.2f} %")
            render_cz_news_card(CZ_NEWS["yield_curve"])
            comp_date_target = last_row["date"] - pd.DateOffset(years=1)
            comp_df = df_raw[df_raw["date"] <= comp_date_target]
            comp_row = comp_df.iloc[-1] if not comp_df.empty else None
            fig_curve_cz = build_yield_curve_snapshot(last_row, comp_row)
            render_plotly_chart(fig_curve_cz, key="chart_cz_yield_curve")
            st.caption("📌 **Zdroj dat:** Ministerstvo financí ČR (Dluhopisy CZGB) & Mezibankovní úrokové swapy CZK IRS")

            # Kreditní a swapové spready CZ
            st.markdown('<div class="section-header" style="margin-top: 24px;">Kreditní a swapové spready (CZGB vs. Bund & ASW 10Y CZK)</div>', unsafe_allow_html=True)
            col_sp1, col_sp2, col_sp3, col_sp4 = st.columns(4)
            col_sp1.metric("Kreditní spread 10Y CZGB vs. 10Y Bund", f"{czgb_bund_sp_curr:+.0f} bps", help="Přirážka českého 10Y dluhopisu vůči německému Bundu")
            col_sp2.metric("Asset Swap Spread (ASW 10Y CZK)", f"{cz_asw_curr:+.0f} bps", help="Rozdíl 10Y CZGB a sazby CZK IRS na mezibankovním trhu")
            col_sp3.metric("Výnos 10Y CZGB", f"{czgb10:.2f} %")
            col_sp4.metric("Výnos 10Y Německý Bund", f"{bund10_curr:.2f} %")
            fig_spreads_cz = build_credit_spreads_chart(df, region="CZ")
            render_plotly_chart(fig_spreads_cz, key="chart_cz_credit_spreads")
            st.caption("📌 **Zdroj dat:** Ministerstvo financí ČR (CZGB), Deutsche Bundesbank (Bund) & Refinitiv / Bloomberg")

        elif is_eu:
            st.markdown('<div class="section-header">Výnosová křivka Německých Bundů (Benchmark Eurozóny: 2Y–30Y)</div>', unsafe_allow_html=True)
            comp_date_target_eu = last_row["date"] - pd.DateOffset(years=1)
            comp_df_eu = df_raw[df_raw["date"] <= comp_date_target_eu]
            comp_row_eu = comp_df_eu.iloc[-1] if not comp_df_eu.empty else None
            fig_curve_eu = build_eu_yield_curve_snapshot(last_row, comp_row_eu)
            render_plotly_chart(fig_curve_eu, key="chart_eu_yield_curve")
            st.caption("📌 **Zdroj dat:** Deutsche Bundesbank & Eurostat (Government Bond Yields)")

            # Rizikový spread BTP - Bund
            st.markdown('<div class="section-header" style="margin-top: 24px;">Rizikový spread periferie Eurozóny: 10Y BTP (Itálie) vs. 10Y Bund (Německo)</div>', unsafe_allow_html=True)
            col_esp1, col_esp2, col_esp3, col_esp4 = st.columns(4)
            col_esp1.metric("Rizikový spread Itálie vs. Německo", f"{eu_btp_sp_curr:+.0f} bps", delta=f"{eu_btp_sp_curr - eu_btp_sp_prev:+.1f} bps", delta_color="inverse", help="10Y BTP − 10Y Bund - klíčový ukazatel fragmentace Eurozóny")
            col_esp2.metric("10Y Německý Bund (Kotva)", f"{bund10_curr:.2f} %")
            col_esp3.metric("10Y BTP Itálie (Implikovaný)", f"{bund10_curr + (eu_btp_sp_curr / 100.0):.2f} %")
            col_esp4.metric("Sledovaný práh ECB", "< 200 bps", help="Hranice aktivace nástroje TPI")
            fig_spreads_eu = build_credit_spreads_chart(df, region="EU")
            render_plotly_chart(fig_spreads_eu, key="chart_eu_credit_spreads")
            st.caption("📌 **Zdroj dat:** Banca d'Italia, Deutsche Bundesbank & Eurostat – Spready vládních dluhopisů")

        else:
            st.markdown('<div class="section-header">Výnosová křivka USA (U.S. Treasury Par Yield Curve: 1M–30Y)</div>', unsafe_allow_html=True)
            comp_date_target_us = last_row["date"] - pd.DateOffset(years=1)
            comp_df_us = df_raw[df_raw["date"] <= comp_date_target_us]
            comp_row_us = comp_df_us.iloc[-1] if not comp_df_us.empty else None
            fig_curve_us = build_us_yield_curve_snapshot(last_row, comp_row_us)
            render_plotly_chart(fig_curve_us, key="chart_us_yield_curve")
            st.caption("📌 **Zdroj dat:** U.S. Department of the Treasury (Daily Treasury Par Yield Curve Rates)")

    # 1.3 Měnové kurzy (FX) s výběrem měn
    with sub_tab_fx:
        st.markdown('<div class="section-header">Devizové trhy a měnové kurzy (Denní & Měsíční data)</div>', unsafe_allow_html=True)
        st.caption("Filtrujte zobrazené měny v grafu níže, aby byl přehledný a neobsahoval příliš mnoho překrývajících se křivek.")

        col_fx_ctrl1, col_fx_ctrl2 = st.columns([2.5, 1.5])
        with col_fx_ctrl1:
            fx_selected_currencies = st.multiselect(
                "Zvolte měny ke zobrazení:",
                options=["CZK", "EUR", "USD", "GBP", "PLN"],
                default=["EUR", "USD", "CZK"] if is_cz else (["EUR", "USD", "PLN"] if is_eu else ["USD", "EUR", "GBP"]),
                key="fx_currencies_multiselect",
                help="Vyberte měny, které se mají vykreslit do grafu."
            )
        with col_fx_ctrl2:
            fx_view_mode = st.radio(
                "Frekvence řady:",
                ["📅 Denní data (High-Frequency)", "📊 Měsíční agregace"],
                horizontal=True,
                key="fx_freq_view_mode"
            )

        df_for_fx_plot = df_daily_fx_filtered if "Denní" in fx_view_mode else df

        # Summary metriky pro FX
        col_fx1, col_fx2, col_fx3, col_fx4 = st.columns(4)
        if is_cz:
            col_fx1.metric("EUR / CZK", f"{daily_eur_czk:.2f} Kč")
            col_fx2.metric("USD / CZK", f"{daily_usd_czk:.2f} Kč")
            col_fx3.metric("PLN / CZK", f"{daily_pln_czk:.2f} Kč")
            col_fx4.metric("GBP / CZK", f"{daily_gbp_czk:.2f} Kč")
            render_cz_news_card(CZ_NEWS["fx"])
            fig_fx = build_dynamic_fx_chart_cz(df_for_fx_plot, fx_selected_currencies)
            st.caption("📌 **Zdroj dat:** Česká národní banka (ČNB) – Oficiální denní devizový kurzovní lístek")
        elif is_eu:
            col_fx1.metric("EUR / USD", f"{daily_eur_usd:.4f} $")
            col_fx2.metric("EUR / CZK", f"{daily_eur_czk:.2f} Kč")
            col_fx3.metric("EUR / PLN", f"{daily_eur_pln:.4f} zł")
            col_fx4.metric("EUR / GBP", f"{daily_eur_gbp:.4f} £")
            fig_fx = build_dynamic_fx_chart_eu(df_for_fx_plot, fx_selected_currencies)
            st.caption("📌 **Zdroj dat:** Evropská centrální banka (ECB) – Euro foreign exchange reference rates")
        else:
            col_fx1.metric("Dolarový index DXY", f"{daily_dxy:.2f} b.")
            col_fx2.metric("EUR / USD", f"{daily_eur_usd:.4f} $")
            col_fx3.metric("GBP / USD", f"{daily_gbp_usd:.4f} $")
            col_fx4.metric("USD / PLN", f"{daily_usd_pln:.4f} zł")
            fig_fx = build_dynamic_fx_chart_us(df_for_fx_plot, fx_selected_currencies)
            st.caption("📌 **Zdroj dat:** Intercontinental Exchange (ICE DXY Index) & Federal Reserve H.10 FX Rates")

        render_plotly_chart(fig_fx, key="chart_dynamic_fx")

        # Tlačítko stažení denních dat
        csv_daily_fx = df_daily_fx_filtered.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")
        st.download_button(
            label="📥 Stáhnout kompletní denní data FX kurzů (CSV)",
            data=csv_daily_fx,
            file_name=f"denni_kurzy_FX_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            key="btn_dl_dynamic_fx_csv"
        )

    # 1.4 Bankovní sektor, úvěry a měnová zásoba
    with sub_tab_banking:
        if is_cz:
            st.markdown('<div class="section-header">Bankovní sektor, hypoteční trh a měnová zásoba ČR</div>', unsafe_allow_html=True)
            col_bk1, col_bk2, col_bk3, col_bk4 = st.columns(4)
            col_bk1.metric("Nové hypotéky – průměrná sazba", f"{cz_mort_rate_curr:.2f} % p.a.", delta=f"{cz_mort_rate_curr - cz_mort_rate_prev:+.2f} p.b.", delta_color="inverse")
            col_bk2.metric("Nové hypotéky – měsíční objem", f"{cz_mort_vol_curr:.1f} mld. Kč")
            col_bk3.metric("Korporátní úvěry (meziroční růst)", f"{cz_corp_loans_curr:+.1f} %", delta=f"{cz_corp_loans_curr - cz_corp_loans_prev:+.1f} p.b.")
            col_bk4.metric("Měnový agregát M2 (meziročně)", f"{cz_m2_curr:+.1f} %", delta=f"{cz_m2_curr - cz_m2_prev:+.1f} p.b.")
            render_cz_news_card(CZ_NEWS.get("banking"))
            fig_bk = build_banking_and_loans_chart(df)
            render_plotly_chart(fig_bk, key="chart_cz_banking_loans")
            st.caption("📌 **Zdroj dat:** Česká bankovní asociace (ČBA Hypomonitor) & Česká národní banka (ČNB ARAD – Měnová a bankovní statistika)")
        elif is_eu:
            st.markdown('<div class="section-header">Bankovní sektor a úvěrová dynamika v Eurozóně</div>', unsafe_allow_html=True)
            col_ebk1, col_ebk2, col_ebk3, col_ebk4 = st.columns(4)
            col_ebk1.metric("ECB Depozitní sazba (Kotva)", f"{ecb_dep_curr:.2f} %")
            col_ebk2.metric("EURIBOR 3M (Benchmark)", f"{euribor3m_curr:.2f} %")
            col_ebk3.metric("Měnový agregát M3", "Růst +2.9 %", help="Data ECB MFI statistika")
            col_ebk4.metric("Kreditní standardy (BLS)", "Neutrální", help="ECB Bank Lending Survey")
            st.info("💡 Data bankovního sektoru Eurozóny vycházejí z pravidelného šetření ECB Bank Lending Survey (BLS) a statistik měnových finančních institucí (MFI). V ČR je k dispozici detailní měsíční monitoring ČBA Hypomonitor.")
            st.caption("📌 **Zdroj dat:** Evropská centrální banka (ECB) – Bank Lending Survey & Monetary Developments in the Euro Area")
        else:
            st.markdown('<div class="section-header">Bankovní sektor, úvěry a měnová zásoba USA</div>', unsafe_allow_html=True)
            col_ubk1, col_ubk2, col_ubk3, col_ubk4 = st.columns(4)
            col_ubk1.metric("SOFR sazba (Peněžní trh)", f"{sofr_curr:.2f} %")
            col_ubk2.metric("30Y Fixed Mortgage (USA průměr)", "6.75 %", help="Freddie Mac Primary Mortgage Market Survey")
            col_ubk3.metric("M2 Money Supply (USA)", "Růst +2.6 %", help="Federal Reserve H.6 Release")
            col_ubk4.metric("Fed Funds Target", f"{fed_upper_curr:.2f} %")
            st.info("💡 Americký hypoteční a úvěrový trh je sledován primárně prostřednictvím sazeb Freddie Mac (30Y Fixed Rate Mortgage) a bilance komerčních bank Fed H.8.")
            st.caption("📌 **Zdroj dat:** Federal Reserve Board (H.6, H.8) & Freddie Mac PMMS")


# =============================================================================
# 2. KATEGORIE: REÁLNÁ EKONOMIKA & PRÁCE
# =============================================================================
with main_tab_real:
    sub_tab_leading, sub_tab_gdp, sub_tab_inf, sub_tab_act, sub_tab_labor = st.tabs([
        "Předstihové ukazatele & Sentiment",
        "HDP",
        f"Inflace ({'CPI' if not is_eu else 'HICP'})",
        "Průmysl a spotřeba",
        "Trh práce & Mzdy"
    ])

    # 2.1 Předstihové ukazatele & Sentiment
    with sub_tab_leading:
        if is_cz:
            st.markdown('<div class="section-header">Předstihové ukazatele a sentiment ČR (PMI v průmyslu & Důvěra ČSÚ)</div>', unsafe_allow_html=True)
            col_pl1, col_pl2, col_pl3, col_pl4 = st.columns(4)
            col_pl1.metric("PMI v průmyslu ČR", f"{cz_pmi_curr:.1f} b.", delta=f"{cz_pmi_curr - cz_pmi_prev:+.1f} b.", help="Index nákupních manažerů S&P Global (> 50 expanze, < 50 kontrakce)")
            col_pl2.metric("Důvěra podnikatelů a spotřebitelů", f"{cz_conf_curr:.1f} b.", delta=f"{cz_conf_curr - cz_conf_prev:+.1f} b.", help="Souhrnný konjunkturální indikátor ČSÚ (báze 100)")
            col_pl3.metric("Práh expanze PMI", "50.0 b.", help="Hodnota oddělující růst od poklesu výroby")
            col_pl4.metric("Dlouhodobý průměr sentimentu", "100.0 b.", help="Historická norma důvěry ČSÚ")
            render_cz_news_card(CZ_NEWS.get("leading"))
            fig_pl_cz = build_leading_indicators_chart(df, region="CZ")
            render_plotly_chart(fig_pl_cz, key="chart_cz_leading_indicators")
            st.caption("📌 **Zdroj dat:** S&P Global (Czech Republic Manufacturing PMI) & Český statistický úřad (ČSÚ – Konjunkturální průzkumy)")

        elif is_eu:
            st.markdown('<div class="section-header">Předstihové ukazatele Eurozóny a Německa (Composite PMI & Ifo index)</div>', unsafe_allow_html=True)
            col_epl1, col_epl2, col_epl3, col_epl4 = st.columns(4)
            col_epl1.metric("Composite PMI Eurozóny", f"{eu_pmi_curr:.1f} b.", delta=f"{eu_pmi_curr - eu_pmi_prev:+.1f} b.", help="S&P Global / HCOB Eurozone Composite Output Index")
            col_epl2.metric("Německý Ifo index klimatu", f"{eu_ifo_curr:.1f} b.", delta=f"{eu_ifo_curr - eu_ifo_prev:+.1f} b.", help="Ifo Geschäftsklimaindex (klíčový barometr německého hospodářství)")
            col_epl3.metric("Práh expanze PMI", "50.0 b.")
            col_epl4.metric("Ifo dlouhodobý průměr", "100.0 b.")
            fig_pl_eu = build_leading_indicators_chart(df, region="EU")
            render_plotly_chart(fig_pl_eu, key="chart_eu_leading_indicators")
            st.caption("📌 **Zdroj dat:** S&P Global / Hamburg Commercial Bank (HCOB) & Ifo Institut für Wirtschaftsforschung (München)")

        else:
            st.markdown('<div class="section-header">Předstihové ukazatele a spotřebitelský sentiment USA (ISM PMI & Michigan)</div>', unsafe_allow_html=True)
            col_upl1, col_upl2, col_upl3, col_upl4 = st.columns(4)
            col_upl1.metric("ISM Manufacturing PMI", f"{us_ism_mfg_curr:.1f} b.", delta=f"{us_ism_mfg_curr - us_ism_mfg_prev:+.1f} b.", help="Index nákupních manažerů ve zpracovatelském průmyslu USA")
            col_upl2.metric("ISM Services PMI", f"{us_ism_srv_curr:.1f} b.", delta=f"{us_ism_srv_curr - us_ism_srv_prev:+.1f} b.", help="Index nákupních manažerů v nevýrobním sektoru služeb USA")
            col_upl3.metric("Spotřebitelský sentiment (Michigan)", f"{us_mich_curr:.1f} b.", delta=f"{us_mich_curr - us_mich_prev:+.1f} b.", help="University of Michigan Index of Consumer Sentiment")
            col_upl4.metric("Práh expanze ISM", "50.0 b.")
            fig_pl_us = build_leading_indicators_chart(df, region="US")
            render_plotly_chart(fig_pl_us, key="chart_us_leading_indicators")
            st.caption("📌 **Zdroj dat:** Institute for Supply Management (ISM) & University of Michigan (Surveys of Consumers)")

    # 2.2 HDP
    with sub_tab_gdp:
        if is_cz:
            st.markdown('<div class="section-header">Hrubý domácí produkt (HDP) České republiky</div>', unsafe_allow_html=True)
            col_g1, col_g2, col_g3, col_g4 = st.columns(4)
            col_g1.metric("Reálný růst HDP (YoY)", f"{gdp_cz_curr:+.1f} %", delta=f"{gdp_cz_delta:+.1f} p.b.")
            col_g2.metric("Kvartální nominální HDP", f"{nom_cz_val:,.1f} mld. Kč")
            col_g3.metric("Průměrný růst v období", f"{df['gdp_growth_real'].mean():+.2f} %" if "gdp_growth_real" in df.columns else "N/A")
            col_g4.metric("Poslední kvartál", str(last_row.get("quarter", "Aktuální")))
            render_cz_news_card(CZ_NEWS["gdp"])
            fig_gdp = build_gdp_chart(df, selected_indicators)
            render_plotly_chart(fig_gdp, key="chart_cz_gdp")
            st.caption("📌 **Zdroj dat:** Český statistický úřad (ČSÚ) – Čtvrtletní národní účty ČR")

        elif is_eu:
            st.markdown('<div class="section-header">Hrubý domácí produkt Eurozóny / Evropské unie</div>', unsafe_allow_html=True)
            col_eg1, col_eg2, col_eg3, col_eg4 = st.columns(4)
            col_eg1.metric("Reálný růst HDP EU (YoY)", f"{gdp_eu_curr:+.1f} %", delta=f"{gdp_eu_delta:+.1f} p.b.")
            col_eg2.metric("Nominální HDP Eurozóny", f"{nom_eu_val:,.0f} mld. EUR")
            col_eg3.metric("Průměrný růst v období", f"{df['eu_gdp_growth_real'].mean():+.2f} %" if "eu_gdp_growth_real" in df.columns else "N/A")
            col_eg4.metric("Poslední kvartál", str(last_row.get("quarter", "Aktuální")))
            fig_eu_gdp = build_eu_gdp_chart(df, selected_indicators)
            render_plotly_chart(fig_eu_gdp, key="chart_eu_gdp")
            st.caption("📌 **Zdroj dat:** Eurostat – Kvartální národní účty Eurozóny (EA20 / EU27)")

        else:
            st.markdown('<div class="section-header">Hrubý domácí produkt Spojených států (U.S. GDP)</div>', unsafe_allow_html=True)
            col_ug1, col_ug2, col_ug3, col_ug4 = st.columns(4)
            col_ug1.metric("Reálný růst HDP USA (YoY)", f"{gdp_us_curr:+.1f} %", delta=f"{gdp_us_delta:+.1f} p.b.")
            col_ug2.metric("Nominální objem HDP USA", f"{nom_us_val:,.0f} mld. $")
            col_ug3.metric("Průměrný růst v období", f"{df['us_gdp_growth_real'].mean():+.2f} %" if "us_gdp_growth_real" in df.columns else "N/A")
            col_ug4.metric("Poslední kvartál", str(last_row.get("quarter", "Aktuální")))
            fig_us_gdp = build_us_gdp_chart(df, selected_indicators)
            render_plotly_chart(fig_us_us := fig_us_gdp, key="chart_us_gdp")
            st.caption("📌 **Zdroj dat:** U.S. Bureau of Economic Analysis (BEA)")

    # 2.3 Inflace
    with sub_tab_inf:
        if is_cz:
            st.markdown('<div class="section-header">Spotřebitelská & jádrová inflace v ČR (CPI & Core CPI)</div>', unsafe_allow_html=True)
            col_i1, col_i2, col_i3, col_i4 = st.columns(4)
            col_i1.metric("Celková inflace (CPI YoY)", f"{cpi_cz_curr:.1f} %", delta=f"{cpi_cz_delta:+.1f} p.b.", delta_color="inverse")
            col_i2.metric("Jádrová inflace (Core CPI)", f"{core_cpi_cz_curr:.1f} %", delta="Sledováno ČNB", delta_color="off")
            real_cz_rate = repo_curr - cpi_cz_curr
            col_i3.metric("Reálná úroková sazba", f"{real_cz_rate:+.2f} %", delta="Repo − CPI", delta_color="off")
            col_i4.metric("Inflační cíl ČNB", "2.00 %", delta="Toleranční pásmo 1–3 %", delta_color="off")
            render_cz_news_card(CZ_NEWS["inflation"])
            fig_inf = build_inflation_chart(df)
            render_plotly_chart(fig_inf, key="chart_cz_inflation")
            st.caption("📌 **Zdroj dat:** Český statistický úřad (ČSÚ) & ČNB (Odbor měnové politiky)")

        elif is_eu:
            st.markdown('<div class="section-header">Harmonizovaná & jádrová inflace Eurozóny (HICP & Core HICP)</div>', unsafe_allow_html=True)
            col_ei1, col_ei2, col_ei3, col_ei4 = st.columns(4)
            col_ei1.metric("Harmonizovaná inflace (HICP)", f"{cpi_eu_curr:.1f} %", delta=f"{cpi_eu_delta:+.1f} p.b.", delta_color="inverse")
            col_ei2.metric("Jádrová inflace EU (Core HICP)", f"{core_cpi_eu_curr:.1f} %", delta="Bez energií a potravin", delta_color="off")
            real_eu_rate = ecb_dep_curr - cpi_eu_curr
            col_ei3.metric("Reálná sazba ECB", f"{real_eu_rate:+.2f} %", delta="Depo − HICP", delta_color="off")
            col_ei4.metric("Inflační cíl ECB", "2.00 %", delta="Střednědobý cíl", delta_color="off")
            fig_eu_inf = build_eu_inflation_chart(df)
            render_plotly_chart(fig_eu_inf, key="chart_eu_inflation")
            st.caption("📌 **Zdroj dat:** Eurostat (Harmonised Index of Consumer Prices - HICP)")

        else:
            st.markdown('<div class="section-header">Spotřebitelská & jádrová inflace v USA (Headline & Core CPI)</div>', unsafe_allow_html=True)
            col_ui1, col_ui2, col_ui3, col_ui4 = st.columns(4)
            col_ui1.metric("Headline CPI USA (YoY)", f"{cpi_us_curr:.1f} %", delta=f"{cpi_us_delta:+.1f} p.b.", delta_color="inverse")
            col_ui2.metric("Jádrová inflace (Core CPI)", f"{core_cpi_us_curr:.1f} %", delta="Bez potravin a energií", delta_color="off")
            real_us_effr = fed_effr_curr - cpi_us_curr
            col_ui3.metric("Reálná úroková sazba Fedu", f"{real_us_effr:+.2f} %", delta="EFFR − CPI", delta_color="off")
            col_ui4.metric("Inflační cíl Fedu", "2.00 %", delta="PCE benchmark", delta_color="off")
            fig_us_inf = build_us_inflation_chart(df)
            render_plotly_chart(fig_us_inf, key="chart_us_inflation")
            st.caption("📌 **Zdroj dat:** U.S. Bureau of Labor Statistics (BLS)")

    # 2.4 Průmysl a spotřeba
    with sub_tab_act:
        reg_code = "CZ" if is_cz else ("EU" if is_eu else "US")
        reg_title = "České republiky" if is_cz else ("Eurozóny / EU" if is_eu else "Spojených států")
        st.markdown(f'<div class="section-header">Ekonomická aktivita: Maloobchodní tržby (Spotřeba) & Průmyslová produkce ({reg_title})</div>', unsafe_allow_html=True)
        col_a1, col_a2, col_a3, col_a4 = st.columns(4)
        if is_cz:
            col_a1.metric("Maloobchod ČR (Spotřeba YoY)", f"{retail_cz_curr:+.1f} %")
            col_a2.metric("Průmyslová produkce ČR (YoY)", f"{ind_cz_curr:+.1f} %")
            col_a3.metric("Průměrná spotřeba", f"{df['retail_sales_yoy'].mean():+.2f} %")
            col_a4.metric("Průměrný průmysl", f"{df['industrial_prod_yoy'].mean():+.2f} %")
            render_cz_news_card(CZ_NEWS["retail_industry"])
            st_source = "Český statistický úřad (ČSÚ) – Statistika maloobchodu a průmyslu"
        elif is_eu:
            col_a1.metric("Maloobchod EU (Spotřeba YoY)", f"{retail_eu_curr:+.1f} %")
            col_a2.metric("Průmyslová výroba EU (YoY)", f"{ind_eu_curr:+.1f} %")
            col_a3.metric("Průměrná spotřeba EU", f"{df['eu_retail_sales_yoy'].mean():+.2f} %")
            col_a4.metric("Průměrný průmysl EU", f"{df['eu_industrial_prod_yoy'].mean():+.2f} %")
            st_source = "Eurostat – Short-term business statistics (Retail Trade & Industry)"
        else:
            col_a1.metric("Maloobchod USA (Spotřeba YoY)", f"{retail_us_curr:+.1f} %")
            col_a2.metric("Průmyslová produkce USA (YoY)", f"{ind_us_curr:+.1f} %")
            col_a3.metric("Průměrná spotřeba USA", f"{df['us_retail_sales_yoy'].mean():+.2f} %")
            col_a4.metric("Průměrný průmysl USA", f"{df['us_industrial_prod_yoy'].mean():+.2f} %")
            st_source = "U.S. Census Bureau (Retail Sales) & Federal Reserve Board (Industrial Production)"

        fig_act = build_activity_chart(df, region=reg_code)
        render_plotly_chart(fig_act, key="chart_activity_panel")
        st.caption(f"📌 **Zdroj dat:** {st_source}")

    # 2.5 Trh práce & Mzdy
    with sub_tab_labor:
        if is_cz:
            st.markdown('<div class="section-header">Trh práce, nezaměstnanost a mzdový vývoj v ČR (Nominální vs. Reálné mzdy)</div>', unsafe_allow_html=True)
            col_u1, col_u2, col_u3, col_u4 = st.columns(4)
            col_u1.metric("Míra nezaměstnanosti ČR", f"{une_cz_curr:.1f} %", delta=f"{une_cz_delta:+.1f} p.b.", delta_color="inverse")
            col_u2.metric("Průměrná mzda nominálně (YoY)", f"{cz_nom_wage_curr:+.1f} %", delta=f"{cz_nom_wage_curr - cz_nom_wage_prev:+.1f} p.b.")
            col_u3.metric("Průměrná reálná mzda (YoY)", f"{cz_real_wage_curr:+.1f} %", delta=f"{cz_real_wage_curr - cz_real_wage_prev:+.1f} p.b.", help="Nominální mzda očištěná o inflaci CPI (kupní síla)")
            col_u4.metric("Meziroční inflace CPI", f"{cpi_cz_curr:.1f} %")
            render_cz_news_card(CZ_NEWS.get("wages"))
            fig_wages_cz = build_wages_chart(df, region="CZ")
            render_plotly_chart(fig_wages_cz, key="chart_cz_wages")
            fig_une = build_unemployment_chart(df)
            render_plotly_chart(fig_une, key="chart_cz_unemployment")
            st.caption("📌 **Zdroj dat:** Český statistický úřad (ČSÚ – Průměrné mzdy a platy & Zaměstnanost) & Eurostat (metodika ILO)")

        elif is_eu:
            st.markdown('<div class="section-header">Trh práce, nezaměstnanost a sjednané mzdy v Eurozóně (ECB Negotiated Wages)</div>', unsafe_allow_html=True)
            col_eu1, col_eu2, col_eu3, col_eu4 = st.columns(4)
            col_eu1.metric("Nezaměstnanost v EU", f"{une_eu_curr:.1f} %", delta=f"{une_eu_delta:+.1f} p.b.", delta_color="inverse")
            col_eu2.metric("Sjednané mzdy v Eurozóně (ECB YoY)", f"{eu_wages_curr:+.1f} %", delta=f"{eu_wages_curr - eu_wages_prev:+.1f} p.b.", help="ECB Negotiated Wage Indicator (klíčový ukazatel mzdových tlaků pro ECB)")
            col_eu3.metric("Harmonizovaná inflace HICP", f"{cpi_eu_curr:.1f} %")
            col_eu4.metric("Reálný mzdový růst (odhad)", f"{eu_wages_curr - cpi_eu_curr:+.1f} %")
            fig_wages_eu = build_wages_chart(df, region="EU")
            render_plotly_chart(fig_wages_eu, key="chart_eu_wages")
            fig_eu_une = build_eu_unemployment_chart(df)
            render_plotly_chart(fig_eu_une, key="chart_eu_unemployment")
            st.caption("📌 **Zdroj dat:** Evropská centrální banka (ECB – Negotiated Wages) & Eurostat (Harmonised Unemployment Rate)")

        else:
            st.markdown('<div class="section-header">Trh práce, zaměstnanost a průměrná hodinová mzda v USA (Average Hourly Earnings & NFP)</div>', unsafe_allow_html=True)
            col_uu1, col_uu2, col_uu3, col_uu4 = st.columns(4)
            col_uu1.metric("Míra nezaměstnanosti U-3", f"{une_us_curr:.1f} %", delta=f"{une_us_delta:+.1f} p.b.", delta_color="inverse")
            col_uu2.metric("Průměrná hodinová mzda (YoY)", f"{us_earn_curr:+.1f} %", delta=f"{us_earn_curr - us_earn_prev:+.1f} p.b.", help="Average Hourly Earnings of All Employees (BLS)")
            nfp_val = safe_metric(last_row, "us_nonfarm_payrolls_k", 180.0)
            col_uu3.metric("Nová pracovní místa (NFP)", f"{nfp_val:+,.0f} tis.")
            col_uu4.metric("Spotřebitelská inflace CPI", f"{cpi_us_curr:.1f} %")
            fig_wages_us = build_wages_chart(df, region="US")
            render_plotly_chart(fig_wages_us, key="chart_us_wages")
            fig_us_une = build_us_unemployment_chart(df)
            render_plotly_chart(fig_us_une, key="chart_us_unemployment")
            st.caption("📌 **Zdroj dat:** U.S. Bureau of Labor Statistics (BLS – Employment Situation & Average Hourly Earnings)")


# =============================================================================
# 3. KATEGORIE: TRHY (AKCIOVÉ INDEXY & VZÁJEMNÉ SROVNÁNÍ)
# =============================================================================
with main_tab_stocks:
    sub_tab_stock_cmp, sub_tab_px, sub_tab_stoxx, sub_tab_sp500, sub_tab_nasdaq, sub_tab_vix = st.tabs([
        "📊 Vzájemné srovnání indexů",
        "🇨🇿 Index PX (Pražská burza)",
        "🇪🇺 Euro Stoxx 50",
        "🇺🇸 S&P 500",
        "🇺🇸 NASDAQ Composite",
        "⚡ Index volatility VIX (Tržní riziko)"
    ])

    # 3.1 Vzájemné srovnání indexů
    with sub_tab_stock_cmp:
        st.markdown('<div class="section-header">Srovnání výkonnosti hlavních světových a lokálních akciových indexů</div>', unsafe_allow_html=True)
        st.caption("Porovnejte relativní kumulativní výnos nebo normalizovanou bázi pro S&P 500, NASDAQ, Euro Stoxx 50 a Index PX Pražské burzy.")

        # Souhrnné metriky pro všechny 4 indexy
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        sp_first = df["sp500_index"].iloc[0] if ("sp500_index" in df.columns and not df.empty) else 1.0
        sp_chg = ((sp500_curr / sp_first) - 1.0) * 100.0 if sp_first > 0 else 0.0

        nq_first = df["nasdaq_index"].iloc[0] if ("nasdaq_index" in df.columns and not df.empty) else 1.0
        nq_chg = ((nasdaq_curr / nq_first) - 1.0) * 100.0 if nq_first > 0 else 0.0

        sx_first = df["stoxx50_index"].iloc[0] if ("stoxx50_index" in df.columns and not df.empty) else 1.0
        sx_chg = ((stoxx50_curr / sx_first) - 1.0) * 100.0 if sx_first > 0 else 0.0

        px_first = df["px_index"].iloc[0] if ("px_index" in df.columns and not df.empty) else 1.0
        px_chg = ((px_curr / px_first) - 1.0) * 100.0 if px_first > 0 else 0.0

        col_m1.metric("🇺🇸 S&P 500", f"{sp500_curr:,.0f} b.", delta=f"{sp_chg:+.1f} % (za období)")
        col_m2.metric("🇺🇸 NASDAQ Composite", f"{nasdaq_curr:,.0f} b.", delta=f"{nq_chg:+.1f} % (za období)")
        col_m3.metric("🇪🇺 Euro Stoxx 50", f"{stoxx50_curr:,.0f} b.", delta=f"{sx_chg:+.1f} % (za období)")
        col_m4.metric("🇨🇿 Index PX (Praha)", f"{px_curr:,.0f} b.", delta=f"{px_chg:+.1f} % (za období)")

        col_sc1, col_sc2 = st.columns([2.5, 1.5])
        with col_sc1:
            indices_to_compare = st.multiselect(
                "Vyberte indexy ke srovnání v grafu:",
                options=["Index PX (Praha)", "Euro Stoxx 50 (EU)", "S&P 500 (USA)", "NASDAQ (USA)"],
                default=["Index PX (Praha)", "Euro Stoxx 50 (EU)", "S&P 500 (USA)", "NASDAQ (USA)"],
                key="indices_to_compare_multiselect"
            )
        with col_sc2:
            cmp_mode_choice = st.radio(
                "Metrika normalizace:",
                ["📈 Relativní výkonnost (% od počátku období)", "🔢 Rebase na bázi 100"],
                horizontal=True,
                key="stock_cmp_mode_radio"
            )

        cmp_mode = "pct" if "Relativní" in cmp_mode_choice else "rebase"
        fig_stock_cmp = build_stock_comparison_chart(df, indices_to_compare, mode=cmp_mode)
        render_plotly_chart(fig_stock_cmp, key="chart_stock_comparison")
        st.caption("📌 **Zdroj dat:** Burza cenných papírů Praha (PSE / Index PX), STOXX Ltd. (Euro Stoxx 50), S&P Dow Jones Indices (S&P 500) & NASDAQ OMX (NASDAQ Composite) / Yahoo Finance API")

    # 3.2 Index PX
    with sub_tab_px:
        st.markdown('<div class="section-header">Index PX – Burza cenných papírů Praha (BCPP)</div>', unsafe_allow_html=True)
        st.caption("Oficiální cenový index pražské burzy zahrnující klíčové české emise (ČEZ, Komerční banka, Erste Group, Moneta Money Bank, Colt CZ).")
        col_px1, col_px2, col_px3, col_px4 = st.columns(4)
        col_px1.metric("Aktuální hodnota", f"{px_curr:,.1f} bodů")
        col_px2.metric("Výkonnost za vybrané období", f"{px_chg:+.1f} %")
        col_px3.metric("Minimum v období", f"{df['px_index'].min():,.1f} b." if "px_index" in df.columns else "N/A")
        col_px4.metric("Maximum v období", f"{df['px_index'].max():,.1f} b." if "px_index" in df.columns else "N/A")
        render_cz_news_card(CZ_NEWS["stocks_px"])
        fig_single_px = build_single_stock_chart(df, "px_index", "Index PX (Praha)", color="#DC2626")
        render_plotly_chart(fig_single_px, key="chart_single_px")
        st.caption("📌 **Zdroj dat:** Burza cenných papírů Praha (PSE / BCPP) – Oficiální kalkulace indexu PX")

    # 3.3 Euro Stoxx 50
    with sub_tab_stoxx:
        st.markdown('<div class="section-header">Euro Stoxx 50 – Benchmark předních akcií Eurozóny</div>', unsafe_allow_html=True)
        st.caption("Index nejvýznamnějších 50 korporátních lídrů Eurozóny napříč 8 zeměmi (např. ASML, LVMH, SAP, TotalEnergies, Siemens, Allianz, Sanofi).")
        col_sx1, col_sx2, col_sx3, col_sx4 = st.columns(4)
        col_sx1.metric("Aktuální hodnota", f"{stoxx50_curr:,.1f} bodů")
        col_sx2.metric("Výkonnost za vybrané období", f"{sx_chg:+.1f} %")
        col_sx3.metric("Minimum v období", f"{df['stoxx50_index'].min():,.1f} b." if "stoxx50_index" in df.columns else "N/A")
        col_sx4.metric("Maximum v období", f"{df['stoxx50_index'].max():,.1f} b." if "stoxx50_index" in df.columns else "N/A")
        fig_single_stoxx = build_single_stock_chart(df, "stoxx50_index", "Euro Stoxx 50", color="#059669")
        render_plotly_chart(fig_single_stoxx, key="chart_single_stoxx")
        st.caption("📌 **Zdroj dat:** STOXX Ltd. (Deutsche Börse Group) & Yahoo Finance")

    # 3.4 S&P 500
    with sub_tab_sp500:
        st.markdown('<div class="section-header">S&P 500 – Globální měřítko amerického akciového trhu</div>', unsafe_allow_html=True)
        st.caption("Index 500 největších veřejně obchodovaných společností v USA pokrývající přibližně 80 % tržní kapitalizace celého amerického trhu.")
        col_sp1, col_sp2, col_sp3, col_sp4 = st.columns(4)
        col_sp1.metric("Aktuální hodnota", f"{sp500_curr:,.1f} bodů")
        col_sp1_delta = sp500_curr - safe_metric(prev_row, "sp500_index", sp500_curr)
        col_sp2.metric("Výkonnost za vybrané období", f"{sp_chg:+.1f} %", delta=f"{col_sp1_delta:+.1f} b.")
        col_sp3.metric("Minimum v období", f"{df['sp500_index'].min():,.1f} b." if "sp500_index" in df.columns else "N/A")
        col_sp4.metric("Maximum v období", f"{df['sp500_index'].max():,.1f} b." if "sp500_index" in df.columns else "N/A")
        fig_single_sp = build_single_stock_chart(df, "sp500_index", "S&P 500", color="#2563EB")
        render_plotly_chart(fig_single_sp, key="chart_single_sp")
        st.caption("📌 **Zdroj dat:** S&P Dow Jones Indices & Yahoo Finance")

    # 3.5 NASDAQ Composite
    with sub_tab_nasdaq:
        st.markdown('<div class="section-header">NASDAQ Composite – Světový technologický a inovační lídr</div>', unsafe_allow_html=True)
        st.caption("Index zahrnující přes 3 000 akcií kótovaných na burze NASDAQ s vysokým zastoupením technologického sektoru (Apple, Microsoft, Nvidia, Amazon, Alphabet, Meta).")
        col_nq1, col_nq2, col_nq3, col_nq4 = st.columns(4)
        col_nq1.metric("Aktuální hodnota", f"{nasdaq_curr:,.1f} bodů")
        col_nq1_delta = nasdaq_curr - safe_metric(prev_row, "nasdaq_index", nasdaq_curr)
        col_nq2.metric("Výkonnost za vybrané období", f"{nq_chg:+.1f} %", delta=f"{col_nq1_delta:+.1f} b.")
        col_nq3.metric("Minimum v období", f"{df['nasdaq_index'].min():,.1f} b." if "nasdaq_index" in df.columns else "N/A")
        col_nq4.metric("Maximum v období", f"{df['nasdaq_index'].max():,.1f} b." if "nasdaq_index" in df.columns else "N/A")
        fig_single_nq = build_single_stock_chart(df, "nasdaq_index", "NASDAQ Composite", color="#7C3AED")
        render_plotly_chart(fig_single_nq, key="chart_single_nasdaq")
        st.caption("📌 **Zdroj dat:** NASDAQ OMX Group & Yahoo Finance")

    # 3.6 Index volatility VIX (Tržní sentiment & riziko)
    with sub_tab_vix:
        st.markdown('<div class="section-header">Index volatility VIX – Tržní sentiment a vnímané riziko (Cboe "Index strachu")</div>', unsafe_allow_html=True)
        st.caption("Cboe Volatility Index (VIX) vyjadřuje implikovanou 30denní volatilitu opcí na index S&P 500. Je klíčovým barometrem tržního strachu, averze k riziku a stresu na globálních trzích.")
        col_vx1, col_vx2, col_vx3, col_vx4 = st.columns(4)
        vix_delta = vix_curr - vix_prev
        col_vx1.metric("Index VIX", f"{vix_curr:.2f} bodů", delta=f"{vix_delta:+.2f} b.", delta_color="inverse")
        if vix_curr < 15.0:
            regime_label = "Klid / Sebeuspokojení (< 15)"
        elif vix_curr <= 20.0:
            regime_label = "Normální rozmezí (15–20)"
        elif vix_curr <= 30.0:
            regime_label = "Zvýšená nervozita (20–30)"
        else:
            regime_label = "Tržní panika / Stres (> 30)"
        col_vx2.metric("Tržní režim sentimentu", regime_label)
        vix_min = df["vix_index"].min() if "vix_index" in df.columns else 12.0
        vix_max = df["vix_index"].max() if "vix_index" in df.columns else 35.0
        col_vx3.metric("Minimum v období", f"{vix_min:.2f} b.")
        col_vx4.metric("Maximum v období", f"{vix_max:.2f} b.")

        st.markdown(
            """
            <div style="background: #f8fafc; border-left: 4px solid #6366f1; border-radius: 6px; padding: 10px 14px; margin: 12px 0 16px 0; font-size: 0.86rem; color: #334155;">
                <strong>📊 Jak interpretovat hladiny indexu VIX:</strong><br>
                &bull; <strong>Pod 15 bodů:</strong> Nízká vnímaná rizika, stabilní růst akciových trhů (potenciální riziko sebeuspokojení / complacency).<br>
                &bull; <strong>15 až 20 bodů:</strong> Běžná historická průměrná úroveň volatility, vyvážený a zdravý trh.<br>
                &bull; <strong>20 až 30 bodů:</strong> Zvýšená tržní nervozita, makroekonomická nejistota, korekce na trzích.<br>
                &bull; <strong>Nad 30 bodů:</strong> Akutní tržní stres, prudké výprodeje, likviditní šok (např. pandemický pád březen 2020 nebo hypoteční krize 2008).
            </div>
            """,
            unsafe_allow_html=True
        )
        fig_vix = build_vix_chart(df)
        render_plotly_chart(fig_vix, key="chart_vix_sentiment")
        st.caption("📌 **Zdroj dat:** Chicago Board Options Exchange (Cboe VIX Index) & S&P Dow Jones Indices / Yahoo Finance API (^VIX)")


# =============================================================================
# 4. KATEGORIE: VEŘEJNÉ FINANCE & SVĚT
# =============================================================================
with main_tab_public:
    sub_tab_debt, sub_tab_external, sub_tab_intl = st.tabs([
        "Veřejný dluh",
        f"Vnější rovnováha & Zahraniční obchod ({'ČR' if is_cz else ('Eurozóna' if is_eu else 'USA')})",
        "Mezinárodní srovnání"
    ])

    # 4.1 Veřejný dluh & Saldo rozpočtu
    with sub_tab_debt:
        if is_cz:
            st.markdown('<div class="section-header">Fiskální politika a veřejný dluh České republiky</div>', unsafe_allow_html=True)
            col_d1, col_d2, col_d3 = st.columns(3)
            col_d1.metric("Veřejný dluh k HDP", f"{debt_cz_pct:.1f} %", delta="Limit < 60 % HDP", delta_color="normal")
            debt_nom_val = safe_metric(last_row, "public_debt_czk_bn", 3300.0)
            col_d2.metric("Nominální veřejný dluh", f"{debt_nom_val:,.1f} mld. Kč")
            col_d3.metric("Kvartální saldo rozpočtu", f"{deficit_cz_curr:,.1f} mld. Kč")
            render_cz_news_card(CZ_NEWS["debt"])
            fig_d1, fig_d2 = build_debt_charts(df)
            c_da, c_db = st.columns(2)
            with c_da:
                render_plotly_chart(fig_d1, key="chart_cz_debt_pct")
            with c_db:
                render_plotly_chart(fig_d2, key="chart_cz_deficit")
            st.caption("📌 **Zdroj dat:** Ministerstvo financí ČR (MF ČR) & Eurostat (Maastrichtská notifikace dluhu)")

        elif is_eu:
            st.markdown('<div class="section-header">Fiskální politika a veřejný dluh Eurozóny / EU</div>', unsafe_allow_html=True)
            col_ed1, col_ed2, col_ed3 = st.columns(3)
            col_ed1.metric("Veřejný dluh Eurozóny k HDP", f"{debt_eu_pct:.1f} %", delta="Maastricht 60 % limit", delta_color="normal")
            col_ed2.metric("Nominální dluh Eurozóny", f"{debt_eu_nom:,.0f} mld. EUR")
            col_ed3.metric("Kvartální saldo rozpočtu EU", f"{deficit_eu_curr:,.0f} mld. EUR")
            fig_ed1, fig_ed2 = build_eu_debt_charts(df)
            c_eda, c_edb = st.columns(2)
            with c_eda:
                render_plotly_chart(fig_ed1, key="chart_eu_debt_pct")
            with c_edb:
                render_plotly_chart(fig_ed2, key="chart_eu_deficit")
            st.caption("📌 **Zdroj dat:** Eurostat – Vládní finanční statistika (Government Finance Statistics - EDP)")

        else:
            st.markdown('<div class="section-header">Fiskální politika a federální dluh Spojených států</div>', unsafe_allow_html=True)
            col_ud1, col_ud2, col_ud3 = st.columns(3)
            col_ud1.metric("Federální dluh USA k HDP", f"{debt_us_pct:.1f} %", delta="Historické maximum", delta_color="inverse")
            col_ud2.metric("Nominální federální dluh", f"{debt_us_nom:,.0f} mld. $")
            col_ud3.metric("Kvartální federální deficit", f"{deficit_us_curr:,.0f} mld. $")
            fig_ud1, fig_ud2 = build_us_debt_charts(df)
            c_uda, c_udb = st.columns(2)
            with c_uda:
                render_plotly_chart(fig_ud1, key="chart_us_debt_pct")
            with c_udb:
                render_plotly_chart(fig_ud2, key="chart_us_deficit")
            st.caption("📌 **Zdroj dat:** U.S. Department of the Treasury (Fiscal Service - Debt to the Penny)")

    # 4.2 Vnější rovnováha & Zahraniční obchod
    with sub_tab_external:
        if is_cz:
            st.markdown('<div class="section-header">Vnější rovnováha ČR: Běžný účet platební bilance & Bilance zahraničního obchodu ČSÚ</div>', unsafe_allow_html=True)
            col_ex1, col_ex2, col_ex3, col_ex4 = st.columns(4)
            col_ex1.metric("Běžný účet (% HDP)", f"{cz_ca_curr:+.1f} %", help="Podíl běžného účtu platební bilance na HDP ČR")
            col_ex2.metric("Bilance zahr. obchodu (ČSÚ)", f"{cz_trade_bal_curr:+.1f} mld. Kč", delta=f"{cz_trade_bal_curr - cz_trade_bal_prev:+.1f} mld. Kč")
            trade_12m_sum = df["cz_trade_balance_czk_bn"].tail(12).sum() if "cz_trade_balance_czk_bn" in df.columns else 120.0
            col_ex3.metric("Kumulované saldo za 12M", f"{trade_12m_sum:+.1f} mld. Kč", help="Součet obchodní bilance za posledních 12 měsíců")
            col_ex4.metric("Kurz EUR/CZK (denní)", f"{daily_eur_czk:.2f} Kč")
            render_cz_news_card(CZ_NEWS.get("external"))
            fig_ext = build_external_balance_chart(df)
            render_plotly_chart(fig_ext, key="chart_cz_external_balance")
            st.caption("📌 **Zdroj dat:** Český statistický úřad (ČSÚ – Zahraniční obchod se zbožím) & Česká národní banka (ČNB – Platební bilance)")
        elif is_eu:
            st.markdown('<div class="section-header">Vnější rovnováha a mezinárodní obchod Eurozóny</div>', unsafe_allow_html=True)
            col_eex1, col_eex2, col_eex3, col_eex4 = st.columns(4)
            col_eex1.metric("Běžný účet Eurozóny (% HDP)", "+2.8 %", help="Trvalý přebytek běžného účtu Eurozóny")
            col_eex2.metric("Měnový kurz EUR/USD", f"{daily_eur_usd:.4f} $")
            col_eex3.metric("Exportní orientace", "Vysoká (Německo, Nizozemsko)")
            col_eex4.metric("Dovoz energií", "Stabilizovaný")
            st.info("💡 Eurozóna dlouhodobě vykazuje strukturální přebytek běžného účtu platební bilance, tažený exportem německého a nizozemského strojírenství, chemického a automobilového průmyslu.")
            st.caption("📌 **Zdroj dat:** Eurostat & Evropská centrální banka (ECB – Balance of Payments)")
        else:
            st.markdown('<div class="section-header">Vnější rovnováha a obchodní bilance Spojených států</div>', unsafe_allow_html=True)
            col_uex1, col_uex2, col_uex3, col_uex4 = st.columns(4)
            col_uex1.metric("Běžný účet USA (% HDP)", "−3.2 %", help="Dlouhodobý strukturální deficit běžného účtu")
            col_uex2.metric("Dolarový index DXY", f"{daily_dxy:.2f} b.")
            col_uex3.metric("Postavení USD", "Globální rezervní měna")
            col_uex4.metric("Příliv kapitálu", "Financuje schodek")
            st.info("💡 USA dlouhodobě hospodaří s deficitem běžného účtu (tzv. dvojí deficit – rozpočtový a obchodní). Schodek je financován trvalým přílivem zahraničního kapitálu do amerických finančních aktiv a rezervním statusem amerického dolaru.")
            st.caption("📌 **Zdroj dat:** U.S. Bureau of Economic Analysis (BEA – U.S. International Transactions)")

    # 4.3 Mezinárodní srovnání
    with sub_tab_intl:
        st.markdown('<div class="section-header">Mezinárodní srovnání sazeb a výnosových spreadů</div>', unsafe_allow_html=True)
        comp_type = "CZ" if is_cz else ("EU" if is_eu else "US")
        col_cp1, col_cp2, col_cp3 = st.columns(3)
        if is_cz:
            rate_diff_us = repo_curr - fed_upper_curr
            rate_diff_ecb = repo_curr - ecb_dep_curr
            col_cp1.metric("Sazbový diferenciál (ČNB vs. Fed)", f"{rate_diff_us:+.2f} p.b.")
            col_cp2.metric("Sazbový diferenciál (ČNB vs. ECB)", f"{rate_diff_ecb:+.2f} p.b.")
            spread_10y_bund = (czgb10_curr - bund10_curr) * 100.0
            col_cp3.metric("Sovereign spread 10Y (CZGB − Bund)", f"{spread_10y_bund:+.0f} bps")
            render_cz_news_card(CZ_NEWS["intl_spread"])
        elif is_eu:
            diff_ecb_fed = ecb_dep_curr - fed_upper_curr
            col_ecp1 = col_cp1.metric("Sazbový diferenciál (ECB vs. Fed)", f"{diff_ecb_fed:+.2f} p.b.")
            spread_bund_us = (bund10_curr - us10_curr) * 100.0
            col_ecp2 = col_cp2.metric("Spread 10Y (Bund − US Treasury)", f"{spread_bund_us:+.0f} bps")
            diff_inf_eu_us = cpi_eu_curr - cpi_us_curr
            col_ecp3 = col_cp3.metric("Inflační diferenciál (EU − USA)", f"{diff_inf_eu_us:+.1f} p.b.")
        else:
            diff_fed_ecb = fed_upper_curr - ecb_dep_curr
            col_ucp1 = col_cp1.metric("Sazbový diferenciál (Fed vs. ECB)", f"{diff_fed_ecb:+.2f} p.b.")
            spread_us_bund_bps = (us10_curr - bund10_curr) * 100.0
            col_ucp2 = col_cp2.metric("Spread 10Y (US Treasury − Bund)", f"{spread_us_bund_bps:+.0f} bps")
            inf_diff_us = cpi_us_curr - cpi_eu_curr
            col_ucp3 = col_cp3.metric("Inflační diferenciál (USA − EU)", f"{inf_diff_us:+.1f} p.b.")

        fig_comp = build_international_spread_chart(df, comparison_type=comp_type)
        render_plotly_chart(fig_comp, key="chart_intl_comparison_tab")
        st.caption("📌 **Zdroj dat:** ČNB, Evropská centrální banka (ECB), Federal Reserve, Eurostat a U.S. Department of the Treasury")


# =============================================================================
# 5. KATEGORIE: DATA A EXPORT
# =============================================================================
with main_tab_export:
    st.markdown(f'<div class="section-header">Datový průzkumník a export ({region_label})</div>', unsafe_allow_html=True)
    st.caption("Interaktivní tabulkový přehled všech vybraných časových řad připravený pro export do formátu CSV.")
    render_dataframe(df_export_active)
    csv_bytes_active = df_export_active.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")
    st.download_button(
        label=f"📥 Stáhnout kompletní data {region_label} (CSV)",
        data=csv_bytes_active,
        file_name=f"makro_data_{region_label}_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        key=f"btn_dl_macro_{region_label.lower()}_active"
    )
    st.caption("📌 **Zdroj dat:** ČNB, Eurostat, U.S. Treasury, Federal Reserve a Burza cenných papírů Praha")


# =============================================================================
# 6. KATEGORIE: SEZNAM UKAZATELŮ & ZDROJE DAT
# =============================================================================
with main_tab_catalog:
    st.markdown('<div class="section-header">Kompletní metodický přehled a katalog všech sledovaných ukazatelů a zdrojů dat</div>', unsafe_allow_html=True)
    st.caption("Strukturovaný přehled všech 100+ makroekonomických a tržních ukazatelů podle jednotlivých zemí a kategorií s uvedením primárních datových zdrojů, metodiky a frekvence aktualizace.")

    col_tb6_g1, col_tb6_g2 = st.columns([1.6, 3.4])
    with col_tb6_g1:
        if st.button("📖 Otevřít Výkladový glosář pro laiky", type="primary", use_container_width=True, key="btn_open_glossary_tab6"):
            st.session_state["current_view"] = "glossary"
            st.rerun()
    with col_tb6_g2:
        st.markdown(
            """
            <div style="font-size: 0.83rem; color: #475569; padding-top: 5px;">
                💡 <em>Hledáte srozumitelný lidský výklad co jednotlivé pojmy znamenají, proč je sledovat a jaký mají vliv na hypotéky či investice? Použijte <strong>Výkladový glosář</strong>.</em>
            </div>
            """,
            unsafe_allow_html=True
        )

    df_cat = get_indicators_catalog_df()

    # Horní souhrnné metriky
    col_c1, col_c2, col_c3, col_c4 = st.columns(4)
    cz_cnt = len(df_cat[df_cat["_region_code"] == "CZ"])
    eu_cnt = len(df_cat[df_cat["_region_code"] == "EU"])
    us_cnt = len(df_cat[df_cat["_region_code"] == "US"])
    col_c1.metric("Celkem ukazatelů", f"{len(df_cat)} metrik")
    col_c2.metric("🇨🇿 Česká republika", f"{cz_cnt} ukazatelů")
    col_c3.metric("🇪🇺 Evropská unie", f"{eu_cnt} ukazatelů")
    col_c4.metric("🇺🇸 Spojené státy", f"{us_cnt} ukazatelů")

    # Interaktivní filtry katalogu
    col_cf1, col_cf2, col_cf3 = st.columns([1.5, 1.5, 2.0])
    with col_cf1:
        cat_country = st.selectbox(
            "Filtrovat podle země:",
            ["Všechny země", "🇨🇿 Česká republika", "🇪🇺 Evropská unie", "🇺🇸 Spojené státy"],
            key="cat_filter_country"
        )
    with col_cf2:
        all_categories = ["Všechny kategorie"] + sorted(list(df_cat["Kategorie"].unique()))
        cat_category = st.selectbox(
            "Filtrovat podle kategorie:",
            all_categories,
            key="cat_filter_category"
        )
    with col_cf3:
        search_query = st.text_input(
            "🔍 Hledat v ukazatelích a zdrojích:",
            placeholder="Zadejte název, kód nebo zdroj (např. inflace, PRIBOR, ČNB, HDP)...",
            key="cat_search_input"
        )

    df_filtered_cat = df_cat.copy()
    if cat_country != "Všechny země":
        df_filtered_cat = df_filtered_cat[df_filtered_cat["Země / Region"] == cat_country]
    if cat_category != "Všechny kategorie":
        df_filtered_cat = df_filtered_cat[df_filtered_cat["Kategorie"] == cat_category]
    if search_query.strip():
        q = search_query.strip().lower()
        df_filtered_cat = df_filtered_cat[
            df_filtered_cat["Název ukazatele"].str.lower().str.contains(q) |
            df_filtered_cat["Kód indikátoru"].str.lower().str.contains(q) |
            df_filtered_cat["Primární zdroj dat"].str.lower().str.contains(q) |
            df_filtered_cat["Metodický popis"].str.lower().str.contains(q)
        ]

    st.markdown(f"**Nalezeno {len(df_filtered_cat)} z {len(df_cat)} ukazatelů**")

    display_cat_df = df_filtered_cat.drop(columns=["_region_code"])
    st.dataframe(
        display_cat_df,
        use_container_width=True,
        hide_index=True,
        height=480
    )

    # Tlačítko pro stažení katalogu do CSV
    csv_cat_buffer = io.StringIO()
    display_cat_df.to_csv(csv_cat_buffer, index=False, sep=";", decimal=",", encoding="utf-8-sig")
    st.download_button(
        label="📥 Stáhnout kompletní katalog ukazatelů a zdrojů (CSV)",
        data=csv_cat_buffer.getvalue().encode("utf-8-sig"),
        file_name=f"katalog_makro_ukazatelu_a_zdroju_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        key="btn_dl_catalog_csv"
    )

    # Přehled primárních institucí a datových toků
    st.markdown('<div class="section-header">Přehled primárních poskytovatelů dat a integrační architektura</div>', unsafe_allow_html=True)
    c_inst1, c_inst2 = st.columns(2)
    with c_inst1:
        st.markdown(
            """
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px 16px; margin-bottom: 12px;">
                <div style="font-weight: 750; color: #0f172a; font-size: 0.96rem; margin-bottom: 6px;">🇨🇿 Česká republika</div>
                <ul style="margin: 0; padding-left: 20px; font-size: 0.85rem; color: #475569; line-height: 1.5;">
                    <li><strong>Česká národní banka (ČNB):</strong> Otevřené REST API pro denní devizové kurzy v 14:30 (EUR, USD, PLN, GBP, JPY, CHF) a časové řady měnových sazeb (2T repo, diskontní, lombardní, 3M PRIBOR).</li>
                    <li><strong>Český statistický úřad (ČSÚ):</strong> Pravidelné konjunkturální a národní statistiky – HDP, celková inflace CPI, maloobchodní tržby a průmyslová produkce.</li>
                    <li><strong>Ministerstvo financí ČR (MF ČR):</strong> Měsíční pokladní plnění, vládní dluh a aukce státních dluhopisů CZGB.</li>
                    <li><strong>Burza cenných papírů Praha (BCPP / PSE):</strong> Oficiální cenový index PX pražské burzy.</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.markdown(
            """
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px 16px;">
                <div style="font-weight: 750; color: #0f172a; font-size: 0.96rem; margin-bottom: 6px;">🇪🇺 Evropská unie / Eurozóna</div>
                <ul style="margin: 0; padding-left: 20px; font-size: 0.85rem; color: #475569; line-height: 1.5;">
                    <li><strong>Eurostat:</strong> Oficiální JSON REST API pro harmonizovanou inflaci (HICP & Core HICP), HDP Eurozóny, míru nezaměstnanosti, vládní dluh (EDP) a referenční vládní dluhopisy.</li>
                    <li><strong>Evropská centrální banka (ECB) & EMMI:</strong> Klíčový sazbový koridor (DFR, MRO, MLF), referenční peněžní sazba €STR a 3M EURIBOR fixace.</li>
                    <li><strong>Deutsche Bundesbank:</strong> Benchmark výnosové křivky německých státních dluhopisů (Bund 2Y až 30Y).</li>
                    <li><strong>STOXX Ltd. (Deutsche Börse):</strong> Index 50 předních blue-chip společností Eurozóny Euro Stoxx 50.</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True
        )
    with c_inst2:
        st.markdown(
            """
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px 16px; margin-bottom: 12px;">
                <div style="font-weight: 750; color: #0f172a; font-size: 0.96rem; margin-bottom: 6px;">🇺🇸 Spojené státy americké</div>
                <ul style="margin: 0; padding-left: 20px; font-size: 0.85rem; color: #475569; line-height: 1.5;">
                    <li><strong>U.S. Department of the Treasury:</strong> Oficiální denní XML feed výnosové křivky státních dluhopisů (U.S. Treasury Par Yield Curve od 1M po 30Y) a federální dluh.</li>
                    <li><strong>Federal Reserve (Fed) & NY Fed:</strong> Fed Funds Target Range, EFFR, zajištěná sazba peněžního trhu SOFR a index průmyslové produkce (G.17).</li>
                    <li><strong>U.S. Bureau of Labor Statistics (BLS):</strong> Spotřebitelská inflace (Headline & Core CPI) a zpráva o zaměstnanosti (míra nezaměstnanosti U-3 a NFP).</li>
                    <li><strong>U.S. Bureau of Economic Analysis (BEA) & Census:</strong> Kvartální reálný a nominální HDP a maloobchodní tržby.</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.markdown(
            """
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px 16px;">
                <div style="font-weight: 750; color: #0f172a; font-size: 0.96rem; margin-bottom: 6px;">📈 Globální trhy & Agregace</div>
                <ul style="margin: 0; padding-left: 20px; font-size: 0.85rem; color: #475569; line-height: 1.5;">
                    <li><strong>Yahoo Finance API:</strong> Měsíční a denní historické i živé kotace indexů S&P 500 (^GSPC), NASDAQ Composite (^IXIC), Euro Stoxx 50 (^STOXX50E).</li>
                    <li><strong>Intercontinental Exchange (ICE) & FX trhy:</strong> Dolarový index DXY a křížové devizové kurzy měn G10 a CEE (EUR, USD, GBP, PLN, CZK).</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("---")
    with st.expander("📖 Prohlédnout kompletní Výkladový glosář makroekonomických pojmů přímo zde", expanded=False):
        if render_glossary_view:
            render_glossary_view()
