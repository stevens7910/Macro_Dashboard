"""
app.py
======
Český Makroekonomický Dashboard ve Streamlit.
Přehledná, responzivní a modulární aplikace pro vizualizaci klíčových makroekonomických
indikátorů České republiky v čase (ČNB, Inflace, HDP a Trh práce).
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
    page_title="Český Makroekonomický Dashboard | ČNB, HDP, Inflace",
    page_icon="🇨🇿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS pro profesionální design a čitelnost
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
    
    /* Styl záložek (Tabs) */
    button[data-baseweb="tab"] {
        font-size: 1.02rem !important;
        font-weight: 600 !important;
        padding: 10px 18px !important;
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

st.sidebar.title("🇨🇿 Nastavení a filtry")

# Výběr časového horizontu
st.sidebar.subheader("📅 Časový horizont")
horizon_option = st.sidebar.radio(
    "Zvolte období:",
    options=["1 rok", "3 roky", "5 let", "Celá historie (od 2015)", "Vlastní rozsah"],
    index=2,
    help="Rychlé předvolby nebo vlastní nastavení kalendářního rozpětí dat."
)

# Přepínač frekvence
st.sidebar.subheader("⏱️ Frekvence dat")
freq_choice = st.sidebar.radio(
    "Agregace časové řady:",
    options=["Měsíční (Monthly)", "Kvartální (Quarterly)"],
    index=0,
    help="Měsíční data poskytují vyšší detail sazeb a inflace, kvartální data přesně odpovídají periodicitě HDP."
)
frequency_code = "M" if freq_choice.startswith("Měsíční") else "Q"

# Volba indikátorů
st.sidebar.subheader("📊 Zobrazené ukazatele")
all_indicator_keys = list(INDICATORS.keys())
default_indicators = [
    "repo_rate", "discount_rate", "lombard_rate",
    "pribor_3m", "cpi_yoy", "gdp_growth_real",
    "gdp_nominal_czk_bn", "unemployment_rate"
]

selected_indicators = st.sidebar.multiselect(
    "Vyberte ukazatele do dashboardu:",
    options=all_indicator_keys,
    default=default_indicators,
    format_func=lambda k: f"{INDICATORS[k].category}: {INDICATORS[k].name_cz} ({INDICATORS[k].unit})"
)

# Nastavení zdroje a API klíčů
st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Datový zdroj & API")

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
# 5. FILTROVÁNÍ ČASOVÉHO HORIZONTU
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
elif horizon_option == "Celá historie (od 2015)":
    start_filter_date = min_date
    end_filter_date = max_date
else:
    # Vlastní rozsah přes slider/kalendář
    col_s1, col_s2 = st.sidebar.columns(2)
    start_filter_date = pd.to_datetime(col_s1.date_input("Od data:", min_date.date()))
    end_filter_date = pd.to_datetime(col_s2.date_input("Do data:", max_date.date()))

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
    mezibankovního trhu (**PRIBOR**), vývoje spotřebitelských cen (**Inflace CPI**), výkonnosti hospodářství (**HDP**) 
    a míry nezaměstnanosti v čase.
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

    # Koridor: Lombardní (horní) a Diskontní (dolní mez)
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

    # 2T Repo sazba ČNB (Hlavní schodovitá linie)
    if "repo_rate" in indicators and "repo_rate" in dframe.columns:
        fig.add_trace(go.Scatter(
            x=dframe["date"],
            y=dframe["repo_rate"],
            mode="lines",
            name="2T Repo sazba ČNB (klíčová)",
            line=dict(color="#1D4ED8", width=3.5, shape="hv"),
            hovertemplate="<b>2T Repo sazba</b>: %{y:.2f} %<extra></extra>"
        ))

    # PRIBOR sazby
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

    # Toleranční pásmo ČNB (1.0 % – 3.0 %)
    fig.add_hrect(
        y0=1.0, y1=3.0,
        fillcolor="rgba(34, 197, 94, 0.12)",
        line_width=0,
        annotation_text="Toleranční pásmo ČNB (1–3 %)",
        annotation_position="top left",
        annotation_font=dict(color="#166534", size=11),
        secondary_y=False
    )

    # Inflační cíl ČNB 2.0 %
    fig.add_hline(
        y=2.0,
        line=dict(color="#16A34A", width=1.8, dash="dash"),
        annotation_text="Inflační cíl (2.0 %)",
        annotation_position="bottom right",
        annotation_font=dict(color="#16A34A", size=11),
        secondary_y=False
    )

    # Inflace CPI
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

    # Reálná úroková sazba (Repo - CPI) na sekundární ose
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

    # 1. Nominální HDP
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

    # 2. Reálný růst HDP
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

tab_rates, tab_inflation, tab_gdp, tab_une, tab_all, tab_table = st.tabs([
    "🏛️ Sazby (ČNB & PRIBOR)",
    "🏷️ Inflace (CPI)",
    "📈 HDP (Růst a objem)",
    "👥 Nezaměstnanost",
    "📊 Všechny grafy",
    "📋 Data a export"
])

# -----------------------------------------------------------------------------
# TAB 1: SAZBY (ČNB & PRIBOR)
# -----------------------------------------------------------------------------
with tab_rates:
    st.markdown('<div class="section-header">🏛️ Měnová politika ČNB a mezibankovní sazby PRIBOR</div>', unsafe_allow_html=True)
    st.caption("Úrokový koridor České národní banky: 2T Repo sazba, Diskontní sazba (depozitní facilita) a Lombardní sazba (zápůjční facilita) ve srovnání s tržními sazbami PRIBOR.")
    
    # Rychlé shrnutí sazeb
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
# TAB 5: VŠECHNY GRAFY POHROMADĚ
# -----------------------------------------------------------------------------
with tab_all:
    st.markdown('<div class="section-header">📊 Souhrnný přehled (Všechny makroekonomické grafy)</div>', unsafe_allow_html=True)
    st.caption("Kompletní makroekonomický obrázek pro rychlé zhodnocení souvislostí mezi sazbami, inflací, hospodářským růstem a trhem práce.")

    st.subheader("1. Měnová politika & Inflace (ČNB vs. PRIBOR vs. CPI)")
    fig_combo = build_rates_vs_inflation_chart(df, selected_indicators)
    render_plotly_chart(fig_combo, key="chart_all_combo")

    st.markdown("---")
    st.subheader("2. Hrubý domácí produkt (Nominální objem a reálný růst)")
    render_plotly_chart(fig_gdp, key="chart_all_gdp")

    st.markdown("---")
    st.subheader("3. Trh práce (Míra nezaměstnanosti)")
    render_plotly_chart(fig_une, key="chart_all_une")

# -----------------------------------------------------------------------------
# TAB 6: DATA A EXPORT (CSV)
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
           - *Otevřená REST API*: Denní fixace referenčních sazeb peněžního trhu **PRIBOR** (1M, 3M, 6M) a operace volného trhu.
           - *Měnověpolitické nástroje*: Oficiální historie nastavení klíčových sazeb – **2T repo sazba**, **diskontní sazba** (depozitní facilita) a **lombardní sazba** (zápůjční facilita).
        2. **Eurostat & Český statistický úřad (ČSÚ)**:
           - *Harmonizovaný index spotřebitelských cen (HICP / CPI)*: Meziroční míra inflace za ČR v %.
           - *Čtvrtletní národní účty (namq_10_gdp)*: Reálný meziroční růst HDP v řetězených objemech a objem nominálního HDP v běžných cenách.
           - *Statistika trhu práce (une_rt_m)*: Měsíční sezónně očištěná míra nezaměstnanosti dle definice ILO.
        3. **Federal Reserve Bank of St. Louis (FRED)**:
           - Volitelný záložní zdroj agregovaných mezinárodních časových řad pro ČR (při zadání vlastního API klíče).

        ### Odolnost aplikace (Resilience & Caching)
        - Všechna data jsou cachována na úrovni aplikačního serveru pomocí Streamlit dekorátoru `@st.cache_data(ttl=3600)`.
        - V případě výpadku externích REST služeb nebo nedostupnosti sítě aplikace automaticky aktivuje **realistický historický model (2015–současnost)**, který zachovává skutečné ekonomické milníky (konec kurzového závazku, covidové dno, inflační vlnu 2022–2023 s vrcholem sazeb na 7.00 % i následný dezinflační cyklus).
        """
    )
