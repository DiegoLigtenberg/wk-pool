# Modelgewichten: basisscore vs. wedstrijdcontext (WK 2026 pool)

Doel: voorspellingen zijn **stabiel**, **vooraf vast te leggen**, en **uitlegbaar**. Geen runtime-LLM: alle punten staan in team-YAML en vaste regels in `factor_weights.py`.

## 1. Anker: `power_score` (basissterkte)

- Primair ordeningsanker (~80–90% van wie favoriet is in een neutrale setting).
- Context verfijnt vooral spannende duels; grote gaps (10+ punten basis) blijven dominant.

## 2. Pipeline (runtime)

1. Laad `context_scoring` uit `data/teams/research/{slug}.yaml` (max 2 persistent + 2 per groepstegenstander, ruwe delta).
2. Voeg `host_region` toe voor Canada / Mexico / USA (co-host).
3. Dedupe (`factor_dedupe.py`).
4. **Herweging** (`factor_weights.py`) → effectieve punten + bucket-caps.
5. **Duel-cap (optie B):** `|research_thuis| + |research_uit| ≤ 12` (schaal alleen research, niet host/uit-straf). YAML ±1 → **±2** effectief (`RESEARCH_POINT_SCALE = 2`).
6. `effectiveScore = power_score + contextDelta` → `diff` → kansen (`predictions.py`).

## 3. Herwegingstabel (ruw → effectief)

| Factor-id | Type | Ruw (YAML) | Effectief | Bucket-cap |
|-----------|------|------------|-----------|------------|
| `host_region` | Co-host regio | +1 (inject) | **+2** | Host totaal max **+3** |
| `cohost_crowd` | Co-host publiek | +1 | +1 | (zelfde host-bucket) |
| `home_fixture` | Co-host thuisstad | +1 | +1 | (zelfde host-bucket) |
| `away_fixture` | Uit bij co-host | −1 | **−1** | apart (travel) |
| `crowd_bias` | Publiek (niet co-host) | +1 | +1 | Persistent max ±3 |
| `squad_load` | Selectiebelasting | −2 | **−2** | Persistent |
| `distinctive_spark` | Verhaal/risico | −1 / −2 | −1 / −2 | Persistent |
| `star_dependency` | Sterafhankelijkheid | −1 | −1 | Persistent |
| `selection_drama` | Selectiechaos | −1 | −1 | Persistent |
| `style_matchup` | Stijl vs stijl | ±1 | **±2** | Duel max ±6 |
| `tactical_strength` / `tactical_weakness` | Fase-voorkeur duel | ±1 | **±2** | Duel |
| `opponent_profile_weak` / `opponent_profile_strong` | Tegenstanderprofiel | ±1 | **±2** | Duel |
| `matchup_edge` | Wij counteren hen | +1 | **+2** | Duel |
| `matchup_risk` | Zij counteren ons | −1 | **−2** | Duel |
| `psychology` | Druk in dit duel | −1 / 0 | −1 / 0 | Duel |
| `discipline` | Kaartenrisico duel | −1 | −1 | Duel |
| `opener_context` | Openings/hoogte | −1 / 0 | −1 / 0 | Duel |
| `fixture_story` / `fixture_narrative` | Verhaal | −1 / 0 | −1 / 0 | Duel |

**Research per zijde:** persistent + duel samen max **±8**.  
**Host-bucket:** `host_region` + `cohost_crowd` + `home_fixture` samen max **+3** (geen +5-stack meer).  
**Duel op het veld:** `|research_home| + |research_away| ≤ 12` (implementatie: `scale_matchup_research`).

## 4. Co-host (Canada, Mexico, USA)

- **Niet** meer +3 los plus alle +1’s onbegrensd.
- Structureel voordeel: **+2** regio (`host_region`) + optioneel +1 crowd/fixture tot **max +3** host per wedstrijd.
- Tegenstander **uit** in co-host-stadion: **−1** (`away_fixture`), niet in host-bucket.
- Host geldt in hele toernooi (ook knock-out); dat is bewust voor dit WK-model.

## 5. Kansen en pick (`predictions.py` + `pool_edge.py`)

1. **Research-score:** `baseDiff` = wedstrijdscore uit YAML/context (`context_score.py`).
2. **Pool-bijsturing** (`pool_edge.py`, max ±6 op diff):
   - YAML: `played_matches`, `momentum`, `standings`
   - Onderlinge historie (`head_to_head`)
   - Tactische upset (underdog met sterke duel-signalen vs basisfavoriet)
   - **Groepsvorm (knock-out):** `played_matches` in team-YAML na de groepsfase; **niet** uit demo-CSV en **niet** tijdens pre-WK groepsvoorspelling
3. **Pick** = `_pick_from_diff(adjustedDiff)` (wedstrijdscore + uitzondering basisfavoriet).
4. **Kansen** op `adjustedDiff`, daarna **afgestemd op pick** (pick heeft altijd hoogste %).
5. UI: korte pick-uitleg (`explain_pick` + `explain_pick_score_note`, samengevoegd) staat achteraan in `scoreSummary` onder «Scores en research-details»; `pickLogicNote` blijft leeg.

Knock-out: geen gelijk; pick tussen thuis en uit op `adjustedDiff`.

## 6. Onderhoud (andere agents)

| Agent | Taak |
|-------|------|
| Research / YAML | Ruwe delta ±1/±2 in `context_scoring`; geen coach bij verkeerd land |
| Builder | `context_scoring_builder.py` genereert ruwe factoren; herweging gebeurt runtime |
| Narrative | `verdict` + `leadSummary` zonder score-cijfers; `scoreSummary` + tabel alleen in uitklap |
| Calibration | Alleen `predictions.py` logistic als % niet kloppen met punten |

Code: `app/data/teams/factor_weights.py`, `context_score.py`.
