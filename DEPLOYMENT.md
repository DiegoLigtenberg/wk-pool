# Deployment

This repo is set up for two Railway services:

- Backend service root: `src/backend`
- Frontend service root: `src/frontend`

## Backend

Railway reads `src/backend/railway.json` when the service root is `src/backend`.

Set this backend variable:

```text
WK_POOL_ALLOWED_ORIGINS=https://your-frontend.up.railway.app
```

Railway provides `PORT` automatically. The backend binds to `0.0.0.0` whenever `PORT` is present and exposes `/health` for health checks.

## Frontend

Railway reads `src/frontend/railway.json` when the service root is `src/frontend`.

Set this frontend build variable before building:

```text
VITE_API_BASE_URL=https://your-backend.up.railway.app
```

The Vite preview server binds to `0.0.0.0` and uses Railway's `PORT`.
