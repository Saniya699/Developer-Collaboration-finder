# Deploy on Render (Fastest Path)

This repo is pre-configured for Render with `render.yaml`.

## What gets created

- `developer-collaboration-finder-api` (Python web service)
- `developer-collaboration-finder-web` (Static React frontend)
- `developer-collaboration-finder-db` (PostgreSQL)

## One-time steps

1. Push latest code to GitHub.
2. In Render dashboard, click **New +** -> **Blueprint**.
3. Select this GitHub repo.
4. Render will detect `render.yaml` and show the 3 resources.
5. Click **Apply**.

## Important notes

- The frontend is configured to call:
  - `https://developer-collaboration-finder-api.onrender.com`
- CORS is configured on backend via:
  - `FRONTEND_ORIGIN=https://developer-collaboration-finder-web.onrender.com`

If you rename services in Render, update these two env values accordingly.

## Backend start command (already set)

`gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT wsgi:app`

## Health check

- Backend health endpoint: `/api/health`

## After deploy

- Frontend URL:
  - `https://developer-collaboration-finder-web.onrender.com`
- Backend URL:
  - `https://developer-collaboration-finder-api.onrender.com`

