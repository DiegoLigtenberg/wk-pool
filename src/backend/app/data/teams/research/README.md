# `research/{slug}.yaml` ,  volledig landdossier

Eén bestand per deelnemer. De backend laadt dit **direct** (geen JSON-build).

## Snel overzicht

| Sectie | Wie vult in | Wanneer |
|--------|-------------|---------|
| `power_score`, `tier`, `macro_style`, … | `sync_research_yaml` | Vaste pool + CSV |
| Coach/tactiek/psychologie/matchup-tekst | **Jij** | Research-pass |
| `tournament_context.phases.group.fixture_plan` | **Sync** (CSV) | Voor tornooi / na CSV-wijziging |
| `played_matches`, `standings`, `momentum` | **Jij** | **Tijdens** tornooi |
| `tournament_context.phases.knockout` | **Jij** (+ later sync bracket) | Na groepsfase |
| `head_to_head` | **Jij** | Research; bijwerken na elke H2H-wedstrijd |

---

## Verplichte velden (basis)

- `team_id` ,  Nederlandse landnaam (`Nederland`, `Ivoorkust`, …)
- `slug` ,  bestandsnaam (`netherlands`, `cote_d_ivoire`)
- `power_score`, `tier`, `macro_style`, `strengths`, `risks`
- `confederation`, `cohost_status`
- Research: `interpretive_ceiling_vs_floor`, `phase_preferences`, psychologie, matchup-teksten, …

Optioneel: `distinctive_spark_notes`, `star_dependency` (`high`|`medium`), blessure-notities, enz.

---

## Tournament context (`tournament_context`)

**Generiek schema** voor elke tornooifase. Zelfde structuur voor groep en knock-out, zodat we later R16/kwart/halve/finale kunnen toevoegen zonder nieuw formaat.

```yaml
tournament_context:
  schema_version: 1
  phases:
    group: { ... }
    knockout: { ... }
  head_to_head: [ ... ]
```

### Fase-object (`phases.<naam>`)

Elke fase (nu: `group`, `knockout`) heeft dezelfde velden:

| Veld | Sync? | Betekenis |
|------|-------|-----------|
| `status` | Nee | Fase-status (zie onder) |
| `fixture_plan` | **Ja** (groep) | Geplande wedstrijden, stadions, rust |
| `played_matches` | Nee | **Gespeeld** ,  uitslag, score, notities |
| `standings` | Nee | Punten/positie **snapshot** (vooral groep) |
| `momentum` | Nee | `rising` / `stable` / `falling` + tekst |
| `phase_notes` | Nee | Vrije context voor deze fase |

#### `status` ,  toegestane waarden

| Waarde | Typisch gebruik |
|--------|-----------------|
| `upcoming` | Vóór eerste wedstrijd van de fase |
| `in_progress` | Tornooi bezig in deze fase |
| `completed` | Fase afgerond (bv. groep uitgespeeld) |
| `eliminated` | Uitgeschakeld in deze fase |
| `not_applicable` | Nog niet van toepassing (standaard knock-out vóór WK) |

#### `fixture_plan` (gepland ,  uit CSV)

- **Groep:** gevuld door `python -m app.data.teams.sync_research_yaml`
- **Knock-out:** nu `null`; later bracket/ tegenstander uit CSV of handmatig

Bevat: `group`, `opponents_nl`, `opponents_fifa`, `fixtures[]`, `fixture_hooks`, `schedule_rest_notes`, `venue_dispersion_notes`.

#### `played_matches` (gespeeld ,  handmatig)

Lijst van **afgeronde** wedstrijden in deze fase. Gebruik voor momentum en voorspelling na groepsronde 1/2/3.

```yaml
played_matches:
  - match_number: 1
    opponent_fifa: Japan
    opponent_nl: Japan
    result: W              # W | D | L
    score_for: 2
    score_against: 1
    stage_round: group     # group | round_of_16 | quarter_final | ...
    notes: "Simons ontbrak; Dumfries beslissend"
```

#### `standings` (groep ,  snapshot)

Handmatig bijwerken na elke speelronde (of alleen na ronde 3):

```yaml
standings:
  points: 6
  played: 3
  wins: 2
  draws: 0
  losses: 1
  goals_for: 5
  goals_against: 3
  position: 1
```

#### `momentum`

```yaml
momentum:
  label: rising    # rising | stable | falling | null
  notes: "Twee clean sheets; Gakpo in vorm"
```

Gebruik in voorspelling: later kleine correctie op `power_score` als fase `in_progress` en momentum bekend is.

---

## `head_to_head` ,  historische onderlinge uitslagen

**Niet** hetzelfde als `played_matches` (alleen dit tornooi). Dit is research over eerdere duels vs die tegenstander.

```yaml
head_to_head:
  - opponent_fifa: Brazil
    opponent_nl: Brazilië
    scope: world_cup       # all_time | world_cup | recent
    wins: 0
    draws: 1
    losses: 2
    last_meeting: "WK 2022 halve finale 2-2 (pen 3-4)"
    notes: "Rematch mogelijk in KO; Neymar-factor"
```

- `opponent_fifa` ,  FIFA/CSV-sleutel (machine)
- `opponent_nl` ,  weergavenaam
- `scope`:
  - `all_time` ,  alle officiële interlands
  - `world_cup` ,  alleen WK-duels
  - `recent` ,  bv. laatste 10 jaar (in `notes` specificeren)
- Na een gespeelde wedstrijd tegen Brazilië: **of** `played_matches` bijwerken **én** eventueel H2H-totalen hier optellen

Meerdere regels per tegenstander mag (andere `scope`).

---

## Knock-out later toevoegen

Wanneer de bracket vaststaat:

1. Zet `phases.knockout.status` op `upcoming` of `active`
2. Vul `fixture_plan` (of aparte velden in loader):
   ```yaml
   knockout:
     status: active
     fixture_plan:
       bracket_notes: "R16 vs Argentinië, winnaar poule C"
       fixtures:
         - match_number: null
           kickoff: "2026-07-05T20:00"
           is_home: false
           opponent_fifa: Argentina
           opponent_nl: Argentinië
           stadium: Dallas Stadium
     played_matches: []
   ```
3. Optioneel extra fases: `round_of_16`, `quarter_final` ,  zelfde structuur; loader moet dan uitgebreid worden (nu alleen `group` + `knockout` keys)

---

## Sync-commando

```bash
cd src/backend
python -m app.data.teams.sync_research_yaml
```

**Wat sync doet:**

- Vult `power_score`, ratings, `confederation`, …
- Overschrijft `tournament_context.phases.group.fixture_plan` + legacy root `group_stage`
- Zet knock-out skeleton als die nog ontbreekt
- **Laat ongemoeid:** `played_matches`, `standings`, `momentum`, `phase_notes`, `head_to_head`, alle narratieve research-velden

---

## Loader (code)

- `team_loader.py` ,  leest YAML → `TeamBundle`
- `tournament_context_loader.py` ,  parse `tournament_context`
- `group_stage` op bundle = `fixture_plan` (uit context of legacy root key)

**Volgende implementatiestappen** (nog niet in voorspelling):

1. `played_matches` + `standings` → momentum-score in `context_score.py`
2. `head_to_head` → kleine Δ bij bekende underdog/favoriet-H2H
3. Knock-out `fixture_plan` uit bracket-CSV

---

## Template

Kopieer `_template.yaml` voor een nieuw land of nieuwe velden.
