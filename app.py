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
        margin-top: 1.2rem;
        margin-bottom: 0.6rem;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    /* Zmenšení paddingu v expanderu */
    .streamlit-expanderContent {
        padding-top: 0.5rem !important;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# =============================================================================
# 2. POMOCNÉ FORMÁTOVACÍ FUNKCE
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


def render_plotly_chart(fig: go.Figure) -> None:
    """Vykreslí Plotly graf s plnou kompatibilitou napříč verzemi Streamlit."""
    try:
        st.plotly_chart(fig, width="stretch")
    except (TypeError, ValueError):
        st.plotly_chart(fig, use_container_width=True)


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
    # Vlastní rozsah přes slider
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

# Informační pruh nahoře
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

# 1. ČNB 2T Repo sazba
last_row = df.iloc[-1]
prev_row = df.iloc[-2] if len(df) > 1 else last_row

repo_curr = last_row.get("repo_rate")
repo_prev = prev_row.get("repo_rate")
repo_delta = (repo_curr - repo_prev) if (repo_curr is not None and repo_prev is not None) else 0.0

with kpi_cols[0]:
    st.metric(
        label="🏛️ 2T Repo sazba ČNB",
        value=f"{repo_curr:.2f} %" if repo_curr is not None else "N/A",
        delta=f"{repo_delta:+.2f} p.b." if len(df) > 1 else "Aktuální",
        delta_color="inverse",  # Zvýšení sazeb = zpřísnění podmínek
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
        delta_color="inverse",  # Růst inflace = negativní delta
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
        delta_color="normal",  # Růst HDP = pozitivní
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
        delta_color="inverse",  # Růst nezaměstnanosti = negativní
        help="Obecná míra nezaměstnanosti sezónně očištěná (Eurostat / ČSÚ). Česká republika si dlouhodobě udržuje nejnižší nezaměstnanost v EU."
    )

st.markdown("---")


# =============================================================================
# 8. GRAF 1: MĚNOVÁ POLITIKA (SAZBY ČNB vs PRIBOR vs INFLACE)
# =============================================================================

st.markdown('<div class="section-header">🏛️ Graf 1: Měnová politika (Sazby ČNB vs. Mezibankovní PRIBOR vs. Inflace CPI)</div>', unsafe_allow_html=True)
st.caption("Srovnání úrokového koridoru ČNB (Repo, Diskontní a Lombardní sazba), referenčních sazeb mezibankovního trhu PRIBOR a meziroční inflace CPI.")

fig_rates = make_subplots(
    rows=1, cols=1,
    specs=[[{"secondary_y": True}]]
)

# 1. Koridor sazeb ČNB (Lombardní a Diskontní sazba s výplní)
if "lombard_rate" in selected_indicators and "lombard_rate" in df.columns:
    fig_rates.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["lombard_rate"],
            mode="lines",
            name="Lombardní sazba ČNB (horní mez)",
            line=dict(color="rgba(148, 163, 184, 0.7)", width=1.5, dash="dash"),
            hoverinfo="x+y+name"
        ),
        secondary_y=False
    )

if "discount_rate" in selected_indicators and "discount_rate" in df.columns:
    fig_rates.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["discount_rate"],
            mode="lines",
            name="Diskontní sazba ČNB (dolní mez)",
            line=dict(color="rgba(148, 163, 184, 0.7)", width=1.5, dash="dash"),
            fill="tonexty" if ("lombard_rate" in selected_indicators and "lombard_rate" in df.columns) else None,
            fillcolor="rgba(226, 232, 240, 0.35)",  # Jemné podbarvení koridoru
            hoverinfo="x+y+name"
        ),
        secondary_y=False
    )

# 2. 2T Repo sazba ČNB (Hlavní linie)
if "repo_rate" in selected_indicators and "repo_rate" in df.columns:
    fig_rates.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["repo_rate"],
            mode="lines",
            name="2T Repo sazba ČNB",
            line=dict(color="#1D4ED8", width=3.5, shape="hv"),  # Schodovitý tvar
            hovertemplate="<b>2T Repo sazba</b>: %{y:.2f} %<extra></extra>"
        ),
        secondary_y=False
    )

# 3. PRIBOR sazby
pribor_colors = {
    "pribor_1m": ("#06B6D4", "PRIBOR 1M", 1.5),
    "pribor_3m": ("#0D9488", "PRIBOR 3M", 2.2),
    "pribor_6m": ("#047857", "PRIBOR 6M", 1.5)
}
for p_col, (p_color, p_name, p_width) in pribor_colors.items():
    if p_col in selected_indicators and p_col in df.columns:
        fig_rates.add_trace(
            go.Scatter(
                x=df["date"],
                y=df[p_col],
                mode="lines",
                name=p_name,
                line=dict(color=p_color, width=p_width, dash="dot" if p_col != "pribor_3m" else "solid"),
                hovertemplate=f"<b>{p_name}</b>: %{{y:.2f}} %<extra></extra>"
            ),
            secondary_y=False
        )

# 4. Inflace CPI (na sekundární ose Y pro přehledné srovnání dynamiky)
if "cpi_yoy" in selected_indicators and "cpi_yoy" in df.columns:
    fig_rates.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["cpi_yoy"],
            mode="lines+markers",
            name="Inflace CPI (meziročně v %)",
            line=dict(color="#DC2626", width=2.5),
            marker=dict(size=4, color="#DC2626"),
            hovertemplate="<b>Inflace CPI</b>: %{y:.1f} %<extra></extra>"
        ),
        secondary_y=True
    )

    # Inflační cíl ČNB 2.0 % jako referenční čára
    fig_rates.add_hline(
        y=2.0,
        line=dict(color="#16A34A", width=1.5, dash="dash"),
        annotation_text="Inflační cíl ČNB (2.0 %)",
        annotation_position="bottom right",
        annotation_font=dict(color="#16A34A", size=10),
        secondary_y=True
    )

fig_rates.update_layout(
    height=480,
    hovermode="x unified",
    margin=dict(l=20, r=20, t=30, b=20),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1,
        bgcolor="rgba(255, 255, 255, 0.8)"
    ),
    xaxis=dict(
        title="",
        showgrid=True,
        gridcolor="#f1f5f9"
    ),
    yaxis=dict(
        title="Úrokové sazby ČNB & PRIBOR (%)",
        title_font=dict(color="#1D4ED8"),
        tickfont=dict(color="#1D4ED8"),
        showgrid=True,
        gridcolor="#f1f5f9",
        ticksuffix=" %"
    ),
    yaxis2=dict(
        title="Meziroční inflace CPI (%)",
        title_font=dict(color="#DC2626"),
        tickfont=dict(color="#DC2626"),
        overlaying="y",
        side="right",
        showgrid=False,
        ticksuffix=" %"
    ),
    plot_bgcolor="#FFFFFF",
    paper_bgcolor="#FFFFFF"
)

render_plotly_chart(fig_rates)


# =============================================================================
# 9. GRAF 2: HRUBÝ DOMÁCÍ PRODUKT (REÁLNÝ RŮST A NOMINÁLNÍ OBJEM)
# =============================================================================

st.markdown('<div class="section-header">📈 Graf 2: Hrubý domácí produkt (Reálný růst v % a Nominální objem v mld. CZK)</div>', unsafe_allow_html=True)
st.caption("Kombinovaný graf: Levá osa zobrazuje nominální tvorbu HDP v mld. CZK, pravá osa ukazuje reálné meziroční tempo růstu.")

fig_gdp = make_subplots(
    rows=1, cols=1,
    specs=[[{"secondary_y": True}]]
)

# 1. Nominální HDP (Sloupcový graf)
if "gdp_nominal_czk_bn" in selected_indicators and "gdp_nominal_czk_bn" in df.columns:
    # Odstraníme případné duplicity kvartálu pro čisté zobrazení sloupců
    df_gdp_plot = df.drop_duplicates(subset=["quarter"] if "quarter" in df.columns else ["date"]).copy()
    
    fig_gdp.add_trace(
        go.Bar(
            x=df_gdp_plot["date"],
            y=df_gdp_plot["gdp_nominal_czk_bn"],
            name="Nominální HDP (mld. CZK)",
            marker=dict(
                color="rgba(71, 85, 105, 0.55)",
                line=dict(color="#334155", width=1)
            ),
            hovertemplate="<b>Nominální HDP</b>: %{y:,.1f} mld. CZK<extra></extra>"
        ),
        secondary_y=False
    )

# 2. Reálný růst HDP (Spojnicový graf se značkami)
if "gdp_growth_real" in selected_indicators and "gdp_growth_real" in df.columns:
    df_growth_plot = df.drop_duplicates(subset=["quarter"] if "quarter" in df.columns else ["date"]).copy()
    
    # Rozlišení barev pro kladný a záporný růst
    marker_colors = ["#16A34A" if val >= 0 else "#DC2626" for val in df_growth_plot["gdp_growth_real"]]

    fig_gdp.add_trace(
        go.Scatter(
            x=df_growth_plot["date"],
            y=df_growth_plot["gdp_growth_real"],
            mode="lines+markers",
            name="Reálný růst HDP (YoY %)",
            line=dict(color="#D97706", width=3),
            marker=dict(size=7, color=marker_colors, line=dict(color="#FFFFFF", width=1.5)),
            hovertemplate="<b>Reálný růst</b>: %{y:+.1f} %<extra></extra>"
        ),
        secondary_y=True
    )

    # Nulová referenční čára (hranice expanze a recese)
    fig_gdp.add_hline(
        y=0.0,
        line=dict(color="#94A3B8", width=1.5, dash="dash"),
        secondary_y=True
    )

fig_gdp.update_layout(
    height=440,
    hovermode="x unified",
    margin=dict(l=20, r=20, t=30, b=20),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1,
        bgcolor="rgba(255, 255, 255, 0.8)"
    ),
    xaxis=dict(
        title="",
        showgrid=True,
        gridcolor="#f1f5f9"
    ),
    yaxis=dict(
        title="Nominální HDP (mld. CZK / kvartál)",
        title_font=dict(color="#334155"),
        tickfont=dict(color="#334155"),
        showgrid=True,
        gridcolor="#f1f5f9",
        ticksuffix=" mld."
    ),
    yaxis2=dict(
        title="Reálný růst HDP (YoY %)",
        title_font=dict(color="#D97706"),
        tickfont=dict(color="#D97706"),
        overlaying="y",
        side="right",
        showgrid=False,
        ticksuffix=" %"
    ),
    plot_bgcolor="#FFFFFF",
    paper_bgcolor="#FFFFFF"
)

render_plotly_chart(fig_gdp)


# =============================================================================
# 10. GRAF 3: TRH PRÁCE (MÍRA NEZAMĚSTNANOSTI)
# =============================================================================

st.markdown('<div class="section-header">👥 Graf 3: Trh práce (Vývoj obecné míry nezaměstnanosti v ČR)</div>', unsafe_allow_html=True)
st.caption("Časová řada sezónně očištěné míry nezaměstnanosti v České republice (Eurostat / ČSÚ) s vyznačeným dlouhodobým průměrem.")

if "unemployment_rate" in selected_indicators and "unemployment_rate" in df.columns:
    fig_une = go.Figure()

    # Vyplněná oblast pod křivkou
    fig_une.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["unemployment_rate"],
            mode="lines",
            name="Míra nezaměstnanosti v ČR",
            line=dict(color="#4F46E5", width=2.8),
            fill="tozeroy",
            fillcolor="rgba(79, 70, 229, 0.08)",
            hovertemplate="<b>Nezaměstnanost</b>: %{y:.1f} %<extra></extra>"
        )
    )

    # Dlouhodobý průměr
    avg_une = df["unemployment_rate"].mean()
    fig_une.add_hline(
        y=avg_une,
        line=dict(color="#64748B", width=1.5, dash="dash"),
        annotation_text=f"Průměr ve zvoleném období: {avg_une:.2f} %",
        annotation_position="top right",
        annotation_font=dict(color="#64748B", size=11)
    )

    # Anotace minima a maxima
    min_une_val = df["unemployment_rate"].min()
    max_une_val = df["unemployment_rate"].max()
    min_une_row = df.loc[df["unemployment_rate"] == min_une_val].iloc[0]
    max_une_row = df.loc[df["unemployment_rate"] == max_une_val].iloc[0]

    fig_une.add_trace(
        go.Scatter(
            x=[min_une_row["date"], max_une_row["date"]],
            y=[min_une_val, max_une_val],
            mode="markers+text",
            name="Extrémy (Min / Max)",
            marker=dict(size=8, color=["#16A34A", "#DC2626"]),
            text=[f"Min: {min_une_val:.1f} %", f"Max: {max_une_val:.1f} %"],
            textposition=["bottom center", "top center"],
            showlegend=False,
            hoverinfo="skip"
        )
    )

    fig_une.update_layout(
        height=380,
        hovermode="x unified",
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis=dict(
            title="",
            showgrid=True,
            gridcolor="#f1f5f9"
        ),
        yaxis=dict(
            title="Míra nezaměstnanosti (%)",
            ticksuffix=" %",
            showgrid=True,
            gridcolor="#f1f5f9",
            range=[0, max(6.0, max_une_val + 1.0)]
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF"
    )

    render_plotly_chart(fig_une)
else:
    st.info("Ukazatel Míra nezaměstnanosti není vybrán v postranním panelu.")

st.markdown("---")


# =============================================================================
# 11. TABULKA SUROVÝCH DAT A EXPORT (DATA EXPLORER)
# =============================================================================

st.markdown('<div class="section-header">📋 Přehled surových dat a export do CSV</div>', unsafe_allow_html=True)

# Příprava tabulky pro uživatele
cols_to_display = ["date"]
if "quarter" in df.columns and frequency_code == "Q":
    cols_to_display.append("quarter")

for col in selected_indicators:
    if col in df.columns and col not in cols_to_display:
        cols_to_display.append(col)

df_export = df[cols_to_display].copy()

# Přejmenování sloupců do češtiny s jednotkami
rename_dict = {"date": "Datum", "quarter": "Kvartál"}
for col in selected_indicators:
    info = INDICATORS.get(col)
    if info:
        rename_dict[col] = f"{info.name_cz} [{info.unit}]"

df_export_cz = df_export.rename(columns=rename_dict)
df_export_cz["Datum"] = df_export_cz["Datum"].dt.strftime("%d.%m.%Y")

col_table_top1, col_table_top2 = st.columns([3, 1])

with col_table_top1:
    st.caption(f"Tabulka obsahuje **{len(df_export_cz)}** časových záznamů a **{len(cols_to_display) - 1}** vybraných indikátorů.")

with col_table_top2:
    # Generování CSV s UTF-8 BOM pro bezchybné zobrazení diakritiky v Microsoft Excel
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
# 12. METODIKA A POPIS INDIKÁTORŮ
# =============================================================================

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
