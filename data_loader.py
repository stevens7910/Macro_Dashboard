"""
data_loader.py
==============
Modul pro načítání, transformaci a validaci českých a amerických makroekonomických dat.
Poskytuje třídu DataLoader s podporou pro:
- Veřejná REST API: Eurostat (CZ CPI, HDP, nezaměstnanost, dluh vládních institucí, 10Y dluhopisy),
  ČNB (PRIBOR, klíčové sazby, denní devizové kurzy EUR, USD, GBP, JPY, CHF)
  a U.S. Department of the Treasury (denní US výnosová křivka 1M–30Y).
- Globální FX konverze a denní data pro měnové páry EUR/CZK, USD/CZK, EUR/USD, GBP/USD, USD/JPY, DXY index.
- Volitelnou integraci FRED API (St. Louis Fed) pro uživatele s API klíčem.
- Odolný Fallback model: realistická denní, měsíční a kvartální data pro ČR i USA v období 2015–současnost.
- Měsíční (M) i kvartální (Q) agregaci časových řad + plnohodnotný denní dataset měnových kurzů.
- Caching pro Streamlit pomocí @st.cache_data.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup

# Konfigurace logování
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DataLoader")

# Kompatibilita pro pandas frekvence (novější pandas používá ME/QE místo M/Q)
PANDAS_VERSION = pd.__version__
OFFSET_MONTH_END = "ME" if PANDAS_VERSION >= "2.2" else "M"
OFFSET_QUARTER_END = "QE" if PANDAS_VERSION >= "2.2" else "Q"


@dataclass
class IndicatorInfo:
    """Metadatová definice makroekonomického indikátoru."""
    code: str
    name_cz: str
    unit: str
    category: str
    description: str
    region: str = "CZ"  # "CZ" nebo "US"


INDICATORS: Dict[str, IndicatorInfo] = {
    # =========================================================================
    # 🇨🇿 ČESKÁ REPUBLIKA (CZ)
    # =========================================================================
    "repo_rate": IndicatorInfo(
        code="repo_rate",
        name_cz="2T Repo sazba ČNB",
        unit="%",
        category="Měnová politika",
        description="Hlavní měnověpolitická sazba ČNB, kterou se úročí 2týdenní operace stahování likvidity z bankovního sektoru.",
        region="CZ"
    ),
    "discount_rate": IndicatorInfo(
        code="discount_rate",
        name_cz="Diskontní sazba ČNB",
        unit="%",
        category="Měnová politika",
        description="Spodní hranice koridoru sazeb ČNB (úročení přebytečné likvidity přes noc – depozitní facilita).",
        region="CZ"
    ),
    "lombard_rate": IndicatorInfo(
        code="lombard_rate",
        name_cz="Lombardní sazba ČNB",
        unit="%",
        category="Měnová politika",
        description="Horní hranice koridoru sazeb ČNB (půjčky likvidity přes noc proti kolaterálu – zápůjční facilita).",
        region="CZ"
    ),
    "pribor_1m": IndicatorInfo(
        code="pribor_1m",
        name_cz="PRIBOR 1M",
        unit="%",
        category="Mezibankovní trh",
        description="Prague Interbank Offered Rate pro splatnost 1 měsíc.",
        region="CZ"
    ),
    "pribor_3m": IndicatorInfo(
        code="pribor_3m",
        name_cz="PRIBOR 3M",
        unit="%",
        category="Mezibankovní trh",
        description="Klíčová referenční sazba mezibankovního trhu pro splatnost 3 měsíce (benchmark úvěrů a derivátů).",
        region="CZ"
    ),
    "pribor_6m": IndicatorInfo(
        code="pribor_6m",
        name_cz="PRIBOR 6M",
        unit="%",
        category="Mezibankovní trh",
        description="Referenční sazba mezibankovního trhu pro splatnost 6 měsíců.",
        region="CZ"
    ),
    "cpi_yoy": IndicatorInfo(
        code="cpi_yoy",
        name_cz="Inflace (CPI meziročně)",
        unit="%",
        category="Cenová hladina",
        description="Meziroční míra inflace vyjádřená indexem spotřebitelských cen (HICP / národní CPI).",
        region="CZ"
    ),
    "gdp_growth_real": IndicatorInfo(
        code="gdp_growth_real",
        name_cz="Reálný růst HDP (YoY)",
        unit="%",
        category="Hrubý domácí produkt",
        description="Meziroční reálná změna hrubého domácího produktu v řetězených objemech (očištěno o sezónnost a vliv cen).",
        region="CZ"
    ),
    "gdp_nominal_czk_bn": IndicatorInfo(
        code="gdp_nominal_czk_bn",
        name_cz="Nominální HDP ČR",
        unit="mld. CZK",
        category="Hrubý domácí produkt",
        description="Objem hrubého domácího produktu v běžných cenách v miliardách Kč za dané období.",
        region="CZ"
    ),
    "unemployment_rate": IndicatorInfo(
        code="unemployment_rate",
        name_cz="Míra nezaměstnanosti ČR",
        unit="%",
        category="Trh práce",
        description="Sezónně očištěná obecná míra nezaměstnanosti dle metodiky ILO / Eurostat pro věk 15–74 let.",
        region="CZ"
    ),
    "eur_czk": IndicatorInfo(
        code="eur_czk",
        name_cz="Měnový kurz EUR/CZK",
        unit="CZK",
        category="Měnové kurzy",
        description="Oficiální směnný kurz české koruny vůči euru (ČNB devizový trh – denní fixace).",
        region="CZ"
    ),
    "usd_czk": IndicatorInfo(
        code="usd_czk",
        name_cz="Měnový kurz USD/CZK",
        unit="CZK",
        category="Měnové kurzy",
        description="Oficiální směnný kurz české koruny vůči americkému dolaru (ČNB devizový trh – denní fixace).",
        region="CZ"
    ),
    "public_debt_czk_bn": IndicatorInfo(
        code="public_debt_czk_bn",
        name_cz="Veřejný dluh ČR",
        unit="mld. CZK",
        category="Fiskální politika",
        description="Konsolidovaný hrubý dluh sektoru vládních institucí (vládní/státní dluh) v mld. Kč.",
        region="CZ"
    ),
    "public_debt_gdp_pct": IndicatorInfo(
        code="public_debt_gdp_pct",
        name_cz="Veřejný dluh ČR k HDP",
        unit="% HDP",
        category="Fiskální politika",
        description="Poměr dluhu vládních institucí k HDP v % (maastrichtské fiskální kritérium s limitem 60 %).",
        region="CZ"
    ),
    "budget_deficit_czk_bn": IndicatorInfo(
        code="budget_deficit_czk_bn",
        name_cz="Saldo státního rozpočtu ČR",
        unit="mld. CZK",
        category="Fiskální politika",
        description="Saldo hospodaření státního rozpočtu (deficit je záporný, přebytek kladný) v mld. Kč.",
        region="CZ"
    ),
    "czgb_10y": IndicatorInfo(
        code="czgb_10y",
        name_cz="Výnos 10Y CZGB (benchmark)",
        unit="%",
        category="Dluhopisový trh",
        description="Výnos do splatnosti 10letého referenčního státního dluhopisu ČR (Eurostat Maastricht criterion).",
        region="CZ"
    ),
    "czgb_2y": IndicatorInfo(
        code="czgb_2y",
        name_cz="Výnos 2Y CZGB",
        unit="%",
        category="Dluhopisový trh",
        description="Výnos do splatnosti 2letého státního dluhopisu ČR (krátký konec dluhopisové křivky).",
        region="CZ"
    ),
    "czgb_5y": IndicatorInfo(
        code="czgb_5y",
        name_cz="Výnos 5Y CZGB",
        unit="%",
        category="Dluhopisový trh",
        description="Výnos do splatnosti 5letého státního dluhopisu ČR (střední segment křivky).",
        region="CZ"
    ),
    "czgb_15y": IndicatorInfo(
        code="czgb_15y",
        name_cz="Výnos 15Y CZGB",
        unit="%",
        category="Dluhopisový trh",
        description="Výnos do splatnosti 15letého státního dluhopisu ČR (dlouhý konec křivky).",
        region="CZ"
    ),
    "irs_10y": IndicatorInfo(
        code="irs_10y",
        name_cz="Sazba 10Y CZK IRS",
        unit="%",
        category="Derivátový trh (IRS)",
        description="Referenční tržní sazba úrokového swapu CZK IRS pro 10 let (mezibankovní benchmark pro ocenění fixací).",
        region="CZ"
    ),
    "irs_5y": IndicatorInfo(
        code="irs_5y",
        name_cz="Sazba 5Y CZK IRS",
        unit="%",
        category="Derivátový trh (IRS)",
        description="Referenční tržní sazba úrokového swapu CZK IRS pro 5 let (benchmark 5letých fixací hypoték v ČR).",
        region="CZ"
    ),
    "czgb_spread_10y_2y": IndicatorInfo(
        code="czgb_spread_10y_2y",
        name_cz="Sklon křivky CZGB (10Y − 2Y)",
        unit="p.b.",
        category="Dluhopisový trh",
        description="Sklon výnosové křivky (rozdíl mezi 10Y a 2Y výnosem). Záporná hodnota představuje inverzi křivky.",
        region="CZ"
    ),

    # =========================================================================
    # 🇺🇸 SPOJENÉ STÁTY (US)
    # =========================================================================
    "fed_funds_upper": IndicatorInfo(
        code="fed_funds_upper",
        name_cz="Fed Funds Target (horní mez)",
        unit="%",
        category="US Měnová politika",
        description="Horní hranice cílového koridoru základní úrokové sazby Federálního rezervního systému (Fed).",
        region="US"
    ),
    "fed_funds_lower": IndicatorInfo(
        code="fed_funds_lower",
        name_cz="Fed Funds Target (dolní mez)",
        unit="%",
        category="US Měnová politika",
        description="Dolní hranice cílového koridoru základní úrokové sazby Fedu.",
        region="US"
    ),
    "fed_effective_rate": IndicatorInfo(
        code="fed_effective_rate",
        name_cz="Efektivní sazba Fed Funds (EFFR)",
        unit="%",
        category="US Měnová politika",
        description="Vážená efektivní úroková sazba jednodenních mezibankovních rezervních fondů (EFFR).",
        region="US"
    ),
    "sofr_rate": IndicatorInfo(
        code="sofr_rate",
        name_cz="SOFR (Secured Overnight Rate)",
        unit="%",
        category="US Peněžní trh",
        description="Zajištěná jednodenní sazba financování krytá americkými státními dluhopisy (nástupce USD LIBOR).",
        region="US"
    ),
    "us_1m": IndicatorInfo(
        code="us_1m",
        name_cz="Výnos 1M US Treasury Bill",
        unit="%",
        category="US Peněžní trh",
        description="Výnos 1měsíční americké pokladniční poukázky (krátkodobá bezriziková sazba).",
        region="US"
    ),
    "us_3m": IndicatorInfo(
        code="us_3m",
        name_cz="Výnos 3M US Treasury Bill",
        unit="%",
        category="US Peněžní trh",
        description="Výnos 3měsíční pokladniční poukázky USA (klíčový benchmark peněžního trhu USD).",
        region="US"
    ),
    "us_cpi_yoy": IndicatorInfo(
        code="us_cpi_yoy",
        name_cz="Inflace USA (CPI meziročně)",
        unit="%",
        category="US Cenová hladina",
        description="Meziroční míra spotřebitelské inflace v USA (Headline Consumer Price Index – U.S. BLS).",
        region="US"
    ),
    "us_core_cpi_yoy": IndicatorInfo(
        code="us_core_cpi_yoy",
        name_cz="Jádrová inflace USA (Core CPI)",
        unit="%",
        category="US Cenová hladina",
        description="Meziroční míra jádrové inflace v USA očištěná o volatilní ceny potravin a energií.",
        region="US"
    ),
    "us_gdp_growth_real": IndicatorInfo(
        code="us_gdp_growth_real",
        name_cz="Reálný růst HDP USA (YoY)",
        unit="%",
        category="US Hrubý domácí produkt",
        description="Meziroční změna reálného hrubého domácího produktu USA (U.S. Bureau of Economic Analysis).",
        region="US"
    ),
    "us_gdp_nominal_usd_bn": IndicatorInfo(
        code="us_gdp_nominal_usd_bn",
        name_cz="Nominální HDP USA",
        unit="mld. USD",
        category="US Hrubý domácí produkt",
        description="Objem hrubého domácího produktu USA v běžných cenách v miliardách USD.",
        region="US"
    ),
    "us_unemployment_rate": IndicatorInfo(
        code="us_unemployment_rate",
        name_cz="Míra nezaměstnanosti USA (U-3)",
        unit="%",
        category="US Trh práce",
        description="Oficiální míra nezaměstnanosti v USA (U.S. Bureau of Labor Statistics U-3 rate).",
        region="US"
    ),
    "us_nonfarm_payrolls_k": IndicatorInfo(
        code="us_nonfarm_payrolls_k",
        name_cz="Tvorba pracovních míst (NFP)",
        unit="tis. míst",
        category="US Trh práce",
        description="Měsíční přírůstek nových pracovních míst mimo zemědělský sektor v USA (U.S. BLS Nonfarm Payrolls).",
        region="US"
    ),
    "dxy_index": IndicatorInfo(
        code="dxy_index",
        name_cz="Dolarový index (DXY)",
        unit="body",
        category="US Měnové kurzy",
        description="U.S. Dollar Index vyjadřující relativní hodnotu amerického dolaru vůči koši světových měn.",
        region="US"
    ),
    "eur_usd": IndicatorInfo(
        code="eur_usd",
        name_cz="Měnový kurz EUR/USD",
        unit="USD",
        category="US Měnové kurzy",
        description="Směnný kurz eura vůči americkému dolaru (největší devizový trh světa).",
        region="US"
    ),
    "usd_jpy": IndicatorInfo(
        code="usd_jpy",
        name_cz="Měnový kurz USD/JPY",
        unit="JPY",
        category="US Měnové kurzy",
        description="Směnný kurz amerického dolaru vůči japonskému jenu.",
        region="US"
    ),
    "gbp_usd": IndicatorInfo(
        code="gbp_usd",
        name_cz="Měnový kurz GBP/USD",
        unit="USD",
        category="US Měnové kurzy",
        description="Směnný kurz britské libry vůči americkému dolaru (Cable).",
        region="US"
    ),
    "usd_chf": IndicatorInfo(
        code="usd_chf",
        name_cz="Měnový kurz USD/CHF",
        unit="CHF",
        category="US Měnové kurzy",
        description="Směnný kurz amerického dolaru vůči švýcarskému franku.",
        region="US"
    ),
    "us_public_debt_usd_bn": IndicatorInfo(
        code="us_public_debt_usd_bn",
        name_cz="Federální dluh USA",
        unit="mld. USD",
        category="US Fiskální politika",
        description="Celkový hrubý veřejný dluh federální vlády USA (Total Public Debt Outstanding).",
        region="US"
    ),
    "us_public_debt_gdp_pct": IndicatorInfo(
        code="us_public_debt_gdp_pct",
        name_cz="Federální dluh USA k HDP",
        unit="% HDP",
        category="US Fiskální politika",
        description="Poměr veřejného dluhu USA k nominálnímu HDP v %.",
        region="US"
    ),
    "us_budget_deficit_usd_bn": IndicatorInfo(
        code="us_budget_deficit_usd_bn",
        name_cz="Saldo federálního rozpočtu USA",
        unit="mld. USD",
        category="US Fiskální politika",
        description="Kvartální saldo hospodaření federální vlády USA (deficit je záporný) v mld. USD.",
        region="US"
    ),
    "us_10y": IndicatorInfo(
        code="us_10y",
        name_cz="Výnos 10Y US Treasury (benchmark)",
        unit="%",
        category="US Dluhopisový trh",
        description="Výnos do splatnosti 10letého referenčního státního dluhopisu USA (globální benchmark ocenění aktiv).",
        region="US"
    ),
    "us_2y": IndicatorInfo(
        code="us_2y",
        name_cz="Výnos 2Y US Treasury",
        unit="%",
        category="US Dluhopisový trh",
        description="Výnos do splatnosti 2letého vládního dluhopisu USA (krátký konec citlivý na sazby Fedu).",
        region="US"
    ),
    "us_5y": IndicatorInfo(
        code="us_5y",
        name_cz="Výnos 5Y US Treasury",
        unit="%",
        category="US Dluhopisový trh",
        description="Výnos do splatnosti 5letého státního dluhopisu USA (střední segment americké křivky).",
        region="US"
    ),
    "us_30y": IndicatorInfo(
        code="us_30y",
        name_cz="Výnos 30Y US Treasury Bond",
        unit="%",
        category="US Dluhopisový trh",
        description="Výnos do splatnosti 30letého dlouhodobého vládního dluhopisu USA (Long Bond).",
        region="US"
    ),
    "us_spread_10y_2y": IndicatorInfo(
        code="us_spread_10y_2y",
        name_cz="Sklon US křivky (10Y − 2Y)",
        unit="p.b.",
        category="US Dluhopisový trh",
        description="Rozdíl mezi 10Y a 2Y americkým vládním výnosem (hlavní globální indikátor recese při inverzi).",
        region="US"
    )
}

# Rychlé filtry indikátorů podle regionu
CZ_INDICATORS: Dict[str, IndicatorInfo] = {k: v for k, v in INDICATORS.items() if v.region == "CZ"}
US_INDICATORS: Dict[str, IndicatorInfo] = {k: v for k, v in INDICATORS.items() if v.region == "US"}


class DataLoader:
    """
    Robustní třída pro stahování, parsing a agregaci dat z veřejných REST API
    s automatickým fallbackem na realistický historický model pro ČR i USA.
    """

    def __init__(self, request_timeout: int = 8):
        self.timeout = request_timeout
        self.headers = {
            "User-Agent": "CzechMacroDashboard/2.0 (Mozilla/5.0; Macro Terminal System)"
        }
        self.source_status: Dict[str, str] = {}
        self.last_fetch_time: Optional[datetime] = None

    # =========================================================================
    # 1. LIVE API: Eurostat (CPI, Nezaměstnanost, HDP, Vládní dluh, 10Y CZGB)
    # =========================================================================

    def fetch_eurostat_cpi(self) -> pd.DataFrame:
        """Stáhne meziroční inflaci (HICP) pro Českou republiku z Eurostat REST API."""
        url = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/prc_hicp_manr?geo=CZ&coicop=CP00"
        resp = requests.get(url, headers=self.headers, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()

        time_labels = list(data.get("dimension", {}).get("time", {}).get("category", {}).get("label", {}).values())
        values_dict = data.get("value", {})

        records = []
        for idx, t_str in enumerate(time_labels):
            val = values_dict.get(str(idx))
            if val is not None:
                dt = pd.to_datetime(t_str) + pd.offsets.MonthEnd(0)
                records.append({"date": dt, "cpi_yoy": float(val)})

        if not records:
            raise ValueError("Eurostat CPI vrátil prázdný dataset.")

        return pd.DataFrame(records).sort_values("date").drop_duplicates("date").reset_index(drop=True)

    def fetch_eurostat_unemployment(self) -> pd.DataFrame:
        """Stáhne sezónně očištěnou míru nezaměstnanosti pro ČR z Eurostat REST API."""
        url = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/une_rt_m?geo=CZ&s_adj=SA&age=TOTAL&unit=PC_ACT&sex=T"
        resp = requests.get(url, headers=self.headers, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()

        time_labels = list(data.get("dimension", {}).get("time", {}).get("category", {}).get("label", {}).values())
        values_dict = data.get("value", {})

        records = []
        for idx, t_str in enumerate(time_labels):
            val = values_dict.get(str(idx))
            if val is not None:
                dt = pd.to_datetime(t_str) + pd.offsets.MonthEnd(0)
                records.append({"date": dt, "unemployment_rate": float(val)})

        if not records:
            raise ValueError("Eurostat nezaměstnanost vrátil prázdný dataset.")

        return pd.DataFrame(records).sort_values("date").drop_duplicates("date").reset_index(drop=True)

    def fetch_eurostat_gdp(self) -> pd.DataFrame:
        """Stáhne reálný růst HDP (YoY) a nominální HDP v CZK z Eurostat REST API."""
        url_real = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/namq_10_gdp?geo=CZ&unit=CLV_PCH_SM&s_adj=SCA&na_item=B1GQ"
        url_nom = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/namq_10_gdp?geo=CZ&unit=CP_MNAC&s_adj=NSA&na_item=B1GQ"

        r_real = requests.get(url_real, headers=self.headers, timeout=self.timeout)
        r_real.raise_for_status()
        d_real = r_real.json()

        r_nom = requests.get(url_nom, headers=self.headers, timeout=self.timeout)
        r_nom.raise_for_status()
        d_nom = r_nom.json()

        t_real = list(d_real.get("dimension", {}).get("time", {}).get("category", {}).get("label", {}).values())
        v_real = d_real.get("value", {})

        t_nom = list(d_nom.get("dimension", {}).get("time", {}).get("category", {}).get("label", {}).values())
        v_nom = d_nom.get("value", {})

        nom_map = {}
        for idx, t_str in enumerate(t_nom):
            val = v_nom.get(str(idx))
            if val is not None:
                nom_map[t_str] = float(val) / 1000.0  # mil. CZK -> mld. CZK

        records = []
        for idx, t_str in enumerate(t_real):
            val_r = v_real.get(str(idx))
            val_n = nom_map.get(t_str)
            if val_r is not None or val_n is not None:
                year_part, q_part = t_str.split("-Q")
                quarter_end_month = int(q_part) * 3
                dt = pd.to_datetime(f"{year_part}-{quarter_end_month:02d}-01") + pd.offsets.MonthEnd(0)
                records.append({
                    "date": dt,
                    "quarter": t_str,
                    "gdp_growth_real": float(val_r) if val_r is not None else None,
                    "gdp_nominal_czk_bn": float(val_n) if val_n is not None else None
                })

        if not records:
            raise ValueError("Eurostat HDP vrátil prázdný dataset.")

        return pd.DataFrame(records).sort_values("date").drop_duplicates("date").reset_index(drop=True)

    def fetch_eurostat_debt(self) -> pd.DataFrame:
        """Stáhne konsolidovaný dluh vládních institucí v % HDP a v milionech CZK z Eurostatu."""
        url_pct = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/gov_10q_ggdebt?geo=CZ&unit=PC_GDP&sector=S13&na_item=GD"
        url_czk = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/gov_10q_ggdebt?geo=CZ&unit=MIO_NAC&sector=S13&na_item=GD"

        r_pct = requests.get(url_pct, headers=self.headers, timeout=self.timeout)
        r_pct.raise_for_status()
        d_pct = r_pct.json()

        r_czk = requests.get(url_czk, headers=self.headers, timeout=self.timeout)
        r_czk.raise_for_status()
        d_czk = r_czk.json()

        t_pct = list(d_pct.get("dimension", {}).get("time", {}).get("category", {}).get("label", {}).values())
        v_pct = d_pct.get("value", {})
        v_czk = d_czk.get("value", {})

        records = []
        for idx_str, val in v_pct.items():
            quarter_label = t_pct[int(idx_str)]
            val_czk = v_czk.get(idx_str)
            if quarter_label and val is not None:
                year_part, q_part = quarter_label.split("-Q")
                quarter_end_month = int(q_part) * 3
                dt = pd.to_datetime(f"{year_part}-{quarter_end_month:02d}-01") + pd.offsets.MonthEnd(0)
                records.append({
                    "date": dt,
                    "quarter": quarter_label,
                    "public_debt_gdp_pct": float(val),
                    "public_debt_czk_bn": float(val_czk) / 1000.0 if val_czk is not None else None
                })

        if not records:
            raise ValueError("Eurostat vládní dluh vrátil prázdný dataset.")

        return pd.DataFrame(records).sort_values("date").drop_duplicates("date").reset_index(drop=True)

    def fetch_eurostat_10y_bond(self) -> pd.DataFrame:
        """Stáhne dlouhodobé výnosy 10letých státních dluhopisů ČR (Maastrichtské kritérium) z Eurostatu."""
        url = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/irt_lt_mcby_m?geo=CZ"
        resp = requests.get(url, headers=self.headers, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()

        time_labels = list(data.get("dimension", {}).get("time", {}).get("category", {}).get("label", {}).values())
        vals_dict = data.get("value", {})

        records = []
        for idx, t_str in enumerate(time_labels):
            val = vals_dict.get(str(idx))
            if val is not None:
                dt = pd.to_datetime(t_str) + pd.offsets.MonthEnd(0)
                records.append({"date": dt, "czgb_10y": float(val)})

        if not records:
            raise ValueError("Eurostat 10Y výnosy dluhopisů vrátily prázdný dataset.")

        return pd.DataFrame(records).sort_values("date").drop_duplicates("date").reset_index(drop=True)

    @staticmethod
    def compute_curve_tenors(repo_val: float, y10_val: float) -> Tuple[Dict[str, float], Dict[str, float]]:
        """
        Vygeneruje tenorskou strukturu výnosové křivky CZGB a IRS pro splatnosti 1Y, 2Y, 3Y, 5Y, 7Y, 10Y, 15Y.
        """
        tenor_years = [1, 2, 3, 5, 7, 10, 15]
        diff = y10_val - repo_val
        czgb: Dict[str, float] = {}
        irs: Dict[str, float] = {}
        w_10 = 1.0 - np.exp(-10.0 / 3.2)
        for t in tenor_years:
            w_t = (1.0 - np.exp(-t / 3.2)) / w_10
            y = repo_val + diff * w_t
            if t == 1:
                y = repo_val + (0.15 if diff >= 0 else -0.40)
            elif t == 15:
                y = y10_val + (0.18 if diff >= 0 else 0.05)
            y = max(0.05, float(y))
            czgb[f"czgb_{t}y"] = round(y, 2)
            asw_spread = 0.16 + 0.018 * min(t, 10)
            irs[f"irs_{t}y"] = round(y + asw_spread, 2)
        return czgb, irs

    # =========================================================================
    # 2. LIVE API: ČNB (PRIBOR, Sazby ČNB, DENNÍ DEVIZOVÉ KURZY)
    # =========================================================================

    def fetch_cnb_pribor(self, start_year: int = 2015, end_year: int = 2026) -> pd.DataFrame:
        """Stáhne denní hodnoty PRIBOR (1M, 3M, 6M) z otevřeného REST API ČNB."""
        all_records = []
        for yr in range(start_year, end_year + 1):
            url = f"https://api.cnb.cz/cnbapi/pribor/daily-year?year={yr}"
            try:
                resp = requests.get(url, headers=self.headers, timeout=self.timeout)
                if resp.status_code == 200:
                    for it in resp.json().get("priborRates", []):
                        all_records.append({
                            "date": pd.to_datetime(it["date"]),
                            "maturity": it["maturity"],
                            "rate": float(it["rate"])
                        })
            except Exception as e:
                logger.warning("Chyba při stahování PRIBOR dat pro rok %d: %s", yr, e)

        if not all_records:
            raise ValueError("ČNB PRIBOR API nevrátilo žádné záznamy.")

        df_raw = pd.DataFrame(all_records)
        pivot = df_raw.pivot_table(index="date", columns="maturity", values="rate", aggfunc="last").reset_index()
        pivot = pivot.rename(columns={
            "ONE_MONTH": "pribor_1m",
            "THREE_MONTH": "pribor_3m",
            "SIX_MONTH": "pribor_6m"
        })
        return pivot.sort_values("date").reset_index(drop=True)

    def fetch_cnb_policy_rates(self) -> pd.DataFrame:
        """
        Stáhne kompletní historii změn hlavních sazeb ČNB (2T repo, diskontní a lombardní)
        a vytvoří souvislou denní časovou řadu.
        """
        slug_map = {
            "repo_rate": "Jak-se-vyvijela-dvoutydenni-repo-sazba-CNB",
            "discount_rate": "Jak-se-vyvijela-diskontni-sazba-CNB",
            "lombard_rate": "Jak-se-vyvijela-lombardni-sazba-CNB"
        }
        series_dict: Dict[str, pd.DataFrame] = {}

        for col, slug in slug_map.items():
            url = f"https://www.cnb.cz/cs/casto-kladene-dotazy/{slug}/"
            resp = requests.get(url, headers=self.headers, timeout=self.timeout)
            resp.raise_for_status()

            soup = BeautifulSoup(resp.text, "html.parser")
            table = soup.find("table")
            if not table:
                raise ValueError(f"Tabulka se sazbami nebyla nalezena na {url}")

            rows = table.find_all("tr")
            items = []
            for row in rows[1:]:
                cols = [c.get_text(strip=True).replace("\xa0", " ") for c in row.find_all(["td", "th"])]
                if len(cols) >= 2:
                    try:
                        dt = pd.to_datetime(cols[0], format="%d.%m.%Y")
                        val_str = cols[1].replace(",", ".").replace("%", "").strip()
                        items.append({"date": dt, col: float(val_str)})
                    except Exception:
                        continue

            if not items:
                raise ValueError(f"Žádná data sazeb neparsována pro {col}")

            series_dict[col] = pd.DataFrame(items).sort_values("date").drop_duplicates("date")

        today = pd.to_datetime(datetime.now().strftime("%Y-%m-%d"))
        timeline = pd.date_range("2015-01-01", today, freq="D")
        df_daily = pd.DataFrame({"date": timeline})

        for col, df_sub in series_dict.items():
            merged = pd.merge(df_daily, df_sub, on="date", how="left")
            prior = df_sub[df_sub["date"] <= pd.to_datetime("2015-01-01")]
            init_val = prior.iloc[-1][col] if not prior.empty else df_sub.iloc[0][col]
            if pd.isna(merged.loc[0, col]):
                merged.loc[0, col] = init_val
            merged[col] = merged[col].ffill()
            df_daily[col] = merged[col]

        return df_daily

    def fetch_cnb_fx_daily(self, start_year: int = 2015, end_year: int = 2026) -> pd.DataFrame:
        """
        Stáhne kompletní historii denních devizových kurzů z REST API ČNB (daily-year).
        Vypočítá přímé kurzy vůči CZK (EUR/CZK, USD/CZK, GBP/CZK, CHF/CZK)
        a světové měnové páry (EUR/USD, GBP/USD, USD/JPY, USD/CHF, DXY Index).
        """
        records = []
        for yr in range(start_year, end_year + 1):
            url = f"https://api.cnb.cz/cnbapi/exrates/daily-year?year={yr}"
            try:
                resp = requests.get(url, headers=self.headers, timeout=self.timeout)
                if resp.status_code == 200:
                    for it in resp.json().get("rates", []):
                        cc = it.get("currencyCode")
                        if cc in ("EUR", "USD", "GBP", "JPY", "CHF"):
                            amt = float(it.get("amount", 1))
                            rate = float(it.get("rate", 0))
                            records.append({
                                "date": pd.to_datetime(it["validFor"]),
                                "currency": cc,
                                "unit_rate": rate / amt if amt > 0 else rate
                            })
            except Exception as e:
                logger.warning("Chyba při stahování denních kurzů ČNB pro rok %d: %s", yr, e)

        if not records:
            raise ValueError("ČNB Daily FX API nevrátilo žádné záznamy.")

        df_raw = pd.DataFrame(records)
        pivot = df_raw.pivot_table(index="date", columns="currency", values="unit_rate", aggfunc="last").reset_index()
        pivot = pivot.sort_values("date").reset_index(drop=True)

        for c in ["EUR", "USD", "GBP", "JPY", "CHF"]:
            if c in pivot.columns:
                pivot[c] = pivot[c].ffill().bfill()

        df_out = pd.DataFrame()
        df_out["date"] = pivot["date"]

        # CZ Páry
        if "EUR" in pivot.columns:
            df_out["eur_czk"] = np.round(pivot["EUR"], 4)
        if "USD" in pivot.columns:
            df_out["usd_czk"] = np.round(pivot["USD"], 4)
        if "GBP" in pivot.columns:
            df_out["gbp_czk"] = np.round(pivot["GBP"], 4)
        if "CHF" in pivot.columns:
            df_out["chf_czk"] = np.round(pivot["CHF"], 4)

        # US & Globální křížové páry
        if "EUR" in pivot.columns and "USD" in pivot.columns:
            df_out["eur_usd"] = np.round(pivot["EUR"] / pivot["USD"], 4)
        if "GBP" in pivot.columns and "USD" in pivot.columns:
            df_out["gbp_usd"] = np.round(pivot["GBP"] / pivot["USD"], 4)
        if "USD" in pivot.columns and "JPY" in pivot.columns:
            df_out["usd_jpy"] = np.round(pivot["USD"] / pivot["JPY"], 3)
        if "USD" in pivot.columns and "CHF" in pivot.columns:
            df_out["usd_chf"] = np.round(pivot["USD"] / pivot["CHF"], 4)

        # ICE U.S. Dollar Index (DXY) vážený geometrický vzorec
        if "eur_usd" in df_out.columns and "usd_jpy" in df_out.columns and "gbp_usd" in df_out.columns:
            dxy = 50.14348112 * (df_out["eur_usd"] ** -0.576) * (df_out["usd_jpy"] ** 0.136) * (df_out["gbp_usd"] ** -0.119)
            if "usd_chf" in df_out.columns:
                dxy = dxy * (df_out["usd_chf"] ** 0.036)
            df_out["dxy_index"] = np.round(dxy, 2)

        return df_out.sort_values("date").drop_duplicates("date").reset_index(drop=True)

    def fetch_cnb_fx_rates(self, start_year: int = 2015, end_year: int = 2026) -> pd.DataFrame:
        """Kompatibilní metoda vracející agregovaná měsíční FX data."""
        df_daily = self.fetch_cnb_fx_daily(start_year, end_year)
        df_m = df_daily.set_index("date").resample(OFFSET_MONTH_END).last().reset_index()
        return df_m

    # =========================================================================
    # 3. LIVE API: U.S. DEPARTMENT OF THE TREASURY (Výnosová křivka US 1M–30Y)
    # =========================================================================

    def fetch_us_treasury_yields(self, start_year: int = 2024, end_year: int = 2026) -> pd.DataFrame:
        """
        Stáhne denní výnosy amerických státních dluhopisů (US Daily Treasury Par Yield Curve Rates)
        přímo z oficiálního otevřeného XML API U.S. Department of the Treasury.
        """
        import xml.etree.ElementTree as ET

        ns = {
            "atom": "http://www.w3.org/2005/Atom",
            "d": "http://schemas.microsoft.com/ado/2007/08/dataservices",
            "m": "http://schemas.microsoft.com/ado/2007/08/dataservices/metadata"
        }
        cols = {
            "BC_1MONTH": "us_1m",
            "BC_3MONTH": "us_3m",
            "BC_6MONTH": "us_6m",
            "BC_1YEAR": "us_1y",
            "BC_2YEAR": "us_2y",
            "BC_3YEAR": "us_3y",
            "BC_5YEAR": "us_5y",
            "BC_7YEAR": "us_7y",
            "BC_10YEAR": "us_10y",
            "BC_20YEAR": "us_20y",
            "BC_30YEAR": "us_30y"
        }

        records = []
        for yr in range(start_year, end_year + 1):
            url = f"https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml?data=daily_treasury_yield_curve&field_tdr_date_value={yr}"
            try:
                resp = requests.get(url, headers=self.headers, timeout=self.timeout)
                if resp.status_code == 200:
                    root = ET.fromstring(resp.content)
                    for entry in root.findall("atom:entry", ns):
                        props = entry.find("atom:content/m:properties", ns)
                        if props is None:
                            continue
                        d_elem = props.find("d:NEW_DATE", ns)
                        if d_elem is None or not d_elem.text:
                            continue
                        dt = pd.to_datetime(d_elem.text.split("T")[0])
                        row = {"date": dt}
                        for xml_tag, col_name in cols.items():
                            val_elem = props.find(f"d:{xml_tag}", ns)
                            if val_elem is not None and val_elem.text:
                                try:
                                    row[col_name] = float(val_elem.text)
                                except (ValueError, TypeError):
                                    row[col_name] = None
                            else:
                                row[col_name] = None
                        records.append(row)
            except Exception as e:
                logger.warning("Chyba při stahování US Treasury dat pro rok %d: %s", yr, e)

        if not records:
            raise ValueError("US Treasury API nevrátilo žádné záznamy.")

        df_daily = pd.DataFrame(records).sort_values("date").drop_duplicates("date").reset_index(drop=True)
        return df_daily

    # =========================================================================
    # 4. VOLITELNÉ API: FRED (Federal Reserve Bank of St. Louis)
    # =========================================================================

    def fetch_fred_series(self, series_id: str, api_key: str) -> pd.DataFrame:
        """Stáhne časovou řadu z FRED API při zadání platného API klíče."""
        url = f"https://api.stlouisfed.org/fred/series/observations?series_id={series_id}&api_key={api_key}&file_type=json"
        resp = requests.get(url, headers=self.headers, timeout=self.timeout)
        resp.raise_for_status()
        observations = resp.json().get("observations", [])
        records = []
        for obs in observations:
            val_str = obs.get("value")
            if val_str and val_str != ".":
                try:
                    records.append({
                        "date": pd.to_datetime(obs["date"]),
                        "value": float(val_str)
                    })
                except (ValueError, TypeError):
                    continue
        return pd.DataFrame(records)

    # =========================================================================
    # 5. HISTORICKÝ FALLBACK MODEL (2015–2026: ČR, USA a DENNÍ FX)
    # =========================================================================

    def generate_fallback_daily_fx(self) -> pd.DataFrame:
        """Vygeneruje souvislý denní dataset devizových kurzů 2015–2026."""
        dates_d = pd.date_range("2015-01-01", "2026-10-10", freq="B")
        np.random.seed(101)
        n = len(dates_d)

        # EUR/CZK trend
        eur_base = 27.02 + np.cumsum(np.random.normal(-0.0007, 0.04, n))
        eur_base = np.clip(eur_base, 23.40, 27.50)

        # USD/CZK trend
        usd_base = 24.50 + np.cumsum(np.random.normal(-0.0008, 0.05, n))
        usd_base = np.clip(usd_base, 20.80, 25.80)

        gbp_base = eur_base * 1.18 + np.random.normal(0, 0.05, n)
        chf_base = eur_base * 0.95 + np.random.normal(0, 0.04, n)

        eur_usd = eur_base / usd_base
        gbp_usd = gbp_base / usd_base
        usd_jpy = 110.0 + np.cumsum(np.random.normal(0.012, 0.35, n))
        usd_jpy = np.clip(usd_jpy, 102.0, 161.0)
        usd_chf = usd_base / chf_base

        dxy = 50.14348112 * (eur_usd ** -0.576) * (usd_jpy ** 0.136) * (gbp_usd ** -0.119) * (usd_chf ** 0.036)

        df = pd.DataFrame({
            "date": dates_d,
            "eur_czk": np.round(eur_base, 4),
            "usd_czk": np.round(usd_base, 4),
            "gbp_czk": np.round(gbp_base, 4),
            "chf_czk": np.round(chf_base, 4),
            "eur_usd": np.round(eur_usd, 4),
            "gbp_usd": np.round(gbp_usd, 4),
            "usd_jpy": np.round(usd_jpy, 3),
            "usd_chf": np.round(usd_chf, 4),
            "dxy_index": np.round(dxy, 2)
        })
        return df

    def generate_fallback_dataset(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Generuje realistická historická data pro ČR i USA za období 2015–2026.
        Vrací trojici (df_monthly, df_quarterly, df_daily_fx).
        """
        dates_m = pd.date_range("2015-01-01", "2026-10-01", freq=OFFSET_MONTH_END)
        n_m = len(dates_m)

        # ---------------------------------------------------------------------
        # A. ČR: Sazby ČNB a PRIBOR
        # ---------------------------------------------------------------------
        repo_series = []
        for d in dates_m:
            yr, mo = d.year, d.month
            if yr < 2017 or (yr == 2017 and mo < 8):
                rate = 0.05
            elif yr == 2017:
                rate = 0.25 if mo < 11 else 0.50
            elif yr == 2018:
                if mo < 2:
                    rate = 0.50
                elif mo < 6:
                    rate = 0.75
                elif mo < 8:
                    rate = 1.00
                elif mo < 9:
                    rate = 1.25
                elif mo < 11:
                    rate = 1.50
                else:
                    rate = 1.75
            elif yr == 2019:
                rate = 1.75 if mo < 5 else 2.00
            elif yr == 2020:
                if mo < 2:
                    rate = 2.00
                elif mo == 2:
                    rate = 2.25
                elif mo == 3:
                    rate = 1.75
                elif mo == 4:
                    rate = 1.00
                else:
                    rate = 0.25
            elif yr == 2021:
                if mo < 6:
                    rate = 0.25
                elif mo < 8:
                    rate = 0.50
                elif mo < 9:
                    rate = 0.75
                elif mo < 11:
                    rate = 1.50
                else:
                    rate = 2.75
            elif yr == 2022:
                if mo < 2:
                    rate = 3.75
                elif mo < 3:
                    rate = 4.50
                elif mo < 5:
                    rate = 5.00
                elif mo < 6:
                    rate = 5.75
                else:
                    rate = 7.00
            elif yr == 2023:
                rate = 7.00 if mo < 12 else 6.75
            elif yr == 2024:
                rates_24 = [6.25, 5.75, 5.75, 5.25, 4.75, 4.75, 4.50, 4.50, 4.25, 4.00, 4.00, 4.00]
                rate = rates_24[mo - 1]
            elif yr == 2025:
                rates_25 = [4.00, 3.75, 3.75, 3.75, 3.50, 3.50, 3.50, 3.50, 3.50, 3.50, 3.50, 3.50]
                rate = rates_25[mo - 1]
            else:
                rate = 3.50 if mo < 6 else 3.75
            repo_series.append(rate)

        repo_arr = np.array(repo_series)
        discount_arr = np.maximum(0.05, repo_arr - 1.0)
        lombard_arr = repo_arr + 1.0

        np.random.seed(42)
        noise = np.random.normal(0, 0.02, n_m)
        pribor_1m = np.maximum(0.08, repo_arr + 0.06 + noise)
        pribor_3m = np.maximum(0.12, repo_arr + 0.12 + noise * 1.2)
        pribor_6m = np.maximum(0.18, repo_arr + 0.22 + noise * 1.5)

        # ---------------------------------------------------------------------
        # B. ČR: Inflace CPI & Nezaměstnanost
        # ---------------------------------------------------------------------
        cpi_series = []
        for d in dates_m:
            yr, mo = d.year, d.month
            if yr == 2015:
                cpi = 0.3 + 0.1 * np.sin(mo)
            elif yr == 2016:
                cpi = 0.7 + 0.3 * (mo / 12)
            elif yr == 2017:
                cpi = 2.4 + 0.2 * np.cos(mo)
            elif yr == 2018:
                cpi = 2.1 + 0.3 * np.sin(mo)
            elif yr == 2019:
                cpi = 2.8 + 0.2 * (mo / 12)
            elif yr == 2020:
                cpi = 3.2 - 0.5 * (mo / 12)
            elif yr == 2021:
                cpi = 3.1 + 3.5 * (mo / 12)
            elif yr == 2022:
                traj = [9.9, 11.1, 12.7, 14.2, 16.0, 17.2, 17.5, 17.2, 18.0, 15.1, 16.2, 15.8]
                cpi = traj[mo - 1]
            elif yr == 2023:
                traj = [17.5, 16.7, 15.0, 12.7, 11.1, 9.7, 8.8, 8.5, 6.9, 8.5, 7.3, 6.9]
                cpi = traj[mo - 1]
            elif yr == 2024:
                traj = [2.3, 2.0, 2.0, 2.9, 2.6, 2.0, 2.2, 2.2, 2.6, 2.8, 2.8, 2.7]
                cpi = traj[mo - 1]
            elif yr == 2025:
                cpi = 2.4 + 0.2 * np.sin(mo)
            else:
                cpi = 2.3 - 0.2 * (mo / 10)
            cpi_series.append(round(cpi, 1))

        une_series = []
        for d in dates_m:
            yr, mo = d.year, d.month
            if yr == 2015:
                une = 5.2 - 0.8 * (mo / 12)
            elif yr == 2016:
                une = 4.2 - 0.6 * (mo / 12)
            elif yr == 2017:
                une = 3.4 - 0.8 * (mo / 12)
            elif yr == 2018:
                une = 2.4 - 0.2 * (mo / 12)
            elif yr == 2019:
                une = 2.0 + 0.1 * np.sin(mo)
            elif yr == 2020:
                une = 2.1 + 0.9 * (mo / 12)
            elif yr == 2021:
                une = 3.0 - 0.7 * (mo / 12)
            elif yr == 2022:
                une = 2.3 + 0.1 * np.cos(mo)
            elif yr == 2023:
                une = 2.6 + 0.1 * np.sin(mo)
            elif yr == 2024:
                une = 2.7 + 0.2 * (mo / 12)
            elif yr == 2025:
                une = 2.8 + 0.1 * np.cos(mo)
            else:
                une = 2.8
            une_series.append(round(une, 1))

        # ---------------------------------------------------------------------
        # C. ČR: Dluhopisy CZGB & Úrokové swapy IRS
        # ---------------------------------------------------------------------
        y10_series = []
        for d in dates_m:
            yr, mo = d.year, d.month
            if yr == 2015:
                y10 = 0.55 + 0.15 * np.sin(mo)
            elif yr == 2016:
                y10 = 0.42 - 0.10 * (mo / 12)
            elif yr == 2017:
                y10 = 0.70 + 0.80 * (mo / 12)
            elif yr == 2018:
                y10 = 1.95 + 0.20 * np.cos(mo)
            elif yr == 2019:
                y10 = 1.65 - 0.25 * (mo / 12)
            elif yr == 2020:
                y10 = 1.25 + 0.15 * np.sin(mo)
            elif yr == 2021:
                y10 = 1.60 + 1.25 * (mo / 12)
            elif yr == 2022:
                traj_10y = [3.2, 3.5, 4.0, 4.4, 4.9, 5.4, 5.2, 4.8, 5.1, 5.5, 5.3, 5.0]
                y10 = traj_10y[mo - 1]
            elif yr == 2023:
                traj_10y = [4.7, 4.8, 4.9, 4.7, 4.8, 4.6, 4.5, 4.6, 4.7, 4.8, 4.6, 4.3]
                y10 = traj_10y[mo - 1]
            elif yr == 2024:
                traj_10y = [4.1, 4.0, 4.2, 4.3, 4.4, 4.2, 4.1, 4.1, 4.0, 4.2, 4.2, 4.1]
                y10 = traj_10y[mo - 1]
            elif yr == 2025:
                y10 = 4.25 + 0.15 * np.sin(mo)
            else:
                y10 = 4.40
            y10_series.append(round(y10, 2))

        curve_records_czgb = []
        curve_records_irs = []
        for r_val, y10_val in zip(repo_arr, y10_series):
            c_czgb, c_irs = DataLoader.compute_curve_tenors(float(r_val), float(y10_val))
            curve_records_czgb.append(c_czgb)
            curve_records_irs.append(c_irs)

        df_czgb_m = pd.DataFrame(curve_records_czgb)
        df_irs_m = pd.DataFrame(curve_records_irs)

        # ---------------------------------------------------------------------
        # D. USA: Sazby Fedu, Peněžní trh & Výnosová křivka US Treasury
        # ---------------------------------------------------------------------
        fed_upper_series = []
        us_cpi_series = []
        us_core_cpi_series = []
        us_une_series = []
        us_nfp_series = []
        us_10y_series = []
        us_2y_series = []
        us_3m_series = []

        for d in dates_m:
            yr, mo = d.year, d.month
            # Fed Funds Target Upper
            if yr == 2015:
                fu = 0.25 if mo < 12 else 0.50
                ucpi = 0.4
                ucore = 1.8
                u_une = 5.3
                unfp = 220
                y10, y2, y3m = 2.15 + 0.15 * np.sin(mo), 0.65, 0.05
            elif yr == 2016:
                fu = 0.50 if mo < 12 else 0.75
                ucpi = 1.3
                ucore = 2.2
                u_une = 4.9
                unfp = 200
                y10, y2, y3m = 1.85, 0.85, 0.30
            elif yr == 2017:
                fu = 1.00 if mo < 6 else (1.25 if mo < 12 else 1.50)
                ucpi = 2.1
                ucore = 1.8
                u_une = 4.4
                unfp = 180
                y10, y2, y3m = 2.35, 1.40, 0.95
            elif yr == 2018:
                fu = 1.75 if mo < 6 else (2.00 if mo < 9 else (2.25 if mo < 12 else 2.50))
                ucpi = 2.4
                ucore = 2.2
                u_une = 3.9
                unfp = 190
                y10, y2, y3m = 2.90, 2.50, 2.00
            elif yr == 2019:
                fu = 2.50 if mo < 8 else (2.25 if mo < 9 else (2.00 if mo < 11 else 1.75))
                ucpi = 1.8
                ucore = 2.3
                u_une = 3.7
                unfp = 175
                y10, y2, y3m = 2.15, 1.95, 2.10
            elif yr == 2020:
                fu = 1.75 if mo < 3 else 0.25
                ucpi = 1.2
                ucore = 1.6
                u_une = 3.6 if mo < 3 else (14.7 if mo == 4 else (10.2 if mo < 8 else 6.7))
                unfp = -20500 if mo == 4 else (4800 if mo == 6 else 150)
                y10, y2, y3m = 0.90, 0.25, 0.15
            elif yr == 2021:
                fu = 0.25
                ucpi = 2.6 + (mo / 12) * 4.4
                ucore = 1.6 + (mo / 12) * 3.8
                u_une = 6.3 - (mo / 12) * 2.4
                unfp = 450
                y10, y2, y3m = 1.45, 0.45, 0.05
            elif yr == 2022:
                fed_traj = [0.25, 0.25, 0.50, 0.50, 1.00, 1.75, 2.50, 2.50, 3.25, 3.25, 4.00, 4.50]
                cpi_traj = [7.5, 7.9, 8.5, 8.3, 8.6, 9.1, 8.5, 8.3, 8.2, 7.7, 7.1, 6.5]
                core_traj = [6.0, 6.4, 6.5, 6.2, 6.0, 5.9, 5.9, 6.3, 6.6, 6.3, 6.0, 5.7]
                fu = fed_traj[mo - 1]
                ucpi = cpi_traj[mo - 1]
                ucore = core_traj[mo - 1]
                u_une = 3.6
                unfp = 380
                traj_10 = [1.8, 2.0, 2.3, 2.8, 2.9, 3.1, 2.9, 3.0, 3.6, 4.0, 3.9, 3.8]
                traj_2 = [1.0, 1.4, 2.3, 2.6, 2.6, 2.9, 2.9, 3.4, 4.1, 4.4, 4.4, 4.3]
                traj_3m = [0.2, 0.4, 0.5, 0.8, 1.1, 1.6, 2.4, 2.9, 3.3, 4.1, 4.3, 4.4]
                y10, y2, y3m = traj_10[mo - 1], traj_2[mo - 1], traj_3m[mo - 1]
            elif yr == 2023:
                fed_traj = [4.50, 4.75, 5.00, 5.00, 5.25, 5.25, 5.50, 5.50, 5.50, 5.50, 5.50, 5.50]
                cpi_traj = [6.4, 6.0, 5.0, 4.9, 4.0, 3.0, 3.2, 3.7, 3.7, 3.2, 3.1, 3.4]
                core_traj = [5.6, 5.5, 5.6, 5.5, 5.3, 4.8, 4.7, 4.3, 4.1, 4.0, 4.0, 3.9]
                fu = fed_traj[mo - 1]
                ucpi = cpi_traj[mo - 1]
                ucore = core_traj[mo - 1]
                u_une = 3.6
                unfp = 250
                traj_10 = [3.5, 3.8, 3.6, 3.5, 3.6, 3.8, 4.0, 4.2, 4.4, 4.8, 4.5, 4.0]
                traj_2 = [4.2, 4.7, 4.1, 4.0, 4.3, 4.8, 4.8, 4.9, 5.0, 5.0, 4.7, 4.3]
                traj_3m = [4.6, 4.8, 4.9, 5.1, 5.3, 5.4, 5.4, 5.4, 5.5, 5.5, 5.4, 5.3]
                y10, y2, y3m = traj_10[mo - 1], traj_2[mo - 1], traj_3m[mo - 1]
            elif yr == 2024:
                fed_traj = [5.50, 5.50, 5.50, 5.50, 5.50, 5.50, 5.50, 5.50, 5.00, 5.00, 4.75, 4.50]
                cpi_traj = [3.1, 3.2, 3.5, 3.4, 3.3, 3.0, 2.9, 2.5, 2.4, 2.6, 2.7, 2.7]
                core_traj = [3.9, 3.8, 3.8, 3.6, 3.4, 3.3, 3.2, 3.2, 3.3, 3.3, 3.3, 3.2]
                fu = fed_traj[mo - 1]
                ucpi = cpi_traj[mo - 1]
                ucore = core_traj[mo - 1]
                u_une = 4.1
                unfp = 180
                traj_10 = [4.1, 4.2, 4.2, 4.6, 4.5, 4.3, 4.2, 3.9, 3.8, 4.2, 4.3, 4.5]
                traj_2 = [4.3, 4.6, 4.6, 4.9, 4.8, 4.7, 4.4, 3.9, 3.6, 4.1, 4.2, 4.3]
                traj_3m = [5.3, 5.4, 5.4, 5.4, 5.4, 5.3, 5.2, 5.1, 4.9, 4.6, 4.5, 4.4]
                y10, y2, y3m = traj_10[mo - 1], traj_2[mo - 1], traj_3m[mo - 1]
            elif yr == 2025:
                fu = 4.50 if mo < 6 else 4.25
                ucpi = 2.5
                ucore = 2.8
                u_une = 4.1
                unfp = 160
                y10, y2, y3m = 4.55, 4.35, 4.30
            else:
                fu = 4.00
                ucpi = 2.3
                ucore = 2.6
                u_une = 4.2
                unfp = 150
                y10, y2, y3m = 4.40, 4.15, 3.95

            fed_upper_series.append(fu)
            us_cpi_series.append(round(ucpi, 1))
            us_core_cpi_series.append(round(ucore, 1))
            us_une_series.append(round(u_une, 1))
            us_nfp_series.append(unfp)
            us_10y_series.append(round(y10, 2))
            us_2y_series.append(round(y2, 2))
            us_3m_series.append(round(y3m, 2))

        fu_arr = np.array(fed_upper_series)
        fl_arr = np.maximum(0.0, fu_arr - 0.25)
        effr_arr = np.maximum(0.05, fu_arr - 0.17)
        sofr_arr = np.maximum(0.05, fu_arr - 0.19)

        us_curve_records = []
        for y10, y2, y3m in zip(us_10y_series, us_2y_series, us_3m_series):
            diff = y10 - y2
            y1m = max(0.02, y3m - 0.05)
            y6m = max(0.05, y3m + 0.08)
            y1y = max(0.08, y2 - 0.15 if diff >= 0 else y2 + 0.10)
            y3y = y2 + 0.3 * diff
            y5y = y2 + 0.6 * diff
            y7y = y2 + 0.85 * diff
            y20y = y10 + (0.35 if diff >= 0 else 0.15)
            y30y = y10 + (0.28 if diff >= 0 else 0.10)
            us_curve_records.append({
                "us_1m": round(y1m, 2),
                "us_3m": round(y3m, 2),
                "us_6m": round(y6m, 2),
                "us_1y": round(y1y, 2),
                "us_2y": round(y2, 2),
                "us_3y": round(y3y, 2),
                "us_5y": round(y5y, 2),
                "us_7y": round(y7y, 2),
                "us_10y": round(y10, 2),
                "us_20y": round(y20y, 2),
                "us_30y": round(y30y, 2),
                "us_spread_10y_2y": round(y10 - y2, 2),
            })
        df_us_curve_m = pd.DataFrame(us_curve_records)

        # ---------------------------------------------------------------------
        # E. DENNÍ DEVÍZOVÝ DATASET A MĚSÍČNÍ AGREGACE
        # ---------------------------------------------------------------------
        df_daily_fx = self.generate_fallback_daily_fx()
        df_fx_m = pd.merge_asof(
            pd.DataFrame({"date": dates_m}),
            df_daily_fx.sort_values("date"),
            on="date",
            direction="backward"
        )

        df_monthly_data = {
            "date": dates_m,
            # CZ
            "repo_rate": np.round(repo_arr, 2),
            "discount_rate": np.round(discount_arr, 2),
            "lombard_rate": np.round(lombard_arr, 2),
            "pribor_1m": np.round(pribor_1m, 2),
            "pribor_3m": np.round(pribor_3m, 2),
            "pribor_6m": np.round(pribor_6m, 2),
            "cpi_yoy": cpi_series,
            "unemployment_rate": une_series,
            "eur_czk": df_fx_m["eur_czk"],
            "usd_czk": df_fx_m["usd_czk"],
            "gbp_czk": df_fx_m["gbp_czk"],
            "chf_czk": df_fx_m["chf_czk"],
            "czgb_10y": df_czgb_m["czgb_10y"],
            "czgb_1y": df_czgb_m["czgb_1y"],
            "czgb_2y": df_czgb_m["czgb_2y"],
            "czgb_3y": df_czgb_m["czgb_3y"],
            "czgb_5y": df_czgb_m["czgb_5y"],
            "czgb_7y": df_czgb_m["czgb_7y"],
            "czgb_15y": df_czgb_m["czgb_15y"],
            "irs_1y": df_irs_m["irs_1y"],
            "irs_2y": df_irs_m["irs_2y"],
            "irs_3y": df_irs_m["irs_3y"],
            "irs_5y": df_irs_m["irs_5y"],
            "irs_7y": df_irs_m["irs_7y"],
            "irs_10y": df_irs_m["irs_10y"],
            "irs_15y": df_irs_m["irs_15y"],
            "czgb_spread_10y_2y": np.round(df_czgb_m["czgb_10y"] - df_czgb_m["czgb_2y"], 2),
            # US
            "fed_funds_upper": np.round(fu_arr, 2),
            "fed_funds_lower": np.round(fl_arr, 2),
            "fed_effective_rate": np.round(effr_arr, 2),
            "sofr_rate": np.round(sofr_arr, 2),
            "us_1m": df_us_curve_m["us_1m"],
            "us_3m": df_us_curve_m["us_3m"],
            "us_6m": df_us_curve_m["us_6m"],
            "us_1y": df_us_curve_m["us_1y"],
            "us_2y": df_us_curve_m["us_2y"],
            "us_3y": df_us_curve_m["us_3y"],
            "us_5y": df_us_curve_m["us_5y"],
            "us_7y": df_us_curve_m["us_7y"],
            "us_10y": df_us_curve_m["us_10y"],
            "us_20y": df_us_curve_m["us_20y"],
            "us_30y": df_us_curve_m["us_30y"],
            "us_spread_10y_2y": df_us_curve_m["us_spread_10y_2y"],
            "us_cpi_yoy": us_cpi_series,
            "us_core_cpi_yoy": us_core_cpi_series,
            "us_unemployment_rate": us_une_series,
            "us_nonfarm_payrolls_k": us_nfp_series,
            "dxy_index": df_fx_m["dxy_index"],
            "eur_usd": df_fx_m["eur_usd"],
            "gbp_usd": df_fx_m["gbp_usd"],
            "usd_jpy": df_fx_m["usd_jpy"],
            "usd_chf": df_fx_m["usd_chf"]
        }
        df_monthly = pd.DataFrame(df_monthly_data)

        # ---------------------------------------------------------------------
        # F. Kvartální HDP, Veřejný dluh a Deficity (ČR i USA)
        # ---------------------------------------------------------------------
        dates_q = pd.date_range("2015-01-01", "2026-07-01", freq=OFFSET_QUARTER_END)
        q_records = []

        gdp_growth_map_cz = {
            2015: [5.5, 5.6, 5.2, 5.0],
            2016: [2.8, 2.5, 2.3, 2.4],
            2017: [5.0, 5.2, 5.4, 5.1],
            2018: [3.5, 3.2, 3.1, 2.9],
            2019: [3.2, 3.1, 2.9, 2.7],
            2020: [-1.8, -10.8, -5.0, -4.4],
            2021: [-2.1, 8.5, 3.9, 4.0],
            2022: [4.2, 3.4, 1.6, 0.4],
            2023: [-0.4, -0.6, -0.5, 0.3],
            2024: [0.6, 0.8, 1.2, 1.6],
            2025: [2.0, 2.3, 2.5, 2.6],
            2026: [2.1, 1.8]
        }

        gdp_growth_map_us = {
            2015: [3.3, 2.7, 2.4, 2.3],
            2016: [1.6, 1.4, 1.9, 2.0],
            2017: [2.0, 2.3, 2.3, 2.5],
            2018: [2.8, 3.0, 3.0, 2.6],
            2019: [2.2, 2.4, 2.5, 2.6],
            2020: [0.3, -8.6, -2.2, -1.8],
            2021: [1.2, 12.2, 4.9, 5.4],
            2022: [3.6, 1.9, 1.7, 0.7],
            2023: [1.7, 2.4, 2.9, 3.1],
            2024: [2.9, 3.0, 2.8, 2.5],
            2025: [2.2, 2.3, 2.4, 2.2],
            2026: [2.1, 2.0]
        }

        fiscal_map_cz = {
            2015: (1673.0, 39.9, -62.8),
            2016: (1613.0, 36.6, 61.8),
            2017: (1625.0, 34.2, -6.2),
            2018: (1622.0, 32.1, 2.9),
            2019: (1640.0, 30.0, -28.5),
            2020: (2050.0, 37.7, -367.4),
            2021: (2466.0, 42.0, -419.7),
            2022: (2895.0, 44.2, -360.4),
            2023: (3111.0, 44.0, -288.5),
            2024: (3340.0, 43.8, -282.0),
            2025: (3580.0, 43.5, -241.0),
            2026: (3820.0, 44.1, -220.0),
        }

        nom_base_cz = 1150.0
        nom_base_us = 4500.0  # kvartální US nominální HDP (v mld. USD, roční ~18 000 mld.)
        debt_base_us = 18150.0
        quarter_idx = 0

        for d in dates_q:
            yr = d.year
            q_num = (d.month - 1) // 3 + 1

            # CZ HDP & Dluh
            growth_vals_cz = gdp_growth_map_cz.get(yr, [2.0, 2.0, 2.0, 2.0])
            growth_cz = growth_vals_cz[min(q_num - 1, len(growth_vals_cz) - 1)]
            nom_cz = nom_base_cz + (quarter_idx * 24.5)
            if yr in (2022, 2023):
                nom_cz += 40.0 * (yr - 2021)
            debt_nom_cz, debt_pct_cz, def_ann_cz = fiscal_map_cz.get(yr, (3000.0, 44.0, -250.0))
            debt_q_cz = debt_nom_cz + (q_num - 2) * 35.0
            def_q_cz = def_ann_cz / 4.0

            # US HDP & Dluh
            growth_vals_us = gdp_growth_map_us.get(yr, [2.2, 2.2, 2.2, 2.2])
            growth_us = growth_vals_us[min(q_num - 1, len(growth_vals_us) - 1)]
            nom_us = nom_base_us + (quarter_idx * 65.0)
            if yr >= 2021:
                nom_us += 80.0 * (yr - 2020)

            debt_us = debt_base_us + (quarter_idx * 370.0)
            if yr == 2020:
                debt_us += 2000.0
            debt_pct_us = min(125.0, 101.0 + (quarter_idx * 0.55))
            def_q_us = -350.0 - (quarter_idx * 3.5)
            if yr == 2020:
                def_q_us = -780.0

            q_records.append({
                "date": d,
                "quarter": f"{yr}-Q{q_num}",
                "gdp_growth_real": round(growth_cz, 1),
                "gdp_nominal_czk_bn": round(nom_cz, 1),
                "public_debt_czk_bn": round(debt_q_cz, 1),
                "public_debt_gdp_pct": round(debt_pct_cz + (q_num - 2) * 0.2, 1),
                "budget_deficit_czk_bn": round(def_q_cz, 1),
                "us_gdp_growth_real": round(growth_us, 1),
                "us_gdp_nominal_usd_bn": round(nom_us * 4.0, 1),  # anualizovaný nominál
                "us_public_debt_usd_bn": round(debt_us, 1),
                "us_public_debt_gdp_pct": round(debt_pct_us, 1),
                "us_budget_deficit_usd_bn": round(def_q_us, 1)
            })
            quarter_idx += 1

        df_quarterly_macro = pd.DataFrame(q_records)

        # Propojení kvartálních indikátorů do měsíčního datasetu
        df_monthly = pd.merge_asof(
            df_monthly.sort_values("date"),
            df_quarterly_macro.sort_values("date"),
            on="date",
            direction="nearest"
        )

        # Sestavení kvartálního agregovaného datasetu
        agg_rules: Dict[str, str] = {c: "mean" for c in df_monthly.columns if c not in ("date", "quarter")}
        # Specifická pravidla agregace
        for col_last in ["repo_rate", "discount_rate", "lombard_rate", "fed_funds_upper", "fed_funds_lower", "eur_czk", "usd_czk", "eur_usd", "dxy_index"]:
            if col_last in agg_rules:
                agg_rules[col_last] = "last"

        # Kvartální dataframe agregovaný z měsíčního
        df_quarterly = df_monthly.set_index("date").resample(OFFSET_QUARTER_END).agg(agg_rules).reset_index()
        df_quarterly["quarter"] = df_quarterly["date"].dt.year.astype(str) + "-Q" + ((df_quarterly["date"].dt.month - 1) // 3 + 1).astype(str)

        return df_monthly, df_quarterly, df_daily_fx

    # =========================================================================
    # 6. HLAVNÍ METODA NAČTENÍ A SJEDNOCENÍ
    # =========================================================================

    def load_macro_data(
        self,
        frequency: str = "M",
        fred_api_key: Optional[str] = None,
        force_fallback: bool = False
    ) -> Tuple[pd.DataFrame, Dict[str, Any], pd.DataFrame]:
        """
        Hlavní metoda pro načtení kompletního makroekonomického datasetu pro ČR i USA.
        Vrací trojici (final_df, status_info, df_daily_fx).
        """
        self.last_fetch_time = datetime.now()
        status_info: Dict[str, Any] = {
            "mode": "FALLBACK" if force_fallback else "LIVE",
            "fetch_timestamp": self.last_fetch_time.strftime("%d.%m.%Y %H:%M:%S"),
            "endpoints": {},
            "frequency": frequency,
            "errors": []
        }

        # Základní matice z robustního fallback modelu
        df_fb_m, df_fb_q, df_daily_fx_fallback = self.generate_fallback_dataset()
        base_df = df_fb_m if frequency == "M" else df_fb_q
        df_daily_fx = df_daily_fx_fallback.copy()

        if force_fallback:
            status_info["mode"] = "FALLBACK"
            status_info["status_badge"] = "🟠 Fallback Model (Historická data ČR & USA 2015–2026)"
            return base_df, status_info, df_daily_fx

        live_components: Dict[str, pd.DataFrame] = {}
        all_success = True

        # 1. Eurostat: CPI ČR
        try:
            df_cpi = self.fetch_eurostat_cpi()
            live_components["cpi"] = df_cpi
            status_info["endpoints"]["Eurostat CPI (ČR)"] = "🟢 OK (Live)"
        except Exception as e:
            logger.warning("Chyba načítání Eurostat CPI: %s", e)
            status_info["endpoints"]["Eurostat CPI (ČR)"] = f"⚠️ Fallback ({type(e).__name__})"
            status_info["errors"].append(f"Eurostat CPI: {e}")
            all_success = False

        # 2. Eurostat: Nezaměstnanost ČR
        try:
            df_une = self.fetch_eurostat_unemployment()
            live_components["unemployment"] = df_une
            status_info["endpoints"]["Eurostat Nezaměstnanost (ČR)"] = "🟢 OK (Live)"
        except Exception as e:
            logger.warning("Chyba načítání Eurostat Nezaměstnanost: %s", e)
            status_info["endpoints"]["Eurostat Nezaměstnanost (ČR)"] = f"⚠️ Fallback ({type(e).__name__})"
            status_info["errors"].append(f"Eurostat Nezaměstnanost: {e}")
            all_success = False

        # 3. Eurostat: HDP ČR
        try:
            df_gdp = self.fetch_eurostat_gdp()
            live_components["gdp"] = df_gdp
            status_info["endpoints"]["Eurostat HDP (ČR)"] = "🟢 OK (Live)"
        except Exception as e:
            logger.warning("Chyba načítání Eurostat HDP: %s", e)
            status_info["endpoints"]["Eurostat HDP (ČR)"] = f"⚠️ Fallback ({type(e).__name__})"
            status_info["errors"].append(f"Eurostat HDP: {e}")
            all_success = False

        # 4. Eurostat: Veřejný dluh ČR
        try:
            df_debt = self.fetch_eurostat_debt()
            live_components["debt"] = df_debt
            status_info["endpoints"]["Eurostat Veřejný dluh (ČR)"] = "🟢 OK (Live)"
        except Exception as e:
            logger.warning("Chyba načítání Eurostat Veřejný dluh: %s", e)
            status_info["endpoints"]["Eurostat Veřejný dluh (ČR)"] = f"⚠️ Fallback ({type(e).__name__})"
            status_info["errors"].append(f"Eurostat Veřejný dluh: {e}")

        # 5. ČNB: Sazby měnové politiky
        try:
            df_rates = self.fetch_cnb_policy_rates()
            live_components["rates"] = df_rates
            status_info["endpoints"]["ČNB Sazby (Repo, Diskont, Lombard)"] = "🟢 OK (Live)"
        except Exception as e:
            logger.warning("Chyba načítání ČNB sazeb: %s", e)
            status_info["endpoints"]["ČNB Sazby"] = f"⚠️ Fallback ({type(e).__name__})"
            status_info["errors"].append(f"ČNB Sazby: {e}")
            all_success = False

        # 6. ČNB: PRIBOR
        try:
            current_year = datetime.now().year
            df_prib = self.fetch_cnb_pribor(start_year=2015, end_year=current_year)
            live_components["pribor"] = df_prib
            status_info["endpoints"]["ČNB PRIBOR (1M, 3M, 6M)"] = "🟢 OK (Live)"
        except Exception as e:
            logger.warning("Chyba načítání ČNB PRIBOR: %s", e)
            status_info["endpoints"]["ČNB PRIBOR"] = f"⚠️ Fallback ({type(e).__name__})"
            status_info["errors"].append(f"ČNB PRIBOR: {e}")
            all_success = False

        # 7. ČNB: DENNÍ DEVÍZOVÉ KURZY (EUR, USD, GBP, JPY, CHF & DXY)
        try:
            current_year = datetime.now().year
            df_fx_daily_live = self.fetch_cnb_fx_daily(start_year=2015, end_year=current_year)
            if not df_fx_daily_live.empty:
                df_daily_fx = df_fx_daily_live
                live_components["fx_daily"] = df_fx_daily_live
                status_info["endpoints"]["ČNB Denní kurzy (EUR, USD, JPY, DXY)"] = "🟢 OK (Live Denní data)"
        except Exception as e:
            logger.warning("Chyba načítání denních kurzů ČNB: %s", e)
            status_info["endpoints"]["ČNB Denní kurzy"] = f"⚠️ Fallback ({type(e).__name__})"
            status_info["errors"].append(f"ČNB Denní kurzy: {e}")

        # 8. Eurostat: 10Y Státní dluhopisy ČR
        try:
            df_b10 = self.fetch_eurostat_10y_bond()
            live_components["bond_10y"] = df_b10
            status_info["endpoints"]["Eurostat 10Y CZGB Bond"] = "🟢 OK (Live)"
        except Exception as e:
            logger.warning("Chyba načítání Eurostat 10Y bondu: %s", e)
            status_info["endpoints"]["Eurostat 10Y CZGB Bond"] = f"⚠️ Fallback ({type(e).__name__})"
            status_info["errors"].append(f"Eurostat 10Y Bond: {e}")

        # 9. U.S. Treasury: Výnosová křivka US (1M až 30Y)
        try:
            current_year = datetime.now().year
            df_us_live = self.fetch_us_treasury_yields(start_year=2024, end_year=current_year)
            live_components["us_treasury"] = df_us_live
            status_info["endpoints"]["U.S. Treasury (home.treasury.gov)"] = "🟢 OK (Live)"
        except Exception as e:
            logger.warning("Chyba načítání US Treasury: %s", e)
            status_info["endpoints"]["U.S. Treasury"] = f"⚠️ Fallback ({type(e).__name__})"
            status_info["errors"].append(f"U.S. Treasury: {e}")

        # 10. Volitelně FRED API (pokud je zadán klíč)
        if fred_api_key and fred_api_key.strip():
            try:
                df_fred_cpi = self.fetch_fred_series("CPIAUCSL", fred_api_key.strip())
                if not df_fred_cpi.empty:
                    df_fred_cpi["date"] = df_fred_cpi["date"] + pd.offsets.MonthEnd(0)
                    df_fred_cpi["us_cpi_yoy"] = df_fred_cpi["value"].pct_change(12) * 100.0
                    live_components["us_cpi"] = df_fred_cpi.dropna(subset=["us_cpi_yoy"])
                    status_info["endpoints"]["FRED API (U.S. CPI)"] = "🔵 OK (Ověřeno)"
            except Exception as e:
                logger.warning("FRED API selhalo: %s", e)
                status_info["endpoints"]["FRED API"] = f"❌ Chyba ({e})"
                status_info["errors"].append(f"FRED API: {e}")

        # Sloučení komponent do finálního datasetu
        final_df = base_df.copy()

        if "rates" in live_components:
            df_r = live_components["rates"]
            df_r_agg = df_r.set_index("date").resample(OFFSET_MONTH_END if frequency == "M" else OFFSET_QUARTER_END).last().reset_index()
            final_df = pd.merge(final_df.drop(columns=["repo_rate", "discount_rate", "lombard_rate"], errors="ignore"),
                                df_r_agg[["date", "repo_rate", "discount_rate", "lombard_rate"]], on="date", how="left")
            final_df["repo_rate"] = final_df["repo_rate"].ffill()
            final_df["discount_rate"] = final_df["discount_rate"].ffill()
            final_df["lombard_rate"] = final_df["lombard_rate"].ffill()

        if "pribor" in live_components:
            df_p = live_components["pribor"]
            df_p_agg = df_p.set_index("date").resample(OFFSET_MONTH_END if frequency == "M" else OFFSET_QUARTER_END).mean().reset_index()
            final_df = pd.merge(final_df.drop(columns=["pribor_1m", "pribor_3m", "pribor_6m"], errors="ignore"),
                                df_p_agg[["date", "pribor_1m", "pribor_3m", "pribor_6m"]], on="date", how="left")
            final_df["pribor_1m"] = final_df["pribor_1m"].ffill()
            final_df["pribor_3m"] = final_df["pribor_3m"].ffill()
            final_df["pribor_6m"] = final_df["pribor_6m"].ffill()

        if "cpi" in live_components:
            df_c = live_components["cpi"]
            if frequency == "Q":
                df_c = df_c.set_index("date").resample(OFFSET_QUARTER_END).mean().reset_index()
            final_df = pd.merge(final_df.drop(columns=["cpi_yoy"], errors="ignore"),
                                df_c[["date", "cpi_yoy"]], on="date", how="left")
            final_df["cpi_yoy"] = final_df["cpi_yoy"].ffill()

        if "unemployment" in live_components:
            df_u = live_components["unemployment"]
            if frequency == "Q":
                df_u = df_u.set_index("date").resample(OFFSET_QUARTER_END).mean().reset_index()
            final_df = pd.merge(final_df.drop(columns=["unemployment_rate"], errors="ignore"),
                                df_u[["date", "unemployment_rate"]], on="date", how="left")
            final_df["unemployment_rate"] = final_df["unemployment_rate"].ffill()

        if "gdp" in live_components:
            df_g = live_components["gdp"]
            if frequency == "M":
                final_df = pd.merge_asof(
                    final_df.drop(columns=["gdp_growth_real", "gdp_nominal_czk_bn"], errors="ignore").sort_values("date"),
                    df_g[["date", "gdp_growth_real", "gdp_nominal_czk_bn"]].sort_values("date"),
                    on="date",
                    direction="nearest"
                )
            else:
                final_df = pd.merge(final_df.drop(columns=["gdp_growth_real", "gdp_nominal_czk_bn"], errors="ignore"),
                                    df_g[["date", "gdp_growth_real", "gdp_nominal_czk_bn"]], on="date", how="left")
            final_df["gdp_growth_real"] = final_df["gdp_growth_real"].ffill()
            final_df["gdp_nominal_czk_bn"] = final_df["gdp_nominal_czk_bn"].ffill()

        if "debt" in live_components:
            df_d = live_components["debt"]
            if frequency == "M":
                final_df = pd.merge_asof(
                    final_df.drop(columns=["public_debt_gdp_pct", "public_debt_czk_bn"], errors="ignore").sort_values("date"),
                    df_d[["date", "public_debt_gdp_pct", "public_debt_czk_bn"]].sort_values("date"),
                    on="date",
                    direction="nearest"
                )
            else:
                final_df = pd.merge(final_df.drop(columns=["public_debt_gdp_pct", "public_debt_czk_bn"], errors="ignore"),
                                    df_d[["date", "public_debt_gdp_pct", "public_debt_czk_bn"]], on="date", how="left")
            final_df["public_debt_gdp_pct"] = final_df["public_debt_gdp_pct"].ffill()
            final_df["public_debt_czk_bn"] = final_df["public_debt_czk_bn"].ffill()

        # Agregace denních kurzů do hlavní matice
        fx_cols_to_merge = [c for c in df_daily_fx.columns if c != "date"]
        df_fx_agg = df_daily_fx.set_index("date").resample(OFFSET_MONTH_END if frequency == "M" else OFFSET_QUARTER_END).last().reset_index()
        final_df = pd.merge(final_df.drop(columns=fx_cols_to_merge, errors="ignore"), df_fx_agg, on="date", how="left")
        for c in fx_cols_to_merge:
            final_df[c] = final_df[c].ffill().bfill()

        if "bond_10y" in live_components:
            df_b = live_components["bond_10y"]
            if frequency == "Q":
                df_b = df_b.set_index("date").resample(OFFSET_QUARTER_END).mean().reset_index()
            final_df = pd.merge(final_df.drop(columns=["czgb_10y"], errors="ignore"),
                                df_b[["date", "czgb_10y"]], on="date", how="left")
            final_df["czgb_10y"] = final_df["czgb_10y"].ffill()

        if "us_treasury" in live_components:
            df_u = live_components["us_treasury"]
            us_cols = [c for c in df_u.columns if c != "date"]
            df_u_agg = df_u.set_index("date").resample(OFFSET_MONTH_END if frequency == "M" else OFFSET_QUARTER_END).last().reset_index()
            final_df = pd.merge(final_df, df_u_agg, on="date", how="left", suffixes=("", "_live"))
            for col in us_cols:
                live_c = f"{col}_live"
                if live_c in final_df.columns:
                    final_df[col] = final_df[live_c].combine_first(final_df[col])
                    final_df = final_df.drop(columns=[live_c])
                final_df[col] = final_df[col].ffill().bfill()
            if "us_10y" in final_df.columns and "us_2y" in final_df.columns:
                final_df["us_spread_10y_2y"] = np.round(final_df["us_10y"] - final_df["us_2y"], 2)

        # Přepočet a kalibrace křivek CZGB a IRS
        recalc_czgb = []
        recalc_irs = []
        for _, row in final_df.iterrows():
            r_val = row.get("repo_rate", 3.75)
            y10_val = row.get("czgb_10y", 4.10)
            c_czgb, c_irs = DataLoader.compute_curve_tenors(float(r_val), float(y10_val))
            recalc_czgb.append(c_czgb)
            recalc_irs.append(c_irs)

        df_rec_czgb = pd.DataFrame(recalc_czgb)
        df_rec_irs = pd.DataFrame(recalc_irs)
        for cname in df_rec_czgb.columns:
            if cname != "czgb_10y":
                final_df[cname] = df_rec_czgb[cname]
        for cname in df_rec_irs.columns:
            final_df[cname] = df_rec_irs[cname]
        final_df["czgb_spread_10y_2y"] = np.round(final_df["czgb_10y"] - final_df["czgb_2y"], 2)

        # Kontrola integrity všech definovaných indikátorů
        for ind_key in INDICATORS.keys():
            if ind_key not in final_df.columns:
                if ind_key in base_df.columns:
                    final_df[ind_key] = base_df[ind_key]
                else:
                    final_df[ind_key] = 0.0
            final_df[ind_key] = final_df[ind_key].ffill().bfill()

        # Stavový badge
        if all_success and live_components:
            status_info["mode"] = "LIVE"
            status_info["status_badge"] = "🟢 Živá data (ČNB Denní kurzy, Sazby, Eurostat & US Treasury)"
        elif live_components:
            status_info["mode"] = "PARTIAL_LIVE"
            status_info["status_badge"] = "🟡 Kombinovaný režim (Částečná Live API + Fallback)"
        else:
            status_info["mode"] = "FALLBACK"
            status_info["status_badge"] = "🟠 Fallback Model (Historická data 2015–2026)"

        final_df = final_df.sort_values("date").reset_index(drop=True)
        numeric_cols = [c for c in final_df.columns if c not in ("date", "quarter")]
        final_df[numeric_cols] = final_df[numeric_cols].round(2)

        return final_df, status_info, df_daily_fx


# =============================================================================
# CACHOVANÉ FUNKCE PRO STREAMLIT
# =============================================================================

try:
    import streamlit as st

    @st.cache_data(ttl=3600, show_spinner="Stahuji a zpracovávám makroekonomická data ČR a USA...")
    def get_cached_macro_data(
        frequency: str = "M",
        fred_api_key: Optional[str] = None,
        force_fallback: bool = False,
        _cache_bust: str = "v2026_10_10_daily_us_cz_v3"
    ) -> Tuple[pd.DataFrame, Dict[str, Any], pd.DataFrame]:
        """Cachovaná funkce vracející (makro_df, status_info, df_denni_fx)."""
        loader = DataLoader()
        return loader.load_macro_data(
            frequency=frequency,
            fred_api_key=fred_api_key,
            force_fallback=force_fallback
        )

except ImportError:
    def get_cached_macro_data(
        frequency: str = "M",
        fred_api_key: Optional[str] = None,
        force_fallback: bool = False,
        _cache_bust: str = "v2026_10_10_daily_us_cz_v3"
    ) -> Tuple[pd.DataFrame, Dict[str, Any], pd.DataFrame]:
        loader = DataLoader()
        return loader.load_macro_data(
            frequency=frequency,
            fred_api_key=fred_api_key,
            force_fallback=force_fallback
        )
