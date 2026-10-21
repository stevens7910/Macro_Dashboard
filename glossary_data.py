"""
glossary_data.py
================
Komplexní metodický a vzdělávací výkladový glosář makroekonomických a finančních pojmů
pro Makroekonomický & Tržní Monitor (ČR, EU, USA a akciové trhy).

Obsahuje exaktní finanční a ekonomické definice uzpůsobené pro laické i pokročilé čtenáře,
včetně praktického významu pro osobní finance, hypotéky, investice a podnikání.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional
import streamlit as st

GLOSSARY_VERSION = "2026.10.16.v3"


@dataclass
class GlossaryItem:
    """Reprezentace položky ve výkladovém glosáři."""
    term: str
    category: str
    region: str  # "ČR", "EU", "USA", "Globální"
    simple_explanation: str
    economic_meaning: str
    practical_impact: str
    primary_source: str
    frequency: str


GLOSSARY_ITEMS: List[GlossaryItem] = [
    # =========================================================================
    # 1. MĚNOVÁ POLITIKA & ÚROKOVÉ SAZBY
    # =========================================================================
    GlossaryItem(
        term="2T Repo sazba ČNB",
        category="Měnová politika & Úrokové sazby",
        region="ČR",
        simple_explanation=(
            "Klíčová úroková sazba v České republice. Představuje úrok, za který si komerční banky (např. ČSOB, Česká spořitelna, Komerční banka) "
            "mohou bezpečně uložit své přebytečné peníze u České národní banky na dobu dvou týdnů (2 týdny = 2T). Když ČNB tuto sazbu zvýší, "
            "všechny banky zdraží půjčky a hypotéky, ale zároveň začnou lépe úročit spořicí účty. Když ji sníží, půjčky zlevní a spoření nese méně."
        ),
        economic_meaning=(
            "Základní nástroj transmisního mechanismu měnové politiky ČNB. Prostřednictvím repo operací (repurchase agreements) centrální banka "
            "stahuje přebytečnou likviditu z mezibankovního trhu proti zástavě státních pokladničních poukázek. Výše repo sazby přímo ovlivňuje cenu "
            "krátkodobých peněz na mezibankovním trhu (PRIBOR), diskontní faktory v ekonomice a úvěrovou expanzi."
        ),
        practical_impact=(
            "Přímo určuje výši úroků na spořicích účtech občanů a ovlivňuje cenu hypotečních a spotřebitelských úvěrů. "
            "Její růst tlumí spotřebu a inflaci, ale zdražuje financování firmám; její pokles naopak stimuluje investice a hospodářský růst."
        ),
        primary_source="Česká národní banka (ČNB) – Rozhodnutí Bankovní rady (8× ročně)",
        frequency="8× ročně (plánovaná měnová zasedání ČNB)"
    ),
    GlossaryItem(
        term="Diskontní sazba ČNB",
        category="Měnová politika & Úrokové sazby",
        region="ČR",
        simple_explanation=(
            "Spodní mantinel úrokových sazeb v ČR. Jde o minimální úrok, který komerční banka dostane od ČNB, když u ní nechá peníze ležet přes noc "
            "(tzv. depozitní facilita). Na mezibankovním trhu tak úroky nikdy neklesnou pod tuto hodnotu, protože banky nemají důvod půjčovat někomu "
            "za méně, než kolik jim garantuje ČNB bez jakéhokoliv rizika."
        ),
        economic_meaning=(
            "Tvoří spodní hranici asymetrického či symetrického koridoru úrokových sazeb ČNB (tzv. standing facilities). Obvykle je nastavena "
            "100 bazických bodů (1,00 p.b.) pod dvoutýdenní repo sazbou. Zabraňuje propadu krátkodobých tržních sazeb pod požadovanou mez."
        ),
        practical_impact=(
            "Slouží jako minimální technické dno pro úročení likvidity v českém bankovním systému a používá se i v legislativě při výpočtu zákonných úroků z prodlení."
        ),
        primary_source="Česká národní banka (ČNB)",
        frequency="8× ročně (spolu s repo sazbou)"
    ),
    GlossaryItem(
        term="Lombardní sazba ČNB",
        category="Měnová politika & Úrokové sazby",
        region="ČR",
        simple_explanation=(
            "Horní strop úrokových sazeb v ČR. Pokud komerční bance dojdou peníze a potřebuje si od ČNB akutně půjčit na jeden den přes noc, "
            "musí zaplatit právě lombardní sazbu a navíc ručit cennými papíry. Je to jakási 'nouzová půjčka s přirážkou', proto tržní úroky nikdy "
            "nepřekročí tuto hodnotu."
        ),
        economic_meaning=(
            "Představuje horní hranici úrokového koridoru centrální banky (tzv. marginální zápůjční facilita). Standardně je ukotvena "
            "100 bazických bodů (1,00 p.b.) nad 2T repo sazbou. Zaručuje, že banky se v případě náhlého šoku likvidity nedostanou do insolvence, "
            "ale penalizuje neopatrné řízení likvidity."
        ),
        practical_impact=(
            "Limituje maximální volatilitu na jednodenním peněžním trhu a zajišťuje absolutní stabilitu mezibankovního zúčtovacího systému CERTIS."
        ),
        primary_source="Česká národní banka (ČNB)",
        frequency="8× ročně (spolu s repo sazbou)"
    ),
    GlossaryItem(
        term="PRIBOR (Prague Interbank Offered Rate)",
        category="Měnová politika & Úrokové sazby",
        region="ČR",
        simple_explanation=(
            "Úrok, za který si české komerční banky půjčují peníze mezi sebou navzájem. Zkratka znamená pražskou mezibankovní nabídkovou sazbu. "
            "Nejvýznamnější je PRIBOR 3M (tříměsíční). Právě od této sazby se přímo odvíjí úročení většiny firemních úvěrů, provozních kontokorentů "
            "a hypoték s plovoucí sazbou."
        ),
        economic_meaning=(
            "Klíčový referenční benchmark českého peněžního trhu vypočítávaný administrátorem na základě kotací referenčních bank. "
            "Zahrnuje v sobě očekávání budoucího vývoje repo sazby ČNB po dobu trvání tenoru a prémii za úvěrové riziko a likviditu."
        ),
        practical_impact=(
            "Když roste PRIBOR 3M, firmám okamžitě rostou měsíční úrokové náklady na jejich úvěry a domácnostem s variabilní hypotékou stoupá splátka. "
            "Pokles PRIBORu naopak firmám okamžitě uvolňuje cash flow."
        ),
        primary_source="Česká národní banka (ČNB) & Czech Financial Benchmark Facility (CFBF)",
        frequency="Denní fixace (v pracovní dny kolem 13:00)"
    ),
    GlossaryItem(
        term="Depozitní sazba ECB (Deposit Facility Rate - DFR)",
        category="Měnová politika & Úrokové sazby",
        region="EU",
        simple_explanation=(
            "Nejdůležitější úroková sazba pro celou Eurozónu. Určuje, kolik Evropská centrální banka ve Frankfurtu platí komerčním bankám za to, "
            "že si u ní přes noc bezpečně uloží eura. V podmínkách obrovského přebytku hotovosti v evropském bankovním systému je to právě tato sazba, "
            "která řídí cenu eura a ovlivňuje úvěry v Německu, Francii i na Slovensku."
        ),
        economic_meaning=(
            "Základní operační cíl měnové politiky Eurosystému. V prostředí strukturálního přebytku bankovních rezerv tvoří spodní část koridoru, "
            "avšak de facto představuje dominantní kotvu krátkodobých úrokových sazeb a peněžního trhu v měně EUR."
        ),
        practical_impact=(
            "Rozhoduje o síle eura vůči dolaru a české koruně. Když ECB sazbu sníží, oslabuje to euro a zlevňuje eurové úvěry, které české firmy "
            "často využívají pro financování svých exportů."
        ),
        primary_source="Evropská centrální banka (ECB)",
        frequency="Zasedání Rady guvernérů ECB (každých 6 týdnů)"
    ),
    GlossaryItem(
        term="EURIBOR (Euro Interbank Offered Rate)",
        category="Měnová politika & Úrokové sazby",
        region="EU",
        simple_explanation=(
            "Evropská obdoba PRIBORu. Průměrný úrok, za který si přední evropské banky půjčují eura mezi sebou na mezibankovním trhu. "
            "Naprostá většina hypoték v zemích platících eurem (např. na Slovensku, ve Španělsku či Itálii) je přímo navázána na 3M nebo 6M EURIBOR."
        ),
        economic_meaning=(
            "Evropský referenční úrokový benchmark splňující nařízení BMR (EU Benchmark Regulation). Slouží jako podkladové aktivum pro finanční "
            "deriváty, úrokové swapy (EUR IRS) a dluhové instrumenty v hodnotě desítek bilionů eur."
        ),
        practical_impact=(
            "Pro české firmy čerpající eurové úvěry je 3M EURIBOR základní složkou jejich úrokové marže. Jeho růst zdražuje eurové financování."
        ),
        primary_source="European Money Markets Institute (EMMI) & ECB",
        frequency="Denní fixace v 11:00 SEČ"
    ),
    GlossaryItem(
        term="€STR (Euro Short-Term Rate)",
        category="Měnová politika & Úrokové sazby",
        region="EU",
        simple_explanation=(
            "Oficiální bezriziková jednodenní sazba eura, kterou každý den počítá ECB ze skutečně uskutečněných půjček mezi bankami. "
            "Nahradila dřívější starší sazbu EONIA a je považována za nejčistší měřítko ceny peněz v Eurozóně na jeden den."
        ),
        economic_meaning=(
            "Risk-free rate (RFR) pro měnu EUR vypočítaná z reálných transakcí nezajištěného velkoobchodního peněžního trhu. "
            "Slouží jako základní stavební kámen moderní diskontní křivky pro oceňování finančních instrumentů OIS (Overnight Indexed Swaps)."
        ),
        practical_impact=(
            "Používají ji banky a fondy pro přesné oceňování derivátů a jako stabilní kotvu peněžních trhů Eurozóny."
        ),
        primary_source="Evropská centrální banka (ECB)",
        frequency="Denně v 08:00 SEČ za předchozí bankovní den"
    ),
    GlossaryItem(
        term="Fed Funds Target Range",
        category="Měnová politika & Úrokové sazby",
        region="USA",
        simple_explanation=(
            "Cílové pásmo úrokových sazeb americké centrální banky (Federal Reserve / Fed). Udává se vždy jako rozmezí (např. 4,25 % – 4,50 %). "
            "Jedná se o nejvlivnější úrokovou sazbu na planetě, protože americký dolar je hlavní světovou rezervní měnou. Co udělá Fed, to obvykle "
            "určuje směr pro světové burzy, ceny komodit i ostatní centrální banky."
        ),
        economic_meaning=(
            "Cílové koridorové rozpětí pro sazbu federal funds rate (jednodenní mezibankovní zápůjčky rezerv u Federálního rezervního systému). "
            "Fed toto pásmo udržuje kombinací úročení rezervních zůstatků (IORB) a reverzních repo operací (ON RRP)."
        ),
        practical_impact=(
            "Zvýšení sazeb Fedu stahuje globální kapitál do dolarových aktiv, posiluje dolar a může způsobit pokles na akciových trzích. "
            "Snížení sazeb naopak uvolňuje likviditu a podporuje růst akcií a komodit."
        ),
        primary_source="Federal Reserve Board (FOMC – Federální výbor pro otevřený trh)",
        frequency="8× ročně (zasedání FOMC)"
    ),
    GlossaryItem(
        term="SOFR (Secured Overnight Financing Rate)",
        category="Měnová politika & Úrokové sazby",
        region="USA",
        simple_explanation=(
            "Moderní americká bezriziková sazba, která po finančních skandálech definitivně nahradila nechvalně známý LIBOR. Měří průměrný úrok "
            "z jednodenních půjček v dolarech, které jsou plně jištěny americkými státními dluhopisy (proto je 'zajištěná' – secured)."
        ),
        economic_meaning=(
            "Objemově největší referenční sazba na světě, denně podložená transakcemi přesahujícími 1 bilion USD. Vychází ze skutečných repo transakcí "
            "s kolaterálem U.S. Treasury a stala se globálním standardem pro dolarové úvěry, dluhopisy a deriváty."
        ),
        practical_impact=(
            "Odráží okamžitou dostupnost a cenu likvidity na Wall Street a používá se pro kalkulaci všech moderních dolarových finančních kontraktů."
        ),
        primary_source="Federal Reserve Bank of New York (NY Fed)",
        frequency="Každý pracovní den v 08:00 EST"
    ),

    # =========================================================================
    # 2. DLUHOPISY & VÝNOSOVÉ KŘIVKY
    # =========================================================================
    GlossaryItem(
        term="Výnos do splatnosti (Yield to Maturity - YTM)",
        category="Dluhopisy & Výnosové křivky",
        region="Globální",
        simple_explanation=(
            "Celkový roční výnos v procentech, který investor získá, pokud koupí dluhopis za dnešní tržní cenu a ponechá si ho až do dne jeho splacení. "
            "Platí zásadní pravidlo finančního světa: když tržní cena dluhopisu klesá, jeho výnos do splatnosti roste (a naopak)."
        ),
        economic_meaning=(
            "Vnitřní výnosové procento (IRR) toku budoucích hotovostních příjmů z dluhopisu (kupónové platby + nominální hodnota při splatnosti) "
            "vzhledem k jeho aktuální nákupní ceně (dirty price). Představuje klíčovou diskontní míru trhu."
        ),
        practical_impact=(
            "Určuje cenu, za jakou si státy a korporace půjčují peníze od investorů. Rostoucí výnosy znamenají dražší státní dluh a vyšší úroky pro celou ekonomiku."
        ),
        primary_source="Burzy cenných papírů, Ministerstva financí, Bloomberg, Reuters",
        frequency="Kontinuální tržní obchodování"
    ),
    GlossaryItem(
        term="10letý státní dluhopis (10Y Benchmark)",
        category="Dluhopisy & Výnosové křivky",
        region="Globální",
        simple_explanation=(
            "Zlatý standard finančních trhů. Výnos 10letého státního dluhopisu (v ČR je to CZGB 10Y, v Německu Bund 10Y, v USA 10Y Treasury) "
            "ukazuje, kolik peněz chce trh ročně za půjčku státu na 10 let. Slouží jako základní měřítko stability a 'bezriziková sazba', "
            "od které se odvíjí dlouhodobé úvěry, hypotéky i ocenění firem."
        ),
        economic_meaning=(
            "Klíčový bod výnosové křivky odrážející dlouhodobá inflační očekávání, očekávanou měnovou politiku centrální banky v příští dekádě "
            "a časovou prémii (term premium). V modelech diskontovaných peněžních toků (DCF) slouží jako bezriziková míra (Rf)."
        ),
        practical_impact=(
            "Když roste výnos 10letého dluhopisu, bankám rostou náklady na dlouhé peníze a zdražují se fixace hypoték na 5 až 10 let. "
            "Zároveň to zvyšuje náklady státu na obsluhu státního dluhu."
        ),
        primary_source="MF ČR / Deutsche Bundesbank / U.S. Treasury",
        frequency="Denní tržní kotace"
    ),
    GlossaryItem(
        term="Výnosová křivka & Normální sklon",
        category="Dluhopisy & Výnosové křivky",
        region="Globální",
        simple_explanation=(
            "Graf, který spojuje úroky státních dluhopisů od nejkratších (např. 1 měsíc) po nejdelší (např. 10 nebo 30 let). "
            "Ve zdravé rostoucí ekonomice má křivka 'normální' stoupající tvar: čím na delší dobu někomu půjčíte, tím vyšší úrok logicky požadujete, "
            "protože nesete riziko neznámé budoucnosti a inflace."
        ),
        economic_meaning=(
            "Časová struktura úrokových sazeb (Term Structure of Interest Rates). Pozitivní sklon křivky je dán časovou prémií (term premium), "
            "která kompenzuje investory za duraci a nejistotu budoucího makroekonomického vývoje."
        ),
        practical_impact=(
            "Normální sklon umožňuje bankám transformovat krátkodobé vklady na dlouhodobé úvěry se ziskem, což podporuje poskytování úvěrů a zdravý hospodářský růst."
        ),
        primary_source="Analýzy ČNB, ECB a U.S. Department of the Treasury",
        frequency="Průběžná aktualizace"
    ),
    GlossaryItem(
        term="Inverze výnosové křivky (Inverted Yield Curve)",
        category="Dluhopisy & Výnosové křivky",
        region="Globální",
        simple_explanation=(
            "Anomálie na trhu, kdy krátkodobé dluhopisy (např. na 2 roky) nesou vyšší úrok než dlouhodobé (na 10 let). Křivka se 'převrátí'. "
            "Děje se to tehdy, když centrální banka prudce zvýší sazby, aby zchladila inflaci, ale investoři očekávají, že ekonomika kvůli tomu "
            "spadne do recese a sazby budou muset jít brzy zase dolů. Historicky jde o nejspolehlivější varovný signál blížící se ekonomické krize."
        ),
        economic_meaning=(
            "Negativní diferenciál mezi dlouhým a krátkým koncem křivky (Spread 10Y − 2Y < 0). Podle hypotézy racionálních očekávání odráží "
            "předpověď budoucího agresivního snižování úrokových sazeb způsobeného ekonomickým útlumem."
        ),
        practical_impact=(
            "Pro banky inverze znamená stlačení čisté úrokové marže (NIM), což vede ke zpřísnění úvěrových standardů a omezení toku peněz do ekonomiky."
        ),
        primary_source="Finanční trhy, FED St. Louis, Patria Finance",
        frequency="Sledováno denně"
    ),
    GlossaryItem(
        term="Spread 10Y − 2Y",
        category="Dluhopisy & Výnosové křivky",
        region="Globální",
        simple_explanation=(
            "Rozdíl mezi výnosem 10letého a 2letého státního dluhopisu vyjádřený v bazických bodech (bps). Jeden bazický bod je setina procenta (0,01 %). "
            "Pokud je hodnota kladná (např. +50 bps), křivka je normální. Pokud je záporná (např. −40 bps), křivka je invertovaná."
        ),
        economic_meaning=(
            "Kvantitativní míra strmosti výnosové křivky. Návrat ze záporných hodnot do kladných (tzv. un-inversion neboli napřimování) často nastává "
            "těsně před začátkem hospodářské recese, kdy centrální banka začíná nouzově uvolňovat krátké sazby."
        ),
        practical_impact=(
            "Klíčový indikátor pro portfolio manažery a stratégy při alokaci kapitálu mezi akcie, dluhopisy a peněžní trh."
        ),
        primary_source="Kalkulace z dat MF ČR, Bundesbanky a U.S. Treasury",
        frequency="Denní data"
    ),
    GlossaryItem(
        term="Sovereign Credit Spread (CZGB vs. Bund)",
        category="Dluhopisy & Výnosové křivky",
        region="ČR & EU",
        simple_explanation=(
            "Riziková přirážka České republiky vůči Německu. Ukazuje, o kolik vyšší úrok musí česká vláda investorům nabídnout na 10letém dluhopisu "
            "ve srovnání s německým Bundem (který je považován za nejbezpečnější dluhopis v Evropě). Vyšší spread znamená vyšší vnímané riziko měny a rozpočtu."
        ),
        economic_meaning=(
            "Rozdíl výnosů do splatnosti (YTM_CZGB − YTM_Bund). Skládá se z prémie za měnové riziko koruny (koruna vs. euro), úrokového diferenciálu "
            "mezi ČNB a ECB a specifické fiskální rizikové prémie suverénního emitenta."
        ),
        practical_impact=(
            "Ukazuje důvěru mezinárodních investorů v českou ekonomiku a stabilitu veřejných financí ČR. Úzký spread znamená vysokou prestiž a levnější financování státu."
        ),
        primary_source="Kombinace dat MF ČR a Deutsche Bundesbank",
        frequency="Denní výpočet"
    ),
    GlossaryItem(
        term="Úrokové swapy (CZK IRS)",
        category="Dluhopisy & Výnosové křivky",
        region="ČR",
        simple_explanation=(
            "Finanční dohoda mezi bankami, kde si jedna strana vyměňuje pohyblivý úrok (PRIBOR) za pevně stanovený stálý úrok na několik let dopředu. "
            "Právě z cen těchto swapů (např. 5Y IRS) české banky přímo počítají, jaký fixní úrok nabídnou občanům na pětiletou fixaci hypotéky."
        ),
        economic_meaning=(
            "Interest Rate Swap – derivátový instrument sloužící k řízení úrokového rizika (ALM). Tržní křivka swapových sazeb představuje "
            "očekávanou průměrnou úroveň mezibankovních sazeb v daném časovém horizontu bez započtení státního kreditního rizika."
        ),
        practical_impact=(
            "Když na trhu roste cena 5Y IRS, hypoteční banky během několika dnů zdraží pětileté fixace hypoték pro koncové klienty."
        ),
        primary_source="Mezibankovní trh derivátů (OTC)",
        frequency="Průběžné mezibankovní kotace"
    ),

    # =========================================================================
    # 3. MĚNOVÉ KURZY & DEVIZOVÝ TRH (FX)
    # =========================================================================
    GlossaryItem(
        term="Měnový kurz EUR/CZK & USD/CZK",
        category="Měnové kurzy & Devizový trh (FX)",
        region="ČR",
        simple_explanation=(
            "Cena jednoho eura či amerického dolaru vyjádřená v českých korunách. Když kurz EUR/CZK klesá (např. z 25,50 na 25,00 Kč), koruna posiluje – "
            "pro Čechy zlevňuje dovozové zboží, pohonné hmoty, elektronika a dovolené v zahraničí, ale exportéři utrží za své výrobky méně korun. "
            "Když kurz roste, koruna oslabuje."
        ),
        economic_meaning=(
            "Nominální směnný kurz vyjadřující relativní kupní sílu a poptávku po domácí a zahraniční měně. Kurzový kanál je klíčovou součástí "
            "měnových podmínek v malé otevřené exportní ekonomice, kde vývoz tvoří přes 70 % HDP."
        ),
        practical_impact=(
            "Silnější koruna působí protiinflačně (zlevňuje dováženou ropu a plyn), slabší koruna pomáhá konkurenceschopnosti exportérů, ale prodražuje nákupy v cizině."
        ),
        primary_source="Česká národní banka (ČNB – Denní devizový trh)",
        frequency="Denní oficiální fixace ČNB v 14:30 SEČ"
    ),
    GlossaryItem(
        term="Dolarový index (DXY / U.S. Dollar Index)",
        category="Měnové kurzy & Devizový trh (FX)",
        region="USA & Globální",
        simple_explanation=(
            "Index, který měří celkovou sílu amerického dolaru vůči koši šesti nejdůležitějších světových měn (více než 57 % váhy má euro, dále jen, "
            "britská libra, kanadský dolar, švédská koruna a švýcarský frank). Když DXY roste, dolar celosvětově posiluje a vysává kapitál z jiných trhů."
        ),
        economic_meaning=(
            "Geometricky vážený průměr směnné hodnoty USD vůči hlavním obchodním partnerům. Základní hodnota indexu byla nastavena na 100 v roce 1973. "
            "Funguje jako barometr globální averze k riziku – v dobách mezinárodního napětí investoři utíkají do dolaru jako bezpečného přístavu."
        ),
        practical_impact=(
            "Silný dolar (vysoký DXY) zdražuje celosvětově komodity kótované v USD (ropa, zlato, pšenice) a vytváří tlak na měny rozvíjejících se zemí."
        ),
        primary_source="Intercontinental Exchange (ICE)",
        frequency="Reálný čas / denní vypořádání"
    ),
    GlossaryItem(
        term="Úrokový diferenciál (Interest Rate Differential)",
        category="Měnové kurzy & Devizový trh (FX)",
        region="Globální",
        simple_explanation=(
            "Rozdíl mezi úrokovými sazbami dvou různých zemí (např. sazba ČNB 4,00 % minus sazba ECB 3,00 % = úrokový rozdíl +1,00 p.b.). "
            "Mezinárodní investoři rádi ukládají peníze do měny, která nese vyšší úrok (tzv. carry trade). Když má ČR vyšší úroky než eurozóna, "
            "láká to zahraniční kapitál a koruna má tendenci posilovat."
        ),
        economic_meaning=(
            "Základní proměnná teorie nekryté úrokové parity (UIP). Vyjadřuje očekávanou budoucí změnu směnného kurzu kompenzující rozdíl v úrokových výnosech. "
            "V praxi je hnací silou krátkodobých kapitálových toků."
        ),
        practical_impact=(
            "Určuje ochotu mezinárodních fondů držet českou korunu. Pokud ČNB snižuje sazby rychleji než ECB nebo Fed, koruna ztrácí úrokovou výhodu a může oslabit."
        ),
        primary_source="Srovnání sazeb centrálních bank (ČNB vs. ECB vs. Fed)",
        frequency="Průběžný vývoj dle zasedání centrálních bank"
    ),

    # =========================================================================
    # 4. HOSPODÁŘSKÝ RŮST & HDP
    # =========================================================================
    GlossaryItem(
        term="Hrubý domácí produkt (HDP / GDP)",
        category="Hospodářský růst & HDP",
        region="Globální",
        simple_explanation=(
            "Celková hodnota všech výrobků a služeb, které se v zemi vytvoří za určité období (obvykle za jeden kvartál nebo rok). "
            "Představuje souhrnné vysvědčení výkonnosti celé ekonomiky. Udává se v miliardách korun/eur/dolarů (nominální HDP) a sleduje se "
            "především jeho procentní růst."
        ),
        economic_meaning=(
            "Souhrnný makroekonomický agregát vyjadřující finální produkci rezidentských výrobních jednotek. Lze jej měřit třemi metodami: "
            "výrobní (přidaná hodnota), výdajovou (spotřeba + investice + vládní výdaje + čistý export) nebo důchodovou (mzdy + zisky + daně)."
        ),
        practical_impact=(
            "Rostoucí HDP znamená více pracovních míst, vyšší zisky firem, prostor pro růst mezd a vyšší daňové příjmy státního rozpočtu."
        ),
        primary_source="Český statistický úřad (ČSÚ) / Eurostat / U.S. BEA",
        frequency="Kvartální zveřejnění (Rychlý odhad a zpřesněné národní účty)"
    ),
    GlossaryItem(
        term="Reálný vs. Nominální růst HDP",
        category="Hospodářský růst & HDP",
        region="Globální",
        simple_explanation=(
            "Zásadní rozdíl: Nominální HDP počítá produkci v dnešních cenách, takže roste i tehdy, když se vyrobí stejně zboží, ale všechno jen zdraží. "
            "Reálný HDP je očistěný o inflaci a měří skutečný fyzický růst množství vyprodukovaných věcí a služeb. Když zprávy hlásí 'ekonomika vzrostla o 2 %', "
            "myslí se tím vždy reálný HDP."
        ),
        economic_meaning=(
            "Nominální HDP je oceněn v běžných cenách (current prices). Reálný HDP je přepočten do stálých cen referenčního roku (chained volume measures) "
            "prostřednictvím deflátoru HDP, což eliminuje vliv cenových změn a izoluje čistý objemový růst produkce."
        ),
        practical_impact=(
            "Pouze reálný růst HDP přináší skutečné zvýšení životní úrovně obyvatelstva a kupní síly společnosti."
        ),
        primary_source="Statistické úřady (ČSÚ, Eurostat, BEA)",
        frequency="Kvartální"
    ),
    GlossaryItem(
        term="Hospodářská recese (Technická recese)",
        category="Hospodářský růst & HDP",
        region="Globální",
        simple_explanation=(
            "Stav, kdy ekonomika neroste, ale propadá se. 'Technická recese' nastává tehdy, když reálný HDP klesne dva kalendářní kvartály po sobě. "
            "V recesi firmy omezují výrobu a investice, lidé méně utrácejí a může růst nezaměstnanost."
        ),
        economic_meaning=(
            "Fáze hospodářského cyklu charakterizovaná poklesem agregátní poptávky a nabídky, zápornou produkční mezerou (output gap) "
            "a deflačními či dezinflačními tlaky. V USA definuje recesi výbor NBER (National Bureau of Economic Research) na základě širšího spektra indikátorů."
        ),
        practical_impact=(
            "V recesi centrální banky obvykle prudce snižují úrokové sazby a vlády zvyšují rozpočtové výdaje, aby ekonomiku podpořily."
        ),
        primary_source="Oficiální statistiky národních účtů",
        frequency="Vyhodnocováno kvartálně"
    ),

    # =========================================================================
    # 5. INFLACE & CENOVÁ HLADINA
    # =========================================================================
    GlossaryItem(
        term="Spotřebitelská inflace (CPI Headline)",
        category="Inflace & Cenová hladina",
        region="Globální",
        simple_explanation=(
            "Míra zdražování v běžném životě. Měří se pomocí 'spotřebního koše', ve kterém statistici sledují ceny stovek položek, které běžná domácnost "
            "kupuje – od rohlíků a másla přes nájemné a elektřinu až po boty a benzín. Meziroční inflace 2,5 % znamená, že to, co loni stálo 100 Kč, "
            "stojí letos v průměru 102,50 Kč."
        ),
        economic_meaning=(
            "Index spotřebitelských cen (Consumer Price Index). Vyjadřuje změnu cenové hladiny spotřebních statků a služeb vážených podle struktury "
            "výdajů domácností zjištěné statistickým šetřením. Je primárním cílem pro režim cílování inflace většiny centrálních bank."
        ),
        practical_impact=(
            "Vysoká inflace znehodnocuje úspory na běžných účtech a snižuje reálnou kupní sílu mezd. Nízká a stabilní inflace naopak umožňuje "
            "předvídatelné plánování pro rodiny i podniky."
        ),
        primary_source="ČSÚ (ČR) / Eurostat (HICP v EU) / BLS (USA)",
        frequency="Měsíčně (kolem 10. dne následujícího měsíce)"
    ),
    GlossaryItem(
        term="Jádrová inflace (Core CPI / Core HICP)",
        category="Inflace & Cenová hladina",
        region="Globální",
        simple_explanation=(
            "Očištěná inflace, která ukazuje skutečné trvalé cenové tlaky v ekonomice. Z celkového spotřebního koše se vyškrtnou položky, "
            "jejichž ceny divoce kolísají kvůli počasí nebo geopolitice – tedy nezpracované potraviny a energie (benzín, plyn, elektřina). "
            "Ukazuje, jak moc zdražují služby, restaurace, řemeslníci a průmyslové zboží vlivem rostoucích mezd."
        ),
        economic_meaning=(
            "Měřítko základního inflačního trendu zbavené přechodných exogenních cenových šoků a vlivu regulovaných cen či změn nepřímých daní. "
            "Pro centrální bankéře je jádrová inflace spolehlivějším vodítkem pro nastavení úrokových sazeb než celková kolísavá inflace."
        ),
        practical_impact=(
            "Pokud je jádrová inflace vysoká (tzv. lepkavá), centrální banka nemůže snižovat úrokové sazby, i když celková inflace opticky klesá."
        ),
        primary_source="ČNB / Eurostat / U.S. Bureau of Labor Statistics",
        frequency="Měsíčně"
    ),
    GlossaryItem(
        term="Inflační cíl (2,0 %)",
        category="Inflace & Cenová hladina",
        region="Globální",
        simple_explanation=(
            "Cílová úroveň zdražování, o kterou usilují moderní centrální banky (ČNB, ECB, Fed). Proč nechtějí nulovou inflaci? "
            "Mírná inflace kolem 2 % funguje jako 'mazivo v motoru ekonomiky' – motivuje lidi a firmy neutápět peníze pod polštářem, "
            "ale investovat je a utrácet, a chrání zemi před nebezpečnou deflací (poklesem cen), která vede k odkládání nákupů a krizím."
        ),
        economic_meaning=(
            "Kvantitativní ukotvení inflačních očekávání v rámci měnověpolitického režimu (Inflation Targeting). "
            "ČNB má cíl 2,0 % s tolerančním pásmem ±1 procentní bod (1,0 % až 3,0 %). Dlouhodobě ukotvená očekávání na 2 % stabilizují mzdová vyjednávání."
        ),
        practical_impact=(
            "Pokud inflace uteče výrazně nad cíl, centrální banka musí šlápnout na brzdu a zdražit úvěry. Pokud klesne pod cíl, sazby se snižují."
        ),
        primary_source="Měnověpolitická strategie ČNB / ECB / Fed",
        frequency="Dlouhodobý strategický cíl"
    ),
    GlossaryItem(
        term="Reálná úroková míra (Real Interest Rate)",
        category="Inflace & Cenová hladina",
        region="Globální",
        simple_explanation=(
            "Čistý výnos z peněz po odečtení inflace (nominální úrok minus inflace podle Fisherovy rovnice). "
            "Příklad: Máte spořicí účet s úrokem 4 % a inflace je 2,5 %. Vaše reálná úroková míra je +1,5 % (reálně bohatnete). "
            "Pokud byl úrok 4 %, ale inflace 15 % (jako v roce 2022), reálná sazba byla záporná (−11 %) a úspory reálně chudly."
        ),
        economic_meaning=(
            "Ex-ante nebo ex-post reálná cena kapitálu (r = i − π). Rozhoduje o mezičasové substituci spotřeby – zda se ekonomickým subjektům "
            "vyplatí spotřebovávat dnes, nebo spořit na zítřek."
        ),
        practical_impact=(
            "Kladná reálná úroková míra chrání střadatele a motivuje k tvorbě úspor, ale zvyšuje reálné břemeno dlužníků."
        ),
        primary_source="Analytický propočet z dat úroků a inflace",
        frequency="Průběžně"
    ),

    # =========================================================================
    # 6. REÁLNÁ EKONOMIKA, SPOTŘEBA & PRŮMYSL
    # =========================================================================
    GlossaryItem(
        term="Maloobchodní tržby (Retail Sales YoY)",
        category="Reálná ekonomika & Konjunktura",
        region="Globální",
        simple_explanation=(
            "Ukazatel měřící celkové útraty lidí v obchodech – za potraviny, oblečení, elektroniku, nábytek i nákupy přes internet. "
            "Je to přímé zrcadlo spotřebitelské nálady. Když lidé věří budoucnosti a rostou jim reálné mzdy, maloobchodní tržby rostou. "
            "Když mají strach, nákupy odkládají."
        ),
        economic_meaning=(
            "Meziroční reálná změna tržeb v maloobchodě očištěná o cenové vlivy a kalendářní dny. Představuje klíčový předstihový indikátor "
            "pro výdaje domácností na konečnou spotřebu, která tvoří přibližně 50 % celkového HDP."
        ),
        practical_impact=(
            "Silné tržby signalizují hospodářské oživení, ale mohou také vytvářet poptávkové inflační tlaky v sektoru obchodu a služeb."
        ),
        primary_source="ČSÚ / Eurostat / U.S. Census Bureau",
        frequency="Měsíčně"
    ),
    GlossaryItem(
        term="Průmyslová produkce (Industrial Production YoY)",
        category="Reálná ekonomika & Konjunktura",
        region="Globální",
        simple_explanation=(
            "Měřítko výkonu továren, hutí, elektráren a těžebních podniků. Pro Českou republiku je naprosto zásadní, protože ČR patří "
            "k nejprůmyslovějším zemím Evropy (obrovskou roli hraje výroba aut – Škoda, Hyundai, Toyota a jejich subdodavatelé). "
            "Růst průmyslu znamená plné zakázkové knihy; pokles varuje před ochlazením poptávky na zahraničních trzích."
        ),
        economic_meaning=(
            "Index průmyslové produkce (IPP) měřený ve stálých cenách. Pokrývá zpracovatelský průmysl, těžbu a dobývání a energetiku. "
            "Vyznačuje se vysokou korelací s výkonem německého hospodářství a exportní dynamikou."
        ),
        practical_impact=(
            "Klíčový ukazatel pro hodnocení kondice firemního sektoru, průmyslové zaměstnanosti a poptávky po energiích a logistice."
        ),
        primary_source="ČSÚ / Eurostat / Federální rezervní systém (Fed G.17)",
        frequency="Měsíčně"
    ),

    # =========================================================================
    # 7. TRH PRÁCE & ZAMĚSTNANOST
    # =========================================================================
    GlossaryItem(
        term="Míra nezaměstnanosti (Metodika ILO)",
        category="Trh práce & Zaměstnanost",
        region="Globální",
        simple_explanation=(
            "Mezinárodně srovnatelné procento lidí, kteří nemají práci, ale aktivně si ji hledají a jsou schopni do ní okamžitě nastoupit. "
            "Tuto metodiku používá Eurostat a ČSÚ. Česká republika se podle této metriky dlouhodobě pyšní nejnižší nebo jednou z nejnižších "
            "nezaměstnaností v celé Evropské unii (kolem 2,5 až 3,0 %)."
        ),
        economic_meaning=(
            "Podíl nezaměstnaných osob na celkové pracovní síle (ekonomicky aktivním obyvatelstvu) zjišťovaný Výběrovým šetřením pracovních sil (VŠPS) "
            "podle standardů Mezinárodní organizace práce (International Labour Organization - ILO). Zahrnuje pouze osoby aktivně hledající zaměstnání."
        ),
        practical_impact=(
            "Nízká nezaměstnanost dává zaměstnancům silnou vyjednávací pozici při žádostech o zvýšení mzdy, ale firmám způsobuje nedostatek pracovních sil."
        ),
        primary_source="Eurostat / ČSÚ (VŠPS) / U.S. Bureau of Labor Statistics",
        frequency="Měsíčně"
    ),
    GlossaryItem(
        term="Podíl nezaměstnaných osob (MPSV ČR)",
        category="Trh práce & Zaměstnanost",
        region="ČR",
        simple_explanation=(
            "Česká národní statistika, kterou každý měsíc zveřejňuje Ministerstvo práce a sociálních věcí. Počítá se jednoduše z evidence úřadů práce: "
            "kolik lidí je vedeno na úřadu práce jako uchazeči o zaměstnání vůči všem obyvatelům ČR ve věku 15 až 64 let. Číslo bývá obvykle o něco vyšší "
            "(kolem 3,5 až 4,0 %) než metodika ILO."
        ),
        economic_meaning=(
            "Administrativní ukazatel Ministerstva práce a sociálních věcí ČR zavedený v roce 2013. Vyjadřuje podíl dosažitelných uchazečů o zaměstnání "
            "evidovaných na úřadech práce ve věku 15–64 let na celkovém počtu obyvatel ve stejném věku."
        ),
        practical_impact=(
            "Poskytuje detailní pohled na regionální rozdíly v ČR (např. Praha vs. Mostecko či Karvinsko) a poměr mezi počtem uchazečů a volných pracovních míst."
        ),
        primary_source="Ministerstvo práce a sociálních věcí ČR (MPSV)",
        frequency="Měsíčně (vždy na začátku měsíce za měsíc předchozí)"
    ),

    # =========================================================================
    # 8. AKCIOVÉ TRHY & BURZOVNÍ INDEXY
    # =========================================================================
    GlossaryItem(
        term="Index PX (Pražská burza)",
        category="Akciové trhy & Burzovní indexy",
        region="ČR",
        simple_explanation=(
            "Oficiální index Burzy cenných papírů Praha (BCPP). Funguje jako teploměr české akciové scény. Jeho hodnota se počítá z cen největších "
            "českých firem obchodovaných na burze – hlavní váhu mají banky (Erste Group, Komerční banka, Moneta Money Bank), energetický gigant ČEZ "
            "a zbrojařská skupina Colt CZ. Je známý velmi vysokým dividendovým výnosem (často přes 7 % ročně)."
        ),
        economic_meaning=(
            "Tržně kapitalizovaný cenový index (price index) vážený volně plovoucími akciemi (free-float market capitalization). "
            "Byl zaveden v dubnu 1994 s výchozí hodnotou 1 000 bodů. Vzhledem k sektorové koncentraci odráží zejména ziskovost bankovnictví a utilit."
        ),
        practical_impact=(
            "Klíčové aktivum pro české dividendové investory a penzijní fondy investující na domácím kapitálovém trhu."
        ),
        primary_source="Burza cenných papírů Praha (BCPP / PSE)",
        frequency="Průběžně v reálném čase během obchodních dnů (09:00–16:20)"
    ),
    GlossaryItem(
        term="Euro Stoxx 50",
        category="Akciové trhy & Burzovní indexy",
        region="EU",
        simple_explanation=(
            "Nejvýznamnější akciový index Eurozóny. Sdružuje 50 největších a nejhodnotnějších společností napříč 8 evropskými zeměmi platícími eurem. "
            "Najdete v něm technologické giganty (ASML, SAP), luxusní značky (LVMH, Hermès), průmysl (Siemens, Schneider Electric) i finance (Allianz, BNP Paribas)."
        ),
        economic_meaning=(
            "Blue-chip index spravovaný společností STOXX Ltd. (součást Deutsche Börse Group). Zahrnuje přední lídry evropského byznysu vážené volným floatem "
            "s 10% zastropováním maximální váhy jedné společnosti. Slouží jako základní evropský benchmark."
        ),
        practical_impact=(
            "Hlavní nástroj pro pasivní investování (ETF) do evropských akcií a zrcadlo hospodářské kondice největších korporací Eurozóny."
        ),
        primary_source="STOXX Ltd. / Deutsche Börse",
        frequency="Reálný čas během evropských obchodních hodin"
    ),
    GlossaryItem(
        term="S&P 500",
        category="Akciové trhy & Burzovní indexy",
        region="USA & Globální",
        simple_explanation=(
            "Nejsledovanější akciový index světa. Zahrnuje 500 největších veřejně obchodovaných amerických společností (Apple, Microsoft, Nvidia, "
            "Amazon, Alphabet/Google, Berkshire Hathaway a další). Tvoří zhruba 80 % hodnoty celého amerického akciového trhu a je považován "
            "za nejlepší měřítko úspěchu amerického kapitalismu a globální ekonomiky."
        ),
        economic_meaning=(
            "Vážený index tržní kapitalizace (free-float market cap weighted index) spravovaný společností S&P Dow Jones Indices. "
            "Vyznačuje se přísnými kritérii pro zařazení (ziskovost za poslední 4 kvartály, vysoká likvidita, sídlo v USA)."
        ),
        practical_impact=(
            "Základní kámen investičních portfolií po celém světě. Dlouhodobě dosahuje průměrného zhodnocení kolem 9–10 % ročně (včetně reinvestovaných dividend)."
        ),
        primary_source="S&P Dow Jones Indices / Wall Street",
        frequency="Reálný čas během obchodování na NYSE a NASDAQ"
    ),
    GlossaryItem(
        term="NASDAQ Composite",
        category="Akciové trhy & Burzovní indexy",
        region="USA & Globální",
        simple_explanation=(
            "Index americké technologické burzy NASDAQ, který zahrnuje více než 3 000 firem. Dominují mu technologičtí inovátoři, polovodičové společnosti, "
            "software, internetové platformy a biotechnologie. Bývá citlivější na změny úrokových sazeb a hospodářského cyklu než S&P 500."
        ),
        economic_meaning=(
            "Široký tržní index pokrývající všechny kmenové akcie kótované na trhu NASDAQ. Vzhledem k vysokému podílu růstových firem s dlouhou durací "
            "peněžních toků (growth stocks) vykazuje vyšší betu a volatilitu vůči makroekonomickým zprávám."
        ),
        practical_impact=(
            "Představuje barometr technologických inovací, digitalizace, rozvoje umělé inteligence (AI) a ochoty investorů riskovat."
        ),
        primary_source="NASDAQ OMX Group",
        frequency="Reálný čas (15:30–22:00 SEČ)"
    ),
    GlossaryItem(
        term="Normalizované srovnání výkonnosti (Báze = 100)",
        category="Akciové trhy & Burzovní indexy",
        region="Globální",
        simple_explanation=(
            "Matematický trik, který umožňuje spravedlivě porovnat indexy, které mají úplně jiné hodnoty v bodech (např. PX má 1 700 bodů, "
            "S&P 500 má 6 000 bodů a NASDAQ 20 000 bodů). Všechny indexy se k vybranému datu v minulosti přepočtou na výchozí hodnotu 100. "
            "Pokud dnes jeden index ukazuje 145 a druhý 120, okamžitě vidíte, že první vydělal 45 % a druhý 20 % bez ohledu na výchozí bodovou hladinu."
        ),
        economic_meaning=(
            "Indexace časových řad (re-basing). Hodnota každého pozorování v čase t se vydělí hodnotou v základním období t0 a vynásobí 100 "
            "(Index_t = (Cena_t / Cena_t0) × 100). Odstraňuje měřítkový bias a umožňuje přímou vizuální komparaci kumulativních výnosů."
        ),
        practical_impact=(
            "Nezbytný analytický nástroj pro porovnávání výnosnosti různých trhů a tříd aktiv v čase."
        ),
        primary_source="Metodický standard finanční analýzy",
        frequency="Počítáno pro libovolný zvolený časový horizont"
    ),

    # =========================================================================
    # 9. VEŘEJNÉ FINANCE & STÁTNÍ DLUH
    # =========================================================================
    GlossaryItem(
        term="Veřejný vládní dluh k HDP (% HDP)",
        category="Veřejné finance & Státní dluh",
        region="Globální",
        simple_explanation=(
            "Poměr, který ukazuje, jak moc je stát zadlužený vzhledem k velikosti své celé ekonomiky. Podobá se to srovnání dluhu domácnosti "
            "vůči jejímu ročnímu platu. ČR má dluh kolem 44 % HDP (jeden z nejnižších v EU), průměr Eurozóny je kolem 88 % HDP a USA mají přes 120 % HDP. "
            "Čím vyšší dluh, tím více peněz musí stát každý rok pálit jen na úroky místo na školy, nemocnice či dálnice."
        ),
        economic_meaning=(
            "Dluh sektoru vládních institucí (General Government Debt) podle metodiky ESA 2010 v poměru k nominálnímu ročnímu HDP. "
            "Představuje klíčové měřítko fiskální udržitelnosti suverénního státu."
        ),
        practical_impact=(
            "Země s nízkým poměrem dluhu k HDP mají vyšší kreditní rating, snáze zvládají neočekávané krize a platí nižší úroky mezinárodním investorům."
        ),
        primary_source="Ministerstvo financí ČR / Eurostat (EDP notifikace) / U.S. Treasury",
        frequency="Kvartální notifikace a roční revize"
    ),
    GlossaryItem(
        term="Maastrichtská konvergenční kritéria",
        category="Veřejné finance & Státní dluh",
        region="EU & ČR",
        simple_explanation=(
            "Pravidla finanční disciplíny v Evropské unii zavedená Maastrichtskou smlouvou. Pro veřejné finance stanovují dva slavné stropy: "
            "1. Veřejný dluh nesmí překročit 60 % HDP. "
            "2. Roční schodek státního rozpočtu nesmí přesáhnout 3 % HDP. "
            "Česká republika kritérium dluhu do 60 % bezpečně plní."
        ),
        economic_meaning=(
            "Soustava fiskálních a měnových podmínek nezbytných pro vstup do Hospodářské a měnové unie (Eurozóny) a zakotvených v Paktu stability "
            "a růstu (Stability and Growth Pact). Zahrnuje také kritéria cenové stability, konvergence úrokových sazeb a stability měnového kurzu v ERM II."
        ),
        practical_impact=(
            "Zabraňuje nezodpovědnému zadlužování států a chrání stabilitu společné evropské měny před rizikem státního bankrotu."
        ),
        primary_source="Evropská komise & Rada EU",
        frequency="Pravidelný pololetní a roční fiskální dohled"
    ),
    GlossaryItem(
        term="Saldo státního rozpočtu (Deficit / Přebytek)",
        category="Veřejné finance & Státní dluh",
        region="Globální",
        simple_explanation=(
            "Výsledek ročního hospodaření státní pokladny. Pokud stát vybere na daních a poplatcích více, než kolik utratí, vzniká přebytek (surplus). "
            "Pokud utratí více, než kolik vybere, vzniká schodek neboli deficit, který si vláda musí půjčit vydáním státních dluhopisů."
        ),
        economic_meaning=(
            "Čisté výpůjčky / výpůjční pozice sektoru vládních institucí (Net lending / net borrowing). Skládá se ze strukturálního salda "
            "(očištěného o vliv hospodářského cyklu a jednorázová opatření) a cyklické složky odrážející aktuální fázi ekonomiky."
        ),
        practical_impact=(
            "Dlouhodobé strukturální deficity zvyšují celkový státní dluh a vyvolávají nutnost konsolidačních balíčků (zvyšování daní či škrtání výdajů)."
        ),
        primary_source="Ministerstvo financí ČR (Pokladní plnění) / U.S. Treasury",
        frequency="Měsíční pokladní zpráva a roční státní závěrečný účet"
    ),
    GlossaryItem(
        term="Náklady na obsluhu státního dluhu",
        category="Veřejné finance & Státní dluh",
        region="Globální",
        simple_explanation=(
            "Čisté úroky, které musí stát každý rok zaplatit majitelům státních dluhopisů za to, že mu půjčili peníze. "
            "V ČR tyto náklady v posledních letech vzrostly z cca 40 miliard Kč ročně na téměř 100 miliard Kč ročně kvůli vyšším úrokovým sazbám "
            "a většímu objemu dluhu. Jsou to peníze, které vláda musí zaplatit přednostně před jakýmikoliv jinými výdaji."
        ),
        economic_meaning=(
            "Úrokové výdaje vládního sektoru (Debt service costs). Jsou funkcí celkového objemu emitovaného vládního dluhu a průměrného efektivního "
            "výnosu dluhopisového portfolia státu. Představují mandatorní výdaj státního rozpočtu."
        ),
        practical_impact=(
            "Vysoké úroky z dluhu odčerpávají desítky miliard korun z veřejných rozpočtů, které by jinak mohly směřovat do školství, zdravotnictví či vědy."
        ),
        primary_source="Ministerstvo financí ČR (Zpráva o řízení státního dluhu)",
        frequency="Kvartální a roční zprávy MF ČR"
    ),

    # =========================================================================
    # 6. PŘEDSTIHOVÉ UKAZATELE, MZDY, BANKOVNÍ SEKTOR & TRŽNÍ SENTIMENT
    # =========================================================================
    GlossaryItem(
        term="PMI v průmyslu ČR (S&P Global)",
        category="Předstihové ukazatele & Sentiment",
        region="ČR",
        simple_explanation=(
            "Měsíční index nákupních manažerů v českém zpracovatelském průmyslu. Funguje jako nejrychlejší seismograf: manažeři velkých továren "
            "odpovídají, zda jim přibývají zakázky, jak vyrábí a zda nabírají lidi. Hranice 50 bodů je zlomová: nad 50 značí růst a optimismus, "
            "pod 50 útlum a pokles výroby."
        ),
        economic_meaning=(
            "Purchasing Managers' Index (PMI) je difúzní index vypočítávaný společností S&P Global na základě váženého průměru nových objednávek (30 %), "
            "produkce (25 %), zaměstnanosti (20 %), dodacích lhůt (15 %) a zásob nákupu (10 %). Vykazuje vysokou korelaci s budoucím HDP a průmyslovou výrobou s předstihem 1 až 2 měsíců."
        ),
        practical_impact=(
            "Varuje investory a firmy před blížícím se ochlazením ekonomiky dříve než oficiální data ČSÚ. Pomáhá podnikům plánovat nákup zásob a rozpočty."
        ),
        primary_source="S&P Global Czech Republic Manufacturing PMI",
        frequency="Měsíčně (vždy první pracovní den v měsíci)"
    ),
    GlossaryItem(
        term="Důvěra podnikatelů a spotřebitelů (ČSÚ)",
        category="Předstihové ukazatele & Sentiment",
        region="ČR",
        simple_explanation=(
            "Oficiální průzkum ČSÚ mezi tisíci českými firmami a domácnostmi. Zjišťuje, jak podnikatelé vidí poptávku po svých výrobcích a jak se rodiny "
            "dívají na svou finanční situaci – zda se bojí zdražování, ztráty práce a zda plánují velké nákupy."
        ),
        economic_meaning=(
            "Souhrnný indikátor důvěry (Economic Sentiment Indicator) harmonizovaný s metodikou Evropské komise. Skládá se z podnikatelského sentimentu "
            "(průmysl, stavebnictví, obchod, služby s vahou 80 %) a spotřebitelské důvěry (váha 20 %). Dlouhodobý průměr je normalizován na bázi 100 bodů."
        ),
        practical_impact=(
            "Růst spotřebitelské důvěry předznamenává vyšší ochotu lidí utrácet a oživení tržeb v obchodech; propad důvěry vede k preventivnímu spoření a odkládání investic."
        ),
        primary_source="Český statistický úřad (ČSÚ – Konjunkturální průzkum)",
        frequency="Měsíčně (kolem 24. dne v měsíci)"
    ),
    GlossaryItem(
        term="Průměrná hrubá mzda nominálně (YoY)",
        category="Trh práce & Mzdy",
        region="ČR",
        simple_explanation=(
            "O kolik procent vzrostla průměrná hrubá výplata zaměstnanců v Česku oproti stejnému období minulého roku, před odečtením inflace a daní. "
            "Udává, kolik peněz navíc lidé dostali na svých výplatních páskách."
        ),
        economic_meaning=(
            "Meziroční nominální tempo růstu průměrné hrubé měsíční mzdy přepočtené na plně zaměstnané osoby v národním hospodářství ČR. "
            "Klíčový ukazatel mzdových nákladů firem a agregátní kupní síly."
        ),
        practical_impact=(
            "Mzdový růst tlačí na růst cen služeb a spotřebitelskou inflaci (mzdově-inflační spirála), proto jej bedlivě sleduje ČNB při rozhodování o úrokových sazbách."
        ),
        primary_source="Český statistický úřad (ČSÚ – Vývoj mezd a zaměstnanosti)",
        frequency="Čtvrtletně (počátkem března, června, září a prosince)"
    ),
    GlossaryItem(
        term="Průměrná reálná mzda (YoY)",
        category="Trh práce & Mzdy",
        region="ČR",
        simple_explanation=(
            "Růst mzdy očištěný o inflaci. Ukazuje skutečnou změnu životní úrovně – tedy zda si za svou výplatu můžete reálně koupit více rohlíků, benzínu "
            "a služeb než loni. Pokud mzdy vzrostou o 7 %, ale inflace je 10 %, reálná mzda klesla o 3 % a vy jste zchudli."
        ),
        economic_meaning=(
            "Poměr indexu nominální mzdy k indexu spotřebitelských cen (CPI). Kladná hodnota znamená růst reálného disponibilního důchodu a blahobytu, "
            "záporná hodnota eroduje kupní sílu obyvatelstva."
        ),
        practical_impact=(
            "V letech 2022–2023 zažilo Česko historický propad reálných mezd o více než 8 %, což vedlo k propadu maloobchodních tržeb; návrat do plusu v roce 2024 obnovil růst spotřeby."
        ),
        primary_source="Český statistický úřad (ČSÚ)",
        frequency="Čtvrtletně"
    ),
    GlossaryItem(
        term="Nové hypotéky – objem a průměrná sazba",
        category="Bankovní sektor & Úvěry",
        region="ČR",
        simple_explanation=(
            "Kolik miliard korun banky v Česku za daný měsíc skutečně nově napůjčovaly lidem na nákup nemovitostí a za jaký průměrný úrok. "
            "Nezahrnuje refinancování starých úvěrů, takže ukazuje čerstvou poptávku po vlastním bydlení."
        ),
        economic_meaning=(
            "Statistika nových obchodů hypotečních úvěrů na bydlení fyzickým osobám sledovaná ČNB a ČBA. Odráží transmisní mechanismus sazeb ČNB do retailového "
            "úvěrování, marže komerčních bank a aktivitu na realitním trhu."
        ),
        practical_impact=(
            "Přímo ukazuje dostupnost bydlení a oživení či zamrznutí realitního trhu. Při sazbách přes 6 % v letech 2022–2023 objemy spadly na třetinu, při poklesu k pásmu 4,6–5,1 % se hypoteční trh výrazně oživil."
        ),
        primary_source="Česká bankovní asociace (ČBA Hypomonitor / cbamonitor.cz) & ČNB ARAD",
        frequency="Měsíčně"
    ),
    GlossaryItem(
        term="Korporátní úvěry – meziroční růst",
        category="Bankovní sektor & Úvěry",
        region="ČR",
        simple_explanation=(
            "Meziroční procentuální změna celkového objemu úvěrů, které banky půjčily podnikům a firmám v ČR. Zahrnuje jak korunové půjčky, tak úvěry v eurech."
        ),
        economic_meaning=(
            "Tempo úvěrové expanze nefinančním podnikům z měnové statistiky ČNB. Ukazuje ochotu bank nést úvěrové riziko a apetit firem investovat "
            "do nových technologií, hal a provozního kapitálu."
        ),
        practical_impact=(
            "Vysoké úroky v CZK donutily české exportní firmy přejít na levnější eurové úvěry (euroizace firemního sektoru), což oslabilo účinnost zvyšování úrokových sazeb ČNB."
        ),
        primary_source="Česká národní banka (ARAD – Měnová statistika)",
        frequency="Měsíčně"
    ),
    GlossaryItem(
        term="Měnový agregát M2 (YoY)",
        category="Měnová politika & Měnová zásoba",
        region="ČR",
        simple_explanation=(
            "Růst celkového množství peněz v oběhu v české ekonomice. Zahrnuje hotovost v peněženkách, peníze na běžných účtech i termínované vklady "
            "a spořicí účty se splatností do 2 let. Pokud množství peněz roste příliš rychle oproti tomu, kolik ekonomika vyrobí, hrozí inflace."
        ),
        economic_meaning=(
            "Široká peněžní zásoba definovaná ČNB a ECB. Skládá se z úzkých peněz M1 (oběživo + jednodenní vklady) plus vkladů s dohodnutou splatností do 2 let "
            "a s výpovědní lhůtou do 3 měsíců. Dle kvantitativní teorie peněz dlouhodobě determinuje cenovou hladinu."
        ),
        practical_impact=(
            "Masivní nárůst M2 v letech 2020–2021 (přes 10 % ročně) v důsledku covidových stimulů a vládních deficitů položil základy pro následnou vysokou inflaci."
        ),
        primary_source="Česká národní banka (Statistika peněžního oběhu)",
        frequency="Měsíčně"
    ),
    GlossaryItem(
        term="Běžný účet platební bilance (k HDP)",
        category="Vnější rovnováha & Mezinárodní obchod",
        region="ČR",
        simple_explanation=(
            "Celkové účetní vysvědčení České republiky vůči zbytku světa vyjádřené v procentech HDP. Zahrnuje export a import zboží, služeb (např. IT, turismus), "
            "ale i toky dividend zahraničním vlastníkům a dotace z EU. Kladná hodnota znamená, že Česko více vydělává v zahraničí než utrácí."
        ),
        economic_meaning=(
            "Current Account Balance k HDP. Vyjadřuje národní úspory minus investice (S − I). Deficit znamená, že země je čistým dlužníkem vůči zahraničí "
            "a musí jej profinancovat přílivem kapitálu na finančním účtu."
        ),
        practical_impact=(
            "Hluboký schodek (např. -5,4 % HDP v roce 2022 vlivem drahého dovozu plynu a ropy) vytváří silný oslabující tlak na kurz české koruny; přebytek naopak korunu zpevňuje."
        ),
        primary_source="Česká národní banka (Platební bilance) & ČSÚ",
        frequency="Kvartálně a měsíčně"
    ),
    GlossaryItem(
        term="Bilance zahraničního obchodu ČSÚ",
        category="Vnější rovnováha & Mezinárodní obchod",
        region="ČR",
        simple_explanation=(
            "Rozdíl mezi hodnotou zboží vyvezeného z Česka do světa (např. auta Škoda, stroje, chemie) a hodnotou zboží dovezeného do Česka (ropa, plyn, elektronika, spotřební zboží). "
            "Kladné číslo značí přebytek (vývoz > dovoz), záporné schodek."
        ),
        economic_meaning=(
            "Měsíční saldo zahraničního obchodu se zbožím podle národního pojetí v miliardách Kč. Jako silně proexportní otevřená ekonomika Česko dlouhodobě "
            "dosahuje vysokých přebytků v řádu 10–25 mld. Kč měsíčně."
        ),
        practical_impact=(
            "Klíčový pilíř stability české koruny a motor HDP. Při energetické krizi v roce 2022 se bilance propadla do rekordního deficitu, v letech 2023–2024 se však vrátila k masivním přebytkům."
        ),
        primary_source="Český statistický úřad (ČSÚ – Přeshraniční statistika obchodu)",
        frequency="Měsíčně (kolem 6. dne v měsíci)"
    ),
    GlossaryItem(
        term="Kreditní spread 10Y CZGB vs. 10Y Bund",
        category="Dluhopisový trh & Spready",
        region="ČR & EU",
        simple_explanation=(
            "Rozdíl ve výnosu (úroku) mezi 10letým českým státním dluhopisem a nejbezpečnějším evropským německým dluhopisem (Bundem) měřený v bazických bodech "
            "(100 bps = 1,00 %). Ukazuje, o kolik vyšší úrok musí Česko platit investorům oproti Německu."
        ),
        economic_meaning=(
            "Sovereign yield spread. Reflektuje úrokový diferenciál mezi měnovými politikami ČNB a ECB, inflační prémii koruny a kreditní/zeměpisné riziko České republiky mimo eurozónu."
        ),
        practical_impact=(
            "Vyšší spread zdražuje financování schodku českého státního rozpočtu na mezinárodním trhu, ale nabízí vyšší výnos konzervativním dluhopisovým investorům a penzijním fondům."
        ),
        primary_source="Ministerstvo financí ČR / Deutsche Bundesbank / Eurostat",
        frequency="Denně (tržní kotace) a měsíčně"
    ),
    GlossaryItem(
        term="Asset Swap Spread (ASW 10Y CZK)",
        category="Dluhopisový trh & Spready",
        region="ČR",
        simple_explanation=(
            "Rozdíl mezi výnosem 10letého českého státního dluhopisu a sazbou úrokového swapu (IRS) na mezibankovním trhu. Vyjadřuje, zda jsou státní dluhopisy "
            "v porovnání s čistým bankovním trhem levné nebo drahé."
        ),
        economic_meaning=(
            "Asset Swap (ASW) spread v bazických bodech měří prémii státního dluhopisu nad bezrizikovou křivkou úrokových swapů. Kladný ASW spread značí, "
            "že dluhopis nese vyšší výnos než swap (přebytek nabídky dluhopisů státu), záporný značí vysokou poptávku po státním kolaterálu."
        ),
        practical_impact=(
            "Standardní ukazatel pro správce dluhopisových portfolií, treasury oddělení bank a primární dealery při řízení rizika a arbitráži."
        ),
        primary_source="Mezibankovní trh úrokových swapů & MF ČR",
        frequency="Denně a měsíčně"
    ),
    GlossaryItem(
        term="Německý Ifo index podnikatelského klimatu",
        category="Předstihové ukazatele & Sentiment",
        region="EU",
        simple_explanation=(
            "Nejdůležitější barometr největší evropské ekonomiky – Německa. Každý měsíc mnichovský institut Ifo zpovídá 9 000 šéfů německých firem ze všech oborů. "
            "Protože Německo je pro ČR klíčový obchodní partner (odebírá třetinu českého exportu), vývoj Ifo indexu přímo předpovídá, jak se bude dařit českému průmyslu."
        ),
        economic_meaning=(
            "Ifo Geschäftsklimaindex vychází ze souběžného hodnocení aktuální obchodní situace firem a jejich očekávání na příštích 6 měsíců. Vykazuje mimořádně "
            "vysokou spolehlivost při detekci recese a oživení v celém prostoru Eurozóny."
        ),
        practical_impact=(
            "Při propadu německého Ifo indexu české exportní fabriky brzy pociťují úbytek zakázek na autodíly, ocel a stroje; růst Ifo je předzvěstí hospodářské expanze."
        ),
        primary_source="Ifo Institut Mnichov (ifo Geschäftsklimaindex)",
        frequency="Měsíčně (kolem 25. dne v měsíci)"
    ),
    GlossaryItem(
        term="Composite PMI Eurozóny",
        category="Předstihové ukazatele & Sentiment",
        region="EU",
        simple_explanation=(
            "Souhrnný index nákupních manažerů pro celou dvacítku zemí platících eurem (Eurozónu). Kombinuje data z průmyslových továren i firem poskytujících služby "
            "(hotely, IT, doprava). Hodnota nad 50 bodů signalizuje expanzi, pod 50 hospodářský pokles Eurozóny."
        ),
        economic_meaning=(
            "HCOB / S&P Global Flash Eurozone Composite PMI sestavovaný na bázi dotazníků z více než 5 000 podniků. Slouží jako bezprostřední 'nowcast' "
            "kvartálního růstu HDP Eurozóny."
        ),
        practical_impact=(
            "Rozhodující vodítko pro Radu guvernérů ECB při stanovení úrokových sazeb a pro devizové obchodníky s eurem (EUR/USD)."
        ),
        primary_source="S&P Global & Hamburg Commercial Bank (HCOB)",
        frequency="Měsíčně (předběžný flash odhad kolem 22. dne, finální začátkem měsíce)"
    ),
    GlossaryItem(
        term="Sjednané mzdy v Eurozóně (ECB YoY)",
        category="Trh práce & Mzdy",
        region="EU",
        simple_explanation=(
            "Oficiální ukazatel ECB sledující, jaký meziroční růst platů si zaměstnanci a odbory vyjednali v kolektivních smlouvách napříč zeměmi Eurozóny. "
            "Ukazuje, jak silně tlačí rostoucí výplaty na náklady evropských firem."
        ),
        economic_meaning=(
            "Euro Area Negotiated Wage Growth je vážený index smluvně dohodnutých mezd sledovaný Evropskou centrální bankou. Představuje hlavní indikátor "
            "setrvačnosti jádrové inflace a inflace ve službách."
        ),
        practical_impact=(
            "Pokud růst sjednaných mezd překračuje 3,5–4,0 % ročně, ECB se zdráhá snižovat úrokové sazby ze strachu před sekundárními inflačními dopady."
        ),
        primary_source="Evropská centrální banka (ECB Statistical Data Warehouse)",
        frequency="Čtvrtletně"
    ),
    GlossaryItem(
        term="Rizikový spread Itálie vs. Německo (10Y BTP - Bund)",
        category="Dluhopisový trh & Spready",
        region="EU",
        simple_explanation=(
            "Rozdíl mezi úrokem, který platí za půjčku na 10 let italská vláda (dluhopisy BTP) a německá vláda (Bund). Je to slavný 'teploměr finančního napětí v Evropě': "
            "když roste, investoři se bojí vysokého italského dluhu a hrozby rozpadu eurozóny; když klesá, vládne klid."
        ),
        economic_meaning=(
            "BTP-Bund yield spread v bazických bodech (bps). Ztělesňuje kreditní a fiskální riziko jihoevropské periferie Eurozóny a důvěru v transmisi jednotné měnové "
            "politiky ECB. V krizi 2011–2012 dosáhl až 550 bps, v klidových časech se pohybuje kolem 110–140 bps."
        ),
        practical_impact=(
            "Při prudkém rozšíření spreadu nad 200–250 bps je ECB připravena zasáhnout nákupem italských dluhopisů prostřednictvím nástroje TPI (Transmission Protection Instrument)."
        ),
        primary_source="MTS / Bloomberg / Deutsche Bundesbank & Banca d'Italia",
        frequency="Denně a měsíčně"
    ),
    GlossaryItem(
        term="ISM Index ve výrobě (Manufacturing PMI)",
        category="Předstihové ukazatele & Sentiment",
        region="USA",
        simple_explanation=(
            "Americký index nákupních manažerů ve zpracovatelském průmyslu od Institute for Supply Management. Jeden z celosvětově nejuznávanějších a nejdéle měřených "
            "makroindikátorů na světě. Hranice 50 bodů odděluje expanzi od útlumu americké průmyslové mašinérie."
        ),
        economic_meaning=(
            "ISM Manufacturing Index je difúzní index založený na měsíčním šetření nákupních manažerů více než 300 výrobních firem v USA. Sleduje nové zakázky, "
            "produkci, zaměstnanost, dodávky od dodavatelů a zásoby."
        ),
        practical_impact=(
            "Okamžitě po zveřejnění hýbe kurzem dolaru, akciemi na Wall Street a výnosy státních dluhopisů po celém světě. Hodnota pod 45 bodů v historii takřka vždy znamenala recesi amerického hospodářství."
        ),
        primary_source="Institute for Supply Management (ISM)",
        frequency="Měsíčně (vždy první pracovní den v měsíci)"
    ),
    GlossaryItem(
        term="ISM Index ve službách (Services PMI)",
        category="Předstihové ukazatele & Sentiment",
        region="USA",
        simple_explanation=(
            "Měsíční index nákupních manažerů v americkém sektoru služeb (banky, zdravotnictví, IT, maloobchod, logistika). Protože služby tvoří více než 75 % celé "
            "ekonomiky USA, je tento index ještě důležitější pro celkový růst než výrobní index."
        ),
        economic_meaning=(
            "ISM Services PMI (dříve Non-Manufacturing index). Měří aktivitu, zaměstnanost a cenové tlaky v nevýrobním sektoru americké ekonomiky. Hodnota nad 50 bodů značí růst."
        ),
        practical_impact=(
            "Ukazuje odolnost amerického spotřebitele. Dokud se index služeb drží nad 50 body, americká ekonomika obvykle neupadá do recese ani při ochlazení těžkého průmyslu."
        ),
        primary_source="Institute for Supply Management (ISM)",
        frequency="Měsíčně (třetí pracovní den v měsíci)"
    ),
    GlossaryItem(
        term="Spotřebitelský sentiment (Univ. of Michigan)",
        category="Předstihové ukazatele & Sentiment",
        region="USA",
        simple_explanation=(
            "Legendární průzkum Michiganské univerzity měřící náladu a optimismus amerických rodin. Zjišťuje, jak lidé hodnotí své rodinné finance, zda očekávají zdražování "
            "a zda považují současnost za vhodnou dobu pro nákup auta, domu či nábytku."
        ),
        economic_meaning=(
            "University of Michigan Consumer Sentiment Index (MCSI) založený na 500 telefonických rozhovorech měsíčně. Součástí jsou také klíčová data o 1letých "
            "a 5letých inflačních očekáváních spotřebitelů, která přímo sleduje americký Fed."
        ),
        practical_impact=(
            "Americká spotřeba tvoří téměř 70 % HDP Spojených států. Propad sentimentu (např. v létě 2022 na historické dno 50 bodů vlivem benzínu za 5 USD/galon) spolehlivě tlumí budoucí útraty domácností."
        ),
        primary_source="University of Michigan (Surveys of Consumers)",
        frequency="Měsíčně (předběžný odhad v polovině měsíce, finální na konci měsíce)"
    ),
    GlossaryItem(
        term="Průměrná hodinová mzda USA (Average Hourly Earnings YoY)",
        category="Trh práce & Mzdy",
        region="USA",
        simple_explanation=(
            "O kolik procent vzrostla průměrná hodinová odměna amerických zaměstnanců v soukromém sektoru oproti stejnému měsíci minulého roku. Vychází každý měsíc "
            "v ostře sledované zprávě spolu s počtem nových pracovních míst (NFP)."
        ),
        economic_meaning=(
            "Average Hourly Earnings Total Private YoY od U.S. Bureau of Labor Statistics. Představuje primární indikátor mzdového tlaku a napětí na americkém trhu práce."
        ),
        practical_impact=(
            "Když hodinové výdělky rostou rychleji než 4 % ročně, Fed se obává zakořenění inflace a drží úrokové sazby na vysokých úrovních déle; ochlazení k 3–3,5 % naopak otevírá dveře ke snižování sazeb."
        ),
        primary_source="U.S. Bureau of Labor Statistics (BLS – Employment Situation)",
        frequency="Měsíčně (první pátek v měsíci)"
    ),
    GlossaryItem(
        term="Index volatility VIX",
        category="Tržní sentiment & Riziko",
        region="USA & Globální",
        simple_explanation=(
            "Světově proslulý 'index strachu' na Wall Street. Měří očekávané kolísání (volatilitu) amerického akciového indexu S&P 500 v příštích 30 dnech, vypočítané z cen opcí. "
            "Když na trzích panuje klid a růst, VIX je nízký (pod 15 bodů). Když přijde krach, válka nebo panika, VIX prudce vystřelí nahoru (nad 30 až 80 bodů)."
        ),
        economic_meaning=(
            "Cboe Volatility Index (VIX) kalkulovaný Chicago Board Options Exchange. Je odvozen z cen nákupních (call) a prodejních (put) opcí na index S&P 500 "
            "a reprezentuje roční směrodatnou odchylku očekávaného tržního pohybu pro 30denní horizont. Pásma: <15 (nízká volatilita/optimismus), 15–20 (normální stav), "
            "20–30 (zvýšené riziko), >30 (tržní panika a likvidační výprodeje)."
        ),
        practical_impact=(
            "Slouží jako pojistka a indikátor tržního stresu pro globální institucionální fondy. Známé investorské přísloví praví: 'Když je VIX vysoký, je čas nakupovat; když je VIX nízký, je čas dávat si pozor.'"
        ),
        primary_source="Chicago Board Options Exchange (Cboe) & Yahoo Finance",
        frequency="Denně v reálném čase (intradenní kalkulace)"
    )
]


def render_glossary_view(active_filter_category: Optional[str] = None):
    """Vykreslí přehledný, vyhledávatelný a interaktivní výkladový glosář."""
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%); border-radius: 10px; padding: 18px 22px; color: white; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.12);">
            <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
                <div>
                    <div style="font-size: 1.40rem; font-weight: 800; letter-spacing: -0.02em;">📖 Výkladový glosář makroekonomických a finančních pojmů</div>
                    <div style="font-size: 0.85rem; color: #cbd5e1; margin-top: 4px;">Srozumitelný, ekonomicky exaktní a praktický průvodce všemi ukazateli pro laiky i investory</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Horní ovládací prvky a filtry
    col_search, col_cat, col_reg = st.columns([2.0, 1.5, 1.2])

    with col_search:
        search_kw = st.text_input(
            "🔍 Hledat v glosáři (název, text, vysvětlení):",
            placeholder="např. repo, inflace, výnosová křivka, spread, DXY, PRIBOR...",
            key="glossary_search_kw"
        )

    categories = ["Všechny kategorie"] + sorted(list(set(item.category for item in GLOSSARY_ITEMS)))
    default_cat_idx = 0
    if active_filter_category and active_filter_category in categories:
        default_cat_idx = categories.index(active_filter_category)

    with col_cat:
        selected_cat = st.selectbox(
            "Kategorie pojmů:",
            categories,
            index=default_cat_idx,
            key="glossary_select_cat"
        )

    regions = ["Všechny regiony", "ČR", "EU", "USA", "Globální"]
    with col_reg:
        selected_reg = st.selectbox(
            "Region / Země:",
            regions,
            key="glossary_select_reg"
        )

    # Filtrování položek
    filtered_items = GLOSSARY_ITEMS
    if selected_cat != "Všechny kategorie":
        filtered_items = [it for it in filtered_items if it.category == selected_cat]

    if selected_reg != "Všechny regiony":
        filtered_items = [it for it in filtered_items if selected_reg in it.region or it.region == "Globální"]

    if search_kw.strip():
        q = search_kw.strip().lower()
        filtered_items = [
            it for it in filtered_items
            if (q in it.term.lower() or
                q in it.simple_explanation.lower() or
                q in it.economic_meaning.lower() or
                q in it.practical_impact.lower() or
                q in it.primary_source.lower())
        ]

    st.markdown(f"**Nalezeno {len(filtered_items)} pojmů z celkem {len(GLOSSARY_ITEMS)} definovaných**")

    # Vykreslení karet
    for idx, item in enumerate(filtered_items):
        st.markdown(
            f"""
            <div style="background: #ffffff; border: 1px solid #cbd5e1; border-left: 5px solid #1e3a8a; border-radius: 8px; padding: 14px 18px; margin-bottom: 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; margin-bottom: 10px; border-bottom: 1px solid #f1f5f9; padding-bottom: 8px;">
                    <span style="font-size: 1.15rem; font-weight: 800; color: #0f172a;">{item.term}</span>
                    <div style="display: flex; gap: 6px; align-items: center;">
                        <span style="background: #eff6ff; color: #1e40af; font-size: 0.72rem; font-weight: 700; padding: 3px 8px; border-radius: 4px; border: 1px solid #bfdbfe;">{item.category}</span>
                        <span style="background: #f1f5f9; color: #334155; font-size: 0.72rem; font-weight: 700; padding: 3px 8px; border-radius: 4px; border: 1px solid #cbd5e1;">📍 {item.region}</span>
                    </div>
                </div>
                <div style="margin-bottom: 8px;">
                    <div style="font-size: 0.80rem; font-weight: 750; color: #1e3a8a; text-transform: uppercase; letter-spacing: 0.03em; margin-bottom: 2px;">
                        📖 Srozumitelně pro každého (Lidskou řečí):
                    </div>
                    <div style="font-size: 0.88rem; color: #1e293b; line-height: 1.45; background: #f8fafc; padding: 8px 12px; border-radius: 6px; border: 1px solid #e2e8f0;">
                        {item.simple_explanation}
                    </div>
                </div>
                <div style="margin-bottom: 8px;">
                    <div style="font-size: 0.80rem; font-weight: 750; color: #334155; text-transform: uppercase; letter-spacing: 0.03em; margin-bottom: 2px;">
                        ⚙️ Ekonomický & finanční význam:
                    </div>
                    <div style="font-size: 0.85rem; color: #475569; line-height: 1.45;">
                        {item.economic_meaning}
                    </div>
                </div>
                <div style="margin-bottom: 8px;">
                    <div style="font-size: 0.80rem; font-weight: 750; color: #059669; text-transform: uppercase; letter-spacing: 0.03em; margin-bottom: 2px;">
                        💡 Proč to sledovat & Dopad na praxi:
                    </div>
                    <div style="font-size: 0.85rem; color: #334155; line-height: 1.45;">
                        {item.practical_impact}
                    </div>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; font-size: 0.74rem; color: #64748b; margin-top: 10px; padding-top: 6px; border-top: 1px dashed #e2e8f0;">
                    <span>🏛️ <strong>Primární autorita:</strong> {item.primary_source}</span>
                    <span>⏱️ <strong>Frekvence:</strong> {item.frequency}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )



# =============================================================================
# BILINGUAL (CS / EN) GLOSSARY TRANSLATIONS & RENDERER
# =============================================================================

GLOSSARY_I18N_EN: Dict[str, Dict[str, str]] = {
    "2T Repo sazba ČNB": {
        "term": "CNB 2W Repo Rate",
        "category": "Monetary Policy & Interest Rates",
        "region": "CZ",
        "simple_explanation": "The key interest rate in the Czech Republic. It represents the interest rate the Czech National Bank (CNB) pays commercial banks when they deposit excess liquidity at the CNB for two weeks (2W). When the CNB raises this rate, banks increase interest rates on loans and mortgages while paying more on savings accounts; when the CNB cuts it, borrowing becomes cheaper.",
        "economic_meaning": "Primary monetary policy transmission rate of the CNB. Through two-week repurchase operations (repo tenders), the central bank absorbs excess liquidity from the interbank market against collateral. It directly anchors short-term money market rates (PRIBOR), discount factors, and credit creation.",
        "practical_impact": "Directly determines yields on household savings accounts and shapes mortgage and corporate loan pricing. Higher repo rates cool consumption and inflation; rate cuts stimulate investment and economic growth.",
        "primary_source": "Czech National Bank (CNB) – Bank Board Decisions (8x per year)",
        "frequency": "8x per year (scheduled CNB monetary policy meetings)",
    },
    "Diskontní sazba ČNB": {
        "term": "CNB Discount Rate",
        "category": "Monetary Policy & Interest Rates",
        "region": "CZ",
        "simple_explanation": "The floor of interest rates in the Czech Republic. It is the interest rate commercial banks earn when they deposit money overnight with the CNB (deposit facility). Interbank rates never fall below this level because banks have no reason to lend to anyone for less than the risk-free overnight rate paid by the CNB.",
        "economic_meaning": "Forms the lower bound of the CNB's standing facilities interest rate corridor, typically set 100 basis points (1.00 pp) below the 2W repo rate.",
        "practical_impact": "Serves as the technical floor for overnight liquidity in the Czech banking sector and as a statutory reference rate for late-payment interest under Czech law.",
        "primary_source": "Czech National Bank (CNB)",
        "frequency": "8x per year (alongside the repo rate)",
    },
    "Lombardní sazba ČNB": {
        "term": "CNB Lombard Rate",
        "category": "Monetary Policy & Interest Rates",
        "region": "CZ",
        "simple_explanation": "The ceiling of interest rates in the Czech Republic. If a commercial bank runs short of liquidity and needs to borrow overnight from the CNB against securities collateral, it pays the Lombard rate. Because this acts as an emergency credit line, market rates do not exceed this ceiling.",
        "economic_meaning": "Represents the upper bound of the central bank's interest rate corridor (marginal lending facility), typically anchored 100 basis points (1.00 pp) above the 2W repo rate.",
        "practical_impact": "Caps overnight money market volatility and ensures smooth settlement across the CERTIS interbank payment system.",
        "primary_source": "Czech National Bank (CNB)",
        "frequency": "8x per year (alongside the repo rate)",
    },
    "PRIBOR (Prague Interbank Offered Rate)": {
        "term": "PRIBOR (Prague Interbank Offered Rate)",
        "category": "Monetary Policy & Interest Rates",
        "region": "CZ",
        "simple_explanation": "The interest rate at which banks in the Prague interbank market lend Czech koruna (CZK) funds to each other. The 3-month PRIBOR (PRIBOR 3M) is the most important tenor and serves as the direct benchmark for corporate loans, credit lines, and floating-rate mortgages.",
        "economic_meaning": "Key reference benchmark of the Czech money market, reflecting market expectations of the CNB repo rate over the given tenor plus a credit and liquidity risk premium.",
        "practical_impact": "Rising 3M PRIBOR immediately increases monthly interest expenses on floating-rate corporate loans; falling PRIBOR relieves corporate cash flow.",
        "primary_source": "Czech National Bank (CNB) & Czech Financial Benchmark Facility (CFBF)",
        "frequency": "Daily fixing (business days around 13:00 CET)",
    },
    "Depozitní sazba ECB (Deposit Facility Rate - DFR)": {
        "term": "ECB Deposit Facility Rate (DFR)",
        "category": "Monetary Policy & Interest Rates",
        "region": "EU",
        "simple_explanation": "The most important interest rate across the entire Eurozone. It determines the interest the European Central Bank (ECB) in Frankfurt pays commercial banks for overnight euro deposits. Given abundant excess reserves in the European banking system, this rate effectively steers the price of credit across all euro-area countries.",
        "economic_meaning": "Primary operational anchor of Eurosystem monetary policy. In an environment of structural excess liquidity, the Deposit Facility Rate acts as the de facto anchor for short-term EUR money market rates.",
        "practical_impact": "Shapes the strength of the euro and the cost of EUR-denominated corporate loans, which many Czech exporters also use to finance operations.",
        "primary_source": "European Central Bank (ECB)",
        "frequency": "ECB Governing Council meetings (every 6 weeks)",
    },
    "EURIBOR (Euro Interbank Offered Rate)": {
        "term": "EURIBOR (Euro Interbank Offered Rate)",
        "category": "Monetary Policy & Interest Rates",
        "region": "EU",
        "simple_explanation": "The European equivalent of PRIBOR—the average interest rate at which leading European banks lend euros to one another. Most mortgages and corporate loans across the Eurozone (as well as EUR loans taken by Czech exporters) are directly indexed to 3M or 6M EURIBOR.",
        "economic_meaning": "Primary EU Benchmark Regulation (BMR) money market reference rate underlying trillions of euros in loans, floating-rate notes, and EUR interest rate swaps.",
        "practical_impact": "For Czech companies borrowing in euros, 3M EURIBOR is the base component of their financing cost.",
        "primary_source": "European Money Markets Institute (EMMI) & ECB",
        "frequency": "Daily fixing at 11:00 CET",
    },
    "€STR (Euro Short-Term Rate)": {
        "term": "€STR (Euro Short-Term Rate)",
        "category": "Monetary Policy & Interest Rates",
        "region": "EU",
        "simple_explanation": "The official overnight risk-free euro interest rate calculated daily by the ECB from actual wholesale money market transactions. It replaced EONIA and serves as the cleanest gauge of the overnight cost of money in the Eurozone.",
        "economic_meaning": "Overnight risk-free rate (RFR) for the euro based on unsecured wholesale borrowing transactions, forming the foundation of the EUR OIS discount curve.",
        "practical_impact": "Used by banks and institutional funds to price derivatives and anchor Eurozone money markets.",
        "primary_source": "European Central Bank (ECB)",
        "frequency": "Daily at 08:00 CET for the previous business day",
    },
    "Fed Funds Target Range": {
        "term": "Fed Funds Target Range",
        "category": "Monetary Policy & Interest Rates",
        "region": "USA",
        "simple_explanation": "The target interest rate range of the U.S. central bank (Federal Reserve / Fed), quoted as a 25 bps band (e.g., 3.25% – 3.50%). Because the U.S. dollar is the world's primary reserve currency, the Fed Funds rate is the single most influential interest rate for global financial markets.",
        "economic_meaning": "Target corridor set by the Federal Open Market Committee (FOMC) for overnight interbank lending of reserve balances, enforced via Interest on Reserve Balances (IORB) and the ON RRP facility.",
        "practical_impact": "Fed rate hikes attract global capital into USD assets and tighten global financial conditions; rate cuts boost global liquidity, equities, and commodities.",
        "primary_source": "Federal Reserve Board (FOMC)",
        "frequency": "8x per year (FOMC meetings)",
    },
    "SOFR (Secured Overnight Financing Rate)": {
        "term": "SOFR (Secured Overnight Financing Rate)",
        "category": "Monetary Policy & Interest Rates",
        "region": "USA",
        "simple_explanation": "The modern U.S. dollar overnight risk-free rate that replaced USD LIBOR. It measures the cost of borrowing cash overnight collateralized by U.S. Treasury securities.",
        "economic_meaning": "Transaction-based benchmark backed by over $1 trillion in daily U.S. Treasury repo volume, serving as the global standard for USD loans, floating-rate notes, and derivatives.",
        "practical_impact": "Reflects immediate funding liquidity on Wall Street and underpins modern USD financial contracts.",
        "primary_source": "Federal Reserve Bank of New York (NY Fed)",
        "frequency": "Every business day at 08:00 EST",
    },
    "Výnos do splatnosti (Yield to Maturity - YTM)": {
        "term": "Yield to Maturity (YTM)",
        "category": "Bonds & Yield Curves",
        "region": "Global",
        "simple_explanation": "The total annualized percentage return an investor earns by buying a bond at today's market price and holding it until maturity. A fundamental rule of finance applies: when a bond's price falls, its yield to maturity rises (and vice versa).",
        "economic_meaning": "Internal rate of return (IRR) equating the present value of all future bond cash flows (coupons and principal) to its current market price.",
        "practical_impact": "Determines the cost of borrowing for governments and corporations across the economy.",
        "primary_source": "Stock Exchanges, Ministries of Finance, Bloomberg, Refinitiv",
        "frequency": "Continuous market trading",
    },
    "10letý státní dluhopis (10Y Benchmark)": {
        "term": "10-Year Government Bond Yield (10Y Benchmark)",
        "category": "Bonds & Yield Curves",
        "region": "Global",
        "simple_explanation": "The gold standard of financial markets. The 10-year government bond yield (10Y CZGB in Czechia, 10Y Bund in Germany, 10Y Treasury in the US) shows the annual return investors demand to lend money to the government for 10 years. It serves as the primary benchmark for fixed-rate mortgages and corporate valuations.",
        "economic_meaning": "Anchor point of the sovereign yield curve reflecting long-term inflation expectations, expected monetary policy path, and the term premium. Used as the risk-free rate (Rf) in DCF valuation models.",
        "practical_impact": "When 10Y bond yields rise, long-term funding costs increase and 5- to 10-year mortgage fixations become more expensive.",
        "primary_source": "MoF CZ / Deutsche Bundesbank / U.S. Treasury",
        "frequency": "Daily market quotes",
    },
    "Výnosová křivka & Normální sklon": {
        "term": "Yield Curve & Normal Slope",
        "category": "Bonds & Yield Curves",
        "region": "Global",
        "simple_explanation": "A chart plotting government bond yields across maturities from shortest (1M/1Y) to longest (10Y/30Y). In a healthy expanding economy, the curve slopes upward ('normal slope'): lending money for longer requires a higher interest rate to compensate for inflation and future uncertainty.",
        "economic_meaning": "Term structure of interest rates. A positive slope reflects a positive term premium compensating investors for duration risk.",
        "practical_impact": "A positively sloped curve enables banks to profitably transform short-term deposits into long-term loans, supporting healthy credit growth.",
        "primary_source": "CNB, ECB, and U.S. Department of the Treasury",
        "frequency": "Continuous updates",
    },
    "Inverze výnosové křivky (Inverted Yield Curve)": {
        "term": "Inverted Yield Curve",
        "category": "Bonds & Yield Curves",
        "region": "Global",
        "simple_explanation": "An unusual market anomaly where short-term bonds (e.g., 2-year) pay higher yields than long-term bonds (10-year). This occurs when the central bank hikes short-term rates sharply to fight inflation, but investors expect the economy to slow into a recession and force future rate cuts. Historically, it is the most reliable leading indicator of a recession.",
        "economic_meaning": "Negative spread between long- and short-dated yields (10Y − 2Y < 0), signaling market expectations of monetary policy easing due to macroeconomic slowdown.",
        "practical_impact": "Compresses bank net interest margins (NIM), tightening credit standards and slowing lending to the real economy.",
        "primary_source": "Financial markets, St. Louis Fed (FRED)",
        "frequency": "Monitored daily",
    },
    "Spread 10Y − 2Y": {
        "term": "10Y − 2Y Yield Curve Spread",
        "category": "Bonds & Yield Curves",
        "region": "Global",
        "simple_explanation": "The difference between the 10-year and 2-year government bond yield expressed in percentage points or basis points (100 bps = 1.00%). Positive values indicate a normal upward-sloping curve; negative values indicate yield curve inversion.",
        "economic_meaning": "Standard quantitative gauge of yield curve steepness. Re-steepening ('un-inversion') from negative back above zero often precedes the onset of a recession as central banks begin cutting short-term rates.",
        "practical_impact": "Key macro signal for asset allocation between equities, fixed income, and cash.",
        "primary_source": "Calculated from MoF CZ, Bundesbank, and U.S. Treasury data",
        "frequency": "Daily data",
    },
    "Sovereign Credit Spread (CZGB vs. Bund)": {
        "term": "Sovereign Credit Spread (CZGB vs. Bund)",
        "category": "Bonds & Yield Curves",
        "region": "CZ & EU",
        "simple_explanation": "The extra yield the Czech government must pay on its 10-year bond compared to Germany's 10-year Bund (Europe's safest benchmark). It reflects the interest rate differential between the CNB and ECB as well as currency and fiscal risk perceptions.",
        "economic_meaning": "Yield differential (YTM_CZGB − YTM_Bund) in basis points, capturing the CZK-EUR interest rate differential, currency risk premium, and sovereign creditworthiness.",
        "practical_impact": "Measures international investor confidence in Czech public finances. A narrow spread keeps state debt servicing costs low.",
        "primary_source": "MoF CZ & Deutsche Bundesbank",
        "frequency": "Daily calculation",
    },
    "Úrokové swapy (CZK IRS)": {
        "term": "Interest Rate Swaps (CZK IRS)",
        "category": "Bonds & Yield Curves",
        "region": "CZ",
        "simple_explanation": "An interbank contract exchanging a floating interest rate (PRIBOR) for a fixed rate over a multi-year period (e.g., 5Y or 10Y IRS). Czech banks directly price fixed-rate mortgages off the CZK IRS curve.",
        "economic_meaning": "Over-the-counter derivative instrument used for asset-liability management (ALM), representing the market's expected path of interbank rates over the swap tenor.",
        "practical_impact": "When 5Y or 10Y CZK IRS rates rise, commercial banks raise fixed mortgage interest rates within days or weeks.",
        "primary_source": "Interbank OTC Derivatives Market",
        "frequency": "Continuous interbank quotes",
    },
    "Měnový kurz EUR/CZK & USD/CZK": {
        "term": "EUR/CZK & USD/CZK Exchange Rates",
        "category": "Exchange Rates & FX Market",
        "region": "CZ",
        "simple_explanation": "The price of one euro or U.S. dollar in Czech koruna. When EUR/CZK falls (e.g., from 25.50 to 25.00 CZK), the koruna strengthens—making imported goods, fuel, electronics, and foreign travel cheaper for Czech households, while reducing CZK revenues for exporters.",
        "economic_meaning": "Nominal bilateral exchange rate. In a small open export-oriented economy where exports exceed 70% of GDP, the exchange rate channel is a powerful component of overall monetary conditions.",
        "practical_impact": "A stronger koruna dampens imported inflation; a weaker koruna boosts exporter price competitiveness but raises import costs.",
        "primary_source": "Czech National Bank (CNB Daily FX Fixing)",
        "frequency": "Daily official CNB fixing at 14:30 CET",
    },
    "Dolarový index (DXY / U.S. Dollar Index)": {
        "term": "U.S. Dollar Index (DXY)",
        "category": "Exchange Rates & FX Market",
        "region": "US & Global",
        "simple_explanation": "An index measuring the overall strength of the U.S. dollar against a basket of six major world currencies (led by the euro at 57.6% weight, followed by JPY, GBP, CAD, SEK, and CHF). When DXY rises, the dollar is strengthening globally.",
        "economic_meaning": "Geometrically weighted index of USD value established in 1973 (base = 100), acting as a global barometer of USD liquidity and risk aversion.",
        "practical_impact": "A strong dollar (high DXY) puts downward pressure on USD-denominated commodities (gold, oil, copper) and emerging-market currencies.",
        "primary_source": "Intercontinental Exchange (ICE)",
        "frequency": "Real-time / daily settlement",
    },
    "Úrokový diferenciál (Interest Rate Differential)": {
        "term": "Interest Rate Differential",
        "category": "Exchange Rates & FX Market",
        "region": "Global",
        "simple_explanation": "The difference in policy interest rates between two central banks (e.g., CNB rate minus ECB rate). International investors favor currencies offering higher yields ('carry trade'), so a positive interest rate differential supports the Czech koruna.",
        "economic_meaning": "Core variable in Uncovered Interest Rate Parity (UIP), driving short-term cross-border capital flows and forward FX points.",
        "practical_impact": "If the CNB cuts rates faster than the ECB or Fed, the koruna loses its yield advantage and may face depreciation pressure.",
        "primary_source": "Central bank policy rates (CNB vs. ECB vs. Fed)",
        "frequency": "Continuous across central bank meetings",
    },
    "Hrubý domácí produkt (HDP / GDP)": {
        "term": "Gross Domestic Product (GDP)",
        "category": "Economic Growth & GDP",
        "region": "Global",
        "simple_explanation": "The total monetary value of all final goods and services produced within a country over a given period (typically a quarter or a year). It is the comprehensive scorecard of an economy's size and performance.",
        "economic_meaning": "Aggregate macroeconomic output measured via production (value added), expenditure (C + I + G + NX), or income approaches.",
        "practical_impact": "Growing GDP translates into job creation, higher corporate earnings, rising wages, and stronger government tax revenues.",
        "primary_source": "CZSO (CZ) / Eurostat (EU) / U.S. BEA (US)",
        "frequency": "Quarterly (flash estimate and revised national accounts)",
    },
    "Reálný vs. Nominální růst HDP": {
        "term": "Real vs. Nominal GDP Growth",
        "category": "Economic Growth & GDP",
        "region": "Global",
        "simple_explanation": "Nominal GDP measures output at current market prices, so it rises even if prices simply inflate without more goods being produced. Real GDP strips out inflation to measure the true physical growth in goods and services produced.",
        "economic_meaning": "Nominal GDP is valued at current prices, whereas Real GDP is chain-linked at constant prices using the GDP deflator to isolate volume growth.",
        "practical_impact": "Only real GDP growth delivers genuine improvements in living standards and societal wealth.",
        "primary_source": "Statistical offices (CZSO, Eurostat, BEA)",
        "frequency": "Quarterly",
    },
    "Hospodářská recese (Technická recese)": {
        "term": "Economic Recession (Technical Recession)",
        "category": "Economic Growth & GDP",
        "region": "Global",
        "simple_explanation": "A period when economic output contracts instead of growing. A 'technical recession' is defined as two consecutive quarters of negative quarter-on-quarter real GDP growth.",
        "economic_meaning": "Contractionary phase of the business cycle characterized by a negative output gap, declining investment, rising unemployment, and disinflationary pressure.",
        "practical_impact": "During recessions, central banks typically cut interest rates and governments deploy fiscal stimulus to restore growth.",
        "primary_source": "Official national accounts statistics / NBER (US)",
        "frequency": "Evaluated quarterly",
    },
}

GLOSSARY_I18N_EN.update({
    "Spotřebitelská inflace (CPI Headline)": {
        "term": "Headline Consumer Inflation (CPI)",
        "category": "Inflation & Price Level",
        "region": "Global",
        "simple_explanation": "The rate at which everyday prices rise. Statisticians track a 'consumer basket' of hundreds of goods and services bought by a typical household—food, housing, utilities, transport, and clothing. YoY inflation of 2.5% means a basket costing 100 last year costs 102.50 today.",
        "economic_meaning": "Consumer Price Index (CPI / HICP) measuring the weighted change in the price level of household consumption goods and services. Primary target metric for inflation-targeting central banks.",
        "practical_impact": "High inflation erodes uninvested cash savings and purchasing power; low and stable inflation enables predictable financial planning.",
        "primary_source": "CZSO (CZ) / Eurostat (HICP in EU) / BLS (USA)",
        "frequency": "Monthly (around the 10th of the following month)",
    },
    "Jádrová inflace (Core CPI / Core HICP)": {
        "term": "Core Inflation (Core CPI / Core HICP)",
        "category": "Inflation & Price Level",
        "region": "Global",
        "simple_explanation": "Underlying inflation that strips out volatile food and energy prices (fuel, electricity, gas) and tax changes. It reveals persistent domestic price pressures in services, housing, and wages.",
        "economic_meaning": "Measure of trend inflation excluding exogenous supply shocks and regulated price adjustments, serving as the primary guide for medium-term monetary policy.",
        "practical_impact": "If core inflation remains sticky, central banks keep interest rates elevated even if headline inflation temporarily dips due to cheaper oil.",
        "primary_source": "CNB / Eurostat / U.S. Bureau of Labor Statistics",
        "frequency": "Monthly",
    },
    "Inflační cíl (2,0 %)": {
        "term": "Inflation Target (2.0%)",
        "category": "Inflation & Price Level",
        "region": "Global",
        "simple_explanation": "The 2.0% annual inflation rate targeted by modern central banks (CNB, ECB, Fed). Mild inflation around 2% acts as 'lubricant' for the economy, encouraging investment and preventing harmful deflation.",
        "economic_meaning": "Nominal anchor for medium-term inflation expectations under an Inflation Targeting regime (CNB target: 2.0% with a ±1 pp tolerance band of 1.0%–3.0%).",
        "practical_impact": "When inflation exceeds the target, central banks hike rates; when inflation falls below target, they cut rates.",
        "primary_source": "Monetary policy strategy of CNB / ECB / Fed",
        "frequency": "Long-term strategic target",
    },
    "Reálná úroková míra (Real Interest Rate)": {
        "term": "Real Interest Rate",
        "category": "Inflation & Price Level",
        "region": "Global",
        "simple_explanation": "The true return on money after subtracting inflation (nominal interest rate minus inflation, per the Fisher equation). If your savings account pays 4.0% and inflation is 2.5%, your real interest rate is +1.5% (your purchasing power grows).",
        "economic_meaning": "Ex-ante or ex-post real cost of capital (r = i − π), governing intertemporal consumption and investment decisions.",
        "practical_impact": "Positive real rates reward savers and restrain excessive borrowing; negative real rates erode cash savings.",
        "primary_source": "Analytical calculation from interest rate and CPI data",
        "frequency": "Continuous",
    },
    "Maloobchodní tržby (Retail Sales YoY)": {
        "term": "Retail Sales (YoY)",
        "category": "Real Economy & Business Cycle",
        "region": "Global",
        "simple_explanation": "Tracks total household spending in physical and online stores. When households feel confident and real wages grow, retail sales expand; when uncertainty rises, consumers cut back on discretionary spending.",
        "economic_meaning": "Year-on-year real change in retail trade turnover (deflated for price changes), acting as a key monthly proxy for household consumption (~50–70% of GDP).",
        "practical_impact": "Strong retail sales signal resilient domestic demand, while sharp drops warn of economic cooling.",
        "primary_source": "CZSO / Eurostat / U.S. Census Bureau",
        "frequency": "Monthly",
    },
    "Průmyslová produkce (Industrial Production YoY)": {
        "term": "Industrial Production (YoY)",
        "category": "Real Economy & Business Cycle",
        "region": "Global",
        "simple_explanation": "Measures real output across factories, mines, and power plants. Crucial for the Czech Republic, one of Europe's most industrialized economies (led by automotive manufacturing and engineering).",
        "economic_meaning": "Industrial Production Index (IPI) at constant prices covering manufacturing, mining, and utilities, highly correlated with German industrial demand and exports.",
        "practical_impact": "Key indicator of manufacturing health, export momentum, and industrial employment.",
        "primary_source": "CZSO / Eurostat / Federal Reserve (G.17)",
        "frequency": "Monthly",
    },
    "Míra nezaměstnanosti (Metodika ILO)": {
        "term": "Unemployment Rate (ILO Methodology)",
        "category": "Labor Market & Employment",
        "region": "Global",
        "simple_explanation": "Internationally comparable percentage of the labor force that is jobless, actively seeking work, and immediately available to start. The Czech Republic consistently ranks among the countries with the lowest unemployment in the EU.",
        "economic_meaning": "Share of unemployed persons in the economically active population based on the Labour Force Survey (LFS) under International Labour Organization (ILO) standards.",
        "practical_impact": "Low unemployment gives workers strong bargaining power for wage increases but creates labor shortages for employers.",
        "primary_source": "Eurostat / CZSO (LFS) / U.S. BLS",
        "frequency": "Monthly",
    },
    "Podíl nezaměstnaných osob (MPSV ČR)": {
        "term": "Share of Unemployed Persons (MoLSA CZ)",
        "category": "Labor Market & Employment",
        "region": "CZ",
        "simple_explanation": "National administrative unemployment rate published monthly by the Czech Ministry of Labor and Social Affairs (MoLSA), measuring registered job applicants aged 15–64 relative to the total population of the same age.",
        "economic_meaning": "Administrative labor market indicator capturing registered reachable job seekers at Czech Labor Offices.",
        "practical_impact": "Provides granular monthly insight into regional labor markets and job vacancy ratios across Czech districts.",
        "primary_source": "Ministry of Labor and Social Affairs CZ (MoLSA)",
        "frequency": "Monthly",
    },
    "Index PX (Pražská burza)": {
        "term": "PX Index (Prague Stock Exchange)",
        "category": "Equity Markets & Stock Indices",
        "region": "CZ",
        "simple_explanation": "The official benchmark index of the Prague Stock Exchange (PSE), tracking leading Czech blue-chip companies—primarily banks (Erste Group, Komercni banka, Moneta), energy utility CEZ, and Colt CZ. Known for high dividend yields.",
        "economic_meaning": "Free-float market-capitalization-weighted price index of the Prague Stock Exchange (established in 1994 with a base of 1,000 points).",
        "practical_impact": "Core benchmark for domestic equity investors and Czech pension funds.",
        "primary_source": "Prague Stock Exchange (PSE / BCPP)",
        "frequency": "Real-time on trading days (09:00–16:20 CET)",
    },
    "Euro Stoxx 50": {
        "term": "Euro Stoxx 50",
        "category": "Equity Markets & Stock Indices",
        "region": "EU",
        "simple_explanation": "The flagship blue-chip stock index of the Eurozone, comprising 50 sector-leading corporations across 8 euro-area countries (including ASML, SAP, LVMH, Siemens, TotalEnergies, and Allianz).",
        "economic_meaning": "Free-float market-cap-weighted index managed by STOXX Ltd. (Deutsche Börse Group) with a 10% component cap.",
        "practical_impact": "Primary benchmark for European equity ETFs and corporate earnings sentiment in the Eurozone.",
        "primary_source": "STOXX Ltd. / Deutsche Börse",
        "frequency": "Real-time during European trading hours",
    },
    "S&P 500": {
        "term": "S&P 500",
        "category": "Equity Markets & Stock Indices",
        "region": "US & Global",
        "simple_explanation": "The world's most closely watched stock market index, tracking 500 of the largest publicly traded U.S. corporations (Apple, Microsoft, Nvidia, Amazon, Alphabet, Berkshire Hathaway, etc.) and representing ~80% of total U.S. equity market value.",
        "economic_meaning": "Float-adjusted market-cap-weighted index maintained by S&P Dow Jones Indices requiring positive trailing 4-quarter GAAP earnings and high liquidity.",
        "practical_impact": "Cornerstone of global investment portfolios and retirement funds worldwide.",
        "primary_source": "S&P Dow Jones Indices",
        "frequency": "Real-time during NYSE / NASDAQ trading hours",
    },
    "NASDAQ Composite": {
        "term": "NASDAQ Composite",
        "category": "Equity Markets & Stock Indices",
        "region": "US & Global",
        "simple_explanation": "A broad index of over 3,000 stocks listed on the NASDAQ exchange, heavily weighted toward technology, semiconductors, software, AI, internet platforms, and biotech.",
        "economic_meaning": "Market-capitalization-weighted index with high exposure to long-duration growth equities, exhibiting higher sensitivity (beta) to interest rate changes.",
        "practical_impact": "Barometer of global technology innovation, AI investment, and investor risk appetite.",
        "primary_source": "NASDAQ OMX Group",
        "frequency": "Real-time (15:30–22:00 CET)",
    },
    "Normalizované srovnání výkonnosti (Báze = 100)": {
        "term": "Normalized Performance Comparison (Rebase = 100)",
        "category": "Equity Markets & Stock Indices",
        "region": "Global",
        "simple_explanation": "A mathematical method to fairly compare assets with very different nominal point levels (e.g., PX at 2,600 pts vs. NASDAQ at 27,000 pts). All series are rescaled to 100 at the start of the selected period so relative percentage gains are immediately visible.",
        "economic_meaning": "Time-series indexing: Index_t = (Price_t / Price_t0) × 100, eliminating scale bias across asset classes.",
        "practical_impact": "Essential analytical tool for comparing cumulative returns across indices, currencies, and commodities.",
        "primary_source": "Financial analysis standard",
        "frequency": "Computed dynamically for any selected time horizon",
    },
    "Veřejný vládní dluh k HDP (% HDP)": {
        "term": "General Government Debt to GDP (% GDP)",
        "category": "Public Finance & Government Debt",
        "region": "Global",
        "simple_explanation": "Measures a country's total public debt relative to the size of its annual economic output (GDP). Czechia's debt (~44% of GDP) remains well below the Eurozone average (~88% of GDP) and the US (>120% of GDP).",
        "economic_meaning": "Consolidated general government gross debt (ESA 2010 methodology in the EU) divided by nominal annual GDP—the premier gauge of sovereign fiscal sustainability.",
        "practical_impact": "Countries with lower debt-to-GDP ratios enjoy higher credit ratings and spend less tax revenue on debt interest payments.",
        "primary_source": "MoF CZ / Eurostat (EDP) / U.S. Treasury",
        "frequency": "Quarterly notifications and annual revisions",
    },
    "Maastrichtská konvergenční kritéria": {
        "term": "Maastricht Convergence Criteria",
        "category": "Public Finance & Government Debt",
        "region": "EU & CZ",
        "simple_explanation": "EU fiscal discipline rules established by the Maastricht Treaty, setting two famous thresholds: (1) Public debt must not exceed 60% of GDP, and (2) Annual government budget deficit must not exceed 3% of GDP.",
        "economic_meaning": "Fiscal and monetary convergence rules enshrined in the Stability and Growth Pact (SGP) and required for Eurozone accession.",
        "practical_impact": "Anchors fiscal discipline across EU member states and safeguards sovereign debt sustainability.",
        "primary_source": "European Commission & EU Council",
        "frequency": "Semi-annual and annual fiscal surveillance",
    },
    "Saldo státního rozpočtu (Deficit / Přebytek)": {
        "term": "State Budget Balance (Deficit / Surplus)",
        "category": "Public Finance & Government Debt",
        "region": "Global",
        "simple_explanation": "The difference between government revenues (taxes, duties) and expenditures. When spending exceeds revenue, the government runs a budget deficit that must be financed by issuing government bonds.",
        "economic_meaning": "Net lending (+) or net borrowing (−) of the government sector, comprising a structural component and a cyclical component.",
        "practical_impact": "Persistent structural deficits increase public debt and require future fiscal consolidation.",
        "primary_source": "Ministry of Finance CZ / Eurostat / U.S. Treasury",
        "frequency": "Monthly cash execution & quarterly national accounts",
    },
    "Náklady na obsluhu státního dluhu": {
        "term": "Government Debt Servicing Costs",
        "category": "Public Finance & Government Debt",
        "region": "Global",
        "simple_explanation": "The annual interest payments the state must pay to holders of its government bonds. Higher interest rates and larger debt volumes directly increase these mandatory budget expenses.",
        "economic_meaning": "General government interest expenditure, determined by total debt stock and the weighted average yield of the sovereign bond portfolio.",
        "practical_impact": "Higher debt service costs crowd out productive public spending on infrastructure, education, and healthcare.",
        "primary_source": "Ministry of Finance CZ (Debt Management Report)",
        "frequency": "Quarterly and annual MoF reports",
    },
    "PMI v průmyslu ČR (S&P Global)": {
        "term": "CZ Manufacturing PMI (S&P Global)",
        "category": "Leading Indicators & Sentiment",
        "region": "CZ",
        "simple_explanation": "Monthly survey of purchasing managers in Czech manufacturing companies tracking new orders, output, employment, supplier delivery times, and inventories. 50.0 is the dividing line: above 50 signals expansion, below 50 contraction.",
        "economic_meaning": "Diffusion index compiled by S&P Global from weighted sub-indices (New Orders 30%, Output 25%, Employment 20%, Suppliers' Delivery Times 15%, Stocks of Purchases 10%), leading hard industrial data by 1–2 months.",
        "practical_impact": "Provides the earliest monthly signal of turning points in Czech manufacturing and export demand.",
        "primary_source": "S&P Global Czech Republic Manufacturing PMI",
        "frequency": "Monthly (first business day of the month)",
    },
    "Důvěra podnikatelů a spotřebitelů (ČSÚ)": {
        "term": "Business & Consumer Confidence (CZSO)",
        "category": "Leading Indicators & Sentiment",
        "region": "CZ",
        "simple_explanation": "Official monthly survey by the Czech Statistical Office among thousands of Czech businesses and households gauging economic expectations, hiring plans, and household financial outlook (long-term average = 100 points).",
        "economic_meaning": "Composite Economic Sentiment Indicator harmonized with European Commission methodology (80% business confidence across industry, construction, retail, and services; 20% consumer confidence).",
        "practical_impact": "Rising confidence precedes stronger retail sales and corporate investment; falling confidence signals precautionary saving.",
        "primary_source": "Czech Statistical Office (CZSO – Business Cycle Surveys)",
        "frequency": "Monthly (around the 24th of the month)",
    },
    "Průměrná hrubá mzda nominálně (YoY)": {
        "term": "Average Gross Nominal Wage (YoY)",
        "category": "Labor Market & Wages",
        "region": "CZ",
        "simple_explanation": "The year-on-year percentage increase in the average gross monthly paycheck of Czech employees before deducting inflation and taxes.",
        "economic_meaning": "Nominal YoY growth of full-time equivalent (FTE) average gross monthly earnings in the Czech national economy.",
        "practical_impact": "Rapid nominal wage growth boosts household income but is closely watched by the CNB as a driver of services inflation.",
        "primary_source": "Czech Statistical Office (CZSO)",
        "frequency": "Quarterly",
    },
    "Průměrná reálná mzda (YoY)": {
        "term": "Average Real Wage (YoY)",
        "category": "Labor Market & Wages",
        "region": "CZ",
        "simple_explanation": "Wage growth adjusted for inflation—showing whether employees can actually buy more goods and services with their paycheck than a year ago.",
        "economic_meaning": "Ratio of the nominal wage index to the Consumer Price Index (CPI), measuring changes in real household purchasing power.",
        "practical_impact": "Positive real wage growth is the primary engine of household consumption recovery.",
        "primary_source": "Czech Statistical Office (CZSO)",
        "frequency": "Quarterly",
    },
    "Nové hypotéky – objem a průměrná sazba": {
        "term": "New Mortgages – Volume & Average Rate",
        "category": "Banking Sector & Loans",
        "region": "CZ",
        "simple_explanation": "Monthly volume (in CZK billions) of newly originated residential mortgages in Czechia (excluding refinancing) and their average realized interest rate.",
        "economic_meaning": "CBA Hypomonitor and CNB ARAD statistics on new household housing loans, capturing monetary policy pass-through and housing market activity.",
        "practical_impact": "Direct barometer of housing affordability and real estate market momentum.",
        "primary_source": "Czech Banking Association (CBA Hypomonitor) & CNB ARAD",
        "frequency": "Monthly",
    },
    "Korporátní úvěry – meziroční růst": {
        "term": "Corporate Loans – YoY Growth",
        "category": "Banking Sector & Loans",
        "region": "CZ",
        "simple_explanation": "Year-on-year percentage change in total bank loans extended to non-financial corporations in the Czech Republic (including both CZK and EUR loans).",
        "economic_meaning": "Credit growth to non-financial corporations from CNB monetary statistics, reflecting corporate investment appetite and bank lending standards.",
        "practical_impact": "High CZK interest rates have prompted many Czech exporters to borrow in EUR ('euroization' of corporate credit).",
        "primary_source": "Czech National Bank (ARAD – Monetary Statistics)",
        "frequency": "Monthly",
    },
    "Měnový agregát M2 (YoY)": {
        "term": "M2 Money Supply (YoY)",
        "category": "Monetary Policy & Money Supply",
        "region": "CZ",
        "simple_explanation": "Year-on-year growth of the total money supply in the Czech economy—including physical cash, checking accounts, and savings/term deposits up to 2 years.",
        "economic_meaning": "Broad money aggregate M2 (M1 currency and overnight deposits + deposits with agreed maturity up to 2 years and redeemable at notice up to 3 months).",
        "practical_impact": "Rapid M2 expansion signals abundant liquidity and potential medium-term inflationary pressures.",
        "primary_source": "Czech National Bank (Monetary Statistics)",
        "frequency": "Monthly",
    },
    "Běžný účet platební bilance (k HDP)": {
        "term": "Current Account Balance (% GDP)",
        "category": "External Balance & International Trade",
        "region": "CZ",
        "simple_explanation": "The country's comprehensive external balance sheet with the rest of the world as a percentage of GDP—combining trade in goods and services, investment income (dividends), and EU transfers.",
        "economic_meaning": "Current Account Balance to GDP (representing national savings minus investment, S − I).",
        "practical_impact": "A current account surplus supports the stability and appreciation of the Czech koruna.",
        "primary_source": "Czech National Bank (Balance of Payments) & CZSO",
        "frequency": "Quarterly and monthly",
    },
    "Bilance zahraničního obchodu ČSÚ": {
        "term": "Foreign Trade Balance (CZSO)",
        "category": "External Balance & International Trade",
        "region": "CZ",
        "simple_explanation": "Monthly difference between the value of Czech goods exported abroad (cars, machinery, electronics) and goods imported into Czechia (oil, gas, components) in CZK billions.",
        "economic_meaning": "Monthly merchandise trade balance compiled by the CZSO under the national concept.",
        "practical_impact": "A structural trade surplus is a key pillar of Czech GDP growth and koruna demand.",
        "primary_source": "Czech Statistical Office (CZSO – External Trade)",
        "frequency": "Monthly (around the 6th of the month)",
    },
    "Kreditní spread 10Y CZGB vs. 10Y Bund": {
        "term": "10Y CZGB vs. 10Y Bund Credit Spread",
        "category": "Bond Market & Spreads",
        "region": "CZ & EU",
        "simple_explanation": "Yield difference in basis points (100 bps = 1.00%) between the 10-year Czech government bond (CZGB) and the 10-year German Bund.",
        "economic_meaning": "Sovereign yield spread reflecting the CNB-ECB policy rate differential, inflation premium, and sovereign risk.",
        "practical_impact": "Tracks relative borrowing costs of the Czech state versus the Eurozone core.",
        "primary_source": "MoF CZ / Deutsche Bundesbank / Eurostat",
        "frequency": "Daily and monthly",
    },
    "Asset Swap Spread (ASW 10Y CZK)": {
        "term": "Asset Swap Spread (10Y CZK ASW)",
        "category": "Bond Market & Spreads",
        "region": "CZ",
        "simple_explanation": "The spread in basis points between the 10-year Czech government bond yield (CZGB) and the 10-year CZK interest rate swap (IRS) rate, indicating whether government bonds are cheap or rich relative to the swap curve.",
        "economic_meaning": "Asset Swap (ASW) spread measuring the sovereign bond yield premium over the interbank CZK IRS curve.",
        "practical_impact": "Key relative-value metric for fixed-income portfolio managers, bank treasuries, and primary dealers.",
        "primary_source": "Interbank Swap Market & MoF CZ",
        "frequency": "Daily and monthly",
    },
    "Německý Ifo index podnikatelského klimatu": {
        "term": "German Ifo Business Climate Index",
        "category": "Leading Indicators & Sentiment",
        "region": "EU",
        "simple_explanation": "The premier monthly business sentiment survey of Germany's economy, based on responses from ~9,000 German firms. Because Germany is Czechia's largest trading partner, the Ifo index is a critical leading indicator for Czech exporters.",
        "economic_meaning": "Ifo Geschäftsklimaindex combining assessments of current business conditions and 6-month expectations across German industry, services, trade, and construction.",
        "practical_impact": "Rises and falls in the German Ifo index directly foreshadow order book trends for Czech industrial suppliers.",
        "primary_source": "Ifo Institute Munich",
        "frequency": "Monthly (around the 25th of the month)",
    },
    "Composite PMI Eurozóny": {
        "term": "Eurozone Composite PMI",
        "category": "Leading Indicators & Sentiment",
        "region": "EU",
        "simple_explanation": "Combined Purchasing Managers' Index across both manufacturing and services in the 20-country Eurozone. Readings above 50 signal economic expansion; readings below 50 signal contraction.",
        "economic_meaning": "HCOB / S&P Global Eurozone Composite Output Index based on surveys of over 5,000 euro-area companies, serving as a reliable real-time nowcast of Eurozone GDP growth.",
        "practical_impact": "Closely watched by the ECB Governing Council and EUR/USD traders.",
        "primary_source": "S&P Global & Hamburg Commercial Bank (HCOB)",
        "frequency": "Monthly (flash around the 22nd, final at month start)",
    },
    "Sjednané mzdy v Eurozóně (ECB YoY)": {
        "term": "Eurozone Negotiated Wages (ECB YoY)",
        "category": "Labor Market & Wages",
        "region": "EU",
        "simple_explanation": "Official ECB indicator tracking year-on-year wage growth agreed in collective bargaining agreements across Eurozone countries.",
        "economic_meaning": "Euro Area Negotiated Wage Growth indicator compiled by the ECB, serving as a primary gauge of domestic wage-push inflation persistence in services.",
        "practical_impact": "Elevated negotiated wage growth (>3.5–4.0%) makes the ECB more cautious about cutting interest rates.",
        "primary_source": "European Central Bank (ECB Statistical Data Warehouse)",
        "frequency": "Quarterly",
    },
    "Rizikový spread Itálie vs. Německo (10Y BTP - Bund)": {
        "term": "Italy vs. Germany Risk Spread (10Y BTP - Bund)",
        "category": "Bond Market & Spreads",
        "region": "EU",
        "simple_explanation": "The yield difference in basis points between Italy's 10-year government bond (BTP) and Germany's 10-year Bund—the classic barometer of financial stress and fragmentation risk in the Eurozone.",
        "economic_meaning": "BTP-Bund 10Y sovereign spread in bps, measuring fiscal and credit risk premia in the southern Eurozone periphery.",
        "practical_impact": "Sharp widening above 200–250 bps can trigger ECB intervention via the Transmission Protection Instrument (TPI).",
        "primary_source": "MTS / Bloomberg / Deutsche Bundesbank & Banca d'Italia",
        "frequency": "Daily and monthly",
    },
    "ISM Index ve výrobě (Manufacturing PMI)": {
        "term": "US ISM Manufacturing PMI",
        "category": "Leading Indicators & Sentiment",
        "region": "USA",
        "simple_explanation": "The flagship monthly survey of U.S. manufacturing purchasing managers by the Institute for Supply Management. Readings above 50 indicate industrial expansion; readings below 50 indicate contraction.",
        "economic_meaning": "Diffusion index tracking new orders, production, employment, supplier deliveries, and inventories across 300+ U.S. industrial firms.",
        "practical_impact": "Immediate market mover for the U.S. dollar, Wall Street equities, and global Treasury yields.",
        "primary_source": "Institute for Supply Management (ISM)",
        "frequency": "Monthly (first business day of the month)",
    },
    "ISM Index ve službách (Services PMI)": {
        "term": "US ISM Services PMI",
        "category": "Leading Indicators & Sentiment",
        "region": "USA",
        "simple_explanation": "Monthly survey of purchasing executives in the U.S. services sector (finance, healthcare, IT, retail, logistics), which accounts for over 75% of total U.S. GDP.",
        "economic_meaning": "ISM Non-Manufacturing / Services PMI measuring business activity, new orders, employment, and prices in the U.S. services economy (50 = expansion threshold).",
        "practical_impact": "Demonstrates the resilience of the U.S. consumer and services economy.",
        "primary_source": "Institute for Supply Management (ISM)",
        "frequency": "Monthly (third business day of the month)",
    },
    "Spotřebitelský sentiment (Univ. of Michigan)": {
        "term": "US Consumer Sentiment (Univ. of Michigan)",
        "category": "Leading Indicators & Sentiment",
        "region": "USA",
        "simple_explanation": "Renowned monthly survey by the University of Michigan measuring how U.S. households view their personal finances, business conditions, and 1-year / 5-year inflation expectations.",
        "economic_meaning": "University of Michigan Consumer Sentiment Index (MCSI), closely monitored by the Federal Reserve for household inflation expectations.",
        "practical_impact": "Because consumer spending drives ~70% of U.S. GDP, swings in consumer sentiment directly impact future U.S. growth.",
        "primary_source": "University of Michigan (Surveys of Consumers)",
        "frequency": "Monthly (preliminary mid-month, final month-end)",
    },
    "Průměrná hodinová mzda USA (Average Hourly Earnings YoY)": {
        "term": "US Average Hourly Earnings (YoY)",
        "category": "Labor Market & Wages",
        "region": "USA",
        "simple_explanation": "Year-on-year percentage growth in the average hourly pay of U.S. private-sector employees, released monthly alongside Nonfarm Payrolls (NFP).",
        "economic_meaning": "Average Hourly Earnings of All Private Nonfarm Employees (YoY) published by the U.S. Bureau of Labor Statistics.",
        "practical_impact": "Key indicator of U.S. labor market tightness and wage-driven inflation pressures for the Fed.",
        "primary_source": "U.S. Bureau of Labor Statistics (BLS – Employment Situation)",
        "frequency": "Monthly (first Friday of the month)",
    },
    "Index volatility VIX": {
        "term": "Cboe Volatility Index (VIX)",
        "category": "Market Sentiment & Risk",
        "region": "US & Global",
        "simple_explanation": "Wall Street's famous 'Fear Index'. It measures the market's expectation of 30-day volatility on the S&P 500 index derived from option prices. Readings below 15 signal market calm; readings above 30 signal acute market stress and panic.",
        "economic_meaning": "Cboe Volatility Index (VIX) representing annualized 30-day implied volatility derived from S&P 500 index call and put options.",
        "practical_impact": "Primary barometer of global risk aversion, portfolio hedging demand, and market stress.",
        "primary_source": "Chicago Board Options Exchange (Cboe) & Yahoo Finance",
        "frequency": "Daily / real-time",
    },
})

_orig_render_glossary_view = render_glossary_view


def render_glossary_view(active_filter_category: Optional[str] = None):
    """Renders the Explanatory Glossary in Czech or English depending on active language."""
    try:
        from i18n import is_en
        en_mode = is_en()
    except Exception:
        en_mode = False

    if not en_mode:
        return _orig_render_glossary_view(active_filter_category=active_filter_category)

    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%); border-radius: 10px; padding: 18px 22px; color: white; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.12);">
            <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
                <div>
                    <div style="font-size: 1.40rem; font-weight: 800; letter-spacing: -0.02em;">📖 Macroeconomic & Financial Explanatory Glossary</div>
                    <div style="font-size: 0.85rem; color: #cbd5e1; margin-top: 4px;">Clear, economically rigorous, and practical guide to all monitored indicators for both laymen and investors</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Build localized items list
    en_items: List[GlossaryItem] = []
    for it in GLOSSARY_ITEMS:
        tr_item = GLOSSARY_I18N_EN.get(it.term)
        if tr_item:
            en_items.append(
                GlossaryItem(
                    term=tr_item["term"],
                    category=tr_item["category"],
                    region=tr_item["region"],
                    simple_explanation=tr_item["simple_explanation"],
                    economic_meaning=tr_item["economic_meaning"],
                    practical_impact=tr_item["practical_impact"],
                    primary_source=tr_item["primary_source"],
                    frequency=tr_item["frequency"],
                )
            )
        else:
            en_items.append(it)

    col_search, col_cat, col_reg = st.columns([2.0, 1.5, 1.2])
    with col_search:
        search_kw = st.text_input(
            "🔍 Search glossary (term, explanation, impact):",
            placeholder="e.g. repo, inflation, yield curve, spread, DXY, PRIBOR...",
            key="glossary_search_kw_en",
        )

    categories = ["All Categories"] + sorted(list(set(item.category for item in en_items)))
    with col_cat:
        selected_cat = st.selectbox(
            "Term Category:",
            categories,
            index=0,
            key="glossary_select_cat_en",
        )

    regions = ["All Regions", "CZ", "EU", "USA", "Global"]
    with col_reg:
        selected_reg = st.selectbox(
            "Region / Country:",
            regions,
            key="glossary_select_reg_en",
        )

    filtered_items = en_items
    if selected_cat != "All Categories":
        filtered_items = [it for it in filtered_items if it.category == selected_cat]

    if selected_reg != "All Regions":
        reg_match = "US" if selected_reg == "USA" else selected_reg
        filtered_items = [it for it in filtered_items if reg_match in it.region or it.region == "Global"]

    if search_kw.strip():
        q = search_kw.strip().lower()
        filtered_items = [
            it for it in filtered_items
            if (
                q in it.term.lower()
                or q in it.simple_explanation.lower()
                or q in it.economic_meaning.lower()
                or q in it.practical_impact.lower()
                or q in it.primary_source.lower()
            )
        ]

    st.markdown(f"**Showing {len(filtered_items)} of {len(en_items)} defined terms**")

    for item in filtered_items:
        st.markdown(
            f"""
            <div style="background: #ffffff; border: 1px solid #cbd5e1; border-left: 5px solid #1e3a8a; border-radius: 8px; padding: 14px 18px; margin-bottom: 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; margin-bottom: 10px; border-bottom: 1px solid #f1f5f9; padding-bottom: 8px;">
                    <span style="font-size: 1.15rem; font-weight: 800; color: #0f172a;">{item.term}</span>
                    <div style="display: flex; gap: 6px; align-items: center;">
                        <span style="background: #eff6ff; color: #1e40af; font-size: 0.72rem; font-weight: 700; padding: 3px 8px; border-radius: 4px; border: 1px solid #bfdbfe;">{item.category}</span>
                        <span style="background: #f1f5f9; color: #334155; font-size: 0.72rem; font-weight: 700; padding: 3px 8px; border-radius: 4px; border: 1px solid #cbd5e1;">📍 {item.region}</span>
                    </div>
                </div>
                <div style="margin-bottom: 8px;">
                    <div style="font-size: 0.80rem; font-weight: 750; color: #1e3a8a; text-transform: uppercase; letter-spacing: 0.03em; margin-bottom: 2px;">
                        📖 Plain-English Explanation (For Everyone):
                    </div>
                    <div style="font-size: 0.88rem; color: #1e293b; line-height: 1.45; background: #f8fafc; padding: 8px 12px; border-radius: 6px; border: 1px solid #e2e8f0;">
                        {item.simple_explanation}
                    </div>
                </div>
                <div style="margin-bottom: 8px;">
                    <div style="font-size: 0.80rem; font-weight: 750; color: #334155; text-transform: uppercase; letter-spacing: 0.03em; margin-bottom: 2px;">
                        ⚙️ Economic & Financial Meaning:
                    </div>
                    <div style="font-size: 0.85rem; color: #475569; line-height: 1.45;">
                        {item.economic_meaning}
                    </div>
                </div>
                <div style="margin-bottom: 8px;">
                    <div style="font-size: 0.80rem; font-weight: 750; color: #059669; text-transform: uppercase; letter-spacing: 0.03em; margin-bottom: 2px;">
                        💡 Why It Matters & Practical Impact:
                    </div>
                    <div style="font-size: 0.85rem; color: #334155; line-height: 1.45;">
                        {item.practical_impact}
                    </div>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; font-size: 0.74rem; color: #64748b; margin-top: 10px; padding-top: 6px; border-top: 1px dashed #e2e8f0;">
                    <span>🏛️ <strong>Primary Authority:</strong> {item.primary_source}</span>
                    <span>⏱️ <strong>Frequency:</strong> {item.frequency}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


I18N_SYNC_VERSION = "2026.10.21.v3"
