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
    /* Hlavní kontejner a písmo */
    .main .block-container {
        padding-top: 1.8rem;
        padding-bottom: 2.5rem;
    }
    
    /* Vzhled metrických KPI karet */
    div[data-testid="stMetric"] {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 14px 18px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        border-color: #cbd5e1;
    }
    div[data-testid="stMetricLabel"] p {
        font-size: 0.88rem !important;
        font-weight: 600 !important;
        color: #475569 !important;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.75rem !important;
        font-weight: 700 !important;
        color: #0f172a !important;
    }
    
    /* Status tagy */
    .status-badge {
        display: inline-block;
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-bottom: 15px;
    }
    .status-live {
        background-color: #dcfce7;
        color: #166534;
        border: 1px solid #86efac;
    }
    .status-partial {
        background-color: #fef9c3;
        color: #854d0e;
        border: 1px solid #fde047;
    }
    .status-fallback {
        background-color: #ffedd5;
        color: #9a3412;
        border: 1px solid #fdba74;
    }
    
    /* Záhlaví grafů a sekcí */
    .section-header {
        font-size: 1.25rem;
        font-weight: 700;
        color: #1e293b;
        margin-top: 0.8rem;
        margin-bottom: 0.6rem;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    /* ========================================= */
    /* Dvouřadé responsivní záložky (Tabs)       */
    /* ========================================= */
    div[data-baseweb="tab-list"] {
        display: flex !important;
        flex-wrap: wrap !important;
        gap: 8px 10px !important;
        border-bottom: 2px solid #e2e8f0 !important;
        padding-bottom: 8px !important;
        margin-bottom: 1.2rem !important;
        width: 100% !important;
    }

    /* Skrytí defaultní streamlitské podtrhávací lišty */
    div[data-baseweb="tab-highlight"],
    div[data-baseweb="tab-border"] {
        display: none !important;
    }

    /* Vzhled neaktivních oušek (kartiček) */
    button[data-baseweb="tab"] {
        background-color: #f1f5f9 !important;
        color: #334155 !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px !important;
        padding: 8px 16px !important;
        font-size: 0.92rem !important;
        font-weight: 600 !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        white-space: nowrap !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04) !important;
        cursor: pointer !important;
        height: auto !important;
    }

    button[data-baseweb="tab"]:hover {
        background-color: #e2e8f0 !important;
        color: #0f172a !important;
        border-color: #94a3b8 !important;
        transform: translateY(-1px) !important;
    }

    /* ========================================= */
    /* Profesionální Sidebar a Ovládací prvky    */
    /* (Styl finančních terminálů / Stock Analysis)*/
    /* ========================================= */
    
    /* Kontejner postranního panelu */
    section[data-testid="stSidebar"] {
        background-color: #f8fafc !important;
        border-right: 1px solid #e2e8f0 !important;
    }

    section[data-testid="stSidebar"] .block-container {
        padding-top: 1.2rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }

    /* Karta záhlaví sidebaru (Brand Header) */
    .sidebar-brand-card {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        border-radius: 10px;
        padding: 13px 15px;
        color: #ffffff;
        margin-bottom: 18px;
        box-shadow: 0 4px 12px -2px rgba(15, 23, 42, 0.25);
        border: 1px solid #334155;
    }
    .sidebar-brand-top {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 5px;
    }
    .sidebar-brand-badge {
        background: #2563eb;
        color: #ffffff;
        font-size: 0.70rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        padding: 2px 7px;
        border-radius: 4px;
        text-transform: uppercase;
    }
    .sidebar-brand-version {
        font-size: 0.70rem;
        color: #94a3b8;
        font-weight: 600;
        letter-spacing: 0.05em;
    }
    .sidebar-brand-title {
        font-size: 1.10rem;
        font-weight: 700;
        color: #ffffff;
        margin: 0;
        letter-spacing: -0.01em;
    }
    .sidebar-brand-sub {
        font-size: 0.76rem;
        color: #94a3b8;
        margin-top: 3px;
    }

    /* Nadpisy sekcí s odznaky (Section headers) */
    .sidebar-section-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-top: 14px;
        margin-bottom: 8px;
        padding-bottom: 2px;
    }
    .sidebar-section-title {
        font-size: 0.84rem;
        font-weight: 700;
        color: #1e293b;
        letter-spacing: 0.02em;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .sidebar-section-badge {
        font-size: 0.68rem;
        font-weight: 700;
        color: #475569;
        background: #e2e8f0;
        border: 1px solid #cbd5e1;
        padding: 1px 6px;
        border-radius: 4px;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }

    /* Segmented Control (Stock Analysis styl tlačítkového přepínače) */
    div[data-testid="stSegmentedControl"] {
        background-color: #f1f5f9 !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 9px !important;
        padding: 3px !important;
        width: 100% !important;
        box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.04) !important;
    }
    div[data-testid="stSegmentedControl"] > div {
        display: flex !important;
        gap: 3px !important;
        width: 100% !important;
    }
    div[data-testid="stSegmentedControl"] button {
        flex: 1 1 0 !important;
        min-width: 0 !important;
        border-radius: 6px !important;
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        padding: 6px 4px !important;
        border: none !important;
        background: transparent !important;
        color: #475569 !important;
        transition: all 0.15s ease !important;
        box-shadow: none !important;
        white-space: nowrap !important;
        text-align: center !important;
        justify-content: center !important;
    }
    div[data-testid="stSegmentedControl"] button:hover {
        background-color: rgba(255, 255, 255, 0.7) !important;
        color: #0f172a !important;
    }
    div[data-testid="stSegmentedControl"] button[aria-selected="true"],
    div[data-testid="stSegmentedControl"] button[aria-checked="true"],
    div[data-testid="stSegmentedControl"] button[data-selected="true"] {
        background: linear-gradient(135deg, #1e40af 0%, #1d4ed8 100%) !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        box-shadow: 0 2px 4px rgba(29, 78, 216, 0.35) !important;
    }
    div[data-testid="stSegmentedControl"] button[aria-selected="true"] p,
    div[data-testid="stSegmentedControl"] button[aria-checked="true"] p,
    div[data-testid="stSegmentedControl"] button[data-selected="true"] p {
        color: #ffffff !important;
        font-weight: 700 !important;
    }

    /* Fallback pro horizontální st.radio (převede radio na tlačítka a skryje kolečka) */
    div[data-testid="stSidebar"] div[data-testid="stRadio"] > div[role="radiogroup"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: wrap !important;
        gap: 4px !important;
        background: #f1f5f9 !important;
        padding: 3px !important;
        border-radius: 9px !important;
        border: 1px solid #cbd5e1 !important;
        width: 100% !important;
    }
    div[data-testid="stSidebar"] div[data-testid="stRadio"] > div[role="radiogroup"] > label {
        flex: 1 1 0 !important;
        min-width: 0 !important;
        background: transparent !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 6px 4px !important;
        margin: 0 !important;
        cursor: pointer !important;
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        color: #475569 !important;
        transition: all 0.15s ease !important;
        justify-content: center !important;
        text-align: center !important;
        display: flex !important;
    }
    div[data-testid="stSidebar"] div[data-testid="stRadio"] > div[role="radiogroup"] > label:hover {
        background: rgba(255, 255, 255, 0.7) !important;
        color: #0f172a !important;
    }
    div[data-testid="stSidebar"] div[data-testid="stRadio"] > div[role="radiogroup"] > label > div:first-child {
        display: none !important; /* Skryje nativní radio kolečko */
    }
    div[data-testid="stSidebar"] div[data-testid="stRadio"] > div[role="radiogroup"] > label:has(input:checked) {
        background: linear-gradient(135deg, #1e40af 0%, #1d4ed8 100%) !important;
        box-shadow: 0 2px 4px rgba(29, 78, 216, 0.35) !important;
    }
    div[data-testid="stSidebar"] div[data-testid="stRadio"] > div[role="radiogroup"] > label:has(input:checked) p,
    div[data-testid="stSidebar"] div[data-testid="stRadio"] > div[role="radiogroup"] > label:has(input:checked) span {
        color: #ffffff !important;
        font-weight: 700 !important;
    }

    /* MultiSelect tagy (Sleek chip styl) */
    div[data-testid="stMultiSelect"] span[data-baseweb="tag"] {
        background-color: #e0e7ff !important;
        border: 1px solid #c7d2fe !important;
        border-radius: 6px !important;
        font-size: 0.80rem !important;
        font-weight: 600 !important;
        color: #1e3a8a !important;
    }
    div[data-testid="stMultiSelect"] span[data-baseweb="tag"] span {
        color: #1e3a8a !important;
    }

    /* Akční tlačítka v sidebaru */
    div[data-testid="stSidebar"] button[kind="secondary"] {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        color: #1e293b !important;
        transition: all 0.15s ease !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05) !important;
    }
    div[data-testid="stSidebar"] button[kind="secondary"]:hover {
        background-color: #f1f5f9 !important;
        border-color: #94a3b8 !important;
        color: #0f172a !important;
        transform: translateY(-1px) !important;
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
    "czgb_10y", "czgb_2y", "irs_10y", "czgb_spread_10y_2y"
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
# 6. HLAVNÍ PLOCHA DASHBOARDU: ZÁHLAVÍ
# =============================================================================

st.title("🇨🇿 Český Makroekonomický Dashboard")
st.markdown(
    """
    Interaktivní monitor klíčových ukazatelů české ekonomiky: měnové politiky České národní banky (**ČNB**), 
    vývoje spotřebitelských cen (**Inflace CPI**), výkonnosti hospodářství (**HDP**), trhu práce, devizových kurzů 
    (**EUR & USD**) a vývoje **veřejného dluhu a deficitu státního rozpočtu**.
    """
)

col_badge, col_info = st.columns([1, 2])
with col_badge:
    st.markdown(
        f'<div class="status-badge {badge_class}">{status_info.get("status_badge")}</div>',
        unsafe_allow_html=True
    )
with col_info:
    freq_desc = "Měsíční frekvence (konec měsíce)" if frequency_code == "M" else "Kvartální frekvence (konec kvartálu)"
    st.caption(f"📅 Zobrazeno: **{df['date'].min().strftime('%m/%Y')} – {df['date'].max().strftime('%m/%Y')}** | Agregace: **{freq_desc}** | Záznamů: **{len(df)}**")


# =============================================================================
# 7. KPI KARTY (st.metric)
# =============================================================================

st.markdown('<div class="section-header">📌 Klíčové makroekonomické ukazatele (Aktuální stav)</div>', unsafe_allow_html=True)

kpi_cols = st.columns(4)

last_row = df.iloc[-1]
prev_row = df.iloc[-2] if len(df) > 1 else last_row

# 1. ČNB 2T Repo sazba
repo_curr = last_row.get("repo_rate")
repo_prev = prev_row.get("repo_rate")
repo_delta = (repo_curr - repo_prev) if (repo_curr is not None and repo_prev is not None) else 0.0

with kpi_cols[0]:
    st.metric(
        label="🏛️ 2T Repo sazba ČNB",
        value=f"{repo_curr:.2f} %" if repo_curr is not None else "N/A",
        delta=f"{repo_delta:+.2f} p.b." if len(df) > 1 else "Aktuální",
        delta_color="inverse",
        help="Základní úroková sazba ČNB pro 2týdenní repo operace. Spolu s diskontní a lombardní sazbou tvoří koridor měnové politiky."
    )

# 2. Inflace (CPI YoY)
cpi_curr = last_row.get("cpi_yoy")
cpi_prev = prev_row.get("cpi_yoy")
cpi_delta = (cpi_curr - cpi_prev) if (cpi_curr is not None and cpi_prev is not None) else 0.0

with kpi_cols[1]:
    st.metric(
        label="🏷️ Inflace (CPI meziročně)",
        value=f"{cpi_curr:.1f} %" if cpi_curr is not None else "N/A",
        delta=f"{cpi_delta:+.1f} p.b." if len(df) > 1 else "Aktuální",
        delta_color="inverse",
        help="Meziroční míra inflace měřená indexem spotřebitelských cen. Cíl ČNB činí 2.0 % s tolerančním pásmem ±1 p.b. (1–3 %)."
    )

# 3. Reálný růst HDP (YoY)
gdp_curr = last_row.get("gdp_growth_real")
gdp_prev = prev_row.get("gdp_growth_real")
gdp_delta = (gdp_curr - gdp_prev) if (gdp_curr is not None and gdp_prev is not None) else 0.0

with kpi_cols[2]:
    st.metric(
        label="📈 Reálný růst HDP (YoY)",
        value=f"{gdp_curr:+.1f} %" if gdp_curr is not None else "N/A",
        delta=f"{gdp_delta:+.1f} p.b." if len(df) > 1 else "Aktuální",
        delta_color="normal",
        help="Meziroční růst hrubého domácího produktu ve stálých cenách (sezónně očištěno dle Eurostatu)."
    )

# 4. Míra nezaměstnanosti
une_curr = last_row.get("unemployment_rate")
une_prev = prev_row.get("unemployment_rate")
une_delta = (une_curr - une_prev) if (une_curr is not None and une_prev is not None) else 0.0

with kpi_cols[3]:
    st.metric(
        label="👥 Míra nezaměstnanosti",
        value=f"{une_curr:.1f} %" if une_curr is not None else "N/A",
        delta=f"{une_delta:+.1f} p.b." if len(df) > 1 else "Aktuální",
        delta_color="inverse",
        help="Obecná míra nezaměstnanosti sezónně očištěná (Eurostat / ČSÚ). Česká republika si dlouhodobě udržuje nejnižší nezaměstnanost v EU."
    )

st.markdown("---")


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
# 10. ZÁLOŽKY (OUŠKA) PRO JEDNOTLIVÉ SEKCE
# =============================================================================

tab_rates, tab_inflation, tab_gdp, tab_une, tab_fx, tab_debt, tab_yield_curve, tab_all, tab_table = st.tabs([
    "🏛️ Sazby (ČNB & PRIBOR)",
    "🏷️ Inflace (CPI)",
    "📈 HDP (Růst a objem)",
    "👥 Nezaměstnanost",
    "💱 Měnové kurzy (FX)",
    "🏛️ Veřejný dluh a Deficit SR",
    "📉 Výnosová křivka (CZGB & IRS)",
    "📊 Všechny grafy",
    "📋 Data a export"
])

# -----------------------------------------------------------------------------
# TAB 1: SAZBY (ČNB & PRIBOR)
# -----------------------------------------------------------------------------
with tab_rates:
    st.markdown('<div class="section-header">🏛️ Měnová politika ČNB a mezibankovní sazby PRIBOR</div>', unsafe_allow_html=True)
    st.caption("Úrokový koridor České národní banky: 2T Repo sazba, Diskontní sazba (depozitní facilita) a Lombardní sazba (zápůjční facilita) ve srovnání s tržními sazbami PRIBOR.")
    
    col_r1, col_r2, col_r3, col_r4 = st.columns(4)
    disc_val = last_row.get("discount_rate")
    lomb_val = last_row.get("lombard_rate")
    prib3m_val = last_row.get("pribor_3m")
    
    col_r1.metric("2T Repo sazba", f"{repo_curr:.2f} %" if repo_curr else "N/A", help="Hlavní nástroj stahování likvidity")
    col_r2.metric("Diskontní sazba (dolní mez)", f"{disc_val:.2f} %" if disc_val else "N/A", help="Úročení vkladů bank přes noc u ČNB")
    col_r3.metric("Lombardní sazba (horní mez)", f"{lomb_val:.2f} %" if lomb_val else "N/A", help="Úročení zápůjček bank přes noc od ČNB")
    col_r4.metric("PRIBOR 3M", f"{prib3m_val:.2f} %" if prib3m_val else "N/A", help="Referenční tržní sazba")

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
    st.markdown('<div class="section-header">🏷️ Vývoj inflace (CPI) a reálné úrokové míry</div>', unsafe_allow_html=True)
    st.caption("Meziroční index spotřebitelských cen (HICP / CPI) vůči inflačnímu cíli ČNB (2,0 %) a vývoj reálné úrokové sazby (2T Repo − CPI).")

    col_i1, col_i2, col_i3 = st.columns(3)
    target_diff = (cpi_curr - 2.0) if cpi_curr else 0.0
    real_rate_curr = (repo_curr - cpi_curr) if (repo_curr and cpi_curr) else 0.0

    col_i1.metric("Aktuální inflace CPI", f"{cpi_curr:.1f} %" if cpi_curr else "N/A", delta=f"{cpi_delta:+.1f} p.b.", delta_color="inverse")
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
    st.markdown('<div class="section-header">📈 Hrubý domácí produkt: Reálný růst v % a nominální tvorba</div>', unsafe_allow_html=True)
    st.caption("Kvartální výkon české ekonomiky: Nominální objem HDP v miliardách Kč (sloupce, levá osa) a meziroční reálné tempo růstu (čára, pravá osa).")

    df_gdp_unique = df.drop_duplicates(subset=["quarter"] if "quarter" in df.columns else ["date"])
    last_nom_gdp = df_gdp_unique.iloc[-1].get("gdp_nominal_czk_bn") if not df_gdp_unique.empty else None
    
    col_g1, col_g2, col_g3 = st.columns(3)
    col_g1.metric("Reálný růst HDP (YoY)", f"{gdp_curr:+.1f} %" if gdp_curr else "N/A", delta=f"{gdp_delta:+.1f} p.b.")
    col_g2.metric("Kvartální nominální HDP", f"{last_nom_gdp:,.1f} mld. Kč".replace(",", " ") if last_nom_gdp else "N/A", help="Běžné ceny za poslední známý kvartál")
    annualized_nom = (last_nom_gdp * 4) if last_nom_gdp else 0.0
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
    st.markdown('<div class="section-header">👥 Trh práce: Míra nezaměstnanosti v České republice</div>', unsafe_allow_html=True)
    st.caption("Sezónně očištěná obecná míra nezaměstnanosti dle metodiky ILO / Eurostat pro věkovou skupinu 15–74 let.")

    col_u1, col_u2, col_u3, col_u4 = st.columns(4)
    avg_une_val = df["unemployment_rate"].mean() if "unemployment_rate" in df.columns else None
    min_une_val = df["unemployment_rate"].min() if "unemployment_rate" in df.columns else None
    max_une_val = df["unemployment_rate"].max() if "unemployment_rate" in df.columns else None

    col_u1.metric("Aktuální nezaměstnanost", f"{une_curr:.1f} %" if une_curr else "N/A", delta=f"{une_delta:+.1f} p.b.", delta_color="inverse")
    col_u2.metric("Dlouhodobý průměr", f"{avg_une_val:.2f} %" if avg_une_val else "N/A", help="Průměr ve zvoleném období")
    col_u3.metric("Historické minimum", f"{min_une_val:.1f} %" if min_une_val else "N/A", help="Nejnižší hodnota ve sledovaném období")
    col_u4.metric("Historické maximum", f"{max_une_val:.1f} %" if max_une_val else "N/A", help="Nejvyšší hodnota ve sledovaném období")

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
    st.markdown('<div class="section-header">💱 Měnové kurzy: Vývoj české koruny vůči EUR a USD</div>', unsafe_allow_html=True)
    st.caption("Oficiální kurzy devizového trhu České národní banky (ČNB fixing) pro měnové páry EUR/CZK a USD/CZK.")

    col_fx1, col_fx2, col_fx3, col_fx4 = st.columns(4)
    eur_curr = last_row.get("eur_czk")
    eur_prev = prev_row.get("eur_czk")
    eur_delta = (eur_curr - eur_prev) if (eur_curr and eur_prev) else 0.0

    usd_curr = last_row.get("usd_czk")
    usd_prev = prev_row.get("usd_czk")
    usd_delta = (usd_curr - usd_prev) if (usd_curr and usd_prev) else 0.0

    cross_eurusd = (eur_curr / usd_curr) if (eur_curr and usd_curr and usd_curr > 0) else None

    col_fx1.metric("EUR / CZK", f"{eur_curr:.2f} Kč" if eur_curr else "N/A", delta=f"{eur_delta:+.2f} Kč", delta_color="off", help="Počet Kč za 1 Euro")
    col_fx2.metric("USD / CZK", f"{usd_curr:.2f} Kč" if usd_curr else "N/A", delta=f"{usd_delta:+.2f} Kč", delta_color="off", help="Počet Kč za 1 Americký dolar")
    col_fx3.metric("Křížový poměr EUR / USD", f"{cross_eurusd:.3f} $" if cross_eurusd else "N/A", help="Tržní hodnota 1 EUR v amerických dolarech")
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
    st.markdown('<div class="section-header">🏛️ Fiskální politika: Veřejný dluh a deficit státního rozpočtu</div>', unsafe_allow_html=True)
    st.caption("Vývoj zadlužení sektoru vládních institucí vůči HDP (Maastrichtská kritéria) a saldo státního rozpočtu České republiky.")

    col_d1, col_d2, col_d3, col_d4 = st.columns(4)
    debt_gdp_curr = last_row.get("public_debt_gdp_pct")
    debt_gdp_prev = prev_row.get("public_debt_gdp_pct")
    debt_gdp_delta = (debt_gdp_curr - debt_gdp_prev) if (debt_gdp_curr and debt_gdp_prev) else 0.0

    debt_nom_curr = last_row.get("public_debt_czk_bn")
    deficit_curr = last_row.get("budget_deficit_czk_bn")
    maastricht_buffer = (60.0 - debt_gdp_curr) if debt_gdp_curr else 0.0

    col_d1.metric("Veřejný dluh k HDP", f"{debt_gdp_curr:.1f} %" if debt_gdp_curr else "N/A", delta=f"{debt_gdp_delta:+.1f} p.b.", delta_color="inverse", help="Maastrichtský strop je 60.0 % HDP")
    col_d2.metric("Nominální veřejný dluh", f"{debt_nom_curr:,.0f} mld. Kč".replace(",", " ") if debt_nom_curr else "N/A", help="Celkový konsolidovaný dluh vládního sektoru")
    col_d3.metric("Kvartální saldo rozpočtu", f"{deficit_curr:+.1f} mld. Kč" if deficit_curr else "N/A", delta="Schodek" if (deficit_curr and deficit_curr < 0) else "Přebytek", delta_color="off")
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
# TAB 7: VÝNOSOVÁ KŘIVKA (CZGB & IRS)
# -----------------------------------------------------------------------------
with tab_yield_curve:
    st.markdown('<div class="section-header">📉 Výnosová křivka: České státní dluhopisy (CZGB 1–15Y) a Úrokové swapy (IRS)</div>', unsafe_allow_html=True)
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
        chk_show_vals = st.checkbox("🏷️ Zobrazit hodnoty u bodů v grafu", value=True, key="chk_yc_show_vals")

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

    with st.expander("🔍 Zobrazit detailní tabulku splatností (Term Sheet: 1Y až 15Y)", expanded=False):
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
        "Inverze signalizuje, že trh očekává prudký pokles inflace a uvolňování měnové politiky centrální bankou.\n"
        "- **Úrokové swapy (IRS):** Swapová křivka odráží cenu peněz na mezibankovním trhu. "
        "5Y a 10Y CZK IRS jsou klíčovými benchmarky, které komerční banky v ČR používají k tvorbě cen pro fixace hypotečních úvěrů a firemních půjček."
    )

# -----------------------------------------------------------------------------
# TAB 8: VŠECHNY GRAFY POHROMADĚ
# -----------------------------------------------------------------------------
with tab_all:
    st.markdown('<div class="section-header">📊 Souhrnný přehled (Všechny makroekonomické grafy)</div>', unsafe_allow_html=True)
    st.caption("Kompletní makroekonomický obrázek pro rychlé zhodnocení souvislostí mezi sazbami, inflací, hospodářským růstem, trhem práce a kurzy.")

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
    st.subheader("6. Výnosová křivka (CZGB 1–15Y vs. IRS)")
    fig_all_yc = build_yield_curve_snapshot(df_row=last_row, compare_row=None, show_czgb=True, show_irs=True)
    render_plotly_chart(fig_all_yc, key="chart_all_yc_snapshot")

    st.markdown("---")
    st.subheader("7. Sklon výnosové křivky (Spread 10Y − 2Y v bps)")
    fig_all_spread = build_curve_spread_chart(df)
    render_plotly_chart(fig_all_spread, key="chart_all_yc_spread")

# -----------------------------------------------------------------------------
# TAB 9: DATA A EXPORT (CSV)
# -----------------------------------------------------------------------------
with tab_table:
    st.markdown('<div class="section-header">📋 Přehled surových dat a export do CSV</div>', unsafe_allow_html=True)

    col_table_top1, col_table_top2 = st.columns([3, 1])

    with col_table_top1:
        st.caption(f"Filtrovaná data obsahují **{len(df_export_cz)}** časových záznamů a **{len(cols_to_display) - 1}** vybraných indikátorů.")

    with col_table_top2:
        csv_buffer = io.StringIO()
        df_export_cz.to_csv(csv_buffer, index=False, sep=";", encoding="utf-8")
        csv_bytes = ("\ufeff" + csv_buffer.getvalue()).encode("utf-8")

        st.download_button(
            label="📥 Stáhnout data (CSV pro Excel)",
            data=csv_bytes,
            file_name=f"czech_macro_data_{frequency_code.lower()}_{datetime.now().strftime('%Y%m%d')}.csv",
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
