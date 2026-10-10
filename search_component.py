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
    Vykreslí interaktivní vyhledávací pole s reálným textovým vstupem v sidebaru,
    placeholdrem, ikonou lupy, zkratkou Ctrl + K a našeprávacím drawerem/dropdownem.
    """
    catalog = build_indicator_search_catalog()
    catalog_json = json.dumps(catalog, ensure_ascii=False)

    html_code = f"""
    <!-- STYLY PRO INTERAKTIVNÍ SEARCH BAR A AUTOCOMPLETE DRAWER -->
    <style>
    .macro-search-wrapper {{
        position: relative;
        margin-top: 10px;
        margin-bottom: 14px;
        width: 100%;
        box-sizing: border-box;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        z-index: 10000;
    }}

    div[data-testid="stElementContainer"]:has(.macro-search-wrapper),
    .stHtml:has(.macro-search-wrapper) {{
        overflow: visible !important;
    }}

    .macro-search-box {{
        display: flex;
        align-items: center;
        background: #ffffff;
        border: 1.5px solid #cbd5e1;
        border-radius: 9px;
        padding: 6px 10px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        transition: all 0.15s ease-in-out;
        box-sizing: border-box;
        width: 100%;
        cursor: text;
    }}

    .macro-search-box:focus-within {{
        border-color: #2563eb;
        background: #ffffff;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.18);
    }}

    .macro-search-icon {{
        font-size: 0.95rem;
        margin-right: 8px;
        flex-shrink: 0;
        line-height: 1;
        user-select: none;
    }}

    .macro-search-input {{
        flex: 1;
        min-width: 0;
        border: none !important;
        outline: none !important;
        background: transparent !important;
        font-size: 0.81rem;
        font-weight: 500;
        color: #0f172a;
        padding: 2px 0;
        font-family: inherit;
        box-shadow: none !important;
    }}

    .macro-search-input::placeholder {{
        color: #64748b;
        font-weight: 450;
        opacity: 0.9;
    }}

    .macro-search-clear-btn {{
        display: none;
        background: transparent;
        border: none;
        color: #94a3b8;
        font-size: 0.95rem;
        cursor: pointer;
        padding: 0 4px;
        line-height: 1;
        border-radius: 3px;
    }}

    .macro-search-clear-btn:hover {{
        color: #0f172a;
        background: #f1f5f9;
    }}

    .macro-search-shortcut {{
        background: #f1f5f9;
        border: 1px solid #cbd5e1;
        border-radius: 5px;
        padding: 2px 6px;
        font-size: 0.68rem;
        font-weight: 700;
        color: #475569;
        font-family: monospace;
        letter-spacing: -0.01em;
        flex-shrink: 0;
        margin-left: 6px;
        user-select: none;
        line-height: 1.2;
    }}

    /* Dropdown results container right below the search box */
    .macro-search-dropdown {{
        display: none;
        position: absolute;
        top: calc(100% + 5px);
        left: 0;
        right: 0;
        width: 100%;
        max-height: 480px;
        overflow-y: auto;
        background: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 10px;
        box-shadow: 0 14px 30px -4px rgba(15, 23, 42, 0.22), 0 4px 10px -2px rgba(15, 23, 42, 0.08);
        z-index: 999999;
        box-sizing: border-box;
        padding: 8px 10px;
        scrollbar-width: thin;
        animation: dropdownSlideIn 0.12s ease-out forwards;
    }}

    @keyframes dropdownSlideIn {{
        from {{ opacity: 0; transform: translateY(-4px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}

    .macro-search-dropdown.is-open {{
        display: block !important;
    }}

    /* Quick tips container */
    .macro-search-quick-tips {{
        padding: 6px 4px 10px 4px;
        border-bottom: 1px solid #f1f5f9;
        margin-bottom: 6px;
    }}

    .macro-search-tips-title {{
        font-size: 0.72rem;
        font-weight: 750;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-bottom: 6px;
    }}

    .macro-search-tips-chips {{
        display: flex;
        flex-wrap: wrap;
        gap: 5px;
    }}

    .macro-search-chip {{
        display: inline-block;
        padding: 3px 8px;
        background: #f8fafc;
        border: 1px solid #cbd5e1;
        border-radius: 12px;
        font-size: 0.73rem;
        color: #334155;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.12s ease;
        user-select: none;
    }}

    .macro-search-chip:hover {{
        background: #e0f2fe;
        border-color: #38bdf8;
        color: #0369a1;
    }}

    /* Region Group Header */
    .macro-search-group-header {{
        font-size: 0.72rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748b;
        padding: 8px 8px 3px 8px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }}

    .macro-search-group-count {{
        font-size: 0.66rem;
        font-weight: 700;
        background: #f1f5f9;
        color: #475569;
        padding: 1px 5px;
        border-radius: 8px;
    }}

    /* Result item */
    .macro-search-item {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 8px 10px;
        margin-bottom: 2px;
        border-radius: 7px;
        cursor: pointer;
        transition: background 0.12s ease, border-left-color 0.12s ease;
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
        padding-right: 8px;
    }}

    .macro-search-item-name {{
        font-size: 0.86rem;
        font-weight: 750;
        color: #0f172a;
        line-height: 1.25;
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
        gap: 5px;
        font-size: 0.72rem;
        color: #64748b;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}

    .macro-search-item-cat {{
        font-weight: 600;
        color: #475569;
    }}

    .macro-search-item-bc {{
        color: #94a3b8;
    }}

    .macro-search-item-right {{
        display: flex;
        align-items: center;
        gap: 6px;
        flex-shrink: 0;
    }}

    .macro-search-region-badge {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.67rem;
        font-weight: 800;
        letter-spacing: 0.02em;
        text-transform: uppercase;
        border: 1px solid transparent;
    }}

    /* Empty state */
    .macro-search-empty-state {{
        text-align: center;
        padding: 24px 14px;
        color: #64748b;
    }}

    .macro-search-empty-icon {{
        font-size: 1.8rem;
        margin-bottom: 6px;
        display: block;
        opacity: 0.7;
    }}

    .macro-search-empty-title {{
        font-size: 0.95rem;
        font-weight: 750;
        color: #1e293b;
        margin-bottom: 4px;
    }}

    .macro-search-empty-sub {{
        font-size: 0.78rem;
        color: #64748b;
        line-height: 1.4;
    }}

    /* Dropdown footer */
    .macro-search-dropdown-footer {{
        margin-top: 6px;
        padding: 6px 6px 2px 6px;
        border-top: 1px solid #f1f5f9;
        display: flex;
        align-items: center;
        justify-content: space-between;
        font-size: 0.68rem;
        color: #64748b;
        user-select: none;
    }}

    .macro-search-dropdown-footer kbd {{
        background: #f1f5f9;
        border: 1px solid #cbd5e1;
        border-radius: 3px;
        padding: 1px 4px;
        font-size: 0.64rem;
        font-family: monospace;
        color: #334155;
        font-weight: 700;
    }}
    </style>

    <!-- REAL TEXT INPUT IN SIDEBAR WITH LIVE DROPDOWN DRAWER -->
    <div class="macro-search-wrapper" id="macro-search-wrapper">
        <div class="macro-search-box" id="macro-search-box" onclick="const el=document.getElementById('macro-sidebar-search-input'); if(el) el.focus();">
            <span class="macro-search-icon">🔍</span>
            <input type="text"
                   id="macro-sidebar-search-input"
                   class="macro-search-input"
                   placeholder="Hledat indikátor... (např. CPI, repo, Bund, PRIBOR)"
                   autocomplete="off"
                   autocorrect="off"
                   autocapitalize="off"
                   spellcheck="false"
                   oninput="window.macroSearchOnInput && window.macroSearchOnInput(this.value)"
                   onfocus="window.macroSearchOnFocus && window.macroSearchOnFocus(this.value)"
                   onkeydown="window.macroSearchOnKeydown && window.macroSearchOnKeydown(event)" />
            <button type="button" id="macro-sidebar-clear-btn" class="macro-search-clear-btn" title="Vymazat" onclick="window.macroSearchClear && window.macroSearchClear()">✕</button>
            <span class="macro-search-shortcut"><kbd>Ctrl</kbd> + <kbd>K</kbd></span>
        </div>

        <div id="macro-sidebar-dropdown" class="macro-search-dropdown">
            <div id="macro-sidebar-dropdown-content">
                <!-- Dynamicky generovaný obsah -->
            </div>
            <div class="macro-search-dropdown-footer">
                <div><span><kbd>↑</kbd><kbd>↓</kbd> posun • <kbd>↵</kbd> přejít • <kbd>esc</kbd> zavřít</span></div>
                <div><span id="macro-search-total-count">101</span> ukazatelů</div>
            </div>
        </div>
    </div>

    <!-- JAVASCRIPT: FUZZY SEARCH, KLÁVESNICE, VÝBĚR A HLAVNÍ NAVIGACE -->
    <script>
    (function() {{
        const CATALOG = {catalog_json};
        let selectedIdx = 0;
        let currentResults = [];

        function stripDiacritics(str) {{
            if (!str) return '';
            return str
                .normalize('NFD')
                .replace(/[\u0300-\u036f]/g, '')
                .toLowerCase()
                .trim();
        }}

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

        function getDoms() {{
            return {{
                wrapper: document.getElementById('macro-search-wrapper'),
                input: document.getElementById('macro-sidebar-search-input'),
                clearBtn: document.getElementById('macro-sidebar-clear-btn'),
                dropdown: document.getElementById('macro-sidebar-dropdown'),
                content: document.getElementById('macro-sidebar-dropdown-content')
            }};
        }}

        function openDropdown() {{
            const doms = getDoms();
            if (doms.dropdown) {{
                doms.dropdown.classList.add('is-open');
                renderResults(doms.input ? doms.input.value : '');
            }}
        }}

        function closeDropdown() {{
            const doms = getDoms();
            if (doms.dropdown) {{
                doms.dropdown.classList.remove('is-open');
            }}
            selectedIdx = 0;
        }}

        function navigateTo(code) {{
            const doms = getDoms();
            if (doms.input) doms.input.value = '';
            closeDropdown();

            const topWin = (typeof window.parent !== 'undefined' && window.parent && window.parent.location) ? window.parent : window;
            const url = new URL(topWin.location.href);
            url.searchParams.set('search_indicator', code);
            topWin.location.href = url.toString();
        }}

        function renderResults(query = '') {{
            const doms = getDoms();
            if (!doms.content) return;

            const cleanQ = stripDiacritics(query);
            if (doms.clearBtn) {{
                doms.clearBtn.style.display = cleanQ.length > 0 ? 'inline-block' : 'none';
            }}

            // Pokud je dotaz prázdný, zobrazíme rychlé tipy a výběr hlavních ukazatelů
            if (!cleanQ) {{
                const defaultItems = CATALOG.filter(item => [
                    'repo_rate', 'cpi_yoy', 'czgb_10y', 'cz_mortgage_rate',
                    'ecb_deposit_rate', 'bund_10y', 'eu_cpi_yoy',
                    'fed_funds_upper', 'us_10y', 'sp500_index', 'vix_index'
                ].includes(item.code));

                currentResults = defaultItems;
                selectedIdx = 0;

                let html = `
                    <div class="macro-search-quick-tips">
                        <div class="macro-search-tips-title">💡 Rychlé tipy & hledané pojmy:</div>
                        <div class="macro-search-tips-chips">
                            <span class="macro-search-chip" data-q="repo">2T Repo sazba</span>
                            <span class="macro-search-chip" data-q="cpi">Inflace CPI</span>
                            <span class="macro-search-chip" data-q="bund">10Y Bund</span>
                            <span class="macro-search-chip" data-q="pribor">PRIBOR 3M</span>
                            <span class="macro-search-chip" data-q="hypo">Hypotéky</span>
                            <span class="macro-search-chip" data-q="sp500">S&P 500</span>
                            <span class="macro-search-chip" data-q="vix">VIX</span>
                            <span class="macro-search-chip" data-q="mzdy">Mzdy</span>
                        </div>
                    </div>
                `;
                html += renderGroupedList(defaultItems, query);
                doms.content.innerHTML = html;
                bindItemsEvents();
                return;
            }}

            // Multi-token fuzzy matching od 1 znaku
            const tokens = cleanQ.split(/\s+/).filter(Boolean);
            const filtered = CATALOG.filter(item => {{
                return tokens.every(tok => item.searchText.includes(tok));
            }});

            currentResults = filtered;
            selectedIdx = 0;

            if (filtered.length === 0) {{
                doms.content.innerHTML = `
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

            doms.content.innerHTML = renderGroupedList(filtered, query);
            bindItemsEvents();
        }}

        function renderGroupedList(items, query) {{
            const groups = {{
                'CZ': {{ title: '🇨🇿 Česká republika', items: [] }},
                'EU': {{ title: '🇪🇺 Evropská unie', items: [] }},
                'US': {{ title: '🇺🇸 Spojené státy', items: [] }}
            }};

            items.forEach((item, globalIdx) => {{
                if (groups[item.region]) {{
                    groups[item.region].items.push({{ item, globalIdx }});
                }}
            }});

            let out = '';
            ['CZ', 'EU', 'US'].forEach(regKey => {{
                const grp = groups[regKey];
                if (grp.items.length > 0) {{
                    out += `
                        <div class="macro-search-group-header">
                            <span>${{grp.title}}</span>
                            <span class="macro-search-group-count">${{grp.items.length}}</span>
                        </div>
                    `;
                    grp.items.forEach(({{ item, globalIdx }}) => {{
                        const isSel = (globalIdx === selectedIdx);
                        const highlighted = highlightMatch(item.name, query);
                        out += `
                            <div class="macro-search-item ${{isSel ? 'is-selected' : ''}}"
                                 data-idx="${{globalIdx}}"
                                 data-code="${{item.code}}"
                                 id="macro-item-${{globalIdx}}">
                                <div class="macro-search-item-left">
                                    <div class="macro-search-item-name">${{highlighted}}</div>
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
                                </div>
                            </div>
                        `;
                    }});
                }}
            }});
            return out;
        }}

        function updateSelection(newIdx, shouldScroll = true) {{
            if (currentResults.length === 0) return;
            const doms = getDoms();
            if (!doms.content) return;

            const oldNode = doms.content.querySelector(`.macro-search-item[data-idx="${{selectedIdx}}"]`);
            if (oldNode) oldNode.classList.remove('is-selected');

            selectedIdx = Math.max(0, Math.min(newIdx, currentResults.length - 1));

            const newNode = doms.content.querySelector(`.macro-search-item[data-idx="${{selectedIdx}}"]`);
            if (newNode) {{
                newNode.classList.add('is-selected');
                if (shouldScroll) {{
                    newNode.scrollIntoView({{ block: 'nearest', behavior: 'smooth' }});
                }}
            }}
        }}

        function bindItemsEvents() {{
            const doms = getDoms();
            if (!doms.content) return;

            // Kliknutí na výsledky
            const items = doms.content.querySelectorAll('.macro-search-item');
            items.forEach(it => {{
                it.addEventListener('click', () => {{
                    const code = it.getAttribute('data-code');
                    if (code) navigateTo(code);
                }});
                it.addEventListener('mouseenter', () => {{
                    const idx = parseInt(it.getAttribute('data-idx'), 10);
                    if (!isNaN(idx)) updateSelection(idx, false);
                }});
            }});

            // Kliknutí na chipy
            const chips = doms.content.querySelectorAll('.macro-search-chip');
            chips.forEach(chip => {{
                chip.addEventListener('click', (e) => {{
                    e.stopPropagation();
                    const q = chip.getAttribute('data-q');
                    if (doms.input && q) {{
                        doms.input.value = q;
                        doms.input.focus();
                        renderResults(q);
                    }}
                }});
            }});
        }}

        // Globální napojení pro okamžitou odezvu HTML eventů
        window.macroSearchOnInput = function(val) {{
            openDropdown();
            renderResults(val);
        }};

        window.macroSearchOnFocus = function(val) {{
            openDropdown();
            renderResults(val || '');
        }};

        window.macroSearchOnKeydown = function(e) {{
            e.stopPropagation();
            if (e.key === 'ArrowDown') {{
                e.preventDefault();
                updateSelection(selectedIdx + 1, true);
            }} else if (e.key === 'ArrowUp') {{
                e.preventDefault();
                updateSelection(selectedIdx - 1, true);
            }} else if (e.key === 'Enter') {{
                e.preventDefault();
                if (currentResults.length > 0 && currentResults[selectedIdx]) {{
                    navigateTo(currentResults[selectedIdx].code);
                }}
            }} else if (e.key === 'Escape') {{
                e.preventDefault();
                const doms = getDoms();
                if (doms.input) doms.input.value = '';
                closeDropdown();
            }}
        }};

        window.macroSearchClear = function() {{
            const doms = getDoms();
            if (doms.input) {{
                doms.input.value = '';
                doms.input.focus();
                renderResults('');
            }}
        }};

        function init() {{
            const doms = getDoms();
            if (!doms.input) return;

            // 1. Psaní do vstupu
            doms.input.addEventListener('input', (e) => {{
                openDropdown();
                renderResults(e.target.value);
            }});

            // 2. Focus na vstup
            doms.input.addEventListener('focus', () => {{
                openDropdown();
            }});

            // 3. Klávesnice uvnitř vstupu - izolace od Streamlit hotkeys
            doms.input.addEventListener('keydown', (e) => {{
                e.stopPropagation();
                if (e.key === 'ArrowDown') {{
                    e.preventDefault();
                    updateSelection(selectedIdx + 1, true);
                }} else if (e.key === 'ArrowUp') {{
                    e.preventDefault();
                    updateSelection(selectedIdx - 1, true);
                }} else if (e.key === 'Enter') {{
                    e.preventDefault();
                    if (currentResults.length > 0 && currentResults[selectedIdx]) {{
                        navigateTo(currentResults[selectedIdx].code);
                    }}
                }} else if (e.key === 'Escape') {{
                    e.preventDefault();
                    if (doms.input) doms.input.value = '';
                    closeDropdown();
                }}
            }});

            doms.input.addEventListener('keyup', (e) => {{
                e.stopPropagation();
            }});

            doms.input.addEventListener('keypress', (e) => {{
                e.stopPropagation();
            }});

            // 4. Tlačítko pro vymazání ✕
            if (doms.clearBtn) {{
                doms.clearBtn.addEventListener('click', (e) => {{
                    e.stopPropagation();
                    if (doms.input) {{
                        doms.input.value = '';
                        doms.input.focus();
                        renderResults('');
                    }}
                }});
            }}

            // 5. Zavření při kliknutí mimo vyhledávač
            document.addEventListener('click', (e) => {{
                if (doms.wrapper && !doms.wrapper.contains(e.target)) {{
                    closeDropdown();
                }}
            }});

            // 6. Globální zkratka Ctrl+K / Cmd+K kdekoliv na stránce i v parent okně
            const handleGlobalK = (e) => {{
                if ((e.ctrlKey || e.metaKey) && (e.key === 'k' || e.key === 'K')) {{
                    e.preventDefault();
                    e.stopPropagation();
                    if (doms.input) {{
                        doms.input.focus();
                        doms.input.select();
                        openDropdown();
                    }}
                }}
            }};
            window.addEventListener('keydown', handleGlobalK);
            try {{
                if (window.parent && window.parent !== window) {{
                    window.parent.addEventListener('keydown', handleGlobalK);
                }}
            }} catch (err) {{}}
        }}

        // Inicializujeme ihned a pojistíme dalším voláním
        init();
        setTimeout(init, 100);
        setTimeout(init, 350);
    }})();
    </script>
    """

    # Vykreslení do sidebaru s povoleným JavaScriptem
    if hasattr(st.sidebar, "html"):
        st.sidebar.html(html_code, unsafe_allow_javascript=True)
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
        st.html(script, unsafe_allow_javascript=True)
    else:
        st.markdown(script, unsafe_allow_html=True)
