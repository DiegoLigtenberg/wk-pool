# Review: groepswedstrijden context-audit (72 duels)

Gegenereerd: `scripts/audit_group_match_context.py` → `group_match_context_audit.csv`  
Model: `power_score` + hergewogen context (`factor_weights.py`)

## Samenvatting

| Metriek | Waarde |
|---------|--------|
| Groepswedstrijden | 72 |
| Co-host betrokken (MX/USA/CAN) | 9 |
| Beide kanten context = 0 | 9 |
| Pick = gelijk (`3`) | 6 |
| Pick ≠ basis-sterkte pick | 4 (allen **gelijk-gedwongen**, geen context-flip) |
| \|ctx_swing\| ≥ 5 | 1 (alleen #32 USA–AUS) |
| Research op zij-cap (\|r\| ≥ 4) | 1 (#48 COL–COD) |

**Conclusie:** Herweging werkt zoals bedoeld: co-host max ~+3 host + duel-research, geen co-host vs co-host. Geen wedstrijd waar context de pick **omdraait** t.o.v. pure `power_score` (wel 6× gelijk door `|diff|≤2`-regel). Aandachtspunten: 1 duel met extreme swing (USA–Australië), 3 landen op research-cap met mogelijke YAML-dubbeling, topfavorieten structureel -2/−3 door persistente minpunten.

---

## Grootste context-impact (|swing| = diff − basis_diff)

| # | Duel | basis_diff | swing | diff | Opmerking |
|---|------|------------|-------|------|-----------|
| 32 | USA – Australië | +7 | **+7** | +14 | USA host +4; AUS squad_load −2 + uit −1 |
| 20 | Oostenrijk – Jordanië | +14 | +2 | +16 | Na YAML-fix: JOR research −2 |
| 70 | Jordanië – Argentinië | −29 | −2 | −31 | Zelfde; ARG crowd +1 |
| 6 | Australië – Turkije | −5 | −4 | −9 | AUS squad_load −2 |
| 28 | Mexico – Zuid-Korea | +7 | +4 | +11 | MX host +3 |
| 51 | Zwitserland – Canada | +7 | −4 | +3 | CAN co-host +3 dempt favoriet |
| 53 | Tsjechië – Mexico | −6 | −4 | −10 | MX “uit” in CSV maar +4 ctx (regio) |

### #32 USA – Australië (review)

- **Grootste swing van het toernooi.** Verwacht: co-host + blessurebelasting gast.
- USA: host-bucket vol (+3) + `style_matchup` +1 → **+4** totaal.
- Australië: `squad_load` −2 + `away_fixture` −1 → **−3**.
- Pick blijft USA; geen model-fout. Wel: diff +14 → ~76% thuis (steil t.o.v. “spannende” wedstrijd in UI).

### #53 Tsjechië – Mexico

- Mexico staat als **uit** in FIFA-CSV maar krijgt `host_region` + crowd + stijl → **+4**.
- **Bewust** in model: co-host = hele regio, niet alleen `is_home`. Documentatie klopt; voor gebruikers uitleggen in narrative.

---

## Research-cap per zijde (|research| = 4)

| # | Duel | Zijde | Factoren (samenvatting) | Actie research-agent |
|---|------|-------|-------------------------|----------------------|
| 48 | COL – COD | Colombia −4 | squad_load −2 + style −1 + risk −1 | Plausibel; James/spitsbelasting |

---

## Topfavorieten structureel omlaag (swing ≤ −3, basis_diff ≥ 8)

| # | Duel | swing | Thuis context |
|---|------|-------|----------------|
| 7 | Brazilië – Marokko | −3 | star −1, selection −1, matchup_risk −1 |
| 11 | Nederland – Japan | −3 | squad_load −2, … |
| 35 | Nederland – Zweden | −3 | squad_load −2, matchup_risk −1 |

**Review:** Persistent `squad_load` / sterrenrisico **verlaagt** grote favorieten met 2–3 punten op wedstrijdscore. Dat is gewenst als “onzekerheid”, maar verklaart waarom UI soms weinig duel-±1 ziet terwijl favoriet toch “maar” 50–55% krijgt (logistic + negatieve persistent).

---

## Gelijk-picks (pick = 3)

| # | Duel | diff | basis_diff | Reden |
|---|------|------|------------|--------|
| 2 | Zuid-Korea – Tsjechië | 0 | −1 | \|diff\|≤2 → gelijk |
| 9 | Ivoorkust – Ecuador | −1 | 0 | idem |
| 52 | Bosnië – Qatar | −1 | −1 | idem |
| 57 | Japan – Zweden | 2 | +2 | idem |
| 63 | Egypte – Iran | 1 | +1 | idem |
| 72 | Congo – Oezbekistan | 1 | 0 | idem |

Geen enkele gelijk-pick komt door co-host of duel-cap alleen; allemaal **nauwelijks verschil na context**.

---

## Co-host wedstrijden (9×)

| # | Duel | USA/MX/CAN ctx | Tegenstander ctx |
|---|------|----------------|------------------|
| 1 | Mexico – Zuid-Afrika | +3 | 0 |
| 4 | USA – Paraguay | +3 | 0 |
| 28 | Mexico – Zuid-Afrika | +3 | −1 |
| 32 | USA – Australië | +4 | −3 |
| 59 | Turkije – USA | +4 | +1 |
| 3, 27, 51, 53 | Canada / Mexico varianten | +1…+4 | 0…−1 |

Host-bucket **+3** wordt overal gerespecteerd; geen +5-stacks meer na herweging.

---

## Negen “kale” duels (beide context 0)

Geen host, geen research-factoren met effect, o.a. Qatar–Zwitserland (#8), Haïti–Schotland (#5), veel H/G-underdog duels. **OK:** basissterkte alleen.

---

## Aanbevolen vervolgacties (geen code in deze review)

1. ~~**Jordanië YAML:** dedupe~~ **Gedaan:** dubbele `fixture_narrative` per tegenstander verwijderd.
2. **Narrative:** bij #53 en co-host “uit” in CSV expliciet “spelen in eigen regio” tonen.
3. **Optioneel kalibratie:** bij diff > 12 iets steilere % (USA–AUS), apart van gewichten.

---

## Bestanden

- `group_match_context_audit.csv`, alle 72 rijen, kolommen: basis/host/travel/research/context per kant, factors, pick, %.
- Opnieuw draaien: `cd src/backend && python scripts/audit_group_match_context.py`
