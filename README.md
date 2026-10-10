# 🇨🇿🇺🇸 Český & US Makroekonomický Dashboard (Streamlit)

Moderní, minimalistická a responzivní webová aplikace ve **Streamlit** inspirovaná designem finančních portálů (**Stock Analysis**). Slouží pro komplexní vizualizaci a analýzu klíčových makroekonomických ukazatelů České republiky a Spojených států v čase (období 2015–současnost).

Aplikace disponuje **okamžitým přepínačem mezi Českou republikou (ČR) a Spojenými státy (USA)** v pravém horním rohu, přičemž obě ekonomiky mají **zrcadlově identickou strukturu dat**, vysokofrekvenční **denní devizové kurzy (FX)** a optimalizaci pro mobilní zařízení (PWA).

---

## 🎛️ Volba ekonomiky (Vpravo nahoře)

Uživatel může v pravém horním rohu stránky jediným kliknutím přepínat mezi:
- **🇨🇿 Česká republika**: ČNB úrokový koridor, PRIBOR, inflace CPI, HDP v mld. Kč, nezaměstnanost, denní EUR/CZK a USD/CZK, veřejný dluh ČR, výnosová křivka CZGB & IRS.
- **🇺🇸 Spojené státy**: Fed Funds Target Range, EFFR, SOFR peněžní trh, U.S. Headline & Core CPI, reálný a nominální HDP USA, míra nezaměstnanosti U-3 & NFP, Dolarový index DXY, EUR/USD, GBP/USD, USD/JPY, federální dluh USA a oficiální U.S. Treasury Par Yield Curve (1M–30Y).

---

## 📊 Sledované ukazatele

### 🇨🇿 Česká republika (CZ)
1. **Měnová politika**: 2T Repo sazba ČNB, Diskontní sazba, Lombardní sazba.
2. **Mezibankovní trh**: Sazby PRIBOR (1M, 3M, 6M).
3. **Cenová hladina**: Meziroční inflace (CPI / HICP) v %, 2% inflační cíl a toleranční pásmo (1–3 %).
4. **HDP**: Reálný meziroční růst HDP (%) a nominální HDP v běžných cenách (mld. CZK).
5. **Trh práce**: Míra nezaměstnanosti (ILO / Eurostat) v %.
6. **Měnové kurzy (FX - Denní data)**: Denní fixace devizového trhu ČNB pro **EUR/CZK** a **USD/CZK**.
7. **Fiskální politika**: Konsolidovaný dluh vládních institucí k HDP (% HDP, limit 60 %) a saldo státního rozpočtu.
8. **Výnosová křivka**: Státní dluhopisy ČR (CZGB 1Y–15Y) a úrokové swapy (CZK IRS 1Y–15Y) + sklon křivky (10Y − 2Y).

### 🇺🇸 Spojené státy (USA - Stejná datová struktura)
1. **Měnová politika**: Fed Funds Target Rate (horní a dolní limit koridoru), efektivní sazba EFFR.
2. **Peněžní trh**: SOFR (Secured Overnight Financing Rate) a U.S. Treasury Bills (1M, 3M).
3. **Cenová hladina**: U.S. Headline CPI (%) a Jádrová inflace Core CPI (%) s 2% inflačním cílem Fedu.
4. **HDP**: Reálný meziroční růst HDP USA (%) a roční nominální HDP (mld. USD).
5. **Trh práce**: Oficiální míra nezaměstnanosti USA (U-3) a tvorba pracovních míst (Nonfarm Payrolls).
6. **Měnové kurzy (FX - Denní data)**: **U.S. Dollar Index (DXY)**, **EUR/USD**, **GBP/USD**, **USD/JPY**, **USD/CHF**.
7. **Fiskální politika**: Hrubý federální dluh USA (mld. USD), dluh k HDP (% HDP) a federální deficit.
8. **Výnosová křivka**: Oficiální U.S. Treasury Par Yield Curve (1M, 3M, 6M, 1Y, 2Y, 3Y, 5Y, 7Y, 10Y, 20Y, 30Y) a sklon křivky (10Y − 2Y, indikátor recese).

### 🌍 Mezinárodní srovnání (ČR vs. USA)
- **Úrokový diferenciál**: 2T Repo ČNB vs. Fed Funds Target Rate.
- **Inflační diferenciál**: Meziroční CPI ČR vs. USA.
- **Sovereign výnosový spread**: 10Y CZGB minus 10Y US Treasury (v bazických bodech bps).

---

## 🏗️ Architektura a zdroje dat

- **Primární Live zdroje**:
  - **Česká národní banka (ČNB)**: Otevřená REST API pro denní fixace měnových kurzů (EUR, USD, GBP, JPY, CHF) a časové řady sazeb.
  - **Eurostat REST API**: JSON API pro HICP inflaci ČR, HDP, nezaměstnanost a veřejný dluh.
  - **U.S. Department of the Treasury (`home.treasury.gov`)**: Oficiální otevřené XML API pro denní výnosové křivky USA (1M až 30Y).
  - **FRED API (St. Louis Fed)**: Volitelná integrace pro přímé ověřování dat.
- **Fallback model**:
  - Při nedostupnosti sítě nebo selhání API systém automaticky a bez pádu aktivuje interní model 2015–2026.

---

## 📱 Mobilní optimalizace a instalace na Android (PWA)

- **Responzivní design**:
  - Automatické sbalení postranního panelu na mobilních telefonech (`initial_sidebar_state="auto"`).
  - Dotykové ovládání grafů Plotly bez nechtěného zasekávání posunu stránky (`scrollZoom: False`, `responsive: True`).
  - Media queries pro malé displeje (360–420 px).
- **Instalace na Android**:
  1. Otevřete aplikaci v mobilním Google Chrome.
  2. Klepněte na tři tečky vpravo nahoře.
  3. Zvolte **„Přidat na plochu“** (nebo *„Nainstalovat aplikaci“*).
  4. Aplikace se spouští v celoobrazovkovém nativním režimu s vlastní ikonou.

---

## 🚀 Rychlé spuštění

```bash
# Instalace závislostí
pip install -r requirements.txt

# Spuštění aplikace
streamlit run app.py
```
Aplikace se otevře na adrese `http://localhost:8501`.
