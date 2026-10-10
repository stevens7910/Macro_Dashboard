# 🇨🇿🇪🇺🇺🇸 Makroekonomický & Tržní Monitor: ČR & Evropská unie & USA (Streamlit)

Moderní, minimalistická a responzivní webová aplikace ve **Streamlit** inspirovaná designem finančních portálů (**Stock Analysis**). Slouží pro komplexní vizualizaci a analýzu klíčových makroekonomických ukazatelů České republiky, Evropské unie (Eurozóny), Spojených států amerických a světových akciových trhů v čase (období 2015–současnost).

Aplikace disponuje **okamžitým přepínačem mezi ČR, EU a USA** v pravém horním rohu, přičemž všechny tři ekonomiky mají **zrcadlově identickou strukturu dat**, ukazatele **jádrové inflace**, **spotřeby** a **průmyslové výroby**, vysokofrekvenční **denní devizové kurzy (FX)** včetně **PLN a GBP**, sekci **Trhy** pro akciové indexy, **finanční zpravodajství** pod hlavními ukazateli ČR a samostatnou stránku **Seznam ukazatelů & Zdroje**.

---

## 🎛️ Volba ekonomiky (Pod názvem monitoru)

Přímo pod hlavním názvem **MAKROEKONOMICKÝ & TRŽNÍ MONITOR** může uživatel jediným kliknutím přepínat mezi:
- **🇨🇿 Česká republika**: ČNB úrokový koridor, PRIBOR, celková inflace CPI & jádrová inflace, reálný a nominální HDP, maloobchodní tržby (spotřeba) a průmyslová produkce, míra nezaměstnanosti, denní devizové kurzy EUR, USD, PLN, GBP, veřejný dluh ČR, výnosová křivka CZGB & IRS.
- **🇪🇺 Evropská unie / Eurozóna**: Sazby ECB (Depozitní facilita, MRO, Mezní sazba), mezibankovní EURIBOR 3M & peněžní sazba €STR, harmonizovaná inflace HICP & jádrová inflace Core HICP, HDP Eurozóny, maloobchodní tržby (spotřeba) a průmyslová produkce EU, míra nezaměstnanosti, denní kurzy EUR/USD, EUR/CZK, EUR/PLN, EUR/GBP, veřejný dluh Eurozóny a referenční křivka Německých Bundů (2Y–30Y).
- **🇺🇸 Spojené státy**: Fed Funds Target Range, EFFR, SOFR peněžní trh, U.S. Headline & Core CPI, reálný a nominální HDP USA, maloobchodní tržby (spotřeba) a průmyslová výroba USA, míra nezaměstnanosti U-3 & NFP, Dolarový index DXY, EUR/USD, GBP/USD, USD/PLN, USD/JPY, federální dluh USA a oficiální U.S. Treasury Par Yield Curve (1M–30Y).

---

## 📖 Výkladový glosář pojmů (Glossary pro laiky i investory)

V levém postranním panelu se nachází dedikované tlačítko **📖 Glosář pojmů (Glossary)**, které uživatele přenese na samostatnou vzdělávací stránku:
- **Srozumitelný lidský jazyk:** Každý ukazatel (přes 35+ klíčových pojmů) je vysvětlen lidskou řečí a metaforami srozumitelnými i pro úplné laiky.
- **Ekonomická a finanční exaktnost:** Součástí každé karty je rigorózní makroekonomická definice, vazby na měnovou transmisi a vzorce.
- **Praktický dopad:** Přesný popis, jak se růst či pokles ukazatele projevuje na osobních financích, sazbách hypoték, úsporách, investičním portfoliu nebo kurzu měny.
- **Vyhledávání a filtry:** Okamžité fulltextové vyhledávání a filtrování podle tematických kategorií a regionů (ČR, EU, USA, Globální).
- **Přístupnost ze všech částí:** Glosář je přístupný z hlavního levého menu, s tlačítkem návratu na monitor, i jako vnořený náhled v záložce *Seznam ukazatelů & Zdroje*.

---

## 📑 Hlavní kategorie záložek (6 Tematických bloků)

Všechny ukazatele jsou **trvale aktivovány a zobrazeny** (bez nutnosti jejich ruční aktivace v postranním panelu):

1. **💳 Finanční trhy & Měna**:
   - **Měnověpolitické sazby**: ČNB (2T Repo, Lombard, Diskont, 3M PRIBOR) / ECB (Depozitní, MRO, Mezní zápůjční, 3M EURIBOR, €STR) / Fed (Fed Funds Upper/Lower, SOFR, 3M T-Bill).
   - **Výnosová křivka**: Křivky státních dluhopisů (ČR CZGB & IRS 1Y–15Y, EU Německé Bundy 2Y–30Y, USA Treasury 1M–30Y) s meziročním srovnáním posunu křivky.
   - **Měnové kurzy (FX)**: Interaktivní výběr měn (**CZK, EUR, USD, GBP, PLN**) pro čistý a přehledný graf, denní data vs. měsíční agregace, okamžitý download CSV.
2. **🏛️ Reálná ekonomika & Práce**:
   - **HDP**: Čtvrtletní reálný růst (YoY %) a nominální objem (mld. CZK / EUR / USD).
   - **Inflace**: Celková inflace (Headline CPI / HICP) vs. **Jádrová inflace (Core CPI / Core HICP)**, reálná repo/depo sazba a inflační cíl 2,0 %.
   - **Průmysl a spotřeba**: Maloobchodní tržby (spotřeba domácností YoY %) vs. Index průmyslové produkce (YoY %).
   - **Trh práce**: Míra nezaměstnanosti (ČR / EU / USA U-3 & Nonfarm Payrolls).
3. **📈 Trhy (Akciové indexy)**:
   - **Vzájemné srovnání indexů**: Normalizovaná kumulativní výkonnost v % (od počátku vybraného období) nebo rebase na bázi 100 pro:
     - 🇨🇿 **Index PX** (Burza cenných papírů Praha / BCPP)
     - 🇪🇺 **Euro Stoxx 50** (Přední korporátní lídři Eurozóny)
     - 🇺🇸 **S&P 500** (Široký benchmark amerického akciového trhu)
     - 🇺🇸 **NASDAQ Composite** (Globální technologický a inovační lídr)
   - **Detailní pohledy na jednotlivé indexy**: Samostatné cenové grafy, 12měsíční klouzavý průměr, rozpětí minima/maxima a statistiky zhodnocení.
4. **🌐 Veřejné finance & Svět**:
   - **Veřejný dluh & Saldo**: Konsolidovaný veřejný dluh k HDP (% HDP, maastrichtské pravidlo 60 %) a kvartální schodky/přebytky rozpočtu.
   - **Mezinárodní srovnání**: Sovereign výnosové spready 10Y dluhopisů (ČR vs. Německo, ČR vs. USA, Německo vs. USA) v bazických bodech (bps).
5. **📋 Data a export**:
   - Datový průzkumník s českými popisky, filtrováním a okamžitým stažením kompletního datového setu ve formátu CSV.
6. **📖 Seznam ukazatelů & Zdroje (Katalog metadat)**:
   - Strukturovaný katalog všech 80+ makroekonomických ukazatelů s filtry podle země, kategorie a fulltextovým vyhledáváním.
   - U každého indikátoru je uveden kód, jednotka, periodicita, oficiální primární datový zdroj a metodická definice.
   - Možnost stažení kompletního katalogu metadat do CSV.

---

## 📰 Kontextové finanční zpravodajství (CZ Indikátory)

Přímo pod hlavními 4 metrickými boxy v každé oblasti pro Českou republiku se zobrazuje **karta aktuálního finančního zpravodajství**:
- **Datum a instituce:** Čas poslední změny či zveřejnění dat.
- **Ověřený renomovaný zdroj:** Česká národní banka (tiskové konference BR ČNB), Český statistický úřad (Rychlé informace), Ministerstvo financí ČR, Burza cenných papírů Praha, Patria Finance, ČTK.
- **Důvod změny & klíčové faktory:** Co přesně vedlo ke změně sazby, kurzu či makroekonomického indikátoru.
- **Makroekonomický kontext:** Širší dopady na hospodářství, mzdový vývoj, inflační očekávání a trhy.

---

## 🎨 Vylepšení uživatelského rozhraní (UI & UX)

- **Přesunutí volby ekonomiky pod název:** Záložky pro volbu ČR, EU a USA jsou přehledně umístěny přímo pod titulem monitoru.
- **Zmenšené a vyvážené písmo 4 hlavních boxů:** Font metrických hodnot v KPI kartách byl zmenšen a zarovnán pro čisté a kompaktní zobrazení bez přetékání jednotek.
- **Zvýrazněné hlavní kategorie:** Kategorie záložek mají jemné podbarvení kontejneru (`#e2e8f0`), kontrastní tmavomodré písmo (`#1e3a8a`) a sytě tmavomodrou aktivní záložku s bílým textem.
- **Informace o aktuálnosti dat u obnovení:** Přímo pod tlačítkem *„🔄 Obnovit data (Vymazat cache)“* se zobrazuje přesné datum, ke kterému jsou načtena makroekonomická data, datum denních FX trhů a čas posledního stažení.
- **Trvalá aktivace všech indikátorů**: Všechny ukazatele se načítají a zobrazují automaticky.
- **Skrytá detailní tabulka indikátorů**: Původní rozsáhlá tabulka metrik je ve výchozím stavu elegantně sbalena v expanderu.
- **Filtrování měn na FX grafu**: Uživatel si může v multiselectu zvolit pouze ty měny, které ho zajímají (`CZK`, `USD`, `GBP`, `EUR`, `PLN`).
- **Zdroje dat u každého grafu**: Každý graf obsahuje přesnou citaci primárního zdroje dat.

---

## 🏗️ Architektura a zdroje dat

- **Primární Live REST API**:
  - **Česká národní banka (ČNB)**: Otevřená REST API pro denní devizové kurzy (EUR, USD, PLN, GBP, JPY, CHF) a časové řady měnových sazeb.
  - **Eurostat REST API**: JSON API pro celkovou i **jádrovou inflaci (Core HICP)**, HDP, míru nezaměstnanosti, veřejný dluh a 10Y referenční výnosy.
  - **U.S. Department of the Treasury (`home.treasury.gov`)**: Oficiální XML API pro denní výnosové křivky USA (1M až 30Y).
  - **Yahoo Finance API**: Měsíční a denní kotace akciových indexů (^GSPC, ^IXIC, ^STOXX50E, ^PX).
  - **FRED API (St. Louis Fed)**: Volitelná integrace pro americké časové řady.
- **Odolný Fallback model**:
  - Při výpadku konektivity nebo nedostupnosti externích serverů se automaticky bez přerušení chodu aktivuje interní model 2015–2026 pro všechny ukazatele.

---

## 📱 Mobilní optimalizace a instalace na Android (PWA)

- **Responzivní design**:
  - Automatické sbalení postranního panelu na mobilních telefonech (`initial_sidebar_state="auto"`).
  - Dotykové ovládání grafů Plotly bez nechtěného zasekávání posunu stránky (`scrollZoom: False`, `responsive: True`).
  - Flexibilní horizontální posun záložek (`overflow-x: auto`, dotykový kinetický scroll).
- **Instalace na Android**:
  1. Otevřete aplikaci v mobilním Google Chrome.
  2. Klepněte na tři tečky vpravo nahoře.
  3. Zvolte **„Přidat na plochu“** (nebo *„Nainstalovat aplikaci“*).
  4. Aplikace se spouští v celoobrazovkovém režimu s vlastní ikonou.

---

## 🚀 Rychlé spuštění

```bash
# Instalace závislostí
pip install -r requirements.txt

# Spuštění aplikace
streamlit run app.py
```
Aplikace se otevře na adrese `http://localhost:8501`.
