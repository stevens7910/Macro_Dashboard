"""
Localization (i18n) Module for the Macroeconomic & Market Monitor (CZ / EN).
Provides full bilingual support (Czech & English) across UI controls, KPI cards,
Plotly charts, dynamic financial news, indicator catalog, data export, search bar,
and explanatory glossary.
"""

import re
import functools
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
import streamlit as st
from streamlit.delta_generator import DeltaGenerator


# =============================================================================
# 1. LANGUAGE STATE & SWITCHER
# =============================================================================

def init_language_state() -> str:
    """Initializes language state from URL query params or session_state."""
    qp_lang = st.query_params.get("lang", "")
    if qp_lang:
        qp_clean = str(qp_lang).strip().lower()
        if qp_clean in ("en", "eng", "gb", "uk", "us"):
            st.session_state["ui_lang"] = "🇬🇧 EN"
        elif qp_clean in ("cs", "cz"):
            st.session_state["ui_lang"] = "🇨🇿 CZ"
        try:
            del st.query_params["lang"]
        except Exception:
            pass

    if "ui_lang" not in st.session_state or st.session_state["ui_lang"] not in ("🇨🇿 CZ", "🇬🇧 EN"):
        st.session_state["ui_lang"] = "🇨🇿 CZ"
    return get_lang()


def get_lang() -> str:
    """Returns 'en' if English is selected, otherwise 'cs'."""
    val = st.session_state.get("ui_lang", "🇨🇿 CZ")
    if val in ("🇬🇧 EN", "EN", "en"):
        return "en"
    return "cs"


def is_en() -> bool:
    """Returns True when the English language mode is active."""
    return get_lang() == "en"


def render_language_switcher(container: Any = st, key_suffix: str = "top") -> str:
    """Renders a compact CZ / EN language switcher."""
    init_language_state()
    current_val = st.session_state.get("ui_lang", "🇨🇿 CZ")
    if current_val not in ("🇨🇿 CZ", "🇬🇧 EN"):
        current_val = "🇨🇿 CZ"

    widget_key = f"ui_lang_switch_{key_suffix}"

    def _on_lang_change():
        new_v = st.session_state.get(widget_key)
        if new_v in ("🇨🇿 CZ", "🇬🇧 EN"):
            st.session_state["ui_lang"] = new_v

    try:
        selected = container.segmented_control(
            "Jazyk / Language",
            options=["🇨🇿 CZ", "🇬🇧 EN"],
            default=current_val,
            label_visibility="collapsed",
            key=widget_key,
            on_change=_on_lang_change,
        )
    except AttributeError:
        selected = container.radio(
            "Jazyk / Language",
            options=["🇨🇿 CZ", "🇬🇧 EN"],
            index=1 if current_val == "🇬🇧 EN" else 0,
            horizontal=True,
            label_visibility="collapsed",
            key=widget_key,
            on_change=_on_lang_change,
        )

    if selected in ("🇨🇿 CZ", "🇬🇧 EN") and selected != st.session_state.get("ui_lang"):
        st.session_state["ui_lang"] = selected
        st.rerun()

    return get_lang()


# =============================================================================
# 2. INDICATOR METADATA TRANSLATIONS (68+ INDICATORS)
# =============================================================================

INDICATOR_I18N: Dict[str, Dict[str, str]] = {
    # CZ
    "repo_rate": {
        "name": "CNB 2W Repo Rate",
        "unit": "%",
        "category": "Monetary Policy",
        "description": "Main monetary policy rate of the CNB used to remunerate 2-week liquidity-absorbing operations in the banking sector.",
    },
    "discount_rate": {
        "name": "CNB Discount Rate",
        "unit": "%",
        "category": "Monetary Policy",
        "description": "Lower bound of the CNB interest rate corridor (overnight deposit facility for excess bank liquidity).",
    },
    "lombard_rate": {
        "name": "CNB Lombard Rate",
        "unit": "%",
        "category": "Monetary Policy",
        "description": "Upper bound of the CNB interest rate corridor (overnight marginal lending facility against collateral).",
    },
    "pribor_1m": {
        "name": "PRIBOR 1M",
        "unit": "%",
        "category": "Interbank Market",
        "description": "Prague Interbank Offered Rate for 1-month maturity.",
    },
    "pribor_3m": {
        "name": "PRIBOR 3M",
        "unit": "%",
        "category": "Interbank Market",
        "description": "Key 3-month reference rate of the Czech interbank market (benchmark for corporate loans and derivatives).",
    },
    "pribor_6m": {
        "name": "PRIBOR 6M",
        "unit": "%",
        "category": "Interbank Market",
        "description": "Reference rate of the Czech interbank market for 6-month maturity.",
    },
    "cpi_yoy": {
        "name": "CZ Inflation (CPI YoY)",
        "unit": "%",
        "category": "Price Level",
        "description": "Year-on-year headline inflation rate measured by the Consumer Price Index (HICP / national CPI).",
    },
    "cpi_core_yoy": {
        "name": "CZ Core Inflation (Core CPI)",
        "unit": "%",
        "category": "Price Level",
        "description": "Year-on-year core inflation in the Czech Republic (excluding regulated prices, food, and fuels, monitored by the CNB).",
    },
    "gdp_growth_real": {
        "name": "CZ Real GDP Growth (YoY)",
        "unit": "%",
        "category": "Gross Domestic Product",
        "description": "Year-on-year real change in Gross Domestic Product in chain-linked volumes (seasonally and price adjusted).",
    },
    "gdp_nominal_czk_bn": {
        "name": "CZ Nominal GDP",
        "unit": "CZK bn",
        "category": "Gross Domestic Product",
        "description": "Nominal Gross Domestic Product at current prices in billions of CZK for the given period.",
    },
    "retail_sales_yoy": {
        "name": "CZ Retail Sales (Consumption YoY)",
        "unit": "%",
        "category": "Economic Activity",
        "description": "Year-on-year real change in retail trade sales excluding automotive segment (key household consumption indicator).",
    },
    "industrial_prod_yoy": {
        "name": "CZ Industrial Production (YoY)",
        "unit": "%",
        "category": "Economic Activity",
        "description": "Year-on-year Industrial Production Index in the Czech Republic adjusted for working days (CZSO / Eurostat).",
    },
    "unemployment_rate": {
        "name": "CZ Unemployment Rate",
        "unit": "%",
        "category": "Labor Market",
        "description": "Seasonally adjusted general unemployment rate under ILO / Eurostat methodology for ages 15–74.",
    },
    "eur_czk": {
        "name": "EUR/CZK Exchange Rate",
        "unit": "CZK",
        "category": "Exchange Rates",
        "description": "Official exchange rate of the Czech koruna against the euro (CNB daily FX market fixing).",
    },
    "usd_czk": {
        "name": "USD/CZK Exchange Rate",
        "unit": "CZK",
        "category": "Exchange Rates",
        "description": "Official exchange rate of the Czech koruna against the US dollar (CNB daily FX market fixing).",
    },
    "pln_czk": {
        "name": "PLN/CZK Exchange Rate",
        "unit": "CZK",
        "category": "Exchange Rates",
        "description": "Exchange rate of the Polish zloty against the Czech koruna (CNB daily FX market fixing).",
    },
    "gbp_czk": {
        "name": "GBP/CZK Exchange Rate",
        "unit": "CZK",
        "category": "Exchange Rates",
        "description": "Exchange rate of the British pound against the Czech koruna (CNB daily FX market fixing).",
    },
    "public_debt_czk_bn": {
        "name": "CZ Public Debt",
        "unit": "CZK bn",
        "category": "Fiscal Policy",
        "description": "Consolidated gross general government debt of the Czech Republic in billions of CZK.",
    },
    "public_debt_gdp_pct": {
        "name": "CZ Public Debt to GDP",
        "unit": "% GDP",
        "category": "Fiscal Policy",
        "description": "Ratio of general government debt to GDP in % (Maastricht fiscal criterion with 60% limit).",
    },
    "budget_deficit_czk_bn": {
        "name": "CZ State Budget Balance",
        "unit": "CZK bn",
        "category": "Fiscal Policy",
        "description": "State budget balance (deficit is negative, surplus is positive) in billions of CZK.",
    },
    "czgb_10y": {
        "name": "10Y CZGB Yield (Benchmark)",
        "unit": "%",
        "category": "Bond Market",
        "description": "Yield to maturity on the 10-year benchmark Czech government bond (Eurostat Maastricht criterion).",
    },
    "czgb_2y": {
        "name": "2Y CZGB Yield",
        "unit": "%",
        "category": "Bond Market",
        "description": "Yield to maturity on the 2-year Czech government bond (short end of the yield curve).",
    },
    "czgb_5y": {
        "name": "5Y CZGB Yield",
        "unit": "%",
        "category": "Bond Market",
        "description": "Yield to maturity on the 5-year Czech government bond (middle segment of the yield curve).",
    },
    "czgb_15y": {
        "name": "15Y CZGB Yield",
        "unit": "%",
        "category": "Bond Market",
        "description": "Yield to maturity on the 15-year Czech government bond (long end of the yield curve).",
    },
    "irs_10y": {
        "name": "10Y CZK IRS Rate",
        "unit": "%",
        "category": "Derivatives Market (IRS)",
        "description": "Reference market rate of the 10-year CZK Interest Rate Swap (interbank benchmark for fixed rate pricing).",
    },
    "irs_5y": {
        "name": "5Y CZK IRS Rate",
        "unit": "%",
        "category": "Derivatives Market (IRS)",
        "description": "Reference market rate of the 5-year CZK Interest Rate Swap (benchmark for 5-year mortgage fixations in CZ).",
    },
    "czgb_spread_10y_2y": {
        "name": "CZGB Curve Slope (10Y − 2Y)",
        "unit": "pp",
        "category": "Bond Market",
        "description": "Yield curve slope (spread between 10Y and 2Y yields). Negative value represents yield curve inversion.",
    },
    "cz_pmi_manufacturing": {
        "name": "CZ Manufacturing PMI (S&P Global)",
        "unit": "pts",
        "category": "Leading Indicators",
        "description": "Purchasing Managers' Index in Czech manufacturing by S&P Global. Values above 50 indicate expansion, below 50 contraction.",
    },
    "cz_confidence_composite": {
        "name": "CZ Business & Consumer Confidence (CZSO)",
        "unit": "pts",
        "category": "Leading Indicators",
        "description": "Composite confidence indicator (CZSO survey) combining business sentiment (industry, construction, trade, services) and consumer confidence.",
    },
    "cz_nominal_wage_yoy": {
        "name": "CZ Average Nominal Gross Wage (YoY)",
        "unit": "%",
        "category": "Labor Market",
        "description": "Year-on-year nominal growth of the average gross monthly wage per FTE employee in the Czech economy (CZSO).",
    },
    "cz_real_wage_yoy": {
        "name": "CZ Average Real Wage (YoY)",
        "unit": "%",
        "category": "Labor Market",
        "description": "Year-on-year real change in the average gross wage in the Czech Republic deflated by CPI inflation (CZSO).",
    },
    "cz_mortgage_rate": {
        "name": "CZ New Mortgages – Volume & Average Rate",
        "unit": "% / CZK bn",
        "category": "Banking Sector & Loans",
        "description": "Average interest rate and monthly volume of genuinely new housing mortgage loans excluding refinancing (CBA Hypomonitor / CNB).",
    },
    "cz_corporate_loans_yoy": {
        "name": "CZ Corporate Loans – YoY Growth",
        "unit": "%",
        "category": "Banking Sector & Loans",
        "description": "Year-on-year growth rate of bank loans provided to non-financial corporations in the Czech Republic (CNB monetary statistics).",
    },
    "cz_m2_growth_yoy": {
        "name": "CZ M2 Money Supply (YoY)",
        "unit": "%",
        "category": "Money Supply",
        "description": "Year-on-year growth of broad money aggregate M2 in the Czech Republic (currency in circulation, overnight and term deposits – CNB).",
    },
    "cz_current_account_gdp_pct": {
        "name": "CZ Current Account Balance (% of GDP)",
        "unit": "% GDP",
        "category": "External Balance",
        "description": "Current account balance of the Czech Republic as a ratio to GDP reflecting external trade and income flows (CNB / CZSO).",
    },
    "cz_trade_balance_czk_bn": {
        "name": "CZ Foreign Trade Balance (CZSO)",
        "unit": "CZK bn",
        "category": "External Balance",
        "description": "Monthly foreign trade balance in goods under national methodology in billions of CZK (Czech Statistical Office).",
    },
    "czgb_bund_spread_10y": {
        "name": "10Y CZGB vs. 10Y Bund Credit Spread",
        "unit": "bps",
        "category": "Bond Market",
        "description": "Yield spread between the 10-year Czech government bond and the German benchmark Bund in basis points (bps).",
    },
    "cz_asw_10y_spread": {
        "name": "Asset Swap Spread (ASW 10Y CZK)",
        "unit": "bps",
        "category": "Bond Market",
        "description": "Asset swap spread of the 10-year CZGB government bond against the CZK IRS swap curve in basis points.",
    },
    # EU
    "ecb_deposit_rate": {
        "name": "ECB Deposit Facility Rate",
        "unit": "%",
        "category": "EU Monetary Policy",
        "description": "Key interest rate of the European Central Bank for overnight bank deposits (main policy anchor of the ECB).",
    },
    "ecb_refi_rate": {
        "name": "ECB Main Refinancing Rate (MRO)",
        "unit": "%",
        "category": "EU Monetary Policy",
        "description": "Main Refinancing Operations rate of the ECB (weekly liquidity provision).",
    },
    "ecb_lending_rate": {
        "name": "ECB Marginal Lending Rate",
        "unit": "%",
        "category": "EU Monetary Policy",
        "description": "Overnight marginal lending facility rate of the ECB (upper bound of the policy rate corridor).",
    },
    "euribor_3m": {
        "name": "EURIBOR 3M",
        "unit": "%",
        "category": "EU Interbank Market",
        "description": "Key 3-month reference rate of the Eurozone interbank market (benchmark for EUR loans).",
    },
    "estr_rate": {
        "name": "€STR (Euro Short-Term Rate)",
        "unit": "%",
        "category": "EU Money Market",
        "description": "Risk-free overnight rate of the euro money market calculated by the ECB (successor to EONIA).",
    },
    "eu_cpi_yoy": {
        "name": "Eurozone Inflation (HICP)",
        "unit": "%",
        "category": "EU Price Level",
        "description": "Year-on-year headline inflation rate measured by the Harmonised Index of Consumer Prices (Eurostat HICP).",
    },
    "eu_core_cpi_yoy": {
        "name": "EU Core Inflation (Core HICP)",
        "unit": "%",
        "category": "EU Price Level",
        "description": "Eurozone core inflation excluding energy, food, alcohol, and tobacco (Eurostat Core HICP).",
    },
    "eu_gdp_growth_real": {
        "name": "Eurozone Real GDP Growth (YoY)",
        "unit": "%",
        "category": "EU Gross Domestic Product",
        "description": "Year-on-year real change in Eurozone / EU Gross Domestic Product at constant prices (Eurostat).",
    },
    "eu_gdp_nominal_eur_bn": {
        "name": "Eurozone Nominal GDP",
        "unit": "EUR bn",
        "category": "EU Gross Domestic Product",
        "description": "Quarterly nominal GDP of the Eurozone at current prices in billions of EUR.",
    },
    "eu_retail_sales_yoy": {
        "name": "EU Retail Sales (Consumption YoY)",
        "unit": "%",
        "category": "EU Economic Activity",
        "description": "Year-on-year change in retail trade volume in the Eurozone / EU (Eurostat Retail Trade Index).",
    },
    "eu_industrial_prod_yoy": {
        "name": "EU Industrial Production (YoY)",
        "unit": "%",
        "category": "EU Economic Activity",
        "description": "Year-on-year industrial production index in the Eurozone / EU (Eurostat Industrial Production).",
    },
    "eu_unemployment_rate": {
        "name": "EU Unemployment Rate",
        "unit": "%",
        "category": "EU Labor Market",
        "description": "Seasonally adjusted general unemployment rate in the EU / Eurozone under Eurostat methodology.",
    },
    "eur_pln": {
        "name": "EUR/PLN Exchange Rate",
        "unit": "PLN",
        "category": "EU Exchange Rates",
        "description": "Exchange rate of the euro against the Polish zloty (daily fixing).",
    },
    "eur_gbp": {
        "name": "EUR/GBP Exchange Rate",
        "unit": "GBP",
        "category": "EU Exchange Rates",
        "description": "Exchange rate of the euro against the British pound (daily fixing).",
    },
    "eu_public_debt_gdp_pct": {
        "name": "Eurozone Public Debt to GDP",
        "unit": "% GDP",
        "category": "EU Fiscal Policy",
        "description": "Consolidated general government debt of Eurozone member states as % of GDP (Maastricht average).",
    },
    "eu_public_debt_eur_bn": {
        "name": "Eurozone Public Debt",
        "unit": "EUR bn",
        "category": "EU Fiscal Policy",
        "description": "Total consolidated gross general government debt of the Eurozone in billions of EUR.",
    },
    "eu_budget_deficit_eur_bn": {
        "name": "Eurozone Government Budget Balance",
        "unit": "EUR bn",
        "category": "EU Fiscal Policy",
        "description": "Quarterly general government budget balance of the Eurozone (deficit is negative) in billions of EUR.",
    },
    "bund_10y": {
        "name": "10Y German Bund Yield (Benchmark)",
        "unit": "%",
        "category": "EU Bond Market",
        "description": "Yield to maturity on the 10-year German government bond (key risk-free benchmark of the Eurozone).",
    },
    "bund_2y": {
        "name": "2Y German Bund Yield",
        "unit": "%",
        "category": "EU Bond Market",
        "description": "Yield to maturity on the 2-year German government bond (short end sensitive to ECB policy).",
    },
    "bund_5y": {
        "name": "5Y German Bund Yield",
        "unit": "%",
        "category": "EU Bond Market",
        "description": "Yield to maturity on the 5-year German government bond (Bobl).",
    },
    "bund_30y": {
        "name": "30Y German Bund Yield",
        "unit": "%",
        "category": "EU Bond Market",
        "description": "Yield to maturity on the 30-year German government bond (ultra-long end of the curve).",
    },
    "bund_spread_10y_2y": {
        "name": "German Bund Curve Slope (10Y − 2Y)",
        "unit": "pp",
        "category": "EU Bond Market",
        "description": "Spread between 10Y and 2Y German government bond yields (inversion indicator in the Eurozone).",
    },
    "eu_ifo_business_climate": {
        "name": "German Ifo Business Climate Index",
        "unit": "pts",
        "category": "EU Leading Indicators",
        "description": "Ifo Geschäftsklimaindex – leading barometer of the German economy based on a monthly survey of 9,000 firms (Ifo Institute Munich).",
    },
    "eu_composite_pmi": {
        "name": "Eurozone Composite PMI",
        "unit": "pts",
        "category": "EU Leading Indicators",
        "description": "Composite Purchasing Managers' Index of the Eurozone combining manufacturing and services (S&P Global / HCOB Flash Eurozone PMI).",
    },
    "eu_negotiated_wages_yoy": {
        "name": "Eurozone Negotiated Wages (ECB YoY)",
        "unit": "%",
        "category": "EU Labor Market",
        "description": "Year-on-year growth in collectively agreed wages in the Eurozone monitored by the ECB as a key signal for wage-inflation dynamics.",
    },
    "eu_btp_bund_spread": {
        "name": "Italy vs. Germany Risk Spread (10Y BTP - Bund)",
        "unit": "bps",
        "category": "EU Bond Market",
        "description": "Yield spread between the 10-year Italian government bond (BTP) and the German Bund in basis points (barometer of Eurozone peripheral risk).",
    },
    # US
    "fed_funds_upper": {
        "name": "Fed Funds Target (Upper Bound)",
        "unit": "%",
        "category": "US Monetary Policy",
        "description": "Upper bound of the Federal Reserve (Fed) target federal funds rate range.",
    },
    "fed_funds_lower": {
        "name": "Fed Funds Target (Lower Bound)",
        "unit": "%",
        "category": "US Monetary Policy",
        "description": "Lower bound of the Federal Reserve (Fed) target federal funds rate range.",
    },
    "fed_effective_rate": {
        "name": "Effective Federal Funds Rate (EFFR)",
        "unit": "%",
        "category": "US Monetary Policy",
        "description": "Volume-weighted median effective overnight federal funds rate (EFFR).",
    },
    "sofr_rate": {
        "name": "SOFR (Secured Overnight Rate)",
        "unit": "%",
        "category": "US Money Market",
        "description": "Secured Overnight Financing Rate backed by U.S. Treasury collateral (successor to USD LIBOR).",
    },
    "us_1m": {
        "name": "1M US Treasury Bill Yield",
        "unit": "%",
        "category": "US Money Market",
        "description": "Yield on the 1-month U.S. Treasury Bill (short-term risk-free rate).",
    },
    "us_3m": {
        "name": "3M US Treasury Bill Yield",
        "unit": "%",
        "category": "US Money Market",
        "description": "Yield on the 3-month U.S. Treasury Bill (key USD money market benchmark).",
    },
    "us_cpi_yoy": {
        "name": "US Inflation (CPI YoY)",
        "unit": "%",
        "category": "US Price Level",
        "description": "Year-on-year consumer inflation rate in the United States (Headline Consumer Price Index – U.S. BLS).",
    },
    "us_core_cpi_yoy": {
        "name": "US Core Inflation (Core CPI)",
        "unit": "%",
        "category": "US Price Level",
        "description": "Year-on-year core consumer inflation rate in the US excluding volatile food and energy prices.",
    },
    "us_gdp_growth_real": {
        "name": "US Real GDP Growth (YoY)",
        "unit": "%",
        "category": "US Gross Domestic Product",
        "description": "Year-on-year change in real U.S. Gross Domestic Product (U.S. Bureau of Economic Analysis).",
    },
    "us_gdp_nominal_usd_bn": {
        "name": "US Nominal GDP",
        "unit": "USD bn",
        "category": "US Gross Domestic Product",
        "description": "U.S. Gross Domestic Product at current prices in billions of USD.",
    },
    "us_retail_sales_yoy": {
        "name": "US Retail Sales (Consumption YoY)",
        "unit": "%",
        "category": "US Economic Activity",
        "description": "Year-on-year change in U.S. retail sales (U.S. Census Bureau Advance Retail Sales).",
    },
    "us_industrial_prod_yoy": {
        "name": "US Industrial Production (YoY)",
        "unit": "%",
        "category": "US Economic Activity",
        "description": "Year-on-year U.S. Industrial Production Index (Federal Reserve G.17).",
    },
    "us_unemployment_rate": {
        "name": "US Unemployment Rate (U-3)",
        "unit": "%",
        "category": "US Labor Market",
        "description": "Official unemployment rate in the United States (U.S. Bureau of Labor Statistics U-3 rate).",
    },
    "us_nonfarm_payrolls_k": {
        "name": "US Nonfarm Payrolls (NFP)",
        "unit": "k jobs",
        "category": "US Labor Market",
        "description": "Monthly change in U.S. nonfarm payroll employment in thousands (U.S. BLS Employment Situation).",
    },
    "dxy_index": {
        "name": "U.S. Dollar Index (DXY)",
        "unit": "pts",
        "category": "US Exchange Rates",
        "description": "U.S. Dollar Index measuring the relative value of the USD against a basket of major world currencies.",
    },
    "eur_usd": {
        "name": "EUR/USD Exchange Rate",
        "unit": "USD",
        "category": "US Exchange Rates",
        "description": "Exchange rate of the euro against the US dollar (world's largest FX pair).",
    },
    "usd_jpy": {
        "name": "USD/JPY Exchange Rate",
        "unit": "JPY",
        "category": "US Exchange Rates",
        "description": "Exchange rate of the US dollar against the Japanese yen.",
    },
    "gbp_usd": {
        "name": "GBP/USD Exchange Rate",
        "unit": "USD",
        "category": "US Exchange Rates",
        "description": "Exchange rate of the British pound against the US dollar (Cable).",
    },
    "usd_pln": {
        "name": "USD/PLN Exchange Rate",
        "unit": "PLN",
        "category": "US Exchange Rates",
        "description": "Exchange rate of the US dollar against the Polish zloty.",
    },
    "usd_chf": {
        "name": "USD/CHF Exchange Rate",
        "unit": "CHF",
        "category": "US Exchange Rates",
        "description": "Exchange rate of the US dollar against the Swiss franc.",
    },
    "us_public_debt_usd_bn": {
        "name": "US Federal Public Debt",
        "unit": "USD bn",
        "category": "US Fiscal Policy",
        "description": "Total gross federal public debt of the United States (Total Public Debt Outstanding).",
    },
    "us_public_debt_gdp_pct": {
        "name": "US Federal Debt to GDP",
        "unit": "% GDP",
        "category": "US Fiscal Policy",
        "description": "Ratio of U.S. federal public debt to nominal GDP in %.",
    },
    "us_budget_deficit_usd_bn": {
        "name": "US Federal Budget Balance",
        "unit": "USD bn",
        "category": "US Fiscal Policy",
        "description": "Quarterly federal budget balance of the United States (deficit is negative) in billions of USD.",
    },
    "us_10y": {
        "name": "10Y US Treasury Yield (Benchmark)",
        "unit": "%",
        "category": "US Bond Market",
        "description": "Yield to maturity on the 10-year benchmark U.S. Treasury Note (global benchmark).",
    },
    "us_2y": {
        "name": "2Y US Treasury Yield",
        "unit": "%",
        "category": "US Bond Market",
        "description": "Yield to maturity on the 2-year U.S. Treasury Note (short end sensitive to Fed policy).",
    },
    "us_5y": {
        "name": "5Y US Treasury Yield",
        "unit": "%",
        "category": "US Bond Market",
        "description": "Yield to maturity on the 5-year U.S. Treasury Note (middle segment of the US curve).",
    },
    "us_30y": {
        "name": "30Y US Treasury Bond Yield",
        "unit": "%",
        "category": "US Bond Market",
        "description": "Yield to maturity on the 30-year U.S. Treasury Long Bond.",
    },
    "us_spread_10y_2y": {
        "name": "US Curve Slope (10Y − 2Y)",
        "unit": "pp",
        "category": "US Bond Market",
        "description": "Spread between 10Y and 2Y U.S. Treasury yields (primary global recession indicator when inverted).",
    },
    "us_ism_manufacturing": {
        "name": "US ISM Manufacturing PMI",
        "unit": "pts",
        "category": "US Leading Indicators",
        "description": "Purchasing Managers' Index in U.S. manufacturing by the Institute for Supply Management (ISM). 50 separates expansion from contraction.",
    },
    "us_ism_services": {
        "name": "US ISM Services PMI",
        "unit": "pts",
        "category": "US Leading Indicators",
        "description": "Purchasing Managers' Index in the U.S. services sector by the Institute for Supply Management (ISM Non-Manufacturing PMI).",
    },
    "us_michigan_sentiment": {
        "name": "US Consumer Sentiment (Univ. of Michigan)",
        "unit": "pts",
        "category": "US Leading Indicators",
        "description": "University of Michigan Consumer Sentiment Index measuring confidence and expectations of U.S. households.",
    },
    "us_hourly_earnings_yoy": {
        "name": "US Average Hourly Earnings (YoY)",
        "unit": "%",
        "category": "US Labor Market",
        "description": "Year-on-year growth in average hourly earnings of all private nonfarm employees in the US (U.S. Bureau of Labor Statistics).",
    },
    "vix_index": {
        "name": "Cboe Volatility Index (VIX)",
        "unit": "pts",
        "category": "Market Sentiment & Risk",
        "description": "Cboe Volatility Index ('Fear Index') measuring market expectations of 30-day implied volatility on S&P 500 index options.",
    },
    "px_index": {
        "name": "PX Index (Prague Stock Exchange)",
        "unit": "pts",
        "category": "Equity Markets",
        "description": "Official price index of the Prague Stock Exchange (PSE) comprising leading Czech blue-chip equities (CEZ, Komercni banka, Erste, Moneta).",
    },
    "stoxx50_index": {
        "name": "Euro Stoxx 50",
        "unit": "pts",
        "category": "Equity Markets",
        "description": "Leading European blue-chip equity index of 50 sector leaders across 8 Eurozone countries (STOXX Ltd.).",
    },
    "sp500_index": {
        "name": "S&P 500 Index",
        "unit": "pts",
        "category": "Equity Markets",
        "description": "Standard & Poor's 500 – flagship U.S. equity market benchmark representing 500 leading publicly traded U.S. companies.",
    },
    "nasdaq_index": {
        "name": "NASDAQ Composite",
        "unit": "pts",
        "category": "Equity Markets",
        "description": "Flagship technology-heavy index of the NASDAQ stock exchange comprising over 3,000 U.S. and international companies.",
    },
    "gold_usd": {
        "name": "Gold",
        "unit": "USD/oz",
        "category": "Commodities",
        "description": "Spot / futures price of gold on COMEX in USD per troy ounce (31.1035 g). Traditional global safe haven, store of value, and hedge against inflation and geopolitical risk.",
    },
    "oil_brent_usd": {
        "name": "Brent Crude Oil",
        "unit": "USD/bbl",
        "category": "Commodities",
        "description": "North Sea Brent sweet light crude oil (ICE Futures Europe) in USD per barrel (159 liters). Global energy benchmark and key driver of cost-push inflation and fuel prices.",
    },
    "natgas_usd": {
        "name": "Natural Gas (Henry Hub)",
        "unit": "USD/MMBtu",
        "category": "Commodities",
        "description": "Benchmark price of natural gas at the U.S. Henry Hub (NYMEX) in USD per million British thermal units (MMBtu). Key input for power generation, industry, and heating.",
    },
    "copper_usd": {
        "name": "Copper (Doctor Copper)",
        "unit": "USD/lb",
        "category": "Commodities",
        "description": "Benchmark price of electrolytic copper on COMEX in USD per pound (0.4536 kg). Known as 'Doctor Copper' – leading barometer of global industry, construction, power grids, and electrification.",
    },
    "silver_usd": {
        "name": "Silver",
        "unit": "USD/oz",
        "category": "Commodities",
        "description": "Price of physical silver on COMEX in USD per troy ounce. Dual-purpose metal combining strong industrial demand (photovoltaics, electronics, EVs) with precious metal investment demand.",
    },
}


# =====================================================================
# 2. EXACT & PHRASE TRANSLATION DICTIONARIES (CS -> EN)
# =====================================================================

EXACT_TRANSLATIONS = {
    # Economies & Top Bar
    "🇨🇿 Česká republika": "🇨🇿 Czech Republic",
    "🇪🇺 Evropská unie (Eurozóna)": "🇪🇺 European Union (Eurozone)",
    "🇺🇸 Spojené státy (USA)": "🇺🇸 United States (USA)",
    "🇨🇿 ČR": "🇨🇿 CZ",
    "🇪🇺 EU": "🇪🇺 EU",
    "🇺🇸 USA": "🇺🇸 USA",
    "🖥️ PC": "🖥️ PC",
    "📱 Mobil": "📱 Mobile",
    "🖥️ Přepnout na PC verzi": "🖥️ Switch to PC version",
    "Makroekonomický přehled ČR": "Macroeconomic Monitor",
    "Makro Monitor": "Macro Monitor",
    "Přehled klíčových makroekonomických ukazatelů České republiky, Evropské unie a USA": "Overview of key macroeconomic indicators of the Czech Republic, European Union, and USA",
    "ČNB (ARAD) • ČSÚ • ECB • Eurostat • Fed (FRED) • MF ČR": "CNB (ARAD) • CZSO • ECB • Eurostat • Fed (FRED) • MoF CZ",
    # Main Tabs (PC & Mobile)
    "📈Sazby & Inflace": "📈Rates & Inflation",
    "📊HDP & Aktivita": "📊GDP & Activity",
    "👷Trh práce": "👷Labor Market",
    "💱Devizové kurzy & Dluh": "💱FX & Public Debt",
    "🏛️Trhy & Sentiment": "🏛️Markets & Sentiment",
    "📚Vysvětlivky": "📚Glossary",
    "📋Katalog & Export": "📋Catalog & Export",
    "📈 Sazby": "📈 Rates",
    "📊 HDP": "📊 GDP",
    "👷 Práce": "👷 Labor",
    "💱 FX & Dluh": "💱 FX & Debt",
    "🏛️ Trhy": "🏛️ Markets",
    "📚 Pojmy": "📚 Glossary",
    "📋 Katalog": "📋 Catalog",
    # Sub-tabs
    "🏦 Sazby & Inflace": "🏦 Rates & Inflation",
    "📈 Peněžní trh & PRIBOR": "📈 Money Market & PRIBOR",
    "📈 Peněžní trh & EURIBOR": "📈 Money Market & EURIBOR",
    "📈 Peněžní trh & SOFR / T-Bills": "📈 Money Market & SOFR / T-Bills",
    "🏠 Hypotéky & Úvěry": "🏠 Mortgages & Loans",
    "📊 HDP & Zahraniční obchod": "📊 GDP & Foreign Trade",
    "📊 HDP Eurozóny": "📊 Eurozone GDP",
    "📊 HDP USA": "📊 US GDP",
    "🏭 Průmysl, Maloobchod & Stavebnictví": "🏭 Industry, Retail & Construction",
    "🏭 Průmysl & Maloobchod": "🏭 Industry & Retail",
    "👷 Nezaměstnanost (MPSV vs. ČSÚ)": "👷 Unemployment (MoLSA vs. CZSO)",
    "💰 Mzdy & Kupní síla": "💰 Wages & Purchasing Power",
    "💱 Devizové kurzy ČNB": "💱 CNB Exchange Rates",
    "💱 Kurzy Eura & DXY": "💱 Euro Rates & DXY",
    "💱 Dolarový index (DXY) & Kurzy USD": "💱 U.S. Dollar Index (DXY) & USD Rates",
    "🏛️ Veřejné finance & Dluh": "🏛️ Public Finance & Debt",
    "🏛️ Dluhopisy & Výnosová křivka": "🏛️ Bonds & Yield Curve",
    "🔮 Sentiment & PMI": "🔮 Sentiment & PMI",
    "🔮 Sentiment & ISM PMI": "🔮 Sentiment & ISM PMI",
    "📈 Akciové indexy & VIX": "📈 Equity Indices & VIX",
    "🛢️ Komodity (Zlato, Ropa, Plyn, Měď)": "🛢️ Commodities (Gold, Oil, Gas, Copper)",
    "📰 Zprávy z ČR (Finance & Politika)": "📰 Czech News (Finance & Policy)",
    "📋 Katalog indikátorů & Zdroje": "📋 Indicator Catalog & Sources",
    "💾 Datový náhled & Export": "💾 Data Preview & Export",
    "🏛️ Dluhopisy": "🏛️ Bonds",
    "🔮 Sentiment": "🔮 Sentiment",
    "📈 Akcie & VIX": "📈 Equities & VIX",
    "🛢️ Komodity": "🛢️ Commodities",
    "📰 Zprávy ČR": "📰 CZ News",
    "📋 Katalog & Zdroje": "📋 Catalog & Sources",
    "💾 Export dat": "💾 Data Export",
    "💱 Kurzy ČNB": "💱 CNB Rates",
    "💱 Kurzy EUR": "💱 EUR Rates",
    "💱 DXY & USD": "💱 DXY & USD",
    "🏛️ Dluh & Deficit": "🏛️ Debt & Deficit",
    "📊 HDP & Obchod": "📊 GDP & Trade",
    "🏭 Aktivita": "🏭 Activity",
    "👷 Nezaměstnanost": "👷 Unemployment",
    "💰 Mzdy": "💰 Wages",
    "📈 Peněžní trh": "📈 Money Market",
    "🏠 Hypotéky": "🏠 Mortgages",
    # Sidebar & Quick Settings
    "⚙️ Nastavení a filtry": "⚙️ Settings & Filters",
    "⚙️ Rychlé nastavení (Období, Aktualizace dat)": "⚙️ Quick Settings (Period, Data Refresh)",
    "🌍 Ekonomika / Region": "🌍 Economy / Region",
    "Vyberte sledovanou ekonomiku": "Select monitored economy",
    "Přepíná celý dashboard mezi makroekonomickými daty České republiky (ČNB/ČSÚ), Eurozóny (ECB/Eurostat) a USA (Fed/FRED).": "Switches the entire dashboard between macroeconomic data of the Czech Republic (CNB/CZSO), Eurozone (ECB/Eurostat), and USA (Fed/FRED).",
    "📅 Časové období": "📅 Time Period",
    "Rychlý výběr období": "Quick Period Selection",
    "Od": "From",
    "Do": "To",
    "Od:": "From:",
    "Do:": "To:",
    "Období": "Period",
    "Poslední 1 rok": "Last 1 Year",
    "Poslední 3 roky": "Last 3 Years",
    "Posledních 5 let": "Last 5 Years",
    "Od roku 2020 (COVID + energetická krize)": "Since 2020 (COVID + Energy Crisis)",
    "Celá historie (od 2018)": "Full History (since 2018)",
    "Vlastní rozsah": "Custom Range",
    "1R": "1Y",
    "3R": "3Y",
    "5R": "5Y",
    "Od 2020": "Since 2020",
    "Vše (2018+)": "All (2018+)",
    "🔄 Aktualizovat všechna data": "🔄 Refresh All Data",
    "🔄 Obnovit živá data": "🔄 Refresh Live Data",
    "Stahuji čerstvá data z API...": "Fetching fresh data from APIs...",
    "Stahuji data...": "Fetching data...",
    "📚 Datové zdroje a API status": "📚 Data Sources & API Status",
    "📡 Zdroje dat a stav API": "📡 Data Sources & API Status",
    "Zobrazit orientační benchmarky při výpadku API": "Show fallback benchmarks on API outage",
    "Zobrazit orientační benchmarky (při výpadku API)": "Show fallback benchmarks (on API outage)",
    "Pokud některé API neodpovídá, zobrazí v grafech referenční historickou křivku s jasným upozorněním.": "If an API fails to respond, charts will display a reference historical curve with a clear notice.",
    "💡 Tip: Kliknutím do legendy grafu můžete jednotlivé křivky skrývat nebo zobrazovat. Dvojklikem vyfiltrujete pouze jedinou křivku.": "💡 Tip: Click on a chart legend item to show/hide individual series. Double-click to isolate a single series.",
    # Overview Expander
    "📋 Podrobný přehled hlavních ukazatelů (Minimum / Maximum / Průměr za vybrané období)": "📋 Detailed Overview of Key Indicators (Min / Max / Average over selected period)",
    "📋 Statistika hlavních ukazatelů (Min / Max / Průměr)": "📋 Key Indicators Statistics (Min / Max / Average)",
    # Widget options (format_func targets)
    "📈 Denní kurzy (detailní pohled)": "📈 Daily Rates (detailed view)",
    "📊 Měsíční průměry": "📊 Monthly Averages",
    "Denní detail": "Daily Detail",
    "Měsíční průměr": "Monthly Average",
    "📈 Relativní výkonnost (Zhodnocení v % od začátku období)": "📈 Relative Performance (% return from period start)",
    "🔢 Nominální hodnoty v bodech (Index začátek = 100 b.)": "🔢 Indexed Values in Points (Start = 100 pts)",
    "📊 Samostatné karty (Skutečné tržní body každého indexu)": "📊 Separate Cards (Actual market points for each index)",
    "Relativní (%)": "Relative (%)",
    "Index (100 b.)": "Indexed (100 pts)",
    "Všechny kategorie": "All Categories",
    "🇨🇿 PX Index (Pražská burza)": "🇨🇿 PX Index (Prague Stock Exchange)",
    "🇪🇺 Euro Stoxx 50 (Eurozóna)": "🇪🇺 Euro Stoxx 50 (Eurozone)",
    "🇺🇸 S&P 500 (USA)": "🇺🇸 S&P 500 (USA)",
    "🇺🇸 NASDAQ Composite (USA Tech)": "🇺🇸 NASDAQ Composite (USA Tech)",
    "🥇 Zlato (USD/oz)": "🥇 Gold (USD/oz)",
    "🛢️ Ropa Brent (USD/bbl)": "🛢️ Brent Crude Oil (USD/bbl)",
    "🔥 Zemní plyn (USD/MMBtu)": "🔥 Natural Gas (USD/MMBtu)",
    "🧱 Měď (USD/lb)": "🧱 Copper (USD/lb)",
    "🥈 Stříbro (USD/oz)": "🥈 Silver (USD/oz)",
    "🥇 Zlato": "🥇 Gold",
    "🛢️ Ropa Brent": "🛢️ Brent Oil",
    "🔥 Zemní plyn": "🔥 Natural Gas",
    "🧱 Měď": "🧱 Copper",
    "🥈 Stříbro": "🥈 Silver",
    "CZK / EUR": "CZK / EUR",
    "CZK / USD": "CZK / USD",
    "CZK / GBP": "CZK / GBP",
    "CZK / PLN": "CZK / PLN",
    "CZK / CHF": "CZK / CHF",
    "EUR / USD": "EUR / USD",
    "EUR / GBP": "EUR / GBP",
    "EUR / CHF": "EUR / CHF",
    "EUR / JPY": "EUR / JPY",
    "USD / JPY": "USD / JPY",
    "GBP / USD": "GBP / USD",
    "USD / PLN": "USD / PLN",
    "USD / CHF": "USD / CHF",
}

PHRASE_REPLACEMENTS = [
    # Longer phrases first so they match before shorter substrings
    ("Makroekonomický přehled ČR", "Macroeconomic Monitor"),
    ("Česká republika", "Czech Republic"),
    ("Evropská unie (Eurozóna)", "European Union (Eurozone)"),
    ("Spojené státy (USA)", "United States (USA)"),
    ("Eurozóna / EU", "Eurozone / EU"),
    ("Eurozóny", "Eurozone"),
    ("Eurozóně", "Eurozone"),
    ("Eurozóna", "Eurozone"),
    ("České republiky", "Czech Republic"),
    ("v České republice", "in the Czech Republic"),
    ("v ČR", "in CZ"),
    ("pro ČR", "for CZ"),
    # Hero strip labels & units
    ("2T Repo ČNB", "CNB 2W Repo"),
    ("Inflace (CPI YoY)", "Inflation (CPI YoY)"),
    ("HDP reálně (YoY)", "Real GDP (YoY)"),
    ("Nezaměstnanost", "Unemployment"),
    ("Kurz EUR / CZK", "EUR / CZK Rate"),
    ("Kurz EUR / USD", "EUR / USD Rate"),
    ("Výnos 10Y CZGB", "10Y CZGB Yield"),
    ("Výnos 10Y Bund", "10Y Bund Yield"),
    ("Výnos 10Y UST", "10Y UST Yield"),
    ("ECB Depozitní", "ECB Deposit Rate"),
    ("Inflace (HICP YoY)", "Inflation (HICP YoY)"),
    ("Fed Funds (horní)", "Fed Funds (Upper)"),
    ("Inflace (US CPI)", "Inflation (US CPI)"),
    ("Měnová politika ČNB", "CNB Monetary Policy"),
    ("Měnová politika ECB", "ECB Monetary Policy"),
    ("Měnová politika Fedu", "Fed Monetary Policy"),
    ("Index spotřebitelských cen", "Consumer Price Index"),
    ("Harmonizovaný index HICP", "Harmonised HICP Index"),
    ("US Consumer Price Index", "US Consumer Price Index"),
    ("Hrubý domácí produkt", "Gross Domestic Product"),
    ("HDP Eurozóny (Eurostat)", "Eurozone GDP (Eurostat)"),
    ("HDP USA (BEA)", "US GDP (BEA)"),
    ("Podíl nezaměstnaných (MPSV)", "Share of Unemployed (MoLSA)"),
    ("Harmonizovaná míra (ILO)", "Harmonised Rate (ILO)"),
    ("Míra nezaměstnanosti U-3", "U-3 Unemployment Rate"),
    ("Devizový trh (fixing ČNB)", "FX Market (CNB Fixing)"),
    ("Devizový trh (ECB fixing)", "FX Market (ECB Fixing)"),
    ("Globální devizový trh", "Global FX Market"),
    ("Český státní dluhopis 10L", "Czech 10Y Gov. Bond"),
    ("Německý státní dluhopis 10L", "German 10Y Bund"),
    ("Americký státní dluhopis 10L", "US 10Y Treasury Note"),
    ("Beze změny", "Unchanged"),
    ("předch.", "prev."),
    # Overview table headers
    ("Ukazatel", "Indicator"),
    ("Kategorie", "Category"),
    ("Poslední hodnota", "Latest Value"),
    ("Aktuální hodnota", "Current Value"),
    ("Předchozí", "Previous"),
    ("Změna", "Change"),
    ("Minimum (období)", "Minimum (Period)"),
    ("Maximum (období)", "Maximum (Period)"),
    ("Průměr (období)", "Average (Period)"),
    ("Jednotka", "Unit"),
    ("Frekvence", "Frequency"),
    ("Zdroj dat", "Data Source"),
    ("Kód / Sazba", "Code / Series"),
    ("Metodický popis", "Methodological Description"),
    ("Stav dat", "Data Status"),
    ("Poslední datum", "Latest Date"),
    ("Kód", "Code"),
    ("Název ukazatele", "Indicator Name"),
    ("Hodnota", "Value"),
    ("Období", "Period"),
    ("Zdroj", "Source"),
    # Frequencies
    ("Denní (po rozhodnutí)", "Daily (post-decision)"),
    ("Denní (pracovní dny)", "Daily (business days)"),
    ("Měsíční", "Monthly"),
    ("Čtvrtletní", "Quarterly"),
    ("Denní", "Daily"),
    ("Roční", "Annual"),
    # Units
    ("Kč/EUR", "CZK/EUR"),
    ("Kč/USD", "CZK/USD"),
    ("Kč/GBP", "CZK/GBP"),
    ("Kč/PLN", "CZK/PLN"),
    ("Kč/CHF", "CZK/CHF"),
    ("mld. Kč", "CZK bn"),
    ("mld. EUR", "EUR bn"),
    ("mld. USD", "USD bn"),
    ("% HDP", "% GDP"),
    ("tis. osob", "k persons"),
    ("tis. míst", "k jobs"),
    ("bodů", "pts"),
    ("b.", "pts"),
    ("Kč", "CZK"),
    # Common Metric Deltas & Tooltips
    ("Neutrální (50 b.)", "Neutral (50 pts)"),
    ("Neutrální = 50 b.", "Neutral = 50 pts"),
    ("Neutrální = 100 b.", "Neutral = 100 pts"),
    ("Dlouhodobý průměr = 100 b.", "Long-term avg = 100 pts"),
    ("Cíl ČNB: 2,0 %", "CNB Target: 2.0%"),
    ("Cíl ECB: 2,0 %", "ECB Target: 2.0%"),
    ("Cíl Fedu: 2,0 %", "Fed Target: 2.0%"),
    ("Cíl 2,0 %", "Target 2.0%"),
    ("2% cíl ČNB", "2% CNB Target"),
    ("2% cíl ECB", "2% ECB Target"),
    ("2% cíl Fedu", "2% Fed Target"),
    ("Maastrichtský limit: 60 % HDP", "Maastricht limit: 60% GDP"),
    ("Maastricht 60 % HDP", "Maastricht 60% GDP"),
    ("Kladná = kladný reálný výnos", "Positive = positive real yield"),
    ("Záporná = inflace převyšuje repo", "Negative = inflation exceeds repo"),
    ("Záporná = inflace převyšuje sazbu", "Negative = inflation exceeds rate"),
    ("Normální sklon křivky", "Normal curve slope"),
    ("Inverze výnosové křivky!", "Yield curve inversion!"),
    ("Inverze křivky!", "Curve inversion!"),
    ("Inverze křivky (< 0)", "Curve inversion (< 0)"),
    ("Kladné = zvýhodnění úspor v CZK", "Positive = CZK carry advantage"),
    ("Záporné = nižší sazby než v EA", "Negative = lower rates than EA"),
    ("Přebytek (export > import)", "Surplus (export > import)"),
    ("Schodek (import > export)", "Deficit (import > export)"),
    ("Kladný reálný růst", "Positive real growth"),
    ("Pokles reálné kupní síly", "Real purchasing power decline"),
    ("Pásmo expanze (> 50 b.)", "Expansion zone (> 50 pts)"),
    ("Pásmo kontrakce (< 50 b.)", "Contraction zone (< 50 pts)"),
    ("Expanze (> 50)", "Expansion (> 50)"),
    ("Kontrakce (< 50)", "Contraction (< 50)"),
    ("Expanze (>50)", "Expansion (>50)"),
    ("Kontrakce (<50)", "Contraction (<50)"),
    ("Nad průměrem (> 100 b.)", "Above average (> 100 pts)"),
    ("Pod průměrem (< 100 b.)", "Below average (< 100 pts)"),
    ("Nad průměrem (>100)", "Above average (>100)"),
    ("Pod průměrem (<100)", "Below average (<100)"),
    ("Nízká volatilita (klid na trzích)", "Low volatility (calm markets)"),
    ("Zvýšená nervozita na trzích", "Elevated market nervousness"),
    ("Vysoká volatilita / panika!", "High volatility / market panic!"),
    ("Klid (<20)", "Calm (<20)"),
    ("Nervozita", "Nervousness"),
    ("Panika (≥30)", "Panic (≥30)"),
    ("Historický rozsah:", "Historical range:"),
    ("Za vybrané období", "Over selected period"),
    ("za vybrané období", "over selected period"),
    ("od začátku období", "since period start"),
    ("Meziročně:", "YoY:"),
    ("Meziročně", "Year-on-Year"),
    ("Meziměsíčně", "Month-on-Month"),
    ("Mezičtvrtletně", "Quarter-on-Quarter"),
    ("Kumulativní změna:", "Cumulative change:"),
    ("Kumulativní:", "Cumulative:"),
    ("Průměr za vybrané období:", "Average over period:"),
    ("Průměr v období:", "Period average:"),
    ("Průměr:", "Average:"),
    ("Medián:", "Median:"),
    ("Max v období:", "Period max:"),
    ("Min v období:", "Period min:"),
    ("Rozpětí (Max - Min):", "Range (Max - Min):"),
    ("1M změna:", "1M change:"),
    ("3M změna:", "3M change:"),
    ("1Y změna:", "1Y change:"),
    ("Denní změna:", "Daily change:"),
    ("Poslední změna:", "Last change:"),
    ("Poslední hodnota:", "Latest value:"),
    ("předchozí:", "previous:"),
    ("předchozí", "previous"),
    ("beze změny", "unchanged"),
    # Section Headers & Subtitles
    ("Sazby centrální banky, inflace a úvěrový trh", "Central Bank Rates, Inflation & Credit Market"),
    ("Sazby ECB, inflace HICP a peněžní trh Eurozóny", "ECB Rates, HICP Inflation & Eurozone Money Market"),
    ("Sazby Fedu, inflace CPI a peněžní trh USA", "Fed Rates, CPI Inflation & US Money Market"),
    ("Přehled klíčových úrokových sazeb ČNB", "Overview of Key CNB Interest Rates"),
    ("Přehled klíčových úrokových sazeb ECB", "Overview of Key ECB Interest Rates"),
    ("Přehled klíčových sazeb Fedu a inflace v USA", "Overview of Key Fed Rates & US Inflation"),
    ("Vývoj úrokových sazeb ČNB a inflace (CPI)", "CNB Interest Rates & Inflation (CPI) Evolution"),
    ("Vývoj úrokových sazeb ECB a inflace (HICP)", "ECB Interest Rates & Inflation (HICP) Evolution"),
    ("Vývoj sazeb Fedu (Fed Funds) a inflace v USA (CPI)", "Fed Funds Rates & US Inflation (CPI) Evolution"),
    ("Srovnání měnověpolitických sazeb ČNB a meziroční míry inflace v ČR", "Comparison of CNB monetary policy rates and YoY inflation in CZ"),
    ("Měnověpolitické sazby ČNB (2T Repo, Diskontní, Lombardní)", "CNB Monetary Policy Rates (2W Repo, Discount, Lombard)"),
    ("Inflace v ČR: Celková (CPI) vs. Jádrová vs. HICP", "Inflation in CZ: Headline (CPI) vs. Core vs. HICP"),
    ("Inflace v Eurozóně: Celková (HICP) vs. Jádrová inflace", "Eurozone Inflation: Headline (HICP) vs. Core Inflation"),
    ("Inflace v USA: Celková (Headline CPI) vs. Jádrová (Core CPI)", "US Inflation: Headline CPI vs. Core CPI"),
    ("Reálná úroková sazba v ČR (Ex-post: 2T Repo − CPI)", "Real Interest Rate in CZ (Ex-post: 2W Repo − CPI)"),
    ("Reálná úroková sazba v Eurozóně (ECB Depozitní − HICP)", "Real Interest Rate in Eurozone (ECB Deposit − HICP)"),
    ("Reálná úroková sazba v USA (Fed Funds − US CPI)", "Real Interest Rate in the US (Fed Funds − US CPI)"),
    ("Mezibankovní sazby PRIBOR a úrokový diferenciál", "PRIBOR Interbank Rates & Interest Rate Differential"),
    ("Evropský peněžní trh: EURIBOR a €STR", "European Money Market: EURIBOR & €STR"),
    ("Americký peněžní trh: SOFR, EFFR a T-Bills", "US Money Market: SOFR, EFFR & T-Bills"),
    ("Hypoteční trh a úrokové sazby úvěrů v ČR", "Mortgage Market & Loan Interest Rates in CZ"),
    ("Hospodářský růst (HDP), průmysl, maloobchod a obchodní bilance", "Economic Growth (GDP), Industry, Retail & Trade Balance"),
    ("Hospodářský růst (HDP), průmysl a maloobchod v Eurozóně", "Economic Growth (GDP), Industry & Retail in the Eurozone"),
    ("Hospodářský růst (HDP), průmysl a maloobchod v USA", "Economic Growth (GDP), Industry & Retail in the US"),
    ("Meziroční růst reálného HDP (%)", "Real GDP Growth YoY (%)"),
    ("Nominální HDP (mld. Kč, běžné ceny)", "Nominal GDP (CZK bn, current prices)"),
    ("Nominální HDP Eurozóny (mld. EUR)", "Eurozone Nominal GDP (EUR bn)"),
    ("Nominální HDP USA (mld. USD)", "US Nominal GDP (USD bn)"),
    ("Bilance zahraničního obchodu ČR se zbožím (mld. Kč)", "CZ Foreign Trade Balance in Goods (CZK bn)"),
    ("Průmyslová produkce, maloobchodní tržby a stavebnictví (YoY %)", "Industrial Production, Retail Sales & Construction (YoY %)"),
    ("Průmyslová produkce a maloobchodní tržby (YoY %)", "Industrial Production & Retail Sales (YoY %)"),
    ("Trh práce, nezaměstnanost a vývoj mezd", "Labor Market, Unemployment & Wage Evolution"),
    ("Míra nezaměstnanosti a volná pracovní místa v ČR", "Unemployment Rate & Job Vacancies in CZ"),
    ("Trh práce v Eurozóně: Nezaměstnanost a vyjednané mzdy", "Eurozone Labor Market: Unemployment & Negotiated Wages"),
    ("Trh práce v USA: Nezaměstnanost (U-3), Nonfarm Payrolls (NFP) a mzdy", "US Labor Market: Unemployment (U-3), Nonfarm Payrolls (NFP) & Earnings"),
    ("Průměrná hrubá mzda a reálný růst mezd v ČR", "Average Gross Wage & Real Wage Growth in CZ"),
    ("Nominální vs. Reálný meziroční růst mezd v ČR (%)", "Nominal vs. Real Wage Growth in CZ YoY (%)"),
    ("Průměrná hrubá měsíční mzda v ČR (Kč)", "Average Gross Monthly Wage in CZ (CZK)"),
    ("Devizové kurzy a veřejné finance (Státní dluh a rozpočet)", "Exchange Rates & Public Finance (Public Debt & Budget)"),
    ("Devizové kurzy ČNB (CZK vůči hlavním světovým měnám)", "CNB Exchange Rates (CZK against major currencies)"),
    ("Devizové kurzy Eura (ECB) a Dolarový index", "Euro Exchange Rates (ECB) & U.S. Dollar Index"),
    ("Dolarový index (DXY) a hlavní měnové páry USD", "U.S. Dollar Index (DXY) & Major USD Currency Pairs"),
    ("Režim zobrazení kurzů:", "Exchange rate display mode:"),
    ("Vyberte měnový pár pro detailní graf:", "Select currency pair for detailed chart:"),
    ("Srovnání relativní změny kurzů", "Relative Exchange Rate Performance Comparison"),
    ("Veřejné finance, státní dluh a saldo rozpočtu", "Public Finance, Government Debt & Budget Balance"),
    ("Státní dluh a saldo státního rozpočtu ČR", "Czech Government Debt & State Budget Balance"),
    ("Vládní dluh a rozpočtový deficit v Eurozóně", "Government Debt & Budget Deficit in the Eurozone"),
    ("Federální dluh a rozpočtový deficit USA", "US Federal Debt & Budget Deficit"),
    ("Dluhopisy, předstihové indikátory, akcie, komodity a zprávy", "Bonds, Leading Indicators, Equities, Commodities & News"),
    ("Státní dluhopisy a tvar výnosové křivky", "Government Bonds & Yield Curve Shape"),
    ("České státní dluhopisy (CZGB) a výnosová křivka", "Czech Government Bonds (CZGB) & Yield Curve"),
    ("Dluhopisy Eurozóny (Německý Bund) a rizikový spread BTP-Bund", "Eurozone Bonds (German Bund) & BTP-Bund Risk Spread"),
    ("Americké státní dluhopisy (US Treasuries) a sklon křivky (10Y-2Y)", "U.S. Treasuries & Yield Curve Slope (10Y-2Y)"),
    ("Aktuální tvar výnosové křivky (Snapshot)", "Current Yield Curve Shape (Snapshot)"),
    ("Tvar výnosové křivky (Snapshot podle splatností)", "Yield Curve Shape (Snapshot by Maturity)"),
    ("Vývoj výnosů státních dluhopisů v čase", "Government Bond Yields Evolution Over Time"),
    ("Sklon výnosové křivky (Spread 10Y − 2Y)", "Yield Curve Slope (10Y − 2Y Spread)"),
    ("Předstihové indikátory: PMI ve výrobě a ekonomický sentiment", "Leading Indicators: Manufacturing PMI & Economic Sentiment"),
    ("Předstihové indikátory Eurozóny: PMI a spotřebitelská důvěra", "Eurozone Leading Indicators: PMI & Consumer Confidence"),
    ("Předstihové indikátory USA: ISM PMI a spotřebitelský sentiment Michigan", "US Leading Indicators: ISM PMI & Michigan Consumer Sentiment"),
    (" Globální a regionální akciové indexy & Index strachu VIX", " Global & Regional Equity Indices & VIX Fear Index"),
    ("Akciové trhy (PX, Euro Stoxx 50, S&P 500, NASDAQ) a VIX", "Equity Markets (PX, Euro Stoxx 50, S&P 500, NASDAQ) & VIX"),
    ("Vyberte akciové indexy pro porovnání:", "Select equity indices for comparison:"),
    ("Režim zobrazení akciových indexů:", "Equity indices display mode:"),
    ("Index strachu VIX (Cboe Volatility Index – implikovaná volatilita S&P 500)", "VIX Fear Index (Cboe Volatility Index – S&P 500 implied volatility)"),
    ("Globální komoditní trhy (Zlato, Ropa Brent, Zemní plyn, Měď, Stříbro)", "Global Commodity Markets (Gold, Brent Oil, Natural Gas, Copper, Silver)"),
    ("Vyberte komodity pro porovnání v grafu:", "Select commodities for chart comparison:"),
    ("Režim zobrazení komoditního grafu:", "Commodity chart display mode:"),
    ("Přehled klíčových komodit (Spot / Futures ceny, změny a pásmo za období)", "Key Commodities Overview (Spot / Futures prices, changes & period range)"),
    ("Poměr ceny Zlato / Ropa Brent (Gold-to-Oil Ratio)", "Gold-to-Oil Price Ratio (Gold / Brent)"),
    ("Poměr ceny Zlato / Stříbro (Gold-to-Silver Ratio)", "Gold-to-Silver Price Ratio (Gold / Silver)"),
    ("Makroekonomické a finanční zpravodajství z ČR", "Czech Macroeconomic & Financial News"),
    ("Přehled klíčových událostí, měnové politiky ČNB, rozpočtu a ekonomiky ČR", "Overview of key events, CNB monetary policy, state budget, and Czech economy"),
    ("Filtrovat zprávy podle tématu:", "Filter news by topic:"),
    ("Hledat ve zprávách:", "Search news:"),
    ("Všechna témata", "All Topics"),
    ("Oficiální informační zdroje a kalendář institucí", "Official Information Sources & Institutional Links"),
    ("Přímé odkazy na zpravodajské sekce a analýzy klíčových českých institucí:", "Direct links to news sections and analyses of key Czech institutions:"),
    ("Kompletní katalog sledovaných indikátorů", "Complete Catalog of Monitored Indicators"),
    ("Filtrovat podle kategorie:", "Filter by category:"),
    ("Hledat indikátor (název, kód, popis):", "Search indicator (name, code, description):"),
    ("Náhled dat a export do CSV", "Data Preview & CSV Export"),
    ("Vyberte sadu dat pro zobrazení a export:", "Select dataset for preview and export:"),
    ("📥 Stáhnout filtrovaná data (CSV)", "📥 Download Filtered Data (CSV)"),
    ("📥 Stáhnout kompletní databázi ČR + EU + USA (CSV)", "📥 Download Complete Database CZ + EU + USA (CSV)"),
    ("📥 Stáhnout CSV", "📥 Download CSV"),
    ("📥 Stáhnout vše (CSV)", "📥 Download All (CSV)"),
    # Chart legend & trace labels
    ("Pásmo 25–75 %", "25–75% Band"),
    ("Medián", "Median"),
    ("Průměr", "Average"),
    ("Aktuální křivka", "Current Curve"),
    ("Před 1 rokem", "1 Year Ago"),
    ("Před 6 měsíci", "6 Months Ago"),
    ("Neutrální hranice (50 b.)", "Neutral threshold (50 pts)"),
    ("Dlouhodobý průměr (100 b.)", "Long-term average (100 pts)"),
    ("Hranice klidu (20 b.)", "Calm threshold (20 pts)"),
    ("Hranice paniky (30 b.)", "Panic threshold (30 pts)"),
    ("Maastrichtské kritérium (60 % HDP)", "Maastricht criterion (60% GDP)"),
    ("Inflační cíl (2,0 %)", "Inflation target (2.0%)"),
    ("Toleranční pásmo ČNB (1–3 %)", "CNB tolerance band (1–3%)"),
    ("Reálná sazba (2T Repo − CPI)", "Real Rate (2W Repo − CPI)"),
    ("Reálná sazba (Depo − HICP)", "Real Rate (Depo − HICP)"),
    ("Reálná sazba (Fed − CPI)", "Real Rate (Fed − CPI)"),
    ("Kladný reálný výnos", "Positive real yield"),
    ("Záporný reálný výnos", "Negative real yield"),
    ("Expanze", "Expansion"),
    ("Kontrakce", "Contraction"),
    ("Recese / Inverze", "Recession / Inversion"),
    ("Normální sklon", "Normal slope"),
    ("Přebytek", "Surplus"),
    ("Schodek", "Deficit"),
    ("Otevřít článek", "Read article"),
    ("Zdroj:", "Source:"),
    ("Živá API data", "Live API Data"),
    ("Referenční benchmark", "Reference Benchmark"),
]

EXACT_TRANSLATIONS.update({
    # Actual Economy & Device Options in app.py / app_mobile.py
    "🇪🇺 Evropská unie": "🇪🇺 European Union",
    "🇺🇸 Spojené státy": "🇺🇸 United States",
    "💻 PC": "💻 PC",
    "Zvolte ekonomiku:": "Select economy:",
    "Zobrazení:": "Display mode:",
    "Od 2015": "Since 2015",
    "Vlastní": "Custom",
    "Měsíční": "Monthly",
    "Kvartální": "Quarterly",
    "📅 Měsíční (M)": "📅 Monthly (M)",
    "📊 Kvartální (Q)": "📊 Quarterly (Q)",
    "📅 Měsíční": "📅 Monthly",
    "📊 Kvartální": "📊 Quarterly",
    "Zvolte období:": "Select period:",
    "Od (měsíc/rok):": "From (MM/YYYY):",
    "Do (měsíc/rok):": "To (MM/YYYY):",
    "Agregace časové řady:": "Time series aggregation:",
    "Vynutit Fallback data (Offline režim)": "Force Fallback Data (Offline mode)",
    "Přepne dashboard na interní historický model bez volání externích REST API.": "Switches the dashboard to the internal historical model without calling external REST APIs.",
    "Volitelný FRED API Klíč:": "Optional FRED API Key:",
    "Pokud máte klíč k Federal Reserve Bank of St. Louis (FRED), můžete jej zde zadat.": "If you have a Federal Reserve Bank of St. Louis (FRED) API key, you can enter it here.",
    "🔄 Obnovit data (Vymazat cache)": "🔄 Refresh Data (Clear Cache)",
    "🔄 Obnovit živá data (Vymazat cache)": "🔄 Refresh Live Data (Clear Cache)",
    "ℹ️ Stav jednotlivých API endpointů": "ℹ️ Individual API Endpoints Status",
    "📊 Monitor": "📊 Monitor",
    "📊 Makro Monitor": "📊 Macro Monitor",
    "📖 Glosář pojmů": "📖 Glossary",
    "⬅️ Zpět na Makroekonomický Monitor": "⬅️ Back to Macroeconomic Monitor",
    "📖 Otevřít Výkladový glosář pro laiky": "📖 Open Layman's Explanatory Glossary",
    "📖 Prohlédnout kompletní Výkladový glosář makroekonomických pojmů přímo zde": "📖 View complete Macroeconomic Explanatory Glossary right here",
    "📊 Zobrazit detailní přehled indikátorů a metrik": "📊 Show Detailed Indicators & Metrics Overview",
    # Main Dashboard Tabs (app.py & app_mobile.py)
    "Měnová politika & FX": "Monetary Policy & FX",
    "Ekonomika & Práce": "Economy & Labor",
    "Akciové trhy": "Equity Markets",
    "Komodity": "Commodities",
    "Fiskál & Svět": "Fiscal & Global",
    "Export": "Export",
    "Metriky": "Metrics Catalog",
    # Sub-tabs in app.py & app_mobile.py
    "Sazby (ČNB)": "Rates (CNB)",
    "Sazby (ECB)": "Rates (ECB)",
    "Sazby (Fed)": "Rates (Fed)",
    "Výnosová křivka & Spready (CZ)": "Yield Curve & Spreads (CZ)",
    "Výnosová křivka & Spready (Bund)": "Yield Curve & Spreads (Bund)",
    "Výnosová křivka & Spready (US)": "Yield Curve & Spreads (US)",
    "Měnové kurzy (FX)": "Exchange Rates (FX)",
    "Bankovní sektor & Úvěry (ČR)": "Banking & Loans (CZ)",
    "Bankovní sektor & Úvěry (Eurozóna)": "Banking & Loans (Eurozone)",
    "Bankovní sektor & Úvěry (USA)": "Banking & Loans (USA)",
    "Předstihové ukazatele & Sentiment": "Leading Indicators & Sentiment",
    "HDP": "GDP",
    "Inflace (CPI)": "Inflation (CPI)",
    "Inflace (HICP)": "Inflation (HICP)",
    "Průmysl a spotřeba": "Industry & Consumption",
    "Trh práce & Mzdy": "Labor Market & Wages",
    "📊 Vzájemné srovnání indexů": "📊 Index Comparison",
    "🇨🇿 Index PX (Pražská burza)": "🇨🇿 PX Index (Prague Stock Exchange)",
    "🇪🇺 Euro Stoxx 50": "🇪🇺 Euro Stoxx 50",
    "🇺🇸 S&P 500": "🇺🇸 S&P 500",
    "🇺🇸 NASDAQ Composite": "🇺🇸 NASDAQ Composite",
    "⚡ Index volatility VIX (Tržní riziko)": "⚡ VIX Volatility Index (Market Risk)",
    "📊 Vzájemné srovnání komodit": "📊 Commodity Comparison",
    "🟡 Zlato (Gold)": "🟡 Gold",
    "🛢️ Ropa Brent": "🛢️ Brent Crude Oil",
    "🔥 Zemní plyn (Henry Hub)": "🔥 Natural Gas (Henry Hub)",
    "🔥 Zemní plyn": "🔥 Natural Gas",
    "🏗️ Měď (Doctor Copper)": "🏗️ Copper (Doctor Copper)",
    "🏗️ Měď (Copper)": "🏗️ Copper",
    "⚪ Stříbro (Silver)": "⚪ Silver",
    "Veřejný dluh": "Public Debt",
    "Vnější rovnováha & Zahraniční obchod (ČR)": "External Balance & Foreign Trade (CZ)",
    "Vnější rovnováha & Zahraniční obchod (Eurozóna)": "External Balance & Foreign Trade (Eurozone)",
    "Vnější rovnováha & Zahraniční obchod (USA)": "External Balance & Foreign Trade (USA)",
    "Mezinárodní srovnání": "International Comparison",
    # Radio / Multiselect options
    "📅 Denní data (High-Frequency)": "📅 Daily Data (High-Frequency)",
    "📊 Měsíční agregace": "📊 Monthly Aggregation",
    "📈 Relativní výkonnost (% od počátku období)": "📈 Relative Performance (% from period start)",
    "🔢 Rebase na bázi 100": "🔢 Rebase to 100",
    "Index PX (Praha)": "PX Index (Prague)",
    "Euro Stoxx 50 (EU)": "Euro Stoxx 50 (EU)",
    "S&P 500 (USA)": "S&P 500 (USA)",
    "NASDAQ (USA)": "NASDAQ (USA)",
    "Zlato (Gold)": "Gold",
    "Ropa Brent": "Brent Crude Oil",
    "Zemní plyn (Henry Hub)": "Natural Gas (Henry Hub)",
    "Měď (Doctor Copper)": "Copper (Doctor Copper)",
    "Stříbro (Silver)": "Silver",
    "Všechny země": "All Countries",
    "Filtrovat podle země:": "Filter by country:",
    "Filtrovat podle kategorie:": "Filter by category:",
    "🔍 Hledat v ukazatelích a zdrojích:": "🔍 Search indicators and sources:",
    "Zadejte název, kód nebo zdroj (např. inflace, PRIBOR, ČNB, HDP)...": "Enter name, code, or source (e.g. inflation, PRIBOR, CNB, GDP)...",
    "Zvolte měny ke zobrazení:": "Select currencies to display:",
    "Frekvence řady:": "Series frequency:",
    "Frekvence řady pro grafy:": "Series frequency for charts:",
    "Vyberte indexy ke srovnání v grafu:": "Select indices for chart comparison:",
    "Metrika normalizace:": "Normalization metric:",
    "Vyberte komodity ke srovnání v grafu:": "Select commodities for chart comparison:",
    "Metrika normalizace komodit:": "Commodity normalization metric:",
})

PHRASE_REPLACEMENTS.extend([
    # Header & Sidebar HTML
    ("MAKROEKONOMICKÝ & TRŽNÍ MONITOR", "MACROECONOMIC & MARKET MONITOR"),
    ("Institucionální analýza", "Institutional Analysis"),
    ("Akciové indexy", "Equity Indices"),
    ("Výnosové křivky", "Yield Curves"),
    ("Nastavení a filtry", "Settings & Filters"),
    ("ČR MACRO", "CZ MACRO"),
    ("Křivka", "Yield Curve"),
    ("🧭 Hlavní navigace", "🧭 Main Navigation"),
    ("📅 Časový horizont", "📅 Time Horizon"),
    ("📅 Vlastní časové rozpětí:", "📅 Custom Date Range:"),
    ("⏱️ Frekvence dat", "⏱️ Data Frequency"),
    ("✅ Všechny ukazatele aktivní", "✅ All Indicators Active"),
    ("Všechny časové řady jsou trvale zapnuty. Podrobný metodický přehled a zdroje dat naleznete v záložce", "All time series are permanently enabled. For a detailed methodological overview and data sources, see the"),
    ("Metriky", "Metrics Catalog"),
    ("⚙️ Zdroj dat & Server", "⚙️ Data Source & Server"),
    ("📅 Data aktuální k:", "📅 Data current as of:"),
    ("Denní kurzy & trhy:", "Daily FX & Markets:"),
    ("Poslední stažení:", "Last fetched:"),
    ("Čas aktualizace:", "Update timestamp:"),
    ("Režim:", "Mode:"),
    ("Chybové hlášky:", "Error messages:"),
    ("⚙️ Rychlé nastavení & Glosář", "⚙️ Quick Settings & Glossary"),
    ("📅 ČASOVÝ HORIZONT GRAFŮ:", "📅 CHART TIME HORIZON:"),
    ("⏱️ FREKVENCE DAT:", "⏱️ DATA FREQUENCY:"),
    # Hero Strip & Overview Card
    ("TRHY AKTIVNÍ", "MARKETS ACTIVE"),
    ("Spojené státy americké", "United States of America"),
    ("Evropská unie / Eurozóna", "European Union / Eurozone"),
    ("Evropská unie", "European Union"),
    ("Spojené státy", "United States"),
    ("Zobrazit detail metriky:", "View metric details:"),
    ("Trend posledních pozorování", "Recent observations trend"),
    ("10Y CZGB Výnos", "10Y CZGB Yield"),
    ("2Y CZGB Výnos", "2Y CZGB Yield"),
    ("Inflace ČR (CPI)", "CZ Inflation (CPI)"),
    ("Reálný růst HDP EU", "EU Real GDP Growth"),
    ("Reálný růst HDP USA", "US Real GDP Growth"),
    ("Reálný růst HDP", "Real GDP Growth"),
    ("Míra nezaměstnanosti", "Unemployment Rate"),
    ("Index PX (Praha)", "PX Index (Prague)"),
    ("Depozitní sazba ECB", "ECB Deposit Rate"),
    ("10Y Německý Bund", "10Y German Bund"),
    ("Inflace Eurozóny (HICP)", "Eurozone Inflation (HICP)"),
    ("Nezaměstnanost EU", "EU Unemployment"),
    ("Dolarový index DXY", "U.S. Dollar Index DXY"),
    ("Inflace USA (CPI)", "US Inflation (CPI)"),
    ("Nezaměstnanost USA (U-3)", "US Unemployment (U-3)"),
    ("Index S&P 500", "S&P 500 Index"),
    ("Cíl 2.0 %", "Target 2.0%"),
    ("stabilní", "stable"),
    ("**Čas aktualizace:**", "**Update Time:**"),
    ("**Režim:**", "**Mode:**"),
    ("Chybové hlášky: ", "Error messages: "),
    ("Data načtena", "Data loaded"),
    ("Živá data (API)", "Live Data (API)"),
    ("Kombinovaná data (API + Cache)", "Combined Data (API + Cache)"),
    ("Záložní lokální data", "Fallback Local Data"),
    ("denní:", "daily:"),
    ("měsíční:", "monthly:"),
    ("kvartální:", "quarterly:"),
    ("Aktuální", "Current"),
    # Detailed stats card rows
    ("2T Repo sazba ČNB", "CNB 2W Repo Rate"),
    ("Diskontní sazba (spodní koridor)", "Discount Rate (lower bound)"),
    ("Lombardní sazba (horní koridor)", "Lombard Rate (upper bound)"),
    ("PRIBOR 3M (referenční sazba)", "PRIBOR 3M (reference rate)"),
    ("Meziroční inflace CPI", "CPI Inflation (YoY)"),
    ("Jádrová inflace ČR (Core CPI)", "CZ Core Inflation (Core CPI)"),
    ("Maloobchodní tržby (Spotřeba YoY)", "Retail Sales (Consumption YoY)"),
    ("Průmyslová produkce (YoY)", "Industrial Production (YoY)"),
    ("Míra nezaměstnanosti (ILO)", "Unemployment Rate (ILO)"),
    ("Nejnižší v EU", "Lowest in EU"),
    ("Výnos 10Y CZGB (státní dluhopis)", "10Y CZGB Yield (gov. bond)"),
    ("Sklon křivky CZGB (10Y − 2Y)", "CZGB Curve Slope (10Y − 2Y)"),
    ("Veřejný dluh ČR (% HDP)", "CZ Public Debt (% GDP)"),
    ("< 60 % limit", "< 60% limit"),
    ("&lt; 60 % limit", "&lt; 60% limit"),
    ("Kvartální saldo rozpočtu", "Quarterly Budget Balance"),
    ("PMI v průmyslu ČR (S&P Global)", "CZ Manufacturing PMI (S&P Global)"),
    ("Důvěra konjunktury (ČSÚ)", "Economic Confidence (CZSO)"),
    ("Průměrná hrubá mzda (YoY)", "Average Gross Wage (YoY)"),
    ("Průměrná reálná mzda (YoY)", "Average Real Wage (YoY)"),
    ("Nové hypotéky (sazba & objem)", "New Mortgages (rate & volume)"),
    ("Korporátní úvěry & M2 (YoY)", "Corporate Loans & M2 (YoY)"),
    ("Běžný účet k HDP & Obchod ČSÚ", "Current Account % GDP & Trade"),
    ("Spread CZGB vs. Bund & ASW 10Y", "CZGB vs. Bund Spread & 10Y ASW"),
    ("Refinanční operace (MRO)", "Main Refinancing (MRO)"),
    ("Mezní zápůjční sazba ECB", "ECB Marginal Lending Rate"),
    ("Harmonizovaná inflace (HICP)", "Harmonised Inflation (HICP)"),
    ("Jádrová inflace EU (Core HICP)", "EU Core Inflation (Core HICP)"),
    ("Maloobchodní tržby EU (Spotřeba YoY)", "EU Retail Sales (Consumption YoY)"),
    ("Průmyslová produkce EU (YoY)", "EU Industrial Production (YoY)"),
    ("Průmyslová výroba EU (YoY)", "EU Industrial Production (YoY)"),
    ("Reálný růst HDP Eurozóny (YoY)", "Eurozone Real GDP Growth (YoY)"),
    ("Míra nezaměstnanosti v EU", "EU Unemployment Rate"),
    ("Sklon Bund křivky (10Y − 2Y)", "Bund Curve Slope (10Y − 2Y)"),
    ("Veřejný dluh Eurozóny k HDP", "Eurozone Public Debt to GDP"),
    ("Kvartální deficit vládních institucí", "Quarterly General Gov. Deficit"),
    ("Composite PMI Eurozóny", "Eurozone Composite PMI"),
    ("Německý Ifo index klimatu", "German Ifo Business Climate"),
    ("Sjednané mzdy Eurozóna (ECB YoY)", "Eurozone Negotiated Wages (ECB YoY)"),
    ("Rizikový spread 10Y BTP - Bund", "10Y BTP - Bund Risk Spread"),
    ("Běžný účet Eurozóny (% HDP)", "Eurozone Current Account (% GDP)"),
    ("Fed Funds Target (horní limit)", "Fed Funds Target (upper bound)"),
    ("Fed Funds Target (dolní limit)", "Fed Funds Target (lower bound)"),
    ("Efektivní sazba EFFR", "Effective Rate (EFFR)"),
    ("Spotřebitelská inflace (CPI Headline)", "Consumer Inflation (Headline CPI)"),
    ("Jádrová inflace USA (Core CPI)", "US Core Inflation (Core CPI)"),
    ("Maloobchodní tržby USA (Spotřeba YoY)", "US Retail Sales (Consumption YoY)"),
    ("Průmyslová produkce USA (YoY)", "US Industrial Production (YoY)"),
    ("Míra nezaměstnanosti (U-3)", "Unemployment Rate (U-3)"),
    ("Výnos 10Y US Treasury (Benchmark)", "10Y US Treasury Yield (Benchmark)"),
    ("Sklon US křivky (10Y − 2Y)", "US Curve Slope (10Y − 2Y)"),
    ("Federální dluh USA k HDP", "US Federal Debt to GDP"),
    ("Kvartální federální deficit", "Quarterly Federal Deficit"),
    ("Spotřebitelský sentiment Michigan", "Michigan Consumer Sentiment"),
    ("Průměrná hodinová mzda (YoY)", "Average Hourly Earnings (YoY)"),
    ("Index volatility VIX (Tržní riziko)", "VIX Volatility Index (Market Risk)"),
    ("Normální", "Normal"),
    ("Inverze", "Inversion"),
    ("Útlum", "Contraction"),
    # Section Headers & Metrics in Tabs 1-6
    ("Měnová politika ČNB a mezibankovní sazby PRIBOR", "CNB Monetary Policy & PRIBOR Interbank Rates"),
    ("2T Repo sazba", "2W Repo Rate"),
    ("Diskontní sazba", "Discount Rate"),
    ("Lombardní sazba", "Lombard Rate"),
    ("Hlavní nástroj stahování likvidity", "Primary liquidity absorption rate"),
    ("Úročení vkladů bank u ČNB", "Overnight deposit facility rate at CNB"),
    ("Úročení zápůjček likvidity", "Marginal lending facility rate at CNB"),
    ("Referenční tržní sazba", "Reference interbank market rate"),
    ("Měnová politika ECB a sazby EURIBOR / €STR", "ECB Monetary Policy & EURIBOR / €STR Rates"),
    ("Refinanční sazba MRO", "MRO Refinancing Rate"),
    ("Mezní sazba ECB", "ECB Marginal Lending Rate"),
    ("Měnová politika Federálního rezervního systému (Fed) & SOFR", "Federal Reserve (Fed) Monetary Policy & SOFR"),
    ("Výnosová křivka ČR (Státní dluhopisy CZGB & CZK IRS swapy)", "CZ Yield Curve (CZGB Gov. Bonds & CZK IRS Swaps)"),
    ("Sklon (10Y − 2Y)", "Slope (10Y − 2Y)"),
    ("Kreditní a swapové spready (CZGB vs. Bund & ASW 10Y CZK)", "Credit & Swap Spreads (CZGB vs. Bund & 10Y CZK ASW)"),
    ("Kreditní spread 10Y CZGB vs. 10Y Bund", "10Y CZGB vs. 10Y Bund Credit Spread"),
    ("Přirážka českého 10Y dluhopisu vůči německému Bundu", "Yield premium of 10Y Czech gov. bond over German Bund"),
    ("Rozdíl 10Y CZGB a sazby CZK IRS na mezibankovním trhu", "Spread between 10Y CZGB yield and 10Y CZK IRS rate"),
    ("Výnosová křivka Německých Bundů (Benchmark Eurozóny: 2Y–30Y)", "German Bund Yield Curve (Eurozone Benchmark: 2Y–30Y)"),
    ("Rizikový spread periferie Eurozóny: 10Y BTP (Itálie) vs. 10Y Bund (Německo)", "Eurozone Periphery Risk Spread: 10Y BTP (Italy) vs. 10Y Bund (Germany)"),
    ("Rizikový spread Itálie vs. Německo", "Italy vs. Germany Risk Spread"),
    ("10Y Německý Bund (Kotva)", "10Y German Bund (Anchor)"),
    ("10Y BTP Itálie (Implikovaný)", "10Y Italy BTP (Implied)"),
    ("Sledovaný práh ECB", "ECB Monitored Threshold"),
    ("Hranice aktivace nástroje TPI", "Transmission Protection Instrument (TPI) activation threshold"),
    ("Výnosová křivka USA (U.S. Treasury Par Yield Curve: 1M–30Y)", "US Yield Curve (U.S. Treasury Par Yield Curve: 1M–30Y)"),
    ("Devizové trhy a měnové kurzy (Denní & Měsíční data)", "Foreign Exchange Markets & Currency Rates (Daily & Monthly Data)"),
    ("Filtrujte zobrazené měny v grafu níže, aby byl přehledný a neobsahoval příliš mnoho překrývajících se křivek.", "Filter the currencies displayed in the chart below to keep the view clean and readable."),
    ("Vyberte měny, které se mají vykreslit do grafu.", "Select currencies to plot in the chart."),
    ("📥 Stáhnout kompletní denní data FX kurzů (CSV)", "📥 Download Complete Daily FX Rates Data (CSV)"),
    ("Bankovní sektor, hypoteční trh a měnová zásoba ČR", "Banking Sector, Mortgage Market & Money Supply in CZ"),
    ("Nové hypotéky – průměrná sazba", "New Mortgages – Average Rate"),
    ("Nové hypotéky – měsíční objem", "New Mortgages – Monthly Volume"),
    ("Korporátní úvěry (meziroční růst)", "Corporate Loans (YoY Growth)"),
    ("Měnový agregát M2 (meziročně)", "M2 Money Supply (YoY)"),
    ("Bankovní sektor a úvěrová dynamika v Eurozóně", "Banking Sector & Credit Dynamics in the Eurozone"),
    ("ECB Depozitní sazba (Kotva)", "ECB Deposit Rate (Anchor)"),
    ("Měnový agregát M3", "M3 Money Supply"),
    ("Růst +2.9 %", "Growth +2.9%"),
    ("Růst +2.6 %", "Growth +2.6%"),
    ("Kreditní standardy (BLS)", "Credit Standards (BLS)"),
    ("Neutrální", "Neutral"),
    ("Bankovní sektor, úvěry a měnová zásoba USA", "Banking Sector, Loans & Money Supply in the US"),
    ("SOFR sazba (Peněžní trh)", "SOFR Rate (Money Market)"),
    ("30Y Fixed Mortgage (USA průměr)", "30Y Fixed Mortgage (US Average)"),
    ("Předstihové ukazatele a sentiment ČR (PMI v průmyslu & Důvěra ČSÚ)", "Leading Indicators & Sentiment in CZ (Manufacturing PMI & CZSO Confidence)"),
    ("PMI v průmyslu ČR", "CZ Manufacturing PMI"),
    ("Důvěra podnikatelů a spotřebitelů", "Business & Consumer Confidence"),
    ("Práh expanze PMI", "PMI Expansion Threshold"),
    ("Práh expanze ISM", "ISM Expansion Threshold"),
    ("Dlouhodobý průměr sentimentu", "Long-Term Sentiment Average"),
    ("Ifo dlouhodobý průměr", "Ifo Long-Term Average"),
    ("Předstihové ukazatele Eurozóny a Německa (Composite PMI & Ifo index)", "Eurozone & German Leading Indicators (Composite PMI & Ifo Index)"),
    ("Předstihové ukazatele a spotřebitelský sentiment USA (ISM PMI & Michigan)", "US Leading Indicators & Consumer Sentiment (ISM PMI & Michigan)"),
    ("Spotřebitelský sentiment (Michigan)", "Consumer Sentiment (Michigan)"),
    ("Hrubý domácí produkt (HDP) České republiky", "Gross Domestic Product (GDP) of the Czech Republic"),
    ("Hrubý domácí produkt Eurozóny / Evropské unie", "Gross Domestic Product of the Eurozone / European Union"),
    ("Hrubý domácí produkt Spojených států (U.S. GDP)", "Gross Domestic Product of the United States (U.S. GDP)"),
    ("Reálný růst HDP (YoY)", "Real GDP Growth (YoY)"),
    ("Reálný růst HDP EU (YoY)", "EU Real GDP Growth (YoY)"),
    ("Reálný růst HDP USA (YoY)", "US Real GDP Growth (YoY)"),
    ("Kvartální nominální HDP", "Quarterly Nominal GDP"),
    ("Nominální HDP Eurozóny", "Eurozone Nominal GDP"),
    ("Nominální objem HDP USA", "US Nominal GDP Volume"),
    ("Průměrný růst v období", "Average Growth in Period"),
    ("Poslední kvartál", "Latest Quarter"),
    ("Spotřebitelská & jádrová inflace v ČR (CPI & Core CPI)", "Consumer & Core Inflation in CZ (CPI & Core CPI)"),
    ("Celková inflace (CPI YoY)", "Headline Inflation (CPI YoY)"),
    ("Jádrová inflace (Core CPI)", "Core Inflation (Core CPI)"),
    ("Sledováno ČNB", "Monitored by CNB"),
    ("Reálná úroková sazba Fedu", "Fed Real Interest Rate"),
    ("Reálná úroková sazba", "Real Interest Rate"),
    ("Reálná sazba ECB", "ECB Real Rate"),
    ("Inflační cíl ČNB", "CNB Inflation Target"),
    ("Inflační cíl ECB", "ECB Inflation Target"),
    ("Inflační cíl Fedu", "Fed Inflation Target"),
    ("Toleranční pásmo 1–3 %", "Tolerance band 1–3%"),
    ("Bez energií a potravin", "Excl. energy & food"),
    ("Bez potravin a energií", "Excl. food & energy"),
    ("Střednědobý cíl", "Medium-term target"),
    ("Harmonizovaná & jádrová inflace Eurozóny (HICP & Core HICP)", "Eurozone Harmonised & Core Inflation (HICP & Core HICP)"),
    ("Spotřebitelská & jádrová inflace v USA (Headline & Core CPI)", "US Consumer & Core Inflation (Headline & Core CPI)"),
    ("Ekonomická aktivita: Maloobchodní tržby (Spotřeba) & Průmyslová produkce", "Economic Activity: Retail Sales (Consumption) & Industrial Production"),
    ("Maloobchod ČR (Spotřeba YoY)", "CZ Retail Sales (Consumption YoY)"),
    ("Průmyslová produkce ČR (YoY)", "CZ Industrial Production (YoY)"),
    ("Průměrná spotřeba EU", "EU Average Consumption"),
    ("Průměrný průmysl EU", "EU Average Industry"),
    ("Průměrná spotřeba USA", "US Average Consumption"),
    ("Průměrný průmysl USA", "US Average Industry"),
    ("Průměrná spotřeba", "Average Consumption"),
    ("Průměrný průmysl", "Average Industry"),
    ("Maloobchod EU (Spotřeba YoY)", "EU Retail Sales (Consumption YoY)"),
    ("Maloobchod USA (Spotřeba YoY)", "US Retail Sales (Consumption YoY)"),
    ("Trh práce, nezaměstnanost a mzdový vývoj v ČR (Nominální vs. Reálné mzdy)", "Labor Market, Unemployment & Wage Evolution in CZ (Nominal vs. Real Wages)"),
    ("Míra nezaměstnanosti ČR", "CZ Unemployment Rate"),
    ("Průměrná mzda nominálně (YoY)", "Average Nominal Wage (YoY)"),
    ("Průměrná reálná mzda (YoY)", "Average Real Wage (YoY)"),
    ("Trh práce, nezaměstnanost a sjednané mzdy v Eurozóně (ECB Negotiated Wages)", "Labor Market, Unemployment & Negotiated Wages in Eurozone (ECB)"),
    ("Sjednané mzdy v Eurozóně (ECB YoY)", "Eurozone Negotiated Wages (ECB YoY)"),
    ("Reálný mzdový růst (odhad)", "Real Wage Growth (est.)"),
    ("Trh práce, zaměstnanost a průměrná hodinová mzda v USA (Average Hourly Earnings & NFP)", "US Labor Market, Employment & Average Hourly Earnings (NFP)"),
    ("Nová pracovní místa (NFP)", "Nonfarm Payrolls (NFP)"),
    ("Spotřebitelská inflace CPI", "Consumer Inflation CPI"),
    ("Srovnání výkonnosti hlavních světových a lokálních akciových indexů (Denní data)", "Performance Comparison of Global & Local Equity Indices (Daily Data)"),
    ("Porovnejte relativní kumulativní výnos nebo normalizovanou bázi pro S&P 500, NASDAQ, Euro Stoxx 50 a Index PX Pražské burzy s denní frekvencí.", "Compare relative cumulative return or rebased performance for S&P 500, NASDAQ, Euro Stoxx 50, and Prague Stock Exchange PX Index on a daily basis."),
    ("Poslední denní závěr:", "Last daily close:"),
    ("Změna za sledované období:", "Change over selected period:"),
    ("📥 Stáhnout kompletní denní data akciových indexů (CSV)", "📥 Download Complete Daily Equity Indices Data (CSV)"),
    ("Index PX – Burza cenných papírů Praha (BCPP – Denní data)", "PX Index – Prague Stock Exchange (PSE – Daily Data)"),
    ("Oficiální cenový index pražské burzy zahrnující klíčové české emise (ČEZ, Komerční banka, Erste Group, Moneta Money Bank, Colt CZ).", "Official price index of the Prague Stock Exchange comprising leading Czech blue-chip equities (CEZ, Komercni banka, Erste Group, Moneta Money Bank, Colt CZ)."),
    ("Aktuální denní kurz", "Current Daily Close"),
    ("Výkonnost za vybrané období", "Selected Period Performance"),
    ("Minimum v období", "Period Minimum"),
    ("Maximum v období", "Period Maximum"),
    ("Euro Stoxx 50 – Benchmark předních akcií Eurozóny (Denní data)", "Euro Stoxx 50 – Eurozone Blue-Chip Benchmark (Daily Data)"),
    ("S&P 500 – Globální měřítko amerického akciového trhu (Denní data)", "S&P 500 – Flagship U.S. Equity Market Benchmark (Daily Data)"),
    ("NASDAQ Composite – Světový technologický a inovační lídr (Denní data)", "NASDAQ Composite – Global Technology & Innovation Leader (Daily Data)"),
    ("Index volatility VIX – Tržní sentiment a vnímané riziko (Cboe \"Index strachu\" – Denní data)", "VIX Volatility Index – Market Sentiment & Perceived Risk (Cboe 'Fear Index' – Daily Data)"),
    ("Klid / Sebeuspokojení (< 15)", "Calm / Complacency (< 15)"),
    ("Normální rozmezí (15–20)", "Normal Range (15–20)"),
    ("Zvýšená nervozita (20–30)", "Elevated Nervousness (20–30)"),
    ("Tržní panika / Stres (> 30)", "Market Panic / Stress (> 30)"),
    ("Tržní režim sentimentu", "Market Sentiment Regime"),
    ("📊 Jak interpretovat hladiny indexu VIX:", "📊 How to interpret VIX index levels:"),
    ("Pod 15 bodů:", "Below 15 points:"),
    ("Nízká vnímaná rizika, stabilní růst akciových trhů (potenciální riziko sebeuspokojení / complacency).", "Low perceived risk, steady equity market uptrend (potential risk of market complacency)."),
    ("15 až 20 bodů:", "15 to 20 points:"),
    ("Běžná historická průměrná úroveň volatility, vyvážený a zdravý trh.", "Normal historical average volatility range, balanced and healthy market."),
    ("20 až 30 bodů:", "20 to 30 points:"),
    ("Zvýšená tržní nervozita, makroekonomická nejistota, korekce na trzích.", "Elevated market nervousness, macroeconomic uncertainty, market pullbacks."),
    ("Nad 30 bodů:", "Above 30 points:"),
    ("Akutní tržní stres, prudké výprodeje, likviditní šok (např. pandemický pád březen 2020 nebo hypoteční krize 2008).", "Acute market stress, sharp sell-offs, liquidity shock (e.g., March 2020 pandemic crash or 2008 financial crisis)."),
    # Commodities
    ("Srovnání výkonnosti hlavních světových komodit (Měsíční data)", "Global Commodities Performance Comparison (Monthly Data)"),
    ("Porovnejte normalizovanou výkonnost 5 klíčových komodit: drahé kovy (Zlato, Stříbro), energie (Ropa Brent, Zemní plyn) a klíčový průmyslový kov (Měď).", "Compare normalized performance across 5 key commodities: precious metals (Gold, Silver), energy (Brent Oil, Natural Gas), and industrial bellwether (Copper)."),
    ("📥 Stáhnout kompletní měsíční data komodit (CSV)", "📥 Download Complete Monthly Commodities Data (CSV)"),
    ("Aktuální cena", "Current Price"),
    ("🟡 Zlato (Gold) – Globální bezpečný přístav a monetární kotva", "🟡 Gold – Global Safe Haven & Monetary Anchor"),
    ("MAKROEKONOMICKÝ VÝZNAM & STRATEGIE CENTRÁLNÍCH BANK", "MACROECONOMIC SIGNIFICANCE & CENTRAL BANK STRATEGY"),
    ("🏛️ ČNB & Globální centrální banky", "🏛️ CNB & Global Central Banks"),
    ("Cena zlata dosahuje", "Gold price reaches"),
    ("za trojskou unci", "per troy ounce"),
    ("🔍 Hlavní cenotvorné faktory:", "🔍 Key Price Drivers:"),
    ("Poptávka po fyzickém zlatě je tažena agresivními nákupy centrálních bank (včetně České národní banky, která dlouhodobě navyšuje podíl zlata v devizových rezervách na cílových 100 tun), geopolitickou fragmentací a očekáváním uvolňování úrokových sazeb Fedu.", "Physical gold demand is driven by strategic central bank purchases (including the Czech National Bank, which is expanding its gold reserves toward a 100-ton target), geopolitical fragmentation, and Fed rate-cut expectations."),
    ("📊 Tržní vazby & Korelace:", "📊 Market Links & Correlations:"),
    ("Zlato historicky vykazuje silnou inverzní korelaci s reálnými americkými dluhopisovými výnosy (TIPS) a sílou dolarového indexu (DXY). Pokles reálných sazeb snižuje oportunitní náklad držby neúročeného drahého kovu.", "Gold historically exhibits a strong inverse correlation with U.S. real Treasury yields (TIPS) and the U.S. Dollar Index (DXY). Lower real yields reduce the opportunity cost of holding non-yielding precious metal."),
    ("🛢️ Ropa Brent (Brent Crude Oil) – Světový energetický benchmark", "🛢️ Brent Crude Oil – Global Energy Benchmark"),
    ("ENERGETICKÁ ROVNOVÁHA & KARTEL OPEC+", "ENERGY BALANCE & OPEC+ ALLIANCE"),
    ("🛢️ Mezinárodní energetická agentura (IEA)", "🛢️ International Energy Agency (IEA)"),
    ("Cena ropy Brent se pohybuje na úrovni", "Brent crude oil trades at"),
    ("za barel", "per barrel"),
    ("🔍 Nabídková a poptávková strana:", "🔍 Supply & Demand Dynamics:"),
    ("Rovnováha trhu s ropou závisí na těžebních kvótách aliance OPEC+ (vedené Saúdskou Arábií a Ruskem) a tempu těžby z břidličných ložisek v USA. Na straně poptávky hraje rozhodující roli průmyslová aktivita v Číně a globální letecká i nákladní doprava.", "Crude oil market balance depends on OPEC+ production quotas and U.S. shale output growth. On the demand side, industrial activity in China and global aviation and freight transport play a decisive role."),
    ("📊 Dopad na českou a evropskou ekonomiku:", "📊 Impact on Czech & European Economy:"),
    ("Pohyby cen ropy se s prodlevou 2–3 týdnů přímo promítají do cen pohonných hmot (Benzin Natural 95, Nafta) na tuzemských čerpacích stanicích a ovlivňují dopravní složku spotřebitelského koše inflace CPI.", "Oil price movements pass through within 2–3 weeks into domestic retail fuel prices (gasoline and diesel) and directly affect the transport component of the CPI inflation basket."),
    ("🔥 Zemní plyn (Natural Gas) – Henry Hub Benchmark", "🔥 Natural Gas – Henry Hub Benchmark"),
    ("GLOBÁLNÍ TRH LNG & EVROPSKÁ ENERGETICKÁ BEZPEČNOST", "GLOBAL LNG MARKET & EUROPEAN ENERGY SECURITY"),
    ("Zemní plyn Henry Hub se obchoduje za", "Henry Hub natural gas trades at"),
    ("🔍 Sezónnost a globální toky LNG:", "🔍 Seasonality & Global LNG Flows:"),
    ("Trh se zemním plynem vykazuje výraznou sezónnost závislou na zimních teplotách na severní polokouli. Po odstřižení ruských plynovodů se americký Henry Hub stal klíčovou referencí pro export zkapalněného plynu (LNG) do evropských terminálů (nizozemský uzel TTF).", "Natural gas markets exhibit strong winter weather seasonality across the Northern Hemisphere. Following the halt of Russian pipeline supplies, U.S. Henry Hub has become a key benchmark for LNG exports to European terminals (Dutch TTF)."),
    ("📊 Průmyslový dopad:", "📊 Industrial Impact:"),
    ("Cena plynu přímo determinuje náklady výroby elektřiny v paroplynových elektrárnách a je základní surovinou pro chemický průmysl (výroba čpavku a dusíkatých hnojiv pro zemědělství).", "Natural gas prices directly determine marginal power generation costs in gas-fired plants and serve as a critical feedstock for the chemical and fertilizer industries."),
    ("🏗️ Měď (Doctor Copper) – Barometr globální průmyslové a zelené transformace", "🏗️ Copper (Doctor Copper) – Barometer of Global Industry & Green Transition"),
    ("STRUKTURÁLNÍ MEGATRENDY & PRŮMYSLOVÝ CYKLUS", "STRUCTURAL MEGATRENDS & INDUSTRIAL CYCLE"),
    ("Cena mědi dosahuje", "Copper price reaches"),
    ("za libru", "per pound"),
    ("🔍 Proč Doctor Copper?:", "🔍 Why 'Doctor Copper'?:"),
    ("Měď nachází uplatnění v každém odvětví moderní ekonomiky: od stavebních rozvodů přes strojírenství až po spotřební elektroniku. Růst cen mědi spolehlivě signalizuje expanzi průmyslové výroby, zatímco propad varuje před přicházející recesí.", "Copper is used across every sector of the modern economy: from construction wiring and machinery to consumer electronics. Rising copper prices reliably signal industrial expansion, whereas slumps warn of economic slowdowns."),
    ("⚡ Elektrifikace & AI Datacentra:", "⚡ Electrification & AI Data Centers:"),
    ("Strukturální poptávku akceleruje přechod na elektromobilitu (elektromobil vyžaduje cca 4× více mědi než spalovací vůz), výstavba větrných/solárních parků a masivní investice do elektrické infrastruktury pro výpočetní centra umělé inteligence (AI).", "Structural demand is accelerated by EV adoption (an EV requires ~4x more copper than an ICE vehicle), renewable power grids, and massive electrical infrastructure investments for AI data centers."),
    ("⚪ Stříbro (Silver) – Duální kov: Investiční bezpečí & Průmyslová revoluce", "⚪ Silver – Dual Metal: Safe-Haven Investment & Industrial Revolution"),
    ("FOTOVOLTAIKA & GOLD/SILVER RATIO", "PHOTOVOLTAICS & GOLD/SILVER RATIO"),
    ("Stříbro se obchoduje na", "Silver trades at"),
    ("za unci (Gold/Silver poměr:", "per ounce (Gold/Silver ratio:"),
    ("🔍 Průmyslová poptávka:", "🔍 Industrial Demand:"),
    ("Více než 50 % celosvětové roční těžby stříbra směřuje do průmyslu. Klíčovým motorem je výroba fotovoltaických solárních panelů (PV články), kde má stříbro nejvyšší elektrickou a tepelnou vodivost ze všech kovů, a automobilová elektronika.", "Over 50% of annual global silver supply goes to industrial applications. Key growth drivers include photovoltaic solar cells (where silver offers the highest electrical conductivity of any metal) and automotive electronics."),
    ("📊 Poměr zlata a stříbra (Gold/Silver Ratio):", "📊 Gold/Silver Ratio:"),
    ("Aktuální poměr cen zlata a stříbra činí", "The current Gold/Silver price ratio stands at"),
    ("Historický průměr ve 20. století se pohyboval okolo 50–60. Vyšší hodnota indikuje relativní podhodnocení stříbra vůči zlatu, což v býčích cyklech drahých kovů často vede k prudkému zhodnocení stříbra.", "The 20th-century historical average hovered around 50–60. Higher readings indicate relative undervaluation of silver versus gold, often preceding sharp silver outperformance during precious metal bull markets."),
    # Tab 5 Fiscal & Global
    ("Fiskální politika a veřejný dluh České republiky", "Fiscal Policy & Public Debt of the Czech Republic"),
    ("Veřejný dluh k HDP", "Public Debt to GDP"),
    ("Limit < 60 % HDP", "Limit < 60% GDP"),
    ("Nominální veřejný dluh", "Nominal Public Debt"),
    ("Fiskální politika a veřejný dluh Eurozóny / EU", "Fiscal Policy & Public Debt of the Eurozone / EU"),
    ("Nominální dluh Eurozóny", "Eurozone Nominal Debt"),
    ("Kvartální saldo rozpočtu EU", "EU Quarterly Budget Balance"),
    ("Fiskální politika a federální dluh Spojených států", "Fiscal Policy & Federal Debt of the United States"),
    ("Historické maximum", "All-time high"),
    ("Nominální federální dluh", "Nominal Federal Debt"),
    ("Vnější rovnováha ČR: Běžný účet platební bilance & Bilance zahraničního obchodu ČSÚ", "CZ External Balance: Current Account & Foreign Trade Balance (CZSO)"),
    ("Běžný účet (% HDP)", "Current Account (% GDP)"),
    ("Bilance zahr. obchodu (ČSÚ)", "Foreign Trade Balance (CZSO)"),
    ("Kumulované saldo za 12M", "12M Cumulative Balance"),
    ("Kurz EUR/CZK (denní)", "EUR/CZK Rate (daily)"),
    ("Vnější rovnováha a mezinárodní obchod Eurozóny", "External Balance & International Trade of the Eurozone"),
    ("Měnový kurz EUR/USD", "EUR/USD Exchange Rate"),
    ("Exportní orientace", "Export Orientation"),
    ("Vysoká (Německo, Nizozemsko)", "High (Germany, Netherlands)"),
    ("Dovoz energií", "Energy Imports"),
    ("Stabilizovaný", "Stabilized"),
    ("Vnější rovnováha a obchodní bilance Spojených států", "External Balance & Trade Balance of the United States"),
    ("Běžný účet USA (% HDP)", "US Current Account (% GDP)"),
    ("Postavení USD", "USD Status"),
    ("Globální rezervní měna", "Global Reserve Currency"),
    ("Příliv kapitálu", "Capital Inflows"),
    ("Financuje schodek", "Finances Deficit"),
    ("Mezinárodní srovnání sazeb a výnosových spreadů", "International Comparison of Policy Rates & Yield Spreads"),
    ("Sazbový diferenciál (ČNB vs. Fed)", "Policy Rate Differential (CNB vs. Fed)"),
    ("Sazbový diferenciál (ČNB vs. ECB)", "Policy Rate Differential (CNB vs. ECB)"),
    ("Sazbový diferenciál (ECB vs. Fed)", "Policy Rate Differential (ECB vs. Fed)"),
    ("Sazbový diferenciál (Fed vs. ECB)", "Policy Rate Differential (Fed vs. ECB)"),
    ("Inflační diferenciál (EU − USA)", "Inflation Differential (EU − US)"),
    ("Inflační diferenciál (USA − EU)", "Inflation Differential (US − EU)"),
    # Tab 6 Export & Tab 7 Catalog
    ("Datový průzkumník a export", "Data Explorer & Export"),
    ("Interaktivní tabulkový přehled všech vybraných časových řad připravený pro export do formátu CSV.", "Interactive tabular preview of all selected time series ready for CSV export."),
    ("📥 Stáhnout kompletní data", "📥 Download Complete Data"),
    ("Kompletní metodický přehled a katalog všech sledovaných ukazatelů a zdrojů dat", "Complete Methodological Overview & Catalog of All Monitored Indicators and Data Sources"),
    ("Strukturovaný přehled všech 100+ makroekonomických a tržních ukazatelů podle jednotlivých zemí a kategorií s uvedením primárních datových zdrojů, metodiky a frekvence aktualizace.", "Structured directory of all 100+ macroeconomic and market indicators by country and category, including primary data sources, methodology, and update frequency."),
    ("Hledáte srozumitelný lidský výklad co jednotlivé pojmy znamenají, proč je sledovat a jaký mají vliv na hypotéky či investice? Použijte", "Looking for a clear, plain-English explanation of what each indicator means, why it matters, and how it affects mortgages or investments? Open the"),
    ("Výkladový glosář", "Explanatory Glossary"),
    ("Celkem ukazatelů", "Total Indicators"),
    ("metrik", "metrics"),
    ("ukazatelů", "indicators"),
    ("Nalezeno", "Found"),
    ("📥 Stáhnout kompletní katalog ukazatelů a zdrojů (CSV)", "📥 Download Complete Indicator & Source Catalog (CSV)"),
    ("Přehled primárních poskytovatelů dat a integrační architektura", "Overview of Primary Data Providers & Integration Architecture"),
    ("Globální trhy & Agregace", "Global Markets & Aggregation"),
    ("poslední aktualizace:", "last updated:"),
    ("Zdrojový článek", "Source article"),
    ("Nejnovější zpráva k tématu", "Latest topic news"),
    ("Ověřená data & hlavní faktory:", "Verified Data & Key Drivers:"),
    ("Makroekonomický kontext:", "Macroeconomic Context:"),
    ("/ barel", "/ bbl"),
    ("/ libra", "/ lb"),
    ("$/barel", "$/bbl"),
    ("$/libra", "$/lb"),
    ("p.b.", "pp"),
])


# Additional Plotly & News & Institution Card phrases
PHRASE_REPLACEMENTS.extend([
    # Plotly chart titles, traces, axes, annotations
    ("Lombardní sazba ČNB (horní mez)", "CNB Lombard Rate (upper bound)"),
    ("Diskontní sazba ČNB (dolní mez)", "CNB Discount Rate (lower bound)"),
    ("2T Repo sazba ČNB (klíčová)", "CNB 2W Repo Rate (key)"),
    ("PRIBOR 3M (benchmark)", "PRIBOR 3M (benchmark)"),
    ("Úrokové sazby (%)", "Interest Rates (%)"),
    ("Mezní zápůjční sazba ECB (strop)", "ECB Marginal Lending Rate (ceiling)"),
    ("Depozitní sazba ECB (hlavní kotva)", "ECB Deposit Facility Rate (anchor)"),
    ("Refinanční sazba ECB (MRO)", "ECB Main Refinancing Rate (MRO)"),
    ("Úrokové sazby EUR (%)", "EUR Interest Rates (%)"),
    ("Efektivní Fed Funds (EFFR)", "Effective Fed Funds (EFFR)"),
    ("Úrokové sazby USD (%)", "USD Interest Rates (%)"),
    ("Toleranční pásmo ČNB (1–3 %)", "CNB Tolerance Band (1–3%)"),
    ("Inflační cíl (2.0 %)", "Inflation Target (2.0%)"),
    ("Inflační cíl ECB (2.0 %)", "ECB Inflation Target (2.0%)"),
    ("Inflační cíl Fedu (2.0 %)", "Fed Inflation Target (2.0%)"),
    ("Celková inflace CPI (YoY %)", "Headline CPI Inflation (YoY %)"),
    ("Reálná sazba (Repo − CPI)", "Real Rate (Repo − CPI)"),
    ("Reálná sazba ECB (Depo − HICP)", "ECB Real Rate (Depo − HICP)"),
    ("Reálná sazba (Fed EFFR − CPI)", "Real Rate (Fed EFFR − CPI)"),
    ("Meziroční inflace (%)", "YoY Inflation (%)"),
    ("Reálná úroková míra (%)", "Real Interest Rate (%)"),
    ("Reálná úroková míra EUR (%)", "EUR Real Interest Rate (%)"),
    ("Reálná úroková míra USA (%)", "US Real Interest Rate (%)"),
    ("Harmonizovaná inflace (HICP YoY %)", "Harmonised Inflation (HICP YoY %)"),
    ("Inflace Eurozóny (% YoY)", "Eurozone Inflation (% YoY)"),
    ("Inflace USA (% YoY)", "US Inflation (% YoY)"),
    ("Nominální HDP (mld. CZK)", "Nominal GDP (CZK bn)"),
    ("Nominální HDP ČR", "CZ Nominal GDP"),
    ("Reálný růst HDP ČR (YoY %)", "CZ Real GDP Growth (YoY %)"),
    ("Reálný růst ČR", "CZ Real Growth"),
    ("Reálný růst HDP (YoY %)", "Real GDP Growth (YoY %)"),
    ("Nominální HDP Eurozóny (mld. EUR)", "Eurozone Nominal GDP (EUR bn)"),
    ("Nominální HDP EU (mld. EUR)", "EU Nominal GDP (EUR bn)"),
    ("Nominální HDP EU", "EU Nominal GDP"),
    ("Reálný růst HDP Eurozóny (YoY %)", "Eurozone Real GDP Growth (YoY %)"),
    ("Reálný růst HDP EU (YoY %)", "EU Real GDP Growth (YoY %)"),
    ("Reálný růst EU", "EU Real Growth"),
    ("Nominální HDP USA (mld. USD)", "US Nominal GDP (USD bn)"),
    ("Nominální HDP USA", "US Nominal GDP"),
    ("Reálný růst HDP USA (YoY %)", "US Real GDP Growth (YoY %)"),
    ("Reálný růst USA", "US Real Growth"),
    ("Maloobchodní tržby ČR (Spotřeba YoY)", "CZ Retail Sales (Consumption YoY)"),
    ("Meziroční růst / pokles (%)", "YoY Growth / Decline (%)"),
    ("Meziroční změna (%)", "YoY Change (%)"),
    ("Extrémy", "Extremes"),
    ("pravá osa", "right axis"),
    ("Kurz EUR, USD, GBP (Kč)", "EUR, USD, GBP Rate (CZK)"),
    ("Kurz PLN (Kč)", "PLN Rate (CZK)"),
    ("Kurz EUR/USD & EUR/GBP", "EUR/USD & EUR/GBP Rate"),
    ("Kurz EUR/CZK & EUR/PLN", "EUR/CZK & EUR/PLN Rate"),
    ("Dolarový index DXY (body)", "U.S. Dollar Index DXY (pts)"),
    ("Měnové kurzy ($)", "Exchange Rates ($)"),
    ("Báze (0 %)", "Base (0%)"),
    ("Báze (100 b.)", "Base (100 pts)"),
    ("Relativní zhodnocení (%)", "Relative Return (%)"),
    ("Index rebase (báze = 100)", "Rebased Index (Base = 100)"),
    ("50D klouzavý průměr", "50D Moving Average"),
    ("12M klouzavý průměr", "12M Moving Average"),
    ("Hodnota indexu (body)", "Index Value (points)"),
    ("Cena (", "Price ("),
    ("hodnota:", "value:"),
    ("cena:", "price:"),
    ("Maastrichtský limit (60.0 % HDP)", "Maastricht Limit (60.0% GDP)"),
    ("Maastrichtské kritérium (60.0 % HDP)", "Maastricht Criterion (60.0% GDP)"),
    ("Hranice 100 % HDP", "100% GDP Threshold"),
    ("Dluh k HDP", "Debt to GDP"),
    ("Dluh Eurozóny k HDP", "Eurozone Debt to GDP"),
    ("Dluh USA k HDP", "US Debt to GDP"),
    ("Veřejný dluh (% HDP)", "Public Debt (% GDP)"),
    ("Veřejný dluh EU (% HDP)", "EU Public Debt (% GDP)"),
    ("Dluh USA (% HDP)", "US Debt (% GDP)"),
    ("Federální dluh USA (% HDP)", "US Federal Debt (% GDP)"),
    ("Kvartální saldo rozpočtu Eurozóny", "Eurozone Quarterly Budget Balance"),
    ("Saldo rozpočtu (mld. CZK)", "Budget Balance (CZK bn)"),
    ("Saldo rozpočtu (mld. EUR)", "Budget Balance (EUR bn)"),
    ("Saldo rozpočtu (mld. USD)", "Budget Balance (USD bn)"),
    ("Saldo SR", "Budget Balance"),
    ("Saldo EU", "EU Balance"),
    ("Deficit USA", "US Deficit"),
    ("Státní dluhopisy (CZGB)", "Government Bonds (CZGB)"),
    ("Úrokové swapy (CZK IRS)", "Interest Rate Swaps (CZK IRS)"),
    ("CZGB (Před rokem)", "CZGB (1 Year Ago)"),
    ("Německý Bund (Aktuální)", "German Bund (Current)"),
    ("Německý Bund (Před rokem)", "German Bund (1 Year Ago)"),
    ("U.S. Treasury (Aktuální)", "U.S. Treasury (Current)"),
    ("U.S. Treasury (Před rokem)", "U.S. Treasury (1 Year Ago)"),
    ("historie", "1Y ago"),
    ("Splatnost", "Maturity"),
    ("Výnos do splatnosti (% p.a.)", "Yield to Maturity (% p.a.)"),
    ("Spread 10Y (CZGB − Německý Bund)", "10Y Spread (CZGB − German Bund)"),
    ("Spread 10Y (CZGB − US Treasury)", "10Y Spread (CZGB − US Treasury)"),
    ("Spread 10Y (Německý Bund − US Treasury)", "10Y Spread (German Bund − US Treasury)"),
    ("Spread 10Y (US Treasury − Německý Bund)", "10Y Spread (US Treasury − German Bund)"),
    ("Mezinárodní sovereign spready ČR (v bps)", "CZ International Sovereign Spreads (bps)"),
    ("Transatlantické rozpětí: Eurozóna vs. Spojené státy (v bps)", "Transatlantic Spread: Eurozone vs. United States (bps)"),
    ("Mezinárodní spread Spojených států (v bps)", "US International Yield Spread (bps)"),
    ("Parita výnosů (0 bps)", "Yield Parity (0 bps)"),
    ("Rozpětí (bps)", "Spread (bps)"),
    ("PMI 50 = Expanze / Kontrakce", "PMI 50 = Expansion / Contraction"),
    ("PMI 50 = Hranice růstu", "PMI 50 = Growth Threshold"),
    ("ISM 50 = Hranice expanze", "ISM 50 = Expansion Threshold"),
    ("PMI Index (50 = zlom)", "PMI Index (50 = threshold)"),
    ("ISM PMI (50 = zlom)", "ISM PMI (50 = threshold)"),
    ("Důvěra ČSÚ (body)", "CZSO Confidence (pts)"),
    ("Composite PMI (body)", "Composite PMI (pts)"),
    ("Ifo Index Německa (body)", "German Ifo Index (pts)"),
    ("Michigan Sentiment (body)", "Michigan Sentiment (pts)"),
    ("Předstihové ukazatele ČR: PMI průmyslu (S&P Global) vs. Souhrnná důvěra (ČSÚ)", "CZ Leading Indicators: Manufacturing PMI (S&P Global) vs. Composite Confidence (CZSO)"),
    ("Předstihové ukazatele EU: Composite PMI Eurozóny & Německý Ifo index podnikatelského klimatu", "EU Leading Indicators: Eurozone Composite PMI & German Ifo Business Climate"),
    ("US Předstihové ukazatele: ISM Výroba, ISM Služby & Spotřebitelský sentiment Univ. of Michigan", "US Leading Indicators: ISM Manufacturing, ISM Services & Univ. of Michigan Consumer Sentiment"),
    ("Průměrná hrubá mzda nominálně (YoY)", "Average Gross Nominal Wage (YoY)"),
    ("Průměrná reálná mzda (YoY)", "Average Real Wage (YoY)"),
    ("Inflace CPI ČR (YoY)", "CZ CPI Inflation (YoY)"),
    ("Vývoj mezd v ČR: Nominální vs. Reálná mzda (očištěná o inflaci CPI)", "Wage Growth in CZ: Nominal vs. Real Wage (CPI-adjusted)"),
    ("Sjednané mzdy Eurozóny (ECB YoY)", "Eurozone Negotiated Wages (ECB YoY)"),
    ("Harmonizovaná inflace EU (HICP)", "EU Harmonised Inflation (HICP)"),
    ("Mzdový růst v Eurozóně: Sjednané mzdy (ECB) vs. Harmonizovaná inflace HICP", "Eurozone Wage Growth: Negotiated Wages (ECB) vs. HICP Inflation"),
    ("Průměrná hodinová mzda USA (Average Hourly Earnings YoY)", "US Average Hourly Earnings (YoY)"),
    ("Trh práce USA: Růst hodinových výdělků vs. Inflace CPI", "US Labor Market: Hourly Earnings Growth vs. CPI Inflation"),
    ("Nové hypotéky – objem (mld. Kč)", "New Mortgages – Volume (CZK bn)"),
    ("Průměrná sazba nových hypoték (% p.a.)", "Average New Mortgage Rate (% p.a.)"),
    ("Korporátní úvěry (YoY)", "Corporate Loans (YoY)"),
    ("Měnový agregát M2 (YoY)", "M2 Money Supply (YoY)"),
    ("Bankovní sektor ČR: Hypotéky (objem v mld. Kč & sazba % p.a.), korporátní úvěry a peněžní zásoba M2", "CZ Banking Sector: Mortgages (Volume in CZK bn & Rate % p.a.), Corporate Loans & M2 Money Supply"),
    ("Objem nových hypoték (mld. Kč)", "New Mortgage Volume (CZK bn)"),
    ("Sazby & Růst (%)", "Rates & Growth (%)"),
    ("Měsíční saldo zahraničního obchodu ČSÚ (mld. Kč)", "Monthly Foreign Trade Balance CZSO (CZK bn)"),
    ("Běžný účet platební bilance (% HDP)", "Current Account Balance (% GDP)"),
    ("Vnější rovnováha ČR: Bilance zahraničního obchodu (ČSÚ) & Běžný účet (% HDP)", "CZ External Balance: Foreign Trade Balance (CZSO) & Current Account (% GDP)"),
    ("Obchodní bilance (mld. Kč)", "Trade Balance (CZK bn)"),
    ("Dluhopisové a swapové spready ČR: 10Y CZGB vs. Bund & Asset Swap Spread (ASW 10Y CZK)", "CZ Bond & Swap Spreads: 10Y CZGB vs. Bund & Asset Swap Spread (10Y CZK ASW)"),
    ("Rizikový spread Itálie vs. Německo (10Y BTP - Bund)", "Italy vs. Germany Risk Spread (10Y BTP - Bund)"),
    ("Zvýšené periferní riziko (200 bps)", "Elevated Periphery Risk (200 bps)"),
    ("Dluhopisové rizikové spready Eurozóny: Itálie (BTP) vs. Německo (Bund) 10Y", "Eurozone Sovereign Risk Spreads: Italy (BTP) vs. Germany (Bund) 10Y"),
    ("Index volatility VIX (Cboe)", "Cboe Volatility Index (VIX)"),
    ("Klid & Býčí sentiment (<15)", "Calm & Bullish Sentiment (<15)"),
    ("Normální volatilita (15–20)", "Normal Volatility (15–20)"),
    ("Zvýšená nervozita & riziko (20–30)", "Elevated Nervousness & Risk (20–30)"),
    ("Extrémní stres & panika (>30)", "Extreme Stress & Panic (>30)"),
    ("Index volatility Cboe VIX ('Index strachu') a režimy tržního sentimentu", "Cboe VIX Volatility Index ('Fear Index') & Market Sentiment Regimes"),
    ("VIX Index (body)", "VIX Index (pts)"),
    ("Zlato", "Gold"),
    ("Zemní plyn", "Natural Gas"),
    ("Měď", "Copper"),
    ("Stříbro", "Silver"),
    (" mld. €", " EUR bn"),
    (" mld. $", " USD bn"),
    (" mld.", " bn"),
    # Info boxes & Institution architecture cards
    ("💡 Eurozóna dlouhodobě vykazuje strukturální přebytek běžného účtu platební bilance, tažený exportem německého a nizozemského strojírenství, chemického a automobilového průmyslu.", "💡 The Eurozone maintains a structural current account surplus, driven by German and Dutch machinery, chemical, and automotive exports."),
    ("💡 USA dlouhodobě hospodaří s deficitem běžného účtu (tzv. dvojí deficit – rozpočtový a obchodní). Schodek je financován trvalým přílivem zahraničního kapitálu do amerických finančních aktiv a rezervním statusem amerického dolaru.", "💡 The United States runs a persistent structural current account deficit ('twin deficit' – fiscal and trade), financed by global capital inflows into U.S. financial assets and the reserve status of the U.S. dollar."),
    ("💡 Data bankovního sektoru Eurozóny vycházejí z pravidelného šetření ECB Bank Lending Survey (BLS) a statistik měnových finančních institucí (MFI). V ČR je k dispozici detailní měsíční monitoring ČBA Hypomonitor.", "💡 Eurozone banking sector data is sourced from the regular ECB Bank Lending Survey (BLS) and Monetary Financial Institutions (MFI) statistics. For the Czech Republic, detailed monthly monitoring is provided via the CBA Hypomonitor."),
    ("💡 Americký hypoteční a úvěrový trh je sledován primárně prostřednictvím sazeb Freddie Mac (30Y Fixed Rate Mortgage) a bilance komerčních bank Fed H.8.", "💡 The U.S. mortgage and credit market is tracked primarily via Freddie Mac (30Y Fixed Rate Mortgage) surveys and Federal Reserve H.8 commercial bank balance sheet releases."),
    ("Otevřené REST API pro denní devizové kurzy v 14:30 (EUR, USD, PLN, GBP, JPY, CHF) a časové řady měnových sazeb (2T repo, diskontní, lombardní, 3M PRIBOR).", "Open REST API for daily FX fixing rates at 14:30 CET (EUR, USD, PLN, GBP, JPY, CHF) and monetary policy rate series (2W Repo, Discount, Lombard, 3M PRIBOR)."),
    ("Pravidelné konjunkturální a národní statistiky – HDP, celková inflace CPI, maloobchodní tržby a průmyslová produkce.", "Official national accounts and short-term statistics – GDP, headline CPI inflation, retail sales, and industrial production."),
    ("Měsíční pokladní plnění, vládní dluh a aukce státních dluhopisů CZGB.", "Monthly state budget execution, government debt statistics, and CZGB government bond auctions."),
    ("Oficiální cenový index PX pražské burzy.", "Official PX price index of the Prague Stock Exchange."),
    ("Oficiální JSON REST API pro harmonizovanou inflaci (HICP & Core HICP), HDP Eurozóny, míru nezaměstnanosti, vládní dluh (EDP) a referenční vládní dluhopisy.", "Official JSON REST API for harmonised inflation (HICP & Core HICP), Eurozone GDP, unemployment rate, government debt (EDP), and sovereign bond yields."),
    ("Klíčový sazbový koridor (DFR, MRO, MLF), referenční peněžní sazba €STR a 3M EURIBOR fixace.", "Key ECB policy rate corridor (DFR, MRO, MLF), €STR overnight benchmark rate, and 3M EURIBOR fixings."),
    ("Benchmark výnosové křivky německých státních dluhopisů (Bund 2Y až 30Y).", "Benchmark German sovereign yield curve (Bunds 2Y to 30Y)."),
    ("Index 50 předních blue-chip společností Eurozóny Euro Stoxx 50.", "Euro Stoxx 50 index of 50 leading Eurozone blue-chip corporations."),
    ("Oficiální denní XML feed výnosové křivky státních dluhopisů (U.S. Treasury Par Yield Curve od 1M po 30Y) a federální dluh.", "Official daily XML feed of the U.S. Treasury Par Yield Curve (1M to 30Y) and federal public debt."),
    ("Fed Funds Target Range, EFFR, zajištěná sazba peněžního trhu SOFR a index průmyslové produkce (G.17).", "Fed Funds Target Range, EFFR, Secured Overnight Financing Rate (SOFR), and Industrial Production Index (G.17)."),
    ("Spotřebitelská inflace (Headline & Core CPI) a zpráva o zaměstnanosti (míra nezaměstnanosti U-3 a NFP).", "Consumer inflation (Headline & Core CPI) and Employment Situation report (U-3 unemployment rate and Nonfarm Payrolls)."),
    ("Kvartální reálný a nominální HDP a maloobchodní tržby.", "Quarterly real and nominal GDP and advance retail sales."),
    ("Měsíční a denní historické i živé kotace indexů S&P 500 (^GSPC), NASDAQ Composite (^IXIC), Euro Stoxx 50 (^STOXX50E).", "Daily and monthly historical and live quotes for S&P 500 (^GSPC), NASDAQ Composite (^IXIC), and Euro Stoxx 50 (^STOXX50E)."),
    ("Dolarový index DXY a křížové devizové kurzy měn G10 a CEE (EUR, USD, GBP, PLN, CZK).", "U.S. Dollar Index (DXY) and G10 / CEE cross currency rates (EUR, USD, GBP, PLN, CZK)."),
])


# =====================================================================
# 3. CORE TRANSLATION FUNCTIONS & STREAMLIT / PLOTLY WRAPPERS
# =====================================================================

def tr(text: Any) -> Any:
    """Translates a Czech UI string or phrase into English when is_en() is True."""
    if not isinstance(text, str) or not text or not is_en():
        return text

    stripped = text.strip()
    if stripped in EXACT_TRANSLATIONS:
        return text.replace(stripped, EXACT_TRANSLATIONS[stripped])

    res = text
    # Dynamic regex patterns (e.g. "Nalezeno X z Y ukazatelů")
    res = re.sub(
        r"Nalezeno\s+(\d+)\s+z\s+(\d+)\s+ukazatelů",
        r"Showing \1 of \2 indicators",
        res,
    )
    for cs_phrase, en_phrase in PHRASE_REPLACEMENTS:
        if cs_phrase in res:
            res = res.replace(cs_phrase, en_phrase)
    return res


def tr_html(html_text: Any) -> Any:
    """Translates embedded Czech phrases inside HTML blocks when is_en() is True."""
    if not isinstance(html_text, str) or not html_text or not is_en():
        return html_text
    # Do not touch pure <style> blocks without visible text
    if html_text.lstrip().startswith("<style>") and html_text.rstrip().endswith("</style>"):
        return html_text
    return tr(html_text)


def translate_plotly_figure(fig: Any) -> Any:
    """Translates Plotly figure titles, axis labels, tick suffixes, trace names, hovertemplates, and annotations."""
    if fig is None or not is_en():
        return fig
    try:
        # 1. Layout title & axes
        if hasattr(fig, "layout"):
            if getattr(fig.layout, "title", None) and getattr(fig.layout.title, "text", None):
                fig.layout.title.text = tr(fig.layout.title.text)
            for axis_attr in ("xaxis", "yaxis", "yaxis2", "yaxis3"):
                ax = getattr(fig.layout, axis_attr, None)
                if ax is not None:
                    if getattr(ax, "title", None) and getattr(ax.title, "text", None):
                        ax.title.text = tr(ax.title.text)
                    if getattr(ax, "ticksuffix", None):
                        ax.ticksuffix = tr(ax.ticksuffix)
            # Annotations
            if getattr(fig.layout, "annotations", None):
                for ann in fig.layout.annotations:
                    if getattr(ann, "text", None):
                        ann.text = tr(ann.text)
        # 2. Traces
        if hasattr(fig, "data"):
            for trace in fig.data:
                if getattr(trace, "name", None):
                    trace.name = tr(trace.name)
                if getattr(trace, "hovertemplate", None):
                    trace.hovertemplate = tr(trace.hovertemplate)
    except Exception:
        pass
    return fig


def translate_cz_news_card_item(news_item: Optional[Dict[str, str]]) -> Optional[Dict[str, str]]:
    """Translates a CZ_NEWS dictionary item into English when is_en() is True."""
    if not news_item or not is_en():
        return news_item

    item = dict(news_item)
    tag_map = {
        "MĚNOVÁ POLITIKA ČNB & SAZBY": "CNB MONETARY POLICY & RATES",
        "DLUHOPISOVÝ TRH & VÝNOSY": "BOND MARKET & YIELDS",
        "DEVIZOVÝ TRH & KURZ KORUNY": "FX MARKET & KORUNA RATE",
        "NÁRODNÍ ÚČTY & HOSPODÁŘSKÝ RŮST": "NATIONAL ACCOUNTS & GDP GROWTH",
        "SPOTŘEBITELSKÉ CENY & INFLACE": "CONSUMER PRICES & INFLATION",
        "KONJUNKTURA: SPOTŘEBA & PRŮMYSL": "BUSINESS CYCLE: CONSUMPTION & INDUSTRY",
        "TRH PRÁCE & ZAMĚSTNANOST": "LABOR MARKET & EMPLOYMENT",
        "AKCIOVÉ TRHY & BCPP": "EQUITY MARKETS & PSE",
        "FISKÁLNÍ POLITIKA & STÁTNÍ ROZPOČET": "FISCAL POLICY & STATE BUDGET",
        "DLUHOPISOVÉ SPREADY & RIZIKO": "BOND SPREADS & SOVEREIGN RISK",
        "PŘEDSTIHOVÉ UKAZATELE & KONJUNKTURA": "LEADING INDICATORS & SENTIMENT",
        "TRH PRÁCE & MZDOVÝ VÝVOJ": "LABOR MARKET & WAGE DYNAMICS",
        "BANKOVNÍ SEKTOR & ČBA HYPOMONITOR": "BANKING SECTOR & CBA HYPOMONITOR",
        "VNĚJŠÍ ROVNOVÁHA & ZAHRANIČNÍ OBCHOD": "EXTERNAL BALANCE & FOREIGN TRADE",
    }
    if item.get("tag") in tag_map:
        item["tag"] = tag_map[item["tag"]]

    news_replacements = [
        ("Aktuální stav", "Current status"),
        ("Denní fixing ČNB", "CNB Daily Fixing"),
        ("Kvartální národní účty ČSÚ", "CZSO Quarterly National Accounts"),
        ("Indexy spotřebitelských cen ČSÚ", "CZSO Consumer Price Indices"),
        ("Měsíční konjunkturální data ČSÚ", "CZSO Monthly Short-Term Statistics"),
        ("Měsíční statistika Eurostat / MPSV", "Eurostat / MoLSA Monthly Statistics"),
        ("Burza cenných papírů Praha", "Prague Stock Exchange"),
        ("Statistika vládního dluhu", "Government Debt Statistics"),
        ("Sekundární dluhopisový trh", "Secondary Bond Market"),
        ("Průzkum PMI & Konjunktura ČSÚ", "PMI Survey & CZSO Business Cycle"),
        ("Statistika průměrných mezd ČSÚ", "CZSO Average Wage Statistics"),
        ("Zahraniční obchod ČSÚ & Platební bilance ČNB", "CZSO Foreign Trade & CNB Balance of Payments"),
        ("Česká národní banka (ČNB)", "Czech National Bank (CNB)"),
        ("Česká národní banka", "Czech National Bank"),
        ("Český statistický úřad (ČSÚ)", "Czech Statistical Office (CZSO)"),
        ("Ministerstvo financí ČR", "Ministry of Finance CZ"),
        ("Česká bankovní asociace", "Czech Banking Association"),
        ("Bankovní rada ČNB uvolňuje měnovou politiku: 2T repo sazba snížena na", "CNB Bank Board eases monetary policy: 2W repo rate cut to"),
        ("Bankovní rada ČNB zpřísňuje měnovou politiku: 2T repo sazba zvýšena na", "CNB Bank Board tightens monetary policy: 2W repo rate raised to"),
        ("Bankovní rada ČNB ponechává 2T repo sazbu na", "CNB Bank Board keeps 2W repo rate at"),
        ("PRIBOR 3M činí", "3M PRIBOR stands at"),
        ("Při meziroční inflaci", "With year-on-year inflation at"),
        ("se reálná repo sazba ČNB pohybuje na", "the real CNB repo rate stands at"),
        ("což ukotvuje měnové podmínky v kladném reálném pásmu. Tříměsíční PRIBOR se nachází na", "anchoring monetary conditions in positive real territory. The 3-month PRIBOR stands at"),
        ("ČNB udržuje obezřetnou měnovou politiku s cílem tlumit přetrvávající cenové tlaky ve službách a na trhu nemovitostí. Kladná reálná repo sazba", "The CNB maintains a prudent monetary policy stance aimed at containing persistent price pressures in services and the housing market. A positive real repo rate"),
        ("podporuje stabilitu koruny.", "supports koruna stability."),
        ("Výnosová křivka ČR: 10Y dluhopis CZGB na", "CZ Yield Curve: 10Y CZGB bond yield at"),
        ("sklon 10Y–2Y činí", "10Y–2Y slope at"),
        ("Desetiletý vládní benchmark CZGB se obchoduje s výnosem", "The 10-year CZGB government benchmark trades at a yield of"),
        ("zatímco 2letý dluhopis dosahuje", "while the 2-year bond yield stands at"),
        ("Kladné rozpětí", "A positive spread of"),
        ("potvrzuje kladný sklon křivky a vyšší delší korunové tržní sazby (IRS).", "confirms a positively sloped yield curve and elevated long-end CZK market swap rates (IRS)."),
        ("Vyšší výnosy na delším konci křivky a růst korunových úrokových swapů (10Y IRS na", "Higher long-end yields and CZK interest rate swaps (10Y IRS at"),
        ("zároveň brání zlevňování dlouhodobých úvěrů a hypoték. Výnosový spread vůči německému Bundu činí", "limit further reductions in long-term loan and mortgage rates. The yield spread over the German Bund stands at"),
        ("Česká koruna se obchoduje na", "Czech koruna trades at"),
        ("kurz vůči dolaru činí", "USD/CZK rate stands at"),
        ("Oficiální denní kurz ČNB dosahuje", "The official CNB daily fixing stands at"),
        ("Kč za euro", "CZK per euro"),
        ("denní posílení o", "daily appreciation of"),
        ("denní oslabení o", "daily depreciation of"),
        ("denní stabilizace", "daily stabilization"),
        ("Koruně poskytuje oporu kladný úrokový diferenciál ČNB vůči ECB", "The koruna is supported by the positive CNB-ECB interest rate differential"),
        ("a přebytková bilance zahraničního obchodu.", "and a foreign trade surplus."),
        ("Vůči americkému dolaru kurz činí", "Against the U.S. dollar the exchange rate stands at"),
        ("a vůči zlotému", "and against the Polish zloty at"),
        ("Stabilní kurz koruny pomáhá tlumit dováženou inflaci u surovin a energií.", "A stable koruna exchange rate helps dampen imported inflation across commodities and energy."),
        ("Česká ekonomika zrychluje: Meziroční reálný růst HDP dosahuje", "Czech economy accelerates: YoY real GDP growth reaches"),
        ("Česká ekonomika drží tempo: Meziroční reálný růst HDP dosahuje", "Czech economy holds pace: YoY real GDP growth reaches"),
        ("Česká ekonomika zpomaluje: Meziroční reálný růst HDP dosahuje", "Czech economy moderates: YoY real GDP growth reaches"),
        ("Hrubý domácí produkt vzrostl meziročně o", "Gross Domestic Product grew year-on-year by"),
        ("změna", "change"),
        ("Hlavním tahounem hospodářského růstu je oživená spotřeba domácností podpořená reálným růstem mezd.", "Economic growth is primarily driven by recovering household consumption supported by real wage growth."),
        ("Česká ekonomika vykazuje solidní růstovou dynamiku taženou domácí poptávkou a službami, která kompenzuje utlumenější průmyslovou poptávku v Německu.", "The Czech economy shows solid growth momentum driven by domestic demand and services, offsetting softer industrial demand in Germany."),
        ("Meziroční inflace v ČR činí", "YoY inflation in CZ stands at"),
        ("jádrová inflace dosahuje", "core inflation reaches"),
        ("Spotřebitelská inflace CPI se nachází na úrovni", "Headline CPI consumer inflation stands at"),
        ("přičemž se drží v tolerančním pásmu ČNB (1,0–3,0 %). Jádrová inflace činí", "remaining within the CNB tolerance band (1.0–3.0%). Core inflation stands at"),
        ("Zatímco ceny energií a zboží působí protiinflačně, zvýšená dynamika přetrvává v sektoru služeb a u imputovaného nájemného, což vede ČNB k opatrnosti při dalším nastavování úrokových sazeb.", "While energy and goods prices act disinflationarily, elevated price momentum persists in services and imputed rent, keeping the CNB cautious on further rate adjustments."),
        ("Maloobchodní tržby vykazují", "Retail sales record"),
        ("průmyslová produkce", "industrial production"),
        ("Spotřebitelské tržby v maloobchodě rostou meziročně o", "Retail sales grew year-on-year by"),
        ("díky pokračujícímu růstu reálných mezd. Průmyslová produkce vykazuje meziroční změnu", "supported by continued real wage growth. Industrial production recorded a YoY change of"),
        ("Ekonomika si udržuje dvourychlostní charakter: sektor obchodu a služeb těží ze silné domácí spotřeby, zatímco průmysloví exportéři čelí kolísavé zahraniční poptávce.", "The economy maintains a two-speed profile: retail and services benefit from strong domestic consumption, while industrial exporters face volatile external demand."),
        ("Míra nezaměstnanosti v ČR činí", "CZ unemployment rate stands at"),
        ("Česko patří mezi země s nejnižší nezaměstnaností v EU", "Czechia maintains one of the lowest unemployment rates in the EU"),
        ("Harmonizovaná míra nezaměstnanosti (ILO/Eurostat) dosahuje", "The harmonised unemployment rate (ILO/Eurostat) stands at"),
        ("Trh práce vykazuje mírné ochlazování v průmyslu, které je však absorbováno sektorem služeb.", "The labor market shows mild cooling in manufacturing, which continues to be absorbed by the services sector."),
        ("Nízká míra nezaměstnanosti podporuje mzdové vyjednávání a spotřebitelský sentiment domácností.", "Low unemployment supports wage bargaining and household consumer confidence."),
        ("Index PX pražské burzy se obchoduje na", "Prague Stock Exchange PX Index trades at"),
        ("bodech", "points"),
        ("Index PX dosahuje", "The PX Index stands at"),
        ("bodů (denní změna", "points (daily change"),
        ("Hlavní váhu v indexu drží finanční tituly (Erste Group, Komerční banka, Moneta Money Bank, VIG) a energetická skupina ČEZ.", "The index is heavily weighted toward financial blue chips (Erste Group, Komercni banka, Moneta Money Bank, VIG) and energy utility CEZ."),
        ("Pražská burza těží ze silné ziskovosti tuzemského bankovního sektoru, rostoucího objemu poskytnutých úvěrů a nadprůměrného dividendového výnosu.", "The Prague Stock Exchange benefits from strong profitability in the domestic banking sector, expanding loan volumes, and above-average dividend yields."),
        ("Vládní dluh ČR dosahuje", "CZ general government debt stands at"),
        ("HDP, výrazně pod 60% maastrichtským limitem", "of GDP, well below the 60% Maastricht limit"),
        ("Veřejné zadlužení České republiky činí", "Public debt of the Czech Republic stands at"),
        ("HDP (nominálně cca", "of GDP (nominally approx."),
        ("což zůstává hluboko pod průměrem eurozóny", "remaining well below the Eurozone average"),
        ("Klíčovým fiskálním tématem zůstává udržení schodku státního rozpočtu v zákonných limitech a řízení nákladů na obsluhu státního dluhu při vyšších výnosech dluhopisů.", "Keeping the state budget deficit within statutory fiscal rules and managing debt servicing costs amid higher bond yields remain key fiscal priorities."),
        ("Spread 10Y CZGB vs. 10Y Bund činí", "10Y CZGB vs. 10Y Bund spread stands at"),
        ("Rozpětí mezi výnosem 10Y českého dluhopisu", "The yield spread between the 10Y Czech government bond"),
        ("a německého Bundu", "and the German Bund"),
        ("činí", "stands at"),
        ("Spread odráží úrokový diferenciál mezi ČNB", "The spread reflects the policy rate differential between the CNB"),
        ("a ECB", "and the ECB"),
        ("Vysoká důvěra investorů a nízký podíl cizoměnového dluhu chrání české státní dluhopisy před vnějšími šoky.", "Strong investor confidence and a low share of foreign-currency debt insulate Czech government bonds from external shocks."),
        ("Předstihové indikátory: PMI v průmyslu na", "Leading indicators: Manufacturing PMI at"),
        ("souhrnná důvěra ČSÚ na", "CZSO composite confidence at"),
        ("Průmyslový index nákupních manažerů PMI dosahuje", "The Manufacturing Purchasing Managers' Index (PMI) stands at"),
        ("Konjunkturní indikátor důvěry ČSÚ činí", "The CZSO composite economic confidence indicator stands at"),
        ("Zatímco důvěra spotřebitelů a podnikatelů ve službách se drží nad dlouhodobým průměrem (100 b.), zpracovatelský průmysl se postupně stabilizuje poblíž 50bodové hranice.", "While consumer and services confidence holds near or above the long-term average (100 pts), manufacturing is gradually stabilizing near the 50-point threshold."),
        ("Růst mezd: Průměrná nominální mzda roste o", "Wage growth: Average nominal wage grows by"),
        ("reálná mzda o", "real wage by"),
        ("se nominální růst mezd", "nominal wage growth"),
        ("promítá do solidního růstu reálné kupní síly zaměstnanců o", "translates into solid real purchasing power gains of"),
        ("Pokračující reálný růst výdělků je hlavním pilířem oživení spotřeby domácností, zároveň však ČNB sleduje mzdovou dynamiku jako potenciální proinflační faktor ve službách.", "Continued real wage growth is the main pillar of recovering household consumption, though the CNB closely monitors wage dynamics as a potential pro-inflationary factor in services."),
        ("ČBA Hypomonitor: Průměrná sazba nových hypoték", "CBA Hypomonitor: Average new mortgage rate"),
        ("klesá na", "declines to"),
        ("pokles o", "down by"),
        ("roste na", "rises to"),
        ("nárůst o", "up by"),
        ("setrvává na", "holds steady at"),
        ("objem nových hypoték bez refinancování roste na", "new mortgage volume excl. refinancing rises to"),
        ("objem nových hypoték bez refinancování činí", "new mortgage volume excl. refinancing stands at"),
        ("objem nových hypoték bez refinancování dosahuje", "new mortgage volume excl. refinancing reaches"),
        ("Podle nejnovějších dat ČBA Hypomonitor a ČNB průměrná realizovaná úroková sazba nových hypoték činí", "According to the latest CBA Hypomonitor and CNB data, the average realized interest rate on new mortgages stands at"),
        ("předchozí měsíc", "previous month"),
        ("Měsíční objem skutečně nově poskytnutých hypoték bez refinancování dosahuje", "Monthly volume of newly originated mortgages excluding refinancing reaches"),
        ("Obrat v sazbách na trhu hypoték je tažen růstem tržních úrokových sazeb (delších korunových swapů IRS a výnosů státních dluhopisů).", "Mortgage rate dynamics are driven by movements in long-term market rates (CZK interest rate swaps and government bond yields)."),
        ("Objem firemních úvěrů meziročně roste o", "Corporate loan volume grows year-on-year by"),
        ("(tažen zejména cizoměnovými úvěry v eurech) a celkové vklady / M2 rostou o", "(driven notably by EUR-denominated corporate borrowing) and total deposits / M2 grow by"),
        ("Vnější rovnováha: Obchodní bilance v přebytku", "External balance: Trade balance records a surplus of"),
        ("běžný účet", "current account at"),
        ("Bilance zahraničního obchodu se zbožím (ČSÚ) dosahuje přebytku", "The foreign trade balance in goods (CZSO) posted a surplus of"),
        ("Běžný účet platební bilance vykazuje kladné saldo", "The current account of the balance of payments recorded a positive balance of"),
        ("Kladná obchodní bilance podpořená vývozem automobilového průmyslu a strojírenství dlouhodobě posiluje vnější rovnováhu české ekonomiky.", "A positive trade balance supported by automotive and machinery exports reinforces the external stability of the Czech economy."),
    ]

    for field in ("date", "source", "title", "reason", "context"):
        val = item.get(field)
        if isinstance(val, str) and val:
            for cs_str, en_str in news_replacements:
                val = val.replace(cs_str, en_str)
            item[field] = tr(val)
    return item


def translate_catalog_df(df_cat: Any) -> Any:
    """Translates the Indicator Catalog DataFrame values while keeping column names compatible with filtering."""
    if df_cat is None or getattr(df_cat, "empty", True) or not is_en():
        return df_cat

    df_out = df_cat.copy()
    freq_map = {
        "Denní (D) & Měsíční (M)": "Daily (D) & Monthly (M)",
        "Kvartální (Q) & Měsíční (M)": "Quarterly (Q) & Monthly (M)",
        "Kvartální (Q)": "Quarterly (Q)",
        "Měsíční (M)": "Monthly (M)",
    }
    region_map = {
        "🇨🇿 Česká republika": "🇨🇿 Czech Republic",
        "🇪🇺 Evropská unie": "🇪🇺 European Union",
        "🇺🇸 Spojené státy": "🇺🇸 United States",
    }

    for idx, row in df_out.iterrows():
        code = row.get("Kód indikátoru", "")
        en_meta = INDICATOR_I18N.get(code)
        if en_meta:
            df_out.at[idx, "Kategorie"] = en_meta["category"]
            df_out.at[idx, "Název ukazatele"] = en_meta["name"]
            df_out.at[idx, "Jednotka"] = en_meta["unit"]
            df_out.at[idx, "Metodický popis"] = en_meta["description"]
        if "Periodicita" in df_out.columns:
            p_val = str(row.get("Periodicita", ""))
            df_out.at[idx, "Periodicita"] = freq_map.get(p_val, tr(p_val))
        if "Primární zdroj dat" in df_out.columns:
            df_out.at[idx, "Primární zdroj dat"] = tr(str(row.get("Primární zdroj dat", "")))
        if "Země / Region" in df_out.columns:
            r_val = str(row.get("Země / Region", ""))
            df_out.at[idx, "Země / Region"] = region_map.get(r_val, tr(r_val))

    return df_out


def translate_catalog_display_df(df_disp: Any) -> Any:
    """Renames the displayed catalog DataFrame columns into English when is_en() is True."""
    if df_disp is None or getattr(df_disp, "empty", True) or not is_en():
        return df_disp
    col_map = {
        "Země / Region": "Country / Region",
        "Kategorie": "Category",
        "Název ukazatele": "Indicator Name",
        "Kód indikátoru": "Indicator Code",
        "Jednotka": "Unit",
        "Periodicita": "Frequency",
        "Primární zdroj dat": "Primary Data Source",
        "Metodický popis": "Methodological Description",
    }
    return df_disp.rename(columns=col_map)


def translate_export_df(df_exp: Any, indicators_dict: Any = None) -> Any:
    """Translates the Data Explorer / Export DataFrame column names into English when is_en() is True."""
    if df_exp is None or getattr(df_exp, "empty", True) or not is_en():
        return df_exp
    new_cols = {}
    new_cols["Datum"] = "Date"
    new_cols["Kvartál"] = "Quarter"
    if indicators_dict:
        for code, info in indicators_dict.items():
            cz_col = f"{info.name_cz} [{info.unit}]"
            en_meta = INDICATOR_I18N.get(code)
            if en_meta:
                new_cols[cz_col] = f"{en_meta['name']} [{en_meta['unit']}]"
    return df_exp.rename(columns=new_cols)


_STREAMLIT_PATCHED = False


def install_streamlit_i18n() -> None:
    """
    Installs transparent i18n wrappers around Streamlit's DeltaGenerator methods so all UI widgets,
    metrics, tabs, markdown, and captions automatically render in English when is_en() is True,
    while preserving 100% of underlying Python return values and widget keys.
    """
    global _STREAMLIT_PATCHED
    if _STREAMLIT_PATCHED:
        return
    _STREAMLIT_PATCHED = True

    from streamlit.delta_generator import DeltaGenerator

    orig_markdown = DeltaGenerator.markdown
    orig_caption = DeltaGenerator.caption
    orig_info = DeltaGenerator.info
    orig_warning = DeltaGenerator.warning
    orig_error = DeltaGenerator.error
    orig_metric = DeltaGenerator.metric
    orig_expander = DeltaGenerator.expander
    orig_button = DeltaGenerator.button
    orig_download_button = DeltaGenerator.download_button
    orig_checkbox = DeltaGenerator.checkbox
    orig_text_input = DeltaGenerator.text_input
    orig_selectbox = DeltaGenerator.selectbox
    orig_multiselect = DeltaGenerator.multiselect
    orig_radio = DeltaGenerator.radio
    orig_segmented_control = getattr(DeltaGenerator, "segmented_control", None)
    orig_tabs = DeltaGenerator.tabs
    orig_dataframe = DeltaGenerator.dataframe
    orig_write = DeltaGenerator.write

    def _wrap_write(self, *args, **kwargs):
        if is_en():
            args = tuple(tr(a) if isinstance(a, str) else a for a in args)
        return orig_write(self, *args, **kwargs)

    def _wrap_markdown(self, body, *args, **kwargs):
        if is_en() and isinstance(body, str):
            body = tr_html(body)
        return orig_markdown(self, body, *args, **kwargs)

    def _wrap_caption(self, body, *args, **kwargs):
        if is_en() and isinstance(body, str):
            body = tr(body)
        return orig_caption(self, body, *args, **kwargs)

    def _wrap_info(self, body, *args, **kwargs):
        if is_en() and isinstance(body, str):
            body = tr(body)
        return orig_info(self, body, *args, **kwargs)

    def _wrap_warning(self, body, *args, **kwargs):
        if is_en() and isinstance(body, str):
            body = tr(body)
        return orig_warning(self, body, *args, **kwargs)

    def _wrap_error(self, body, *args, **kwargs):
        if is_en() and isinstance(body, str):
            body = tr(body)
        return orig_error(self, body, *args, **kwargs)

    def _wrap_metric(self, label, value, delta=None, *args, **kwargs):
        if is_en():
            if isinstance(label, str):
                label = tr(label)
            if isinstance(value, str):
                value = tr(value)
            if isinstance(delta, str):
                delta = tr(delta)
            if isinstance(kwargs.get("help"), str):
                kwargs["help"] = tr(kwargs["help"])
        return orig_metric(self, label, value, delta, *args, **kwargs)

    def _wrap_expander(self, label, *args, **kwargs):
        if is_en() and isinstance(label, str):
            label = tr(label)
        return orig_expander(self, label, *args, **kwargs)

    def _wrap_button(self, label, *args, **kwargs):
        if is_en():
            if isinstance(label, str):
                label = tr(label)
            if isinstance(kwargs.get("help"), str):
                kwargs["help"] = tr(kwargs["help"])
        return orig_button(self, label, *args, **kwargs)

    def _wrap_download_button(self, label, *args, **kwargs):
        if is_en():
            if isinstance(label, str):
                label = tr(label)
            if isinstance(kwargs.get("help"), str):
                kwargs["help"] = tr(kwargs["help"])
        return orig_download_button(self, label, *args, **kwargs)

    def _wrap_checkbox(self, label, *args, **kwargs):
        if is_en():
            if isinstance(label, str):
                label = tr(label)
            if isinstance(kwargs.get("help"), str):
                kwargs["help"] = tr(kwargs["help"])
        return orig_checkbox(self, label, *args, **kwargs)

    def _wrap_text_input(self, label, *args, **kwargs):
        if is_en():
            if isinstance(label, str):
                label = tr(label)
            if isinstance(kwargs.get("placeholder"), str):
                kwargs["placeholder"] = tr(kwargs["placeholder"])
            if isinstance(kwargs.get("help"), str):
                kwargs["help"] = tr(kwargs["help"])
        return orig_text_input(self, label, *args, **kwargs)

    def _wrap_selection_kwargs(kwargs):
        if is_en():
            if isinstance(kwargs.get("help"), str):
                kwargs["help"] = tr(kwargs["help"])
            user_fmt = kwargs.get("format_func")
            if user_fmt is not None:
                kwargs["format_func"] = lambda x: tr(user_fmt(x))
            else:
                kwargs["format_func"] = lambda x: tr(str(x)) if isinstance(x, str) else x

    def _wrap_selectbox(self, label, options, *args, **kwargs):
        if is_en() and isinstance(label, str):
            label = tr(label)
        _wrap_selection_kwargs(kwargs)
        return orig_selectbox(self, label, options, *args, **kwargs)

    def _wrap_multiselect(self, label, options, *args, **kwargs):
        if is_en() and isinstance(label, str):
            label = tr(label)
        _wrap_selection_kwargs(kwargs)
        return orig_multiselect(self, label, options, *args, **kwargs)

    def _wrap_radio(self, label, options, *args, **kwargs):
        if is_en() and isinstance(label, str):
            label = tr(label)
        _wrap_selection_kwargs(kwargs)
        return orig_radio(self, label, options, *args, **kwargs)

    def _wrap_segmented_control(self, label, options, *args, **kwargs):
        if is_en() and isinstance(label, str):
            label = tr(label)
        # Do not double-wrap language switcher itself
        if kwargs.get("key", "").startswith("lang_switcher_"):
            return orig_segmented_control(self, label, options, *args, **kwargs)
        _wrap_selection_kwargs(kwargs)
        return orig_segmented_control(self, label, options, *args, **kwargs)

    def _wrap_tabs(self, tabs, *args, **kwargs):
        if is_en():
            tabs = [tr(t) if isinstance(t, str) else t for t in tabs]
            if kwargs.get("default") and isinstance(kwargs["default"], str):
                kwargs["default"] = tr(kwargs["default"])
            if kwargs.get("key") and isinstance(kwargs["key"], str):
                kwargs["key"] = f"{kwargs['key']}_en"
        return orig_tabs(self, tabs, *args, **kwargs)

    def _wrap_dataframe(self, data=None, *args, **kwargs):
        if is_en() and data is not None and hasattr(data, "columns"):
            if "Název ukazatele" in data.columns and "Kód indikátoru" in data.columns:
                data = translate_catalog_display_df(data)
        return orig_dataframe(self, data, *args, **kwargs)

    DeltaGenerator.markdown = _wrap_markdown
    DeltaGenerator.caption = _wrap_caption
    DeltaGenerator.info = _wrap_info
    DeltaGenerator.warning = _wrap_warning
    DeltaGenerator.error = _wrap_error
    DeltaGenerator.metric = _wrap_metric
    DeltaGenerator.expander = _wrap_expander
    DeltaGenerator.button = _wrap_button
    DeltaGenerator.download_button = _wrap_download_button
    DeltaGenerator.checkbox = _wrap_checkbox
    DeltaGenerator.text_input = _wrap_text_input
    DeltaGenerator.selectbox = _wrap_selectbox
    DeltaGenerator.multiselect = _wrap_multiselect
    DeltaGenerator.radio = _wrap_radio
    if orig_segmented_control is not None:
        DeltaGenerator.segmented_control = _wrap_segmented_control
    DeltaGenerator.tabs = _wrap_tabs
    DeltaGenerator.dataframe = _wrap_dataframe
    DeltaGenerator.write = _wrap_write
