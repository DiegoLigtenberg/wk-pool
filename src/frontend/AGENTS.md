# Agent checks (WK Pool frontend)

## UI / UX responsive

Handmatig of geautomatiseerd na wijzigingen aan wedstrijdlijst, AI-panel, modals, filters of knock-out bracket.

```bash
cd src/frontend
# Backend op :8000; frontend dev (proxy, geen CORS-gedoe):
npx vite --host 127.0.0.1 --port 5180
# andere terminal:
npm i -D playwright   # eenmalig
npx playwright install chromium
APP_URL=http://127.0.0.1:5180/ node scripts/audit_responsive.mjs
```

Controleert op **mobile (390px), tablet (834px), desktop (1440px)**:

- Geen pagina-brede horizontale overflow
- AI-panel: open via score, sluit buiten klik, max één panel tegelijk
- AI-badge tap-target ≥ 40px op touch
- Knock-out: inner scroll toegestaan, geen page overflow
- Teamvisie-modal past in viewport

### Fragiele plekken (visueel handmatig nakijken)

| Gebied | Breakpoint | Let op |
|--------|------------|--------|
| Wedstrijdkaarten | `≤760px` | Lange teamnamen, AI-badge + score in smalle kolom |
| AI-panel | `≤760px` | `max-height: 68dvh`, scroll binnen panel |
| Knock-out bracket | `≤900px` | Horizontale scroll in `.knockout-bracket-shell` (bewust) |
| Tablet | `761–1099px` | Nog **desktop-tabel** layout; kolommen kunnen krap worden |
| Teamvisie modal | alle | `safe-area-inset`, Escape sluit |

## Unit tests

```bash
npm test
```

Relevant voor AI-panel gedrag: `src/components/matches/MatchesView.test.tsx`.

## Samen met andere agents

| Agent | Wanneer |
|--------|---------|
| Backend prediction/narrative | Na API/insight-wijzigingen: zie `src/backend/AGENTS.md` |
| API contract | `cd src/backend && poetry run python scripts/validate_tournament_contract.py` |
| Deploy | `npm run build` moet slagen vóór release |
