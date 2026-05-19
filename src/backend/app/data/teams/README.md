# Teamdossiers (YAML)

**Eén bron per land:** `research/{slug}.yaml` ,  research, ratings, groepsprogramma, venues en matchup-taal.

Geen aparte `*.json` meer; de backend laadt YAML **direct** bij voorspellingen en API.

## Inhoud per bestand

| Sectie | Bron |
|--------|------|
| `power_score`, `tier`, `macro_style`, `strengths`, `risks` | Pool-snapshot (via sync) |
| Coach/spelers/tactiek/psychologie | Handmatige research |
| `group_stage` | FIFA-CSV (via sync) ,  tegenstanders, stadions, rust, hooks |
| Optioneel | `distinctive_spark_notes`, `star_dependency`, … |

## Workflow

```bash
cd src/backend
# 1. Bewerk research/nederland.yaml (of ander land)
# 2. Na CSV-wijziging of eerste setup: groepsfase opnieuw uit CSV
python -m app.data.teams.sync_research_yaml
```

**Tornooi bijhouden:** vul `tournament_context.phases.group.played_matches`, `standings` en `momentum` handmatig in; sync overschrijft die niet. Zie `research/README.md` § Tournament context.

Voorspellingen gebruiken `get_team_bundle()` → `power_score` + begrensde **context-laag** (`context_score.py`, uit `context_scoring` in YAML).

## Techniek

- `team_loader.py` ,  laadt YAML
- `fixture_schedule.py` / `fixture_venues.py` ,  CSV-verrijking
- `context_score.py` ,  som `context_scoring` + co-host (max ±6 pt-equivalent op duel)
- `build_context_scoring_yaml.py` ,  genereert `context_scoring` uit research
- `predictions.py` ,  leest bundles, niet meer losse JSON-facetten

FIFA/CSV-naam (Engels) blijft intern als `opponent_fifa` in `group_stage`; overal zichtbaar = Nederlands (`team_id`).
