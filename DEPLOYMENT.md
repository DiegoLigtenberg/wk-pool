# Deployment

This repo is set up for two Railway services:

- Backend service root: `src/backend`
- Frontend service root: `src/frontend`

## Backend

Railway reads `src/backend/railway.json` when the service root is `src/backend`.

Nixpacks installs the app with `pip install .` (see `nixpacks.toml`), not the legacy Poetry 1.3 CLI, so PEP 621 `pyproject.toml` and the Poetry 2 lockfile stay compatible with local development.

Set this backend variable:

```text
WK_POOL_ALLOWED_ORIGINS=https://your-frontend.up.railway.app
```

Railway provides `PORT` automatically. The backend binds to `0.0.0.0` whenever `PORT` is present and exposes `/health` for health checks.

## Frontend

Railway reads `src/frontend/railway.json` when the service root is `src/frontend`.

Nixpacks installs dependencies with `npm ci` and then runs `npm run build`. Do not chain another `npm ci` in `buildCommand` — that can fail with `EBUSY` on `node_modules/.cache`. The frontend requires **Node 20.19+** (configured via `.node-version` / `nixpacks.toml`).

Set this frontend build variable before building:

```text
VITE_API_BASE_URL=https://your-backend.up.railway.app
```

The Vite preview server binds to `0.0.0.0` and uses Railway's `PORT`.
