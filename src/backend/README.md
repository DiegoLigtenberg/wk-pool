# WK Pool Backend

Python backend for WK Pool.

## Setup

```powershell
cd src/backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
poetry install --with dev
```

## Run

```powershell
poetry run wk-pool-backend
```

The backend serves http://127.0.0.1:8000 by default.

When a platform provides `PORT`, the backend binds to `0.0.0.0:$PORT`.
Use `WK_POOL_ALLOWED_ORIGINS` to configure comma-separated frontend origins for CORS.
