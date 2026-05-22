# Deployment



This repo is set up for two Railway services:



- Backend service root: `src/backend`

- Frontend service root: `src/frontend`



## Backend



Railway reads `src/backend/railway.json` when the service root is `src/backend`.



Nixpacks skips the early `pyproject.toml`-only install (`NIXPACKS_PYTHON_PACKAGE_MANAGER=skip`) and runs `pip install .` in the build phase after the full repo is copied (see `nixpacks.toml`). Local development still uses Poetry 2.



Set this backend variable:



```text

WK_POOL_ALLOWED_ORIGINS=https://your-frontend.up.railway.app

```



Railway provides `PORT` automatically. The backend binds to `0.0.0.0` whenever `PORT` (or `RAILWAY_ENVIRONMENT`) is present and exposes `/health` for health checks. The start command must use the venv binary: `/opt/venv/bin/wk-pool-backend --host 0.0.0.0` (see `railway.json`), because a custom Nixpacks build does not put `wk-pool-backend` on the default `PATH`.



## Frontend



Railway reads `src/frontend/railway.json` when the service root is `src/frontend`.



Nixpacks installs dependencies with `npm ci` and then runs `npm run build`. Do not chain another `npm ci` in `buildCommand` ,  that can fail with `EBUSY` on `node_modules/.cache`. The frontend requires **Node 20.19+** (configured via `.node-version` / `nixpacks.toml`).



Set this frontend build variable before building:



```text

VITE_API_BASE_URL=https://your-backend.up.railway.app

```



Production serves the built `dist/` folder with `npm run start` (`serve`), not `vite preview`. Railway's healthcheck hits `/` on the **frontend** service only; a down backend still returns HTTP 200 and shows an in-app error. Set `VITE_API_BASE_URL` at **build** time so the UI can reach the backend after deploy.



## Football results sync (cron)



Use a **third Railway service** that triggers sync on a schedule. It does **not** run the sync itself — it calls the backend over HTTP. Railway volumes can only attach to **one** service, so the data volume lives on the backend.



### 1. Volume on backend only



Without a volume, `match-results.json` is lost on redeploy.



1. Open your Railway project → **wk-pool-backend** → **Settings** → **Volumes**

2. Add a volume (or move your existing one here), mount path **`/data`**

3. Do **not** attach the same volume to the cron service — Railway does not support shared volumes



Set on **wk-pool-backend**:



```text

WK_POOL_DATA_DIR=/data

FOOTBALL_API_KEY=...

FOOTBALL_API_SEASON=2026

FOOTBALL_SYNC_SECRET=choose-a-long-random-string

```



### 2. Create the cron trigger service



1. **+ Add** → **GitHub Repo** → same `wk-pool` repo

2. Service name: e.g. `wk-pool-cron-sync`

3. **Settings → Root Directory:** `src/backend`

4. **Settings → Config file path:** `railway.sync.json`  

   (or paste the same settings manually)

5. **Settings → Cron Schedule:** `0 3,6,9,23 * 6,7 *`  

   → 4× per day in June/July (UTC): 03:00, 06:00, 09:00, 23:00

6. **Settings → Start Command** (if not using config file):



   ```text

   /opt/venv/bin/python scripts/trigger_football_sync.py

   ```



7. Set env vars on the **cron service only**:



   ```text

   BACKEND_URL=https://your-backend.up.railway.app

   FOOTBALL_SYNC_SECRET=same-secret-as-backend

   ```



**Do not** enable a healthcheck on the cron service. It should start, POST to the backend, and **exit**.



You can remove the volume from `wk-pool-cron-sync` if you created one there earlier.



### 3. Before the World Cup starts



Run once against the backend (Railway → backend service → **Run** / one-off, or locally):



```text

/opt/venv/bin/python scripts/sync_football_results.py --force-remap

```



Or trigger via HTTP:



```text

/opt/venv/bin/python scripts/trigger_football_sync.py --force-remap

```



That builds the CSV → API fixture id map (needs API plan with season 2026).



### 4. Outside the tournament



Pause or remove the cron schedule on the sync service so you do not use API quota.



### Local test



```bash

cd src/backend

poetry run python scripts/plan_football_polls.py

poetry run python scripts/sync_football_results.py --dry-run

```


