# Modelgewichten: basisscore vs. wedstrijdcontext (WK 2026 pool)

Doel: voorspellingen zijn **stabiel**, **vooraf vast te leggen**, en **uitlegbaar**. Dit document beschrijft hoe zwaar welke signalen wegen voordat numerieke matchup‑lagen worden toegevoegd.

## 1. Anker: `power_score` (basissterkte)

- Dit is **het primaire ordeningsanker**: wie heeft meer kwaliteit, diepte en verwacht tournament‑impact op basis van selectie‑ en voetbalinhoudelijke prior (geen live odds).
- **Interpretatie voor eindgebruiker**: ~**80, 90%** van het **gedrag van het model** (wie is favoriet in een neutrale wedstrijd) moet hieruit volgen.
- Kleine verschillen (1, 3 punten) zijn **bewust**: voetbal heeft hoge variantie; het model pretendeert geen kommagetallen‑precisie.

## 2. Wedstrijdcontext (fixtures): host‑regio, fase, ronde

**Bedoeld als correctie op het duel**, niet als tweede parallelle ranglijst.

- **Co‑hosts Canada / Mexico / USA**: kleine bonus **alleen voor het team dat effectief speelt in eigen host‑context** (zoals nu in code: +3 aan die zijde van het veld). Dit is **logistiek/publiek‑adjacent**, niet “tactiek”.
- **Groep vs knock‑out**: beïnvloedt vooral **beslisregels** (gelijk mogelijk in groep) ,  dat staat los van kwaliteit.
- **Openingsronde / pouledruk**: kan later tekst‑context (`themes`) uitbreiden; numeriek alleen als er een **harde, begrensde regel** agreed is.

**Caps‑filosofie**: context‑bonussen blijven **klein** t.o.v. `power_score`‑verschil (orde grootte enkele punten), tenzij jullie bewust een uitzondering documenteren.

## 3. Teamdossier per land (`data/teams/research/{slug}.yaml`)

**Eén YAML per land** ,  research, `power_score`, groepsprogramma (tegenstanders, stadions, rust). Geen aparte JSON-build; de backend laadt YAML bij runtime.

- **Basis:** `power_score` + tier uit het dossier (pool-snapshot, handmatig bij te werken).
- **Context-laag** (`app/data/teams/context_score.py`): kleine correctie uit vooraf vastgelegde `context_scoring` (max 2 persistent + 2 per groeps tegenstander) + co-host ,  **max ±6 punten-equivalent** op het verschil.
- **Groepsfase:** `group_stage` uit sync met FIFA-CSV (`sync_research_yaml`).

Matchup‑\(\Delta\) is geen tweede ranglijst; het verfijnt vooral spannende duels t.o.v. kale `power_score`.

## 4. Kansen en pick (`predictions.py`)

- **Eén bron:** `diff` = effectieve thuisscore − effectieve uitscore (basis + context + co-host).
- **Groepsfase:** logistic op `diff` voor marginaal thuis%; gelijk daalt met \|diff\|; bij \|diff\| ≤ 2 is gelijk de pick.
- **Knock-out:** steilere logistic, geen gelijk, thuis% tot ~88.
- **Pick** = uitkomst met hoogste percentage (geen aparte drempel meer).
- Richtwaarden groep: diff 0 → ~36% thuis; diff 8 → ~58% thuis.

## 4. Wat we **niet** automatisch hoog gewicht geven zonder actuele data

- Blessures/schorsingen dag‑van‑wedstrijd (alleen handmatige overrides als je die vastlegt).
- “Vorm van de laatste twee clubweekenden” als aparte tijdreeks ,  tenzij je die expliciet bijwerkt voor een freeze.

## 5. Volgende stap (implementatie‑los van deze repo‑tekst)

Wanneer matchup‑ \(\Delta\) live gaat:

- Hanteer harde grenzen (bijv. totaal matchup‑effect **≤ ±6 punten equivalent** op het duelverschil), tenzij jullie dat breed consensus‑matig verhogen.
- Elke \(\Delta\) heeft een **machine‑leesbare sleutel + menselijke rationale** voor de UI‑breakdown.
