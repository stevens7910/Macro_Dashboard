"""
app.py
======
Český Makroekonomický Dashboard ve Streamlit.
Přehledná, responzivní a modulární aplikace pro vizualizaci klíčových makroekonomických
indikátorů České republiky v čase (ČNB, Inflace, HDP, Trh práce, FX kurzy a Veřejný dluh).
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

from data_loader import DataLoader, INDICATORS, get_cached_macro_data

# =============================================================================
# 1. KONFIGURACE STRÁNKY A STYLING
# =============================================================================

st.set_page_config(
    page_title="Český Makroekonomický Dashboard | ČNB, HDP, Inflace, FX, Dluh",
    page_icon="🇨🇿",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
    /* Základní rozvržení a typografie (Stock Analysis styl) */
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Inter", Helvetica, Arial, sans-serif !important;
    }
    
    .main .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2.5rem;
        max-width: 1400px;
    }
    
    /* Vzhled metrických KPI karet (Čistý, minimalistický Stock Analysis styl) */
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
        font-size: 1.65rem !important;
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
        padding: 3px 10px;
        border-radius: 4px;
        font-size: 0.75rem;
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

    /* ========================================================= */
    /* ZÁLOŽKY (TABS): MINIMALISTICKÝ DESIGN (STOCK ANALYSIS)     */
    /* Žádné ikonky, čistý horizontální pás, jemný aktivní pill   */
    /* ========================================================= */
    div[data-baseweb="tab-list"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
        gap: 2px 6px !important;
        border-bottom: 1px solid #e5e7eb !important;
        padding-bottom: 6px !important;
        margin-bottom: 1.4rem !important;
        overflow-x: auto !important;
        white-space: nowrap !important;
        scrollbar-width: thin !important;
        background: transparent !important;
        width: 100% !important;
    }

    /* Skrytí defaultní streamlitské barevné podtrhávací lišty */
    div[data-baseweb="tab-highlight"],
    div[data-baseweb="tab-border"] {
        display: none !important;
    }

    /* Neaktivní záložky: čistý textový link bez rámečku */
    button[data-baseweb="tab"] {
        background-color: transparent !important;
        color: #475569 !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 6px 14px !important;
        font-size: 0.88rem !important;
        font-weight: 500 !important;
        transition: all 0.15s ease !important;
        white-space: nowrap !important;
        box-shadow: none !important;
        cursor: pointer !important;
        height: auto !important;
    }

    /* Hover stav pro neaktivní ouško */
    button[data-baseweb="tab"]:hover {
        background-color: #f1f5f9 !important;
        color: #0f172a !important;
    }

    /* Aktivní záložka: decentní jemně šedý pill (přesně jako 'Overview' na screenshotu) */
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

    /* ========================================================= */
    /* STOCK ANALYSIS: TOP HEADER & KEY STATS PANELS            */
    /* ========================================================= */
    .sa-header-container {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 20px;
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
        gap: 18px 28px;
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
        font-size: 1.35rem;
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

    /* Dvou-sloupcová tabulka klíčových metrik (Key Metrics Widget ze screenshotu) */
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

    /* Postranní panel (Sidebar) - Čistý, minimalistický vzhled */
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
        font-size: 0.74rem;
        color: #94a3b8;
        margin-top: 2px;
    }
    .sidebar-section-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-top: 14px;
        margin-bottom: 6px;
    }
    .sidebar-section-title {
        font-size: 0.82rem;
        font-weight: 700;
        color: #334155;
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

    /* Segmented Control styl tlačítek v sidebaru */
    div[data-testid="stSegmentedControl"] {
        background-color: #f1f5f9 !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 8px !important;
        padding: 3px !important;
        width: 100% !important;
    }
    div[data-testid="stSegmentedControl"] button {
        border-radius: 6px !important;
        font-size: 0.80rem !important;
        font-weight: 600 !important;
        padding: 6px 4px !important;
        border: none !important;
        background: transparent !important;
        color: #475569 !important;
    }
    div[data-testid="stSegmentedControl"] button[aria-selected="true"] {
        background: #2563eb !important;
        color: #ffffff !important;
    }
    div[data-testid="stSegmentedControl"] button[aria-selected="true"] p,
    div[data-testid="stSegmentedControl"] button[aria-selected="true"] span {
        color: #ffffff !important;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# =============================================================================
# 2. POMOCNÉ FORMÁTOVACÍ A VYKRESLOVACÍ FUNKCE
# =============================================================================

def format_cz_number(val: Optional[float], decimals: int = 2, unit: str = "") -> str:
    """Zformátuje číslo podle českých zvyklostí (čárka jako oddělovač desetin)."""
    if val is None or pd.isna(val):
        return "N/A"
    fmt = f"{val:,.{decimals}f}".replace(",", " ").replace(".", ",")
    return f"{fmt} {unit}".strip() if unit else fmt


def format_delta_str(curr: Optional[float], prev: Optional[float], unit: str = "p.b.") -> str:
    """Spočítá a zformátuje deltu mezi současnou a předchozí hodnotou."""
    if curr is None or prev is None or pd.isna(curr) or pd.isna(prev):
        return "–"
    delta = curr - prev
    sign = "+" if delta > 0 else ""
    return f"{sign}{delta:,.2f} {unit}".replace(".", ",")


def render_plotly_chart(fig: go.Figure, key: Optional[str] = None) -> None:
    """Vykreslí Plotly graf s plnou kompatibilitou napříč verzemi Streamlit."""
    try:
        st.plotly_chart(fig, width="stretch", key=key)
    except (TypeError, ValueError):
        st.plotly_chart(fig, use_container_width=True, key=key)


def render_dataframe(df_to_render: pd.DataFrame) -> None:
    """Vykreslí tabulku s plnou kompatibilitou napříč verzemi Streamlit."""
    try:
        st.dataframe(df_to_render, width="stretch", hide_index=True)
    except (TypeError, ValueError):
        st.dataframe(df_to_render, use_container_width=True, hide_index=True)


# =============================================================================
# 3. SIDEBAR: OVLÁDACÍ PRVKY A NASTAVENÍ
# =============================================================================

st.sidebar.markdown(
    """
    <div class="sidebar-brand-card">
        <div class="sidebar-brand-top">
            <span class="sidebar-brand-badge">ČR MACRO</span>
            <span class="sidebar-brand-version">TERMINAL</span>
        </div>
        <div class="sidebar-brand-title">Nastavení a filtry</div>
        <div class="sidebar-brand-sub">ČNB &bull; Eurostat &bull; Dluh &bull; Výnosová křivka</div>
    </div>
    """,
    unsafe_allow_html=True
)

# 1. Výběr časového horizontu (Stock Analysis styl - Segmented Control)
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

# Příprava seznamu dostupných měsíců pro combo boxy
all_month_dates = pd.date_range("2015-01-01", datetime.now(), freq="MS")
month_options = [d.strftime("%m/%Y") for d in all_month_dates]

start_filter_date = pd.to_datetime("2021-01-01")
end_filter_date = pd.to_datetime(datetime.now().strftime("%Y-%m-%d"))

# Pokud uživatel vybere "Vlastní" (nebo "Vlastní rozsah"), zobrazíme elegantní výběr měsíců
if horizon_option in ("Vlastní", "Vlastní rozsah"):
    st.sidebar.markdown(
        """
        <div style="background: #f1f5f9; border: 1px dashed #cbd5e1; border-radius: 8px; padding: 10px; margin-top: 6px; margin-bottom: 10px;">
            <div style="font-size: 0.74rem; font-weight: 700; color: #475569; text-transform: uppercase; margin-bottom: 6px;">📅 Vlastní časové rozpětí:</div>
        """,
        unsafe_allow_html=True
    )
    col_c1, col_c2 = st.sidebar.columns(2)
    default_start_idx = max(0, len(month_options) - 36)  # výchozí 3 roky zpět
    selected_start_str = col_c1.selectbox("Od (měsíc/rok):", options=month_options, index=default_start_idx, key="sb_custom_from")
    selected_end_str = col_c2.selectbox("Do (měsíc/rok):", options=month_options, index=len(month_options) - 1, key="sb_custom_to")
    
    start_filter_date = pd.to_datetime(selected_start_str, format="%m/%Y")
    end_filter_date = pd.to_datetime(selected_end_str, format="%m/%Y") + pd.offsets.MonthEnd(0)
    
    if start_filter_date > end_filter_date:
        start_filter_date, end_filter_date = end_filter_date, start_filter_date
        st.sidebar.warning("Datum 'Od' bylo po 'Do', rozsah byl automaticky upraven.")
    st.sidebar.markdown("</div>", unsafe_allow_html=True)

# 2. Přepínač frekvence (Stock Analysis styl - Segmented Control)
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

# 3. Volba indikátorů
st.sidebar.markdown(
    """
    <div class="sidebar-section-header">
        <span class="sidebar-section-title">📊 Zobrazené ukazatele</span>
        <span class="sidebar-section-badge">Metriky</span>
    </div>
    """,
    unsafe_allow_html=True
)
all_indicator_keys = list(INDICATORS.keys())
default_indicators = [
    "repo_rate", "discount_rate", "lombard_rate",
    "pribor_3m", "cpi_yoy", "gdp_growth_real",
    "gdp_nominal_czk_bn", "unemployment_rate",
    "eur_czk", "usd_czk",
    "public_debt_gdp_pct", "public_debt_czk_bn", "budget_deficit_czk_bn",
    "czgb_10y", "czgb_2y", "irs_10y", "czgb_spread_10y_2y",
    "us_10y", "us_2y", "us_3m", "us_spread_10y_2y"
]

selected_indicators = st.sidebar.multiselect(
    "Vyberte ukazatele do dashboardu:",
    options=all_indicator_keys,
    default=default_indicators,
    format_func=lambda k: f"{INDICATORS[k].category}: {INDICATORS[k].name_cz} ({INDICATORS[k].unit})"
)

# Nastavení zdroje a API klíčů
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
    help="Přepne dashboard na interní historický model 2015–2026 bez volání externích REST API."
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
# 4. NAČTENÍ DAT S CACHOVÁNÍM
# =============================================================================

with st.spinner("Načítám makroekonomická data z ČNB a Eurostatu..."):
    df_raw, status_info = get_cached_macro_data(
        frequency=frequency_code,
        fred_api_key=fred_key_input,
        force_fallback=force_fallback
    )

if df_raw.empty:
    st.error("Nepodařilo se načíst žádná makroekonomická data. Zkuste aktivovat záložní fallback model v levém panelu.")
    st.stop()

# Stavový badge v sidebaru
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
# 5. APLIKACE ČASOVÉHO HORIZONTU
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
# Pokud je "Vlastní" nebo "Vlastní rozsah", proměnné start_filter_date a end_filter_date jsou již nastaveny výše z combo boxů!

df = df_raw[(df_raw["date"] >= start_filter_date) & (df_raw["date"] <= end_filter_date)].copy()
df = df.sort_values("date").reset_index(drop=True)

if df.empty:
    st.warning("Pro vybraný časový filtr nejsou k dispozici žádné záznamy. Zvolte prosím širší rozsah.")
    st.stop()


# =============================================================================
# 6. HLAVNÍ PLOCHA DASHBOARDU: ZÁHLAVÍ (STOCK ANALYSIS STYL)
# =============================================================================

last_row = df.iloc[-1]
prev_row = df.iloc[-2] if len(df) > 1 else last_row

repo_curr = last_row.get("repo_rate")
repo_prev = prev_row.get("repo_rate")
repo_delta = (repo_curr - repo_prev) if (repo_curr is not None and repo_prev is not None) else 0.0

cpi_curr = last_row.get("cpi_yoy")
cpi_prev = prev_row.get("cpi_yoy")
cpi_delta = (cpi_curr - cpi_prev) if (cpi_curr is not None and cpi_prev is not None) else 0.0

gdp_curr = last_row.get("gdp_growth_real")
gdp_prev = prev_row.get("gdp_growth_real")
gdp_delta = (gdp_curr - gdp_prev) if (gdp_curr is not None and gdp_prev is not None) else 0.0

une_curr = last_row.get("unemployment_rate")
une_prev = prev_row.get("unemployment_rate")
une_delta = (une_curr - une_prev) if (une_curr is not None and une_prev is not None) else 0.0

eur_curr = last_row.get("eur_czk")
usd_curr = last_row.get("usd_czk")
czgb10_curr = last_row.get("czgb_10y")
czgb2_curr = last_row.get("czgb_2y")
us10_curr = last_row.get("us_10y")
us2_curr = last_row.get("us_2y")
us3m_curr = last_row.get("us_3m")
us_spread_curr = last_row.get("us_spread_10y_2y")
cz_spread_curr = last_row.get("czgb_spread_10y_2y")
debt_pct_curr = last_row.get("public_debt_gdp_pct")
prib3m_curr = last_row.get("pribor_3m")

date_str = last_row.get("date").strftime("%d. %m. %Y") if hasattr(last_row.get("date"), "strftime") else "Aktuální"

# Stock Analysis styl: Top Header Box
st.markdown(
    f"""
    <div class="sa-header-container">
        <div class="sa-header-top">
            <div class="sa-header-title-box">
                <h1 class="sa-header-title">Česká republika & Spojené státy</h1>
                <span class="sa-ticker-badge">CZ &bull; US MACRO MONITOR</span>
            </div>
            <div class="sa-header-meta">
                <span class="sa-live-dot"></span>
                <span><strong>TRHY AKTIVNÍ</strong> &bull; ČNB &bull; Eurostat &bull; U.S. Treasury &bull; {date_str}</span>
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
                <span class="sa-hero-label">US Fed Proxy (3M)</span>
                <div class="sa-hero-val-row">
                    <span class="sa-hero-val">{us3m_curr:.2f} %</span>
                    <span class="sa-hero-change-neutral">T-Bill 3M</span>
                </div>
            </div>
            <div class="sa-hero-item">
                <span class="sa-hero-label">Inflace ČR (CPI)</span>
                <div class="sa-hero-val-row">
                    <span class="sa-hero-val">{cpi_curr:.1f} %</span>
                    <span class="sa-hero-change-pos">Cíl 2.0 %</span>
                </div>
            </div>
            <div class="sa-hero-item">
                <span class="sa-hero-label">10Y CZGB Výnos</span>
                <div class="sa-hero-val-row">
                    <span class="sa-hero-val">{czgb10_curr:.2f} %</span>
                    <span class="sa-hero-change-neutral">Benchmark</span>
                </div>
            </div>
            <div class="sa-hero-item">
                <span class="sa-hero-label">10Y US Treasury</span>
                <div class="sa-hero-val-row">
                    <span class="sa-hero-val">{us10_curr:.2f} %</span>
                    <span class="sa-hero-change-neutral">Globální ref.</span>
                </div>
            </div>
            <div class="sa-hero-item">
                <span class="sa-hero-label">Měnový kurz EUR/CZK</span>
                <div class="sa-hero-val-row">
                    <span class="sa-hero-val">{eur_curr:.2f} Kč</span>
                    <span class="sa-hero-change-neutral">ČNB fix</span>
                </div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# Stock Analysis 2-sloupcová tabulka klíčových metrik (Key Metrics Widget ze screenshotu)
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
                    <span class="sa-stat-label">PRIBOR 3M (mezibankovní)</span>
                    <span class="sa-stat-val">{prib3m_curr:.2f} %</span>
                </div>
                <div class="sa-stat-row">
                    <span class="sa-stat-label">Meziroční inflace (CPI)</span>
                    <span class="sa-stat-val">{cpi_curr:.1f} % <span class="sa-hero-change-pos">Cíl 2.0 %</span></span>
                </div>
                <div class="sa-stat-row">
                    <span class="sa-stat-label">Reálný růst HDP (YoY)</span>
                    <span class="sa-stat-val">{gdp_curr:+.1f} % <span class="sa-hero-change-pos">{gdp_delta:+.1f}</span></span>
                </div>
                <div class="sa-stat-row">
                    <span class="sa-stat-label">Míra nezaměstnanosti</span>
                    <span class="sa-stat-val">{une_curr:.1f} % <span class="sa-hero-change-pos">Nejnižší v EU</span></span>
                </div>
                <div class="sa-stat-row">
                    <span class="sa-stat-label">Měnový kurz EUR/CZK</span>
                    <span class="sa-stat-val">{eur_curr:.2f} Kč</span>
                </div>
                <div class="sa-stat-row">
                    <span class="sa-stat-label">Výnos 10Y CZGB (státní dluhopis)</span>
                    <span class="sa-stat-val">{czgb10_curr:.2f} %</span>
                </div>
            </div>
            <div>
                <div class="sa-stat-row">
                    <span class="sa-stat-label">Výnos 10Y US Treasury (Benchmark)</span>
                    <span class="sa-stat-val">{us10_curr:.2f} %</span>
                </div>
                <div class="sa-stat-row">
                    <span class="sa-stat-label">Výnos 2Y US Treasury (Fed citlivý)</span>
                    <span class="sa-stat-val">{us2_curr:.2f} %</span>
                </div>
                <div class="sa-stat-row">
                    <span class="sa-stat-label">Sklon US křivky (10Y − 2Y)</span>
                    <span class="sa-stat-val">{us_spread_curr * 100:+.0f} bps <span class="{"sa-hero-change-pos" if us_spread_curr >= 0 else "sa-hero-change-neg"}">{"Normální" if us_spread_curr >= 0 else "Inverze"}</span></span>
                </div>
                <div class="sa-stat-row">
                    <span class="sa-stat-label">US 3M Treasury Bill (Sazba peněžního trhu)</span>
                    <span class="sa-stat-val">{us3m_curr:.2f} %</span>
                </div>
                <div class="sa-stat-row">
                    <span class="sa-stat-label">Měnový kurz USD/CZK</span>
                    <span class="sa-stat-val">{usd_curr:.2f} Kč</span>
                </div>
                <div class="sa-stat-row">
                    <span class="sa-stat-label">Veřejný dluh k HDP ČR</span>
                    <span class="sa-stat-val">{debt_pct_curr:.1f} % <span class="sa-hero-change-pos">Maastricht 60 %</span></span>
                </div>
                <div class="sa-stat-row">
                    <span class="sa-stat-label">Sklon CZ křivky (10Y − 2Y)</span>
                    <span class="sa-stat-val">{cz_spread_curr * 100:+.0f} bps <span class="{"sa-hero-change-pos" if cz_spread_curr >= 0 else "sa-hero-change-neg"}">{"Normální" if cz_spread_curr >= 0 else "Inverze"}</span></span>
                </div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# 4 Rychlé KPI karty (Čistý minimalistický styl)
kpi_cols = st.columns(4)

with kpi_cols[0]:
    st.metric(
        label="2T Repo sazba ČNB",
        value=f"{repo_curr:.2f} %" if repo_curr is not None else "N/A",
        delta=f"{repo_delta:+.2f} p.b." if len(df) > 1 else "Aktuální",
        delta_color="inverse",
        help="Základní úroková sazba ČNB pro 2týdenní repo operace."
    )

with kpi_cols[1]:
    st.metric(
        label="Inflace (CPI meziročně)",
        value=f"{cpi_curr:.1f} %" if cpi_curr is not None else "N/A",
        delta=f"{cpi_delta:+.1f} p.b." if len(df) > 1 else "Aktuální",
        delta_color="inverse",
        help="Meziroční míra inflace. Cíl ČNB činí 2.0 %."
    )

with kpi_cols[2]:
    st.metric(
        label="Výnos 10Y CZGB (ČR)",
        value=f"{czgb10_curr:.2f} %" if czgb10_curr is not None else "N/A",
        delta=f"Sklon: {cz_spread_curr * 100:+.0f} bps",
        delta_color="off",
        help="Výnos 10letého referenčního státního dluhopisu ČR."
    )

with kpi_cols[3]:
    st.metric(
        label="Výnos 10Y US Treasury (USA)",
        value=f"{us10_curr:.2f} %" if us10_curr is not None else "N/A",
        delta=f"Sklon: {us_spread_curr * 100:+.0f} bps",
        delta_color="off",
        help="Výnos 10letého referenčního vládního dluhopisu USA."
    )


# =============================================================================
# 8. GENERÁTORY GRAFŮ (PLOTLY BUILDERS)
# =============================================================================

def build_rates_chart(dframe: pd.DataFrame, indicators: List[str]) -> go.Figure:
    """Vytvoří graf měnové politiky ČNB (úrokový koridor) a PRIBOR sazeb."""
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
        height=450,
        hovermode="x unified",
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor="rgba(255, 255, 255, 0.8)"),
        xaxis=dict(title="", showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(title="Úrokové sazby (%)", title_font=dict(color="#1D4ED8"), tickfont=dict(color="#1D4ED8"), showgrid=True, gridcolor="#f1f5f9", ticksuffix=" %"),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF"
    )
    return fig


def build_inflation_chart(dframe: pd.DataFrame) -> go.Figure:
    """Vytvoří detailní graf inflace s inflačním cílem ČNB a reálnou úrokovou sazbou."""
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
                hovertemplate="<b>Inflace CPI</b>: %{y:.1f} %<extra></extra>"
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
                name="Reálná úroková sazba (Repo − CPI)",
                line=dict(color="#6366F1", width=2.0, dash="dot"),
                hovertemplate="<b>Reálná sazba</b>: %{y:.1f} %<extra></extra>"
            ),
            secondary_y=True
        )
        fig.add_hline(y=0.0, line=dict(color="#94A3B8", width=1.2, dash="dash"), secondary_y=True)

    fig.update_layout(
        height=450,
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


def build_gdp_chart(dframe: pd.DataFrame, indicators: List[str]) -> go.Figure:
    """Vytvoří kombinovaný graf HDP (sloupce nominálu v mld. CZK a čára reálného růstu v %)."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    df_gdp_plot = dframe.drop_duplicates(subset=["quarter"] if "quarter" in dframe.columns else ["date"]).copy()

    if "gdp_nominal_czk_bn" in indicators and "gdp_nominal_czk_bn" in dframe.columns:
        fig.add_trace(
            go.Bar(
                x=df_gdp_plot["date"],
                y=df_gdp_plot["gdp_nominal_czk_bn"],
                name="Nominální HDP (mld. CZK)",
                marker=dict(color="rgba(71, 85, 105, 0.55)", line=dict(color="#334155", width=1)),
                hovertemplate="<b>Nominální HDP</b>: %{y:,.1f} mld. CZK<extra></extra>"
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
                name="Reálný růst HDP (YoY %)",
                line=dict(color="#D97706", width=3),
                marker=dict(size=7, color=marker_colors, line=dict(color="#FFFFFF", width=1.5)),
                hovertemplate="<b>Reálný růst</b>: %{y:+.1f} %<extra></extra>"
            ),
            secondary_y=True
        )
        fig.add_hline(y=0.0, line=dict(color="#94A3B8", width=1.5, dash="dash"), secondary_y=True)

    fig.update_layout(
        height=450,
        hovermode="x unified",
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor="rgba(255, 255, 255, 0.8)"),
        xaxis=dict(title="", showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(title="Nominální HDP (mld. CZK / kvartál)", title_font=dict(color="#334155"), tickfont=dict(color="#334155"), showgrid=True, gridcolor="#f1f5f9", ticksuffix=" mld."),
        yaxis2=dict(title="Reálný růst HDP (YoY %)", title_font=dict(color="#D97706"), tickfont=dict(color="#D97706"), overlaying="y", side="right", showgrid=False, ticksuffix=" %"),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF"
    )
    return fig


def build_unemployment_chart(dframe: pd.DataFrame) -> go.Figure:
    """Vytvoří plošný graf míry nezaměstnanosti s dlouhodobým průměrem a extrémy."""
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
            hovertemplate="<b>Nezaměstnanost</b>: %{y:.1f} %<extra></extra>"
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


def build_fx_chart(dframe: pd.DataFrame) -> go.Figure:
    """Vytvoří graf měnových kurzů EUR/CZK a USD/CZK."""
    fig = go.Figure()

    # Křivka EUR/CZK
    if "eur_czk" in dframe.columns:
        fig.add_trace(go.Scatter(
            x=dframe["date"],
            y=dframe["eur_czk"],
            mode="lines",
            name="EUR / CZK (Kč za 1 €)",
            line=dict(color="#2563EB", width=3.0),
            hovertemplate="<b>EUR/CZK</b>: %{y:.2f} Kč<extra></extra>"
        ))

    # Křivka USD/CZK
    if "usd_czk" in dframe.columns:
        fig.add_trace(go.Scatter(
            x=dframe["date"],
            y=dframe["usd_czk"],
            mode="lines",
            name="USD / CZK (Kč za 1 $)",
            line=dict(color="#059669", width=2.4),
            hovertemplate="<b>USD/CZK</b>: %{y:.2f} Kč<extra></extra>"
        ))

    # Referenční linie: kurzový závazek ČNB (27.00 CZK/EUR)
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
        yaxis=dict(title="Směnný kurz (CZK)", ticksuffix=" Kč", showgrid=True, gridcolor="#f1f5f9"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor="rgba(255, 255, 255, 0.8)"),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF"
    )
    return fig


def build_debt_charts(dframe: pd.DataFrame) -> Tuple[go.Figure, go.Figure]:
    """Vytvoří grafy pro veřejný dluh k HDP a pro saldo státního rozpočtu (deficit/přebytek)."""
    df_q_plot = dframe.drop_duplicates(subset=["quarter"] if "quarter" in dframe.columns else ["date"]).copy()

    # 1. Graf dluhu k HDP (%)
    fig_debt = go.Figure()
    if "public_debt_gdp_pct" in df_q_plot.columns:
        # Zelená zóna pod 60 % Maastrichtským limitem
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

        # Referenční průměr Eurozóny (~88 % HDP)
        fig_debt.add_hline(
            y=88.0,
            line=dict(color="#94A3B8", width=1.5, dash="dot"),
            annotation_text="Průměr EU / Eurozóny (~88 % HDP)",
            annotation_position="top right",
            annotation_font=dict(color="#64748B", size=10)
        )

    fig_debt.update_layout(
        height=400,
        hovermode="x unified",
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis=dict(title="", showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(title="Veřejný dluh (% HDP)", ticksuffix=" %", showgrid=True, gridcolor="#f1f5f9", range=[20, 95]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF"
    )

    # 2. Graf salda státního rozpočtu (deficit v mld. CZK)
    fig_def = go.Figure()
    if "budget_deficit_czk_bn" in df_q_plot.columns:
        bar_colors = ["#16A34A" if v >= 0 else "#DC2626" for v in df_q_plot["budget_deficit_czk_bn"]]
        fig_def.add_trace(go.Bar(
            x=df_q_plot["date"],
            y=df_q_plot["budget_deficit_czk_bn"],
            name="Kvartální saldo rozpočtu",
            marker=dict(color=bar_colors),
            hovertemplate="<b>Saldo rozpočtu</b>: %{y:+.1f} mld. CZK<extra></extra>"
        ))
        fig_def.add_hline(y=0.0, line=dict(color="#475569", width=1.5))

    fig_def.update_layout(
        height=380,
        hovermode="x unified",
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis=dict(title="", showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(title="Saldo rozpočtu (mld. CZK)", ticksuffix=" mld.", showgrid=True, gridcolor="#f1f5f9"),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF"
    )

    return fig_debt, fig_def


def build_rates_vs_inflation_chart(dframe: pd.DataFrame, indicators: List[str]) -> go.Figure:
    """Vytvoří souhrnný graf měnové politiky vs inflace s duální osou Y."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    if "lombard_rate" in indicators and "lombard_rate" in dframe.columns:
        fig.add_trace(go.Scatter(x=dframe["date"], y=dframe["lombard_rate"], mode="lines", name="Lombardní sazba", line=dict(color="rgba(148, 163, 184, 0.7)", width=1.5, dash="dash")), secondary_y=False)
    if "discount_rate" in indicators and "discount_rate" in dframe.columns:
        fig.add_trace(go.Scatter(x=dframe["date"], y=dframe["discount_rate"], mode="lines", name="Diskontní sazba", line=dict(color="rgba(148, 163, 184, 0.7)", width=1.5, dash="dash"), fill="tonexty" if "lombard_rate" in indicators else None, fillcolor="rgba(226, 232, 240, 0.35)"), secondary_y=False)
    if "repo_rate" in indicators and "repo_rate" in dframe.columns:
        fig.add_trace(go.Scatter(x=dframe["date"], y=dframe["repo_rate"], mode="lines", name="2T Repo sazba", line=dict(color="#1D4ED8", width=3.5, shape="hv")), secondary_y=False)
    if "pribor_3m" in indicators and "pribor_3m" in dframe.columns:
        fig.add_trace(go.Scatter(x=dframe["date"], y=dframe["pribor_3m"], mode="lines", name="PRIBOR 3M", line=dict(color="#0D9488", width=2.2)), secondary_y=False)
    if "cpi_yoy" in indicators and "cpi_yoy" in dframe.columns:
        fig.add_trace(go.Scatter(x=dframe["date"], y=dframe["cpi_yoy"], mode="lines+markers", name="Inflace CPI (YoY %)", line=dict(color="#DC2626", width=2.5), marker=dict(size=4, color="#DC2626")), secondary_y=True)
        fig.add_hline(y=2.0, line=dict(color="#16A34A", width=1.5, dash="dash"), secondary_y=True)

    fig.update_layout(
        height=450,
        hovermode="x unified",
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor="rgba(255, 255, 255, 0.8)"),
        xaxis=dict(title="", showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(title="Sazby ČNB & PRIBOR (%)", title_font=dict(color="#1D4ED8"), tickfont=dict(color="#1D4ED8"), showgrid=True, gridcolor="#f1f5f9", ticksuffix=" %"),
        yaxis2=dict(title="Inflace CPI (%)", title_font=dict(color="#DC2626"), tickfont=dict(color="#DC2626"), overlaying="y", side="right", showgrid=False, ticksuffix=" %"),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF"
    )
    return fig


def build_yield_curve_snapshot(
    df_row: pd.Series,
    compare_row: Optional[pd.Series] = None,
    show_czgb: bool = True,
    show_irs: bool = True,
    compare_label: str = "Před 1 rokem",
    show_values: bool = True
) -> go.Figure:
    """
    Vytvoří graf časové struktury výnosové křivky (Term Structure):
    X-osa = Splatnosti (1Y, 2Y, 3Y, 5Y, 7Y, 10Y, 15Y)
    Y-osa = Výnos do splatnosti / Swapová sazba (% p.a.)
    """
    tenor_keys = ["1y", "2y", "3y", "5y", "7y", "10y", "15y"]
    tenor_labels = ["1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "15Y"]

    fig = go.Figure()

    czgb_vals = [df_row.get(f"czgb_{k}") for k in tenor_keys]
    irs_vals = [df_row.get(f"irs_{k}") for k in tenor_keys]
    comp_czgb = [compare_row.get(f"czgb_{k}") for k in tenor_keys] if compare_row is not None else []

    # 1. České státní dluhopisy (CZGB)
    if show_czgb:
        czgb_mode = "lines+markers+text" if show_values else "lines+markers"
        czgb_text = [
            f"<b>{v:.2f} %</b>" if (v is not None and not pd.isna(v)) else ""
            for v in czgb_vals
        ] if show_values else None

        # Dynamické určení pozice popisků CZGB:
        # Pokud je zobrazen IRS a je vyšší než CZGB, popisek CZGB je dole pod bodem; jinak nahoře
        czgb_pos = []
        for k in tenor_keys:
            c_val = df_row.get(f"czgb_{k}")
            i_val = df_row.get(f"irs_{k}") if show_irs else None
            if i_val is not None and c_val is not None and i_val >= c_val:
                czgb_pos.append("bottom center")
            elif i_val is not None and c_val is not None and i_val < c_val:
                czgb_pos.append("top center")
            else:
                czgb_pos.append("bottom center" if show_irs else "top center")

        fig.add_trace(go.Scatter(
            x=tenor_labels,
            y=czgb_vals,
            mode=czgb_mode,
            name="České státní dluhopisy (CZGB)",
            line=dict(color="#1D4ED8", width=3.5),
            marker=dict(size=9, color="#1D4ED8", symbol="circle"),
            text=czgb_text,
            textposition=czgb_pos if show_values else None,
            textfont=dict(size=10, color="#1D4ED8"),
            cliponaxis=False,
            hovertemplate="<b>CZGB %{x}</b>: %{y:.2f} % p.a.<extra></extra>"
        ))

    # 2. Úrokové swapy (IRS)
    if show_irs:
        irs_mode = "lines+markers+text" if show_values else "lines+markers"
        irs_text = [
            f"<b>{v:.2f} %</b>" if (v is not None and not pd.isna(v)) else ""
            for v in irs_vals
        ] if show_values else None

        # Dynamická pozice popisků IRS: nahoře pokud je IRS >= CZGB, jinak dole
        irs_pos = []
        for k in tenor_keys:
            c_val = df_row.get(f"czgb_{k}") if show_czgb else None
            i_val = df_row.get(f"irs_{k}")
            if c_val is not None and i_val is not None and i_val < c_val:
                irs_pos.append("bottom center")
            else:
                irs_pos.append("top center")

        asw_texts = []
        for k in tenor_keys:
            y_val = df_row.get(f"czgb_{k}")
            i_val = df_row.get(f"irs_{k}")
            if y_val is not None and i_val is not None:
                spread_bps = (i_val - y_val) * 100.0
                asw_texts.append(f"ASW Spread: +{spread_bps:.0f} bps")
            else:
                asw_texts.append("")

        fig.add_trace(go.Scatter(
            x=tenor_labels,
            y=irs_vals,
            mode=irs_mode,
            name="Úrokové swapy (CZK IRS)",
            line=dict(color="#0D9488", width=3.0, dash="dash"),
            marker=dict(size=8, color="#0D9488", symbol="square"),
            text=irs_text,
            textposition=irs_pos if show_values else None,
            textfont=dict(size=10, color="#0F766E"),
            cliponaxis=False,
            customdata=asw_texts,
            hovertemplate="<b>CZK IRS %{x}</b>: %{y:.2f} % p.a.<br>%{customdata}<extra></extra>"
        ))

    # 3. Srovnávací historická křivka (např. před 1 rokem)
    if compare_row is not None:
        comp_mode = "lines+markers+text" if show_values else "lines+markers"
        comp_text = [
            f"<b>{v:.2f} %</b>" if (v is not None and not pd.isna(v)) else ""
            for v in comp_czgb
        ] if show_values else None

        comp_pos = []
        for k in tenor_keys:
            c_val = df_row.get(f"czgb_{k}")
            cmp_val = compare_row.get(f"czgb_{k}")
            if c_val is not None and cmp_val is not None and cmp_val > c_val:
                comp_pos.append("top center")
            else:
                comp_pos.append("bottom center")

        fig.add_trace(go.Scatter(
            x=tenor_labels,
            y=comp_czgb,
            mode=comp_mode,
            name=f"CZGB ({compare_label})",
            line=dict(color="#94A3B8", width=2.0, dash="dot"),
            marker=dict(size=7, color="#94A3B8", symbol="diamond"),
            text=comp_text,
            textposition=comp_pos if show_values else None,
            textfont=dict(size=9, color="#64748B"),
            cliponaxis=False,
            hovertemplate=f"<b>CZGB %{{x}} ({compare_label})</b>: %{{y:.2f}} % p.a.<extra></extra>"
        ))

    dt_obj = df_row.get("date")
    dt_str = dt_obj.strftime("%d.%m.%Y") if hasattr(dt_obj, "strftime") else "Aktuální"

    # Výpočet rozsahu osy Y s rezervou pro popisky hodnot
    all_y = []
    if show_czgb:
        all_y.extend([v for v in czgb_vals if v is not None and not pd.isna(v)])
    if show_irs:
        all_y.extend([v for v in irs_vals if v is not None and not pd.isna(v)])
    if compare_row is not None:
        all_y.extend([v for v in comp_czgb if v is not None and not pd.isna(v)])

    yaxis_dict = dict(
        title="Výnos / Sazba swapu (% p.a.)",
        ticksuffix=" %",
        showgrid=True,
        gridcolor="#F1F5F9"
    )
    if all_y and show_values:
        y_min = min(all_y)
        y_max = max(all_y)
        y_pad = max(0.28, (y_max - y_min) * 0.12)
        yaxis_dict["range"] = [y_min - y_pad, y_max + y_pad]

    fig.update_layout(
        title=dict(
            text=f"Výnosová křivka ČR k datu: {dt_str}",
            font=dict(size=14, color="#1E293B")
        ),
        height=450,
        hovermode="x unified",
        margin=dict(l=20, r=20, t=50, b=25),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(255, 255, 255, 0.85)"
        ),
        xaxis=dict(
            title="Doba do splatnosti (Tenor)",
            showgrid=True,
            gridcolor="#F1F5F9"
        ),
        yaxis=yaxis_dict,
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF"
    )
    return fig


def build_yield_history_chart(dframe: pd.DataFrame, show_irs_history: bool = True) -> go.Figure:
    """Vytvoří časový graf vývoje klíčových výnosů CZGB (2Y, 5Y, 10Y, 15Y) a IRS v čase."""
    fig = go.Figure()

    if "repo_rate" in dframe.columns:
        fig.add_trace(go.Scatter(
            x=dframe["date"],
            y=dframe["repo_rate"],
            mode="lines",
            name="2T Repo sazba ČNB",
            line=dict(color="#CBD5E1", width=1.8, dash="dash"),
            hovertemplate="<b>2T Repo</b>: %{y:.2f} %<extra></extra>"
        ))

    if "czgb_2y" in dframe.columns:
        fig.add_trace(go.Scatter(
            x=dframe["date"],
            y=dframe["czgb_2y"],
            mode="lines",
            name="CZGB 2Y (krátký konec)",
            line=dict(color="#06B6D4", width=2.0),
            hovertemplate="<b>CZGB 2Y</b>: %{y:.2f} %<extra></extra>"
        ))

    if "czgb_5y" in dframe.columns:
        fig.add_trace(go.Scatter(
            x=dframe["date"],
            y=dframe["czgb_5y"],
            mode="lines",
            name="CZGB 5Y (střed)",
            line=dict(color="#3B82F6", width=2.0),
            hovertemplate="<b>CZGB 5Y</b>: %{y:.2f} %<extra></extra>"
        ))

    if "czgb_10y" in dframe.columns:
        fig.add_trace(go.Scatter(
            x=dframe["date"],
            y=dframe["czgb_10y"],
            mode="lines",
            name="CZGB 10Y (benchmark)",
            line=dict(color="#1D4ED8", width=3.5),
            hovertemplate="<b>CZGB 10Y</b>: %{y:.2f} %<extra></extra>"
        ))

    if "czgb_15y" in dframe.columns:
        fig.add_trace(go.Scatter(
            x=dframe["date"],
            y=dframe["czgb_15y"],
            mode="lines",
            name="CZGB 15Y (dlouhý konec)",
            line=dict(color="#7C3AED", width=2.0),
            hovertemplate="<b>CZGB 15Y</b>: %{y:.2f} %<extra></extra>"
        ))

    if show_irs_history and "irs_10y" in dframe.columns:
        fig.add_trace(go.Scatter(
            x=dframe["date"],
            y=dframe["irs_10y"],
            mode="lines",
            name="CZK IRS 10Y",
            line=dict(color="#0D9488", width=2.2, dash="dot"),
            hovertemplate="<b>IRS 10Y</b>: %{y:.2f} %<extra></extra>"
        ))

    fig.update_layout(
        title=dict(text="Časový vývoj benchmarkových výnosů CZGB a IRS", font=dict(size=14, color="#1E293B")),
        height=400,
        hovermode="x unified",
        margin=dict(l=20, r=20, t=45, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor="rgba(255, 255, 255, 0.85)"),
        xaxis=dict(title="", showgrid=True, gridcolor="#F1F5F9"),
        yaxis=dict(title="Výnos do splatnosti (% p.a.)", ticksuffix=" %", showgrid=True, gridcolor="#F1F5F9"),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF"
    )
    return fig


def build_curve_spread_chart(dframe: pd.DataFrame) -> go.Figure:
    """
    Vytvoří graf sklonu výnosové křivky (Spread 10Y − 2Y v bazických bodech bps)
    s barevným vyznačením inverzní zóny (< 0 bps).
    """
    fig = go.Figure()

    if "czgb_spread_10y_2y" in dframe.columns:
        spread_bps = dframe["czgb_spread_10y_2y"] * 100.0

        fig.add_trace(go.Scatter(
            x=dframe["date"],
            y=spread_bps,
            mode="lines",
            name="Sklon křivky (10Y − 2Y)",
            line=dict(color="#2563EB", width=2.5),
            hovertemplate="<b>Sklon (10Y - 2Y)</b>: %{y:+.0f} bps<extra></extra>"
        ))

        fig.add_hline(
            y=0.0,
            line=dict(color="#DC2626", width=1.8, dash="dash"),
            annotation_text="Hranice inverze (0 bps)",
            annotation_position="top left"
        )

    fig.update_layout(
        title=dict(text="Sklon výnosové křivky (Spread 10Y − 2Y v bps) | Indikátor inverze", font=dict(size=14, color="#1E293B")),
        height=400,
        hovermode="x unified",
        margin=dict(l=20, r=20, t=45, b=20),
        xaxis=dict(title="", showgrid=True, gridcolor="#F1F5F9"),
        yaxis=dict(title="Rozpětí (bps)", ticksuffix=" bps", showgrid=True, gridcolor="#F1F5F9"),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF"
    )
    return fig


def build_us_yield_curve_snapshot(
    df_row: pd.Series,
    compare_row: Optional[pd.Series] = None,
    show_czgb: bool = False,
    compare_label: str = "Před 1 rokem",
    show_values: bool = True
) -> go.Figure:
    """
    Vytvoří graf časové struktury US výnosové křivky (U.S. Treasury Par Yield Curve):
    X-osa = Splatnosti (1M, 3M, 6M, 1Y, 2Y, 3Y, 5Y, 7Y, 10Y, 20Y, 30Y)
    Y-osa = Výnos do splatnosti (% p.a.)
    """
    tenor_keys = ["1m", "3m", "6m", "1y", "2y", "3y", "5y", "7y", "10y", "20y", "30y"]
    tenor_labels = ["1M", "3M", "6M", "1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y"]

    fig = go.Figure()

    us_vals = [df_row.get(f"us_{k}") for k in tenor_keys]
    comp_us = [compare_row.get(f"us_{k}") for k in tenor_keys] if compare_row is not None else []

    # 1. Hlavní křivka: US Treasuries
    us_mode = "lines+markers+text" if show_values else "lines+markers"
    us_text = [
        f"<b>{v:.2f} %</b>" if (v is not None and not pd.isna(v)) else ""
        for v in us_vals
    ] if show_values else None

    fig.add_trace(go.Scatter(
        x=tenor_labels,
        y=us_vals,
        mode=us_mode,
        name="U.S. Treasury Yield Curve (Aktuální)",
        line=dict(color="#2563EB", width=3.5),
        marker=dict(size=9, color="#2563EB", symbol="circle"),
        text=us_text,
        textposition="top center",
        textfont=dict(size=10, color="#1E40AF"),
        cliponaxis=False,
        hovertemplate="<b>US Treasury %{x}</b>: %{y:.2f} % p.a.<extra></extra>"
    ))

    # 2. Srovnávací referenční křivka v čase
    if compare_row is not None:
        comp_mode = "lines+markers+text" if show_values else "lines+markers"
        comp_text = [
            f"<b>{v:.2f} %</b>" if (v is not None and not pd.isna(v)) else ""
            for v in comp_us
        ] if show_values else None

        fig.add_trace(go.Scatter(
            x=tenor_labels,
            y=comp_us,
            mode=comp_mode,
            name=f"US Treasury ({compare_label})",
            line=dict(color="#94A3B8", width=2.0, dash="dot"),
            marker=dict(size=7, color="#94A3B8", symbol="diamond"),
            text=comp_text,
            textposition="bottom center",
            textfont=dict(size=9, color="#64748B"),
            cliponaxis=False,
            hovertemplate=f"<b>US Treasury %{{x}} ({compare_label})</b>: %{{y:.2f}} % p.a.<extra></extra>"
        ))

    # 3. Volitelné srovnání s českými státními dluhopisy (CZGB)
    if show_czgb:
        czgb_map = {
            "1Y": df_row.get("czgb_1y"),
            "2Y": df_row.get("czgb_2y"),
            "3Y": df_row.get("czgb_3y"),
            "5Y": df_row.get("czgb_5y"),
            "7Y": df_row.get("czgb_7y"),
            "10Y": df_row.get("czgb_10y"),
        }
        cz_x = [k for k in czgb_map.keys() if czgb_map[k] is not None and not pd.isna(czgb_map[k])]
        cz_y = [czgb_map[k] for k in cz_x]
        cz_text = [f"<b>{v:.2f} %</b>" for v in cz_y] if show_values else None

        fig.add_trace(go.Scatter(
            x=cz_x,
            y=cz_y,
            mode="lines+markers+text" if show_values else "lines+markers",
            name="České státní dluhopisy (CZGB)",
            line=dict(color="#059669", width=2.5, dash="dash"),
            marker=dict(size=8, color="#059669", symbol="square"),
            text=cz_text,
            textposition="bottom center",
            textfont=dict(size=9, color="#047857"),
            cliponaxis=False,
            hovertemplate="<b>CZGB %{x}</b>: %{y:.2f} % p.a.<extra></extra>"
        ))

    dt_obj = df_row.get("date")
    dt_str = dt_obj.strftime("%d.%m.%Y") if hasattr(dt_obj, "strftime") else "Aktuální"

    all_y = [v for v in us_vals if v is not None and not pd.isna(v)]
    if compare_row is not None:
        all_y.extend([v for v in comp_us if v is not None and not pd.isna(v)])

    yaxis_dict = dict(
        title="Výnos do splatnosti (% p.a.)",
        ticksuffix=" %",
        showgrid=True,
        gridcolor="#F1F5F9"
    )
    if all_y and show_values:
        y_min = min(all_y)
        y_max = max(all_y)
        y_pad = max(0.30, (y_max - y_min) * 0.12)
        yaxis_dict["range"] = [y_min - y_pad, y_max + y_pad]

    fig.update_layout(
        title=dict(
            text=f"Výnosová křivka USA (U.S. Treasury) k datu: {dt_str}",
            font=dict(size=14, color="#1E293B")
        ),
        height=450,
        hovermode="x unified",
        margin=dict(l=20, r=20, t=50, b=25),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(255, 255, 255, 0.85)"
        ),
        xaxis=dict(
            title="Splatnost (Tenor)",
            showgrid=True,
            gridcolor="#F1F5F9"
        ),
        yaxis=yaxis_dict,
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF"
    )
    return fig


def build_us_yield_history_chart(dframe: pd.DataFrame) -> go.Figure:
    """Vytvoří časový graf vývoje klíčových výnosů US Treasuries (2Y, 5Y, 10Y, 30Y, 3M) v čase."""
    fig = go.Figure()

    if "us_3m" in dframe.columns:
        fig.add_trace(go.Scatter(
            x=dframe["date"],
            y=dframe["us_3m"],
            mode="lines",
            name="US 3M Bill (Fed proxy)",
            line=dict(color="#94A3B8", width=1.8, dash="dash"),
            hovertemplate="<b>US 3M Bill</b>: %{y:.2f} %<extra></extra>"
        ))

    if "us_2y" in dframe.columns:
        fig.add_trace(go.Scatter(
            x=dframe["date"],
            y=dframe["us_2y"],
            mode="lines",
            name="US 2Y Treasury (krátký konec)",
            line=dict(color="#0284C7", width=2.2),
            hovertemplate="<b>US 2Y</b>: %{y:.2f} %<extra></extra>"
        ))

    if "us_5y" in dframe.columns:
        fig.add_trace(go.Scatter(
            x=dframe["date"],
            y=dframe["us_5y"],
            mode="lines",
            name="US 5Y Treasury",
            line=dict(color="#6366F1", width=2.0),
            hovertemplate="<b>US 5Y</b>: %{y:.2f} %<extra></extra>"
        ))

    if "us_10y" in dframe.columns:
        fig.add_trace(go.Scatter(
            x=dframe["date"],
            y=dframe["us_10y"],
            mode="lines",
            name="US 10Y Treasury (benchmark)",
            line=dict(color="#2563EB", width=3.5),
            hovertemplate="<b>US 10Y</b>: %{y:.2f} %<extra></extra>"
        ))

    if "us_30y" in dframe.columns:
        fig.add_trace(go.Scatter(
            x=dframe["date"],
            y=dframe["us_30y"],
            mode="lines",
            name="US 30Y Treasury (Long Bond)",
            line=dict(color="#7C3AED", width=2.0),
            hovertemplate="<b>US 30Y</b>: %{y:.2f} %<extra></extra>"
        ))

    fig.update_layout(
        title=dict(text="Časový vývoj referenčních výnosů US Treasury (2Y, 5Y, 10Y, 30Y a 3M)", font=dict(size=14, color="#1E293B")),
        height=400,
        hovermode="x unified",
        margin=dict(l=20, r=20, t=45, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor="rgba(255, 255, 255, 0.85)"),
        xaxis=dict(title="", showgrid=True, gridcolor="#F1F5F9"),
        yaxis=dict(title="Výnos do splatnosti (% p.a.)", ticksuffix=" %", showgrid=True, gridcolor="#F1F5F9"),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF"
    )
    return fig


def build_us_curve_spread_chart(dframe: pd.DataFrame) -> go.Figure:
    """
    Vytvoří graf sklonu výnosové křivky USA (Spread 10Y − 2Y v bazických bodech bps)
    s vyznačením inverzní zóny (< 0 bps) – klíčový globální indikátor recese.
    """
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
        height=400,
        hovermode="x unified",
        margin=dict(l=20, r=20, t=45, b=20),
        xaxis=dict(title="", showgrid=True, gridcolor="#F1F5F9"),
        yaxis=dict(title="Rozpětí (bps)", ticksuffix=" bps", showgrid=True, gridcolor="#F1F5F9"),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF"
    )
    return fig


def build_cz_vs_us_spread_chart(dframe: pd.DataFrame) -> go.Figure:
    """
    Vytvoří graf rozpětí mezi 10Y státním dluhopisem ČR (CZGB) a 10Y US Treasury (v bps).
    Představuje sovereign / měnovou prémii koruny vůči dolaru.
    """
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
        height=400,
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
# 10. ZÁLOŽKY (PŘEHLEDNÝ A MINIMALISTICKÝ DESIGN BEZ IKONEK)
# =============================================================================

tab_rates, tab_inflation, tab_gdp, tab_une, tab_fx, tab_debt, tab_cz_curve, tab_us_curve, tab_cz_us, tab_all, tab_table = st.tabs([
    "Sazby (ČNB)",
    "Inflace (CPI)",
    "HDP",
    "Nezaměstnanost",
    "Měnové kurzy",
    "Veřejný dluh",
    "CZ výnosová křivka",
    "US výnosová křivka",
    "Srovnání CZ vs. US",
    "Všechny grafy",
    "Data a export"
])

# -----------------------------------------------------------------------------
# TAB 1: SAZBY (ČNB & PRIBOR)
# -----------------------------------------------------------------------------
with tab_rates:
    st.markdown('<div class="section-header">Měnová politika ČNB a mezibankovní sazby PRIBOR</div>', unsafe_allow_html=True)
    st.caption("Úrokový koridor České národní banky: 2T Repo sazba, Diskontní sazba (depozitní facilita) a Lombardní sazba (zápůjční facilita) ve srovnání s tržními sazbami PRIBOR.")
    
    col_r1, col_r2, col_r3, col_r4 = st.columns(4)
    disc_val = last_row.get("discount_rate")
    lomb_val = last_row.get("lombard_rate")
    prib3m_val = last_row.get("pribor_3m")
    
    col_r1.metric("2T Repo sazba", f"{repo_curr:.2f} %" if repo_curr is not None else "N/A", help="Hlavní nástroj stahování likvidity")
    col_r2.metric("Diskontní sazba (dolní mez)", f"{disc_val:.2f} %" if disc_val is not None else "N/A", help="Úročení vkladů bank přes noc u ČNB")
    col_r3.metric("Lombardní sazba (horní mez)", f"{lomb_val:.2f} %" if lomb_val is not None else "N/A", help="Úročení zápůjček bank přes noc od ČNB")
    col_r4.metric("PRIBOR 3M", f"{prib3m_val:.2f} %" if prib3m_val is not None else "N/A", help="Referenční tržní sazba")

    fig_rates = build_rates_chart(df, selected_indicators)
    render_plotly_chart(fig_rates, key="chart_rates")

    st.info(
        "💡 **Úrokový koridor ČNB:** ČNB udržuje koridor o šířce 200 bazických bodů (2,0 p.b.) se středem v 2T repo sazbě. "
        "Sazby PRIBOR na mezibankovním trhu kopírují repo sazbu s mírnou tržní přirážkou podle splatnosti (1M, 3M, 6M)."
    )

# -----------------------------------------------------------------------------
# TAB 2: INFLACE (CPI)
# -----------------------------------------------------------------------------
with tab_inflation:
    st.markdown('<div class="section-header">Vývoj inflace (CPI) a reálné úrokové míry</div>', unsafe_allow_html=True)
    st.caption("Meziroční index spotřebitelských cen (HICP / CPI) vůči inflačnímu cíli ČNB (2,0 %) a vývoj reálné úrokové sazby (2T Repo − CPI).")

    col_i1, col_i2, col_i3 = st.columns(3)
    target_diff = (cpi_curr - 2.0) if cpi_curr is not None else 0.0
    real_rate_curr = (repo_curr - cpi_curr) if (repo_curr is not None and cpi_curr is not None) else 0.0

    col_i1.metric("Aktuální inflace CPI", f"{cpi_curr:.1f} %" if cpi_curr is not None else "N/A", delta=f"{cpi_delta:+.1f} p.b.", delta_color="inverse")
    col_i2.metric("Odchylka od 2% cíle ČNB", f"{target_diff:+.1f} p.b.", help="Cíl ČNB je 2.0 % s tolerančním pásmem 1–3 %")
    col_i3.metric("Reálná repo sazba (Repo − CPI)", f"{real_rate_curr:+.2f} %", delta="Restrikce" if real_rate_curr > 0 else "Uvolnění", delta_color="off", help="Kladná hodnota znamená reálně restriktivní měnovou politiku")

    fig_inf = build_inflation_chart(df)
    render_plotly_chart(fig_inf, key="chart_inflation")

    st.info(
        "💡 **Reálná úroková míra:** V období inflačního vrcholu (2022–2023) byly reálné sazby hluboko v záporu (až −11 %). "
        "S návratem inflace do tolerančního pásma ČNB (1–3 %) v roce 2024 se reálné sazby vrátily do kladného teritoria."
    )

# -----------------------------------------------------------------------------
# TAB 3: HDP (RŮST A OBJEM)
# -----------------------------------------------------------------------------
with tab_gdp:
    st.markdown('<div class="section-header">Hrubý domácí produkt: Reálný růst v % a nominální tvorba</div>', unsafe_allow_html=True)
    st.caption("Kvartální výkon české ekonomiky: Nominální objem HDP v miliardách Kč (sloupce, levá osa) a meziroční reálné tempo růstu (čára, pravá osa).")

    df_gdp_unique = df.drop_duplicates(subset=["quarter"] if "quarter" in df.columns else ["date"])
    last_nom_gdp = df_gdp_unique.iloc[-1].get("gdp_nominal_czk_bn") if not df_gdp_unique.empty else None
    
    col_g1, col_g2, col_g3 = st.columns(3)
    col_g1.metric("Reálný růst HDP (YoY)", f"{gdp_curr:+.1f} %" if gdp_curr is not None else "N/A", delta=f"{gdp_delta:+.1f} p.b.")
    col_g2.metric("Kvartální nominální HDP", f"{last_nom_gdp:,.1f} mld. Kč".replace(",", " ") if last_nom_gdp is not None else "N/A", help="Běžné ceny za poslední známý kvartál")
    annualized_nom = (last_nom_gdp * 4) if last_nom_gdp is not None else 0.0
    col_g3.metric("Přepočtený roční objem HDP", f"{annualized_nom:,.0f} mld. Kč".replace(",", " ") if annualized_nom else "N/A", help="Odhad roční nominální produkce")

    fig_gdp = build_gdp_chart(df, selected_indicators)
    render_plotly_chart(fig_gdp, key="chart_gdp")

    st.info(
        "💡 **Nominální vs. reálné HDP:** Nominální objem HDP v mld. CZK prudce vzrostl i v době stagnace z důvodu vysoké cenové hladiny (deflátoru HDP). "
        "Reálný růst očišťuje vývoj o cenové vlivy a sezónnost."
    )

# -----------------------------------------------------------------------------
# TAB 4: NEZAMĚSTNANOST
# -----------------------------------------------------------------------------
with tab_une:
    st.markdown('<div class="section-header">Trh práce: Míra nezaměstnanosti v České republice</div>', unsafe_allow_html=True)
    st.caption("Sezónně očištěná obecná míra nezaměstnanosti dle metodiky ILO / Eurostat pro věkovou skupinu 15–74 let.")

    col_u1, col_u2, col_u3, col_u4 = st.columns(4)
    avg_une_val = df["unemployment_rate"].mean() if "unemployment_rate" in df.columns else None
    min_une_val = df["unemployment_rate"].min() if "unemployment_rate" in df.columns else None
    max_une_val = df["unemployment_rate"].max() if "unemployment_rate" in df.columns else None

    col_u1.metric("Aktuální nezaměstnanost", f"{une_curr:.1f} %" if une_curr is not None else "N/A", delta=f"{une_delta:+.1f} p.b.", delta_color="inverse")
    col_u2.metric("Dlouhodobý průměr", f"{avg_une_val:.2f} %" if avg_une_val is not None else "N/A", help="Průměr ve zvoleném období")
    col_u3.metric("Historické minimum", f"{min_une_val:.1f} %" if min_une_val is not None else "N/A", help="Nejnižší hodnota ve sledovaném období")
    col_u4.metric("Historické maximum", f"{max_une_val:.1f} %" if max_une_val is not None else "N/A", help="Nejvyšší hodnota ve sledovaném období")

    fig_une = build_unemployment_chart(df)
    render_plotly_chart(fig_une, key="chart_unemployment")

    st.info(
        "💡 **Český trh práce:** Česká republika si stabilně udržuje nejnižší nebo jednu z nejnižších měr nezaměstnanosti v rámci celé Evropské unie. "
        "Trh práce zůstává strukturálně napjatý s vysokou poptávkou po kvalifikované i technické pracovní síle."
    )

# -----------------------------------------------------------------------------
# TAB 5: MĚNOVÉ KURZY (FX: EUR & USD)
# -----------------------------------------------------------------------------
with tab_fx:
    st.markdown('<div class="section-header">Měnové kurzy: Vývoj české koruny vůči EUR a USD</div>', unsafe_allow_html=True)
    st.caption("Oficiální kurzy devizového trhu České národní banky (ČNB fixing) pro měnové páry EUR/CZK a USD/CZK.")

    col_fx1, col_fx2, col_fx3, col_fx4 = st.columns(4)
    eur_prev = prev_row.get("eur_czk")
    eur_delta = (eur_curr - eur_prev) if (eur_curr is not None and eur_prev is not None) else 0.0

    usd_prev = prev_row.get("usd_czk")
    usd_delta = (usd_curr - usd_prev) if (usd_curr is not None and usd_prev is not None) else 0.0

    cross_eurusd = (eur_curr / usd_curr) if (eur_curr is not None and usd_curr and usd_curr > 0) else None

    col_fx1.metric("EUR / CZK", f"{eur_curr:.2f} Kč" if eur_curr is not None else "N/A", delta=f"{eur_delta:+.2f} Kč", delta_color="off", help="Počet Kč za 1 Euro")
    col_fx2.metric("USD / CZK", f"{usd_curr:.2f} Kč" if usd_curr is not None else "N/A", delta=f"{usd_delta:+.2f} Kč", delta_color="off", help="Počet Kč za 1 Americký dolar")
    col_fx3.metric("Křížový poměr EUR / USD", f"{cross_eurusd:.3f} $" if cross_eurusd is not None else "N/A", help="Tržní hodnota 1 EUR v amerických dolarech")
    min_eur = df["eur_czk"].min() if "eur_czk" in df.columns else None
    max_eur = df["eur_czk"].max() if "eur_czk" in df.columns else None
    col_fx4.metric("Rozpětí EUR/CZK (Min – Max)", f"{min_eur:.2f} – {max_eur:.2f} Kč" if (min_eur and max_eur) else "N/A")

    fig_fx = build_fx_chart(df)
    render_plotly_chart(fig_fx, key="chart_fx")

    st.info(
        "💡 **Měnový vývoj:** Česká národní banka uplatňovala v letech 2013–2017 tzv. kurzový závazek (umělé oslabení koruny nad 27,00 Kč/EUR). "
        "V roce 2022 ČNB intervenovala na devizovém trhu prodejem devizových rezerv k zabránění nadměrného oslabení koruny."
    )

# -----------------------------------------------------------------------------
# TAB 6: VEŘEJNÝ DLUH A DEFICIT SR
# -----------------------------------------------------------------------------
with tab_debt:
    st.markdown('<div class="section-header">Fiskální politika: Veřejný dluh a deficit státního rozpočtu</div>', unsafe_allow_html=True)
    st.caption("Vývoj zadlužení sektoru vládních institucí vůči HDP (Maastrichtská kritéria) a saldo státního rozpočtu České republiky.")

    col_d1, col_d2, col_d3, col_d4 = st.columns(4)
    debt_gdp_curr = last_row.get("public_debt_gdp_pct")
    debt_gdp_prev = prev_row.get("public_debt_gdp_pct")
    debt_gdp_delta = (debt_gdp_curr - debt_gdp_prev) if (debt_gdp_curr is not None and debt_gdp_prev is not None) else 0.0

    debt_nom_curr = last_row.get("public_debt_czk_bn")
    deficit_curr = last_row.get("budget_deficit_czk_bn")
    maastricht_buffer = (60.0 - debt_gdp_curr) if debt_gdp_curr is not None else 0.0

    col_d1.metric("Veřejný dluh k HDP", f"{debt_gdp_curr:.1f} %" if debt_gdp_curr is not None else "N/A", delta=f"{debt_gdp_delta:+.1f} p.b.", delta_color="inverse", help="Maastrichtský strop je 60.0 % HDP")
    col_d2.metric("Nominální veřejný dluh", f"{debt_nom_curr:,.0f} mld. Kč".replace(",", " ") if debt_nom_curr is not None else "N/A", help="Celkový konsolidovaný dluh vládního sektoru")
    col_d3.metric("Kvartální saldo rozpočtu", f"{deficit_curr:+.1f} mld. Kč" if deficit_curr is not None else "N/A", delta="Schodek" if (deficit_curr and deficit_curr < 0) else "Přebytek", delta_color="off")
    col_d4.metric("Rezerva do limitu 60 % HDP", f"{maastricht_buffer:+.1f} p.b.", delta="Bezpečná zóna", delta_color="normal", help="Rozdíl mezi maastrichtským limitem a reálným dluhem ČR")

    fig_debt, fig_def = build_debt_charts(df)
    
    st.subheader("1. Vývoj vládního dluhu k HDP (% HDP)")
    render_plotly_chart(fig_debt, key="chart_debt_gdp")

    st.subheader("2. Saldo hospodaření státního rozpočtu (mld. CZK)")
    render_plotly_chart(fig_def, key="chart_deficit")

    st.info(
        "💡 **Maastrichtská fiskální kritéria:** Limit pro bezpečné zadlužení státu je stanoven na **60 % HDP**. "
        "Česká republika se pohybuje kolem 44 % HDP a řadí se tak dlouhodobě k nejméně zadluženým zemím Evropské unie "
        "(průměrné zadlužení Eurozóny dosahuje zhruba 88 % HDP)."
    )

# -----------------------------------------------------------------------------
# TAB 7: CZ VÝNOSOVÁ KŘIVKA (CZGB & IRS)
# -----------------------------------------------------------------------------
with tab_cz_curve:
    st.markdown('<div class="section-header">Výnosová křivka ČR: Státní dluhopisy (CZGB 1–15Y) a Úrokové swapy (IRS)</div>', unsafe_allow_html=True)
    st.caption("Časová struktura výnosů státních dluhopisů České republiky (CZGB) a mezibankovních úrokových swapů (CZK IRS). Křivka zachycuje tržní ocenění ceny peněz pro různé splatnosti od 1 do 15 let.")

    col_yc1, col_yc2, col_yc3, col_yc4 = st.columns(4)
    y10_curr = last_row.get("czgb_10y")
    y10_prev = prev_row.get("czgb_10y")
    y10_delta = (y10_curr - y10_prev) if (y10_curr is not None and y10_prev is not None) else 0.0

    y2_curr = last_row.get("czgb_2y")
    spread_curr = last_row.get("czgb_spread_10y_2y")
    spread_bps = (spread_curr * 100.0) if spread_curr is not None else 0.0

    irs10_curr = last_row.get("irs_10y")
    asw_10y_bps = ((irs10_curr - y10_curr) * 100.0) if (irs10_curr is not None and y10_curr is not None) else 0.0

    col_yc1.metric(
        "CZGB 10Y (Benchmark)",
        f"{y10_curr:.2f} %" if y10_curr is not None else "N/A",
        delta=f"{y10_delta * 100:+.0f} bps" if len(df) > 1 else "Aktuální",
        help="Výnos 10letého referenčního státního dluhopisu ČR (Eurostat Maastricht criterion)"
    )
    col_yc2.metric(
        "CZGB 2Y (Krátký konec)",
        f"{y2_curr:.2f} %" if y2_curr is not None else "N/A",
        help="Výnos 2letého bondu – silně navázaný na repo sazbu ČNB a měnověpolitická očekávání"
    )

    if spread_bps > 15:
        curve_status = "Normální (rostoucí)"
        curve_delta_color = "normal"
    elif spread_bps < -15:
        curve_status = "Inverzní křivka ⚠️"
        curve_delta_color = "inverse"
    else:
        curve_status = "Plochá křivka"
        curve_delta_color = "off"

    col_yc3.metric(
        "Sklon křivky (10Y − 2Y)",
        f"{spread_bps:+.0f} bps",
        delta=curve_status,
        delta_color=curve_delta_color,
        help="Záporný spread (inverze) historicky signalizuje budoucí pokles sazeb nebo ekonomické ochlazení"
    )
    col_yc4.metric(
        "CZK IRS 10Y (Swapová sazba)",
        f"{irs10_curr:.2f} %" if irs10_curr is not None else "N/A",
        delta=f"ASW: +{asw_10y_bps:.0f} bps",
        delta_color="off",
        help="Sazba úrokového swapu a Asset Swap Spread (ASW = IRS − CZGB) vůči státnímu bondu"
    )

    st.markdown("---")

    col_ctrl1, col_ctrl2 = st.columns([1, 1])
    with col_ctrl1:
        st.markdown("**Volba zobrazovaných křivek a prvků:**")
        chk_col1, chk_col2 = st.columns(2)
        chk_czgb = chk_col1.checkbox("Státní dluhopisy (CZGB 1–15Y)", value=True, key="chk_yc_czgb")
        chk_irs = chk_col2.checkbox("Úrokové swapy (CZK IRS 1–15Y)", value=True, key="chk_yc_irs")
        chk_show_vals = st.checkbox("Zobrazit hodnoty u bodů v grafu", value=True, key="chk_yc_show_vals")

    with col_ctrl2:
        st.markdown("**Porovnání výnosové křivky v čase:**")
        yc_compare_choice = st.selectbox(
            "Zvolte srovnávací referenční křivku:",
            options=["Bez srovnání", "Před 1 měsícem", "Před 6 měsíci", "Před 1 rokem", "Inverze / Vrchol sazeb (Polovina 2022)"],
            index=3,
            key="yc_compare_select"
        )

    compare_row = None
    compare_label = yc_compare_choice
    if yc_compare_choice == "Před 1 měsícem" and len(df) > 1:
        compare_row = df.iloc[-2]
    elif yc_compare_choice == "Před 6 měsíci" and len(df) > 6:
        compare_row = df.iloc[-7]
    elif yc_compare_choice == "Před 1 rokem" and len(df) > 12:
        compare_row = df.iloc[-13]
    elif yc_compare_choice == "Inverze / Vrchol sazeb (Polovina 2022)":
        df_inv = df_raw[df_raw["date"].dt.year == 2022]
        if not df_inv.empty:
            compare_row = df_inv.iloc[-1]
            compare_label = "Červenec 2022 (Inverze)"

    st.subheader("1. Tvar výnosové křivky (Term Structure 1Y–15Y)")
    fig_yc_snapshot = build_yield_curve_snapshot(
        df_row=last_row,
        compare_row=compare_row,
        show_czgb=chk_czgb,
        show_irs=chk_irs,
        compare_label=compare_label,
        show_values=chk_show_vals
    )
    render_plotly_chart(fig_yc_snapshot, key="chart_yc_snapshot")

    tenor_list = ["1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "15Y"]
    tenor_raw_keys = ["1y", "2y", "3y", "5y", "7y", "10y", "15y"]
    table_rows = []
    for t_lbl, t_key in zip(tenor_list, tenor_raw_keys):
        c_val = last_row.get(f"czgb_{t_key}")
        i_val = last_row.get(f"irs_{t_key}")
        c_prev = prev_row.get(f"czgb_{t_key}")
        c_delta = ((c_val - c_prev) * 100.0) if (c_val is not None and c_prev is not None) else None
        asw = ((i_val - c_val) * 100.0) if (i_val is not None and c_val is not None) else None
        row_dict = {
            "Splatnost (Tenor)": t_lbl,
            "CZGB Výnos (% p.a.)": f"{c_val:.2f} %" if c_val is not None else "N/A",
            "CZK IRS Sazba (% p.a.)": f"{i_val:.2f} %" if i_val is not None else "N/A",
            "Asset Swap Spread (bps)": f"+{asw:.0f} bps" if asw is not None else "N/A",
            "Změna MoM (bps)": f"{c_delta:+.0f} bps" if c_delta is not None else "–"
        }
        if compare_row is not None:
            cmp_val = compare_row.get(f"czgb_{t_key}")
            row_dict[f"CZGB ({compare_label})"] = f"{cmp_val:.2f} %" if cmp_val is not None else "N/A"
        table_rows.append(row_dict)
    df_term_sheet = pd.DataFrame(table_rows)

    with st.expander("Zobrazit detailní tabulku splatností (Term Sheet: 1Y až 15Y)", expanded=False):
        render_dataframe(df_term_sheet)

    st.markdown("---")

    col_g_hist1, col_g_hist2 = st.columns(2)
    with col_g_hist1:
        st.subheader("2. Vývoj benchmarkových výnosů v čase")
        fig_hist = build_yield_history_chart(df, show_irs_history=chk_irs)
        render_plotly_chart(fig_hist, key="chart_yc_history")

    with col_g_hist2:
        st.subheader("3. Sklon křivky (10Y − 2Y) & Inverze")
        fig_spread = build_curve_spread_chart(df)
        render_plotly_chart(fig_spread, key="chart_yc_spread")

    st.info(
        "💡 **Co je výnosová křivka a její inverze:**\n\n"
        "- **Normální křivka:** Dlouhodobé výnosy (10Y, 15Y) jsou vyšší než krátkodobé z důvodu termínové a inflační prémie.\n"
        "- **Inverzní křivka (Inverted Yield Curve):** Krátkodobé sazby převyšují dlouhodobé (např. 2022–2023, kdy repo sazba dosáhla 7 %, zatímco 10Y bond byl pod 5 %). "
        "Inverze signalizuje, že trh očekává budoucí pokles inflace a uvolňování měnové politiky centrální bankou.\n"
        "- **Úrokové swapy (IRS):** Swapová křivka odráží cenu peněz na mezibankovním trhu. "
        "5Y a 10Y CZK IRS jsou klíčovými benchmarky, které komerční banky v ČR používají k tvorbě cen pro fixace hypotečních úvěrů a firemních půjček."
    )

# -----------------------------------------------------------------------------
# TAB 8: US VÝNOSOVÁ KŘIVKA (U.S. TREASURY 1M–30Y)
# -----------------------------------------------------------------------------
with tab_us_curve:
    st.markdown('<div class="section-header">Výnosová křivka USA: Vládní dluhopisy (U.S. Treasury Par Yield Curve: 1M–30Y)</div>', unsafe_allow_html=True)
    st.caption("Časová struktura výnosů amerických státních dluhopisů z oficiálního REST XML API U.S. Department of the Treasury. Klíčový globální benchmark pro ocenění bezrizikové sazby (Risk-Free Rate) a nejspolehlivější předstihový indikátor recese v moderní historii.")

    col_us1, col_us2, col_us3, col_us4 = st.columns(4)
    us10_prev = prev_row.get("us_10y")
    us10_delta_bps = ((us10_curr - us10_prev) * 100.0) if (us10_curr is not None and us10_prev is not None) else 0.0

    us2_prev = prev_row.get("us_2y")
    us2_delta_bps = ((us2_curr - us2_prev) * 100.0) if (us2_curr is not None and us2_prev is not None) else 0.0

    us_spread_bps = (us_spread_curr * 100.0) if us_spread_curr is not None else 0.0

    col_us1.metric(
        "US 10Y (Benchmark)",
        f"{us10_curr:.2f} %" if us10_curr is not None else "N/A",
        delta=f"{us10_delta_bps:+.0f} bps" if len(df) > 1 else "Aktuální",
        help="Výnos 10letého referenčního státního dluhopisu USA (10-Year Treasury Note) – globální měřítko ceny kapitálu"
    )
    col_us2.metric(
        "US 2Y (Krátký konec)",
        f"{us2_curr:.2f} %" if us2_curr is not None else "N/A",
        delta=f"{us2_delta_bps:+.0f} bps" if len(df) > 1 else "Aktuální",
        help="Výnos 2letého bondu vlády USA – silně citlivý na budoucí nastavení sazeb Federálního rezervního systému (Fed)"
    )

    if us_spread_bps > 15:
        us_status = "Normální (rostoucí)"
        us_delta_col = "normal"
    elif us_spread_bps < -10:
        us_status = "Inverzní křivka ⚠️"
        us_delta_col = "inverse"
    else:
        us_status = "Plochá křivka"
        us_delta_col = "off"

    col_us3.metric(
        "Sklon křivky (10Y − 2Y)",
        f"{us_spread_bps:+.0f} bps",
        delta=us_status,
        delta_color=us_delta_col,
        help="Záporný spread (inverze) americké křivky spolehlivě předpověděl každou americkou recesi od roku 1955"
    )

    us30_curr = last_row.get("us_30y")
    col_us4.metric(
        "US 30Y (Long Bond)",
        f"{us30_curr:.2f} %" if us30_curr is not None else "N/A",
        delta=f"3M Bill: {us3m_curr:.2f} %" if us3m_curr is not None else "T-Bill",
        delta_color="off",
        help="Výnos 30letého dlouhodobého vládního dluhopisu USA a výnos 3měsíční pokladniční poukázky (Fed proxy)"
    )

    st.markdown("---")

    col_u_ctrl1, col_u_ctrl2 = st.columns([1, 1])
    with col_u_ctrl1:
        st.markdown("**Volba zobrazovaných prvků a srovnání:**")
        chk_us_col1, chk_us_col2 = st.columns(2)
        chk_us_vals = chk_us_col1.checkbox("Zobrazit hodnoty u bodů (% p.a.)", value=True, key="chk_us_vals")
        chk_us_czgb = chk_us_col2.checkbox("Překrýt křivku ČR (CZGB)", value=False, key="chk_us_czgb", help="Zobrazí české státní dluhopisy (CZGB 1–15Y) na stejném grafu pro přímé srovnání")

    with col_u_ctrl2:
        st.markdown("**Porovnání US výnosové křivky v čase:**")
        us_compare_choice = st.selectbox(
            "Zvolte srovnávací referenční období:",
            options=["Bez srovnání", "Před 1 měsícem", "Před 6 měsíci", "Před 1 rokem", "Vrchol inverze (Říjen 2023 - 5.0% 10Y)"],
            index=3,
            key="us_compare_select"
        )

    compare_row_us = None
    compare_label_us = us_compare_choice
    if us_compare_choice == "Před 1 měsícem" and len(df) > 1:
        compare_row_us = df.iloc[-2]
    elif us_compare_choice == "Před 6 měsíci" and len(df) > 6:
        compare_row_us = df.iloc[-7]
    elif us_compare_choice == "Před 1 rokem" and len(df) > 12:
        compare_row_us = df.iloc[-13]
    elif us_compare_choice == "Vrchol inverze (Říjen 2023 - 5.0% 10Y)":
        df_inv_us = df_raw[(df_raw["date"].dt.year == 2023) & (df_raw["date"].dt.month == 10)]
        if not df_inv_us.empty:
            compare_row_us = df_inv_us.iloc[-1]
            compare_label_us = "Říjen 2023 (Vrchol sazeb)"

    st.subheader("1. Tvar výnosové křivky USA (Term Structure: 1M až 30Y)")
    fig_us_snapshot = build_us_yield_curve_snapshot(
        df_row=last_row,
        compare_row=compare_row_us,
        show_czgb=chk_us_czgb,
        compare_label=compare_label_us,
        show_values=chk_us_vals
    )
    render_plotly_chart(fig_us_snapshot, key="chart_us_snapshot")

    us_tenor_keys = ["1m", "3m", "6m", "1y", "2y", "3y", "5y", "7y", "10y", "20y", "30y"]
    us_tenor_labels = ["1M", "3M", "6M", "1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y"]
    us_table_rows = []
    for t_lbl, t_key in zip(us_tenor_labels, us_tenor_keys):
        u_val = last_row.get(f"us_{t_key}")
        u_prev = prev_row.get(f"us_{t_key}")
        u_delta = ((u_val - u_prev) * 100.0) if (u_val is not None and u_prev is not None) else None
        cz_match = last_row.get(f"czgb_{t_key.lower()}")
        spread_cz_us = ((cz_match - u_val) * 100.0) if (cz_match is not None and u_val is not None) else None

        row_dict = {
            "Splatnost (Tenor)": t_lbl,
            "US Treasury Výnos (% p.a.)": f"{u_val:.2f} %" if u_val is not None else "N/A",
            "Změna MoM (bps)": f"{u_delta:+.0f} bps" if u_delta is not None else "–",
            "CZGB Ekvivalent (% p.a.)": f"{cz_match:.2f} %" if cz_match is not None else "–",
            "Rozpětí CZGB − US (bps)": f"{spread_cz_us:+.0f} bps" if spread_cz_us is not None else "–"
        }
        if compare_row_us is not None:
            cmp_u_val = compare_row_us.get(f"us_{t_key}")
            row_dict[f"US ({compare_label_us})"] = f"{cmp_u_val:.2f} %" if cmp_u_val is not None else "N/A"
        us_table_rows.append(row_dict)
    df_us_term_sheet = pd.DataFrame(us_table_rows)

    with st.expander("Zobrazit detailní tabulku splatností US Treasuries (1M až 30Y)", expanded=False):
        render_dataframe(df_us_term_sheet)

    st.markdown("---")

    col_us_g1, col_us_g2 = st.columns(2)
    with col_us_g1:
        st.subheader("2. Časový vývoj benchmarkových výnosů v USA")
        fig_us_hist = build_us_yield_history_chart(df)
        render_plotly_chart(fig_us_hist, key="chart_us_history")

    with col_us_g2:
        st.subheader("3. Sklon americké křivky (10Y − 2Y) & Indikátor recese")
        fig_us_spread = build_us_curve_spread_chart(df)
        render_plotly_chart(fig_us_spread, key="chart_us_spread")

    st.info(
        "💡 **Specifika výnosové křivky Spojených států amerických:**\n\n"
        "- **Globální bezriziková sazba (Risk-Free Rate):** Americké státní dluhopisy (US Treasuries) představují základní referenční aktivum pro oceňování akcií, korporátních dluhopisů, derivátů a nemovitostí po celém světě.\n"
        "- **Inverzní výnosová křivka v USA (10Y − 2Y & 10Y − 3M):** Každou americkou hospodářskou recesi v moderní historii (od roku 1955) předcházela inverze výnosové křivky. Během agresivního utahování měnové politiky Fedu v letech 2022–2023 se křivka propadla do nejhlubší inverze za více než 40 let (přes −100 bps).\n"
        "- **Vliv Federálního rezervního systému:** Krátký konec křivky (1M až 2Y) přímo odráží aktuální a očekávanou sazbu Federal Funds Rate (FFR), zatímco dlouhý konec (10Y až 30Y) odráží dlouhodobá inflační očekávání a hospodářský růst USA."
    )

# -----------------------------------------------------------------------------
# TAB 9: SROVNÁNÍ CZ VS. US
# -----------------------------------------------------------------------------
with tab_cz_us:
    st.markdown('<div class="section-header">Mezinárodní srovnání: Česká republika vs. Spojené státy</div>', unsafe_allow_html=True)
    st.caption("Přímé analytické porovnání měnových politik, referenčních dluhopisových trhů a úrokového diferenciálu mezi Českou národní bankou a americkým Fedem.")

    col_cmp1, col_cmp2, col_cmp3, col_cmp4 = st.columns(4)
    cz_us_10y_spread_bps = ((czgb10_curr - us10_curr) * 100.0) if (czgb10_curr is not None and us10_curr is not None) else 0.0
    cz_us_2y_spread_bps = ((czgb2_curr - us2_curr) * 100.0) if (czgb2_curr is not None and us2_curr is not None) else 0.0

    col_cmp1.metric(
        "Spread 10Y (CZGB − US)",
        f"{cz_us_10y_spread_bps:+.0f} bps",
        delta="Prémie ČR" if cz_us_10y_spread_bps > 0 else "Prémie USA",
        delta_color="off",
        help="Rozdíl mezi 10letým výnosem v ČR a USA. Kladná hodnota znamená vyšší výnos českých dluhopisů."
    )
    col_cmp2.metric(
        "Spread 2Y (CZGB − US)",
        f"{cz_us_2y_spread_bps:+.0f} bps",
        help="Rozdíl na krátkém konci křivky (odráží očekávání sazeb ČNB vs. Fed)"
    )
    col_cmp3.metric(
        "Sazby centrálních bank",
        f"ČNB {repo_curr:.2f} %",
        delta="Fed proxy: " + (f"{us3m_curr:.2f} %" if us3m_curr is not None else "N/A"),
        delta_color="off",
        help="Srovnání základní repo sazby ČNB a amerického peněžního trhu"
    )
    col_cmp4.metric(
        "Měnový kurz USD/CZK",
        f"{usd_curr:.2f} Kč" if usd_curr is not None else "N/A",
        delta=f"EUR/USD: {cross_eurusd:.3f} $" if cross_eurusd is not None else "N/A",
        delta_color="off"
    )

    st.markdown("---")

    col_cmp_c1, col_cmp_c2 = st.columns(2)
    with col_cmp_c1:
        st.subheader("1. Překrytí výnosových křivek: CZGB (ČR) vs. U.S. Treasury (USA)")
        fig_cross_snap = build_us_yield_curve_snapshot(
            df_row=last_row,
            compare_row=None,
            show_czgb=True,
            show_values=True
        )
        render_plotly_chart(fig_cross_snap, key="chart_cmp_snapshot")

    with col_cmp_c2:
        st.subheader("2. Vývoj výnosového spreadu: CZGB 10Y minus US 10Y v čase")
        fig_spread_cz_us = build_cz_vs_us_spread_chart(df)
        render_plotly_chart(fig_spread_cz_us, key="chart_cmp_spread")

    # Tabulka srovnání klíčových parametrů obou ekonomik
    st.subheader("3. Souhrnné porovnání makroekonomických parametrů")
    comp_summary_data = [
        {"Parametr": "Základní sazba centrální banky", "Česká republika (ČNB)": f"{repo_curr:.2f} % (2T Repo)", "Spojené státy (Fed)": f"{us3m_curr:.2f} % (3M T-Bill proxy)"},
        {"Parametr": "Meziroční inflace (CPI)", "Česká republika (ČNB)": f"{cpi_curr:.1f} %", "Spojené státy (Fed)": "2.4 – 2.8 % (PCE / CPI)"},
        {"Parametr": "Výnos 10Y státního dluhopisu", "Česká republika (ČNB)": f"{czgb10_curr:.2f} %", "Spojené státy (Fed)": f"{us10_curr:.2f} %"},
        {"Parametr": "Výnos 2Y státního dluhopisu", "Česká republika (ČNB)": f"{czgb2_curr:.2f} %", "Spojené státy (Fed)": f"{us2_curr:.2f} %"},
        {"Parametr": "Sklon křivky (10Y − 2Y)", "Česká republika (ČNB)": f"{cz_spread_curr * 100:+.0f} bps", "Spojené státy (Fed)": f"{us_spread_curr * 100:+.0f} bps"},
        {"Parametr": "Dluh vládního sektoru k HDP", "Česká republika (ČNB)": f"{debt_pct_curr:.1f} % HDP", "Spojené státy (Fed)": "~122 % HDP"},
    ]
    df_comp_summary = pd.DataFrame(comp_summary_data)
    render_dataframe(df_comp_summary)

# -----------------------------------------------------------------------------
# TAB 10: VŠECHNY GRAFY POHROMADĚ
# -----------------------------------------------------------------------------
with tab_all:
    st.markdown('<div class="section-header">Souhrnný přehled (Všechny makroekonomické grafy)</div>', unsafe_allow_html=True)
    st.caption("Kompletní makroekonomický obrázek pro rychlé zhodnocení souvislostí mezi sazbami, inflací, hospodářským růstem, trhem práce, kurzy a dluhopisovými trhy ČR i USA.")

    st.subheader("1. Měnová politika & Inflace (ČNB vs. PRIBOR vs. CPI)")
    fig_combo = build_rates_vs_inflation_chart(df, selected_indicators)
    render_plotly_chart(fig_combo, key="chart_all_combo")

    st.markdown("---")
    st.subheader("2. Hrubý domácí produkt (Nominální objem a reálný růst)")
    render_plotly_chart(fig_gdp, key="chart_all_gdp")

    st.markdown("---")
    st.subheader("3. Trh práce (Míra nezaměstnanosti)")
    render_plotly_chart(fig_une, key="chart_all_une")

    st.markdown("---")
    st.subheader("4. Měnové kurzy (EUR/CZK a USD/CZK)")
    render_plotly_chart(fig_fx, key="chart_all_fx")

    st.markdown("---")
    st.subheader("5. Veřejný dluh k HDP (%)")
    render_plotly_chart(fig_debt, key="chart_all_debt")

    st.markdown("---")
    st.subheader("6. Výnosová křivka ČR (CZGB 1–15Y vs. IRS)")
    fig_all_yc = build_yield_curve_snapshot(df_row=last_row, compare_row=None, show_czgb=True, show_irs=True)
    render_plotly_chart(fig_all_yc, key="chart_all_yc_snapshot")

    st.markdown("---")
    st.subheader("7. Výnosová křivka USA (U.S. Treasury 1M–30Y)")
    fig_all_us_yc = build_us_yield_curve_snapshot(df_row=last_row, compare_row=None, show_czgb=False, show_values=True)
    render_plotly_chart(fig_all_us_yc, key="chart_all_us_yc")

    st.markdown("---")
    st.subheader("8. Sklon americké křivky (Spread US 10Y − 2Y v bps)")
    fig_all_us_spread = build_us_curve_spread_chart(df)
    render_plotly_chart(fig_all_us_spread, key="chart_all_us_spread")

    st.markdown("---")
    st.subheader("9. Mezinárodní spread (CZGB 10Y minus US 10Y v bps)")
    fig_all_diff = build_cz_vs_us_spread_chart(df)
    render_plotly_chart(fig_all_diff, key="chart_all_spread_diff")

# -----------------------------------------------------------------------------
# TAB 11: DATA A EXPORT (CSV)
# -----------------------------------------------------------------------------
with tab_table:
    st.markdown('<div class="section-header">Přehled dat a export do CSV</div>', unsafe_allow_html=True)

    col_table_top1, col_table_top2 = st.columns([3, 1])

    with col_table_top1:
        st.caption(f"Filtrovaná data obsahují **{len(df_export_cz)}** časových záznamů a **{len(cols_to_display) - 1}** vybraných indikátorů.")

    with col_table_top2:
        csv_buffer = io.StringIO()
        df_export_cz.to_csv(csv_buffer, index=False, sep=";", encoding="utf-8")
        csv_bytes = ("\ufeff" + csv_buffer.getvalue()).encode("utf-8")

        st.download_button(
            label="Stáhnout data (CSV pro Excel)",
            data=csv_bytes,
            file_name=f"macro_data_{frequency_code.lower()}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )

    render_dataframe(df_export_cz)


# =============================================================================
# 11. METODIKA A POPIS INDIKÁTORŮ
# =============================================================================

st.markdown("---")
with st.expander("📚 Metodické vysvětlivky a zdroje dat"):
    st.markdown(
        """
        ### Oficiální zdroje dat
        1. **Česká národní banka (ČNB)**:
           - *Otevřená REST API*: Denní fixace referenčních sazeb peněžního trhu **PRIBOR** (1M, 3M, 6M) a měnových kurzů (**EUR/CZK**, **USD/CZK**).
           - *Měnověpolitické nástroje*: Oficiální historie nastavení klíčových sazeb – **2T repo sazba**, **diskontní sazba** (depozitní facilita) a **lombardní sazba** (zápůjční facilita).
        2. **Eurostat & Český statistický úřad (ČSÚ)**:
           - *Harmonizovaný index spotřebitelských cen (HICP / CPI)*: Meziroční míra inflace za ČR v %.
           - *Čtvrtletní národní účty (namq_10_gdp)*: Reálný meziroční růst HDP v řetězených objemech a objem nominálního HDP v běžných cenách.
           - *Statistika trhu práce (une_rt_m)*: Měsíční sezónně očištěná míra nezaměstnanosti dle definice ILO.
           - *Vládní finanční statistika (gov_10q_ggdebt)*: Konsolidovaný dluh sektoru vládních institucí v % HDP a absolutním vyjádření.
        3. **Federal Reserve Bank of St. Louis (FRED)**:
           - Volitelný záložní zdroj agregovaných mezinárodních časových řad pro ČR (při zadání vlastního API klíče).

        ### Odolnost aplikace (Resilience & Caching)
        - Všechna data jsou cachována na úrovni aplikačního serveru pomocí Streamlit dekorátoru `@st.cache_data(ttl=3600)`.
        - V případě výpadku externích REST služeb nebo nedostupnosti sítě aplikace automaticky aktivuje **realistický historický model (2015–současnost)**, který zachovává skutečné ekonomické milníky (konec kurzového závazku, covidové dno, inflační vlnu 2022–2023 s vrcholem sazeb na 7.00 %, měnové intervence i fiskální schodky).
        """
    )
