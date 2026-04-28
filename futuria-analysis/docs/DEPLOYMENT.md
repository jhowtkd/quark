# Deployment

## What the repo ships today

The committed repository includes:

- `Dockerfile`
- `docker-compose.yml`
- GitHub workflow files under `.github/workflows/`

The deployment shape in this document is limited to what is directly discoverable from those files.

## Docker Compose

`docker-compose.yml` defines a single service named `futuria`.

### Compose behavior

- builds from the repository `Dockerfile`
- loads environment variables from `.env`
- maps host port `3000` to container port `4000`
- maps host port `5001` to container port `5001`
- mounts `./backend/uploads` to `/app/backend/uploads`
- restarts with `unless-stopped`

### Start it

```bash
docker compose up --build
```

## Dockerfile

The committed `Dockerfile`:

- starts from `python:3.11`
- installs `nodejs` and `npm`
- copies `uv` from `ghcr.io/astral-sh/uv:0.9.26`
- installs root and frontend Node dependencies with `npm ci`
- installs backend Python dependencies with `uv sync --frozen`
- additionally runs `uv pip install langgraph>=0.2.0`
- exposes ports `3000` and `5001`
- defaults to `CMD ["npm", "run", "dev"]`

## Important runtime implication

The committed container startup command runs the same development orchestration used locally:

```bash
npm run dev
```

That means the checked-in deployment assets are closest to a development-style container runtime, not a dedicated production process layout.

## Manual non-Docker startup

You can also run the pieces directly.

### Backend

```bash
cd backend
uv sync
uv run python run.py
```

### Frontend

For local development:

```bash
cd frontend
npm install
npm run dev
```

For a production-style frontend build artifact:

```bash
npm run build
```

## Health check

The backend exposes:

```text
GET /health
```

Quick check:

```bash
curl http://localhost:5001/health
```

Expected response:

```json
{"status":"ok","service":"FUTUR.IA Backend"}
```

## Environment file

Both local and compose-based startup depend on the project environment file.

Create it from the example:

```bash
cp .env.example .env
```

See [CONFIGURATION.md](./CONFIGURATION.md) for required values.

## GitHub workflows in the repo

The repo includes:

- `.github/workflows/docker-image.yml`
- `.github/workflows/language-contamination-gate.yml`

This document does not assume any additional external deployment platform beyond those committed assets.
