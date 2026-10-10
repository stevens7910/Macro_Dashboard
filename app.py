"""
app.py
======
Český & US Makroekonomický Dashboard ve Streamlit.
Přehledná, vysoce responzivní a modulární aplikace pro komplexní vizualizaci
a srovnání makroekonomických indikátorů České republiky a Spojených států amerických.
"""

from __future__ import annotations

import io
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from data_loader import (
    DataLoader,
    INDICATORS,
    CZ_INDICATORS,
    US_INDICATORS,
    get_cached_macro_data
)

# =============================================================================
# 1. KONFIGURACE STRÁNKY A STYLING
# =============================================================================

st.set_page_config(
    page_title="Makro Monitor | ČR & USA Macroeconomic Terminal",
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
            padding: 8px 10px !important;
        }
        div[data-testid="stMetricValue"] {
            font-size: 1.35rem !important;
        }
        .sa-header-container {
            padding: 12px 14px !important;
        }
        .sa-header-title {
            font-size: 1.20rem !important;
        }
    }
    
    /* Vzhled metrických KPI karet (Stock Analysis styl) */
    div[data-testid="stMetric"] {
        background-color: #ffffff !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 8px !important;
        padding: 12px 16px !important;
        box-shadow: none !important;
        transition: border-color 0.15s ease !important;
    }
    div[data-testid="stMetric"]:hover {
        border-color: #94a3b8 !important;
    }
    div[data-testid="stMetricLabel"] p {
        font-size: 0.78rem !important;
        font-weight: 600 !important;
        color: #64748b !important;
        text-transform: uppercase !important;
        letter-spacing: 0.04em !important;
        margin-bottom: 2px !important;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.60rem !important;
        font-weight: 700 !important;
        color: #0f172a !important;
        font-variant-numeric: tabular-nums !important;
    }
    div[data-testid="stMetricDelta"] {
        font-size: 0.82rem !important;
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
        margin-top: 1.1rem;
        margin-bottom: 0.4rem;
        display: flex;
        align-items: center;
        gap: 8px;
        border-left: 3px solid #2563eb;
        padding-left: 10px;
    }

    /* ZÁLOŽKY (TABS): MINIMALISTICKÝ DESIGN (STOCK ANALYSIS) */
    div[data-baseweb="tab-list"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
        gap: 2px 6px !important;
        border-bottom: 1px solid #e5e7eb !important;
        padding-bottom: 6px !important;
        margin-bottom: 1.3rem !important;
        overflow-x: auto !important;
        white-space: nowrap !important;
        scrollbar-width: thin !important;
        -webkit-overflow-scrolling: touch !important;
        background: transparent !important;
        width: 100% !important;
    }

    div[data-baseweb="tab-highlight"],
    div[data-baseweb="tab-border"] {
        display: none !important;
    }

    button[data-baseweb="tab"] {
        background-color: transparent !important;
        color: #475569 !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 6px 13px !important;
        font-size: 0.88rem !important;
        font-weight: 500 !important;
        transition: all 0.15s ease !important;
        white-space: nowrap !important;
        box-shadow: none !important;
        cursor: pointer !important;
        height: auto !important;
    }

    button[data-baseweb="tab"]:hover {
        background-color: #f1f5f9 !important;
        color: #0f172a !important;
    }

    button[data-baseweb="tab"][aria-selected="true"],
    button[data-baseweb="tab"][data-selected="true"] {
        background-color: #e9ecef !important;
        color: #0f172a !important;
        font-weight: 700 !important;
        border-radius: 6px !important;
    }

    button[data-baseweb="tab"][aria-selected="true"] p,
    button[data-baseweb="tab"][aria-selected="true"] span,
    button[data-baseweb="tab"][data-selected="true"] p,
    button[data-baseweb="tab"][data-selected="true"] span {
        color: #0f172a !important;
        font-weight: 700 !important;
    }

    /* TOP HEADER & KEY STATS PANELS */
    .sa-header-container {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 18px;
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
        gap: 16px 26px;
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
        font-size: 1.30rem;
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
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 18px;
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
        border-bottom: 1px solid #f1f5f9;
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
    # Na dotykových displejích vypneme scroll zoom, aby uživatel mohl hladce posouvat stránku prstem
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
# 3. VPRAVO NAHOŘE: PŘEPÍNAČ EKONOMIKY (ČR vs. USA)
# =============================================================================

col_top_left, col_top_right = st.columns([2.6, 1.4], vertical_alignment="center")

with col_top_left:
    st.markdown(
        """
        <div style="display: flex; align-items: center; gap: 10px; padding: 2px 0;">
            <span style="font-size: 1.4rem;">🏛️</span>
            <div>
                <div style="font-size: 1.15rem; font-weight: 800; color: #0F172A; letter-spacing: -0.02em;">MAKROEKONOMICKÝ MONITOR</div>
                <div style="font-size: 0.72rem; font-weight: 600; color: #64748B; text-transform: uppercase;">Institucionální analýza &bull; ČNB &bull; Federal Reserve &bull; Denní data</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col_top_right:
    # Přepínač vpravo nahoře
    economy_options = ["🇨🇿 Česká republika", "🇺🇸 Spojené státy"]
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


# =============================================================================
# 4. SIDEBAR: OVLÁDACÍ PRVKY A FILTRY
# =============================================================================

sidebar_badge = "ČR MACRO" if is_cz else "USA MACRO"
sidebar_sub = "ČNB &bull; Eurostat &bull; PRIBOR &bull; Křivka" if is_cz else "Fed &bull; BLS &bull; BEA &bull; Treasury &bull; DXY"

st.sidebar.markdown(
    f"""
    <div class="sidebar-brand-card">
        <div class="sidebar-brand-top">
            <span class="sidebar-brand-badge">{sidebar_badge}</span>
            <span class="sidebar-brand-version">TERMINAL</span>
        </div>
        <div class="sidebar-brand-title">Nastavení a filtry ({'ČR' if is_cz else 'USA'})</div>
        <div class="sidebar-brand-sub">{sidebar_sub}</div>
    </div>
    """,
    unsafe_allow_html=True
)

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

# 3. Výběr indikátorů podle aktivní ekonomiky
st.sidebar.markdown(
    """
    <div class="sidebar-section-header">
        <span class="sidebar-section-title">📊 Výběr ukazatelů</span>
        <span class="sidebar-section-badge">Metriky</span>
    </div>
    """,
    unsafe_allow_html=True
)

if is_cz:
    available_indicator_keys = list(CZ_INDICATORS.keys())
    default_indicators = [
        "repo_rate", "discount_rate", "lombard_rate",
        "pribor_3m", "cpi_yoy", "gdp_growth_real",
        "unemployment_rate", "eur_czk", "public_debt_gdp_pct", "czgb_10y"
    ]
else:
    available_indicator_keys = list(US_INDICATORS.keys())
    default_indicators = [
        "fed_funds_upper", "fed_funds_lower", "sofr_rate",
        "us_3m", "us_cpi_yoy", "us_core_cpi_yoy", "us_gdp_growth_real",
        "us_unemployment_rate", "dxy_index", "eur_usd", "us_public_debt_gdp_pct", "us_10y"
    ]

selected_indicators = st.sidebar.multiselect(
    f"Vyberte ukazatele pro {'ČR' if is_cz else 'USA'}:",
    options=available_indicator_keys,
    default=default_indicators,
    format_func=lambda k: f"{INDICATORS[k].category}: {INDICATORS[k].name_cz} ({INDICATORS[k].unit})"
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


# =============================================================================
# 5. NAČTENÍ DAT S CACHOVÁNÍM
# =============================================================================

with st.spinner("Načítám data z ČNB, Eurostatu a U.S. Department of the Treasury..."):
    df_raw, status_info, df_daily_fx = get_cached_macro_data(
        frequency=frequency_code,
        fred_api_key=fred_key_input,
        force_fallback=force_fallback
    )

if df_raw.empty:
    st.error("Nepodařilo se načíst žádná data. Zkuste aktivovat záložní fallback model v levém panelu.")
    st.stop()

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


# =============================================================================
# 7. HLAVNÍ PLOCHA DASHBOARDU: ZÁHLAVÍ & KEY METRICS (STOCK ANALYSIS STYL)
# =============================================================================

last_row = df.iloc[-1]
prev_row = df.iloc[-2] if len(df) > 1 else last_row

date_str = last_row.get("date").strftime("%d. %m. %Y") if hasattr(last_row.get("date"), "strftime") else "Aktuální"

# Hodnoty pro ČR
repo_curr = safe_metric(last_row, "repo_rate", 3.75)
repo_prev = safe_metric(prev_row, "repo_rate", repo_curr)
repo_delta = repo_curr - repo_prev

cpi_cz_curr = safe_metric(last_row, "cpi_yoy", 2.3)
cpi_cz_prev = safe_metric(prev_row, "cpi_yoy", cpi_cz_curr)
cpi_cz_delta = cpi_cz_curr - cpi_cz_prev

gdp_cz_curr = safe_metric(last_row, "gdp_growth_real", 1.2)
gdp_cz_prev = safe_metric(prev_row, "gdp_growth_real", gdp_cz_curr)
gdp_cz_delta = gdp_cz_curr - gdp_cz_prev

une_cz_curr = safe_metric(last_row, "unemployment_rate", 2.8)
une_cz_prev = safe_metric(prev_row, "unemployment_rate", une_cz_curr)
une_cz_delta = une_cz_curr - une_cz_prev

eur_cz_curr = safe_metric(last_row, "eur_czk", 25.10)
usd_cz_curr = safe_metric(last_row, "usd_czk", 23.20)
czgb10_curr = safe_metric(last_row, "czgb_10y", 4.10)
czgb2_curr = safe_metric(last_row, "czgb_2y", 3.70)
cz_spread_curr = safe_metric(last_row, "czgb_spread_10y_2y", round(czgb10_curr - czgb2_curr, 2))
prib3m_curr = safe_metric(last_row, "pribor_3m", 3.90)
disc_curr = safe_metric(last_row, "discount_rate", 2.75)
lomb_curr = safe_metric(last_row, "lombard_rate", 4.75)
debt_cz_pct = safe_metric(last_row, "public_debt_gdp_pct", 44.0)
deficit_cz_curr = safe_metric(last_row, "budget_deficit_czk_bn", -65.0)

# Hodnoty pro USA
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

une_us_curr = safe_metric(last_row, "us_unemployment_rate", 4.1)
une_us_prev = safe_metric(prev_row, "us_unemployment_rate", une_us_curr)
une_us_delta = une_us_curr - une_us_prev

dxy_curr = safe_metric(last_row, "dxy_index", 101.50)
dxy_prev = safe_metric(prev_row, "dxy_index", dxy_curr)
dxy_delta = dxy_curr - dxy_prev

eur_usd_curr = safe_metric(last_row, "eur_usd", 1.0850)
usd_jpy_curr = safe_metric(last_row, "usd_jpy", 152.40)
us10_curr = safe_metric(last_row, "us_10y", 4.30)
us2_curr = safe_metric(last_row, "us_2y", 4.10)
us_spread_curr = safe_metric(last_row, "us_spread_10y_2y", round(us10_curr - us2_curr, 2))
debt_us_pct = safe_metric(last_row, "us_public_debt_gdp_pct", 123.5)
debt_us_nom = safe_metric(last_row, "us_public_debt_usd_bn", 35500.0)

# Poslední denní FX data
last_daily_fx = df_daily_fx_filtered.iloc[-1] if not df_daily_fx_filtered.empty else last_row
prev_daily_fx = df_daily_fx_filtered.iloc[-2] if len(df_daily_fx_filtered) > 1 else last_daily_fx
daily_eur_czk = safe_metric(last_daily_fx, "eur_czk", eur_cz_curr)
daily_usd_czk = safe_metric(last_daily_fx, "usd_czk", usd_cz_curr)
daily_eur_usd = safe_metric(last_daily_fx, "eur_usd", eur_usd_curr)
daily_dxy = safe_metric(last_daily_fx, "dxy_index", dxy_curr)

# -----------------------------------------------------------------------------
# ZOBRAZENÍ TOP HERO BOXU A KEY STATS PODLE ZVOLENÉ ZEMĚ
# -----------------------------------------------------------------------------

if is_cz:
    st.markdown(
        f"""
        <div class="sa-header-container">
            <div class="sa-header-top">
                <div class="sa-header-title-box">
                    <h1 class="sa-header-title">🇨🇿 Česká republika</h1>
                    <span class="sa-ticker-badge">CZ MACRO MONITOR</span>
                </div>
                <div class="sa-header-meta">
                    <span class="sa-live-dot"></span>
                    <span><strong>TRHY AKTIVNÍ</strong> &bull; ČNB &bull; Eurostat &bull; {date_str}</span>
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
                    <span class="sa-hero-label">Reálný růst HDP</span>
                    <div class="sa-hero-val-row">
                        <span class="sa-hero-val">{gdp_cz_curr:+.1f} %</span>
                        <span class="{'sa-hero-change-pos' if gdp_cz_delta >= 0 else 'sa-hero-change-neg'}">{gdp_cz_delta:+.1f} p.b.</span>
                    </div>
                </div>
                <div class="sa-hero-item">
                    <span class="sa-hero-label">Nezaměstnanost</span>
                    <div class="sa-hero-val-row">
                        <span class="sa-hero-val">{une_cz_curr:.1f} %</span>
                        <span class="sa-hero-change-pos">ILO ČR</span>
                    </div>
                </div>
                <div class="sa-hero-item">
                    <span class="sa-hero-label">Kurz EUR/CZK (Denní)</span>
                    <div class="sa-hero-val-row">
                        <span class="sa-hero-val">{daily_eur_czk:.2f} Kč</span>
                        <span class="sa-hero-change-neutral">ČNB fix</span>
                    </div>
                </div>
                <div class="sa-hero-item">
                    <span class="sa-hero-label">10Y CZGB Výnos</span>
                    <div class="sa-hero-val-row">
                        <span class="sa-hero-val">{czgb10_curr:.2f} %</span>
                        <span class="sa-hero-change-neutral">Dluhopis</span>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 2-sloupcová tabulka pro ČR
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
                        <span class="sa-stat-label">Reálný růst HDP (YoY)</span>
                        <span class="sa-stat-val">{gdp_cz_curr:+.1f} % <span class="sa-hero-change-pos">{gdp_cz_delta:+.1f}</span></span>
                    </div>
                    <div class="sa-stat-row">
                        <span class="sa-stat-label">Míra nezaměstnanosti</span>
                        <span class="sa-stat-val">{une_cz_curr:.1f} % <span class="sa-hero-change-pos">Nejnižší v EU</span></span>
                    </div>
                </div>
                <div>
                    <div class="sa-stat-row">
                        <span class="sa-stat-label">Měnový kurz EUR/CZK (aktuální denní)</span>
                        <span class="sa-stat-val">{daily_eur_czk:.2f} Kč</span>
                    </div>
                    <div class="sa-stat-row">
                        <span class="sa-stat-label">Měnový kurz USD/CZK (aktuální denní)</span>
                        <span class="sa-stat-val">{daily_usd_czk:.2f} Kč</span>
                    </div>
                    <div class="sa-stat-row">
                        <span class="sa-stat-label">Výnos 10Y CZGB (státní dluhopis)</span>
                        <span class="sa-stat-val">{czgb10_curr:.2f} %</span>
                    </div>
                    <div class="sa-stat-row">
                        <span class="sa-stat-label">Výnos 2Y CZGB (krátký konec)</span>
                        <span class="sa-stat-val">{czgb2_curr:.2f} %</span>
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
                    <span class="sa-ticker-badge">US MACRO MONITOR</span>
                </div>
                <div class="sa-header-meta">
                    <span class="sa-live-dot"></span>
                    <span><strong>TRHY AKTIVNÍ</strong> &bull; Federal Reserve &bull; U.S. Treasury &bull; {date_str}</span>
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
                    <span class="sa-hero-label">SOFR / 3M T-Bill</span>
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
                    <span class="sa-hero-label">Reálný růst HDP USA</span>
                    <div class="sa-hero-val-row">
                        <span class="sa-hero-val">{gdp_us_curr:+.1f} %</span>
                        <span class="{'sa-hero-change-pos' if gdp_us_delta >= 0 else 'sa-hero-change-neg'}">{gdp_us_delta:+.1f} p.b.</span>
                    </div>
                </div>
                <div class="sa-hero-item">
                    <span class="sa-hero-label">Míra nezaměstnanosti USA</span>
                    <div class="sa-hero-val-row">
                        <span class="sa-hero-val">{une_us_curr:.1f} %</span>
                        <span class="sa-hero-change-pos">U-3 BLS</span>
                    </div>
                </div>
                <div class="sa-hero-item">
                    <span class="sa-hero-label">Dolarový index (DXY)</span>
                    <div class="sa-hero-val-row">
                        <span class="sa-hero-val">{daily_dxy:.2f}</span>
                        <span class="sa-hero-change-neutral">Globální koš</span>
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

    # 2-sloupcová tabulka pro USA
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
                        <span class="sa-stat-label">SOFR (Secured Overnight Rate)</span>
                        <span class="sa-stat-val">{sofr_curr:.2f} %</span>
                    </div>
                    <div class="sa-stat-row">
                        <span class="sa-stat-label">3M US Treasury Bill (peněžní trh)</span>
                        <span class="sa-stat-val">{us3m_curr:.2f} %</span>
                    </div>
                    <div class="sa-stat-row">
                        <span class="sa-stat-label">Spotřebitelská inflace (CPI Headline)</span>
                        <span class="sa-stat-val">{cpi_us_curr:.1f} % <span class="sa-hero-change-pos">Cíl 2.0 %</span></span>
                    </div>
                    <div class="sa-stat-row">
                        <span class="sa-stat-label">Jádrová inflace USA (Core CPI)</span>
                        <span class="sa-stat-val">{core_cpi_us_curr:.1f} %</span>
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
                        <span class="sa-stat-label">Dolarový index DXY (denní)</span>
                        <span class="sa-stat-val">{daily_dxy:.2f} bodů</span>
                    </div>
                    <div class="sa-stat-row">
                        <span class="sa-stat-label">Měnový kurz EUR/USD (denní)</span>
                        <span class="sa-stat-val">{daily_eur_usd:.4f} $</span>
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
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# =============================================================================
# 8. GENERÁTORY GRAFŮ (PLOTLY BUILDERS PRO ČR I USA)
# =============================================================================

# --- A. SAZBY ---
def build_rates_chart(dframe: pd.DataFrame, indicators: List[str]) -> go.Figure:
    """Graf měnové politiky ČNB (úrokový koridor) a PRIBOR sazeb."""
    fig = go.Figure()

    if "lombard_rate" in indicators and "lombard_rate" in dframe.columns:
        fig.add_trace(go.Scatter(
            x=dframe["date"],
            y=dframe["lombard_rate"],
            mode="lines",
            name="Lombardní sazba ČNB (horní mez)",
            line=dict(color="rgba(148, 163, 184, 0.7)", width=1.5, dash="dash"),
            hoverinfo="x+y+name"
        ))

    if "discount_rate" in indicators and "discount_rate" in dframe.columns:
        fig.add_trace(go.Scatter(
            x=dframe["date"],
            y=dframe["discount_rate"],
            mode="lines",
            name="Diskontní sazba ČNB (dolní mez)",
            line=dict(color="rgba(148, 163, 184, 0.7)", width=1.5, dash="dash"),
            fill="tonexty" if ("lombard_rate" in indicators and "lombard_rate" in dframe.columns) else None,
            fillcolor="rgba(226, 232, 240, 0.35)",
            hoverinfo="x+y+name"
        ))

    if "repo_rate" in indicators and "repo_rate" in dframe.columns:
        fig.add_trace(go.Scatter(
            x=dframe["date"],
            y=dframe["repo_rate"],
            mode="lines",
            name="2T Repo sazba ČNB (klíčová)",
            line=dict(color="#1D4ED8", width=3.5, shape="hv"),
            hovertemplate="<b>2T Repo sazba</b>: %{y:.2f} %<extra></extra>"
        ))

    pribor_colors = {
        "pribor_1m": ("#06B6D4", "PRIBOR 1M", 1.5),
        "pribor_3m": ("#0D9488", "PRIBOR 3M (benchmark)", 2.4),
        "pribor_6m": ("#047857", "PRIBOR 6M", 1.5)
    }
    for p_col, (p_color, p_name, p_width) in pribor_colors.items():
        if p_col in indicators and p_col in dframe.columns:
            fig.add_trace(go.Scatter(
                x=dframe["date"],
                y=dframe[p_col],
                mode="lines",
                name=p_name,
                line=dict(color=p_color, width=p_width, dash="dot" if p_col != "pribor_3m" else "solid"),
                hovertemplate=f"<b>{p_name}</b>: %{{y:.2f}} %<extra></extra>"
            ))

    fig.update_layout(
        height=430,
        hovermode="x unified",
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor="rgba(255, 255, 255, 0.8)"),
        xaxis=dict(title="", showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(title="Úrokové sazby (%)", title_font=dict(color="#1D4ED8"), tickfont=dict(color="#1D4ED8"), showgrid=True, gridcolor="#f1f5f9", ticksuffix=" %"),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF"
    )
    return fig


def build_us_rates_chart(dframe: pd.DataFrame, indicators: List[str]) -> go.Figure:
    """Graf měnové politiky Fedu (cílový koridor) a peněžního trhu USA (SOFR & T-Bills)."""
    fig = go.Figure()

    if "fed_funds_upper" in indicators and "fed_funds_upper" in dframe.columns:
        fig.add_trace(go.Scatter(
            x=dframe["date"],
            y=dframe["fed_funds_upper"],
            mode="lines",
            name="Fed Funds Target (horní limit)",
            line=dict(color="rgba(148, 163, 184, 0.8)", width=1.5, dash="dash"),
            hoverinfo="x+y+name"
        ))

    if "fed_funds_lower" in indicators and "fed_funds_lower" in dframe.columns:
        fig.add_trace(go.Scatter(
            x=dframe["date"],
            y=dframe["fed_funds_lower"],
            mode="lines",
            name="Fed Funds Target (dolní limit)",
            line=dict(color="rgba(148, 163, 184, 0.8)", width=1.5, dash="dash"),
            fill="tonexty" if ("fed_funds_upper" in indicators and "fed_funds_upper" in dframe.columns) else None,
            fillcolor="rgba(226, 232, 240, 0.35)",
            hoverinfo="x+y+name"
        ))

    if "fed_effective_rate" in indicators and "fed_effective_rate" in dframe.columns:
        fig.add_trace(go.Scatter(
            x=dframe["date"],
            y=dframe["fed_effective_rate"],
            mode="lines",
            name="Efektivní Fed Funds (EFFR)",
            line=dict(color="#1D4ED8", width=3.2, shape="hv"),
            hovertemplate="<b>EFFR</b>: %{y:.2f} %<extra></extra>"
        ))

    if "sofr_rate" in indicators and "sofr_rate" in dframe.columns:
        fig.add_trace(go.Scatter(
            x=dframe["date"],
            y=dframe["sofr_rate"],
            mode="lines",
            name="SOFR (Secured Overnight Rate)",
            line=dict(color="#0D9488", width=2.2),
            hovertemplate="<b>SOFR</b>: %{y:.2f} %<extra></extra>"
        ))

    if "us_3m" in indicators and "us_3m" in dframe.columns:
        fig.add_trace(go.Scatter(
            x=dframe["date"],
            y=dframe["us_3m"],
            mode="lines",
            name="3M US Treasury Bill",
            line=dict(color="#D97706", width=2.0, dash="dot"),
            hovertemplate="<b>3M T-Bill</b>: %{y:.2f} %<extra></extra>"
        ))

    fig.update_layout(
        height=430,
        hovermode="x unified",
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor="rgba(255, 255, 255, 0.8)"),
        xaxis=dict(title="", showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(title="Úrokové sazby USD (%)", title_font=dict(color="#1D4ED8"), tickfont=dict(color="#1D4ED8"), showgrid=True, gridcolor="#f1f5f9", ticksuffix=" %"),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF"
    )
    return fig


# --- B. INFLACE ---
def build_inflation_chart(dframe: pd.DataFrame) -> go.Figure:
    """Detailní graf inflace v ČR s inflačním cílem ČNB a reálnou úrokovou sazbou."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_hrect(
        y0=1.0, y1=3.0,
        fillcolor="rgba(34, 197, 94, 0.12)",
        line_width=0,
        annotation_text="Toleranční pásmo ČNB (1–3 %)",
        annotation_position="top left",
        annotation_font=dict(color="#166534", size=11),
        secondary_y=False
    )

    fig.add_hline(
        y=2.0,
        line=dict(color="#16A34A", width=1.8, dash="dash"),
        annotation_text="Inflační cíl (2.0 %)",
        annotation_position="bottom right",
        annotation_font=dict(color="#16A34A", size=11),
        secondary_y=False
    )

    if "cpi_yoy" in dframe.columns:
        fig.add_trace(
            go.Scatter(
                x=dframe["date"],
                y=dframe["cpi_yoy"],
                mode="lines+markers",
                name="Inflace CPI (meziročně v %)",
                line=dict(color="#DC2626", width=3.0),
                marker=dict(size=5, color="#DC2626"),
                hovertemplate="<b>Inflace CPI ČR</b>: %{y:.1f} %<extra></extra>"
            ),
            secondary_y=False
        )

    if "repo_rate" in dframe.columns and "cpi_yoy" in dframe.columns:
        real_rate = dframe["repo_rate"] - dframe["cpi_yoy"]
        fig.add_trace(
            go.Scatter(
                x=dframe["date"],
                y=real_rate,
                mode="lines",
                name="Reálná sazba (Repo − CPI)",
                line=dict(color="#6366F1", width=2.0, dash="dot"),
                hovertemplate="<b>Reálná sazba</b>: %{y:.1f} %<extra></extra>"
            ),
            secondary_y=True
        )
        fig.add_hline(y=0.0, line=dict(color="#94A3B8", width=1.2, dash="dash"), secondary_y=True)

    fig.update_layout(
        height=430,
        hovermode="x unified",
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor="rgba(255, 255, 255, 0.8)"),
        xaxis=dict(title="", showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(title="Meziroční inflace CPI (%)", title_font=dict(color="#DC2626"), tickfont=dict(color="#DC2626"), showgrid=True, gridcolor="#f1f5f9", ticksuffix=" %"),
        yaxis2=dict(title="Reálná úroková míra (%)", title_font=dict(color="#6366F1"), tickfont=dict(color="#6366F1"), overlaying="y", side="right", showgrid=False, ticksuffix=" %"),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF"
    )
    return fig


def build_us_inflation_chart(dframe: pd.DataFrame) -> go.Figure:
    """Graf inflace v USA (Headline CPI a Core CPI) s 2.0% cílem Fedu a reálnou sazbou."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_hline(
        y=2.0,
        line=dict(color="#16A34A", width=1.8, dash="dash"),
        annotation_text="Inflační cíl Fedu (2.0 %)",
        annotation_position="bottom right",
        annotation_font=dict(color="#16A34A", size=11),
        secondary_y=False
    )

    if "us_cpi_yoy" in dframe.columns:
        fig.add_trace(
            go.Scatter(
                x=dframe["date"],
                y=dframe["us_cpi_yoy"],
                mode="lines+markers",
                name="Headline CPI USA (meziročně v %)",
                line=dict(color="#DC2626", width=3.0),
                marker=dict(size=4, color="#DC2626"),
                hovertemplate="<b>Headline CPI</b>: %{y:.1f} %<extra></extra>"
            ),
            secondary_y=False
        )

    if "us_core_cpi_yoy" in dframe.columns:
        fig.add_trace(
            go.Scatter(
                x=dframe["date"],
                y=dframe["us_core_cpi_yoy"],
                mode="lines",
                name="Jádrová inflace (Core CPI)",
                line=dict(color="#D97706", width=2.4, dash="solid"),
                hovertemplate="<b>Core CPI</b>: %{y:.1f} %<extra></extra>"
            ),
            secondary_y=False
        )

    if "fed_effective_rate" in dframe.columns and "us_cpi_yoy" in dframe.columns:
        real_us_rate = dframe["fed_effective_rate"] - dframe["us_cpi_yoy"]
        fig.add_trace(
            go.Scatter(
                x=dframe["date"],
                y=real_us_rate,
                mode="lines",
                name="Reálná sazba (Fed EFFR − CPI)",
                line=dict(color="#6366F1", width=2.0, dash="dot"),
                hovertemplate="<b>Reálná sazba USA</b>: %{y:.1f} %<extra></extra>"
            ),
            secondary_y=True
        )
        fig.add_hline(y=0.0, line=dict(color="#94A3B8", width=1.2, dash="dash"), secondary_y=True)

    fig.update_layout(
        height=430,
        hovermode="x unified",
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor="rgba(255, 255, 255, 0.8)"),
        xaxis=dict(title="", showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(title="Inflace USA (% YoY)", title_font=dict(color="#DC2626"), tickfont=dict(color="#DC2626"), showgrid=True, gridcolor="#f1f5f9", ticksuffix=" %"),
        yaxis2=dict(title="Reálná úroková míra USA (%)", title_font=dict(color="#6366F1"), tickfont=dict(color="#6366F1"), overlaying="y", side="right", showgrid=False, ticksuffix=" %"),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF"
    )
    return fig


# --- C. HDP ---
def build_gdp_chart(dframe: pd.DataFrame, indicators: List[str]) -> go.Figure:
    """Kombinovaný graf HDP ČR (nominál v mld. CZK a reálný růst v %)."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    df_gdp_plot = dframe.drop_duplicates(subset=["quarter"] if "quarter" in dframe.columns else ["date"]).copy()

    if "gdp_nominal_czk_bn" in indicators and "gdp_nominal_czk_bn" in dframe.columns:
        fig.add_trace(
            go.Bar(
                x=df_gdp_plot["date"],
                y=df_gdp_plot["gdp_nominal_czk_bn"],
                name="Nominální HDP (mld. CZK)",
                marker=dict(color="rgba(71, 85, 105, 0.55)", line=dict(color="#334155", width=1)),
                hovertemplate="<b>Nominální HDP ČR</b>: %{y:,.1f} mld. CZK<extra></extra>"
            ),
            secondary_y=False
        )

    if "gdp_growth_real" in indicators and "gdp_growth_real" in dframe.columns:
        marker_colors = ["#16A34A" if val >= 0 else "#DC2626" for val in df_gdp_plot["gdp_growth_real"]]
        fig.add_trace(
            go.Scatter(
                x=df_gdp_plot["date"],
                y=df_gdp_plot["gdp_growth_real"],
                mode="lines+markers",
                name="Reálný růst HDP ČR (YoY %)",
                line=dict(color="#D97706", width=3),
                marker=dict(size=7, color=marker_colors, line=dict(color="#FFFFFF", width=1.5)),
                hovertemplate="<b>Reálný růst ČR</b>: %{y:+.1f} %<extra></extra>"
            ),
            secondary_y=True
        )
        fig.add_hline(y=0.0, line=dict(color="#94A3B8", width=1.5, dash="dash"), secondary_y=True)

    fig.update_layout(
        height=430,
        hovermode="x unified",
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor="rgba(255, 255, 255, 0.8)"),
        xaxis=dict(title="", showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(title="Nominální HDP (mld. CZK)", title_font=dict(color="#334155"), tickfont=dict(color="#334155"), showgrid=True, gridcolor="#f1f5f9", ticksuffix=" mld."),
        yaxis2=dict(title="Reálný růst HDP (YoY %)", title_font=dict(color="#D97706"), tickfont=dict(color="#D97706"), overlaying="y", side="right", showgrid=False, ticksuffix=" %"),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF"
    )
    return fig


def build_us_gdp_chart(dframe: pd.DataFrame, indicators: List[str]) -> go.Figure:
    """Kombinovaný graf HDP USA (nominál v mld. USD a reálný růst v %)."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    df_gdp_plot = dframe.drop_duplicates(subset=["quarter"] if "quarter" in dframe.columns else ["date"]).copy()

    if "us_gdp_nominal_usd_bn" in indicators and "us_gdp_nominal_usd_bn" in dframe.columns:
        fig.add_trace(
            go.Bar(
                x=df_gdp_plot["date"],
                y=df_gdp_plot["us_gdp_nominal_usd_bn"],
                name="Nominální HDP USA (mld. USD)",
                marker=dict(color="rgba(30, 41, 59, 0.55)", line=dict(color="#0f172a", width=1)),
                hovertemplate="<b>Nominální HDP USA</b>: %{y:,.0f} mld. USD<extra></extra>"
            ),
            secondary_y=False
        )

    if "us_gdp_growth_real" in indicators and "us_gdp_growth_real" in dframe.columns:
        marker_colors = ["#16A34A" if val >= 0 else "#DC2626" for val in df_gdp_plot["us_gdp_growth_real"]]
        fig.add_trace(
            go.Scatter(
                x=df_gdp_plot["date"],
                y=df_gdp_plot["us_gdp_growth_real"],
                mode="lines+markers",
                name="Reálný růst HDP USA (YoY %)",
                line=dict(color="#2563EB", width=3),
                marker=dict(size=7, color=marker_colors, line=dict(color="#FFFFFF", width=1.5)),
                hovertemplate="<b>Reálný růst USA</b>: %{y:+.1f} %<extra></extra>"
            ),
            secondary_y=True
        )
        fig.add_hline(y=0.0, line=dict(color="#94A3B8", width=1.5, dash="dash"), secondary_y=True)

    fig.update_layout(
        height=430,
        hovermode="x unified",
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor="rgba(255, 255, 255, 0.8)"),
        xaxis=dict(title="", showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(title="Nominální HDP USA (mld. USD)", title_font=dict(color="#0f172a"), tickfont=dict(color="#0f172a"), showgrid=True, gridcolor="#f1f5f9", ticksuffix=" mld. $"),
        yaxis2=dict(title="Reálný růst HDP USA (YoY %)", title_font=dict(color="#2563EB"), tickfont=dict(color="#2563EB"), overlaying="y", side="right", showgrid=False, ticksuffix=" %"),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF"
    )
    return fig


# --- D. TRH PRÁCE ---
def build_unemployment_chart(dframe: pd.DataFrame) -> go.Figure:
    """Plošný graf míry nezaměstnanosti v ČR s průměrem a extrémy."""
    fig = go.Figure()

    if "unemployment_rate" in dframe.columns:
        fig.add_trace(go.Scatter(
            x=dframe["date"],
            y=dframe["unemployment_rate"],
            mode="lines",
            name="Míra nezaměstnanosti v ČR",
            line=dict(color="#4F46E5", width=2.8),
            fill="tozeroy",
            fillcolor="rgba(79, 70, 229, 0.08)",
            hovertemplate="<b>Nezaměstnanost ČR</b>: %{y:.1f} %<extra></extra>"
        ))

        avg_une = dframe["unemployment_rate"].mean()
        fig.add_hline(
            y=avg_une,
            line=dict(color="#64748B", width=1.5, dash="dash"),
            annotation_text=f"Průměr: {avg_une:.2f} %",
            annotation_position="top right",
            annotation_font=dict(color="#64748B", size=11)
        )

        min_val = dframe["unemployment_rate"].min()
        max_val = dframe["unemployment_rate"].max()
        min_row = dframe.loc[dframe["unemployment_rate"] == min_val].iloc[0]
        max_row = dframe.loc[dframe["unemployment_rate"] == max_val].iloc[0]

        fig.add_trace(go.Scatter(
            x=[min_row["date"], max_row["date"]],
            y=[min_val, max_val],
            mode="markers+text",
            name="Extrémy (Min / Max)",
            marker=dict(size=8, color=["#16A34A", "#DC2626"]),
            text=[f"Min: {min_val:.1f} %", f"Max: {max_val:.1f} %"],
            textposition=["bottom center", "top center"],
            showlegend=False,
            hoverinfo="skip"
        ))

        fig.update_layout(
            height=430,
            hovermode="x unified",
            margin=dict(l=20, r=20, t=30, b=20),
            xaxis=dict(title="", showgrid=True, gridcolor="#f1f5f9"),
            yaxis=dict(title="Míra nezaměstnanosti (%)", ticksuffix=" %", showgrid=True, gridcolor="#f1f5f9", range=[0, max(6.0, max_val + 1.0)]),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            plot_bgcolor="#FFFFFF",
            paper_bgcolor="#FFFFFF"
        )
    return fig


def build_us_unemployment_chart(dframe: pd.DataFrame) -> go.Figure:
    """Graf trhu práce v USA (míra nezaměstnanosti U-3)."""
    fig = go.Figure()

    if "us_unemployment_rate" in dframe.columns:
        fig.add_trace(go.Scatter(
            x=dframe["date"],
            y=dframe["us_unemployment_rate"],
            mode="lines",
            name="Míra nezaměstnanosti USA (U-3)",
            line=dict(color="#2563EB", width=2.8),
            fill="tozeroy",
            fillcolor="rgba(37, 99, 235, 0.08)",
            hovertemplate="<b>Nezaměstnanost USA</b>: %{y:.1f} %<extra></extra>"
        ))

        avg_une = dframe["us_unemployment_rate"].mean()
        fig.add_hline(
            y=avg_une,
            line=dict(color="#64748B", width=1.5, dash="dash"),
            annotation_text=f"Průměr USA: {avg_une:.2f} %",
            annotation_position="top right",
            annotation_font=dict(color="#64748B", size=11)
        )

        min_val = dframe["us_unemployment_rate"].min()
        max_val = dframe["us_unemployment_rate"].max()
        min_row = dframe.loc[dframe["us_unemployment_rate"] == min_val].iloc[0]
        max_row = dframe.loc[dframe["us_unemployment_rate"] == max_val].iloc[0]

        fig.add_trace(go.Scatter(
            x=[min_row["date"], max_row["date"]],
            y=[min_val, max_val],
            mode="markers+text",
            name="Extrémy",
            marker=dict(size=8, color=["#16A34A", "#DC2626"]),
            text=[f"Min: {min_val:.1f} %", f"Max: {max_val:.1f} % (Covid)"],
            textposition=["bottom center", "top center"],
            showlegend=False,
            hoverinfo="skip"
        ))

        fig.update_layout(
            height=430,
            hovermode="x unified",
            margin=dict(l=20, r=20, t=30, b=20),
            xaxis=dict(title="", showgrid=True, gridcolor="#f1f5f9"),
            yaxis=dict(title="Míra nezaměstnanosti USA (%)", ticksuffix=" %", showgrid=True, gridcolor="#f1f5f9", range=[0, max(8.0, max_val + 1.0)]),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            plot_bgcolor="#FFFFFF",
            paper_bgcolor="#FFFFFF"
        )
    return fig


# --- E. MĚNOVÉ KURZY (DENNÍ DATA) ---
def build_fx_daily_chart_cz(dframe_daily: pd.DataFrame) -> go.Figure:
    """Vysokofrekvenční graf denních devizových kurzů EUR/CZK a USD/CZK."""
    fig = go.Figure()

    if "eur_czk" in dframe_daily.columns:
        fig.add_trace(go.Scatter(
            x=dframe_daily["date"],
            y=dframe_daily["eur_czk"],
            mode="lines",
            name="EUR / CZK (Denní fixace)",
            line=dict(color="#2563EB", width=2.4),
            hovertemplate="<b>EUR/CZK (denní)</b>: %{y:.4f} Kč<extra></extra>"
        ))

    if "usd_czk" in dframe_daily.columns:
        fig.add_trace(go.Scatter(
            x=dframe_daily["date"],
            y=dframe_daily["usd_czk"],
            mode="lines",
            name="USD / CZK (Denní fixace)",
            line=dict(color="#059669", width=2.0),
            hovertemplate="<b>USD/CZK (denní)</b>: %{y:.4f} Kč<extra></extra>"
        ))

    fig.add_hline(
        y=27.00,
        line=dict(color="#DC2626", width=1.4, dash="dash"),
        annotation_text="Dřívější kurzový závazek ČNB (27.00 Kč/€)",
        annotation_position="bottom right",
        annotation_font=dict(color="#DC2626", size=10)
    )

    fig.update_layout(
        height=450,
        hovermode="x unified",
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis=dict(title="", showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(title="Denní směnný kurz (Kč)", ticksuffix=" Kč", showgrid=True, gridcolor="#f1f5f9"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor="rgba(255, 255, 255, 0.8)"),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF"
    )
    return fig


def build_fx_daily_chart_us(dframe_daily: pd.DataFrame) -> go.Figure:
    """Vysokofrekvenční graf světových devizových kurzů a DXY indexu."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    if "dxy_index" in dframe_daily.columns:
        fig.add_trace(
            go.Scatter(
                x=dframe_daily["date"],
                y=dframe_daily["dxy_index"],
                mode="lines",
                name="U.S. Dollar Index (DXY)",
                line=dict(color="#1E293B", width=2.6),
                hovertemplate="<b>DXY Index (denní)</b>: %{y:.2f} b.<extra></extra>"
            ),
            secondary_y=False
        )

    if "eur_usd" in dframe_daily.columns:
        fig.add_trace(
            go.Scatter(
                x=dframe_daily["date"],
                y=dframe_daily["eur_usd"],
                mode="lines",
                name="EUR / USD (Denní kurz)",
                line=dict(color="#2563EB", width=2.0),
                hovertemplate="<b>EUR/USD (denní)</b>: %{y:.4f} $<extra></extra>"
            ),
            secondary_y=True
        )

    if "gbp_usd" in dframe_daily.columns:
        fig.add_trace(
            go.Scatter(
                x=dframe_daily["date"],
                y=dframe_daily["gbp_usd"],
                mode="lines",
                name="GBP / USD (Cable)",
                line=dict(color="#D97706", width=1.8, dash="dot"),
                hovertemplate="<b>GBP/USD</b>: %{y:.4f} $<extra></extra>"
            ),
            secondary_y=True
        )

    fig.update_layout(
        height=450,
        hovermode="x unified",
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis=dict(title="", showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(title="Dolarový index DXY (body)", title_font=dict(color="#1E293B"), tickfont=dict(color="#1E293B"), showgrid=True, gridcolor="#f1f5f9"),
        yaxis2=dict(title="Měnový kurz EUR/USD & GBP/USD ($)", title_font=dict(color="#2563EB"), tickfont=dict(color="#2563EB"), overlaying="y", side="right", showgrid=False, ticksuffix=" $"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor="rgba(255, 255, 255, 0.8)"),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF"
    )
    return fig


# --- F. VEŘEJNÝ DLUH & FISKÁL ---
def build_debt_charts(dframe: pd.DataFrame) -> Tuple[go.Figure, go.Figure]:
    """Grafy pro veřejný dluh ČR (% HDP) a saldo státního rozpočtu."""
    df_q_plot = dframe.drop_duplicates(subset=["quarter"] if "quarter" in dframe.columns else ["date"]).copy()

    fig_debt = go.Figure()
    if "public_debt_gdp_pct" in df_q_plot.columns:
        fig_debt.add_hrect(
            y0=0, y1=60.0,
            fillcolor="rgba(34, 197, 94, 0.08)",
            line_width=0,
            annotation_text="Pásmo maastrichtského limitu (< 60 % HDP)",
            annotation_position="top left",
            annotation_font=dict(color="#15803d", size=11)
        )
        fig_debt.add_hline(
            y=60.0,
            line=dict(color="#DC2626", width=2.0, dash="dash"),
            annotation_text="Maastrichtský limit (60.0 % HDP)",
            annotation_position="bottom right",
            annotation_font=dict(color="#DC2626", size=11)
        )
        fig_debt.add_trace(go.Scatter(
            x=df_q_plot["date"],
            y=df_q_plot["public_debt_gdp_pct"],
            mode="lines+markers",
            name="Veřejný dluh ČR (% HDP)",
            line=dict(color="#4F46E5", width=3.0),
            marker=dict(size=6, color="#4F46E5"),
            hovertemplate="<b>Dluh k HDP</b>: %{y:.1f} %<extra></extra>"
        ))

    fig_debt.update_layout(
        height=380,
        hovermode="x unified",
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis=dict(title="", showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(title="Veřejný dluh (% HDP)", ticksuffix=" %", showgrid=True, gridcolor="#f1f5f9", range=[20, 90]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF"
    )

    fig_def = go.Figure()
    if "budget_deficit_czk_bn" in df_q_plot.columns:
        bar_colors = ["#16A34A" if v >= 0 else "#DC2626" for v in df_q_plot["budget_deficit_czk_bn"]]
        fig_def.add_trace(go.Bar(
            x=df_q_plot["date"],
            y=df_q_plot["budget_deficit_czk_bn"],
            name="Kvartální saldo rozpočtu",
            marker=dict(color=bar_colors),
            hovertemplate="<b>Saldo SR</b>: %{y:,.1f} mld. Kč<extra></extra>"
        ))
        fig_def.add_hline(y=0.0, line=dict(color="#334155", width=1.0))

    fig_def.update_layout(
        height=380,
        hovermode="x unified",
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis=dict(title="", showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(title="Saldo rozpočtu (mld. CZK)", ticksuffix=" mld.", showgrid=True, gridcolor="#f1f5f9"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF"
    )
    return fig_debt, fig_def


def build_us_debt_charts(dframe: pd.DataFrame) -> Tuple[go.Figure, go.Figure]:
    """Grafy pro federální dluh USA (% HDP a objem v mld. USD) a federální deficit."""
    df_q_plot = dframe.drop_duplicates(subset=["quarter"] if "quarter" in dframe.columns else ["date"]).copy()

    fig_debt = go.Figure()
    if "us_public_debt_gdp_pct" in df_q_plot.columns:
        fig_debt.add_hline(
            y=100.0,
            line=dict(color="#D97706", width=1.8, dash="dash"),
            annotation_text="Hranice 100 % HDP",
            annotation_position="bottom right",
            annotation_font=dict(color="#D97706", size=11)
        )
        fig_debt.add_trace(go.Scatter(
            x=df_q_plot["date"],
            y=df_q_plot["us_public_debt_gdp_pct"],
            mode="lines+markers",
            name="Federální dluh USA (% HDP)",
            line=dict(color="#DC2626", width=3.0),
            marker=dict(size=6, color="#DC2626"),
            hovertemplate="<b>Dluh USA k HDP</b>: %{y:.1f} %<extra></extra>"
        ))

    fig_debt.update_layout(
        height=380,
        hovermode="x unified",
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis=dict(title="", showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(title="Dluh USA (% HDP)", ticksuffix=" %", showgrid=True, gridcolor="#f1f5f9", range=[80, 140]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF"
    )

    fig_def = go.Figure()
    if "us_budget_deficit_usd_bn" in df_q_plot.columns:
        bar_colors = ["#16A34A" if v >= 0 else "#DC2626" for v in df_q_plot["us_budget_deficit_usd_bn"]]
        fig_def.add_trace(go.Bar(
            x=df_q_plot["date"],
            y=df_q_plot["us_budget_deficit_usd_bn"],
            name="Kvartální federální deficit",
            marker=dict(color=bar_colors),
            hovertemplate="<b>Deficit USA</b>: %{y:,.0f} mld. USD<extra></extra>"
        ))
        fig_def.add_hline(y=0.0, line=dict(color="#334155", width=1.0))

    fig_def.update_layout(
        height=380,
        hovermode="x unified",
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis=dict(title="", showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(title="Saldo federálního rozpočtu (mld. USD)", ticksuffix=" mld. $", showgrid=True, gridcolor="#f1f5f9"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF"
    )
    return fig_debt, fig_def


# --- G. VÝNOSOVÉ KŘIVKY ---
def build_yield_curve_snapshot(df_row: pd.Series, compare_row: Optional[pd.Series] = None) -> go.Figure:
    """Časová struktura české výnosové křivky CZGB a úrokových swapů IRS."""
    tenor_labels = ["1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "15Y"]
    tenor_keys = ["1y", "2y", "3y", "5y", "7y", "10y", "15y"]

    czgb_vals = [df_row.get(f"czgb_{k}") for k in tenor_keys]
    irs_vals = [df_row.get(f"irs_{k}") for k in tenor_keys]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=tenor_labels,
        y=czgb_vals,
        mode="lines+markers+text",
        name="Státní dluhopisy (CZGB)",
        line=dict(color="#1D4ED8", width=3.2),
        marker=dict(size=8, color="#1D4ED8"),
        text=[f"{v:.2f} %" if v is not None else "" for v in czgb_vals],
        textposition="top center",
        hovertemplate="<b>CZGB %{x}</b>: %{y:.2f} % p.a.<extra></extra>"
    ))
    fig.add_trace(go.Scatter(
        x=tenor_labels,
        y=irs_vals,
        mode="lines+markers",
        name="Úrokové swapy (CZK IRS)",
        line=dict(color="#0D9488", width=2.5, dash="dash"),
        marker=dict(size=7, color="#0D9488"),
        hovertemplate="<b>CZK IRS %{x}</b>: %{y:.2f} % p.a.<extra></extra>"
    ))

    if compare_row is not None:
        comp_czgb = [compare_row.get(f"czgb_{k}") for k in tenor_keys]
        fig.add_trace(go.Scatter(
            x=tenor_labels,
            y=comp_czgb,
            mode="lines+markers",
            name="CZGB (Před rokem)",
            line=dict(color="#94A3B8", width=1.8, dash="dot"),
            marker=dict(size=6, color="#94A3B8"),
            hovertemplate="<b>CZGB (historie) %{x}</b>: %{y:.2f} % p.a.<extra></extra>"
        ))

    fig.update_layout(
        height=400,
        hovermode="x unified",
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis=dict(title="Splatnost", showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(title="Výnos do splatnosti (% p.a.)", ticksuffix=" %", showgrid=True, gridcolor="#f1f5f9"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF"
    )
    return fig


def build_us_yield_curve_snapshot(df_row: pd.Series, compare_row: Optional[pd.Series] = None) -> go.Figure:
    """Časová struktura americké výnosové křivky (U.S. Treasury 1M–30Y)."""
    tenor_labels = ["1M", "3M", "6M", "1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y"]
    tenor_keys = ["1m", "3m", "6m", "1y", "2y", "3y", "5y", "7y", "10y", "20y", "30y"]

    us_vals = [df_row.get(f"us_{k}") for k in tenor_keys]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=tenor_labels,
        y=us_vals,
        mode="lines+markers+text",
        name="U.S. Treasury (Aktuální)",
        line=dict(color="#2563EB", width=3.4),
        marker=dict(size=8, color="#2563EB"),
        text=[f"{v:.2f} %" if (v is not None and not pd.isna(v)) else "" for v in us_vals],
        textposition="top center",
        hovertemplate="<b>US Treasury %{x}</b>: %{y:.2f} % p.a.<extra></extra>"
    ))

    if compare_row is not None:
        comp_vals = [compare_row.get(f"us_{k}") for k in tenor_keys]
        fig.add_trace(go.Scatter(
            x=tenor_labels,
            y=comp_vals,
            mode="lines+markers",
            name="U.S. Treasury (Před rokem)",
            line=dict(color="#94A3B8", width=2.0, dash="dot"),
            marker=dict(size=6, color="#94A3B8"),
            hovertemplate="<b>US Treasury (historie) %{x}</b>: %{y:.2f} % p.a.<extra></extra>"
        ))

    fig.update_layout(
        height=400,
        hovermode="x unified",
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis=dict(title="Splatnost", showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(title="Výnos do splatnosti (% p.a.)", ticksuffix=" %", showgrid=True, gridcolor="#f1f5f9"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF"
    )
    return fig


def build_us_curve_spread_chart(dframe: pd.DataFrame) -> go.Figure:
    """Graf sklonu výnosové křivky USA (Spread 10Y − 2Y v bps) | Indikátor recese."""
    fig = go.Figure()
    if "us_spread_10y_2y" in dframe.columns:
        spread_bps = dframe["us_spread_10y_2y"] * 100.0
        fig.add_trace(go.Scatter(
            x=dframe["date"],
            y=spread_bps,
            mode="lines",
            name="Sklon US křivky (10Y − 2Y)",
            line=dict(color="#2563EB", width=2.5),
            hovertemplate="<b>US Sklon (10Y - 2Y)</b>: %{y:+.0f} bps<extra></extra>"
        ))
        fig.add_hline(
            y=0.0,
            line=dict(color="#DC2626", width=1.8, dash="dash"),
            annotation_text="Hranice inverze (0 bps) - Indikátor recese",
            annotation_position="top left",
            annotation_font=dict(color="#DC2626", size=10)
        )

    fig.update_layout(
        title=dict(text="Sklon americké výnosové křivky (Spread 10Y − 2Y v bps) | Indikátor recese", font=dict(size=14, color="#1E293B")),
        height=380,
        hovermode="x unified",
        margin=dict(l=20, r=20, t=45, b=20),
        xaxis=dict(title="", showgrid=True, gridcolor="#F1F5F9"),
        yaxis=dict(title="Rozpětí (bps)", ticksuffix=" bps", showgrid=True, gridcolor="#F1F5F9"),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF"
    )
    return fig


def build_cz_vs_us_spread_chart(dframe: pd.DataFrame) -> go.Figure:
    """Graf rozpětí mezi 10Y státním dluhopisem ČR (CZGB) a 10Y US Treasury (v bps)."""
    fig = go.Figure()
    if "czgb_10y" in dframe.columns and "us_10y" in dframe.columns:
        diff_bps = (dframe["czgb_10y"] - dframe["us_10y"]) * 100.0
        fig.add_trace(go.Scatter(
            x=dframe["date"],
            y=diff_bps,
            mode="lines",
            name="Spread 10Y (CZGB − US Treasury)",
            line=dict(color="#D97706", width=2.5),
            hovertemplate="<b>Spread CZGB - US 10Y</b>: %{y:+.0f} bps<extra></extra>"
        ))
        fig.add_hline(
            y=0.0,
            line=dict(color="#64748B", width=1.5, dash="dash"),
            annotation_text="Parita výnosů (0 bps)",
            annotation_position="bottom left"
        )

    fig.update_layout(
        title=dict(text="Mezinárodní rozpětí: Výnos 10Y CZGB minus 10Y US Treasury (v bps)", font=dict(size=14, color="#1E293B")),
        height=380,
        hovermode="x unified",
        margin=dict(l=20, r=20, t=45, b=20),
        xaxis=dict(title="", showgrid=True, gridcolor="#F1F5F9"),
        yaxis=dict(title="Rozpětí CZ − US (bps)", ticksuffix=" bps", showgrid=True, gridcolor="#F1F5F9"),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF"
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

df_export_cz = df_export.rename(columns=rename_dict)
df_export_cz["Datum"] = df_export_cz["Datum"].dt.strftime("%d.%m.%Y")


# =============================================================================
# 10. ZÁLOŽKY DASHBOARDU (PŘESNĚ ODPOVÍDAJÍCÍ STRUKTURA PRO ČR I USA)
# =============================================================================

if is_cz:
    # --- STRUKTURA PRO ČR ---
    tab_rates, tab_inflation, tab_gdp, tab_une, tab_fx, tab_debt, tab_curve, tab_compare, tab_all, tab_table = st.tabs([
        "Sazby (ČNB)",
        "Inflace (CPI)",
        "HDP",
        "Nezaměstnanost",
        "Měnové kurzy",
        "Veřejný dluh",
        "CZ výnosová křivka",
        "Srovnání ČR vs. USA",
        "Všechny grafy",
        "Data a export"
    ])

    # 1. TAB: SAZBY (ČNB)
    with tab_rates:
        st.markdown('<div class="section-header">Měnová politika ČNB a mezibankovní sazby PRIBOR</div>', unsafe_allow_html=True)
        st.caption("Úrokový koridor České národní banky: 2T Repo sazba, Diskontní sazba (depozitní facilita) a Lombardní sazba (zápůjční facilita) ve srovnání s tržními sazbami PRIBOR.")
        col_r1, col_r2, col_r3, col_r4 = st.columns(4)
        col_r1.metric("2T Repo sazba", f"{repo_curr:.2f} %", delta=f"{repo_delta:+.2f} p.b.", help="Hlavní nástroj stahování likvidity")
        col_r2.metric("Diskontní sazba", f"{disc_curr:.2f} %", help="Úročení vkladů bank přes noc u ČNB")
        col_r3.metric("Lombardní sazba", f"{lomb_curr:.2f} %", help="Úročení zápůjček bank přes noc od ČNB")
        col_r4.metric("PRIBOR 3M", f"{prib3m_curr:.2f} %", help="Referenční tržní sazba mezibankovního trhu")
        fig_rates = build_rates_chart(df, selected_indicators)
        render_plotly_chart(fig_rates, key="chart_cz_rates")

    # 2. TAB: INFLACE (CPI)
    with tab_inflation:
        st.markdown('<div class="section-header">Meziroční míra inflace (CPI) v České republice</div>', unsafe_allow_html=True)
        st.caption("Vývoj indexu spotřebitelských cen (CPI / HICP) s vyznačeným 2% inflačním cílem a tolerančním pásmem ČNB (1–3 %).")
        col_i1, col_i2, col_i3, col_i4 = st.columns(4)
        col_i1.metric("Aktuální inflace (YoY)", f"{cpi_cz_curr:.1f} %", delta=f"{cpi_cz_delta:+.1f} p.b.", delta_color="inverse")
        col_i2.metric("Inflační cíl ČNB", "2.00 %", delta="Pásmo 1–3 %", delta_color="off")
        real_cz_rate = repo_curr - cpi_cz_curr
        col_i3.metric("Reálná úroková sazba", f"{real_cz_rate:+.2f} %", delta="Repo − CPI", delta_color="off")
        col_i4.metric("Průměrná inflace v období", f"{df['cpi_yoy'].mean():.2f} %" if "cpi_yoy" in df.columns else "N/A")
        fig_inf = build_inflation_chart(df)
        render_plotly_chart(fig_inf, key="chart_cz_inflation")

    # 3. TAB: HDP
    with tab_gdp:
        st.markdown('<div class="section-header">Hrubý domácí produkt (HDP) České republiky</div>', unsafe_allow_html=True)
        st.caption("Čtvrtletní nominální objem HDP v běžných cenách a reálný meziroční růst stálých cen (řetězené objemy).")
        col_g1, col_g2, col_g3, col_g4 = st.columns(4)
        col_g1.metric("Reálný růst HDP (YoY)", f"{gdp_cz_curr:+.1f} %", delta=f"{gdp_cz_delta:+.1f} p.b.")
        nom_val = safe_metric(last_row, "gdp_nominal_czk_bn", 1950.0)
        col_g2.metric("Kvartální nominální HDP", f"{nom_val:,.1f} mld. Kč")
        col_g3.metric("Průměrný reálný růst", f"{df['gdp_growth_real'].mean():+.2f} %" if "gdp_growth_real" in df.columns else "N/A")
        col_g4.metric("Poslední kvartál", str(last_row.get("quarter", "Aktuální")))
        fig_gdp = build_gdp_chart(df, selected_indicators)
        render_plotly_chart(fig_gdp, key="chart_cz_gdp")

    # 4. TAB: NEZAMĚSTNANOST
    with tab_une:
        st.markdown('<div class="section-header">Trh práce a míra nezaměstnanosti v ČR</div>', unsafe_allow_html=True)
        st.caption("Obecná míra nezaměstnanosti dle metodiky Eurostatu a ILO pro věkovou skupinu 15–74 let.")
        col_u1, col_u2, col_u3, col_u4 = st.columns(4)
        col_u1.metric("Míra nezaměstnanosti ČR", f"{une_cz_curr:.1f} %", delta=f"{une_cz_delta:+.1f} p.b.", delta_color="inverse")
        col_u2.metric("Průměr EU (srovnání)", "~5.9 %", delta="ČR nejnižší v EU", delta_color="off")
        col_u3.metric("Historické minimum v období", f"{df['unemployment_rate'].min():.1f} %" if "unemployment_rate" in df.columns else "N/A")
        col_u4.metric("Historické maximum v období", f"{df['unemployment_rate'].max():.1f} %" if "unemployment_rate" in df.columns else "N/A")
        fig_une = build_unemployment_chart(df)
        render_plotly_chart(fig_une, key="chart_cz_unemployment")

    # 5. TAB: MĚNOVÉ KURZY (DENNÍ DATA)
    with tab_fx:
        st.markdown('<div class="section-header">Měnové kurzy: Denní data ČNB pro EUR/CZK a USD/CZK</div>', unsafe_allow_html=True)
        st.caption("Oficiální denní fixace devizového trhu České národní banky (ČNB). Zobrazena vysokofrekvenční denní časová řada.")

        # Přepínač detailu pro FX
        fx_view_mode = st.radio("Frekvence grafu měnových kurzů:", ["📅 Denní data (High-Frequency)", "📊 Měsíční agregace"], horizontal=True, key="cz_fx_freq_radio")
        df_for_fx_plot = df_daily_fx_filtered if "Denní" in fx_view_mode else df

        col_fx1, col_fx2, col_fx3, col_fx4 = st.columns(4)
        daily_eur_prev = safe_metric(prev_daily_fx, "eur_czk", daily_eur_czk)
        daily_usd_prev = safe_metric(prev_daily_fx, "usd_czk", daily_usd_czk)
        eur_d_delta = daily_eur_czk - daily_eur_prev
        usd_d_delta = daily_usd_czk - daily_usd_prev
        cross_calc = (daily_eur_czk / daily_usd_czk) if daily_usd_czk > 0 else 1.08

        col_fx1.metric("EUR / CZK (Poslední denní kurz)", f"{daily_eur_czk:.4f} Kč", delta=f"{eur_d_delta:+.4f} Kč", delta_color="off")
        col_fx2.metric("USD / CZK (Poslední denní kurz)", f"{daily_usd_czk:.4f} Kč", delta=f"{usd_d_delta:+.4f} Kč", delta_color="off")
        col_fx3.metric("Křížový poměr EUR / USD", f"{cross_calc:.4f} $", delta="Výpočet ČNB fix")
        min_eur_d = df_daily_fx_filtered["eur_czk"].min() if "eur_czk" in df_daily_fx_filtered.columns else daily_eur_czk
        max_eur_d = df_daily_fx_filtered["eur_czk"].max() if "eur_czk" in df_daily_fx_filtered.columns else daily_eur_czk
        col_fx4.metric("Rozpětí EUR/CZK (Min – Max)", f"{min_eur_d:.2f} – {max_eur_d:.2f} Kč")

        fig_fx_cz = build_fx_daily_chart_cz(df_for_fx_plot)
        render_plotly_chart(fig_fx_cz, key="chart_cz_fx_daily")

        # Tlačítko pro stažení denních FX dat
        csv_daily_fx = df_daily_fx_filtered[["date", "eur_czk", "usd_czk", "gbp_czk", "chf_czk"]].rename(columns={
            "date": "Datum",
            "eur_czk": "EUR/CZK",
            "usd_czk": "USD/CZK",
            "gbp_czk": "GBP/CZK",
            "chf_czk": "CHF/CZK"
        }).to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")

        st.download_button(
            label="📥 Stáhnout kompletní denní data kurzů ČNB (CSV)",
            data=csv_daily_fx,
            file_name=f"CNB_denni_kurzy_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            key="btn_dl_daily_fx_cz"
        )

    # 6. TAB: VEŘEJNÝ DLUH
    with tab_debt:
        st.markdown('<div class="section-header">Fiskální politika a veřejný dluh ČR</div>', unsafe_allow_html=True)
        st.caption("Vývoj konsolidovaného hrubého dluhu sektoru vládních institucí k HDP v porovnání s Maastrichtským kritériem (60 % HDP).")
        col_d1, col_d2, col_d3 = st.columns(3)
        col_d1.metric("Veřejný dluh k HDP", f"{debt_cz_pct:.1f} %", delta="Limit < 60 % HDP", delta_color="normal")
        debt_nom_val = safe_metric(last_row, "public_debt_czk_bn", 3300.0)
        col_d2.metric("Nominální veřejný dluh ČR", f"{debt_nom_val:,.1f} mld. Kč")
        col_d3.metric("Kvartální saldo rozpočtu", f"{deficit_cz_curr:,.1f} mld. Kč")
        fig_d1, fig_d2 = build_debt_charts(df)
        c_da, c_db = st.columns(2)
        with c_da:
            render_plotly_chart(fig_d1, key="chart_cz_debt_pct")
        with c_db:
            render_plotly_chart(fig_d2, key="chart_cz_deficit")

    # 7. TAB: VÝNOSOVÁ KŘIVKA ČR
    with tab_curve:
        st.markdown('<div class="section-header">Výnosová křivka ČR (Státní dluhopisy CZGB & Úrokové swapy IRS)</div>', unsafe_allow_html=True)
        st.caption("Časová struktura výnosů státních dluhopisů ČR (1Y–15Y) a mezibankovních úrokových swapů (CZK IRS).")
        comp_date_target = last_row["date"] - pd.DateOffset(years=1)
        comp_df = df_raw[df_raw["date"] <= comp_date_target]
        comp_row = comp_df.iloc[-1] if not comp_df.empty else None
        fig_curve_cz = build_yield_curve_snapshot(last_row, comp_row)
        render_plotly_chart(fig_curve_cz, key="chart_cz_yield_curve")

    # 8. TAB: SROVNÁNÍ ČR VS. USA
    with tab_compare:
        st.markdown('<div class="section-header">Mezinárodní srovnání: Česká republika vs. Spojené státy</div>', unsafe_allow_html=True)
        st.caption("Analýza úrokového diferenciálu centrálních bank (ČNB vs. Fed) a sovereign spreadu (10Y CZGB − 10Y US Treasury).")
        col_cp1, col_cp2, col_cp3 = st.columns(3)
        rate_diff = repo_curr - fed_upper_curr
        col_cp1.metric("Úrokový diferenciál (Repo − Fed)", f"{rate_diff:+.2f} p.b.")
        spread_10y_bps = (czgb10_curr - us10_curr) * 100.0
        col_cp2.metric("Sovereign spread 10Y (CZGB − US Treasury)", f"{spread_10y_bps:+.0f} bps")
        inf_diff = cpi_cz_curr - cpi_us_curr
        col_cp3.metric("Inflační diferenciál (ČR − USA)", f"{inf_diff:+.1f} p.b.")
        fig_cz_us = build_cz_vs_us_spread_chart(df)
        render_plotly_chart(fig_cz_us, key="chart_cz_us_spread_tab")

    # 9. TAB: VŠECHNY GRAFY
    with tab_all:
        st.markdown('<div class="section-header">Souhrnný přehled všech grafů České republiky</div>', unsafe_allow_html=True)
        render_plotly_chart(fig_rates, key="all_cz_rates")
        render_plotly_chart(fig_inf, key="all_cz_inf")
        render_plotly_chart(fig_gdp, key="all_cz_gdp")
        render_plotly_chart(fig_une, key="all_cz_une")

    # 10. TAB: DATA A EXPORT
    with tab_table:
        st.markdown('<div class="section-header">Datový průzkumník a export (Česká republika)</div>', unsafe_allow_html=True)
        render_dataframe(df_export_cz)
        csv_bytes = df_export_cz.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")
        st.download_button(
            label="📥 Stáhnout data ČR (CSV)",
            data=csv_bytes,
            file_name=f"makro_data_CR_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            key="btn_dl_macro_cz"
        )

else:
    # =========================================================================
    # STRUKTURA PRO USA (STEJNÁ STRUKTURA DAT JAKO PRO ČR)
    # =========================================================================
    tab_rates, tab_inflation, tab_gdp, tab_une, tab_fx, tab_debt, tab_curve, tab_compare, tab_all, tab_table = st.tabs([
        "Sazby (Fed)",
        "Inflace (CPI)",
        "HDP",
        "Trh práce",
        "Měnové kurzy",
        "Veřejný dluh",
        "US výnosová křivka",
        "Srovnání USA vs. ČR",
        "Všechny grafy",
        "Data a export"
    ])

    # 1. TAB: SAZBY (FED & SOFR)
    with tab_rates:
        st.markdown('<div class="section-header">Měnová politika Federálního rezervního systému (Fed) a peněžní trh USA</div>', unsafe_allow_html=True)
        st.caption("Cílový koridor sazeb Fedu (Fed Funds Target Upper & Lower limit), efektivní mezibankovní sazba EFFR a referenční sazba SOFR.")
        col_ur1, col_ur2, col_ur3, col_ur4 = st.columns(4)
        col_ur1.metric("Fed Funds Target (horní limit)", f"{fed_upper_curr:.2f} %", delta=f"{fed_upper_delta:+.2f} p.b.", help="Horní hranice koridoru Fedu")
        col_ur2.metric("Fed Funds Target (dolní limit)", f"{fed_lower_curr:.2f} %", help="Dolní hranice koridoru Fedu")
        col_ur3.metric("SOFR (Secured Rate)", f"{sofr_curr:.2f} %", help="Jednodenní zajištěná sazba krytá státními dluhopisy")
        col_ur4.metric("3M US Treasury Bill", f"{us3m_curr:.2f} %", help="Tradiční benchmark amerického peněžního trhu")
        fig_us_rates = build_us_rates_chart(df, selected_indicators)
        render_plotly_chart(fig_us_rates, key="chart_us_rates")

    # 2. TAB: INFLACE (CPI & CORE CPI)
    with tab_inflation:
        st.markdown('<div class="section-header">Spotřebitelská a jádrová inflace v USA (Headline & Core CPI)</div>', unsafe_allow_html=True)
        st.caption("Meziroční vývoj celkové spotřebitelské inflace (Headline CPI) a jádrové inflace bez volatilních cen potravin a energií (Core CPI).")
        col_ui1, col_ui2, col_ui3, col_ui4 = st.columns(4)
        col_ui1.metric("Headline CPI USA (YoY)", f"{cpi_us_curr:.1f} %", delta=f"{cpi_us_delta:+.1f} p.b.", delta_color="inverse")
        col_ui2.metric("Jádrová inflace (Core CPI)", f"{core_cpi_us_curr:.1f} %", delta="Bez potravin a energií", delta_color="off")
        real_us_effr = fed_effr_curr - cpi_us_curr
        col_ui3.metric("Reálná úroková sazba Fedu", f"{real_us_effr:+.2f} %", delta="EFFR − Headline CPI", delta_color="off")
        col_ui4.metric("Inflační cíl Fedu", "2.00 %", delta="PCE benchmark", delta_color="off")
        fig_us_inf = build_us_inflation_chart(df)
        render_plotly_chart(fig_us_inf, key="chart_us_inflation")

    # 3. TAB: HDP (USA)
    with tab_gdp:
        st.markdown('<div class="section-header">Hrubý domácí produkt Spojených států (U.S. GDP)</div>', unsafe_allow_html=True)
        st.caption("Reálný meziroční růst hrubého domácího produktu USA (YoY v %) a roční nominální objem v miliardách USD.")
        col_ug1, col_ug2, col_ug3, col_ug4 = st.columns(4)
        col_ug1.metric("Reálný růst HDP USA (YoY)", f"{gdp_us_curr:+.1f} %", delta=f"{gdp_us_delta:+.1f} p.b.")
        nom_us_val = safe_metric(last_row, "us_gdp_nominal_usd_bn", 28500.0)
        col_ug2.metric("Nominální objem HDP USA", f"{nom_us_val:,.0f} mld. $", help="Anualizovaný objem ekonomiky")
        col_ug3.metric("Průměrný růst v období", f"{df['us_gdp_growth_real'].mean():+.2f} %" if "us_gdp_growth_real" in df.columns else "N/A")
        col_ug4.metric("Poslední kvartál", str(last_row.get("quarter", "Aktuální")))
        fig_us_gdp = build_us_gdp_chart(df, selected_indicators)
        render_plotly_chart(fig_us_gdp, key="chart_us_gdp")

    # 4. TAB: TRH PRÁCE (USA)
    with tab_une:
        st.markdown('<div class="section-header">Trh práce a zaměstnanost v USA (U-3 Rate & Nonfarm Payrolls)</div>', unsafe_allow_html=True)
        st.caption("Oficiální míra nezaměstnanosti v USA (U.S. Bureau of Labor Statistics U-3 rate) s vyznačením historických maxim a průměrů.")
        col_uu1, col_uu2, col_uu3, col_uu4 = st.columns(4)
        col_uu1.metric("Míra nezaměstnanosti (U-3)", f"{une_us_curr:.1f} %", delta=f"{une_us_delta:+.1f} p.b.", delta_color="inverse")
        nfp_val = safe_metric(last_row, "us_nonfarm_payrolls_k", 180.0)
        col_uu2.metric("Měsíční změna pracovních míst (NFP)", f"{nfp_val:+,.0f} tis.")
        col_uu3.metric("Historické minimum v období", f"{df['us_unemployment_rate'].min():.1f} %" if "us_unemployment_rate" in df.columns else "N/A")
        col_uu4.metric("Průměr nezaměstnanosti USA", f"{df['us_unemployment_rate'].mean():.2f} %" if "us_unemployment_rate" in df.columns else "N/A")
        fig_us_une = build_us_unemployment_chart(df)
        render_plotly_chart(fig_us_une, key="chart_us_unemployment")

    # 5. TAB: MĚNOVÉ KURZY (DENNÍ DATA PRO US / SVĚT)
    with tab_fx:
        st.markdown('<div class="section-header">Měnové kurzy: Denní data pro Dolarový index (DXY) a měnové páry</div>', unsafe_allow_html=True)
        st.caption("Globální devizový trh s vysokofrekvenčními denními daty pro U.S. Dollar Index (DXY), EUR/USD, GBP/USD a USD/JPY.")

        us_fx_view_mode = st.radio("Frekvence grafu měnových kurzů:", ["📅 Denní data (High-Frequency)", "📊 Měsíční agregace"], horizontal=True, key="us_fx_freq_radio")
        df_for_us_fx_plot = df_daily_fx_filtered if "Denní" in us_fx_view_mode else df

        col_uf1, col_uf2, col_uf3, col_uf4 = st.columns(4)
        prev_dxy_d = safe_metric(prev_daily_fx, "dxy_index", daily_dxy)
        dxy_d_delta = daily_dxy - prev_dxy_d
        prev_eurusd_d = safe_metric(prev_daily_fx, "eur_usd", daily_eur_usd)
        eurusd_d_delta = daily_eur_usd - prev_eurusd_d
        daily_usdjpy = safe_metric(last_daily_fx, "usd_jpy", usd_jpy_curr)
        daily_gbpusd = safe_metric(last_daily_fx, "gbp_usd", 1.28)

        col_uf1.metric("Dolarový index (DXY)", f"{daily_dxy:.2f}", delta=f"{dxy_d_delta:+.2f} b.", delta_color="off")
        col_uf2.metric("Měnový kurz EUR / USD", f"{daily_eur_usd:.4f} $", delta=f"{eurusd_d_delta:+.4f} $", delta_color="off")
        col_uf3.metric("Měnový kurz GBP / USD", f"{daily_gbpusd:.4f} $")
        col_uf4.metric("Měnový kurz USD / JPY", f"{daily_usdjpy:.2f} ¥")

        fig_us_fx = build_fx_daily_chart_us(df_for_us_fx_plot)
        render_plotly_chart(fig_us_fx, key="chart_us_fx_daily")

        # Tlačítko pro export denních dat pro US
        csv_daily_us_fx = df_daily_fx_filtered[["date", "dxy_index", "eur_usd", "gbp_usd", "usd_jpy", "usd_chf"]].rename(columns={
            "date": "Datum",
            "dxy_index": "DXY_Index",
            "eur_usd": "EUR/USD",
            "gbp_usd": "GBP/USD",
            "usd_jpy": "USD/JPY",
            "usd_chf": "USD/CHF"
        }).to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")

        st.download_button(
            label="📥 Stáhnout kompletní denní data FX & DXY (CSV)",
            data=csv_daily_us_fx,
            file_name=f"US_denni_kurzy_DXY_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            key="btn_dl_daily_fx_us"
        )

    # 6. TAB: VEŘEJNÝ DLUH (USA)
    with tab_debt:
        st.markdown('<div class="section-header">Fiskální politika a federální dluh Spojených států</div>', unsafe_allow_html=True)
        st.caption("Vývoj hrubého federálního dluhu USA k HDP (Debt-to-GDP ratio) a kvartální saldo federálního rozpočtu.")
        col_ud1, col_ud2, col_ud3 = st.columns(3)
        col_ud1.metric("Federální dluh USA k HDP", f"{debt_us_pct:.1f} %", delta="Historické maximum", delta_color="inverse")
        col_ud2.metric("Nominální federální dluh USA", f"{debt_us_nom:,.0f} mld. $", help="Total Public Debt Outstanding")
        def_us_curr = safe_metric(last_row, "us_budget_deficit_usd_bn", -450.0)
        col_ud3.metric("Kvartální federální deficit", f"{def_us_curr:,.0f} mld. $")
        fig_ud1, fig_ud2 = build_us_debt_charts(df)
        c_uda, c_udb = st.columns(2)
        with c_uda:
            render_plotly_chart(fig_ud1, key="chart_us_debt_pct")
        with c_udb:
            render_plotly_chart(fig_ud2, key="chart_us_deficit")

    # 7. TAB: VÝNOSOVÁ KŘIVKA USA
    with tab_curve:
        st.markdown('<div class="section-header">Výnosová křivka USA (U.S. Treasury Par Yield Curve: 1M–30Y)</div>', unsafe_allow_html=True)
        st.caption("Oficiální Par Yield Curve amerického ministerstva financí (home.treasury.gov) a analýza sklonu křivky (10Y − 2Y).")
        comp_date_target_us = last_row["date"] - pd.DateOffset(years=1)
        comp_df_us = df_raw[df_raw["date"] <= comp_date_target_us]
        comp_row_us = comp_df_us.iloc[-1] if not comp_df_us.empty else None
        fig_curve_us = build_us_yield_curve_snapshot(last_row, comp_row_us)
        render_plotly_chart(fig_curve_us, key="chart_us_yield_curve")
        fig_spread_us = build_us_curve_spread_chart(df)
        render_plotly_chart(fig_spread_us, key="chart_us_spread_curve")

    # 8. TAB: SROVNÁNÍ USA VS. ČR
    with tab_compare:
        st.markdown('<div class="section-header">Mezinárodní srovnání: Spojené státy vs. Česká republika</div>', unsafe_allow_html=True)
        st.caption("Porovnání úrokových sazeb centrálních bank (Fed vs. ČNB) a mezinárodního výnosového spreadu.")
        col_ucp1, col_ucp2, col_ucp3 = st.columns(3)
        rate_diff_us = fed_upper_curr - repo_curr
        col_ucp1.metric("Úrokový diferenciál (Fed − Repo)", f"{rate_diff_us:+.2f} p.b.")
        spread_us_cz_bps = (us10_curr - czgb10_curr) * 100.0
        col_ucp2.metric("Výnosový spread 10Y (US Treasury − CZGB)", f"{spread_us_cz_bps:+.0f} bps")
        inf_diff_us = cpi_us_curr - cpi_cz_curr
        col_ucp3.metric("Inflační diferenciál (USA − ČR)", f"{inf_diff_us:+.1f} p.b.")
        fig_us_cz = build_cz_vs_us_spread_chart(df)
        render_plotly_chart(fig_us_cz, key="chart_us_cz_spread_tab")

    # 9. TAB: VŠECHNY GRAFY (USA)
    with tab_all:
        st.markdown('<div class="section-header">Souhrnný přehled všech grafů Spojených států amerických</div>', unsafe_allow_html=True)
        render_plotly_chart(fig_us_rates, key="all_us_rates")
        render_plotly_chart(fig_us_inf, key="all_us_inf")
        render_plotly_chart(fig_us_gdp, key="all_us_gdp")
        render_plotly_chart(fig_us_une, key="all_us_une")

    # 10. TAB: DATA A EXPORT (USA)
    with tab_table:
        st.markdown('<div class="section-header">Datový průzkumník a export (Spojené státy americké)</div>', unsafe_allow_html=True)
        render_dataframe(df_export_cz)
        csv_bytes_us = df_export_cz.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")
        st.download_button(
            label="📥 Stáhnout data USA (CSV)",
            data=csv_bytes_us,
            file_name=f"makro_data_USA_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            key="btn_dl_macro_us"
        )
