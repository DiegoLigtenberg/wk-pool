# Deployment

This repo is set up for two Railway services:

- Backend service root: `src/backend`
- Frontend service root: `src/frontend`

## Backend

Railway reads `src/backend/railway.json` when the service root is `src/backend`.

Nixpacks installs with `pip`/`setuptools` (`NIXPACKS_PYTHON_PACKAGE_MANAGER=setuptools` in `nixpacks.toml`), not the legacy Poetry 1.3 CLI that `poetry.lock` would otherwise select. Local development still uses Poetry 2.

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

Production serves the built `dist/` folder with `npm run start` (`serve`), not `vite preview`. Railway's healthcheck hits `/` on the **frontend** service only; a down backend still returns HTTP 200 and shows an in-app error. Set `VITE_API_BASE_URL` at **build** time so the UI can reach the backend after deploy.
