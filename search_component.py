"""
search_component.py
===================
Modul pro robustní vyhledávání makroekonomických indikátorů s interaktivním
našeptávačem (Command Palette / Search Drawer).

Funkce a vlastnosti:
- Umístění v levém postranním panelu (sidebar) pod hlavní navigací.
- Vyhledávací pole s ikonou lupy, placeholderem a klávesovou zkratkou Ctrl + K / Cmd + K.
- Interaktivní drawer s okamžitým filtrováním od 1. zadaného znaku.
- Rychlé fuzzy vyhledávání bez ohledu na velikost písmen a českou/anglickou diakritiku.
- Vyhledávání napříč názvy ukazatelů, kategoriemi, regiony a odbornými synonymy (CPI, repo, Bund, PRIBOR...).
- Vizuální seskupení výsledků podle regionu (ČR / EU / USA).
- Zobrazení tučného názvu s dynamickým zvýrazněním shody, barevného badge regionu a nadřazené kategorie.
- Plná klávesnicová navigace (šipky Nahoru / Dolů, Enter pro potvrzení, Escape pro zavření).
- Přejití přímo na cílovou ekonomiku, hlavní záložku, podzáložku a plynulé odrolování ke grafu/kartě.
- Přehledný stav při nenalezení: „Žádný indikátor nebyl nalezen.“
"""

from __future__ import annotations

import json
from typing import Dict, Any, Optional
import streamlit as st
from data_loader import INDICATORS, IndicatorInfo


# =============================================================================
# 1. MAPOVÁNÍ NAVIGACE A CÍLŮ PRO VŠECH 101 INDIKÁTORŮ
# =============================================================================

# Struktura: code -> (region, main_tab_idx, sub_tab_id, anchor_id, extra_aliases)
# main_tab_idx:
#   0 = 💳 Finanční trhy & Měna
#   1 = 🏛️ Reálná ekonomika & Práce
#   2 = 📈 Trhy
#   3 = 🌐 Veřejné finance & Svět
INDICATOR_NAVIGATION_REGISTRY: Dict[str, Dict[str, Any]] = {
    # -------------------------------------------------------------------------
    # 🇨🇿 ČESKÁ REPUBLIKA (CZ)
    # -------------------------------------------------------------------------
    "repo_rate": {
        "region": "CZ", "main_tab": "💳 Finanční trhy & Měna", "sub_tab_id": "rates",
        "sub_tab_label": "Sazby (ČNB)", "anchor": "chart_cz_rates",
        "aliases": ["repo", "2t repo", "cnb", "čnb", "sazby", "urok", "menova politika", "zakladni sazba"]
    },
    "discount_rate": {
        "region": "CZ", "main_tab": "💳 Finanční trhy & Měna", "sub_tab_id": "rates",
        "sub_tab_label": "Sazby (ČNB)", "anchor": "chart_cz_rates",
        "aliases": ["diskont", "diskontni", "vklady bank", "cnb", "sazba"]
    },
    "lombard_rate": {
        "region": "CZ", "main_tab": "💳 Finanční trhy & Měna", "sub_tab_id": "rates",
        "sub_tab_label": "Sazby (ČNB)", "anchor": "chart_cz_rates",
        "aliases": ["lombard", "lombardni", "likvidita", "zapujcky", "cnb", "sazba"]
    },
    "pribor_1m": {
        "region": "CZ", "main_tab": "💳 Finanční trhy & Měna", "sub_tab_id": "rates",
        "sub_tab_label": "Sazby (ČNB)", "anchor": "chart_cz_rates",
        "aliases": ["pribor", "pribor 1m", "mezibankovni sazba", "fixace", "peněžní trh"]
    },
    "pribor_3m": {
        "region": "CZ", "main_tab": "💳 Finanční trhy & Měna", "sub_tab_id": "rates",
        "sub_tab_label": "Sazby (ČNB)", "anchor": "chart_cz_rates",
        "aliases": ["pribor", "pribor 3m", "3m pribor", "mezibankovni trh", "uvery", "hypoteky benchmark"]
    },
    "pribor_6m": {
        "region": "CZ", "main_tab": "💳 Finanční trhy & Měna", "sub_tab_id": "rates",
        "sub_tab_label": "Sazby (ČNB)", "anchor": "chart_cz_rates",
        "aliases": ["pribor", "pribor 6m", "6m pribor", "mezibankovni trh", "fixace"]
    },
    "czgb_10y": {
        "region": "CZ", "main_tab": "💳 Finanční trhy & Měna", "sub_tab_id": "curve",
        "sub_tab_label": "Výnosová křivka & Spready (CZ)", "anchor": "chart_cz_yield_curve",
        "aliases": ["czgb", "10y czgb", "státní dluhopis", "český dluhopis", "vynos", "benchmark", "křivka", "dluhopisy"]
    },
    "czgb_2y": {
        "region": "CZ", "main_tab": "💳 Finanční trhy & Měna", "sub_tab_id": "curve",
        "sub_tab_label": "Výnosová křivka & Spready (CZ)", "anchor": "chart_cz_yield_curve",
        "aliases": ["czgb 2y", "2y czgb", "kratky dluhopis", "statni dluhopis", "vynos", "dluhopisy"]
    },
    "czgb_5y": {
        "region": "CZ", "main_tab": "💳 Finanční trhy & Měna", "sub_tab_id": "curve",
        "sub_tab_label": "Výnosová křivka & Spready (CZ)", "anchor": "chart_cz_yield_curve",
        "aliases": ["czgb 5y", "5y czgb", "strednedoby dluhopis", "statni dluhopis", "vynos", "dluhopisy"]
    },
    "czgb_15y": {
        "region": "CZ", "main_tab": "💳 Finanční trhy & Měna", "sub_tab_id": "curve",
        "sub_tab_label": "Výnosová křivka & Spready (CZ)", "anchor": "chart_cz_yield_curve",
        "aliases": ["czgb 15y", "15y czgb", "dlouhy dluhopis", "statni dluhopis", "vynos", "dluhopisy"]
    },
    "irs_10y": {
        "region": "CZ", "main_tab": "💳 Finanční trhy & Měna", "sub_tab_id": "curve",
        "sub_tab_label": "Výnosová křivka & Spready (CZ)", "anchor": "chart_cz_yield_curve",
        "aliases": ["irs", "irs 10y", "interest rate swap", "urokovy swap", "derivaty", "zajisteni"]
    },
    "irs_5y": {
        "region": "CZ", "main_tab": "💳 Finanční trhy & Měna", "sub_tab_id": "curve",
        "sub_tab_label": "Výnosová křivka & Spready (CZ)", "anchor": "chart_cz_yield_curve",
        "aliases": ["irs 5y", "5y irs", "interest rate swap", "urokovy swap", "derivaty"]
    },
    "czgb_spread_10y_2y": {
        "region": "CZ", "main_tab": "💳 Finanční trhy & Měna", "sub_tab_id": "curve",
        "sub_tab_label": "Výnosová křivka & Spready (CZ)", "anchor": "chart_cz_yield_curve",
        "aliases": ["sklon krivky", "spread", "10y-2y", "inverze krivky", "recese", "spready"]
    },
    "czgb_bund_spread_10y": {
        "region": "CZ", "main_tab": "💳 Finanční trhy & Měna", "sub_tab_id": "curve",
        "sub_tab_label": "Výnosová křivka & Spready (CZ)", "anchor": "chart_cz_credit_spreads",
        "aliases": ["bund", "spread", "spready", "kreditni spread", "czgb vs bund", "rizikova premie"]
    },
    "cz_asw_10y_spread": {
        "region": "CZ", "main_tab": "💳 Finanční trhy & Měna", "sub_tab_id": "curve",
        "sub_tab_label": "Výnosová křivka & Spready (CZ)", "anchor": "chart_cz_credit_spreads",
        "aliases": ["asw", "asset swap", "asw spread", "spread", "spready", "swap spread"]
    },
    "eur_czk": {
        "region": "CZ", "main_tab": "💳 Finanční trhy & Měna", "sub_tab_id": "fx",
        "sub_tab_label": "Měnové kurzy (FX)", "anchor": "chart_dynamic_fx",
        "aliases": ["euro", "koruna", "eur czk", "fx", "devizovy kurz", "mena", "smenny kurz"]
    },
    "usd_czk": {
        "region": "CZ", "main_tab": "💳 Finanční trhy & Měna", "sub_tab_id": "fx",
        "sub_tab_label": "Měnové kurzy (FX)", "anchor": "chart_dynamic_fx",
        "aliases": ["dolar", "dolar koruna", "usd czk", "fx", "devizovy kurz", "mena"]
    },
    "pln_czk": {
        "region": "CZ", "main_tab": "💳 Finanční trhy & Měna", "sub_tab_id": "fx",
        "sub_tab_label": "Měnové kurzy (FX)", "anchor": "chart_dynamic_fx",
        "aliases": ["zloty", "polsky zloty", "pln czk", "fx", "kurz", "mena"]
    },
    "gbp_czk": {
        "region": "CZ", "main_tab": "💳 Finanční trhy & Měna", "sub_tab_id": "fx",
        "sub_tab_label": "Měnové kurzy (FX)", "anchor": "chart_dynamic_fx",
        "aliases": ["libra", "britska libra", "gbp czk", "fx", "kurz", "mena"]
    },
    "cz_mortgage_rate": {
        "region": "CZ", "main_tab": "💳 Finanční trhy & Měna", "sub_tab_id": "banking",
        "sub_tab_label": "Bankovní sektor & Úvěry (ČR)", "anchor": "chart_cz_banking_loans",
        "aliases": ["hypoteka", "hypoteky", "hypotecni sazba", "cba hypomonitor", "uvery na bydleni", "banky"]
    },
    "cz_corporate_loans_yoy": {
        "region": "CZ", "main_tab": "💳 Finanční trhy & Měna", "sub_tab_id": "banking",
        "sub_tab_label": "Bankovní sektor & Úvěry (ČR)", "anchor": "chart_cz_banking_loans",
        "aliases": ["korporatni uvery", "firemni uvery", "podnikatelske pujcky", "banky", "uverovani"]
    },
    "cz_m2_growth_yoy": {
        "region": "CZ", "main_tab": "💳 Finanční trhy & Měna", "sub_tab_id": "banking",
        "sub_tab_label": "Bankovní sektor & Úvěry (ČR)", "anchor": "chart_cz_banking_loans",
        "aliases": ["m2", "peněžní zasoba", "menovy agregat", "likvidita", "inflacni tlaky"]
    },
    "cz_pmi_manufacturing": {
        "region": "CZ", "main_tab": "🏛️ Reálná ekonomika & Práce", "sub_tab_id": "leading",
        "sub_tab_label": "Předstihové ukazatele & Sentiment", "anchor": "chart_cz_leading_indicators",
        "aliases": ["pmi", "prumysl pmi", "predstihove ukazatele", "s&p global", "vyroba", "nakupni manazeri"]
    },
    "cz_confidence_composite": {
        "region": "CZ", "main_tab": "🏛️ Reálná ekonomika & Práce", "sub_tab_id": "leading",
        "sub_tab_label": "Předstihové ukazatele & Sentiment", "anchor": "chart_cz_leading_indicators",
        "aliases": ["duvera", "konjunkturni pruzkum", "sentiment csu", "spotrebitele", "podnikatele", "nalada"]
    },
    "gdp_growth_real": {
        "region": "CZ", "main_tab": "🏛️ Reálná ekonomika & Práce", "sub_tab_id": "gdp",
        "sub_tab_label": "HDP", "anchor": "chart_cz_gdp",
        "aliases": ["hdp", "gdp", "rust hdp", "ekonomicky rust", "realne hdp", "csu"]
    },
    "gdp_nominal_czk_bn": {
        "region": "CZ", "main_tab": "🏛️ Reálná ekonomika & Práce", "sub_tab_id": "gdp",
        "sub_tab_label": "HDP", "anchor": "chart_cz_gdp",
        "aliases": ["nominalni hdp", "velikost ekonomiky", "hdp v miliardach", "hdp cr"]
    },
    "cpi_yoy": {
        "region": "CZ", "main_tab": "🏛️ Reálná ekonomika & Práce", "sub_tab_id": "inflation",
        "sub_tab_label": "Inflace (CPI)", "anchor": "chart_cz_inflation",
        "aliases": ["cpi", "inflace", "zdrazovani", "cenova hladina", "spotrebitelske ceny", "csu"]
    },
    "cpi_core_yoy": {
        "region": "CZ", "main_tab": "🏛️ Reálná ekonomika & Práce", "sub_tab_id": "inflation",
        "sub_tab_label": "Inflace (CPI)", "anchor": "chart_cz_inflation",
        "aliases": ["jadrova inflace", "core cpi", "core inflace", "menove politicka inflace", "csu"]
    },
    "retail_sales_yoy": {
        "region": "CZ", "main_tab": "🏛️ Reálná ekonomika & Práce", "sub_tab_id": "activity",
        "sub_tab_label": "Průmysl a spotřeba", "anchor": "chart_activity_panel",
        "aliases": ["maloobchod", "maloobchodni trzby", "spotreba", "domacnosti", "utraty"]
    },
    "industrial_prod_yoy": {
        "region": "CZ", "main_tab": "🏛️ Reálná ekonomika & Práce", "sub_tab_id": "activity",
        "sub_tab_label": "Průmysl a spotřeba", "anchor": "chart_activity_panel",
        "aliases": ["prumysl", "prumyslova produkce", "tovarny", "vyroba", "automotive"]
    },
    "unemployment_rate": {
        "region": "CZ", "main_tab": "🏛️ Reálná ekonomika & Práce", "sub_tab_id": "labor",
        "sub_tab_label": "Trh práce & Mzdy", "anchor": "chart_cz_unemployment",
        "aliases": ["nezamestnanost", "mira nezamestnanosti", "trh prace", "urad prace", "mpsv"]
    },
    "cz_nominal_wage_yoy": {
        "region": "CZ", "main_tab": "🏛️ Reálná ekonomika & Práce", "sub_tab_id": "labor",
        "sub_tab_label": "Trh práce & Mzdy", "anchor": "chart_cz_wages",
        "aliases": ["mzda", "mzdy", "nominalni mzda", "prumerna hruba mzda", "platy", "prijmy"]
    },
    "cz_real_wage_yoy": {
        "region": "CZ", "main_tab": "🏛️ Reálná ekonomika & Práce", "sub_tab_id": "labor",
        "sub_tab_label": "Trh práce & Mzdy", "anchor": "chart_cz_wages",
        "aliases": ["realna mzda", "kupni sila", "rust mezd po odecteni inflace", "platy"]
    },
    "px_index": {
        "region": "CZ", "main_tab": "📈 Trhy", "sub_tab_id": "px",
        "sub_tab_label": "🇨🇿 Index PX (Pražská burza)", "anchor": "chart_single_px",
        "aliases": ["px", "bcpp", "prazska burza", "ceske akcie", "cez", "erste", "komercni banka"]
    },
    "public_debt_czk_bn": {
        "region": "CZ", "main_tab": "🌐 Veřejné finance & Svět", "sub_tab_id": "debt",
        "sub_tab_label": "Veřejný dluh", "anchor": "chart_cz_debt_pct",
        "aliases": ["statni dluh", "verejny dluh", "dluh cr", "mf cr", "zadluzeni"]
    },
    "public_debt_gdp_pct": {
        "region": "CZ", "main_tab": "🌐 Veřejné finance & Svět", "sub_tab_id": "debt",
        "sub_tab_label": "Veřejný dluh", "anchor": "chart_cz_debt_pct",
        "aliases": ["dluh k hdp", "maastricht", "podil dluhu", "fiskalni pravidla"]
    },
    "budget_deficit_czk_bn": {
        "region": "CZ", "main_tab": "🌐 Veřejné finance & Svět", "sub_tab_id": "debt",
        "sub_tab_label": "Veřejný dluh", "anchor": "chart_cz_deficit",
        "aliases": ["schodek", "deficit", "statni rozpocet", "saldo rozpoctu", "pokladni plneni"]
    },
    "cz_current_account_gdp_pct": {
        "region": "CZ", "main_tab": "🌐 Veřejné finance & Svět", "sub_tab_id": "external",
        "sub_tab_label": "Vnější rovnováha & Zahraniční obchod (ČR)", "anchor": "chart_cz_external_balance",
        "aliases": ["bezny ucet", "platebni bilance", "vnejsi rovnovaha", "export import"]
    },
    "cz_trade_balance_czk_bn": {
        "region": "CZ", "main_tab": "🌐 Veřejné finance & Svět", "sub_tab_id": "external",
        "sub_tab_label": "Vnější rovnováha & Zahraniční obchod (ČR)", "anchor": "chart_cz_external_balance",
        "aliases": ["zahranicni obchod", "obchodni bilance", "export", "import", "csu"]
    },

    # -------------------------------------------------------------------------
    # 🇪🇺 EVROPSKÁ UNIE / EUROZÓNA (EU)
    # -------------------------------------------------------------------------
    "ecb_deposit_rate": {
        "region": "EU", "main_tab": "💳 Finanční trhy & Měna", "sub_tab_id": "rates",
        "sub_tab_label": "Sazby (ECB)", "anchor": "chart_eu_rates",
        "aliases": ["ecb", "depozitni sazba", "dfr", "deposit facility", "sazby eu", "frankfurt"]
    },
    "ecb_refi_rate": {
        "region": "EU", "main_tab": "💳 Finanční trhy & Měna", "sub_tab_id": "rates",
        "sub_tab_label": "Sazby (ECB)", "anchor": "chart_eu_rates",
        "aliases": ["refinancni sazba", "mro", "main refinancing", "ecb", "sazby eurozona"]
    },
    "ecb_lending_rate": {
        "region": "EU", "main_tab": "💳 Finanční trhy & Měna", "sub_tab_id": "rates",
        "sub_tab_label": "Sazby (ECB)", "anchor": "chart_eu_rates",
        "aliases": ["mezni zapujcni sazba", "mlf", "marginal lending", "ecb", "koridor"]
    },
    "euribor_3m": {
        "region": "EU", "main_tab": "💳 Finanční trhy & Měna", "sub_tab_id": "rates",
        "sub_tab_label": "Sazby (ECB)", "anchor": "chart_eu_rates",
        "aliases": ["euribor", "euribor 3m", "3m euribor", "mezibankovni euro", "benchmark"]
    },
    "estr_rate": {
        "region": "EU", "main_tab": "💳 Finanční trhy & Měna", "sub_tab_id": "rates",
        "sub_tab_label": "Sazby (ECB)", "anchor": "chart_eu_rates",
        "aliases": ["estr", "euro short term rate", "overnight sazba", "bezrizikova sazba eu"]
    },
    "bund_10y": {
        "region": "EU", "main_tab": "💳 Finanční trhy & Měna", "sub_tab_id": "curve",
        "sub_tab_label": "Výnosová křivka & Spready (Bund)", "anchor": "chart_eu_yield_curve",
        "aliases": ["bund", "10y bund", "nemecke dluhopisy", "nemecko benchmark", "vynos bundu", "dluhopisy eu"]
    },
    "bund_2y": {
        "region": "EU", "main_tab": "💳 Finanční trhy & Měna", "sub_tab_id": "curve",
        "sub_tab_label": "Výnosová křivka & Spready (Bund)", "anchor": "chart_eu_yield_curve",
        "aliases": ["bund 2y", "schatz", "2y bund", "nemecky statni dluhopis", "kratky bund"]
    },
    "bund_5y": {
        "region": "EU", "main_tab": "💳 Finanční trhy & Měna", "sub_tab_id": "curve",
        "sub_tab_label": "Výnosová křivka & Spready (Bund)", "anchor": "chart_eu_yield_curve",
        "aliases": ["bund 5y", "bobl", "5y bund", "strednedoby bund", "nemecko dluhopis"]
    },
    "bund_30y": {
        "region": "EU", "main_tab": "💳 Finanční trhy & Měna", "sub_tab_id": "curve",
        "sub_tab_label": "Výnosová křivka & Spready (Bund)", "anchor": "chart_eu_yield_curve",
        "aliases": ["bund 30y", "30y bund", "ultra dlouhy bund", "nemecko dluhopis"]
    },
    "bund_spread_10y_2y": {
        "region": "EU", "main_tab": "💳 Finanční trhy & Měna", "sub_tab_id": "curve",
        "sub_tab_label": "Výnosová křivka & Spready (Bund)", "anchor": "chart_eu_yield_curve",
        "aliases": ["sklon nemecke krivky", "bund spread", "spread", "spready", "10y-2y bund"]
    },
    "eu_btp_bund_spread": {
        "region": "EU", "main_tab": "💳 Finanční trhy & Měna", "sub_tab_id": "curve",
        "sub_tab_label": "Výnosová křivka & Spready (Bund)", "anchor": "chart_eu_credit_spreads",
        "aliases": ["btp", "btp bund", "italie spread", "rizikovy spread", "periferie", "spread", "spready"]
    },
    "eur_pln": {
        "region": "EU", "main_tab": "💳 Finanční trhy & Měna", "sub_tab_id": "fx",
        "sub_tab_label": "Měnové kurzy (FX)", "anchor": "chart_dynamic_fx",
        "aliases": ["eur pln", "euro zloty", "fx", "kurz", "mena"]
    },
    "eur_gbp": {
        "region": "EU", "main_tab": "💳 Finanční trhy & Měna", "sub_tab_id": "fx",
        "sub_tab_label": "Měnové kurzy (FX)", "anchor": "chart_dynamic_fx",
        "aliases": ["eur gbp", "euro libra", "fx", "kurz", "mena"]
    },
    "eu_ifo_business_climate": {
        "region": "EU", "main_tab": "🏛️ Reálná ekonomika & Práce", "sub_tab_id": "leading",
        "sub_tab_label": "Předstihové ukazatele & Sentiment", "anchor": "chart_eu_leading_indicators",
        "aliases": ["ifo", "ifo index", "nemecky ifo", "podnikatelske klima", "sentiment", "mnichov"]
    },
    "eu_composite_pmi": {
        "region": "EU", "main_tab": "🏛️ Reálná ekonomika & Práce", "sub_tab_id": "leading",
        "sub_tab_label": "Předstihové ukazatele & Sentiment", "anchor": "chart_eu_leading_indicators",
        "aliases": ["composite pmi", "pmi eurozona", "hcoo pmi", "predstihove ukazatele eu", "vyroba sluzby"]
    },
    "eu_gdp_growth_real": {
        "region": "EU", "main_tab": "🏛️ Reálná ekonomika & Práce", "sub_tab_id": "gdp",
        "sub_tab_label": "HDP", "anchor": "chart_eu_gdp",
        "aliases": ["hdp eurozona", "eu gdp", "rust eurozony", "eurostat", "ekonomika eu"]
    },
    "eu_gdp_nominal_eur_bn": {
        "region": "EU", "main_tab": "🏛️ Reálná ekonomika & Práce", "sub_tab_id": "gdp",
        "sub_tab_label": "HDP", "anchor": "chart_eu_gdp",
        "aliases": ["nominalni hdp eu", "velikost eurozony", "miliardy eur hdp"]
    },
    "eu_cpi_yoy": {
        "region": "EU", "main_tab": "🏛️ Reálná ekonomika & Práce", "sub_tab_id": "inflation",
        "sub_tab_label": "Inflace (HICP)", "anchor": "chart_eu_inflation",
        "aliases": ["hicp", "inflace eu", "cpi eu", "eurostat", "zdrazovani v eurozone"]
    },
    "eu_core_cpi_yoy": {
        "region": "EU", "main_tab": "🏛️ Reálná ekonomika & Práce", "sub_tab_id": "inflation",
        "sub_tab_label": "Inflace (HICP)", "anchor": "chart_eu_inflation",
        "aliases": ["jadrova inflace eu", "core hicp", "core cpi eurozona", "bazicka inflace"]
    },
    "eu_retail_sales_yoy": {
        "region": "EU", "main_tab": "🏛️ Reálná ekonomika & Práce", "sub_tab_id": "activity",
        "sub_tab_label": "Průmysl a spotřeba", "anchor": "chart_activity_panel",
        "aliases": ["maloobchod eu", "spotreba eurozona", "retail sales eurostat"]
    },
    "eu_industrial_prod_yoy": {
        "region": "EU", "main_tab": "🏛️ Reálná ekonomika & Práce", "sub_tab_id": "activity",
        "sub_tab_label": "Průmysl a spotřeba", "anchor": "chart_activity_panel",
        "aliases": ["prumysl eu", "prumyslova produkce eurostat", "vyroba eurozona"]
    },
    "eu_unemployment_rate": {
        "region": "EU", "main_tab": "🏛️ Reálná ekonomika & Práce", "sub_tab_id": "labor",
        "sub_tab_label": "Trh práce & Mzdy", "anchor": "chart_eu_unemployment",
        "aliases": ["nezamestnanost eu", "mira nezamestnanosti eurozona", "eurostat", "trh prace"]
    },
    "eu_negotiated_wages_yoy": {
        "region": "EU", "main_tab": "🏛️ Reálná ekonomika & Práce", "sub_tab_id": "labor",
        "sub_tab_label": "Trh práce & Mzdy", "anchor": "chart_eu_wages",
        "aliases": ["sjednane mzdy", "wages ecb", "mzdova spirala", "rust mezd v eurozone"]
    },
    "stoxx50_index": {
        "region": "EU", "main_tab": "📈 Trhy", "sub_tab_id": "stoxx",
        "sub_tab_label": "🇪🇺 Euro Stoxx 50", "anchor": "chart_single_stoxx",
        "aliases": ["stoxx", "euro stoxx 50", "sx5e", "evropske akcie", "blue chips"]
    },
    "eu_public_debt_gdp_pct": {
        "region": "EU", "main_tab": "🌐 Veřejné finance & Svět", "sub_tab_id": "debt",
        "sub_tab_label": "Veřejný dluh", "anchor": "chart_eu_debt_pct",
        "aliases": ["dluh eurozony", "verejny dluh k hdp eu", "maastrichtsky dluh"]
    },
    "eu_public_debt_eur_bn": {
        "region": "EU", "main_tab": "🌐 Veřejné finance & Svět", "sub_tab_id": "debt",
        "sub_tab_label": "Veřejný dluh", "anchor": "chart_eu_debt_pct",
        "aliases": ["nominalni dluh eu", "dluh v miliardach eur", "vladni dluh eurostat"]
    },
    "eu_budget_deficit_eur_bn": {
        "region": "EU", "main_tab": "🌐 Veřejné finance & Svět", "sub_tab_id": "debt",
        "sub_tab_label": "Veřejný dluh", "anchor": "chart_eu_deficit",
        "aliases": ["schodek eu", "deficit eurozony", "saldo vlady eurostat"]
    },

    # -------------------------------------------------------------------------
    # 🇺🇸 SPOJENÉ STÁTY AMERICKÉ (US)
    # -------------------------------------------------------------------------
    "fed_funds_upper": {
        "region": "US", "main_tab": "💳 Finanční trhy & Měna", "sub_tab_id": "rates",
        "sub_tab_label": "Sazby (Fed)", "anchor": "chart_us_rates",
        "aliases": ["fed", "fed funds", "horni mez", "fomc", "americke sazby", "powell"]
    },
    "fed_funds_lower": {
        "region": "US", "main_tab": "💳 Finanční trhy & Měna", "sub_tab_id": "rates",
        "sub_tab_label": "Sazby (Fed)", "anchor": "chart_us_rates",
        "aliases": ["fed funds dolni mez", "fed floor", "fomc koridor", "fed sazby"]
    },
    "fed_effective_rate": {
        "region": "US", "main_tab": "💳 Finanční trhy & Měna", "sub_tab_id": "rates",
        "sub_tab_label": "Sazby (Fed)", "anchor": "chart_us_rates",
        "aliases": ["effr", "efektivni fed funds", "ny fed", "skutecna sazba"]
    },
    "sofr_rate": {
        "region": "US", "main_tab": "💳 Finanční trhy & Měna", "sub_tab_id": "rates",
        "sub_tab_label": "Sazby (Fed)", "anchor": "chart_us_rates",
        "aliases": ["sofr", "secured overnight", "repo trh usa", "libor nahrada"]
    },
    "us_1m": {
        "region": "US", "main_tab": "💳 Finanční trhy & Měna", "sub_tab_id": "rates",
        "sub_tab_label": "Sazby (Fed)", "anchor": "chart_us_rates",
        "aliases": ["t-bill 1m", "treasury bill 1m", "kratkodoby vynos usa"]
    },
    "us_3m": {
        "region": "US", "main_tab": "💳 Finanční trhy & Měna", "sub_tab_id": "rates",
        "sub_tab_label": "Sazby (Fed)", "anchor": "chart_us_rates",
        "aliases": ["t-bill 3m", "3m treasury bill", "peněžní trh usa"]
    },
    "us_10y": {
        "region": "US", "main_tab": "💳 Finanční trhy & Měna", "sub_tab_id": "curve",
        "sub_tab_label": "Výnosová křivka & Spready (US)", "anchor": "chart_us_yield_curve",
        "aliases": ["10y treasury", "t-note 10y", "americky benchmark", "vynos 10y usa", "dluhopisy usa"]
    },
    "us_2y": {
        "region": "US", "main_tab": "💳 Finanční trhy & Měna", "sub_tab_id": "curve",
        "sub_tab_label": "Výnosová křivka & Spready (US)", "anchor": "chart_us_yield_curve",
        "aliases": ["2y treasury", "t-note 2y", "kratky dluhopis usa", "ocekavani fedu"]
    },
    "us_5y": {
        "region": "US", "main_tab": "💳 Finanční trhy & Měna", "sub_tab_id": "curve",
        "sub_tab_label": "Výnosová křivka & Spready (US)", "anchor": "chart_us_yield_curve",
        "aliases": ["5y treasury", "t-note 5y", "strednedoby dluhopis usa"]
    },
    "us_30y": {
        "region": "US", "main_tab": "💳 Finanční trhy & Měna", "sub_tab_id": "curve",
        "sub_tab_label": "Výnosová křivka & Spready (US)", "anchor": "chart_us_yield_curve",
        "aliases": ["30y treasury", "t-bond 30y", "dlouhy dluhopis usa"]
    },
    "us_spread_10y_2y": {
        "region": "US", "main_tab": "💳 Finanční trhy & Měna", "sub_tab_id": "curve",
        "sub_tab_label": "Výnosová křivka & Spready (US)", "anchor": "chart_us_yield_curve",
        "aliases": ["sklon us krivky", "inverze us krivky", "10y-2y spread", "spread", "spready", "indikator recese"]
    },
    "dxy_index": {
        "region": "US", "main_tab": "💳 Finanční trhy & Měna", "sub_tab_id": "fx",
        "sub_tab_label": "Měnové kurzy (FX)", "anchor": "chart_dynamic_fx",
        "aliases": ["dxy", "dolarovy index", "us dollar index", "sila dolaru", "fx"]
    },
    "eur_usd": {
        "region": "US", "main_tab": "💳 Finanční trhy & Měna", "sub_tab_id": "fx",
        "sub_tab_label": "Měnové kurzy (FX)", "anchor": "chart_dynamic_fx",
        "aliases": ["eur usd", "euro dolar", "hlavni menovy par", "fx", "forex"]
    },
    "usd_jpy": {
        "region": "US", "main_tab": "💳 Finanční trhy & Měna", "sub_tab_id": "fx",
        "sub_tab_label": "Měnové kurzy (FX)", "anchor": "chart_dynamic_fx",
        "aliases": ["usd jpy", "dolar jen", "japonsky jen", "fx", "forex"]
    },
    "gbp_usd": {
        "region": "US", "main_tab": "💳 Finanční trhy & Měna", "sub_tab_id": "fx",
        "sub_tab_label": "Měnové kurzy (FX)", "anchor": "chart_dynamic_fx",
        "aliases": ["gbp usd", "cable", "libra dolar", "fx", "forex"]
    },
    "usd_pln": {
        "region": "US", "main_tab": "💳 Finanční trhy & Měna", "sub_tab_id": "fx",
        "sub_tab_label": "Měnové kurzy (FX)", "anchor": "chart_dynamic_fx",
        "aliases": ["usd pln", "dolar zloty", "fx", "forex"]
    },
    "usd_chf": {
        "region": "US", "main_tab": "💳 Finanční trhy & Měna", "sub_tab_id": "fx",
        "sub_tab_label": "Měnové kurzy (FX)", "anchor": "chart_dynamic_fx",
        "aliases": ["usd chf", "dolar svycarsky frank", "fx", "forex"]
    },
    "us_ism_manufacturing": {
        "region": "US", "main_tab": "🏛️ Reálná ekonomika & Práce", "sub_tab_id": "leading",
        "sub_tab_label": "Předstihové ukazatele & Sentiment", "anchor": "chart_us_leading_indicators",
        "aliases": ["ism", "ism manufacturing", "ism prumysl", "vyrobni pmi usa", "predstihove ukazatele"]
    },
    "us_ism_services": {
        "region": "US", "main_tab": "🏛️ Reálná ekonomika & Práce", "sub_tab_id": "leading",
        "sub_tab_label": "Předstihové ukazatele & Sentiment", "anchor": "chart_us_leading_indicators",
        "aliases": ["ism services", "ism sluzby", "sluzby usa", "nevrobni ism"]
    },
    "us_michigan_sentiment": {
        "region": "US", "main_tab": "🏛️ Reálná ekonomika & Práce", "sub_tab_id": "leading",
        "sub_tab_label": "Předstihové ukazatele & Sentiment", "anchor": "chart_us_leading_indicators",
        "aliases": ["michigan", "michigan sentiment", "spotrebitelsky sentiment", "nalada spotrebitelu usa"]
    },
    "us_gdp_growth_real": {
        "region": "US", "main_tab": "🏛️ Reálná ekonomika & Práce", "sub_tab_id": "gdp",
        "sub_tab_label": "HDP", "anchor": "chart_us_gdp",
        "aliases": ["us gdp", "hdp usa", "rust hdp usa", "bea", "ekonomika spojenych statu"]
    },
    "us_gdp_nominal_usd_bn": {
        "region": "US", "main_tab": "🏛️ Reálná ekonomika & Práce", "sub_tab_id": "gdp",
        "sub_tab_label": "HDP", "anchor": "chart_us_gdp",
        "aliases": ["nominalni hdp usa", "velikost americke ekonomiky", "miliardy dolaru hdp"]
    },
    "us_cpi_yoy": {
        "region": "US", "main_tab": "🏛️ Reálná ekonomika & Práce", "sub_tab_id": "inflation",
        "sub_tab_label": "Inflace (CPI)", "anchor": "chart_us_inflation",
        "aliases": ["cpi usa", "inflace usa", "bls", "spotrebitelske ceny usa", "zdrazovani usa"]
    },
    "us_core_cpi_yoy": {
        "region": "US", "main_tab": "🏛️ Reálná ekonomika & Práce", "sub_tab_id": "inflation",
        "sub_tab_label": "Inflace (CPI)", "anchor": "chart_us_inflation",
        "aliases": ["jadrova inflace usa", "core cpi us", "bls", "jadrovy index cen"]
    },
    "us_retail_sales_yoy": {
        "region": "US", "main_tab": "🏛️ Reálná ekonomika & Práce", "sub_tab_id": "activity",
        "sub_tab_label": "Průmysl a spotřeba", "anchor": "chart_activity_panel",
        "aliases": ["maloobchod usa", "retail sales census", "spotreba americane"]
    },
    "us_industrial_prod_yoy": {
        "region": "US", "main_tab": "🏛️ Reálná ekonomika & Práce", "sub_tab_id": "activity",
        "sub_tab_label": "Průmysl a spotřeba", "anchor": "chart_activity_panel",
        "aliases": ["prumysl usa", "industrial production fed", "g.17", "tovarni vyroba"]
    },
    "us_unemployment_rate": {
        "region": "US", "main_tab": "🏛️ Reálná ekonomika & Práce", "sub_tab_id": "labor",
        "sub_tab_label": "Trh práce & Mzdy", "anchor": "chart_us_unemployment",
        "aliases": ["nezamestnanost usa", "u-3", "bls", "mira nezamestnanosti usa", "trh prace"]
    },
    "us_nonfarm_payrolls_k": {
        "region": "US", "main_tab": "🏛️ Reálná ekonomika & Práce", "sub_tab_id": "labor",
        "sub_tab_label": "Trh práce & Mzdy", "anchor": "chart_us_unemployment",
        "aliases": ["nfp", "nonfarm payrolls", "pracovni mista usa", "tvorba mist", "bls job report"]
    },
    "us_hourly_earnings_yoy": {
        "region": "US", "main_tab": "🏛️ Reálná ekonomika & Práce", "sub_tab_id": "labor",
        "sub_tab_label": "Trh práce & Mzdy", "anchor": "chart_us_wages",
        "aliases": ["hodinova mzda", "hourly earnings", "rust mezd usa", "bls", "wages"]
    },
    "sp500_index": {
        "region": "US", "main_tab": "📈 Trhy", "sub_tab_id": "sp500",
        "sub_tab_label": "🇺🇸 S&P 500", "anchor": "chart_single_sp",
        "aliases": ["sp500", "s&p 500", "s&p", "spy", "americke akcie", "wall street"]
    },
    "nasdaq_index": {
        "region": "US", "main_tab": "📈 Trhy", "sub_tab_id": "nasdaq",
        "sub_tab_label": "🇺🇸 NASDAQ Composite", "anchor": "chart_single_nasdaq",
        "aliases": ["nasdaq", "nasdaq composite", "qqq", "technologicke akcie", "tech index"]
    },
    "vix_index": {
        "region": "US", "main_tab": "📈 Trhy", "sub_tab_id": "vix",
        "sub_tab_label": "⚡ Index volatility VIX (Tržní riziko)", "anchor": "chart_vix_sentiment",
        "aliases": ["vix", "index volatility", "index strachu", "cboe vix", "trzni sentiment", "riziko"]
    },
    "us_public_debt_usd_bn": {
        "region": "US", "main_tab": "🌐 Veřejné finance & Svět", "sub_tab_id": "debt",
        "sub_tab_label": "Veřejný dluh", "anchor": "chart_us_debt_pct",
        "aliases": ["federalni dluh", "dluh usa", "us national debt", "treasury dept", "dluhovy strop"]
    },
    "us_public_debt_gdp_pct": {
        "region": "US", "main_tab": "🌐 Veřejné finance & Svět", "sub_tab_id": "debt",
        "sub_tab_label": "Veřejný dluh", "anchor": "chart_us_debt_pct",
        "aliases": ["us dluh k hdp", "debt to gdp usa", "federalni zadluzeni"]
    },
    "us_budget_deficit_usd_bn": {
        "region": "US", "main_tab": "🌐 Veřejné finance & Svět", "sub_tab_id": "debt",
        "sub_tab_label": "Veřejný dluh", "anchor": "chart_us_deficit",
        "aliases": ["schodek usa", "deficit usa", "us federal deficit", "rozpocet bily dum"]
    }
}


def normalize_czech_text(text: str) -> str:
    """Odstraní českou a obecnou diakritiku a převede na malá písmena."""
    if not text:
        return ""
    import unicodedata
    normalized = unicodedata.normalize("NFKD", str(text))
    return "".join(c for c in normalized if not unicodedata.combining(c)).lower().strip()


def build_indicator_search_catalog() -> list[dict[str, Any]]:
    """Vygeneruje kompletní JSON metadata katalog pro rychlé vyhledávání na klientovi."""
    catalog = []
    region_names = {
        "CZ": "Česká republika",
        "EU": "Evropská unie",
        "US": "Spojené státy"
    }
    region_badges = {
        "CZ": {"code": "CZ", "label": "ČR", "bg": "#eff6ff", "color": "#1d4ed8", "border": "#bfdbfe"},
        "EU": {"code": "EU", "label": "EU", "bg": "#eef2ff", "color": "#4338ca", "border": "#c7d2fe"},
        "US": {"code": "US", "label": "USA", "bg": "#fef2f2", "color": "#b91c1c", "border": "#fecaca"}
    }
    country_switches = {
        "CZ": "🇨🇿 Česká republika",
        "EU": "🇪🇺 Evropská unie",
        "US": "🇺🇸 Spojené státy"
    }

    for code, ind in INDICATORS.items():
        nav_info = INDICATOR_NAVIGATION_REGISTRY.get(code, {})
        reg = ind.region or "CZ"
        category = ind.category or "Makroekonomie"
        name = ind.name_cz or code
        aliases = nav_info.get("aliases", [])

        # Vytvoření normalizovaného vyhledávacího řetězce
        search_tokens = [
            code,
            name,
            category,
            reg,
            region_names.get(reg, ""),
            ind.unit or ""
        ] + aliases
        normalized_search = " ".join([normalize_czech_text(tok) for tok in search_tokens if tok])

        badge_info = region_badges.get(reg, region_badges["CZ"])

        catalog.append({
            "code": code,
            "name": name,
            "category": category,
            "unit": ind.unit or "",
            "region": reg,
            "regionName": region_names.get(reg, "ČR"),
            "regionBadge": badge_info["label"],
            "badgeBg": badge_info["bg"],
            "badgeColor": badge_info["color"],
            "badgeBorder": badge_info["border"],
            "countrySwitch": country_switches.get(reg, "🇨🇿 Česká republika"),
            "mainTab": nav_info.get("main_tab", "💳 Finanční trhy & Měna"),
            "subTabId": nav_info.get("sub_tab_id", "rates"),
            "subTabLabel": nav_info.get("sub_tab_label", "Sazby"),
            "anchor": nav_info.get("anchor", "chart_cz_rates"),
            "searchText": normalized_search
        })

    return catalog


# =============================================================================
# 2. ZPRACOVÁNÍ NAVIGACE Z QUERY PARAMETRU (PŘI VÝBĚRU Z NAŠEPTÁVAČE)
# =============================================================================

def handle_indicator_search_navigation() -> None:
    """
    Zpracuje URL dotaz `?search_indicator=code` vyvolaný výběrem v našeptávači.
    Přepne ekonomiku, hlavní záložku, podzáložku a nastaví odrolování na daný ukazatel.
    """
    selected_code = st.query_params.get("search_indicator")
    if not selected_code:
        return

    # Okamžitě smažeme parametr z URL, aby zůstala čistá a nedocházelo k opakovanému přepínání
    try:
        del st.query_params["search_indicator"]
    except Exception:
        pass

    nav_info = INDICATOR_NAVIGATION_REGISTRY.get(selected_code)
    ind_info = INDICATORS.get(selected_code)
    if not nav_info or not ind_info:
        return

    reg = ind_info.region or "CZ"
    country_map = {
        "CZ": "🇨🇿 Česká republika",
        "EU": "🇪🇺 Evropská unie",
        "US": "🇺🇸 Spojené státy"
    }

    # 1. Zajištění zobrazení monitoru (kdyby byl uživatel v glosáři)
    st.session_state["current_view"] = "monitor"

    # 2. Přepnutí ekonomiky
    st.session_state["macro_region_top_switch"] = country_map.get(reg, "🇨🇿 Česká republika")

    # 3. Přepnutí hlavní záložky
    st.session_state["main_dashboard_tabs_selected"] = nav_info.get("main_tab", "💳 Finanční trhy & Měna")

    # 4. Přepnutí konkrétní podzáložky podle hlavní kategorie
    main_tab_str = nav_info.get("main_tab", "")
    sub_tab_label = nav_info.get("sub_tab_label")

    if "Finanční trhy" in main_tab_str:
        st.session_state["sub_tab_markets_selected"] = sub_tab_label
    elif "Reálná ekonomika" in main_tab_str:
        st.session_state["sub_tab_real_selected"] = sub_tab_label
    elif "Trhy" in main_tab_str:
        st.session_state["sub_tab_stocks_selected"] = sub_tab_label
    elif "Veřejné finance" in main_tab_str:
        st.session_state["sub_tab_public_selected"] = sub_tab_label

    # 5. Uložení kotevního ID pro plynulé odrolování
    st.session_state["target_scroll_anchor"] = nav_info.get("anchor")


# =============================================================================
# 3. VYKRESLENÍ SEARCH BARU A COMMAND PALETTE DRAWERU
# =============================================================================

def render_indicator_search_bar() -> None:
    """
    Vykreslí vyhledávací pole s ikonou lupy, placeholdrem a zkratkou Ctrl + K v sidebaru
    a injektuje interaktivní Command Palette / Search Drawer overlay.
    """
    catalog = build_indicator_search_catalog()
    catalog_json = json.dumps(catalog, ensure_ascii=False)

    html_code = f"""
    <!-- STYLY PRO VYHLEDÁVÁNÍ V SIDEBARU A INTERAKTIVNÍ SEARCH DRAWER -->
    <style>
    /* 1. Sidebar trigger input box */
    .sb-search-trigger-container {{
        margin-top: 10px;
        margin-bottom: 14px;
        width: 100%;
    }}

    .sb-search-trigger-box {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: #f8fafc;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        padding: 7px 11px;
        cursor: pointer;
        transition: all 0.15s ease-in-out;
        user-select: none;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    }}

    .sb-search-trigger-box:hover {{
        background: #ffffff;
        border-color: #3b82f6;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.15);
    }}

    .sb-search-trigger-left {{
        display: flex;
        align-items: center;
        gap: 8px;
        min-width: 0;
        flex: 1;
    }}

    .sb-search-icon {{
        font-size: 0.95rem;
        color: #64748b;
        flex-shrink: 0;
    }}

    .sb-search-placeholder {{
        font-size: 0.81rem;
        color: #64748b;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        font-weight: 450;
    }}

    .sb-search-shortcut-badge {{
        display: inline-flex;
        align-items: center;
        gap: 3px;
        background: #e2e8f0;
        border: 1px solid #cbd5e1;
        border-radius: 5px;
        padding: 2px 6px;
        font-size: 0.68rem;
        font-weight: 700;
        color: #334155;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace;
        letter-spacing: -0.01em;
        flex-shrink: 0;
        margin-left: 6px;
    }}

    /* 2. Command Palette / Search Drawer Overlay */
    #macro-search-drawer-backdrop {{
        position: fixed;
        inset: 0;
        background: rgba(15, 23, 42, 0.65);
        backdrop-filter: blur(5px);
        -webkit-backdrop-filter: blur(5px);
        z-index: 9999999;
        display: none;
        align-items: flex-start;
        justify-content: center;
        padding-top: 8vh;
        box-sizing: border-box;
        animation: fadeInDrawer 0.15s ease-out forwards;
    }}

    @keyframes fadeInDrawer {{
        from {{ opacity: 0; }}
        to {{ opacity: 1; }}
    }}

    .macro-search-modal-card {{
        width: 94vw;
        max-width: 660px;
        max-height: 82vh;
        background: #ffffff;
        border-radius: 14px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 25px 50px -12px rgba(15, 23, 42, 0.35), 0 0 0 1px rgba(0,0,0,0.05);
        display: flex;
        flex-direction: column;
        overflow: hidden;
        animation: slideDownModal 0.18s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }}

    @keyframes slideDownModal {{
        from {{ transform: translateY(-16px) scale(0.98); opacity: 0; }}
        to {{ transform: translateY(0) scale(1); opacity: 1; }}
    }}

    /* Search input area */
    .macro-search-input-header {{
        display: flex;
        align-items: center;
        padding: 13px 18px;
        border-bottom: 1px solid #e2e8f0;
        background: #ffffff;
        gap: 12px;
    }}

    .macro-search-input-icon {{
        font-size: 1.25rem;
        color: #3b82f6;
        flex-shrink: 0;
    }}

    .macro-search-input-field {{
        width: 100%;
        border: none;
        outline: none;
        font-size: 1.02rem;
        font-weight: 500;
        color: #0f172a;
        background: transparent;
        font-family: inherit;
    }}

    .macro-search-input-field::placeholder {{
        color: #94a3b8;
        font-weight: 400;
    }}

    .macro-search-clear-btn {{
        background: transparent;
        border: none;
        color: #94a3b8;
        font-size: 1.15rem;
        cursor: pointer;
        padding: 2px 6px;
        border-radius: 4px;
        display: none;
    }}

    .macro-search-clear-btn:hover {{
        color: #0f172a;
        background: #f1f5f9;
    }}

    .macro-search-esc-badge {{
        background: #f1f5f9;
        border: 1px solid #cbd5e1;
        border-radius: 5px;
        padding: 2px 7px;
        font-size: 0.68rem;
        font-weight: 700;
        color: #475569;
        font-family: monospace;
        flex-shrink: 0;
        user-select: none;
    }}

    /* Quick suggestions bar */
    .macro-search-quick-chips {{
        display: flex;
        align-items: center;
        gap: 6px;
        padding: 9px 18px;
        background: #f8fafc;
        border-bottom: 1px solid #f1f5f9;
        overflow-x: auto;
        white-space: nowrap;
        scrollbar-width: none;
    }}
    .macro-search-quick-chips::-webkit-scrollbar {{
        display: none;
    }}

    .macro-search-chip-label {{
        font-size: 0.73rem;
        font-weight: 700;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.03em;
        margin-right: 2px;
    }}

    .macro-search-chip {{
        display: inline-block;
        padding: 3px 9px;
        background: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 12px;
        font-size: 0.74rem;
        color: #334155;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.12s ease;
    }}

    .macro-search-chip:hover {{
        background: #e0f2fe;
        border-color: #38bdf8;
        color: #0369a1;
    }}

    /* Results list */
    .macro-search-results-container {{
        overflow-y: auto;
        padding: 10px 14px;
        flex: 1;
        max-height: 58vh;
        scrollbar-width: thin;
    }}

    .macro-search-group-header {{
        font-size: 0.72rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #64748b;
        padding: 9px 10px 4px 10px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }}

    .macro-search-group-count {{
        font-size: 0.68rem;
        font-weight: 600;
        background: #f1f5f9;
        color: #475569;
        padding: 1px 6px;
        border-radius: 10px;
    }}

    .macro-search-item {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 9px 12px;
        margin-bottom: 3px;
        border-radius: 8px;
        cursor: pointer;
        transition: background 0.12s ease, border-color 0.12s ease;
        border-left: 3px solid transparent;
    }}

    .macro-search-item:hover,
    .macro-search-item.is-selected {{
        background: #eff6ff;
        border-left-color: #2563eb;
    }}

    .macro-search-item-left {{
        min-width: 0;
        flex: 1;
        padding-right: 12px;
    }}

    .macro-search-item-name {{
        font-size: 0.90rem;
        font-weight: 750;
        color: #0f172a;
        line-height: 1.3;
        margin-bottom: 2px;
        word-break: break-word;
    }}

    .macro-search-highlight {{
        background: #fef08a;
        color: #854d0e;
        padding: 0 2px;
        border-radius: 2px;
        font-weight: 800;
    }}

    .macro-search-item-meta {{
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 0.75rem;
        color: #64748b;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}

    .macro-search-item-cat {{
        font-weight: 550;
        color: #475569;
    }}

    .macro-search-item-bc {{
        color: #94a3b8;
    }}

    .macro-search-item-right {{
        display: flex;
        align-items: center;
        gap: 8px;
        flex-shrink: 0;
    }}

    .macro-search-region-badge {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 2px 7px;
        border-radius: 4px;
        font-size: 0.70rem;
        font-weight: 800;
        letter-spacing: 0.02em;
        text-transform: uppercase;
        border: 1px solid transparent;
    }}

    .macro-search-enter-hint {{
        display: none;
        font-size: 0.70rem;
        color: #2563eb;
        font-weight: 700;
        background: #dbeafe;
        padding: 2px 6px;
        border-radius: 4px;
    }}

    .macro-search-item.is-selected .macro-search-enter-hint {{
        display: inline-block;
    }}

    /* Empty state */
    .macro-search-empty-state {{
        text-align: center;
        padding: 36px 20px;
        color: #64748b;
    }}

    .macro-search-empty-icon {{
        font-size: 2.2rem;
        margin-bottom: 10px;
        display: block;
        opacity: 0.7;
    }}

    .macro-search-empty-title {{
        font-size: 1.02rem;
        font-weight: 750;
        color: #1e293b;
        margin-bottom: 6px;
    }}

    .macro-search-empty-sub {{
        font-size: 0.82rem;
        color: #64748b;
        max-width: 400px;
        margin: 0 auto;
        line-height: 1.45;
    }}

    /* Footer with keyboard hints */
    .macro-search-footer {{
        padding: 8px 18px;
        background: #f8fafc;
        border-top: 1px solid #e2e8f0;
        display: flex;
        align-items: center;
        justify-content: space-between;
        font-size: 0.73rem;
        color: #64748b;
        user-select: none;
    }}

    .macro-search-footer-shortcuts {{
        display: flex;
        align-items: center;
        gap: 12px;
    }}

    .macro-search-footer-kbd {{
        background: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 4px;
        padding: 1px 5px;
        font-size: 0.68rem;
        font-family: monospace;
        color: #334155;
        font-weight: 700;
        margin-right: 3px;
    }}
    </style>

    <!-- SIDEBAR SEARCH BAR ELEMENT -->
    <div class="sb-search-trigger-container">
        <div class="sb-search-trigger-box" id="macro-sidebar-search-btn" title="Hledat indikátor (Ctrl + K)">
            <div class="sb-search-trigger-left">
                <span class="sb-search-icon">🔍</span>
                <span class="sb-search-placeholder">Hledat indikátor... (např. CPI, repo, Bund, PRIBOR)</span>
            </div>
            <span class="sb-search-shortcut-badge"><kbd>Ctrl</kbd> + <kbd>K</kbd></span>
        </div>
    </div>

    <!-- COMMAND PALETTE / SEARCH DRAWER MODAL OVERLAY -->
    <div id="macro-search-drawer-backdrop">
        <div class="macro-search-modal-card" id="macro-search-modal-card">
            <!-- Header s vyhledávacím vstupem -->
            <div class="macro-search-input-header">
                <span class="macro-search-input-icon">🔍</span>
                <input type="text"
                       id="macro-search-modal-input"
                       class="macro-search-input-field"
                       placeholder="Hledat indikátor... (např. CPI, repo, Bund, PRIBOR)"
                       autocomplete="off"
                       spellcheck="false" />
                <button type="button" id="macro-search-clear-btn" class="macro-search-clear-btn" title="Vymazat">✕</button>
                <span class="macro-search-esc-badge"><kbd>ESC</kbd></span>
            </div>

            <!-- Rychlé populární filtry / chips -->
            <div class="macro-search-quick-chips">
                <span class="macro-search-chip-label">Tipy:</span>
                <span class="macro-search-chip" data-query="repo">2T Repo sazba</span>
                <span class="macro-search-chip" data-query="cpi">Inflace (CPI)</span>
                <span class="macro-search-chip" data-query="bund">10Y Bund</span>
                <span class="macro-search-chip" data-query="pribor">PRIBOR 3M</span>
                <span class="macro-search-chip" data-query="hypo">Hypotéky</span>
                <span class="macro-search-chip" data-query="sp500">S&P 500</span>
                <span class="macro-search-chip" data-query="vix">Volatilita VIX</span>
                <span class="macro-search-chip" data-query="hdp">HDP</span>
                <span class="macro-search-chip" data-query="mzdy">Mzdy</span>
            </div>

            <!-- Scrollovatelný kontejner výsledků -->
            <div class="macro-search-results-container" id="macro-search-results-list">
                <!-- Zde se dynamicky renderují seskupené výsledky -->
            </div>

            <!-- Patička s nápovědou klávesových zkratek -->
            <div class="macro-search-footer">
                <div class="macro-search-footer-shortcuts">
                    <span><span class="macro-search-footer-kbd">↑</span><span class="macro-search-footer-kbd">↓</span> navigace</span>
                    <span><span class="macro-search-footer-kbd">↵</span> přejít na indikátor</span>
                    <span><span class="macro-search-footer-kbd">esc</span> zavřít</span>
                </div>
                <div>
                    <span id="macro-search-count-total">101</span> ukazatelů (ČR, EU, USA)
                </div>
            </div>
        </div>
    </div>

    <!-- JAVASCRIPT LOGIKA NAŠEPTÁVAČE, FUZZY SEARCH A KLÁVESNICOVÉ NAVIGACE -->
    <script>
    (function() {{
        // Datový katalog všech 101 indikátorů
        const INDICATORS_CATALOG = {catalog_json};

        // Získání správného kontextu dokumentu (i pro iframe fallback)
        const topWin = (typeof window.parent !== 'undefined' && window.parent && window.parent.document) ? window.parent : window;
        const topDoc = topWin.document;

        // Přemístění overlaye na document.body pro prevenci clippingu či transformací
        function setupModalDom() {{
            const existingBackdrop = topDoc.getElementById('macro-search-drawer-backdrop');
            const localBackdrop = document.getElementById('macro-search-drawer-backdrop');
            if (localBackdrop && (!existingBackdrop || existingBackdrop === localBackdrop)) {{
                if (localBackdrop.parentNode !== topDoc.body) {{
                    topDoc.body.appendChild(localBackdrop);
                }}
            }}
        }}

        // Normalizace diakritiky: převod na lowercase bez háčků a čárek
        function stripDiacritics(str) {{
            if (!str) return '';
            return str
                .normalize('NFD')
                .replace(/[\u0300-\u036f]/g, '')
                .toLowerCase()
                .trim();
        }}

        // Zvýraznění shodujícího se textu
        function highlightMatch(text, rawQuery) {{
            if (!rawQuery) return text;
            const normText = stripDiacritics(text);
            const normQuery = stripDiacritics(rawQuery);
            if (!normQuery) return text;

            const idx = normText.indexOf(normQuery);
            if (idx === -1) return text;

            const matchOriginal = text.substring(idx, idx + rawQuery.length);
            return text.substring(0, idx) +
                   '<mark class="macro-search-highlight">' + matchOriginal + '</mark>' +
                   text.substring(idx + rawQuery.length);
        }}

        // Získání DOM elementů z top documentu
        function getElements() {{
            return {{
                backdrop: topDoc.getElementById('macro-search-drawer-backdrop'),
                card: topDoc.getElementById('macro-search-modal-card'),
                input: topDoc.getElementById('macro-search-modal-input'),
                clearBtn: topDoc.getElementById('macro-search-clear-btn'),
                resultsList: topDoc.getElementById('macro-search-results-list'),
                sidebarBtn: topDoc.getElementById('macro-sidebar-search-btn') || document.getElementById('macro-sidebar-search-btn')
            }};
        }}

        let selectedIndex = 0;
        let currentFilteredResults = [];

        // Otevření draweru
        function openDrawer(initialQuery = '') {{
            setupModalDom();
            const els = getElements();
            if (!els.backdrop || !els.input) return;

            els.backdrop.style.display = 'flex';
            if (initialQuery) {{
                els.input.value = initialQuery;
            }}
            els.input.focus();
            renderSearchResults(els.input.value);
        }}

        // Zavření draweru
        function closeDrawer() {{
            const els = getElements();
            if (!els.backdrop) return;
            els.backdrop.style.display = 'none';
            if (els.input) {{
                els.input.value = '';
            }}
            selectedIndex = 0;
        }}

        // Navigace na indikátor
        function navigateToIndicator(code) {{
            closeDrawer();
            const url = new URL(topWin.location.href);
            url.searchParams.set('search_indicator', code);
            topWin.location.href = url.toString();
        }}

        // Vykreslení výsledků
        function renderSearchResults(query = '') {{
            const els = getElements();
            if (!els.resultsList) return;

            const qClean = stripDiacritics(query);
            if (els.clearBtn) {{
                els.clearBtn.style.display = qClean.length > 0 ? 'inline-block' : 'none';
            }}

            let filtered = [];
            if (!qClean) {{
                // Pokud je pole prázdné, nabídneme reprezentativní výběr klíčových ukazatelů
                filtered = INDICATORS_CATALOG.filter(item => [
                    'repo_rate', 'cpi_yoy', 'czgb_10y', 'pribor_3m', 'cz_mortgage_rate',
                    'ecb_deposit_rate', 'bund_10y', 'eu_cpi_yoy', 'stoxx50_index',
                    'fed_funds_upper', 'us_10y', 'us_cpi_yoy', 'sp500_index', 'vix_index'
                ].includes(item.code));
            }} else {{
                // Multi-token fuzzy matching od 1 zadaného znaku
                const tokens = qClean.split(/\s+/).filter(Boolean);
                filtered = INDICATORS_CATALOG.filter(item => {{
                    return tokens.every(tok => item.searchText.includes(tok));
                }});
            }}

            currentFilteredResults = filtered;
            selectedIndex = 0;

            if (filtered.length === 0) {{
                els.resultsList.innerHTML = `
                    <div class="macro-search-empty-state">
                        <span class="macro-search-empty-icon">🔍</span>
                        <div class="macro-search-empty-title">Žádný indikátor nebyl nalezen.</div>
                        <div class="macro-search-empty-sub">
                            Zkuste zadat jiný výraz (např. <strong>CPI</strong>, <strong>repo</strong>, <strong>Bund</strong>, <strong>PRIBOR</strong>, <strong>HDP</strong>, <strong>hypotéky</strong> nebo <strong>VIX</strong>).
                        </div>
                    </div>
                `;
                return;
            }}

            // Seskupení podle regionů (ČR, EU, USA)
            const groups = {{
                'CZ': {{ title: '🇨🇿 Česká republika', items: [] }},
                'EU': {{ title: '🇪🇺 Evropská unie', items: [] }},
                'US': {{ title: '🇺🇸 Spojené státy', items: [] }}
            }};

            filtered.forEach((item, globalIdx) => {{
                if (groups[item.region]) {{
                    groups[item.region].items.push({{ item, globalIdx }});
                }}
            }});

            let html = '';
            ['CZ', 'EU', 'US'].forEach(regKey => {{
                const grp = groups[regKey];
                if (grp.items.length > 0) {{
                    html += `
                        <div class="macro-search-group-header">
                            <span>${{grp.title}}</span>
                            <span class="macro-search-group-count">${{grp.items.length}}</span>
                        </div>
                    `;
                    grp.items.forEach(({{ item, globalIdx }}) => {{
                        const isSelected = (globalIdx === selectedIndex);
                        const highlightedName = highlightMatch(item.name, query);
                        html += `
                            <div class="macro-search-item ${{isSelected ? 'is-selected' : ''}}"
                                 data-idx="${{globalIdx}}"
                                 data-code="${{item.code}}"
                                 id="macro-search-item-${{globalIdx}}">
                                <div class="macro-search-item-left">
                                    <div class="macro-search-item-name">${{highlightedName}}</div>
                                    <div class="macro-search-item-meta">
                                        <span class="macro-search-item-cat">${{item.category}}</span>
                                        <span class="macro-search-item-bc">• ${{item.mainTab}} › ${{item.subTabLabel}}</span>
                                    </div>
                                </div>
                                <div class="macro-search-item-right">
                                    <span class="macro-search-region-badge"
                                          style="background: ${{item.badgeBg}}; color: ${{item.badgeColor}}; border-color: ${{item.badgeBorder}};">
                                        ${{item.regionBadge}}
                                    </span>
                                    <span class="macro-search-enter-hint">↵</span>
                                </div>
                            </div>
                        `;
                    }});
                }}
            }});

            els.resultsList.innerHTML = html;

            // Navázání click událostí na výsledky
            const itemsDom = els.resultsList.querySelectorAll('.macro-search-item');
            itemsDom.forEach(node => {{
                node.addEventListener('click', () => {{
                    const code = node.getAttribute('data-code');
                    if (code) navigateToIndicator(code);
                }});
                node.addEventListener('mouseenter', () => {{
                    const idx = parseInt(node.getAttribute('data-idx'), 10);
                    if (!isNaN(idx)) {{
                        updateActiveIndex(idx, false);
                    }}
                }});
            }});
        }}

        // Aktualizace aktivní položky při šipkách
        function updateActiveIndex(newIdx, shouldScroll = true) {{
            if (currentFilteredResults.length === 0) return;
            const els = getElements();
            if (!els.resultsList) return;

            const oldNode = els.resultsList.querySelector(`.macro-search-item[data-idx="${{selectedIndex}}"]`);
            if (oldNode) oldNode.classList.remove('is-selected');

            selectedIndex = Math.max(0, Math.min(newIdx, currentFilteredResults.length - 1));

            const newNode = els.resultsList.querySelector(`.macro-search-item[data-idx="${{selectedIndex}}"]`);
            if (newNode) {{
                newNode.classList.add('is-selected');
                if (shouldScroll) {{
                    newNode.scrollIntoView({{ block: 'nearest', behavior: 'smooth' }});
                }}
            }}
        }}

        // Globální listenery klávesnice
        function bindEventListeners() {{
            setupModalDom();
            const els = getElements();

            // 1. Otevření kliknutím na sidebar tlačítko
            const sbBtn = topDoc.getElementById('macro-sidebar-search-btn') || document.getElementById('macro-sidebar-search-btn');
            if (sbBtn) {{
                sbBtn.onclick = () => openDrawer();
            }}

            // 2. Klávesová zkratka Ctrl+K / Cmd+K kdekoliv na stránce
            topWin.addEventListener('keydown', (e) => {{
                if ((e.ctrlKey || e.metaKey) && (e.key === 'k' || e.key === 'K')) {{
                    e.preventDefault();
                    e.stopPropagation();
                    const backdrop = topDoc.getElementById('macro-search-drawer-backdrop');
                    if (backdrop && backdrop.style.display === 'flex') {{
                        closeDrawer();
                    }} else {{
                        openDrawer();
                    }}
                }} else if (e.key === 'Escape') {{
                    const backdrop = topDoc.getElementById('macro-search-drawer-backdrop');
                    if (backdrop && backdrop.style.display === 'flex') {{
                        e.preventDefault();
                        closeDrawer();
                    }}
                }}
            }});

            // 3. Ovládání uvnitř modalu
            if (els.input) {{
                els.input.oninput = (e) => {{
                    renderSearchResults(e.target.value);
                }};

                els.input.onkeydown = (e) => {{
                    if (e.key === 'ArrowDown') {{
                        e.preventDefault();
                        updateActiveIndex(selectedIndex + 1, true);
                    }} else if (e.key === 'ArrowUp') {{
                        e.preventDefault();
                        updateActiveIndex(selectedIndex - 1, true);
                    }} else if (e.key === 'Enter') {{
                        e.preventDefault();
                        if (currentFilteredResults.length > 0 && currentFilteredResults[selectedIndex]) {{
                            navigateToIndicator(currentFilteredResults[selectedIndex].code);
                        }}
                    }}
                }};
            }}

            // 4. Vymazání vstupu tlačítkem ✕
            if (els.clearBtn) {{
                els.clearBtn.onclick = () => {{
                    if (els.input) {{
                        els.input.value = '';
                        els.input.focus();
                        renderSearchResults('');
                    }}
                }};
            }}

            // 5. Zavření kliknutím na backdrop
            if (els.backdrop) {{
                els.backdrop.onclick = (e) => {{
                    if (e.target === els.backdrop) {{
                        closeDrawer();
                    }}
                }};
            }}

            // 6. Rychlé chipy (Tipy)
            const chips = topDoc.querySelectorAll('.macro-search-chip');
            chips.forEach(chip => {{
                chip.onclick = () => {{
                    const q = chip.getAttribute('data-query');
                    if (els.input && q) {{
                        els.input.value = q;
                        els.input.focus();
                        renderSearchResults(q);
                    }}
                }};
            }});
        }}

        // Inicializace při načtení
        setTimeout(bindEventListeners, 120);
        setTimeout(setupModalDom, 250);
    }})();
    </script>
    """

    # Vykreslení do sidebaru
    if hasattr(st.sidebar, "html"):
        st.sidebar.html(html_code)
    else:
        st.sidebar.markdown(html_code, unsafe_allow_html=True)


# =============================================================================
# 4. POMOCNÁ FUNKCE PRO ODROLOVÁNÍ KE KARTĚ NEBO GRAFU
# =============================================================================

def render_scroll_anchor_effect() -> None:
    """
    Pokud bylo při přechodu z vyhledávání nastaveno kotevní ID,
    provede po vyrenderování stránky plynulé odrolování (smooth scroll) na daný element.
    """
    target_anchor = st.session_state.pop("target_scroll_anchor", None)
    if not target_anchor:
        return

    script = f"""
    <script>
    (function() {{
        const targetId = "{target_anchor}";
        setTimeout(function() {{
            const topDoc = (window.parent && window.parent.document) ? window.parent.document : document;
            // Hledání podle ID nebo podle selektoru třídy/atributu
            let el = topDoc.getElementById(targetId) || topDoc.querySelector('[data-testid="stPlotlyChart"]');
            if (el) {{
                el.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                el.style.transition = 'outline 0.3s ease';
                el.style.outline = '3px solid #3b82f6';
                el.style.outlineOffset = '4px';
                setTimeout(() => {{ el.style.outline = 'none'; }}, 2200);
            }}
        }}, 450);
    }})();
    </script>
    """
    if hasattr(st, "html"):
        st.html(script)
    else:
        st.markdown(script, unsafe_allow_html=True)
