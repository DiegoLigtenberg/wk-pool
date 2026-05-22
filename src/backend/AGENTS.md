# Agent checks (WK Pool backend)

Vaste checks voor prediction/narrative en research/context. Draai na wijzigingen aan research-YAML, scoring of teksten.

## Prediction & narrative

```bash
cd src/backend
poetry run pytest tests/test_agent_prediction_research.py tests/test_prediction_narrative.py -q
poetry run python scripts/audit_lead_summaries.py
poetry run python scripts/audit_duplicate_factor_reasons.py
poetry run python scripts/audit_context_duplicates.py
```

- `audit_lead_summaries.py` — verdict + leadSummary (geen cijfers vóór uitklap).
- `audit_duplicate_factor_reasons.py` — zelfde tekst op meerdere factorregels in de UI (bijv. +2 co-host én +1 thuis).
- `audit_context_duplicates.py` — ruwe context/YAML (incl. `cohost_persistent_and_match`).

Controleert o.a.:

- Geen vage voorspellingssjablonen in alle groepsduels
- Pick ↔ kansen ↔ dueltotaal
- Golden duels: Canada–Bosnië, Haïti–Schotland, Duitsland–Curaçao, NL–Japan
- Co-host-narrative niet generiek

## Research & context pipeline

```bash
poetry run pytest tests/test_agent_prediction_research.py::test_stored_context_scoring_matches_fresh_build -q
poetry run pytest tests/test_agent_prediction_research.py::test_research_matchup_bullets_not_cryptic_stubs -q
poetry run python scripts/audit_persistent_versus_overlap.py
```

Na research-YAML wijzigen **altijd**:

```bash
poetry run python -m app.data.teams.build_context_scoring_yaml
```

## Audit-suite (na scoring/tekst-wijzigingen)

Vanuit `src/backend` (scripts zetten zelf `PYTHONPATH`):

```bash
python scripts/audit_factor_sign_alignment.py
python scripts/audit_narrative_quality.py
python scripts/audit_lead_summaries.py
python scripts/audit_lead_repetition.py
python scripts/audit_pick_truth.py
python scripts/audit_persistent_versus_overlap.py
python scripts/audit_context_duplicates.py
python scripts/validate_tournament_contract.py
python scripts/sanity_check_predictions.py
```

`audit_research_clarity.py` schrijft `audit_research_clarity.json` (cryptische research-regels, score ≥ 3).

## Samen met andere agents

| Agent | Wanneer extra draaien |
|--------|------------------------|
| API contract | `python scripts/validate_tournament_contract.py` na insight/JSON-wijzigingen |
| Data quality | CSV sync + `poetry run pytest tests/test_teams.py tests/test_team_bundles.py -q` |
| Narratief/kwaliteit | `python scripts/audit_narrative_quality.py` (gebruikt `leadSummary`) |
| Teken vs tekst | `python scripts/audit_factor_sign_alignment.py` |
| Full backend | `poetry run pytest tests/ -q` vóór release |
| UI / UX responsive | `src/frontend/AGENTS.md`, Playwright smoke + handmatige bracket/tablet check |

**Insight-velden:** `home`/`away` hebben `researchDelta`, `hostDelta`, `travelDelta`; factor-deltas in de tabel tellen op tot `contextDelta` (na bucket-caps en pair-scaling).
