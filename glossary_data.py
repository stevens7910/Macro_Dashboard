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
