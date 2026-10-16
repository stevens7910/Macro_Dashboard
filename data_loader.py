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

import html
import json
import logging
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import quote_plus


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
    "cz_pmi_manufacturing": IndicatorInfo(
        code="cz_pmi_manufacturing",
        name_cz="PMI v průmyslu ČR (S&P Global)",
        unit="bodů",
        category="Předstihové ukazatele",
        description="Index nákupních manažerů v českém zpracovatelském průmyslu od S&P Global. Hodnota nad 50 bodů značí expanzi, pod 50 kontrakci odvětví.",
        region="CZ"
    ),
    "cz_confidence_composite": IndicatorInfo(
        code="cz_confidence_composite",
        name_cz="Důvěra podnikatelů a spotřebitelů (ČSÚ)",
        unit="body",
        category="Předstihové ukazatele",
        description="Souhrnný indikátor důvěry (konjunkturální průzkum ČSÚ) kombinující sentiment podnikatelů (průmysl, stavebnictví, obchod, služby) a spotřebitelů.",
        region="CZ"
    ),
    "cz_nominal_wage_yoy": IndicatorInfo(
        code="cz_nominal_wage_yoy",
        name_cz="Průměrná hrubá mzda nominálně (YoY)",
        unit="%",
        category="Trh práce",
        description="Meziroční nominální růst průměrné hrubé měsíční mzdy na přepočtené počty zaměstnanců v národním hospodářství ČR (ČSÚ).",
        region="CZ"
    ),
    "cz_real_wage_yoy": IndicatorInfo(
        code="cz_real_wage_yoy",
        name_cz="Průměrná reálná mzda (YoY)",
        unit="%",
        category="Trh práce",
        description="Meziroční reálná změna průměrné hrubé mzdy v ČR očištěná o inflaci měřenou indexem spotřebitelských cen (ČSÚ).",
        region="CZ"
    ),
    "cz_mortgage_rate": IndicatorInfo(
        code="cz_mortgage_rate",
        name_cz="Nové hypotéky – objem a průměrná sazba",
        unit="% / mld. Kč",
        category="Bankovní sektor a úvěry",
        description="Průměrná úroková sazba a celkový objem skutečně nově poskytnutých hypotečních úvěrů na bydlení bez refinancování (ČBA Hypomonitor / ČNB).",
        region="CZ"
    ),
    "cz_corporate_loans_yoy": IndicatorInfo(
        code="cz_corporate_loans_yoy",
        name_cz="Korporátní úvěry – meziroční růst",
        unit="%",
        category="Bankovní sektor a úvěry",
        description="Meziroční tempo růstu stavu bankovních úvěrů poskytnutých nefinančním podnikům v České republice (Měnová a finanční statistika ČNB).",
        region="CZ"
    ),
    "cz_m2_growth_yoy": IndicatorInfo(
        code="cz_m2_growth_yoy",
        name_cz="Měnový agregát M2 (YoY)",
        unit="%",
        category="Měnová zásoba",
        description="Meziroční růst peněžní zásoby M2 v ČR (oběživo, jednodenní vklady, vklady se splatností do 2 let a s výpovědní lhůtou do 3 měsíců – ČNB).",
        region="CZ"
    ),
    "cz_current_account_gdp_pct": IndicatorInfo(
        code="cz_current_account_gdp_pct",
        name_cz="Běžný účet platební bilance (k HDP)",
        unit="% HDP",
        category="Vnější rovnováha",
        description="Saldo běžného účtu platební bilance ČR v poměru k HDP vyjadřující vnější rovnováhu a mezinárodní toky zboží, služeb a výnosů (ČNB / ČSÚ).",
        region="CZ"
    ),
    "cz_trade_balance_czk_bn": IndicatorInfo(
        code="cz_trade_balance_czk_bn",
        name_cz="Bilance zahraničního obchodu ČSÚ",
        unit="mld. CZK",
        category="Vnější rovnováha",
        description="Měsíční saldo zahraničního obchodu se zbožím podle národního pojetí v miliardách Kč (Český statistický úřad).",
        region="CZ"
    ),
    "czgb_bund_spread_10y": IndicatorInfo(
        code="czgb_bund_spread_10y",
        name_cz="Kreditní spread 10Y CZGB vs. 10Y Bund",
        unit="bps",
        category="Dluhopisový trh",
        description="Výnosové rozpětí mezi 10letým českým vládním dluhopisem a německým referenčním Bundem v bazických bodech (bps).",
        region="CZ"
    ),
    "cz_asw_10y_spread": IndicatorInfo(
        code="cz_asw_10y_spread",
        name_cz="Asset Swap Spread (ASW 10Y CZK)",
        unit="bps",
        category="Dluhopisový trh",
        description="Asset swap spread 10letého státního dluhopisu CZGB vůči křivce úrokových swapů CZK IRS v bazických bodech (indikátor relativní hodnoty).",
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
    "eu_ifo_business_climate": IndicatorInfo(
        code="eu_ifo_business_climate",
        name_cz="Německý Ifo index podnikatelského klimatu",
        unit="body",
        category="EU Předstihové ukazatele",
        description="Ifo Geschäftsklimaindex – přední barometr německé ekonomiky založený na měsíčním průzkumu mezi 9 000 podniky (Ifo Institut Mnichov).",
        region="EU"
    ),
    "eu_composite_pmi": IndicatorInfo(
        code="eu_composite_pmi",
        name_cz="Composite PMI Eurozóny",
        unit="body",
        category="EU Předstihové ukazatele",
        description="Souhrnný index nákupních manažerů Eurozóny kombinující výrobní sektor a služby (S&P Global / HCOB Flash Eurozone PMI).",
        region="EU"
    ),
    "eu_negotiated_wages_yoy": IndicatorInfo(
        code="eu_negotiated_wages_yoy",
        name_cz="Sjednané mzdy v Eurozóně (ECB YoY)",
        unit="%",
        category="EU Trh práce",
        description="Meziroční růst smluvně sjednaných mezd v Eurozóně sledovaný ECB jako klíčový signál pro mzdově-inflační dynamiku a rozhodování o sazbách.",
        region="EU"
    ),
    "eu_btp_bund_spread": IndicatorInfo(
        code="eu_btp_bund_spread",
        name_cz="Rizikový spread Itálie vs. Německo (10Y BTP - Bund)",
        unit="bps",
        category="EU Dluhopisový trh",
        description="Výnosový spread mezi 10letým italským státním dluhopisem (BTP) a německým Bundem v bazických bodech (barometr periferního rizika Eurozóny).",
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
    "us_ism_manufacturing": IndicatorInfo(
        code="us_ism_manufacturing",
        name_cz="ISM Index ve výrobě (Manufacturing PMI)",
        unit="body",
        category="US Předstihové ukazatele",
        description="Index nákupních manažerů v americkém výrobním sektoru od Institute for Supply Management (ISM). Hranice 50 bodů odděluje expanzi od útlumu.",
        region="US"
    ),
    "us_ism_services": IndicatorInfo(
        code="us_ism_services",
        name_cz="ISM Index ve službách (Services PMI)",
        unit="body",
        category="US Předstihové ukazatele",
        description="Index nákupních manažerů v sektoru služeb USA od Institute for Supply Management (ISM Non-Manufacturing PMI).",
        region="US"
    ),
    "us_michigan_sentiment": IndicatorInfo(
        code="us_michigan_sentiment",
        name_cz="Spotřebitelský sentiment (Univ. of Michigan)",
        unit="body",
        category="US Předstihové ukazatele",
        description="Index spotřebitelského sentimentu Michiganské univerzity (University of Michigan Consumer Sentiment Index) měřící náladu a očekávání amerických domácností.",
        region="US"
    ),
    "us_hourly_earnings_yoy": IndicatorInfo(
        code="us_hourly_earnings_yoy",
        name_cz="Průměrná hodinová mzda USA (Average Hourly Earnings YoY)",
        unit="%",
        category="US Trh práce",
        description="Meziroční růst průměrného hodinového výdělku zaměstnanců v soukromém nezemědělském sektoru USA (U.S. Bureau of Labor Statistics).",
        region="US"
    ),
    "vix_index": IndicatorInfo(
        code="vix_index",
        name_cz="Index volatility VIX",
        unit="body",
        category="Tržní sentiment a riziko",
        description="Cboe Volatility Index ('index strachu') měřící tržní očekávání 30denní volatility amerického akciového indexu S&P 500 implikované z cen opcí.",
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
    ),

    # =========================================================================
    # 🪙 KOMODITNÍ A SUROVINOVÉ TRHY (MĚSÍČNÍ DATA)
    # =========================================================================
    "gold_usd": IndicatorInfo(
        code="gold_usd",
        name_cz="Zlato (Gold)",
        unit="USD/oz",
        category="Komodity",
        description="Spotová / futures cena zlata na burze COMEX v amerických dolarech za trojskou unci (31,1035 g). Tradiční globální bezpečný přístav (safe haven), uchovatel hodnoty a klíčové zajištění proti inflaci a geopolitickému riziku.",
        region="GLOBAL"
    ),
    "oil_brent_usd": IndicatorInfo(
        code="oil_brent_usd",
        name_cz="Ropa Brent",
        unit="USD/barel",
        category="Komodity",
        description="Severomořská lehká ropa Brent (ICE Futures Europe) v USD za barel (159 litrů). Klíčový světový referenční benchmark pro ropné trhy a hlavní determinant nákladové inflace a cen pohonných hmot.",
        region="GLOBAL"
    ),
    "natgas_usd": IndicatorInfo(
        code="natgas_usd",
        name_cz="Zemní plyn (Henry Hub)",
        unit="USD/MMBtu",
        category="Komodity",
        description="Referenční cena zemního plynu na americkém uzlu Henry Hub (NYMEX) v USD za milion britských termálních jednotek (MMBtu). Klíčový energetický vstup pro výrobu elektřiny, průmysl a vytápění.",
        region="GLOBAL"
    ),
    "copper_usd": IndicatorInfo(
        code="copper_usd",
        name_cz="Měď (Doctor Copper)",
        unit="USD/libra",
        category="Komodity",
        description="Referenční cena elektrolytické mědi na burze COMEX v USD za libru (cca 0,4536 kg). Proslulý 'Doctor Copper' – předstihový barometr globálního průmyslu, stavebnictví, energetické sítě a moderní elektromobility.",
        region="GLOBAL"
    ),
    "silver_usd": IndicatorInfo(
        code="silver_usd",
        name_cz="Stříbro (Silver)",
        unit="USD/oz",
        category="Komodity",
        description="Cena fyzického stříbra na burze COMEX v USD za trojskou unci. Kov s duálním charakterem: silná průmyslová poptávka (fotovoltaika, mikroelektronika, automotive) kombinovaná s investiční funkcí drahého kovu.",
        region="GLOBAL"
    )
}

# Rychlé filtry indikátorů podle regionu
CZ_INDICATORS: Dict[str, IndicatorInfo] = {k: v for k, v in INDICATORS.items() if v.region == "CZ"}
EU_INDICATORS: Dict[str, IndicatorInfo] = {k: v for k, v in INDICATORS.items() if v.region == "EU"}
US_INDICATORS: Dict[str, IndicatorInfo] = {k: v for k, v in INDICATORS.items() if v.region == "US"}
MARKET_INDICATORS: Dict[str, IndicatorInfo] = {k: v for k, v in INDICATORS.items() if v.category in ("Akciové trhy", "Tržní sentiment a riziko")}
COMMODITY_INDICATORS: Dict[str, IndicatorInfo] = {k: v for k, v in INDICATORS.items() if v.category == "Komodity"}


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
        """Stáhne meziroční celkovou (HICP) a jádrovou (Core HICP) inflaci pro ČR z Eurostatu."""
        url_head = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/prc_hicp_manr?geo=CZ&coicop=CP00"
        url_core = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/prc_hicp_manr?geo=CZ&coicop=TOT_X_NRG_FOOD"

        resp = requests.get(url_head, headers=self.headers, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        time_labels = list(data.get("dimension", {}).get("time", {}).get("category", {}).get("label", {}).values())
        values_dict = data.get("value", {})

        core_map: Dict[str, float] = {}
        try:
            rc = requests.get(url_core, headers=self.headers, timeout=self.timeout)
            if rc.status_code == 200:
                dc = rc.json()
                tc = list(dc.get("dimension", {}).get("time", {}).get("category", {}).get("label", {}).values())
                vc = dc.get("value", {})
                core_map = {tc[int(k)]: float(v) for k, v in vc.items() if int(k) < len(tc) and v is not None}
        except Exception as e:
            logger.warning("Chyba při stahování Core CPI ČR z Eurostatu: %s", e)

        records = []
        for idx, t_str in enumerate(time_labels):
            val = values_dict.get(str(idx))
            if val is not None:
                row_rec: Dict[str, Any] = {
                    "date": pd.to_datetime(t_str) + pd.offsets.MonthEnd(0),
                    "cpi_yoy": float(val)
                }
                if t_str in core_map:
                    row_rec["cpi_core_yoy"] = core_map[t_str]
                records.append(row_rec)
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
    # 5. LIVE API: YAHOO FINANCE & PSE (Denní akciové indexy + Měsíční komodity)
    # =========================================================================

    def fetch_stock_indices(self, interval: str = "1d") -> pd.DataFrame:
        """
        Stáhne denní historické kurzy hlavních světových a českých akciových indexů:
        - S&P 500 (^GSPC), NASDAQ Composite (^IXIC), Euro Stoxx 50 (^STOXX50E), VIX (^VIX) z Yahoo Finance
        - Index PX (Pražská burza / BCPP) přímo z oficiálního REST API Burzy cenných papírů Praha
        """
        tickers = {
            "sp500_index": "%5EGSPC",
            "nasdaq_index": "%5EIXIC",
            "stoxx50_index": "%5ESTOXX50E",
            "vix_index": "%5EVIX"
        }
        dfs = []
        for col_name, sym in tickers.items():
            try:
                url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range=12y&interval={interval}"
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

        # Stažení Indexu PX přímo z oficiálního API Burzy cenných papírů Praha (PSE / BCPP)
        try:
            url_px = "https://www.pse.cz/api/index-chart?indexName=PX&period=MAX"
            r_px = requests.get(url_px, headers=self.headers, timeout=self.timeout)
            if r_px.status_code == 200:
                data_px = r_px.json()
                vals_px = data_px.get("data", {}).get("value", [])
                if vals_px:
                    df_px = pd.DataFrame(vals_px, columns=["ts", "px_index"])
                    df_px["date"] = pd.to_datetime(df_px["ts"], unit="ms").dt.floor("D")
                    df_px = df_px.drop(columns=["ts"]).drop_duplicates("date").dropna()
                    dfs.append(df_px)
        except Exception as e:
            logger.warning("Chyba při stahování Indexu PX z PSE API: %s", e)

        if not dfs:
            raise ValueError("Nepodařilo se stáhnout žádné akciové indexy z Yahoo Finance ani PSE.")

        res_df = dfs[0]
        for d in dfs[1:]:
            res_df = pd.merge(res_df, d, on="date", how="outer")
        return res_df.sort_values("date").reset_index(drop=True).ffill().bfill()

    def fetch_commodity_prices(self) -> pd.DataFrame:
        """
        Stáhne měsíční historické kurzy 5 hlavních světových komodit z Yahoo Finance:
        - Zlato (Gold Futures GC=F, USD/oz)
        - Ropa Brent (Brent Crude BZ=F, USD/barel)
        - Zemní plyn (Natural Gas Henry Hub NG=F, USD/MMBtu)
        - Měď (Doctor Copper HG=F, USD/lb)
        - Stříbro (Silver Futures SI=F, USD/oz)
        """
        commodity_tickers = {
            "gold_usd": "GC=F",
            "oil_brent_usd": "BZ=F",
            "natgas_usd": "NG=F",
            "copper_usd": "HG=F",
            "silver_usd": "SI=F"
        }
        dfs = []
        for col_name, sym in commodity_tickers.items():
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
                logger.warning("Chyba při stahování komodity %s (%s): %s", col_name, sym, e)

        if not dfs:
            raise ValueError("Nepodařilo se stáhnout data komodit z Yahoo Finance.")

        res_df = dfs[0]
        for d in dfs[1:]:
            res_df = pd.merge(res_df, d, on="date", how="outer")
        return res_df.sort_values("date").reset_index(drop=True).ffill().bfill()

    # =========================================================================
    # 5b. LIVE API: ČBA Monitor (Hypomonitor, Úvěry, Vklady & Aktuální Zprávy)
    # =========================================================================

    @staticmethod
    def _parse_cba_blade_series(html_text: str, series_index: int = 0) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Extrahuje časovou řadu a metadata z var blade_graphData na stránkách cbamonitor.cz."""
        m = re.search(r"var\s+blade_graphData\s*=\s*(\{.*?\});?\s*</script>", html_text, re.DOTALL)
        if not m:
            return [], {}
        raw_json = json.loads(m.group(1))
        graph_data = raw_json.get("graph_data", [])
        graph_params = raw_json.get("graph_params", {}) if isinstance(raw_json.get("graph_params"), dict) else {}
        if not graph_data or series_index >= len(graph_data):
            return [], graph_params

        series_obj = graph_data[series_index]
        pts = list(series_obj.values()) if isinstance(series_obj, dict) else (series_obj if isinstance(series_obj, list) else [])
        records: List[Dict[str, Any]] = []
        for pt in pts:
            if not isinstance(pt, dict):
                continue
            x_str = pt.get("x")
            y_str = pt.get("y")
            if x_str and y_str is not None:
                try:
                    dt = pd.to_datetime(x_str, format="%m/%d/%Y", errors="coerce")
                    if pd.isna(dt):
                        dt = pd.to_datetime(x_str, errors="coerce")
                    if pd.notna(dt):
                        records.append({
                            "date": dt + pd.offsets.MonthEnd(0),
                            "value": float(y_str)
                        })
                except (ValueError, TypeError):
                    continue
        return records, graph_params

    def fetch_cba_hypomonitor_and_banking(self) -> pd.DataFrame:
        """
        Stáhne živá měsíční data ČBA Hypomonitoru a bankovní statistiky ČNB z cbamonitor.cz:
        - cz_mortgage_rate: Průměrná realizovaná úroková sazba nových hypoték bez refinancování (%)
        - cz_mortgage_volume_czk_bn: Objem skutečně nových hypoték bez refinancování (mld. Kč)
        - cz_corporate_loans_yoy: Meziroční dynamika úvěrů podnikům (% YoY)
        - cz_m2_growth_yoy: Meziroční dynamika vkladů / peněžní zásoby (% YoY)
        """
        dfs: List[pd.DataFrame] = []

        # 1. Úroková sazba nových hypoték (ČBA Hypomonitor + historie ČNB 2014–2019)
        try:
            url_rate = "https://www.cbamonitor.cz/statistika/prumerna-urokova-sazba-novych-hypotek"
            r = requests.get(url_rate, headers=self.headers, timeout=self.timeout)
            if r.status_code == 200:
                recs_cba, _ = self._parse_cba_blade_series(r.text, series_index=0)
                recs_cnb, _ = self._parse_cba_blade_series(r.text, series_index=1)
                combined_rate: Dict[pd.Timestamp, float] = {}
                for item in recs_cnb:
                    combined_rate[item["date"]] = round(item["value"], 2)
                for item in recs_cba:
                    combined_rate[item["date"]] = round(item["value"], 2)
                if combined_rate:
                    df_r = pd.DataFrame([
                        {"date": k, "cz_mortgage_rate": v} for k, v in combined_rate.items()
                    ]).sort_values("date").drop_duplicates("date")
                    dfs.append(df_r)
        except Exception as e:
            logger.warning("Chyba při stahování ČBA Hypomonitor sazeb: %s", e)

        # 2. Objem skutečně nových hypoték bez refinancování (mld. Kč)
        try:
            url_vol = "https://www.cbamonitor.cz/statistika/pocet-objem-nove-poskytnutych-hypotek"
            r = requests.get(url_vol, headers=self.headers, timeout=self.timeout)
            if r.status_code == 200:
                recs_vol, _ = self._parse_cba_blade_series(r.text, series_index=0)
                if recs_vol:
                    df_v = pd.DataFrame([
                        {"date": item["date"], "cz_mortgage_volume_czk_bn": round(item["value"], 1)}
                        for item in recs_vol
                    ]).sort_values("date").drop_duplicates("date")
                    dfs.append(df_v)
        except Exception as e:
            logger.warning("Chyba při stahování ČBA Hypomonitor objemů: %s", e)

        # 3. Korporátní úvěry YoY (Úvěry podnikům z ČNB ARAD přes ČBA Monitor)
        try:
            url_loans = "https://www.cbamonitor.cz/statistika/mesicni-vyvoj-uveru-bankovniho-sektoru"
            r = requests.get(url_loans, headers=self.headers, timeout=self.timeout)
            if r.status_code == 200:
                recs_corp, _ = self._parse_cba_blade_series(r.text, series_index=4)
                if not recs_corp:
                    recs_corp, _ = self._parse_cba_blade_series(r.text, series_index=0)
                if recs_corp:
                    df_l = pd.DataFrame([
                        {"date": item["date"], "cz_corporate_loans_yoy": round(item["value"], 1)}
                        for item in recs_corp
                    ]).sort_values("date").drop_duplicates("date")
                    dfs.append(df_l)
        except Exception as e:
            logger.warning("Chyba při stahování dynamiky korporátních úvěrů: %s", e)

        # 4. Dynamika vkladů / M2 YoY
        try:
            url_dep = "https://www.cbamonitor.cz/statistika/dynamika-vkladu"
            r = requests.get(url_dep, headers=self.headers, timeout=self.timeout)
            if r.status_code == 200:
                recs_dep, _ = self._parse_cba_blade_series(r.text, series_index=0)
                if recs_dep:
                    df_d = pd.DataFrame([
                        {"date": item["date"], "cz_m2_growth_yoy": round(item["value"], 1)}
                        for item in recs_dep
                    ]).sort_values("date").drop_duplicates("date")
                    dfs.append(df_d)
        except Exception as e:
            logger.warning("Chyba při stahování dynamiky vkladů: %s", e)

        if not dfs:
            raise ValueError("ČBA Monitor nevrátil žádná data pro bankovní sektor.")

        res = dfs[0]
        for d in dfs[1:]:
            res = pd.merge(res, d, on="date", how="outer")
        return res.sort_values("date").drop_duplicates("date").reset_index(drop=True)

    def fetch_live_cz_topic_news(self) -> Dict[str, Dict[str, Any]]:
        """
        Stáhne nejaktuálnější ověřené zprávy a analytické komentáře pro každou metriku/téma ČR.
        Kombinuje:
        1. Primární makroekonomické a hypoteční analýzy z ČBA Monitoru (cbamonitor.cz/aktualni-deni)
           seřazené striktně sestupně podle data publikace.
        2. Živé zpravodajství z Google News RSS (filtrované podle klíčových slov dané metriky
           a seřazené sestupně podle přesného času publikace pubDate).
        Vrací slovník {topic_key: {"title", "date", "source", "url", "summary", "pub_ts"}}.
        """
        cba_articles: List[Dict[str, Any]] = []
        if BeautifulSoup is not None:
            try:
                resp = requests.get("https://www.cbamonitor.cz/aktualni-deni", headers=self.headers, timeout=6)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    for card in soup.select("div[js-link-new-tab]"):
                        url = (card.get("js-link-new-tab") or "").strip()
                        h3 = card.find("h3")
                        title = h3.get_text(" ", strip=True) if h3 else ""
                        desc_el = card.find("p", attrs={"itemprop": "description"})
                        desc = desc_el.get_text(" ", strip=True) if desc_el else ""
                        date_text = ""
                        pub_dt = datetime(2020, 1, 1)
                        for sp in card.find_all("span"):
                            txt = sp.get_text(" ", strip=True)
                            m_dt = re.search(r"(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{4})", txt)
                            if m_dt:
                                d_i, m_i, y_i = int(m_dt.group(1)), int(m_dt.group(2)), int(m_dt.group(3))
                                pub_dt = datetime(y_i, m_i, d_i, 12, 0)
                                date_text = f"{d_i:02d}. {m_i:02d}. {y_i}"
                                break
                        if title and url:
                            cba_articles.append({
                                "title": title,
                                "url": url,
                                "date": date_text,
                                "summary": desc,
                                "source": "Česká bankovní asociace (ČBA Monitor)",
                                "pub_dt": pub_dt
                            })
            except Exception as e:
                logger.warning("Chyba při načítání aktualit z ČBA Monitoru: %s", e)

        cba_articles.sort(key=lambda x: x["pub_dt"], reverse=True)

        topic_configs: Dict[str, Dict[str, Any]] = {
            "banking": {
                "cba_keywords": ["hypomonitor", "hypote", "bankovní statistika", "úvěr"],
                "rss_query": "hypotéky sazba ČBA Hypomonitor OR úvěry ČNB",
                "rss_keywords": ["hypot", "hypomonitor", "sazb", "úvěr", "bank"],
                "prefer_cba": True
            },
            "rates": {
                "cba_keywords": ["čnb drží sazby", "sazby čnb", "repo", "bankovní rada", "jádrová inflace a energie nechávají"],
                "rss_query": "ČNB úrokové sazby repo sazba bankovní rada",
                "rss_keywords": ["čnb", "sazb", "repo", "bankovní rad", "michl", "měnov"],
                "prefer_cba": True
            },
            "inflation": {
                "cba_keywords": ["inflac", "spotřebitelsk"],
                "rss_query": "inflace ČR ČSÚ spotřebitelské ceny",
                "rss_keywords": ["inflac", "spotřebitelsk", "cen", "čsú"],
                "prefer_cba": True
            },
            "gdp": {
                "cba_keywords": ["růst české ekonomiky", "hdp", "hrubý domácí", "ekonomika ve"],
                "rss_query": "HDP česká ekonomika růst ČSÚ",
                "rss_keywords": ["hdp", "ekonomik", "růst", "čsú", "hrubý domácí"],
                "prefer_cba": True
            },
            "wages": {
                "cba_keywords": ["růst mezd", "mzd", "výdělk"],
                "rss_query": "průměrná mzda ČR ČSÚ reálné mzdy",
                "rss_keywords": ["mzd", "plat", "výdělk", "čsú"],
                "prefer_cba": True
            },
            "leading": {
                "cba_keywords": ["sentiment", "důvěr", "pmi"],
                "rss_query": "PMI průmysl ČR OR důvěra v ekonomiku ČSÚ",
                "rss_keywords": ["pmi", "důvěr", "sentiment", "průmysl", "nákupních manažerů"],
                "prefer_cba": True
            },
            "retail_industry": {
                "cba_keywords": ["průmysl", "maloobchod", "stavebnictví"],
                "rss_query": "průmyslová produkce ČR OR maloobchodní tržby ČSÚ",
                "rss_keywords": ["průmysl", "maloobchod", "tržb", "výrob", "čsú"],
                "prefer_cba": True
            },
            "unemployment": {
                "cba_keywords": ["nezaměstnanost", "trh práce"],
                "rss_query": "nezaměstnanost ČR Úřad práce MPSV",
                "rss_keywords": ["nezaměstnanost", "trh práce", "úřad práce", "volných míst"],
                "prefer_cba": False
            },
            "stocks_px": {
                "cba_keywords": [],
                "rss_query": "pražská burza index PX",
                "rss_keywords": ["pražská burza", "index px", "bcpp", "burz"],
                "prefer_cba": False
            },
            "fx": {
                "cba_keywords": ["korun", "kurz"],
                "rss_query": "kurz koruny EUR CZK ČNB",
                "rss_keywords": ["korun", "eur/czk", "dolar", "deviz", "měn"],
                "prefer_cba": False
            },
            "yield_curve": {
                "cba_keywords": ["výnosov", "dluhopis", "swap"],
                "rss_query": "státní dluhopisy ČR výnosy MF ČR",
                "rss_keywords": ["dluhopis", "výnos", "aukc", "státní", "mf čr"],
                "prefer_cba": False
            },
            "debt": {
                "cba_keywords": ["rozpočet", "dluh", "fiskál", "deficit"],
                "rss_query": "státní rozpočet schodek ČR veřejný dluh Ministerstvo financí",
                "rss_keywords": ["rozpoč", "schod", "dluh", "deficit", "ministerstvo financí"],
                "prefer_cba": False
            },
            "external": {
                "cba_keywords": ["zahraniční obchod", "export", "běžný účet"],
                "rss_query": "zahraniční obchod ČR bilance ČSÚ export",
                "rss_keywords": ["zahraniční obchod", "export", "vývoz", "bilanc", "běžný účet"],
                "prefer_cba": False
            },
            "intl_spread": {
                "cba_keywords": ["dluhopis", "výnos", "ecb", "fed"],
                "rss_query": "české státní dluhopisy výnosy ČNB ECB",
                "rss_keywords": ["dluhopis", "výnos", "čnb", "ecb", "sazb"],
                "prefer_cba": False
            }
        }

        results: Dict[str, Dict[str, Any]] = {}

        for topic_key, cfg in topic_configs.items():
            best_cba: Optional[Dict[str, Any]] = None
            for art in cba_articles:
                haystack = f"{art['title']} {art['summary']}".lower()
                if any(kw in haystack for kw in cfg.get("cba_keywords", [])):
                    best_cba = art
                    break

            best_rss: Optional[Dict[str, Any]] = None
            if not (cfg.get("prefer_cba") and best_cba is not None):
                q_str = cfg.get("rss_query", "")
                if q_str:
                    rss_url = f"https://news.google.com/rss/search?q={quote_plus(q_str)}&hl=cs&gl=CZ&ceid=CZ:cs"
                    try:
                        r_rss = requests.get(rss_url, headers=self.headers, timeout=4)
                        if r_rss.status_code == 200:
                            root = ET.fromstring(r_rss.content)
                            rss_candidates: List[Dict[str, Any]] = []
                            for item in root.findall("./channel/item"):
                                raw_title = (item.findtext("title") or "").strip()
                                link = (item.findtext("link") or "").strip()
                                pub_raw = (item.findtext("pubDate") or "").strip()
                                src_el = item.find("source")
                                src_name = (src_el.text or "").strip() if src_el is not None else ""

                                if " - " in raw_title and not src_name:
                                    parts = raw_title.rsplit(" - ", 1)
                                    clean_title, src_name = parts[0].strip(), parts[1].strip()
                                elif " - " in raw_title and raw_title.endswith(f" - {src_name}"):
                                    clean_title = raw_title[: -len(f" - {src_name}")].strip()
                                else:
                                    clean_title = raw_title

                                clean_title = html.unescape(clean_title)
                                req_kws = cfg.get("rss_keywords", [])
                                if req_kws and not any(k in clean_title.lower() for k in req_kws):
                                    continue

                                try:
                                    dt_parsed = parsedate_to_datetime(pub_raw).replace(tzinfo=None)
                                except Exception:
                                    dt_parsed = datetime(2020, 1, 1)

                                rss_candidates.append({
                                    "title": clean_title,
                                    "url": link,
                                    "date": dt_parsed.strftime("%d. %m. %Y"),
                                    "summary": "",
                                    "source": src_name or "Finanční zpravodajství ČR",
                                    "pub_dt": dt_parsed
                                })

                            if rss_candidates:
                                rss_candidates.sort(key=lambda x: x["pub_dt"], reverse=True)
                                best_rss = rss_candidates[0]
                    except Exception as e:
                        logger.warning("Chyba při načítání RSS pro téma %s: %s", topic_key, e)

            chosen = best_cba if (best_cba and (not best_rss or cfg.get("prefer_cba") or best_cba["pub_dt"] >= best_rss["pub_dt"])) else (best_rss or best_cba)
            if chosen:
                summary_txt = chosen.get("summary", "")
                results[topic_key] = {
                    "title": chosen["title"],
                    "url": chosen["url"],
                    "date": chosen["date"],
                    "summary": summary_txt,
                    "description": summary_txt,
                    "source": chosen["source"],
                    "pub_ts": chosen["pub_dt"].strftime("%Y-%m-%d")
                }

        return results

    # =========================================================================
    # 6. HISTORICKÝ FALLBACK MODEL (2015–2026: ČR, EU a USA)
    # =========================================================================

    def generate_fallback_daily_fx(self) -> pd.DataFrame:
        """Vygeneruje souvislý denní dataset devizových kurzů a akciových trhů 2015–2026 včetně PLN a GBP."""
        dates_d = pd.date_range("2015-01-01", "2026-10-16", freq="B")
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

        # Simulace denních akciových indexů pro fallback model
        sp_daily = 2050.0 + np.cumsum(np.random.normal(1.85, 22.0, n))
        sp_daily = np.clip(sp_daily, 1800.0, 7900.0)
        nq_daily = 4700.0 + np.cumsum(np.random.normal(7.2, 75.0, n))
        nq_daily = np.clip(nq_daily, 4200.0, 27500.0)
        sx_daily = 3150.0 + np.cumsum(np.random.normal(1.0, 25.0, n))
        sx_daily = np.clip(sx_daily, 2400.0, 6300.0)
        px_daily = 950.0 + np.cumsum(np.random.normal(0.55, 8.5, n))
        px_daily = np.clip(px_daily, 690.0, 2650.0)
        vix_daily = 14.5 + np.random.normal(0, 2.5, n)
        vix_daily = np.clip(vix_daily, 9.5, 65.0)

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
            "dxy_index": np.round(dxy, 2),
            "sp500_index": np.round(sp_daily, 2),
            "nasdaq_index": np.round(nq_daily, 2),
            "stoxx50_index": np.round(sx_daily, 2),
            "px_index": np.round(px_daily, 2),
            "vix_index": np.round(vix_daily, 2)
        })

    def generate_fallback_dataset(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Generuje realistická historická data pro ČR, EU i USA za období 2015–2026.
        Vrací trojici (df_monthly, df_quarterly, df_daily_fx).
        """
        dates_m = pd.date_range("2015-01-01", "2026-10-31", freq=OFFSET_MONTH_END)
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

        # Předstihové, mzdové, bankovní a vnější ukazatele ČR
        cz_pmi_series = []
        cz_conf_series = []
        cz_nom_wage_series = []
        cz_real_wage_series = []
        cz_mort_rate_series = []
        cz_mort_vol_series = []
        cz_corp_loans_series = []
        cz_m2_series = []
        cz_ca_series = []
        cz_trade_bal_series = []

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
                rates_25 = [4.00, 3.75, 3.75, 3.75, 3.50, 3.50, 3.50, 3.50, 3.50, 3.50, 3.50, 3.50]
                rate = rates_25[mo - 1]
            else:
                rates_26 = [3.50, 3.50, 3.50, 3.50, 3.50, 3.75, 3.75, 3.75, 3.75, 3.75, 3.75, 3.75]
                rate = rates_26[min(mo - 1, 11)]
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
                cpi_25 = [2.8, 2.7, 2.7, 2.5, 2.4, 2.2, 2.2, 2.1, 2.0, 2.1, 2.2, 2.3]
                core_25 = [2.5, 2.5, 2.6, 2.6, 2.7, 2.7, 2.8, 2.8, 2.8, 2.8, 2.8, 2.9]
                cpi, core = cpi_25[mo - 1], core_25[mo - 1]
            else:
                cpi_26 = [2.1, 2.0, 2.1, 2.2, 2.1, 2.0, 1.8, 1.9, 2.5, 2.5, 2.5, 2.5]
                core_26 = [2.8, 2.8, 2.9, 2.9, 3.0, 3.0, 3.0, 3.0, 2.9, 2.9, 2.9, 2.9]
                cpi, core = cpi_26[min(mo - 1, 11)], core_26[min(mo - 1, 11)]
            cpi_series.append(round(cpi, 1))
            cpi_core_series.append(round(core, 1))

            # Nezaměstnanost ČR (Eurostat SA % / MPSV)
            if yr == 2025:
                une_25 = [2.6, 2.7, 2.7, 2.7, 2.7, 2.7, 2.8, 2.8, 2.8, 2.8, 2.8, 2.9]
                une = une_25[mo - 1]
            elif yr >= 2026:
                une_26 = [2.9, 2.9, 2.9, 3.0, 3.0, 3.0, 3.1, 3.1, 3.2, 3.2, 3.2, 3.2]
                une = une_26[min(mo - 1, 11)]
            else:
                une = 2.7 if yr == 2024 else (2.4 if yr >= 2018 else 4.0)
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
            elif yr == 2025:
                ret_25 = [3.8, 4.1, 4.3, 4.0, 3.9, 4.2, 4.4, 4.0, 3.8, 3.9, 4.1, 4.2]
                ind_25 = [0.8, 1.1, 1.5, 1.2, 1.8, 2.1, 1.9, 1.6, 2.0, 2.2, 2.4, 2.5]
                ret_cz, ind_cz = ret_25[mo - 1], ind_25[mo - 1]
            else:
                ret_26 = [3.9, 3.7, 4.0, 3.8, 3.6, 3.5, 3.8, 3.6, 3.7, 3.7, 3.7, 3.7]
                ind_26 = [2.2, 2.4, 2.8, 2.5, 2.1, 2.3, 1.6, 2.0, 2.0, 2.0, 2.0, 2.0]
                ret_cz, ind_cz = ret_26[min(mo - 1, 11)], ind_26[min(mo - 1, 11)]
            ret_cz_series.append(round(ret_cz, 1))
            ind_cz_series.append(round(ind_cz, 1))

            # Předstihové ukazatele ČR: PMI a Důvěra ČSÚ
            if yr in (2015, 2016, 2017):
                cz_pmi = 55.5 + 1.5 * np.sin(mo)
                cz_conf = 99.0 + 2.0 * np.cos(mo)
            elif yr in (2018, 2019):
                cz_pmi = 51.0 - (mo / 12) * 5.0
                cz_conf = 97.5 - (mo / 12) * 3.0
            elif yr == 2020:
                cz_pmi = 35.1 if mo == 4 else (42.0 if mo < 6 else 48.5)
                cz_conf = 74.5 if mo == 4 else 86.0
            elif yr == 2021:
                cz_pmi = 57.0 + 3.0 * np.sin(mo)
                cz_conf = 96.5 + 1.5 * np.sin(mo)
            elif yr == 2022:
                cz_pmi = 48.0 - (mo / 12) * 6.0
                cz_conf = 91.0 - (mo / 12) * 3.5
            elif yr == 2023:
                cz_pmi = 42.5 + 0.5 * np.cos(mo)
                cz_conf = 89.5 + 1.0 * np.sin(mo)
            elif yr == 2024:
                cz_pmi = 43.5 + (mo / 12) * 2.5
                cz_conf = 93.0 + (mo / 12) * 3.0
            elif yr == 2025:
                cz_pmi = 46.8 + (mo / 12) * 2.4
                cz_conf = 96.5 + (mo / 12) * 2.0
            else:
                pmi_26 = [48.8, 49.2, 49.8, 50.1, 49.7, 49.4, 48.9, 49.3, 49.6, 49.6, 49.6, 49.6]
                conf_26 = [98.6, 99.1, 99.5, 99.2, 98.8, 98.4, 98.1, 97.9, 97.5, 97.5, 97.5, 97.5]
                cz_pmi = pmi_26[min(mo - 1, 11)]
                cz_conf = conf_26[min(mo - 1, 11)]
            cz_pmi_series.append(round(cz_pmi, 1))
            cz_conf_series.append(round(cz_conf, 1))

            # Trh práce ČR: Nominální a reálná mzda YoY
            if yr in (2015, 2016):
                nom_w = 4.2
            elif yr in (2017, 2018, 2019):
                nom_w = 7.5 + 0.5 * np.sin(mo)
            elif yr == 2020:
                nom_w = 3.6
            elif yr == 2021:
                nom_w = 5.8
            elif yr == 2022:
                nom_w = 6.8 + (mo / 12) * 1.2
            elif yr == 2023:
                nom_w = 7.8
            elif yr == 2024:
                nom_w = 7.1
            elif yr == 2025:
                nom_w_25 = [6.8, 6.8, 6.8, 7.0, 7.0, 7.0, 6.9, 6.9, 6.9, 6.7, 6.7, 6.7]
                nom_w = nom_w_25[mo - 1]
            else:
                nom_w_26 = [6.1, 6.1, 6.1, 6.4, 6.4, 6.4, 6.5, 6.5, 6.4, 6.4, 6.4, 6.4]
                nom_w = nom_w_26[min(mo - 1, 11)]
            real_w = round(nom_w - cpi, 1)
            cz_nom_wage_series.append(round(nom_w, 1))
            cz_real_wage_series.append(real_w)

            # Bankovní sektor ČR: Hypotéky (skutečná data ČBA Hypomonitor) & Korporátní úvěry YoY
            if yr <= 2017:
                m_rate, m_vol, c_loans = 2.05, 18.5, 5.2
            elif yr in (2018, 2019):
                m_rate, m_vol, c_loans = 2.65, 17.5, 5.8
            elif yr == 2020:
                m_rate_20 = [2.36, 2.42, 2.42, 2.37, 2.29, 2.20, 2.14, 2.11, 2.08, 2.04, 1.99, 1.97]
                m_vol_20 = [15.3, 16.0, 16.9, 16.3, 15.1, 19.7, 20.1, 17.7, 19.6, 21.7, 22.6, 22.9]
                m_rate, m_vol, c_loans = m_rate_20[mo - 1], m_vol_20[mo - 1], 3.8
            elif yr == 2021:
                m_rate_21 = [1.95, 1.95, 1.96, 2.00, 2.07, 2.13, 2.22, 2.32, 2.43, 2.54, 2.70, 3.00]
                m_vol_21 = [20.7, 23.5, 35.2, 31.8, 34.0, 38.3, 32.0, 32.3, 30.2, 31.2, 35.9, 34.2]
                m_rate, m_vol, c_loans = m_rate_21[mo - 1], m_vol_21[mo - 1], 1.8
            elif yr == 2022:
                m_rate_22 = [3.39, 3.84, 4.15, 4.39, 4.64, 5.01, 5.42, 5.76, 5.83, 5.86, 5.96, 5.98]
                m_vol_22 = [26.3, 20.8, 25.4, 14.2, 16.8, 15.7, 9.8, 8.2, 5.9, 6.1, 6.3, 6.5]
                m_rate, m_vol, c_loans = m_rate_22[mo - 1], m_vol_22[mo - 1], 6.8
            elif yr == 2023:
                m_rate_23 = [5.93, 5.90, 5.86, 5.89, 5.90, 5.86, 5.80, 5.78, 5.74, 5.71, 5.67, 5.65]
                m_vol_23 = [5.3, 6.5, 10.3, 8.7, 10.4, 11.6, 9.5, 11.4, 11.3, 13.2, 13.4, 12.7]
                m_rate, m_vol, c_loans = m_rate_23[mo - 1], m_vol_23[mo - 1], 5.1
            elif yr == 2024:
                m_rate_24 = [5.54, 5.36, 5.19, 5.09, 5.06, 5.05, 5.07, 4.98, 4.96, 4.90, 4.85, 4.80]
                m_vol_24 = [10.8, 13.0, 15.5, 19.0, 20.6, 21.0, 19.4, 25.7, 19.6, 21.7, 21.5, 19.7]
                c_loans_24 = [9.2, 10.6, 10.7, 9.3, 8.3, 7.2, 6.9, 5.8, 6.8, 5.1, 6.2, 5.2]
                m_rate, m_vol, c_loans = m_rate_24[mo - 1], m_vol_24[mo - 1], c_loans_24[mo - 1]
            elif yr == 2025:
                m_rate_25 = [4.78, 4.72, 4.68, 4.65, 4.60, 4.56, 4.53, 4.52, 4.52, 4.48, 4.48, 4.49]
                m_vol_25 = [18.7, 21.1, 27.1, 26.1, 27.3, 29.3, 29.8, 26.0, 29.5, 29.3, 28.1, 28.6]
                c_loans_25 = [4.9, 4.4, 4.1, 4.9, 5.6, 5.9, 1.5, 3.2, 2.9, 1.9, 4.8, 5.1]
                m_rate, m_vol, c_loans = m_rate_25[mo - 1], m_vol_25[mo - 1], c_loans_25[mo - 1]
            else:
                # 2026 skutečná trajektorie ČBA Hypomonitor & ČNB ARAD (leden–září 2026)
                m_rate_26 = [4.48, 4.46, 4.43, 4.52, 4.67, 4.79, 4.90, 5.00, 5.10, 5.10, 5.10, 5.10]
                m_vol_26 = [27.1, 29.7, 40.3, 44.2, 38.1, 36.5, 30.8, 26.8, 28.0, 28.0, 28.0, 28.0]
                c_loans_26 = [5.5, 6.9, 7.2, 7.6, 7.6, 9.6, 13.4, 13.3, 13.3, 13.3, 13.3, 13.3]
                m_rate = m_rate_26[min(mo - 1, 11)]
                m_vol = m_vol_26[min(mo - 1, 11)]
                c_loans = c_loans_26[min(mo - 1, 11)]
            cz_mort_rate_series.append(round(m_rate, 2))
            cz_mort_vol_series.append(round(m_vol, 1))
            cz_corp_loans_series.append(round(c_loans, 1))

            # Měnová zásoba / Dynamika vkladů ČR: M2 YoY
            if yr in (2015, 2016, 2017, 2018, 2019):
                m2_val = 7.2 + 0.6 * np.cos(mo)
            elif yr == 2020:
                m2_val = 10.4
            elif yr == 2021:
                m2_val = 8.5
            elif yr == 2022:
                m2_val = 6.2
            elif yr == 2023:
                m2_val = 7.6
            elif yr == 2024:
                m2_24 = [8.2, 7.2, 8.6, 8.4, 7.0, 6.5, 6.4, 6.6, 6.8, 7.6, 7.3, 7.8]
                m2_val = m2_24[mo - 1]
            elif yr == 2025:
                m2_25 = [5.7, 4.6, 4.1, 3.9, 5.3, 4.8, 4.3, 4.2, 3.6, 3.6, 3.2, 6.1]
                m2_val = m2_25[mo - 1]
            else:
                m2_26 = [5.5, 6.2, 5.6, 5.0, 5.1, 4.8, 4.7, 5.5, 5.5, 5.5, 5.5, 5.5]
                m2_val = m2_26[min(mo - 1, 11)]
            cz_m2_series.append(round(m2_val, 1))

            # Vnější rovnováha ČR: Běžný účet k HDP a Bilance zahraničního obchodu ČSÚ
            if yr <= 2019:
                ca_pct = 0.8
                tr_bal = 14.0 + 3.0 * np.sin(mo)
            elif yr == 2020:
                ca_pct = 1.6
                tr_bal = 12.0
            elif yr == 2021:
                ca_pct = -2.8
                tr_bal = -1.5
            elif yr == 2022:
                ca_pct = -5.4
                tr_bal = -18.0 + 4.0 * np.sin(mo)
            elif yr == 2023:
                ca_pct = 0.5
                tr_bal = 10.5 + 3.0 * np.cos(mo)
            elif yr == 2024:
                ca_pct = 1.5
                tr_bal = 17.5 + 2.5 * np.cos(mo)
            elif yr == 2025:
                ca_pct = 1.4
                tr_bal = 16.5 + 2.0 * np.cos(mo)
            else:
                ca_26 = [1.4, 1.4, 1.3, 1.2, 1.2, 1.1, 1.0, 1.1, 1.1, 1.1, 1.1, 1.1]
                tb_26 = [17.2, 19.8, 22.4, 18.5, 16.2, 18.9, 12.4, 15.6, 16.8, 16.8, 16.8, 16.8]
                ca_pct = ca_26[min(mo - 1, 11)]
                tr_bal = tb_26[min(mo - 1, 11)]
            cz_ca_series.append(round(ca_pct, 1))
            cz_trade_bal_series.append(round(tr_bal, 1))


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
        eu_ifo_series = []
        eu_pmi_series = []
        eu_wages_series = []
        eu_btp_spread_series = []

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

            # EU Předstihové: Ifo a Composite PMI
            if yr <= 2018:
                ifo_v = 102.5 + 2.0 * np.sin(mo)
                pmi_v = 55.0 + 1.5 * np.cos(mo)
            elif yr == 2019:
                ifo_v = 96.0 - (mo / 12) * 2.0
                pmi_v = 51.5
            elif yr == 2020:
                ifo_v = 74.3 if mo == 4 else (85.0 if mo < 6 else 90.0)
                pmi_v = 31.4 if mo == 4 else (42.0 if mo < 6 else 48.0)
            elif yr == 2021:
                ifo_v = 98.5 + 2.0 * np.sin(mo)
                pmi_v = 56.5 + 2.5 * np.sin(mo)
            elif yr == 2022:
                ifo_v = 91.0 - (mo / 12) * 5.5
                pmi_v = 52.0 - (mo / 12) * 4.5
            elif yr == 2023:
                ifo_v = 86.5 + 0.8 * np.cos(mo)
                pmi_v = 47.8 + 0.6 * np.cos(mo)
            elif yr == 2024:
                ifo_v = 87.2 + (mo / 12) * 1.6
                pmi_v = 49.6 + (mo / 12) * 1.4
            elif yr == 2025:
                ifo_v = 89.8
                pmi_v = 51.2
            else:
                ifo_v = 91.5
                pmi_v = 51.8
            eu_ifo_series.append(round(ifo_v, 1))
            eu_pmi_series.append(round(pmi_v, 1))

            # EU Trh práce: Sjednané mzdy ECB YoY
            if yr <= 2020:
                w_eu = 1.8 + 0.2 * np.sin(mo)
            elif yr == 2021:
                w_eu = 1.5
            elif yr == 2022:
                w_eu = 2.8 + (mo / 12) * 0.9
            elif yr == 2023:
                w_eu = 4.5
            elif yr == 2024:
                w_eu = 4.7 if mo < 6 else 3.8
            elif yr == 2025:
                w_eu = 3.3
            else:
                w_eu = 2.8
            eu_wages_series.append(round(w_eu, 1))

            # EU Dluhopisy: Rizikový spread BTP - Bund (bps)
            if yr <= 2019:
                btp_sp = 160.0 + 25.0 * np.sin(mo)
            elif yr == 2020:
                btp_sp = 190.0 if mo < 6 else 140.0
            elif yr == 2021:
                btp_sp = 108.0 + 8.0 * np.sin(mo)
            elif yr == 2022:
                btp_sp = 215.0 + 15.0 * np.cos(mo)
            elif yr == 2023:
                btp_sp = 185.0 - (mo / 12) * 15.0
            elif yr == 2024:
                btp_sp = 138.0 - (mo / 12) * 10.0
            elif yr == 2025:
                btp_sp = 122.0
            else:
                btp_sp = 118.0
            eu_btp_spread_series.append(round(btp_sp, 1))

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
        us_ism_mfg_series = []
        us_ism_srv_series = []
        us_mich_series = []
        us_earn_series = []
        vix_series = []

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

            # US Předstihové ukazatele: ISM Výroba, ISM Služby a Univ. of Michigan Sentiment
            if yr <= 2018:
                mfg_v = 55.0 + 2.5 * np.sin(mo)
                srv_v = 56.0 + 1.8 * np.cos(mo)
                mich_v = 95.0 + 3.0 * np.sin(mo)
            elif yr == 2019:
                mfg_v = 50.5 - (mo / 12) * 2.5
                srv_v = 54.5
                mich_v = 95.5 - (mo / 12) * 1.5
            elif yr == 2020:
                mfg_v = 41.5 if mo == 4 else (53.0 if mo >= 6 else 49.0)
                srv_v = 41.8 if mo == 4 else (56.0 if mo >= 6 else 52.0)
                mich_v = 71.8 if mo == 4 else (76.0 if mo >= 6 else 89.0)
            elif yr == 2021:
                mfg_v = 60.5 + 1.5 * np.sin(mo)
                srv_v = 62.0 + 2.5 * np.sin(mo)
                mich_v = 79.0 - (mo / 12) * 8.0
            elif yr == 2022:
                mfg_v = 54.0 - (mo / 12) * 5.5
                srv_v = 55.5 - (mo / 12) * 2.5
                mich_v = 58.0 - (8.0 if mo in (5, 6) else 0.0)  # dno červen 2022
            elif yr == 2023:
                mfg_v = 46.8 + 0.8 * np.cos(mo)
                srv_v = 52.5 + 0.8 * np.sin(mo)
                mich_v = 64.5 + (mo / 12) * 5.0
            elif yr == 2024:
                mfg_v = 48.0 + (mo / 12) * 1.6
                srv_v = 52.8 + (mo / 12) * 1.4
                mich_v = 73.0 + (mo / 12) * 4.0
            elif yr == 2025:
                mfg_v = 50.5
                srv_v = 53.6
                mich_v = 78.5
            else:
                mfg_v = 51.5
                srv_v = 54.0
                mich_v = 81.0
            us_ism_mfg_series.append(round(mfg_v, 1))
            us_ism_srv_series.append(round(srv_v, 1))
            us_mich_series.append(round(mich_v, 1))

            # US Trh práce: Průměrná hodinová mzda (YoY)
            if yr <= 2019:
                he_v = 2.8 + 0.3 * np.sin(mo)
            elif yr == 2020:
                he_v = 5.4
            elif yr == 2021:
                he_v = 4.8
            elif yr == 2022:
                he_v = 5.2 - (mo / 12) * 0.4
            elif yr == 2023:
                he_v = 4.4 - (mo / 12) * 0.3
            elif yr == 2024:
                he_v = 3.9
            elif yr == 2025:
                he_v = 3.6
            else:
                he_v = 3.4
            us_earn_series.append(round(he_v, 1))

            # Tržní sentiment a riziko: Cboe VIX Index (Index strachu)
            if yr <= 2019:
                vix_v = 14.5 + 2.5 * np.sin(mo)
            elif yr == 2020:
                vix_v = 53.5 if mo == 3 else (35.0 if mo == 4 else 26.0)
            elif yr == 2021:
                vix_v = 18.2 + 2.0 * np.cos(mo)
            elif yr == 2022:
                vix_v = 25.8 + 3.0 * np.sin(mo)
            elif yr == 2023:
                vix_v = 16.5 - (mo / 12) * 2.5
            elif yr == 2024:
                vix_v = 15.2 + (4.5 if mo == 8 else 0.0)  # mini-spike v srpnu 2024
            elif yr == 2025:
                vix_v = 14.8
            else:
                vix_v = 14.2
            vix_series.append(round(vix_v, 1))

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

        # Fallback série pro 5 hlavních komodit (Zlato, Ropa Brent, Plyn, Měď, Stříbro)
        gold_series = []
        brent_series = []
        natgas_series = []
        copper_series = []
        silver_series = []

        for d in dates_m:
            yr, mo = d.year, d.month
            if yr == 2015: au = 1200 - (mo * 10)
            elif yr <= 2018: au = 1250 + (yr - 2016) * 40 + (mo * 3)
            elif yr == 2019: au = 1350 + (mo / 12) * 170
            elif yr == 2020: au = 1580 + (mo / 12) * 320
            elif yr == 2021: au = 1800 + (mo % 4) * 20
            elif yr == 2022: au = 1820 - (mo / 12) * 50
            elif yr == 2023: au = 1920 + (mo / 12) * 140
            elif yr == 2024: au = 2080 + (mo / 12) * 600
            elif yr == 2025: au = 2750 + (mo / 12) * 750
            else: au = 3600 + (mo / 10) * 580
            gold_series.append(round(au, 2))

            if yr == 2015: br = 55 - (mo * 1.5)
            elif yr == 2016: br = 35 + (mo * 1.5)
            elif yr in (2017, 2018): br = 54 + (yr - 2017) * 15 + (mo * 0.8)
            elif yr == 2019: br = 64 + (mo % 3) * 2
            elif yr == 2020: br = 60 if mo < 3 else (25 if mo in (3, 4) else 42 + (mo - 5) * 1.2)
            elif yr == 2021: br = 55 + (mo / 12) * 22
            elif yr == 2022: br = 85 + (mo * 3 if mo <= 6 else 105 - (mo - 6) * 4)
            elif yr == 2023: br = 82 + (mo % 4) * 2
            elif yr == 2024: br = 80 - (mo / 12) * 6
            elif yr == 2025: br = 76 + (mo / 12) * 12
            else: br = 92 + (mo / 10) * 14
            brent_series.append(round(br, 2))

            if yr in (2015, 2016): ng = 2.6 + (mo % 3) * 0.2
            elif yr in (2017, 2018, 2019): ng = 2.8 + (mo % 4) * 0.15
            elif yr == 2020: ng = 1.9 + (mo / 12) * 0.6
            elif yr == 2021: ng = 2.7 + (mo / 12) * 2.5
            elif yr == 2022: ng = 4.5 + (mo * 0.6 if mo <= 8 else 8.5 - (mo - 8) * 1.5)
            elif yr == 2023: ng = 2.8 - (mo / 12) * 0.4
            elif yr == 2024: ng = 2.1 + (mo / 12) * 0.5
            elif yr == 2025: ng = 2.6 + (mo / 12) * 0.4
            else: ng = 3.0 + (mo / 10) * 0.32
            natgas_series.append(round(ng, 3))

            if yr in (2015, 2016): cu = 2.4 + (mo * 0.03)
            elif yr in (2017, 2018, 2019): cu = 2.8 + (mo % 3) * 0.1
            elif yr == 2020: cu = 2.6 if mo < 4 else 3.1 + (mo - 4) * 0.08
            elif yr == 2021: cu = 4.1 + (mo % 3) * 0.15
            elif yr == 2022: cu = 4.4 - (mo / 12) * 0.7
            elif yr == 2023: cu = 3.8 + (mo % 3) * 0.08
            elif yr == 2024: cu = 4.0 + (mo / 12) * 0.8
            elif yr == 2025: cu = 4.8 + (mo / 12) * 0.9
            else: cu = 5.9 + (mo / 10) * 0.82
            copper_series.append(round(cu, 3))

            if yr in (2015, 2016, 2017, 2018): ag = 16.0 + (mo % 4) * 0.5
            elif yr == 2019: ag = 16.5 + (mo / 12) * 1.5
            elif yr == 2020: ag = 15.5 if mo < 4 else 21.0 + (mo - 4) * 0.5
            elif yr in (2021, 2022): ag = 23.5 - (mo / 12) * 2.0
            elif yr == 2023: ag = 23.0 + (mo % 3) * 0.8
            elif yr == 2024: ag = 24.5 + (mo / 12) * 6.5
            elif yr == 2025: ag = 32.0 + (mo / 12) * 14.0
            else: ag = 48.0 + (mo / 10) * 11.3
            silver_series.append(round(ag, 2))

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
            # Předstihové, trh práce, banky, M2 a vnější ukazatele ČR
            "cz_pmi_manufacturing": np.array(cz_pmi_series),
            "cz_confidence_composite": np.array(cz_conf_series),
            "cz_nominal_wage_yoy": np.array(cz_nom_wage_series),
            "cz_real_wage_yoy": np.array(cz_real_wage_series),
            "cz_mortgage_rate": np.array(cz_mort_rate_series),
            "cz_mortgage_volume_czk_bn": np.array(cz_mort_vol_series),
            "cz_corporate_loans_yoy": np.array(cz_corp_loans_series),
            "cz_m2_growth_yoy": np.array(cz_m2_series),
            "cz_current_account_gdp_pct": np.array(cz_ca_series),
            "cz_trade_balance_czk_bn": np.array(cz_trade_bal_series),
            "czgb_bund_spread_10y": np.round((df_czgb_m["czgb_10y"] - np.array(bund_10_series)) * 100.0, 1),
            "cz_asw_10y_spread": np.round((df_czgb_m["czgb_10y"] - df_irs_m["irs_10y"]) * 100.0, 1),
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
            # Předstihové, mzdy a dluhopisy EU
            "eu_ifo_business_climate": np.array(eu_ifo_series),
            "eu_composite_pmi": np.array(eu_pmi_series),
            "eu_negotiated_wages_yoy": np.array(eu_wages_series),
            "eu_btp_bund_spread": np.array(eu_btp_spread_series),
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
            # Předstihové a trh práce USA & Tržní sentiment
            "us_ism_manufacturing": np.array(us_ism_mfg_series),
            "us_ism_services": np.array(us_ism_srv_series),
            "us_michigan_sentiment": np.array(us_mich_series),
            "us_hourly_earnings_yoy": np.array(us_earn_series),
            "vix_index": np.array(vix_series),
            "dxy_index": df_fx_m["dxy_index"],
            "gbp_usd": df_fx_m["gbp_usd"],
            "usd_jpy": df_fx_m["usd_jpy"],
            "usd_pln": df_fx_m["usd_pln"],
            "usd_chf": df_fx_m["usd_chf"],
            # Akciové trhy
            "px_index": px_series,
            "stoxx50_index": stoxx50_series,
            "sp500_index": sp500_series,
            "nasdaq_index": nasdaq_series,
            # Komodity
            "gold_usd": gold_series,
            "oil_brent_usd": brent_series,
            "natgas_usd": natgas_series,
            "copper_usd": copper_series,
            "silver_usd": silver_series
        }
        df_monthly = pd.DataFrame(df_monthly_data)

        # ---------------------------------------------------------------------
        # E. Kvartální HDP, Dluh a Saldo (ČR, EU i USA)
        # ---------------------------------------------------------------------
        dates_q = pd.date_range("2015-01-01", "2026-10-31", freq=OFFSET_QUARTER_END)
        q_records = []

        gdp_growth_map_cz = {
            2015: [5.5, 5.6, 5.2, 5.0], 2016: [2.8, 2.5, 2.3, 2.4], 2017: [5.0, 5.2, 5.4, 5.1],
            2018: [3.5, 3.2, 3.1, 2.9], 2019: [3.2, 3.1, 2.9, 2.7], 2020: [-1.8, -10.8, -5.0, -4.4],
            2021: [-2.1, 8.5, 3.9, 4.0], 2022: [4.2, 3.4, 1.6, 0.4], 2023: [-0.4, -0.6, -0.5, 0.3],
            2024: [0.6, 0.8, 1.2, 1.6], 2025: [2.0, 2.4, 2.7, 2.6], 2026: [2.5, 2.6, 2.6, 2.6]
        }
        gdp_growth_map_eu = {
            2015: [2.1, 2.2, 2.1, 2.2], 2016: [1.9, 1.9, 1.9, 2.1], 2017: [2.6, 2.7, 2.9, 2.8],
            2018: [2.4, 2.2, 1.8, 1.7], 2019: [1.8, 1.7, 1.7, 1.4], 2020: [-3.2, -14.2, -4.1, -4.4],
            2021: [-1.2, 14.1, 4.2, 5.1], 2022: [5.4, 4.2, 2.5, 1.8], 2023: [1.2, 0.6, 0.1, 0.4],
            2024: [0.5, 0.7, 0.9, 1.1], 2025: [1.4, 1.5, 1.6, 1.7], 2026: [1.5, 1.6, 1.6, 1.6]
        }
        gdp_growth_map_us = {
            2015: [3.3, 2.7, 2.4, 2.3], 2016: [1.6, 1.4, 1.9, 2.0], 2017: [2.0, 2.3, 2.3, 2.5],
            2018: [2.8, 3.0, 3.0, 2.6], 2019: [2.2, 2.4, 2.5, 2.6], 2020: [0.3, -8.6, -2.2, -1.8],
            2021: [1.2, 12.2, 4.9, 5.4], 2022: [3.6, 1.9, 1.7, 0.7], 2023: [1.7, 2.4, 2.9, 3.1],
            2024: [2.9, 3.0, 2.8, 2.5], 2025: [2.2, 2.3, 2.4, 2.2], 2026: [2.1, 2.0, 2.0, 2.0]
        }

        fiscal_map_cz = {
            2015: (1673.0, 39.9, -62.8), 2016: (1613.0, 36.6, 61.8), 2017: (1625.0, 34.2, -6.2),
            2018: (1622.0, 32.1, 2.9), 2019: (1640.0, 30.0, -28.5), 2020: (2050.0, 37.7, -367.4),
            2021: (2466.0, 42.0, -419.7), 2022: (2895.0, 44.2, -360.4), 2023: (3111.0, 44.0, -288.5),
            2024: (3340.0, 43.8, -282.0), 2025: (3580.0, 43.5, -241.0), 2026: (3820.0, 43.6, -240.0),
        }

        quarter_idx = 0
        for d in dates_q:
            yr = d.year
            q_num = (d.month - 1) // 3 + 1

            growth_cz = gdp_growth_map_cz.get(yr, [2.0])[min(q_num - 1, len(gdp_growth_map_cz.get(yr, [2.0])) - 1)]
            growth_eu = gdp_growth_map_eu.get(yr, [1.5])[min(q_num - 1, len(gdp_growth_map_eu.get(yr, [1.5])) - 1)]
            growth_us = gdp_growth_map_us.get(yr, [2.2])[min(q_num - 1, len(gdp_growth_map_us.get(yr, [2.2])) - 1)]

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
            "px_index", "stoxx50_index", "sp500_index", "nasdaq_index", "vix_index",
            "gold_usd", "oil_brent_usd", "natgas_usd", "copper_usd", "silver_usd"
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

        # Eurostat ČR CPI & Core
        try:
            live_components["cpi_cz"] = self.fetch_eurostat_cpi()
            status_info["endpoints"]["Eurostat CPI & Jádrová (ČR)"] = "🟢 OK (Live)"
        except Exception as e:
            logger.warning("Chyba Eurostat CPI ČR: %s", e)
            status_info["endpoints"]["Eurostat CPI & Jádrová (ČR)"] = f"⚠️ Fallback ({type(e).__name__})"

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

        # ČBA Hypomonitor & Bankovní statistika ČNB ARAD (Hypotéky, Firemní úvěry, Vklady)
        try:
            df_cba = self.fetch_cba_hypomonitor_and_banking()
            if not df_cba.empty:
                live_components["cba_banking"] = df_cba
                status_info["endpoints"]["ČBA Hypomonitor & ČNB ARAD (Hypotéky, Úvěry, Vklady)"] = "🟢 OK (Live cbamonitor.cz)"
        except Exception as e:
            logger.warning("Chyba ČBA Hypomonitor: %s", e)
            status_info["endpoints"]["ČBA Hypomonitor & ČNB ARAD"] = f"⚠️ Fallback ({type(e).__name__})"

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

        # Yahoo Finance Akciové indexy (S&P 500, NASDAQ, Euro Stoxx 50) + BCPP (PX)
        try:
            live_components["stocks"] = self.fetch_stock_indices(interval="1d")
            status_info["endpoints"]["Akciové trhy (S&P 500, NASDAQ, Euro Stoxx 50, Index PX)"] = "🟢 OK (Live Denní data Yahoo/PSE)"
        except Exception as e:
            logger.warning("Chyba Akciové indexy: %s", e)
            status_info["endpoints"]["Akciové trhy"] = f"⚠️ Fallback ({type(e).__name__})"

        # Yahoo Finance Komodity (Zlato, Ropa Brent, Plyn, Měď, Stříbro)
        try:
            live_components["commodities"] = self.fetch_commodity_prices()
            status_info["endpoints"]["Komodity (Zlato, Ropa Brent, Plyn, Měď, Stříbro)"] = "🟢 OK (Live Měsíční data Yahoo)"
        except Exception as e:
            logger.warning("Chyba Komodity: %s", e)
            status_info["endpoints"]["Komodity"] = f"⚠️ Fallback ({type(e).__name__})"

        # Sloučení komponent do finální matice
        final_df = base_df.copy()

        def _merge_live_columns(df_base: pd.DataFrame, df_live: pd.DataFrame, cols: List[str], agg_func: str = "mean") -> pd.DataFrame:
            avail_cols = [c for c in cols if c in df_live.columns]
            if not avail_cols:
                return df_base
            df_sub = df_live[["date"] + avail_cols].copy()
            if frequency == "Q":
                df_sub = df_sub.set_index("date").resample(OFFSET_QUARTER_END).agg(agg_func).reset_index()
            merged = pd.merge(df_base, df_sub, on="date", how="left", suffixes=("", "_live"))
            for c in avail_cols:
                live_c = f"{c}_live"
                if live_c in merged.columns:
                    valid_live = merged.loc[merged[live_c].notna(), "date"]
                    if not valid_live.empty:
                        max_live_dt = valid_live.max()
                        # Pro neuzavřené měsíce po posledním živém datu nepřebíráme fallback, ale ffillujeme poslední živou hodnotu
                        merged.loc[merged["date"] > max_live_dt, c] = np.nan
                    merged[c] = merged[live_c].combine_first(merged[c])
                    merged = merged.drop(columns=[live_c])
                merged[c] = merged[c].ffill().bfill()
            return merged

        if "cpi_cz" in live_components:
            final_df = _merge_live_columns(final_df, live_components["cpi_cz"], ["cpi_yoy", "cpi_core_yoy"], agg_func="mean")

        if "cpi_ea" in live_components:
            final_df = _merge_live_columns(final_df, live_components["cpi_ea"], ["eu_cpi_yoy", "eu_core_cpi_yoy"], agg_func="mean")

        if "unemployment" in live_components:
            final_df = _merge_live_columns(final_df, live_components["unemployment"], ["unemployment_rate", "eu_unemployment_rate"], agg_func="mean")

        if "gdp" in live_components:
            df_g = live_components["gdp"].sort_values("date")
            gdp_cols = [c for c in ["gdp_growth_real", "eu_gdp_growth_real"] if c in df_g.columns]
            if gdp_cols:
                if frequency == "M":
                    df_g_m = pd.merge_asof(
                        final_df[["date"]].sort_values("date"),
                        df_g[["date"] + gdp_cols],
                        on="date",
                        direction="backward"
                    )
                    final_df = _merge_live_columns(final_df, df_g_m, gdp_cols, agg_func="mean")
                else:
                    final_df = _merge_live_columns(final_df, df_g, gdp_cols, agg_func="mean")

        if "debt" in live_components:
            df_d = live_components["debt"].sort_values("date")
            debt_cols = [c for c in ["public_debt_gdp_pct", "eu_public_debt_gdp_pct"] if c in df_d.columns]
            if debt_cols:
                if frequency == "M":
                    df_d_m = pd.merge_asof(
                        final_df[["date"]].sort_values("date"),
                        df_d[["date"] + debt_cols],
                        on="date",
                        direction="backward"
                    )
                    final_df = _merge_live_columns(final_df, df_d_m, debt_cols, agg_func="mean")
                else:
                    final_df = _merge_live_columns(final_df, df_d, debt_cols, agg_func="mean")

        if "cba_banking" in live_components:
            final_df = _merge_live_columns(
                final_df,
                live_components["cba_banking"],
                ["cz_mortgage_rate", "cz_mortgage_volume_czk_bn", "cz_corporate_loans_yoy", "cz_m2_growth_yoy"],
                agg_func="last"
            )

        if "rates" in live_components:
            df_r = live_components["rates"]
            df_r_agg = df_r.set_index("date").resample(OFFSET_MONTH_END if frequency == "M" else OFFSET_QUARTER_END).last().reset_index()
            final_df = _merge_live_columns(final_df, df_r_agg, ["repo_rate", "discount_rate", "lombard_rate"], agg_func="last")

        if "pribor" in live_components:
            df_p = live_components["pribor"]
            df_p_agg = df_p.set_index("date").resample(OFFSET_MONTH_END if frequency == "M" else OFFSET_QUARTER_END).mean().reset_index()
            final_df = _merge_live_columns(final_df, df_p_agg, ["pribor_1m", "pribor_3m", "pribor_6m"], agg_func="mean")

        # Agregace denních devizových kurzů
        fx_cols_to_merge = [c for c in df_daily_fx.columns if c != "date"]
        df_fx_agg = df_daily_fx.set_index("date").resample(OFFSET_MONTH_END if frequency == "M" else OFFSET_QUARTER_END).last().reset_index()
        final_df = pd.merge(final_df.drop(columns=fx_cols_to_merge, errors="ignore"), df_fx_agg, on="date", how="left")
        for c in fx_cols_to_merge:
            final_df[c] = final_df[c].ffill().bfill()

        if "bond_10y" in live_components:
            final_df = _merge_live_columns(final_df, live_components["bond_10y"], ["czgb_10y", "bund_10y"], agg_func="mean")

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
            # 1. Sloučení denních akciových indexů do společného denního datasetu df_daily_fx
            df_daily_fx = pd.merge(df_daily_fx, df_st, on="date", how="outer").sort_values("date").reset_index(drop=True)
            df_daily_fx = df_daily_fx.ffill().bfill()

            # 2. Agregace denních akciových indexů do měsíčního final_df
            df_st_agg = df_st.set_index("date").resample(OFFSET_MONTH_END if frequency == "M" else OFFSET_QUARTER_END).last().reset_index()
            final_df = pd.merge(final_df, df_st_agg, on="date", how="left", suffixes=("", "_live"))
            for col in st_cols:
                live_c = f"{col}_live"
                if live_c in final_df.columns:
                    final_df[col] = final_df[live_c].combine_first(final_df[col])
                    final_df = final_df.drop(columns=[live_c])
                final_df[col] = final_df[col].ffill().bfill()

        if "commodities" in live_components:
            df_com = live_components["commodities"]
            com_cols = [c for c in df_com.columns if c != "date"]
            df_com_agg = df_com.set_index("date").resample(OFFSET_MONTH_END if frequency == "M" else OFFSET_QUARTER_END).last().reset_index()
            final_df = pd.merge(final_df, df_com_agg, on="date", how="left", suffixes=("", "_live"))
            for col in com_cols:
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
            status_info["status_badge"] = "🟢 Živá data (ČNB, ČBA Hypomonitor, Eurostat, US Treasury, Yahoo/PSE & Komodity)"
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
        _cache_bust: str = "v2026_10_16_cba_hypomonitor_live_news_v1"
    ) -> Tuple[pd.DataFrame, Dict[str, Any], pd.DataFrame]:
        loader = DataLoader()
        return loader.load_macro_data(
            frequency=frequency,
            fred_api_key=fred_api_key,
            force_fallback=force_fallback
        )

    @st.cache_data(ttl=1800, show_spinner=False)
    def get_cached_cz_topic_news(
        _cache_bust: str = "v2026_10_16_live_cz_news_v1"
    ) -> Dict[str, Dict[str, Any]]:
        loader = DataLoader()
        return loader.fetch_live_cz_topic_news()

except ImportError:
    def get_cached_macro_data(
        frequency: str = "M",
        fred_api_key: Optional[str] = None,
        force_fallback: bool = False,
        _cache_bust: str = "v2026_10_16_cba_hypomonitor_live_news_v1"
    ) -> Tuple[pd.DataFrame, Dict[str, Any], pd.DataFrame]:
        loader = DataLoader()
        return loader.load_macro_data(
            frequency=frequency,
            fred_api_key=fred_api_key,
            force_fallback=force_fallback
        )

    def get_cached_cz_topic_news(
        _cache_bust: str = "v2026_10_16_live_cz_news_v1"
    ) -> Dict[str, Dict[str, Any]]:
        loader = DataLoader()
        return loader.fetch_live_cz_topic_news()

