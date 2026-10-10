"""
data_loader.py
==============
Modul pro načítání, transformaci a validaci makroekonomických dat ČR, Eurozóny/EU a USA.
Poskytuje třídu DataLoader s podporou pro:
- Veřejná REST API: Eurostat (ČR & EU CPI, Core CPI, HDP, nezaměstnanost, dluh, 10Y dluhopisy),
  ČNB (PRIBOR, klíčové sazby, denní devizové kurzy EUR, USD, PLN, GBP, JPY, CHF)
  a U.S. Department of the Treasury (denní US výnosová křivka 1M–30Y).
- Globální FX konverze a denní data pro měnové páry EUR/CZK, USD/CZK, PLN/CZK, GBP/CZK,
  EUR/USD, EUR/PLN, EUR/GBP, USD/JPY, USD/PLN a Dolarový index DXY.
- Indikátory jádrové inflace, spotřeby (maloobchodní tržby) a průmyslové výroby pro všechny regiony.
- Odolný Fallback model: realistická denní, měsíční a kvartální data pro ČR, EU i USA (2015–současnost).
- Měsíční (M) i kvartální (Q) agregaci časových řad + plnohodnotný denní dataset devizových kurzů.
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
try:
    from bs4 import BeautifulSoup
except (ImportError, ModuleNotFoundError):
    BeautifulSoup = None

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
    region: str = "CZ"  # "CZ", "EU" nebo "US"


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
        name_cz="Inflace ČR (CPI meziročně)",
        unit="%",
        category="Cenová hladina",
        description="Meziroční míra inflace vyjádřená indexem spotřebitelských cen (HICP / národní CPI).",
        region="CZ"
    ),
    "cpi_core_yoy": IndicatorInfo(
        code="cpi_core_yoy",
        name_cz="Jádrová inflace ČR (Core CPI)",
        unit="%",
        category="Cenová hladina",
        description="Meziroční jádrová inflace v ČR (čistá inflace bez regulovaných cen, potravin a pohonných hmot, sledovaná ČNB).",
        region="CZ"
    ),
    "gdp_growth_real": IndicatorInfo(
        code="gdp_growth_real",
        name_cz="Reálný růst HDP ČR (YoY)",
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
    "retail_sales_yoy": IndicatorInfo(
        code="retail_sales_yoy",
        name_cz="Maloobchodní tržby ČR (Spotřeba YoY)",
        unit="%",
        category="Ekonomická aktivita",
        description="Meziroční reálná změna tržeb v maloobchodě bez motoristického segmentu (klíčový indikátor spotřeby domácností).",
        region="CZ"
    ),
    "industrial_prod_yoy": IndicatorInfo(
        code="industrial_prod_yoy",
        name_cz="Průmyslová produkce ČR (YoY)",
        unit="%",
        category="Ekonomická aktivita",
        description="Meziroční index průmyslové produkce ČR očištěný o vliv počtu pracovních dnů (ČSÚ / Eurostat).",
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
    "pln_czk": IndicatorInfo(
        code="pln_czk",
        name_cz="Měnový kurz PLN/CZK",
        unit="CZK",
        category="Měnové kurzy",
        description="Směnný kurz polského zlotého vůči české koruně (ČNB devizový trh – denní fixace).",
        region="CZ"
    ),
    "gbp_czk": IndicatorInfo(
        code="gbp_czk",
        name_cz="Měnový kurz GBP/CZK",
        unit="CZK",
        category="Měnové kurzy",
        description="Směnný kurz britské libry vůči české koruně (ČNB devizový trh – denní fixace).",
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
    # 🇪🇺 EVROPSKÁ UNIE / EUROZÓNA (EU)
    # =========================================================================
    "ecb_deposit_rate": IndicatorInfo(
        code="ecb_deposit_rate",
        name_cz="Depozitní sazba ECB",
        unit="%",
        category="EU Měnová politika",
        description="Klíčová sazba Evropské centrální banky pro vklady bank přes noc (depozitní facilita – hlavní kotva ECB).",
        region="EU"
    ),
    "ecb_refi_rate": IndicatorInfo(
        code="ecb_refi_rate",
        name_cz="Refinanční sazba ECB (MRO)",
        unit="%",
        category="EU Měnová politika",
        description="Základní sazba pro hlavní refinanční operace ECB (týdenní dodávání likvidity).",
        region="EU"
    ),
    "ecb_lending_rate": IndicatorInfo(
        code="ecb_lending_rate",
        name_cz="Mezní zápůjční sazba ECB",
        unit="%",
        category="EU Měnová politika",
        description="Sazba pro jednodenní půjčky likvidity bankám od ECB (horní koridor sazeb).",
        region="EU"
    ),
    "euribor_3m": IndicatorInfo(
        code="euribor_3m",
        name_cz="EURIBOR 3M",
        unit="%",
        category="EU Mezibankovní trh",
        description="Klíčová referenční sazba mezibankovního trhu Eurozóny pro 3 měsíce (benchmark úvěrů v eurech).",
        region="EU"
    ),
    "estr_rate": IndicatorInfo(
        code="estr_rate",
        name_cz="€STR (Euro Short-Term Rate)",
        unit="%",
        category="EU Peněžní trh",
        description="Bezriziková jednodenní sazba eurového peněžního trhu kalkulovaná ECB (nástupce sazby EONIA).",
        region="EU"
    ),
    "eu_cpi_yoy": IndicatorInfo(
        code="eu_cpi_yoy",
        name_cz="Inflace Eurozóny (HICP)",
        unit="%",
        category="EU Cenová hladina",
        description="Meziroční míra inflace vyjádřená harmonizovaným indexem spotřebitelských cen (Eurostat HICP).",
        region="EU"
    ),
    "eu_core_cpi_yoy": IndicatorInfo(
        code="eu_core_cpi_yoy",
        name_cz="Jádrová inflace EU (Core HICP)",
        unit="%",
        category="EU Cenová hladina",
        description="Jádrová inflace Eurozóny bez energií, potravin, alkoholu a tabáku (Eurostat Core HICP).",
        region="EU"
    ),
    "eu_gdp_growth_real": IndicatorInfo(
        code="eu_gdp_growth_real",
        name_cz="Reálný růst HDP Eurozóny (YoY)",
        unit="%",
        category="EU Hrubý domácí produkt",
        description="Meziroční reálná změna hrubého domácího produktu Eurozóny / EU ve stálých cenách (Eurostat).",
        region="EU"
    ),
    "eu_gdp_nominal_eur_bn": IndicatorInfo(
        code="eu_gdp_nominal_eur_bn",
        name_cz="Nominální HDP Eurozóny",
        unit="mld. EUR",
        category="EU Hrubý domácí produkt",
        description="Kvartální objem HDP Eurozóny v běžných cenách v miliardách EUR.",
        region="EU"
    ),
    "eu_retail_sales_yoy": IndicatorInfo(
        code="eu_retail_sales_yoy",
        name_cz="Maloobchodní tržby EU (Spotřeba YoY)",
        unit="%",
        category="EU Ekonomická aktivita",
        description="Meziroční změna objemu maloobchodního prodeje v Eurozóně / EU (Eurostat Retail Trade index).",
        region="EU"
    ),
    "eu_industrial_prod_yoy": IndicatorInfo(
        code="eu_industrial_prod_yoy",
        name_cz="Průmyslová produkce EU (YoY)",
        unit="%",
        category="EU Ekonomická aktivita",
        description="Meziroční index průmyslové výroby v Eurozóně / EU (Eurostat Industrial Production).",
        region="EU"
    ),
    "eu_unemployment_rate": IndicatorInfo(
        code="eu_unemployment_rate",
        name_cz="Míra nezaměstnanosti EU",
        unit="%",
        category="EU Trh práce",
        description="Sezónně očištěná obecná míra nezaměstnanosti v EU / Eurozóně dle metodiky Eurostatu.",
        region="EU"
    ),
    "eur_pln": IndicatorInfo(
        code="eur_pln",
        name_cz="Měnový kurz EUR/PLN",
        unit="PLN",
        category="EU Měnové kurzy",
        description="Směnný kurz eura vůči polskému zlotému (denní fixace).",
        region="EU"
    ),
    "eur_gbp": IndicatorInfo(
        code="eur_gbp",
        name_cz="Měnový kurz EUR/GBP",
        unit="GBP",
        category="EU Měnové kurzy",
        description="Směnný kurz eura vůči britské libře (denní fixace).",
        region="EU"
    ),
    "eu_public_debt_gdp_pct": IndicatorInfo(
        code="eu_public_debt_gdp_pct",
        name_cz="Veřejný dluh Eurozóny k HDP",
        unit="% HDP",
        category="EU Fiskální politika",
        description="Konsolidovaný veřejný dluh států Eurozóny k HDP v % (maastrichtský průměr).",
        region="EU"
    ),
    "eu_public_debt_eur_bn": IndicatorInfo(
        code="eu_public_debt_eur_bn",
        name_cz="Veřejný dluh Eurozóny",
        unit="mld. EUR",
        category="EU Fiskální politika",
        description="Celkový konsolidovaný hrubý dluh vládních institucí Eurozóny v miliardách EUR.",
        region="EU"
    ),
    "eu_budget_deficit_eur_bn": IndicatorInfo(
        code="eu_budget_deficit_eur_bn",
        name_cz="Saldo vládního rozpočtu Eurozóny",
        unit="mld. EUR",
        category="EU Fiskální politika",
        description="Kvartální saldo hospodaření vládních institucí Eurozóny (deficit je záporný) v mld. EUR.",
        region="EU"
    ),
    "bund_10y": IndicatorInfo(
        code="bund_10y",
        name_cz="Výnos 10Y Německý Bund (Benchmark)",
        unit="%",
        category="EU Dluhopisový trh",
        description="Výnos do splatnosti 10letého německého státního dluhopisu (klíčový bezrizikový benchmark Eurozóny).",
        region="EU"
    ),
    "bund_2y": IndicatorInfo(
        code="bund_2y",
        name_cz="Výnos 2Y Německý Bund",
        unit="%",
        category="EU Dluhopisový trh",
        description="Výnos do splatnosti 2letého německého státního dluhopisu (krátký konec citlivý na ECB).",
        region="EU"
    ),
    "bund_5y": IndicatorInfo(
        code="bund_5y",
        name_cz="Výnos 5Y Německý Bund",
        unit="%",
        category="EU Dluhopisový trh",
        description="Výnos do splatnosti 5letého německého státního dluhopisu (Bobl).",
        region="EU"
    ),
    "bund_30y": IndicatorInfo(
        code="bund_30y",
        name_cz="Výnos 30Y Německý Bund",
        unit="%",
        category="EU Dluhopisový trh",
        description="Výnos do splatnosti 30letého německého státního dluhopisu (ultra-dlouhý konec křivky).",
        region="EU"
    ),
    "bund_spread_10y_2y": IndicatorInfo(
        code="bund_spread_10y_2y",
        name_cz="Sklon německé křivky (10Y − 2Y)",
        unit="p.b.",
        category="EU Dluhopisový trh",
        description="Rozpětí mezi 10Y a 2Y německým státním výnosem (indikátor inverze v Eurozóně).",
        region="EU"
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
    "us_retail_sales_yoy": IndicatorInfo(
        code="us_retail_sales_yoy",
        name_cz="Maloobchodní tržby USA (Spotřeba YoY)",
        unit="%",
        category="US Ekonomická aktivita",
        description="Meziroční změna maloobchodních tržeb v USA (U.S. Census Bureau Advance Retail Sales).",
        region="US"
    ),
    "us_industrial_prod_yoy": IndicatorInfo(
        code="us_industrial_prod_yoy",
        name_cz="Průmyslová produkce USA (YoY)",
        unit="%",
        category="US Ekonomická aktivita",
        description="Meziroční index průmyslové produkce v USA (Federal Reserve Industrial Production Index).",
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
    "usd_pln": IndicatorInfo(
        code="usd_pln",
        name_cz="Měnový kurz USD/PLN",
        unit="PLN",
        category="US Měnové kurzy",
        description="Směnný kurz amerického dolaru vůči polskému zlotému.",
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
        description="Výnos do splatnosti 10letého referenčního státního dluhopisu USA (globální benchmark).",
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
    ),

    # =========================================================================
    # 📈 AKCIOVÉ TRHY & HLAVNÍ INDEXY (ČR, EU, USA)
    # =========================================================================
    "px_index": IndicatorInfo(
        code="px_index",
        name_cz="Index PX (Pražská burza)",
        unit="bodů",
        category="Akciové trhy",
        description="Oficiální index Burzy cenných papírů Praha (BCPP / Prague Stock Exchange) zahrnující přední české blue-chip emise (ČEZ, Komerční banka, Erste, Moneta).",
        region="CZ"
    ),
    "stoxx50_index": IndicatorInfo(
        code="stoxx50_index",
        name_cz="Euro Stoxx 50",
        unit="bodů",
        category="Akciové trhy",
        description="Přední evropský akciový index 50 nejvýznamnějších korporací z 8 zemí Eurozóny (STOXX Ltd.).",
        region="EU"
    ),
    "sp500_index": IndicatorInfo(
        code="sp500_index",
        name_cz="Index S&P 500",
        unit="bodů",
        category="Akciové trhy",
        description="Standard & Poor's 500 – referenční index amerického akciového trhu reprezentující 500 největších veřejně obchodovaných společností v USA.",
        region="US"
    ),
    "nasdaq_index": IndicatorInfo(
        code="nasdaq_index",
        name_cz="NASDAQ Composite",
        unit="bodů",
        category="Akciové trhy",
        description="Vlajkový technologický index burzy NASDAQ zahrnující více než 3 000 amerických i mezinárodních společností.",
        region="US"
    )
}

# Rychlé filtry indikátorů podle regionu
CZ_INDICATORS: Dict[str, IndicatorInfo] = {k: v for k, v in INDICATORS.items() if v.region == "CZ"}
EU_INDICATORS: Dict[str, IndicatorInfo] = {k: v for k, v in INDICATORS.items() if v.region == "EU"}
US_INDICATORS: Dict[str, IndicatorInfo] = {k: v for k, v in INDICATORS.items() if v.region == "US"}
MARKET_INDICATORS: Dict[str, IndicatorInfo] = {k: v for k, v in INDICATORS.items() if v.category == "Akciové trhy"}


class DataLoader:
    """
    Robustní třída pro stahování, parsing a agregaci dat z veřejných REST API
    s automatickým fallbackem na realistický historický model pro ČR, EU i USA.
    """

    def __init__(self, request_timeout: int = 8):
        self.timeout = request_timeout
        self.headers = {
            "User-Agent": "CzechMacroDashboard/2.0 (Mozilla/5.0; Macro Terminal System)"
        }
        self.source_status: Dict[str, str] = {}
        self.last_fetch_time: Optional[datetime] = None

    # =========================================================================
    # 1. LIVE API: Eurostat (ČR & EU / Eurozóna)
    # =========================================================================

    def fetch_eurostat_cpi(self) -> pd.DataFrame:
        """Stáhne meziroční inflaci (HICP) pro ČR z Eurostatu."""
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
                records.append({"date": pd.to_datetime(t_str) + pd.offsets.MonthEnd(0), "cpi_yoy": float(val)})
        if not records:
            raise ValueError("Eurostat CPI vrátil prázdný dataset.")
        return pd.DataFrame(records).sort_values("date").drop_duplicates("date").reset_index(drop=True)

    def fetch_eurostat_ea_cpi(self) -> pd.DataFrame:
        """Stáhne celkovou (HICP) a jádrovou (Core HICP) inflaci Eurozóny z Eurostatu."""
        url_head = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/prc_hicp_manr?geo=EA20&coicop=CP00"
        url_core = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/prc_hicp_manr?geo=EA20&coicop=TOT_X_NRG_FOOD"

        rh = requests.get(url_head, headers=self.headers, timeout=self.timeout)
        rh.raise_for_status()
        dh = rh.json()
        th = list(dh.get("dimension", {}).get("time", {}).get("category", {}).get("label", {}).values())
        vh = dh.get("value", {})

        rc = requests.get(url_core, headers=self.headers, timeout=self.timeout)
        rc.raise_for_status()
        dc = rc.json()
        tc = list(dc.get("dimension", {}).get("time", {}).get("category", {}).get("label", {}).values())
        vc = dc.get("value", {})

        core_map = {tc[int(k)]: float(v) for k, v in vc.items() if int(k) < len(tc)}

        records = []
        for idx, t_str in enumerate(th):
            v_head = vh.get(str(idx))
            if v_head is not None:
                dt = pd.to_datetime(t_str) + pd.offsets.MonthEnd(0)
                records.append({
                    "date": dt,
                    "eu_cpi_yoy": float(v_head),
                    "eu_core_cpi_yoy": core_map.get(t_str)
                })

        if not records:
            raise ValueError("Eurostat EA CPI vrátil prázdný dataset.")
        return pd.DataFrame(records).sort_values("date").drop_duplicates("date").reset_index(drop=True)

    def fetch_eurostat_unemployment(self) -> pd.DataFrame:
        """Stáhne sezónně očištěnou míru nezaměstnanosti pro ČR a EU z Eurostatu."""
        url_cz = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/une_rt_m?geo=CZ&s_adj=SA&age=TOTAL&unit=PC_ACT&sex=T"
        url_eu = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/une_rt_m?geo=EU27_2020&s_adj=SA&age=TOTAL&unit=PC_ACT&sex=T"

        rcz = requests.get(url_cz, headers=self.headers, timeout=self.timeout)
        rcz.raise_for_status()
        dcz = rcz.json()
        tcz = list(dcz.get("dimension", {}).get("time", {}).get("category", {}).get("label", {}).values())
        vcz = dcz.get("value", {})

        reu = requests.get(url_eu, headers=self.headers, timeout=self.timeout)
        reu.raise_for_status()
        deu = reu.json()
        teu = list(deu.get("dimension", {}).get("time", {}).get("category", {}).get("label", {}).values())
        veu = deu.get("value", {})

        eu_map = {teu[int(k)]: float(v) for k, v in veu.items() if int(k) < len(teu)}

        records = []
        for idx, t_str in enumerate(tcz):
            val_cz = vcz.get(str(idx))
            if val_cz is not None:
                dt = pd.to_datetime(t_str) + pd.offsets.MonthEnd(0)
                records.append({
                    "date": dt,
                    "unemployment_rate": float(val_cz),
                    "eu_unemployment_rate": eu_map.get(t_str)
                })
        return pd.DataFrame(records).sort_values("date").drop_duplicates("date").reset_index(drop=True)

    def fetch_eurostat_gdp(self) -> pd.DataFrame:
        """Stáhne reálný růst HDP (YoY) pro ČR a Eurozónu z Eurostatu."""
        url_cz = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/namq_10_gdp?geo=CZ&unit=CLV_PCH_SM&s_adj=SCA&na_item=B1GQ"
        url_ea = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/namq_10_gdp?geo=EA20&unit=CLV_PCH_SM&s_adj=SCA&na_item=B1GQ"

        rcz = requests.get(url_cz, headers=self.headers, timeout=self.timeout)
        rcz.raise_for_status()
        dcz = rcz.json()
        tcz = list(dcz.get("dimension", {}).get("time", {}).get("category", {}).get("label", {}).values())
        vcz = dcz.get("value", {})

        rea = requests.get(url_ea, headers=self.headers, timeout=self.timeout)
        rea.raise_for_status()
        dea = rea.json()
        tea = list(dea.get("dimension", {}).get("time", {}).get("category", {}).get("label", {}).values())
        vea = dea.get("value", {})

        ea_map = {tea[int(k)]: float(v) for k, v in vea.items() if int(k) < len(tea)}

        records = []
        for idx, t_str in enumerate(tcz):
            val_cz = vcz.get(str(idx))
            if val_cz is not None:
                year_part, q_part = t_str.split("-Q")
                quarter_end_month = int(q_part) * 3
                dt = pd.to_datetime(f"{year_part}-{quarter_end_month:02d}-01") + pd.offsets.MonthEnd(0)
                records.append({
                    "date": dt,
                    "quarter": t_str,
                    "gdp_growth_real": float(val_cz),
                    "eu_gdp_growth_real": ea_map.get(t_str)
                })
        return pd.DataFrame(records).sort_values("date").drop_duplicates("date").reset_index(drop=True)

    def fetch_eurostat_debt(self) -> pd.DataFrame:
        """Stáhne konsolidovaný dluh vládních institucí pro ČR a Eurozónu z Eurostatu."""
        url_cz = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/gov_10q_ggdebt?geo=CZ&unit=PC_GDP&sector=S13&na_item=GD"
        url_ea = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/gov_10q_ggdebt?geo=EA20&unit=PC_GDP&sector=S13&na_item=GD"

        rcz = requests.get(url_cz, headers=self.headers, timeout=self.timeout)
        rcz.raise_for_status()
        dcz = rcz.json()
        tcz = list(dcz.get("dimension", {}).get("time", {}).get("category", {}).get("label", {}).values())
        vcz = dcz.get("value", {})

        rea = requests.get(url_ea, headers=self.headers, timeout=self.timeout)
        rea.raise_for_status()
        dea = rea.json()
        tea = list(dea.get("dimension", {}).get("time", {}).get("category", {}).get("label", {}).values())
        vea = dea.get("value", {})

        ea_map = {tea[int(k)]: float(v) for k, v in vea.items() if int(k) < len(tea)}

        records = []
        for idx_str, val in vcz.items():
            if int(idx_str) < len(tcz):
                q_label = tcz[int(idx_str)]
                year_part, q_part = q_label.split("-Q")
                quarter_end_month = int(q_part) * 3
                dt = pd.to_datetime(f"{year_part}-{quarter_end_month:02d}-01") + pd.offsets.MonthEnd(0)
                records.append({
                    "date": dt,
                    "quarter": q_label,
                    "public_debt_gdp_pct": float(val),
                    "eu_public_debt_gdp_pct": ea_map.get(q_label)
                })
        return pd.DataFrame(records).sort_values("date").drop_duplicates("date").reset_index(drop=True)

    def fetch_eurostat_10y_bond(self) -> pd.DataFrame:
        """Stáhne výnosy 10letých státních dluhopisů ČR a Německa (Bund) z Eurostatu."""
        url_cz = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/irt_lt_mcby_m?geo=CZ"
        url_de = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/irt_lt_mcby_m?geo=DE"

        rcz = requests.get(url_cz, headers=self.headers, timeout=self.timeout)
        rcz.raise_for_status()
        dcz = rcz.json()
        tcz = list(dcz.get("dimension", {}).get("time", {}).get("category", {}).get("label", {}).values())
        vcz = dcz.get("value", {})

        rde = requests.get(url_de, headers=self.headers, timeout=self.timeout)
        rde.raise_for_status()
        dde = rde.json()
        tde = list(dde.get("dimension", {}).get("time", {}).get("category", {}).get("label", {}).values())
        vde = dde.get("value", {})

        de_map = {tde[int(k)]: float(v) for k, v in vde.items() if int(k) < len(tde)}

        records = []
        for idx, t_str in enumerate(tcz):
            val_cz = vcz.get(str(idx))
            if val_cz is not None:
                records.append({
                    "date": pd.to_datetime(t_str) + pd.offsets.MonthEnd(0),
                    "czgb_10y": float(val_cz),
                    "bund_10y": de_map.get(t_str)
                })
        return pd.DataFrame(records).sort_values("date").drop_duplicates("date").reset_index(drop=True)

    @staticmethod
    def compute_curve_tenors(repo_val: float, y10_val: float) -> Tuple[Dict[str, float], Dict[str, float]]:
        """Vygeneruje tenorskou strukturu výnosové křivky CZGB a IRS pro splatnosti 1Y až 15Y."""
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
    # 2. LIVE API: ČNB (PRIBOR, Sazby, DENNÍ DEVÍZOVÉ KURZY včetně PLN a GBP)
    # =========================================================================

    def fetch_cnb_pribor(self, start_year: int = 2015, end_year: int = 2026) -> pd.DataFrame:
        """Stáhne denní hodnoty PRIBOR (1M, 3M, 6M) z REST API ČNB."""
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
                logger.warning("Chyba při stahování PRIBOR pro rok %d: %s", yr, e)

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
        """Stáhne kompletní historii sazeb ČNB a vytvoří souvislou denní časovou řadu."""
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

            if BeautifulSoup is None:
                raise ImportError("Knihovna beautifulsoup4 není nainstalována.")

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
                        items.append({"date": dt, col: float(cols[1].replace(",", ".").replace("%", "").strip())})
                    except Exception:
                        continue
            series_dict[col] = pd.DataFrame(items).sort_values("date").drop_duplicates("date")

        today = pd.to_datetime(datetime.now().strftime("%Y-%m-%d"))
        df_daily = pd.DataFrame({"date": pd.date_range("2015-01-01", today, freq="D")})

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
        Stáhne kompletní historii denních devizových kurzů z REST API ČNB (daily-year)
        včetně PLN a GBP a vypočítá všechny přímé a křížové měnové páry pro ČR, EU a USA.
        """
        records = []
        for yr in range(start_year, end_year + 1):
            url = f"https://api.cnb.cz/cnbapi/exrates/daily-year?year={yr}"
            try:
                resp = requests.get(url, headers=self.headers, timeout=self.timeout)
                if resp.status_code == 200:
                    for it in resp.json().get("rates", []):
                        cc = it.get("currencyCode")
                        if cc in ("EUR", "USD", "PLN", "GBP", "JPY", "CHF"):
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

        for c in ["EUR", "USD", "PLN", "GBP", "JPY", "CHF"]:
            if c in pivot.columns:
                pivot[c] = pivot[c].ffill().bfill()

        df_out = pd.DataFrame()
        df_out["date"] = pivot["date"]

        # CZ Páry
        if "EUR" in pivot.columns:
            df_out["eur_czk"] = np.round(pivot["EUR"], 4)
        if "USD" in pivot.columns:
            df_out["usd_czk"] = np.round(pivot["USD"], 4)
        if "PLN" in pivot.columns:
            df_out["pln_czk"] = np.round(pivot["PLN"], 4)
        if "GBP" in pivot.columns:
            df_out["gbp_czk"] = np.round(pivot["GBP"], 4)
        if "CHF" in pivot.columns:
            df_out["chf_czk"] = np.round(pivot["CHF"], 4)

        # EU Páry
        if "EUR" in pivot.columns and "USD" in pivot.columns:
            df_out["eur_usd"] = np.round(pivot["EUR"] / pivot["USD"], 4)
        if "EUR" in pivot.columns and "PLN" in pivot.columns:
            df_out["eur_pln"] = np.round(pivot["EUR"] / pivot["PLN"], 4)
        if "EUR" in pivot.columns and "GBP" in pivot.columns:
            df_out["eur_gbp"] = np.round(pivot["EUR"] / pivot["GBP"], 4)

        # US Páry
        if "GBP" in pivot.columns and "USD" in pivot.columns:
            df_out["gbp_usd"] = np.round(pivot["GBP"] / pivot["USD"], 4)
        if "USD" in pivot.columns and "JPY" in pivot.columns:
            df_out["usd_jpy"] = np.round(pivot["USD"] / pivot["JPY"], 3)
        if "USD" in pivot.columns and "PLN" in pivot.columns:
            df_out["usd_pln"] = np.round(pivot["USD"] / pivot["PLN"], 4)
        if "USD" in pivot.columns and "CHF" in pivot.columns:
            df_out["usd_chf"] = np.round(pivot["USD"] / pivot["CHF"], 4)

        # ICE U.S. Dollar Index (DXY)
        if "eur_usd" in df_out.columns and "usd_jpy" in df_out.columns and "gbp_usd" in df_out.columns:
            dxy = 50.14348112 * (df_out["eur_usd"] ** -0.576) * (df_out["usd_jpy"] ** 0.136) * (df_out["gbp_usd"] ** -0.119)
            if "usd_chf" in df_out.columns:
                dxy = dxy * (df_out["usd_chf"] ** 0.036)
            df_out["dxy_index"] = np.round(dxy, 2)

        return df_out.sort_values("date").drop_duplicates("date").reset_index(drop=True)

    # =========================================================================
    # 3. LIVE API: U.S. DEPARTMENT OF THE TREASURY (Výnosová křivka US 1M–30Y)
    # =========================================================================

    def fetch_us_treasury_yields(self, start_year: int = 2024, end_year: int = 2026) -> pd.DataFrame:
        """Stáhne denní výnosy amerických státních dluhopisů z XML API U.S. Treasury."""
        import xml.etree.ElementTree as ET

        ns = {
            "atom": "http://www.w3.org/2005/Atom",
            "d": "http://schemas.microsoft.com/ado/2007/08/dataservices",
            "m": "http://schemas.microsoft.com/ado/2007/08/dataservices/metadata"
        }
        cols = {
            "BC_1MONTH": "us_1m", "BC_3MONTH": "us_3m", "BC_6MONTH": "us_6m",
            "BC_1YEAR": "us_1y", "BC_2YEAR": "us_2y", "BC_3YEAR": "us_3y",
            "BC_5YEAR": "us_5y", "BC_7YEAR": "us_7y", "BC_10YEAR": "us_10y",
            "BC_20YEAR": "us_20y", "BC_30YEAR": "us_30y"
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
                        row = {"date": pd.to_datetime(d_elem.text.split("T")[0])}
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
                logger.warning("Chyba při stahování US Treasury pro rok %d: %s", yr, e)

        if not records:
            raise ValueError("US Treasury API nevrátilo žádné záznamy.")
        return pd.DataFrame(records).sort_values("date").drop_duplicates("date").reset_index(drop=True)

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
                    records.append({"date": pd.to_datetime(obs["date"]), "value": float(val_str)})
                except (ValueError, TypeError):
                    continue
        return pd.DataFrame(records)

    # =========================================================================
    # 5. LIVE API: YAHOO FINANCE (Akciové indexy S&P 500, NASDAQ, Euro Stoxx 50)
    # =========================================================================

    def fetch_stock_indices(self) -> pd.DataFrame:
        """Stáhne historické kurzy hlavních světových akciových indexů z Yahoo Finance."""
        tickers = {
            "sp500_index": "%5EGSPC",
            "nasdaq_index": "%5EIXIC",
            "stoxx50_index": "%5ESTOXX50E"
        }
        dfs = []
        for col_name, sym in tickers.items():
            try:
                url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range=12y&interval=1mo"
                r = requests.get(url, headers=self.headers, timeout=self.timeout)
                if r.status_code == 200:
                    res = r.json().get("chart", {}).get("result")
                    if res and "timestamp" in res[0]:
                        ts = pd.to_datetime(res[0]["timestamp"], unit="s").tz_localize(None).floor("D")
                        quotes = res[0]["indicators"]["quote"][0].get("close", [])
                        if quotes and len(quotes) == len(ts):
                            sdf = pd.DataFrame({"date": ts, col_name: quotes}).dropna().drop_duplicates("date")
                            dfs.append(sdf)
            except Exception as e:
                logger.warning("Chyba při stahování indexu %s (%s): %s", col_name, sym, e)

        if not dfs:
            raise ValueError("Nepodařilo se stáhnout žádné akciové indexy z Yahoo Finance.")

        res_df = dfs[0]
        for d in dfs[1:]:
            res_df = pd.merge(res_df, d, on="date", how="outer")
        return res_df.sort_values("date").reset_index(drop=True)

    # =========================================================================
    # 6. HISTORICKÝ FALLBACK MODEL (2015–2026: ČR, EU a USA)
    # =========================================================================

    def generate_fallback_daily_fx(self) -> pd.DataFrame:
        """Vygeneruje souvislý denní dataset devizových kurzů 2015–2026 včetně PLN a GBP."""
        dates_d = pd.date_range("2015-01-01", "2026-10-10", freq="B")
        np.random.seed(101)
        n = len(dates_d)

        eur_base = 27.02 + np.cumsum(np.random.normal(-0.0007, 0.04, n))
        eur_base = np.clip(eur_base, 23.40, 27.50)

        usd_base = 24.50 + np.cumsum(np.random.normal(-0.0008, 0.05, n))
        usd_base = np.clip(usd_base, 20.80, 25.80)

        # PLN a GBP vůči CZK
        pln_base = 5.85 + np.cumsum(np.random.normal(0.0001, 0.015, n))
        pln_base = np.clip(pln_base, 5.20, 6.20)

        gbp_base = 32.50 + np.cumsum(np.random.normal(-0.0009, 0.06, n))
        gbp_base = np.clip(gbp_base, 27.50, 38.00)

        chf_base = eur_base * 0.95 + np.random.normal(0, 0.04, n)

        eur_usd = eur_base / usd_base
        eur_pln = eur_base / pln_base
        eur_gbp = eur_base / gbp_base
        gbp_usd = gbp_base / usd_base
        usd_pln = usd_base / pln_base
        usd_jpy = 110.0 + np.cumsum(np.random.normal(0.012, 0.35, n))
        usd_jpy = np.clip(usd_jpy, 102.0, 161.0)
        usd_chf = usd_base / chf_base

        dxy = 50.14348112 * (eur_usd ** -0.576) * (usd_jpy ** 0.136) * (gbp_usd ** -0.119) * (usd_chf ** 0.036)

        return pd.DataFrame({
            "date": dates_d,
            "eur_czk": np.round(eur_base, 4),
            "usd_czk": np.round(usd_base, 4),
            "pln_czk": np.round(pln_base, 4),
            "gbp_czk": np.round(gbp_base, 4),
            "chf_czk": np.round(chf_base, 4),
            "eur_usd": np.round(eur_usd, 4),
            "eur_pln": np.round(eur_pln, 4),
            "eur_gbp": np.round(eur_gbp, 4),
            "gbp_usd": np.round(gbp_usd, 4),
            "usd_pln": np.round(usd_pln, 4),
            "usd_jpy": np.round(usd_jpy, 3),
            "usd_chf": np.round(usd_chf, 4),
            "dxy_index": np.round(dxy, 2)
        })

    def generate_fallback_dataset(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Generuje realistická historická data pro ČR, EU i USA za období 2015–2026.
        Vrací trojici (df_monthly, df_quarterly, df_daily_fx).
        """
        dates_m = pd.date_range("2015-01-01", "2026-10-01", freq=OFFSET_MONTH_END)
        n_m = len(dates_m)

        # ---------------------------------------------------------------------
        # A. ČR: Sazby ČNB, PRIBOR, Inflace CPI, Jádrová inflace, Spotřeba a Průmysl
        # ---------------------------------------------------------------------
        repo_series = []
        cpi_series = []
        cpi_core_series = []
        une_series = []
        ret_cz_series = []
        ind_cz_series = []

        for d in dates_m:
            yr, mo = d.year, d.month

            # 2T Repo ČNB
            if yr < 2017 or (yr == 2017 and mo < 8):
                rate = 0.05
            elif yr == 2017:
                rate = 0.25 if mo < 11 else 0.50
            elif yr == 2018:
                rates_18 = [0.50, 0.75, 0.75, 0.75, 0.75, 1.00, 1.00, 1.25, 1.50, 1.50, 1.75, 1.75]
                rate = rates_18[mo - 1]
            elif yr == 2019:
                rate = 1.75 if mo < 5 else 2.00
            elif yr == 2020:
                rate = 2.00 if mo < 2 else (2.25 if mo == 2 else (1.75 if mo == 3 else (1.00 if mo == 4 else 0.25)))
            elif yr == 2021:
                rate = 0.25 if mo < 6 else (0.50 if mo < 8 else (0.75 if mo < 9 else (1.50 if mo < 11 else 2.75)))
            elif yr == 2022:
                rate = 3.75 if mo < 2 else (4.50 if mo < 3 else (5.00 if mo < 5 else (5.75 if mo < 6 else 7.00)))
            elif yr == 2023:
                rate = 7.00 if mo < 12 else 6.75
            elif yr == 2024:
                rates_24 = [6.25, 5.75, 5.75, 5.25, 4.75, 4.75, 4.50, 4.50, 4.25, 4.00, 4.00, 4.00]
                rate = rates_24[mo - 1]
            elif yr == 2025:
                rate = 3.75 if mo < 6 else 3.50
            else:
                rate = 3.50
            repo_series.append(rate)

            # Inflace CPI & Jádrová inflace ČR
            if yr == 2015:
                cpi, core = 0.3, 1.1
            elif yr == 2016:
                cpi, core = 0.7, 1.3
            elif yr == 2017:
                cpi, core = 2.4, 2.3
            elif yr == 2018:
                cpi, core = 2.1, 2.2
            elif yr == 2019:
                cpi, core = 2.8, 2.7
            elif yr == 2020:
                cpi, core = 3.2, 3.4
            elif yr == 2021:
                cpi, core = 3.8 + (mo / 12) * 2.8, 3.2 + (mo / 12) * 4.6
            elif yr == 2022:
                cpi_traj = [9.9, 11.1, 12.7, 14.2, 16.0, 17.2, 17.5, 17.2, 18.0, 15.1, 16.2, 15.8]
                core_traj = [7.2, 8.5, 10.2, 11.8, 13.5, 14.5, 14.7, 14.5, 14.7, 13.8, 13.5, 13.2]
                cpi, core = cpi_traj[mo - 1], core_traj[mo - 1]
            elif yr == 2023:
                cpi_traj = [17.5, 16.7, 15.0, 12.7, 11.1, 9.7, 8.8, 8.5, 6.9, 8.5, 7.3, 6.9]
                core_traj = [12.3, 11.8, 10.5, 9.2, 8.6, 7.5, 6.8, 6.0, 5.0, 4.2, 3.9, 3.6]
                cpi, core = cpi_traj[mo - 1], core_traj[mo - 1]
            elif yr == 2024:
                cpi_traj = [2.3, 2.0, 2.0, 2.9, 2.6, 2.0, 2.2, 2.2, 2.6, 2.8, 2.8, 2.7]
                core_traj = [2.9, 2.8, 2.7, 2.6, 2.5, 2.2, 2.3, 2.3, 2.3, 2.4, 2.4, 2.4]
                cpi, core = cpi_traj[mo - 1], core_traj[mo - 1]
            elif yr == 2025:
                cpi, core = 2.4, 2.3
            else:
                cpi, core = 2.2, 2.2
            cpi_series.append(round(cpi, 1))
            cpi_core_series.append(round(core, 1))

            # Nezaměstnanost ČR
            une = 2.8 if yr >= 2024 else (2.4 if yr >= 2018 else 4.0)
            une_series.append(round(une, 1))

            # Spotřeba (Maloobchod) & Průmysl ČR
            if yr in (2015, 2016, 2017, 2018, 2019):
                ret_cz = 5.2 + 0.8 * np.sin(mo)
                ind_cz = 4.1 + 1.2 * np.cos(mo)
            elif yr == 2020:
                ret_cz = -10.5 if mo == 4 else 0.5
                ind_cz = -33.5 if mo == 4 else -1.2
            elif yr == 2021:
                ret_cz, ind_cz = 4.5, 8.5
            elif yr == 2022:
                ret_cz, ind_cz = -5.8, 1.2
            elif yr == 2023:
                ret_cz, ind_cz = -2.1, -2.8
            elif yr == 2024:
                ret_cz, ind_cz = 4.2, 0.5
            else:
                ret_cz, ind_cz = 3.2, 2.2
            ret_cz_series.append(round(ret_cz, 1))
            ind_cz_series.append(round(ind_cz, 1))

        repo_arr = np.array(repo_series)
        discount_arr = np.maximum(0.05, repo_arr - 1.0)
        lombard_arr = repo_arr + 1.0

        pribor_1m = np.maximum(0.08, repo_arr + 0.06)
        pribor_3m = np.maximum(0.12, repo_arr + 0.12)
        pribor_6m = np.maximum(0.18, repo_arr + 0.22)

        # Dluhopisy CZGB & IRS
        y10_series = [4.10 if yr >= 2024 else (4.60 if yr == 2023 else (4.50 if yr == 2022 else 1.80)) for yr in [d.year for d in dates_m]]
        curve_records_czgb = []
        curve_records_irs = []
        for r_val, y10_val in zip(repo_arr, y10_series):
            c_czgb, c_irs = DataLoader.compute_curve_tenors(float(r_val), float(y10_val))
            curve_records_czgb.append(c_czgb)
            curve_records_irs.append(c_irs)
        df_czgb_m = pd.DataFrame(curve_records_czgb)
        df_irs_m = pd.DataFrame(curve_records_irs)

        # ---------------------------------------------------------------------
        # B. EU / EUROZÓNA: Sazby ECB, HICP, Jádrová inflace, Bunds, Spotřeba & Průmysl
        # ---------------------------------------------------------------------
        ecb_depo_series = []
        eu_cpi_series = []
        eu_core_cpi_series = []
        eu_une_series = []
        eu_ret_series = []
        eu_ind_series = []
        bund_10_series = []
        bund_2_series = []

        for d in dates_m:
            yr, mo = d.year, d.month

            # ECB Depozitní sazba
            if yr < 2019 or (yr == 2019 and mo < 9):
                depo = -0.40
            elif yr < 2022 or (yr == 2022 and mo < 7):
                depo = -0.50
            elif yr == 2022:
                depo_traj = [-0.50, -0.50, -0.50, -0.50, -0.50, -0.50, 0.00, 0.00, 0.75, 0.75, 1.50, 2.00]
                depo = depo_traj[mo - 1]
            elif yr == 2023:
                depo_traj = [2.00, 2.50, 3.00, 3.00, 3.25, 3.50, 3.50, 3.75, 4.00, 4.00, 4.00, 4.00]
                depo = depo_traj[mo - 1]
            elif yr == 2024:
                depo_traj = [4.00, 4.00, 4.00, 4.00, 4.00, 3.75, 3.75, 3.75, 3.50, 3.25, 3.00, 3.00]
                depo = depo_traj[mo - 1]
            elif yr == 2025:
                depo = 2.75 if mo < 6 else 2.50
            else:
                depo = 2.25
            ecb_depo_series.append(depo)

            # Inflace HICP & Core HICP Eurozóny
            if yr <= 2020:
                eh, ec = 1.2, 1.0
            elif yr == 2021:
                eh, ec = 2.6, 1.8
            elif yr == 2022:
                eh_traj = [5.1, 5.9, 7.4, 7.4, 8.1, 8.6, 8.9, 9.1, 9.9, 10.6, 10.1, 9.2]
                ec_traj = [2.3, 2.7, 2.9, 3.5, 3.8, 3.7, 4.0, 4.3, 4.8, 5.0, 5.0, 5.2]
                eh, ec = eh_traj[mo - 1], ec_traj[mo - 1]
            elif yr == 2023:
                eh_traj = [8.6, 8.5, 6.9, 7.0, 6.1, 5.5, 5.3, 5.2, 4.3, 2.9, 2.4, 2.9]
                ec_traj = [5.3, 5.6, 5.7, 5.6, 5.3, 5.5, 5.5, 5.3, 4.5, 4.2, 3.6, 3.4]
                eh, ec = eh_traj[mo - 1], ec_traj[mo - 1]
            elif yr == 2024:
                eh_traj = [2.8, 2.6, 2.4, 2.4, 2.6, 2.5, 2.6, 2.2, 1.7, 2.0, 2.2, 2.3]
                ec_traj = [3.3, 3.1, 2.9, 2.7, 2.9, 2.9, 2.9, 2.8, 2.7, 2.7, 2.7, 2.7]
                eh, ec = eh_traj[mo - 1], ec_traj[mo - 1]
            else:
                eh, ec = 2.1, 2.1
            eu_cpi_series.append(round(eh, 1))
            eu_core_cpi_series.append(round(ec, 1))

            # Nezaměstnanost EU
            eu_une = 6.4 if yr >= 2024 else (6.6 if yr == 2023 else (7.2 if yr <= 2021 else 6.8))
            eu_une_series.append(round(eu_une, 1))

            # Spotřeba & Průmysl EU
            if yr == 2020:
                ret_eu, ind_eu = -17.0 if mo == 4 else 1.0, -25.0 if mo == 4 else -1.5
            elif yr == 2022:
                ret_eu, ind_eu = -2.5, 1.8
            elif yr == 2023:
                ret_eu, ind_eu = -1.2, -3.0
            elif yr == 2024:
                ret_eu, ind_eu = 1.8, -1.2
            else:
                ret_eu, ind_eu = 2.0, 1.5
            eu_ret_series.append(round(ret_eu, 1))
            eu_ind_series.append(round(ind_eu, 1))

            # Německý Bund 10Y a 2Y
            if yr <= 2021:
                b10, b2 = -0.35, -0.65
            elif yr == 2022:
                b10, b2 = 1.80, 1.60
            elif yr == 2023:
                b10, b2 = 2.60, 3.00
            elif yr == 2024:
                b10, b2 = 2.35, 2.20
            else:
                b10, b2 = 2.20, 2.05
            bund_10_series.append(round(b10, 2))
            bund_2_series.append(round(b2, 2))

        depo_arr = np.array(ecb_depo_series)
        mro_arr = depo_arr + 0.25
        lend_arr = mro_arr + 0.25
        euribor_arr = np.maximum(-0.55, depo_arr + 0.15)
        estr_arr = depo_arr - 0.08

        # ---------------------------------------------------------------------
        # C. USA: Fed Sazby, CPI, Core CPI, Treasury, Spotřeba & Průmysl
        # ---------------------------------------------------------------------
        fed_upper_series = []
        us_cpi_series = []
        us_core_cpi_series = []
        us_une_series = []
        us_nfp_series = []
        us_ret_series = []
        us_ind_series = []
        us_10y_series = []
        us_2y_series = []
        us_3m_series = []

        for d in dates_m:
            yr, mo = d.year, d.month

            if yr == 2015:
                fu = 0.25 if mo < 12 else 0.50
                ucpi, ucore = 0.4, 1.8
                u_une, unfp = 5.3, 220
                y10, y2, y3m = 2.15, 0.65, 0.05
                uret, uind = 4.5, 2.0
            elif yr == 2016:
                fu = 0.50 if mo < 12 else 0.75
                ucpi, ucore = 1.3, 2.2
                u_une, unfp = 4.9, 200
                y10, y2, y3m = 1.85, 0.85, 0.30
                uret, uind = 4.2, 1.5
            elif yr == 2017:
                fu = 1.00 if mo < 6 else (1.25 if mo < 12 else 1.50)
                ucpi, ucore = 2.1, 1.8
                u_une, unfp = 4.4, 180
                y10, y2, y3m = 2.35, 1.40, 0.95
                uret, uind = 4.8, 2.2
            elif yr == 2018:
                fu = 1.75 if mo < 6 else (2.00 if mo < 9 else (2.25 if mo < 12 else 2.50))
                ucpi, ucore = 2.4, 2.2
                u_une, unfp = 3.9, 190
                y10, y2, y3m = 2.90, 2.50, 2.00
                uret, uind = 4.5, 3.5
            elif yr == 2019:
                fu = 2.50 if mo < 8 else (2.25 if mo < 9 else (2.00 if mo < 11 else 1.75))
                ucpi, ucore = 1.8, 2.3
                u_une, unfp = 3.7, 175
                y10, y2, y3m = 2.15, 1.95, 2.10
                uret, uind = 3.6, 0.8
            elif yr == 2020:
                fu = 1.75 if mo < 3 else 0.25
                ucpi, ucore = 1.2, 1.6
                u_une = 3.6 if mo < 3 else (14.7 if mo == 4 else (10.2 if mo < 8 else 6.7))
                unfp = -20500 if mo == 4 else (4800 if mo == 6 else 150)
                y10, y2, y3m = 0.90, 0.25, 0.15
                uret, uind = -15.0 if mo == 4 else 2.5, -16.0 if mo == 4 else -2.5
            elif yr == 2021:
                fu = 0.25
                ucpi, ucore = 2.6 + (mo / 12) * 4.4, 1.6 + (mo / 12) * 3.8
                u_une, unfp = 6.3 - (mo / 12) * 2.4, 450
                y10, y2, y3m = 1.45, 0.45, 0.05
                uret, uind = 18.5, 5.5
            elif yr == 2022:
                fed_traj = [0.25, 0.25, 0.50, 0.50, 1.00, 1.75, 2.50, 2.50, 3.25, 3.25, 4.00, 4.50]
                cpi_traj = [7.5, 7.9, 8.5, 8.3, 8.6, 9.1, 8.5, 8.3, 8.2, 7.7, 7.1, 6.5]
                core_traj = [6.0, 6.4, 6.5, 6.2, 6.0, 5.9, 5.9, 6.3, 6.6, 6.3, 6.0, 5.7]
                fu, ucpi, ucore = fed_traj[mo - 1], cpi_traj[mo - 1], core_traj[mo - 1]
                u_une, unfp = 3.6, 380
                traj_10 = [1.8, 2.0, 2.3, 2.8, 2.9, 3.1, 2.9, 3.0, 3.6, 4.0, 3.9, 3.8]
                traj_2 = [1.0, 1.4, 2.3, 2.6, 2.6, 2.9, 2.9, 3.4, 4.1, 4.4, 4.4, 4.3]
                traj_3m = [0.2, 0.4, 0.5, 0.8, 1.1, 1.6, 2.4, 2.9, 3.3, 4.1, 4.3, 4.4]
                y10, y2, y3m = traj_10[mo - 1], traj_2[mo - 1], traj_3m[mo - 1]
                uret, uind = 8.5, 3.5
            elif yr == 2023:
                fed_traj = [4.50, 4.75, 5.00, 5.00, 5.25, 5.25, 5.50, 5.50, 5.50, 5.50, 5.50, 5.50]
                cpi_traj = [6.4, 6.0, 5.0, 4.9, 4.0, 3.0, 3.2, 3.7, 3.7, 3.2, 3.1, 3.4]
                core_traj = [5.6, 5.5, 5.6, 5.5, 5.3, 4.8, 4.7, 4.3, 4.1, 4.0, 4.0, 3.9]
                fu, ucpi, ucore = fed_traj[mo - 1], cpi_traj[mo - 1], core_traj[mo - 1]
                u_une, unfp = 3.6, 250
                traj_10 = [3.5, 3.8, 3.6, 3.5, 3.6, 3.8, 4.0, 4.2, 4.4, 4.8, 4.5, 4.0]
                traj_2 = [4.2, 4.7, 4.1, 4.0, 4.3, 4.8, 4.8, 4.9, 5.0, 5.0, 4.7, 4.3]
                traj_3m = [4.6, 4.8, 4.9, 5.1, 5.3, 5.4, 5.4, 5.4, 5.5, 5.5, 5.4, 5.3]
                y10, y2, y3m = traj_10[mo - 1], traj_2[mo - 1], traj_3m[mo - 1]
                uret, uind = 3.2, 0.2
            elif yr == 2024:
                fed_traj = [5.50, 5.50, 5.50, 5.50, 5.50, 5.50, 5.50, 5.50, 5.00, 5.00, 4.75, 4.50]
                cpi_traj = [3.1, 3.2, 3.5, 3.4, 3.3, 3.0, 2.9, 2.5, 2.4, 2.6, 2.7, 2.7]
                core_traj = [3.9, 3.8, 3.8, 3.6, 3.4, 3.3, 3.2, 3.2, 3.3, 3.3, 3.3, 3.2]
                fu, ucpi, ucore = fed_traj[mo - 1], cpi_traj[mo - 1], core_traj[mo - 1]
                u_une, unfp = 4.1, 180
                traj_10 = [4.1, 4.2, 4.2, 4.6, 4.5, 4.3, 4.2, 3.9, 3.8, 4.2, 4.3, 4.5]
                traj_2 = [4.3, 4.6, 4.6, 4.9, 4.8, 4.7, 4.4, 3.9, 3.6, 4.1, 4.2, 4.3]
                traj_3m = [5.3, 5.4, 5.4, 5.4, 5.4, 5.3, 5.2, 5.1, 4.9, 4.6, 4.5, 4.4]
                y10, y2, y3m = traj_10[mo - 1], traj_2[mo - 1], traj_3m[mo - 1]
                uret, uind = 3.0, 1.2
            else:
                fu = 4.25
                ucpi, ucore = 2.4, 2.7
                u_une, unfp = 4.1, 160
                y10, y2, y3m = 4.40, 4.20, 4.10
                uret, uind = 2.8, 1.5

            fed_upper_series.append(fu)
            us_cpi_series.append(round(ucpi, 1))
            us_core_cpi_series.append(round(ucore, 1))
            us_une_series.append(round(u_une, 1))
            us_nfp_series.append(unfp)
            us_ret_series.append(round(uret, 1))
            us_ind_series.append(round(uind, 1))
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
            us_curve_records.append({
                "us_1m": round(max(0.02, y3m - 0.05), 2),
                "us_3m": round(y3m, 2),
                "us_6m": round(max(0.05, y3m + 0.08), 2),
                "us_1y": round(max(0.08, y2 - 0.15 if diff >= 0 else y2 + 0.10), 2),
                "us_2y": round(y2, 2),
                "us_3y": round(y2 + 0.3 * diff, 2),
                "us_5y": round(y2 + 0.6 * diff, 2),
                "us_7y": round(y2 + 0.85 * diff, 2),
                "us_10y": round(y10, 2),
                "us_20y": round(y10 + (0.35 if diff >= 0 else 0.15), 2),
                "us_30y": round(y10 + (0.28 if diff >= 0 else 0.10), 2),
                "us_spread_10y_2y": round(y10 - y2, 2),
            })
        df_us_curve_m = pd.DataFrame(us_curve_records)

        # ---------------------------------------------------------------------
        # D. AKCIOVÉ INDEXY (S&P 500, NASDAQ, Euro Stoxx 50, Index PX 2015–2026)
        # ---------------------------------------------------------------------
        px_series = []
        stoxx50_series = []
        sp500_series = []
        nasdaq_series = []

        for d in dates_m:
            yr, mo = d.year, d.month

            # S&P 500
            if yr == 2015: sp = 2050 + (mo - 6) * 15
            elif yr == 2016: sp = 2000 + (mo / 12) * 240
            elif yr == 2017: sp = 2270 + (mo / 12) * 400
            elif yr == 2018: sp = 2750 - (250 if mo >= 10 else 0)
            elif yr == 2019: sp = 2600 + (mo / 12) * 630
            elif yr == 2020: sp = 3250 if mo < 3 else (2580 if mo == 3 else 2900 + (mo - 4) * 110)
            elif yr == 2021: sp = 3800 + (mo / 12) * 960
            elif yr == 2022: sp = 4500 - (mo / 12) * 700
            elif yr == 2023: sp = 3900 + (mo / 12) * 870
            elif yr == 2024: sp = 4850 + (mo / 12) * 1050
            elif yr == 2025: sp = 5900 + (mo / 12) * 250
            else: sp = 6150 + (mo / 12) * 100
            sp500_series.append(round(sp, 1))

            # NASDAQ Composite
            if yr == 2015: nq = 4750 + (mo - 6) * 40
            elif yr == 2016: nq = 4800 + (mo / 12) * 600
            elif yr == 2017: nq = 5500 + (mo / 12) * 1400
            elif yr == 2018: nq = 7200 - (600 if mo >= 10 else 0)
            elif yr == 2019: nq = 7000 + (mo / 12) * 2000
            elif yr == 2020: nq = 9100 if mo < 3 else (7600 if mo == 3 else 8800 + (mo - 4) * 450)
            elif yr == 2021: nq = 13200 + (mo / 12) * 2450
            elif yr == 2022: nq = 15000 - (mo / 12) * 4500
            elif yr == 2023: nq = 11000 + (mo / 12) * 4000
            elif yr == 2024: nq = 15200 + (mo / 12) * 3600
            elif yr == 2025: nq = 19000 + (mo / 12) * 1000
            else: nq = 20200 + (mo / 12) * 400
            nasdaq_series.append(round(nq, 1))

            # Euro Stoxx 50
            if yr == 2015: sx = 3300 + (mo - 6) * 20
            elif yr == 2016: sx = 3050 + (mo / 12) * 240
            elif yr == 2017: sx = 3350 + (mo / 12) * 160
            elif yr == 2018: sx = 3400 - (mo / 12) * 400
            elif yr == 2019: sx = 3100 + (mo / 12) * 650
            elif yr == 2020: sx = 3700 if mo < 3 else (2800 if mo == 3 else 3200 + (mo - 4) * 70)
            elif yr == 2021: sx = 3600 + (mo / 12) * 700
            elif yr == 2022: sx = 4200 - (mo / 12) * 400
            elif yr == 2023: sx = 3900 + (mo / 12) * 620
            elif yr == 2024: sx = 4500 + (mo / 12) * 550
            elif yr == 2025: sx = 5050 + (mo / 12) * 120
            else: sx = 5180 + (mo / 12) * 50
            stoxx50_series.append(round(sx, 1))

            # PX Index (Pražská burza)
            if yr == 2015: px = 950 + (mo - 6) * 10
            elif yr == 2016: px = 900 + (mo / 12) * 30
            elif yr == 2017: px = 940 + (mo / 12) * 140
            elif yr == 2018: px = 1080 - (mo / 12) * 60
            elif yr == 2019: px = 1020 + (mo / 12) * 100
            elif yr == 2020: px = 1100 if mo < 3 else (790 if mo == 3 else 900 + (mo - 4) * 25)
            elif yr == 2021: px = 1050 + (mo / 12) * 370
            elif yr == 2022: px = 1420 - (mo / 12) * 220
            elif yr == 2023: px = 1220 + (mo / 12) * 190
            elif yr == 2024: px = 1430 + (mo / 12) * 180
            elif yr == 2025: px = 1620 + (mo / 12) * 70
            else: px = 1690 + (mo / 12) * 30
            px_series.append(round(px, 1))

        # ---------------------------------------------------------------------
        # E. DENNÍ DEVÍZOVÝ DATASET A MĚSÍČNÍ ALIGNMENT
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
            # ČR
            "repo_rate": np.round(repo_arr, 2),
            "discount_rate": np.round(discount_arr, 2),
            "lombard_rate": np.round(lombard_arr, 2),
            "pribor_1m": np.round(pribor_1m, 2),
            "pribor_3m": np.round(pribor_3m, 2),
            "pribor_6m": np.round(pribor_6m, 2),
            "cpi_yoy": cpi_series,
            "cpi_core_yoy": cpi_core_series,
            "unemployment_rate": une_series,
            "retail_sales_yoy": ret_cz_series,
            "industrial_prod_yoy": ind_cz_series,
            "eur_czk": df_fx_m["eur_czk"],
            "usd_czk": df_fx_m["usd_czk"],
            "pln_czk": df_fx_m["pln_czk"],
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
            # EU
            "ecb_deposit_rate": np.round(depo_arr, 2),
            "ecb_refi_rate": np.round(mro_arr, 2),
            "ecb_lending_rate": np.round(lend_arr, 2),
            "euribor_3m": np.round(euribor_arr, 2),
            "estr_rate": np.round(estr_arr, 2),
            "eu_cpi_yoy": eu_cpi_series,
            "eu_core_cpi_yoy": eu_core_cpi_series,
            "eu_unemployment_rate": eu_une_series,
            "eu_retail_sales_yoy": eu_ret_series,
            "eu_industrial_prod_yoy": eu_ind_series,
            "bund_10y": bund_10_series,
            "bund_2y": bund_2_series,
            "bund_5y": np.round(np.array(bund_10_series) - 0.20, 2),
            "bund_30y": np.round(np.array(bund_10_series) + 0.35, 2),
            "bund_spread_10y_2y": np.round(np.array(bund_10_series) - np.array(bund_2_series), 2),
            "eur_usd": df_fx_m["eur_usd"],
            "eur_pln": df_fx_m["eur_pln"],
            "eur_gbp": df_fx_m["eur_gbp"],
            # USA
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
            "us_retail_sales_yoy": us_ret_series,
            "us_industrial_prod_yoy": us_ind_series,
            "dxy_index": df_fx_m["dxy_index"],
            "gbp_usd": df_fx_m["gbp_usd"],
            "usd_jpy": df_fx_m["usd_jpy"],
            "usd_pln": df_fx_m["usd_pln"],
            "usd_chf": df_fx_m["usd_chf"],
            # Akciové trhy
            "px_index": px_series,
            "stoxx50_index": stoxx50_series,
            "sp500_index": sp500_series,
            "nasdaq_index": nasdaq_series
        }
        df_monthly = pd.DataFrame(df_monthly_data)

        # ---------------------------------------------------------------------
        # E. Kvartální HDP, Dluh a Saldo (ČR, EU i USA)
        # ---------------------------------------------------------------------
        dates_q = pd.date_range("2015-01-01", "2026-07-01", freq=OFFSET_QUARTER_END)
        q_records = []

        gdp_growth_map_cz = {
            2015: [5.5, 5.6, 5.2, 5.0], 2016: [2.8, 2.5, 2.3, 2.4], 2017: [5.0, 5.2, 5.4, 5.1],
            2018: [3.5, 3.2, 3.1, 2.9], 2019: [3.2, 3.1, 2.9, 2.7], 2020: [-1.8, -10.8, -5.0, -4.4],
            2021: [-2.1, 8.5, 3.9, 4.0], 2022: [4.2, 3.4, 1.6, 0.4], 2023: [-0.4, -0.6, -0.5, 0.3],
            2024: [0.6, 0.8, 1.2, 1.6], 2025: [2.0, 2.3, 2.5, 2.6], 2026: [2.1, 1.8]
        }
        gdp_growth_map_eu = {
            2015: [2.1, 2.2, 2.1, 2.2], 2016: [1.9, 1.9, 1.9, 2.1], 2017: [2.6, 2.7, 2.9, 2.8],
            2018: [2.4, 2.2, 1.8, 1.7], 2019: [1.8, 1.7, 1.7, 1.4], 2020: [-3.2, -14.2, -4.1, -4.4],
            2021: [-1.2, 14.1, 4.2, 5.1], 2022: [5.4, 4.2, 2.5, 1.8], 2023: [1.2, 0.6, 0.1, 0.4],
            2024: [0.5, 0.7, 0.9, 1.1], 2025: [1.4, 1.5, 1.6, 1.7], 2026: [1.5, 1.6]
        }
        gdp_growth_map_us = {
            2015: [3.3, 2.7, 2.4, 2.3], 2016: [1.6, 1.4, 1.9, 2.0], 2017: [2.0, 2.3, 2.3, 2.5],
            2018: [2.8, 3.0, 3.0, 2.6], 2019: [2.2, 2.4, 2.5, 2.6], 2020: [0.3, -8.6, -2.2, -1.8],
            2021: [1.2, 12.2, 4.9, 5.4], 2022: [3.6, 1.9, 1.7, 0.7], 2023: [1.7, 2.4, 2.9, 3.1],
            2024: [2.9, 3.0, 2.8, 2.5], 2025: [2.2, 2.3, 2.4, 2.2], 2026: [2.1, 2.0]
        }

        fiscal_map_cz = {
            2015: (1673.0, 39.9, -62.8), 2016: (1613.0, 36.6, 61.8), 2017: (1625.0, 34.2, -6.2),
            2018: (1622.0, 32.1, 2.9), 2019: (1640.0, 30.0, -28.5), 2020: (2050.0, 37.7, -367.4),
            2021: (2466.0, 42.0, -419.7), 2022: (2895.0, 44.2, -360.4), 2023: (3111.0, 44.0, -288.5),
            2024: (3340.0, 43.8, -282.0), 2025: (3580.0, 43.5, -241.0), 2026: (3820.0, 44.1, -220.0),
        }

        quarter_idx = 0
        for d in dates_q:
            yr = d.year
            q_num = (d.month - 1) // 3 + 1

            growth_cz = gdp_growth_map_cz.get(yr, [2.0])[min(q_num - 1, 3)]
            growth_eu = gdp_growth_map_eu.get(yr, [1.5])[min(q_num - 1, 3)]
            growth_us = gdp_growth_map_us.get(yr, [2.2])[min(q_num - 1, 3)]

            nom_cz = 1150.0 + (quarter_idx * 24.5)
            nom_eu = 2800.0 + (quarter_idx * 38.0)
            nom_us = 4500.0 + (quarter_idx * 65.0)

            debt_nom_cz, debt_pct_cz, def_ann_cz = fiscal_map_cz.get(yr, (3000.0, 44.0, -250.0))
            debt_q_cz = debt_nom_cz + (q_num - 2) * 35.0
            def_q_cz = def_ann_cz / 4.0

            q_records.append({
                "date": d,
                "quarter": f"{yr}-Q{q_num}",
                # CZ
                "gdp_growth_real": round(growth_cz, 1),
                "gdp_nominal_czk_bn": round(nom_cz, 1),
                "public_debt_czk_bn": round(debt_q_cz, 1),
                "public_debt_gdp_pct": round(debt_pct_cz + (q_num - 2) * 0.2, 1),
                "budget_deficit_czk_bn": round(def_q_cz, 1),
                # EU
                "eu_gdp_growth_real": round(growth_eu, 1),
                "eu_gdp_nominal_eur_bn": round(nom_eu, 1),
                "eu_public_debt_eur_bn": round(9800.0 + quarter_idx * 85.0, 1),
                "eu_public_debt_gdp_pct": round(88.0 + (quarter_idx * 0.12), 1),
                "eu_budget_deficit_eur_bn": round(-85.0 - (quarter_idx * 1.5), 1),
                # US
                "us_gdp_growth_real": round(growth_us, 1),
                "us_gdp_nominal_usd_bn": round(nom_us * 4.0, 1),
                "us_public_debt_usd_bn": round(18150.0 + (quarter_idx * 370.0), 1),
                "us_public_debt_gdp_pct": round(min(125.0, 101.0 + (quarter_idx * 0.55)), 1),
                "us_budget_deficit_usd_bn": round(-350.0 - (quarter_idx * 3.5), 1)
            })
            quarter_idx += 1

        df_quarterly_macro = pd.DataFrame(q_records)

        df_monthly = pd.merge_asof(
            df_monthly.sort_values("date"),
            df_quarterly_macro.sort_values("date"),
            on="date",
            direction="nearest"
        )

        agg_rules: Dict[str, str] = {c: "mean" for c in df_monthly.columns if c not in ("date", "quarter")}
        for col_last in [
            "repo_rate", "discount_rate", "lombard_rate", "ecb_deposit_rate",
            "fed_funds_upper", "fed_funds_lower", "eur_czk", "usd_czk",
            "pln_czk", "gbp_czk", "eur_usd", "dxy_index",
            "px_index", "stoxx50_index", "sp500_index", "nasdaq_index"
        ]:
            if col_last in agg_rules:
                agg_rules[col_last] = "last"

        df_quarterly = df_monthly.set_index("date").resample(OFFSET_QUARTER_END).agg(agg_rules).reset_index()
        df_quarterly["quarter"] = df_quarterly["date"].dt.year.astype(str) + "-Q" + ((df_quarterly["date"].dt.month - 1) // 3 + 1).astype(str)

        return df_monthly, df_quarterly, df_daily_fx

    # =========================================================================
    # 6. HLAVNÍ METODA NAČTENÍ A SLOUČENÍ
    # =========================================================================

    def load_macro_data(
        self,
        frequency: str = "M",
        fred_api_key: Optional[str] = None,
        force_fallback: bool = False
    ) -> Tuple[pd.DataFrame, Dict[str, Any], pd.DataFrame]:
        """
        Hlavní metoda pro načtení kompletního makroekonomického datasetu pro ČR, EU i USA.
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

        df_fb_m, df_fb_q, df_daily_fx_fallback = self.generate_fallback_dataset()
        base_df = df_fb_m if frequency == "M" else df_fb_q
        df_daily_fx = df_daily_fx_fallback.copy()

        if force_fallback:
            status_info["mode"] = "FALLBACK"
            status_info["status_badge"] = "🟠 Fallback Model (Historická data ČR, EU & USA 2015–2026)"
            return base_df, status_info, df_daily_fx

        live_components: Dict[str, pd.DataFrame] = {}
        all_success = True

        # Eurostat ČR CPI
        try:
            live_components["cpi_cz"] = self.fetch_eurostat_cpi()
            status_info["endpoints"]["Eurostat CPI (ČR)"] = "🟢 OK (Live)"
        except Exception as e:
            logger.warning("Chyba Eurostat CPI ČR: %s", e)
            status_info["endpoints"]["Eurostat CPI (ČR)"] = f"⚠️ Fallback ({type(e).__name__})"

        # Eurostat EU CPI & Core
        try:
            live_components["cpi_ea"] = self.fetch_eurostat_ea_cpi()
            status_info["endpoints"]["Eurostat CPI & Core (EU)"] = "🟢 OK (Live)"
        except Exception as e:
            logger.warning("Chyba Eurostat CPI EU: %s", e)
            status_info["endpoints"]["Eurostat CPI & Core (EU)"] = f"⚠️ Fallback ({type(e).__name__})"

        # Eurostat Nezaměstnanost ČR & EU
        try:
            live_components["unemployment"] = self.fetch_eurostat_unemployment()
            status_info["endpoints"]["Eurostat Nezaměstnanost (ČR & EU)"] = "🟢 OK (Live)"
        except Exception as e:
            logger.warning("Chyba Eurostat Nezaměstnanost: %s", e)
            status_info["endpoints"]["Eurostat Nezaměstnanost"] = f"⚠️ Fallback ({type(e).__name__})"

        # Eurostat HDP ČR & EU
        try:
            live_components["gdp"] = self.fetch_eurostat_gdp()
            status_info["endpoints"]["Eurostat HDP (ČR & EU)"] = "🟢 OK (Live)"
        except Exception as e:
            logger.warning("Chyba Eurostat HDP: %s", e)
            status_info["endpoints"]["Eurostat HDP"] = f"⚠️ Fallback ({type(e).__name__})"

        # Eurostat Dluh ČR & EU
        try:
            live_components["debt"] = self.fetch_eurostat_debt()
            status_info["endpoints"]["Eurostat Veřejný dluh (ČR & EU)"] = "🟢 OK (Live)"
        except Exception as e:
            logger.warning("Chyba Eurostat Dluh: %s", e)
            status_info["endpoints"]["Eurostat Veřejný dluh"] = f"⚠️ Fallback ({type(e).__name__})"

        # ČNB Sazby měnové politiky
        try:
            live_components["rates"] = self.fetch_cnb_policy_rates()
            status_info["endpoints"]["ČNB Sazby (Repo, Diskont, Lombard)"] = "🟢 OK (Live)"
        except Exception as e:
            logger.warning("Chyba ČNB Sazby: %s", e)
            status_info["endpoints"]["ČNB Sazby"] = f"⚠️ Fallback ({type(e).__name__})"

        # ČNB PRIBOR
        try:
            live_components["pribor"] = self.fetch_cnb_pribor(start_year=2015, end_year=datetime.now().year)
            status_info["endpoints"]["ČNB PRIBOR (1M, 3M, 6M)"] = "🟢 OK (Live)"
        except Exception as e:
            logger.warning("Chyba ČNB PRIBOR: %s", e)
            status_info["endpoints"]["ČNB PRIBOR"] = f"⚠️ Fallback ({type(e).__name__})"

        # ČNB Denní devizové kurzy (EUR, USD, PLN, GBP, JPY, CHF & DXY)
        try:
            df_live_fx = self.fetch_cnb_fx_daily(start_year=2015, end_year=datetime.now().year)
            if not df_live_fx.empty:
                df_daily_fx = df_live_fx
                live_components["fx_daily"] = df_live_fx
                status_info["endpoints"]["ČNB Denní kurzy (EUR, USD, PLN, GBP, DXY)"] = "🟢 OK (Live Denní data)"
        except Exception as e:
            logger.warning("Chyba ČNB kurzy: %s", e)
            status_info["endpoints"]["ČNB Denní kurzy"] = f"⚠️ Fallback ({type(e).__name__})"

        # Eurostat 10Y Dluhopisy (ČR CZGB & Německo Bund)
        try:
            live_components["bond_10y"] = self.fetch_eurostat_10y_bond()
            status_info["endpoints"]["Eurostat 10Y Dluhopisy (CZGB & Bund)"] = "🟢 OK (Live)"
        except Exception as e:
            logger.warning("Chyba Eurostat 10Y Dluhopisy: %s", e)
            status_info["endpoints"]["Eurostat 10Y Dluhopisy"] = f"⚠️ Fallback ({type(e).__name__})"

        # U.S. Treasury Výnosová křivka
        try:
            live_components["us_treasury"] = self.fetch_us_treasury_yields(start_year=2024, end_year=datetime.now().year)
            status_info["endpoints"]["U.S. Treasury (home.treasury.gov)"] = "🟢 OK (Live)"
        except Exception as e:
            logger.warning("Chyba US Treasury: %s", e)
            status_info["endpoints"]["U.S. Treasury"] = f"⚠️ Fallback ({type(e).__name__})"

        # Yahoo Finance Akciové indexy (S&P 500, NASDAQ, Euro Stoxx 50)
        try:
            live_components["stocks"] = self.fetch_stock_indices()
            status_info["endpoints"]["Akciové trhy (S&P 500, NASDAQ, Euro Stoxx 50)"] = "🟢 OK (Live Yahoo Finance)"
        except Exception as e:
            logger.warning("Chyba Akciové indexy: %s", e)
            status_info["endpoints"]["Akciové trhy"] = f"⚠️ Fallback ({type(e).__name__})"

        # Sloučení komponent do finální matice
        final_df = base_df.copy()

        if "cpi_cz" in live_components:
            df_c = live_components["cpi_cz"]
            if frequency == "Q":
                df_c = df_c.set_index("date").resample(OFFSET_QUARTER_END).mean().reset_index()
            final_df = pd.merge(final_df.drop(columns=["cpi_yoy"], errors="ignore"), df_c[["date", "cpi_yoy"]], on="date", how="left")
            final_df["cpi_yoy"] = final_df["cpi_yoy"].ffill()

        if "cpi_ea" in live_components:
            df_ea = live_components["cpi_ea"]
            if frequency == "Q":
                df_ea = df_ea.set_index("date").resample(OFFSET_QUARTER_END).mean().reset_index()
            final_df = pd.merge(final_df.drop(columns=["eu_cpi_yoy", "eu_core_cpi_yoy"], errors="ignore"), df_ea[["date", "eu_cpi_yoy", "eu_core_cpi_yoy"]], on="date", how="left")
            final_df["eu_cpi_yoy"] = final_df["eu_cpi_yoy"].ffill()
            final_df["eu_core_cpi_yoy"] = final_df["eu_core_cpi_yoy"].ffill()

        if "unemployment" in live_components:
            df_u = live_components["unemployment"]
            if frequency == "Q":
                df_u = df_u.set_index("date").resample(OFFSET_QUARTER_END).mean().reset_index()
            final_df = pd.merge(final_df.drop(columns=["unemployment_rate", "eu_unemployment_rate"], errors="ignore"), df_u, on="date", how="left")
            final_df["unemployment_rate"] = final_df["unemployment_rate"].ffill()
            final_df["eu_unemployment_rate"] = final_df["eu_unemployment_rate"].ffill()

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

        # Agregace denních devizových kurzů
        fx_cols_to_merge = [c for c in df_daily_fx.columns if c != "date"]
        df_fx_agg = df_daily_fx.set_index("date").resample(OFFSET_MONTH_END if frequency == "M" else OFFSET_QUARTER_END).last().reset_index()
        final_df = pd.merge(final_df.drop(columns=fx_cols_to_merge, errors="ignore"), df_fx_agg, on="date", how="left")
        for c in fx_cols_to_merge:
            final_df[c] = final_df[c].ffill().bfill()

        if "bond_10y" in live_components:
            df_b = live_components["bond_10y"]
            if frequency == "Q":
                df_b = df_b.set_index("date").resample(OFFSET_QUARTER_END).mean().reset_index()
            final_df = pd.merge(final_df.drop(columns=["czgb_10y", "bund_10y"], errors="ignore"), df_b, on="date", how="left")
            final_df["czgb_10y"] = final_df["czgb_10y"].ffill()
            final_df["bund_10y"] = final_df["bund_10y"].ffill()

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

        if "stocks" in live_components:
            df_st = live_components["stocks"]
            st_cols = [c for c in df_st.columns if c != "date"]
            df_st_agg = df_st.set_index("date").resample(OFFSET_MONTH_END if frequency == "M" else OFFSET_QUARTER_END).last().reset_index()
            final_df = pd.merge(final_df, df_st_agg, on="date", how="left", suffixes=("", "_live"))
            for col in st_cols:
                live_c = f"{col}_live"
                if live_c in final_df.columns:
                    final_df[col] = final_df[live_c].combine_first(final_df[col])
                    final_df = final_df.drop(columns=[live_c])
                final_df[col] = final_df[col].ffill().bfill()

        # Kontrola integrity všech definovaných indikátorů
        for ind_key in INDICATORS.keys():
            if ind_key not in final_df.columns:
                if ind_key in base_df.columns:
                    final_df[ind_key] = base_df[ind_key]
                else:
                    final_df[ind_key] = 0.0
            final_df[ind_key] = final_df[ind_key].ffill().bfill()

        if all_success and live_components:
            status_info["mode"] = "LIVE"
            status_info["status_badge"] = "🟢 Živá data (ČNB Denní kurzy & Sazby, Eurostat & US Treasury)"
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

    @st.cache_data(ttl=3600, show_spinner="Stahuji a zpracovávám makroekonomická data ČR, EU a USA...")
    def get_cached_macro_data(
        frequency: str = "M",
        fred_api_key: Optional[str] = None,
        force_fallback: bool = False,
        _cache_bust: str = "v2026_10_10_daily_eu_cz_us_v4"
    ) -> Tuple[pd.DataFrame, Dict[str, Any], pd.DataFrame]:
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
        _cache_bust: str = "v2026_10_10_daily_eu_cz_us_v4"
    ) -> Tuple[pd.DataFrame, Dict[str, Any], pd.DataFrame]:
        loader = DataLoader()
        return loader.load_macro_data(
            frequency=frequency,
            fred_api_key=fred_api_key,
            force_fallback=force_fallback
        )
