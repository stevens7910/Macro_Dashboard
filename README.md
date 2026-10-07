# 🇨🇿 Český Makroekonomický Dashboard (Streamlit)

Moderní, responzivní a modulární webová aplikace ve **Streamlit** pro komplexní vizualizaci a analýzu klíčových makroekonomických ukazatelů České republiky v čase (období 2015–současnost).

---

## 📊 Sledované ukazatele

1. **Inflace (CPI)** – Meziroční míra inflace (HICP / národní index spotřebitelských cen) v %.
2. **Reálný růst HDP** – Meziroční změna HDP ve stálých cenách (řetězené objemy) v %.
3. **Nominální HDP** – Kvartální objem HDP v běžných cenách v miliardách Kč (mld. CZK).
4. **Hlavní sazby ČNB**:
   - **2T repo sazba** (klíčový měnověpolitický nástroj pro stahování likvidity)
   - **Diskontní sazba** (spodní mez koridoru – depozitní facilita)
   - **Lombardní sazba** (horní mez koridoru – zápůjční facilita)
5. **PRIBOR sazby** – Referenční sazby mezibankovního trhu peněz (**1M**, **3M** a **6M PRIBOR**).
6. **Míra nezaměstnanosti** – Sezónně očištěná obecná míra nezaměstnanosti dle ILO / Eurostat v %.

---

## 🏗️ Architektura a zdroje dat

Aplikace je navržena podle principů moderního data engineeringu:
- **Třída `DataLoader` (`data_loader.py`)**: Dedikovaný modul pro asynchronní/synchronní stahování, parsing a sjednocení časových řad.
- **Cachování `@st.cache_data(ttl=3600)`**: Výsledná data jsou v mezipaměti uložena po dobu 1 hodiny, což zaručuje okamžitou odezvu aplikace při změnách filtrů.
- **Primární Live zdroje**:
  - **Česká národní banka (ČNB)**: Otevřená REST API pro denní fixace PRIBOR a oficiální časové řady měnových sazeb.
  - **Eurostat REST API (`geo=CZ`)**: Rychlá a stabilní JSON API pro HICP inflaci, čtvrtletní národní účty (HDP) a měsíční nezaměstnanost.
  - **FRED API**: Možnost zadat vlastní API klíč pro data ze St. Louis Fed.
- **Odolnost proti výpadku (Fallback Resilience)**:
  - Pokud je síť nedostupná nebo některé API selže, aplikace **automaticky a bez pádu** aktivuje interní historický model (2015–současnost).
  - V postranním panelu uživatel vždy přehledně vidí aktuální režim:
    - 🟢 `Živá data (ČNB Open Data & Eurostat REST API)`
    - 🟡 `Kombinovaný režim (Částečná Live API + Fallback)`
    - 🟠 `Fallback Model (Historická data 2015–2026)`

---

## 🚀 Rychlé spuštění

### 1. Požadavky
- Python 3.10, 3.11 nebo 3.12
- Nainstalovaný nástroj `pip` nebo `uv`

### 2. Instalace závislostí
```bash
pip install -r requirements.txt
```
nebo přes ultra-rychlý `uv`:
```bash
uv pip install -r requirements.txt
```

### 3. Spuštění aplikace
```bash
streamlit run app.py
```
Aplikace se automaticky otevře ve vašem webovém prohlížeči na adrese `http://localhost:8501`.

---

## 🖥️ Uživatelské rozhraní (UI)

- **Boční panel (Sidebar)**:
  - **Časový horizont**: Rychlé volby (*1 rok*, *3 roky*, *5 let*, *Celá historie od 2015*) nebo vlastní výběr z kalendáře.
  - **Frekvence**: Přepínač mezi *Měsíční (Monthly)* a *Kvartální (Quarterly)* agregací.
  - **Výběr indikátorů**: Multiselect pro zobrazení/skrytí libovolné metriky.
  - **Zdroje & API**: Možnost zadat FRED API klíč nebo vynutit offline Fallback režim.
  - **Tlačítko obnovy**: `Obnovit data (Vymazat cache)` pro vynucené znovunačtení.
- **Hlavní plocha**:
  - **4 KPI karty (`st.metric`)**: Poslední známé hodnoty a mezidobé delty pro Repo sazbu, Inflaci CPI, Růst HDP a Nezaměstnanost.
  - **Graf 1: Měnová politika a Inflace**: Úrokový koridor ČNB (Repo se schodovitou geometrií, Diskont a Lombard s jemným podbarvením koridoru), sazby PRIBOR a CPI inflace na sekundární ose Y s 2% inflačním cílem.
  - **Graf 2: Výkon ekonomiky (HDP)**: Kombinovaný bar + line graf (nominální objem v mld. CZK + reálný meziroční růst v %).
  - **Graf 3: Trh práce**: Míra nezaměstnanosti s vyznačením dlouhodobého průměru a historických extrémů.
  - **Data Explorer & Export**: Přehledná tabulka s českou lokalizací čísel a tlačítko pro stažení CSV s kódováním UTF-8 BOM pro bezchybné zobrazení v Excelu.

---

## 📂 Struktura projektu

```
Makro_Dashboard/
├── app.py              # Hlavní Streamlit aplikace a UI logika
├── data_loader.py      # DataLoader modul: API napojení, fallback model, transformace
├── requirements.txt    # Výčet python balíčků
└── README.md           # Kompletní dokumentace projektu
```
