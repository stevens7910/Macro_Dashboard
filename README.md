# 🇨🇿🇪🇺🇺🇸 Makroekonomický Monitor: ČR & Evropská unie & USA (Streamlit)

Moderní, minimalistická a responzivní webová aplikace ve **Streamlit** inspirovaná designem finančních portálů (**Stock Analysis**). Slouží pro komplexní vizualizaci a analýzu klíčových makroekonomických ukazatelů České republiky, Evropské unie (Eurozóny) a Spojených států amerických v čase (období 2015–současnost).

Aplikace disponuje **okamžitým přepínačem mezi ČR, EU a USA** v pravém horním rohu, přičemž všechny tři ekonomiky mají **zrcadlově identickou strukturu dat**, ukazatele **jádrové inflace**, **spotřeby** a **průmyslové výroby**, vysokofrekvenční **denní devizové kurzy (FX)** včetně **PLN a GBP** a optimalizaci pro mobilní zařízení (PWA).

---

## 🎛️ Volba ekonomiky (Vpravo nahoře)

Uživatel může v pravém horním rohu stránky jediným kliknutím přepínat mezi:
- **🇨🇿 Česká republika**: ČNB úrokový koridor, PRIBOR, celková inflace CPI & jádrová inflace, reálný a nominální HDP, maloobchodní tržby (spotřeba) a průmyslová produkce, míra nezaměstnanosti, denní devizové kurzy EUR, USD, PLN, GBP, veřejný dluh ČR, výnosová křivka CZGB & IRS.
- **🇪🇺 Evropská unie / Eurozóna**: Sazby ECB (Depozitní facilita, MRO, Mezní sazba), mezibankovní EURIBOR 3M & peněžní sazba €STR, harmonizovaná inflace HICP & jádrová inflace Core HICP, HDP Eurozóny, maloobchodní tržby (spotřeba) a průmyslová produkce EU, míra nezaměstnanosti, denní kurzy EUR/USD, EUR/CZK, EUR/PLN, EUR/GBP, veřejný dluh Eurozóny a referenční křivka Německých Bundů (2Y–30Y).
- **🇺🇸 Spojené státy**: Fed Funds Target Range, EFFR, SOFR peněžní trh, U.S. Headline & Core CPI, reálný a nominální HDP USA, maloobchodní tržby (spotřeba) a průmyslová výroba USA, míra nezaměstnanosti U-3 & NFP, Dolarový index DXY, EUR/USD, GBP/USD, USD/PLN, USD/JPY, federální dluh USA a oficiální U.S. Treasury Par Yield Curve (1M–30Y).

---

## 📊 Sledované ukazatele a shodná struktura (11 Záložek)

Pro každou z ekonomik je k dispozici 11 logicky provázaných záložek:

1. **Sazby (ČNB / ECB / Fed)**: Klíčový měnověpolitický koridor centrální banky a referenční tržní sazby (PRIBOR, EURIBOR, SOFR).
2. **Inflace (Headline & Jádrová inflace)**:
   - Celková spotřebitelská inflace (CPI / HICP).
   - **Jádrová inflace (Core CPI / Core HICP)** očištěná o volatilní položky (energie, potraviny).
   - Reálná úroková míra a inflační cíl 2,0 %.
3. **HDP**: Čtvrtletní reálný meziroční růst (%) a nominální objem (mld. CZK / EUR / USD).
4. **Průmysl a spotřeba (Ekonomická aktivita)**:
   - **Maloobchodní tržby (Spotřeba YoY %)**.
   - **Index průmyslové produkce (YoY %)**.
5. **Trh práce / Nezaměstnanost**: Obecná míra nezaměstnanosti (ILO / Eurostat / U-3 BLS) a tvorba pracovních míst.
6. **Měnové kurzy (FX - Denní data)**:
   - ČR: EUR/CZK, USD/CZK, **PLN/CZK**, **GBP/CZK**.
   - EU: EUR/USD, EUR/CZK, **EUR/PLN**, **EUR/GBP**.
   - USA: **Dolarový index (DXY)**, EUR/USD, **GBP/USD**, **USD/PLN**, USD/JPY.
   - Možnost přepnutí mezi denními daty a měsíční agregací + okamžitý download CSV.
7. **Veřejný dluh & Fiskální politika**: Konsolidovaný veřejný dluh k HDP (% HDP, maastrichtský limit 60 %) a kvartální saldo rozpočtu.
8. **Výnosová křivka**: Časová struktura výnosů státních dluhopisů (ČR CZGB & IRS, EU Německé Bundy 2Y–30Y, USA Treasury 1M–30Y) a sklon křivky (10Y − 2Y).
9. **Mezinárodní srovnání**: Sazbové diferenciály a mezinárodní sovereign výnosové spready (v bps).
10. **Všechny grafy**: Konsolidovaný pohled na všechny klíčové grafy na jedné ploše.
11. **Data a export**: Interaktivní tabulka s filtrovanými daty v českých názvech a jednoklikový CSV export.

---

## 🏗️ Architektura a zdroje dat

- **Primární Live REST API**:
  - **Česká národní banka (ČNB)**: Otevřená REST API pro denní devizové kurzy (EUR, USD, PLN, GBP, JPY, CHF) a časové řady měnových sazeb.
  - **Eurostat REST API**: JSON API pro celkovou i **jádrovou inflaci (Core HICP)**, HDP, míru nezaměstnanosti, veřejný dluh a 10Y referenční výnosy.
  - **U.S. Department of the Treasury (`home.treasury.gov`)**: Oficiální XML API pro denní výnosové křivky USA (1M až 30Y).
  - **FRED API (St. Louis Fed)**: Volitelná integrace pro přímé ověřování amerických časových řad.
- **Odolný Fallback model**:
  - Při výpadku konektivity nebo nedostupnosti externích serverů se automaticky bez přerušení chodu aktivuje interní model 2015–2026 pro všechny ukazatele.

---

## 📱 Mobilní optimalizace a instalace na Android (PWA)

- **Responzivní design**:
  - Automatické sbalení postranního panelu na mobilních telefonech (`initial_sidebar_state="auto"`).
  - Dotykové ovládání grafů Plotly bez nechtěného zasekávání posunu stránky (`scrollZoom: False`, `responsive: True`).
  - Flexibilní horizontální posun záložek (`overflow-x: auto`, dotykový kinetický scroll).
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
